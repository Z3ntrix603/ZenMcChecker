"""Crash-resilient local scan history and portable exports. Never stores tokens."""
import csv
from dataclasses import asdict
from datetime import datetime
import html
import json
import os
from pathlib import Path
import sqlite3
import sys
import uuid
from .checker import Result, STATUSES


def app_directory():
    return Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent.parent


def default_directory():
    preferred = app_directory() / "ZenMcChecker-Daten"
    try:
        preferred.mkdir(parents=True, exist_ok=True)
        with (preferred / ".write-test").open("w") as f:
            f.write("")
        (preferred / ".write-test").unlink()
        return preferred
    except OSError:
        fallback = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "ZenMcChecker"
        fallback.mkdir(parents=True, exist_ok=True)
        return fallback


def atomic_json(path, data):
    path = Path(path)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    temp.replace(path)


class Store:
    def __init__(self, root=None):
        self.root = Path(root) if root else default_directory()
        self.root.mkdir(parents=True, exist_ok=True)
        self.scans = self.root / "Scans"
        self.scans.mkdir(exist_ok=True)
        self.db = sqlite3.connect(self.root / "studio.sqlite3", timeout=20)
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.executescript("""
        CREATE TABLE IF NOT EXISTS scans(id TEXT PRIMARY KEY, created TEXT, label TEXT, folder TEXT,
          config TEXT, names TEXT, state TEXT DEFAULT 'running');
        CREATE TABLE IF NOT EXISTS results(scan_id TEXT, name TEXT COLLATE NOCASE, status TEXT,
          detail TEXT, checked_at TEXT, uuid TEXT, PRIMARY KEY(scan_id,name));
        CREATE TABLE IF NOT EXISTS favorites(name TEXT PRIMARY KEY COLLATE NOCASE, created TEXT);
        """)
        self.db.commit()

    def settings(self):
        try:
            data = json.loads((self.root / "settings.json").read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {}
        except (OSError, ValueError):
            return {}

    def save_settings(self, data):
        atomic_json(self.root / "settings.json", data)

    def create_scan(self, config, names, output=None):
        scan_id = datetime.now().strftime("%Y-%m-%d_%H-%M-%S_") + uuid.uuid4().hex[:6]
        folder = (Path(output) if output else self.scans) / scan_id
        folder.mkdir(parents=True, exist_ok=False)
        config = asdict(config)
        atomic_json(folder / "scan.json", {"id": scan_id, "config": config, "names": names})
        self.db.execute("INSERT INTO scans VALUES(?,?,?,?,?,?,?)",
                        (scan_id, datetime.now().isoformat(timespec="seconds"), config["mode"], str(folder),
                         json.dumps(config), json.dumps(names), "running"))
        self.db.commit()
        self.export(scan_id)
        return scan_id

    def record(self, scan_id, result):
        self.db.execute("INSERT OR REPLACE INTO results VALUES(?,?,?,?,?,?)",
                        (scan_id, result.name, result.status, result.detail, result.checked_at, result.uuid))
        self.db.commit()
        # Append each discovery immediately. Final snapshots are rebuilt from SQLite.
        if result.status in ("available", "unclaimed"):
            folder = self.folder(scan_id)
            filename = "verfuegbar.txt" if result.status == "available" else "unbelegt.txt"
            with (folder / filename).open("a", encoding="utf-8") as f:
                f.write(f"{result.name}\t{result.url}\n")

    def folder(self, scan_id):
        row = self.db.execute("SELECT folder FROM scans WHERE id=?", (scan_id,)).fetchone()
        if not row:
            raise ValueError("Scan nicht gefunden")
        return Path(row[0])

    def results(self, scan_id):
        return [Result(*row) for row in self.db.execute(
            "SELECT name,status,detail,checked_at,uuid FROM results WHERE scan_id=? ORDER BY rowid", (scan_id,))]

    def pending(self, scan_id):
        row = self.db.execute("SELECT names FROM scans WHERE id=?", (scan_id,)).fetchone()
        done = {r.name.lower() for r in self.results(scan_id) if r.status not in ("error", "invalid")}
        return [name for name in json.loads(row[0]) if name.lower() not in done]

    def history(self):
        return self.db.execute("""SELECT s.id,s.created,s.label,s.state,count(r.name),
          sum(CASE WHEN r.status IN ('available','unclaimed') THEN 1 ELSE 0 END)
          FROM scans s LEFT JOIN results r ON s.id=r.scan_id GROUP BY s.id ORDER BY s.created DESC LIMIT 200""").fetchall()

    def set_state(self, scan_id, state):
        self.db.execute("UPDATE scans SET state=? WHERE id=?", (state, scan_id))
        self.db.commit()

    def favorites(self):
        return [r[0] for r in self.db.execute("SELECT name FROM favorites ORDER BY created DESC")]

    def toggle_favorite(self, name):
        exists = self.db.execute("SELECT 1 FROM favorites WHERE name=?", (name,)).fetchone()
        if exists:
            self.db.execute("DELETE FROM favorites WHERE name=?", (name,))
        else:
            self.db.execute("INSERT INTO favorites VALUES(?,?)", (name, datetime.now().isoformat()))
        self.db.commit()

    def export(self, scan_id):
        folder = self.folder(scan_id)
        folder.mkdir(parents=True, exist_ok=True)
        results = self.results(scan_id)
        for status, filename in (("available", "verfuegbar.txt"), ("unclaimed", "unbelegt.txt")):
            (folder / filename).write_text("".join(f"{r.name}\t{r.url}\n" for r in results if r.status == status), encoding="utf-8")
        with (folder / "ergebnisse.csv").open("w", encoding="utf-8-sig", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Username", "Status", "Zeitpunkt (UTC)", "NameMC", "Hinweis", "UUID"])
            for r in results:
                writer.writerow([r.name, STATUSES[r.status], r.checked_at, r.url, r.detail, r.uuid])
        atomic_json(folder / "ergebnisse.json", [r.to_dict() for r in results])
        rows = "".join(f'<tr><td><a href="{r.url}">{html.escape(r.name)}</a></td><td>{STATUSES[r.status]}</td>'
                       f'<td>{html.escape(r.detail)}</td><td>{html.escape(r.checked_at)}</td></tr>' for r in results)
        (folder / "NameMC-Links.html").write_text('''<!doctype html><html lang="de"><meta charset="utf-8">
<meta name="viewport" content="width=device-width"><title>ZenMcChecker · Ergebnisse</title>
<style>body{background:#101514;color:#e8f1ed;font:15px system-ui;margin:5vw}a{color:#99edc2}h1{font-size:40px}
table{width:100%;border-collapse:collapse}td,th{text-align:left;padding:14px;border-bottom:1px solid #293732}
p{color:#a4b6ac}a:hover{color:white}</style><h1>ZenMcChecker / Name Studio</h1>
<p>Unbelegt bedeutet: kein öffentliches Profil gefunden. Reservierungen und Sperren sind möglich.
Verfügbar bedeutet: durch Minecraft Services mit Token bestätigt. Ergebnisse sind Momentaufnahmen.</p>
<table><tr><th>Name ↗ NameMC</th><th>Status</th><th>Hinweis</th><th>UTC</th></tr>''' + rows + '</table></html>', encoding="utf-8")
        return folder

    def close(self):
        self.db.close()
