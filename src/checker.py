"""Conservative official API client with interruptible, per-name retries."""
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import re
import threading
import time
import requests
from .generator import VALID_NAME

PROFILE_URL = "https://api.mojang.com/users/profiles/minecraft/{}"
AVAILABILITY_URL = "https://api.minecraftservices.com/minecraft/profile/name/{}/available"
STATUSES = {"unclaimed": "Unbelegt*", "available": "Verfügbar ✓", "taken": "Belegt",
            "blocked": "Gesperrt / reserviert", "error": "Prüffehler", "invalid": "Ungültig"}


@dataclass
class Result:
    name: str
    status: str
    detail: str = ""
    checked_at: str = ""
    uuid: str = ""

    @property
    def url(self):
        return f"https://namemc.com/profile/{self.name}"

    def to_dict(self):
        return {**asdict(self), "namemc_url": self.url}


class NameChecker:
    def __init__(self, delay=1.0, token="", session=None, on_notice=None):
        self.delay = max(1.0, float(delay))
        self.token = token.strip()
        self.session = session or requests.Session()
        self.session.headers.update({"User-Agent": "ZenMcChecker/2.0"})
        self.stop_event = threading.Event()
        self.pause_event = threading.Event()
        self.pause_event.set()
        self.on_notice = on_notice or (lambda _: None)
        self.last_request = 0.0
        self.auth_failed = False

    def stop(self):
        self.stop_event.set()
        self.pause_event.set()

    def pause(self):
        self.pause_event.clear()

    def resume(self):
        self.pause_event.set()

    def ready(self):
        while not self.stop_event.is_set():
            if self.pause_event.wait(.15):
                return not self.stop_event.is_set()
        return False

    def wait(self, seconds):
        deadline = time.monotonic() + seconds
        while time.monotonic() < deadline:
            if not self.ready() or self.stop_event.wait(min(.15, max(0, deadline - time.monotonic()))):
                return False
        return self.ready()

    def _request(self, url, authenticated=False):
        headers = {"Authorization": f"Bearer {self.token}"} if authenticated else {}
        # Account availability endpoint is intentionally much slower than public lookups.
        interval = max(self.delay, 16.0 if authenticated else 1.0)
        for attempt in range(4):
            if not self.ready() or not self.wait(max(0, self.last_request + interval - time.monotonic())):
                return None, "Abgebrochen"
            try:
                self.last_request = time.monotonic()
                response = self.session.get(url, headers=headers, timeout=(5, 10), allow_redirects=False)
            except requests.RequestException:
                response = None
            if response is not None and response.status_code not in (429, 500, 502, 503, 504):
                return response, ""
            if attempt == 3:
                return None, "API-Limit / Netzwerkfehler nach 4 Versuchen"
            delay = 2 ** (attempt + 1)
            if response is not None and response.status_code == 429:
                value = response.headers.get("Retry-After", "")
                try:
                    delay = max(delay, float(value))
                except ValueError:
                    try:
                        delay = max(delay, (parsedate_to_datetime(value) - datetime.now(timezone.utc)).total_seconds())
                    except (ValueError, TypeError, OverflowError):
                        delay = max(delay, 30)
            self.on_notice(f"API-Pause: {delay:.0f} s · Versuch {attempt + 2}/4")
            if not self.wait(delay):
                return None, "Abgebrochen"
        return None, "API nicht erreichbar"

    def check_one(self, name):
        now = datetime.now(timezone.utc).isoformat(timespec="seconds")
        def result(status, detail="", uuid=""):
            return Result(name, status, detail, now, uuid)
        if not VALID_NAME.fullmatch(name):
            return result("invalid", "Java-Namen: 3–16 Zeichen, a–z, 0–9 oder _")
        if self.token and self.auth_failed:
            return result("error", "Token ungültig / abgelaufen. Token in Einstellungen ersetzen.")
        response, error = self._request(AVAILABILITY_URL.format(name) if self.token else PROFILE_URL.format(name), bool(self.token))
        if response is None:
            return None if self.stop_event.is_set() else result("error", error)
        code = response.status_code
        if self.token:
            if code in (401, 403):
                self.auth_failed = True
                return result("error", "Token ungültig / abgelaufen oder Zugriff verweigert")
            if code == 200:
                try:
                    status = response.json().get("status")
                except (ValueError, AttributeError):
                    status = None
                mapping = {"AVAILABLE": "available", "DUPLICATE": "taken", "NOT_ALLOWED": "blocked"}
                if status in mapping:
                    return result(mapping[status], f"Minecraft Services: {status}")
        else:
            if code == 200:
                try:
                    data = response.json()
                    if isinstance(data, dict) and re.fullmatch(r"[0-9a-fA-F]{32}", data.get("id", "")) and str(data.get("name", "")).lower() == name.lower():
                        return result("taken", "Mojang-Profil gefunden", data["id"])
                except (ValueError, TypeError):
                    pass
            if code in (204, 404):
                return result("unclaimed", "Kein Profil gefunden. Sperren / Reservierungen sind ohne Token nicht prüfbar.")
        return result("error", f"Unerwartete API-Antwort (HTTP {code})")

    def run(self, names, on_result, on_progress=None):
        try:
            for index, name in enumerate(names):
                if not self.ready():
                    break
                result = self.check_one(name)
                if result is None:
                    break
                on_result(result)
                if on_progress:
                    on_progress(index + 1, len(names))
                if self.auth_failed:
                    self.on_notice("Scan angehalten: Token ungültig. Einstellungen prüfen.")
                    break
        finally:
            self.session.close()
