"""ZenMcChecker 2 — desktop Name Studio. Tk access stays on the UI thread."""
from collections import Counter
from dataclasses import asdict, fields
import csv
import json
import os
from pathlib import Path
import queue
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import webbrowser
import customtkinter as ctk
from .checker import NameChecker, STATUSES
from .generator import GeneratorConfig, MODES, generate, describe, dictionary
from .storage import Store, atomic_json

VERSION = "2.0.0"
BG, SIDE, CARD, INPUT = "#0c1110", "#101714", "#141d19", "#0e1512"
BORDER, TEXT, MUTED, ACCENT = "#29392f", "#ecf4ee", "#8da497", "#b7f599"
LANGUAGES = {"Deutsch + Englisch": "both", "Deutsch": "de", "Englisch": "en"}
CASES = {"klein": "lower", "Groß am Anfang": "title", "GROSS": "upper", "Original": "original"}
CATEGORIES = {"animals": "Tiere EN", "nature": "Natur EN", "weapons": "Waffen EN", "mythical": "Mythen EN",
              "abstract": "Abstrakt EN", "materials": "Material EN", "colors": "Farben EN", "adjectives": "Adjektive EN",
              "gaming": "Gaming EN", "og_elite": "OG EN", "tiere": "Tiere DE", "natur": "Natur DE", "waffen": "Waffen DE",
              "mythisch": "Mythen DE", "abstrakt": "Abstrakt DE", "material": "Material DE", "krieg": "Kampf DE", "farben": "Farben DE", "koerper": "Körper DE"}


class ZenMcCheckerApp(ctk.CTk):
    def __init__(self, data_dir=None):
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("green")
        super().__init__()
        self.title("ZenMcChecker · Name Studio")
        self.geometry("1400x900")
        self.minsize(1140, 760)
        self.configure(fg_color=BG)
        icon = Path(__file__).resolve().parent.parent / "assets" / "studio.ico"
        if icon.exists():
            self.iconbitmap(str(icon))
        self.store = Store(data_dir)
        settings = self.store.settings()
        self.events = queue.Queue()
        self.names, self.custom_names, self.results = [], [], {}
        self.scan_id, self.checker = None, None
        self.busy = self.generating = self.closing = self.dirty = False
        self.generated_config = asdict(GeneratorConfig())
        self.config_vars = {}
        for field in fields(GeneratorConfig):
            value = getattr(GeneratorConfig(), field.name)
            if field.name != "categories":
                self.config_vars[field.name] = tk.BooleanVar(value=value) if isinstance(value, bool) else tk.StringVar(value=str(value))
        self.category_vars = {key: tk.BooleanVar(value=False) for key in CATEGORIES}
        for key, value in {"mode": MODES["letters"], "language": "Deutsch + Englisch", "case": "klein", "order": "Zufällig"}.items():
            self.config_vars[key].set(value)
        self.search_var = tk.StringVar()
        self.filter_var = tk.StringVar(value="Alle")
        self.status_var = tk.StringVar(value="Bereit für deinen nächsten Namen.")
        self.output_var = tk.StringVar(value=settings.get("output", str(self.store.scans)))
        self.delay_var = tk.StringVar(value=str(settings.get("delay", "1.0")))
        self.token_var = tk.StringVar()
        self.theme_var = tk.StringVar(value=settings.get("accent", "Mint"))
        self.compact_var = tk.BooleanVar(value=settings.get("compact", False))
        self._layout()
        self._apply_theme()
        self.search_var.trace_add("write", lambda *_: self._render_table())
        self.filter_var.trace_add("write", lambda *_: self._render_table())
        self.bind("<Control-g>", lambda _: self._generate())
        self.bind("<Control-Return>", lambda _: self._start())
        self.bind("<Control-f>", lambda _: self.search_entry.focus_set())
        self.table.bind("<Control-c>", lambda _: self._name_action("copy"))
        self.protocol("WM_DELETE_WINDOW", self._close)
        self.after(100, self._poll)
        self.after(300, self._generate)

    def label(self, parent, text="", size=13, color=TEXT, bold=False, **kw):
        return ctk.CTkLabel(parent, text=text, text_color=color,
                            font=ctk.CTkFont("Segoe UI", size, "bold" if bold else "normal"), **kw)

    def button(self, parent, text, command, primary=False, **kw):
        return ctk.CTkButton(parent, text=text, command=command, height=36, corner_radius=8,
                            fg_color=ACCENT if primary else "#223128", hover_color="#96ce7e" if primary else "#304536",
                            text_color="#172713" if primary else TEXT, font=("Segoe UI", 12, "bold"), **kw)

    def entry(self, parent, variable, **kw):
        return ctk.CTkEntry(parent, textvariable=variable, height=34, fg_color=INPUT,
                           border_color=BORDER, text_color=TEXT, corner_radius=7, **kw)

    def combo(self, parent, variable, values, command=None, **kw):
        return ctk.CTkOptionMenu(parent, variable=variable, values=values, command=command,
                               height=34, fg_color="#23342a", button_color="#304536", button_hover_color="#405b48",
                               text_color=TEXT, dropdown_fg_color=CARD, **kw)

    def _layout(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        sidebar = ctk.CTkFrame(self, width=178, corner_radius=0, fg_color=SIDE)
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_propagate(False)
        self.label(sidebar, "Z /", 38, ACCENT, True).pack(anchor="w", padx=25, pady=(30, 0))
        self.label(sidebar, "ZENMCCHECKER", 12, TEXT, True).pack(anchor="w", padx=25)
        self.label(sidebar, "NAME STUDIO  /  02", 10, MUTED).pack(anchor="w", padx=25, pady=(2, 30))
        self.nav = {}
        for key, title in (("studio", "◈   Name Studio"), ("favorites", "☆   Favoriten"), ("history", "↺   Scan-Verlauf"), ("settings", "☷   Einstellungen")):
            b = self.button(sidebar, title, lambda k=key: self._show(k), anchor="w", width=154)
            b.pack(padx=12, pady=4)
            self.nav[key] = b
        bottom = ctk.CTkFrame(sidebar, fg_color="transparent")
        bottom.pack(side="bottom", fill="x", padx=20, pady=24)
        self.label(bottom, "JAVA EDITION", 10, ACCENT, True).pack(anchor="w")
        self.label(bottom, "3–16 Zeichen\nUnendlich viele Ideen.", 11, MUTED, justify="left").pack(anchor="w", pady=(6, 15))
        self.label(bottom, f"v{VERSION} · by Z3ntrix603", 10, MUTED).pack(anchor="w")
        content = ctk.CTkFrame(self, fg_color=BG, corner_radius=0)
        content.grid(row=0, column=1, sticky="nsew", padx=26, pady=(20, 14))
        content.grid_columnconfigure(0, weight=1)
        content.grid_rowconfigure(1, weight=1)
        header = ctk.CTkFrame(content, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", pady=(0, 20))
        self.label(header, "FIND YOUR NEXT IDENTITY", 10, ACCENT, True).pack(anchor="w")
        self.heading = self.label(header, "", 30, TEXT, True)
        self.heading.pack(anchor="w", pady=(2, 0))
        self.subheading = self.label(header, "", 12, MUTED)
        self.subheading.pack(anchor="w", pady=(3, 0))
        self.pages = {name: ctk.CTkFrame(content, fg_color="transparent") for name in ("studio", "favorites", "history", "settings")}
        self._build_studio(self.pages["studio"])
        self._build_collection(self.pages["favorites"], "favorites")
        self._build_collection(self.pages["history"], "history")
        self._build_settings(self.pages["settings"])
        footer = ctk.CTkFrame(content, fg_color="transparent", height=25)
        footer.grid(row=2, column=0, sticky="ew", pady=(9, 0))
        self.label(footer, "", 11, MUTED, anchor="w", textvariable=self.status_var).pack(side="left", fill="x", expand=True)
        self.label(footer, "CTRL G  Generieren   ·   CTRL ↵  Scan", 10, MUTED).pack(side="right")
        self._show("studio")

    def _section(self, parent, title):
        self.label(parent, title, 11, ACCENT, True).pack(anchor="w", pady=(16, 8))

    def _field(self, parent, title, key, values=None):
        self.label(parent, title, 11, MUTED).pack(anchor="w", pady=(9, 4))
        widget = self.combo(parent, self.config_vars[key], values) if values else self.entry(parent, self.config_vars[key])
        widget.pack(fill="x")
        return widget

    def _pair(self, parent, left, right):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=(9, 0))
        row.grid_columnconfigure((0, 1), weight=1, uniform="pair")
        for col, (title, key) in enumerate((left, right)):
            box = ctk.CTkFrame(row, fg_color="transparent")
            box.grid(row=0, column=col, sticky="ew", padx=(0, 5) if col == 0 else (5, 0))
            self.label(box, title, 11, MUTED).pack(anchor="w", pady=(0, 4))
            self.entry(box, self.config_vars[key], width=90).pack(fill="x")

    def _tree(self, parent, columns, headings, widths):
        tree = ttk.Treeview(parent, columns=columns, show="headings", selectmode="browse", style="Studio.Treeview")
        for col, title, width in zip(columns, headings, widths):
            tree.heading(col, text=title, anchor="w")
            tree.column(col, width=width, minwidth=30 if col == "favorite" else 75, stretch=col != "favorite", anchor="w")
        for status, color in {"available": "#a7f3be", "unclaimed": "#d1eda4", "taken": "#718c7c", "error": "#e7c582", "blocked": "#ed9d9d"}.items():
            tree.tag_configure(status, foreground=color)
        return tree

    def _build_studio(self, page):
        page.grid_columnconfigure(1, weight=1)
        page.grid_rowconfigure(0, weight=1)
        left = ctk.CTkFrame(page, fg_color=CARD, corner_radius=12, width=324, border_width=1, border_color=BORDER)
        left.grid(row=0, column=0, sticky="ns", padx=(0, 18))
        left.grid_propagate(False)
        left.grid_columnconfigure(0, weight=1)
        left.grid_rowconfigure(0, weight=1)
        controls = ctk.CTkScrollableFrame(left, fg_color="transparent", width=286, scrollbar_button_color=BORDER)
        controls.grid(row=0, column=0, sticky="nsew", padx=12, pady=(6, 0))
        self._section(controls, "01 / DEIN GENERATOR")
        self.combo(controls, self.config_vars["mode"], list(MODES.values()), self._mode_changed).pack(fill="x")
        presets = ctk.CTkFrame(controls, fg_color="transparent")
        presets.pack(fill="x", pady=(10, 0))
        for i, (title, mode, length) in enumerate((("3L", "letters", 3), ("4L", "letters", 4), ("4C", "characters", 4), ("4N", "numbers", 4))):
            self.button(presets, title, lambda m=mode, n=length: self._preset(m, n), width=57).pack(side="left", expand=True, fill="x", padx=(0, 4 if i < 3 else 0))
        self.label(controls, "L = Buchstaben   C = a–z, 0–9, _   N = Ziffern", 10, MUTED).pack(anchor="w", pady=(6, 0))
        self._pair(controls, ("Länge von", "min_length"), ("bis · inkl. Anhängen", "max_length"))
        self._field(controls, "Anzahl · max. 20.000 pro Stapel", "count")
        self.dynamic = ctk.CTkFrame(controls, fg_color="transparent", height=1)
        self.dynamic.pack(fill="x")
        self._section(controls, "02 / DEIN FEINSCHLIFF")
        self._pair(controls, ("Präfix", "prefix"), ("Suffix", "suffix"))
        self._field(controls, "Muss enthalten", "contains")
        self._field(controls, "Zeichen ausschließen", "excludes")
        self._field(controls, "Wörter ausschließen · Komma getrennt", "blocked")
        self._field(controls, "Schreibweise", "case", list(CASES))
        self._field(controls, "Max. gleiche Zeichen in Folge · 0 = egal", "max_repeat")
        for title, key in (("Ohne 0, O, 1, I, L", "no_ambiguous"), ("Leetspeak · a → 4, e → 3 …", "leet")):
            ctk.CTkCheckBox(controls, text=title, variable=self.config_vars[key], font=("Segoe UI", 11), checkbox_width=18,
                            checkbox_height=18, fg_color="#79ad69", hover_color="#639355", border_color=MUTED).pack(anchor="w", pady=(13, 0))
        self._section(controls, "03 / REPRODUZIERBAR SUCHEN")
        self._field(controls, "Reihenfolge", "order", ["Zufällig", "Fortlaufend"])
        self._field(controls, "Startposition · für fortlaufende Stapel", "offset")
        self._field(controls, "Zufalls-Seed · optional", "seed")
        saved = ctk.CTkFrame(controls, fg_color="transparent")
        saved.pack(fill="x", pady=(15, 18))
        self.button(saved, "Preset speichern", self._save_preset, width=120).pack(side="left", expand=True, fill="x", padx=(0, 4))
        self.button(saved, "Preset laden", self._load_preset, width=120).pack(side="left", expand=True, fill="x")
        self.generate_button = self.button(left, "✦   Namen generieren", self._generate, primary=True)
        self.generate_button.grid(row=1, column=0, sticky="ew", padx=16, pady=16)
        self._mode_changed()
        right = ctk.CTkFrame(page, fg_color="transparent")
        right.grid(row=0, column=1, sticky="nsew")
        right.grid_columnconfigure(0, weight=1)
        right.grid_rowconfigure(3, weight=1)
        stats = ctk.CTkFrame(right, fg_color="transparent")
        stats.grid(row=0, column=0, sticky="ew", pady=(0, 15))
        stats.grid_columnconfigure((0, 1, 2, 3), weight=1, uniform="stat")
        self.stat_values = []
        for i, (title, color) in enumerate((("KANDIDATEN", TEXT), ("UNBELEGT*", ACCENT), ("BESTÄTIGT FREI", "#9bdbc6"), ("GEPRÜFT", MUTED))):
            card = ctk.CTkFrame(stats, fg_color=CARD, corner_radius=10, border_width=1, border_color=BORDER)
            card.grid(row=0, column=i, sticky="ew", padx=(0 if i == 0 else 5, 0 if i == 3 else 5))
            self.label(card, title, 9, MUTED, True).pack(anchor="w", padx=12, pady=(13, 0))
            value = self.label(card, "0", 27, color, True)
            value.pack(anchor="w", padx=12, pady=(1, 12))
            self.stat_values.append(value)
        action = ctk.CTkFrame(right, fg_color=CARD, corner_radius=10, border_width=1, border_color=BORDER)
        action.grid(row=1, column=0, sticky="ew", pady=(0, 13))
        action.grid_columnconfigure(0, weight=1)
        self.scan_label = self.label(action, "DEIN SUCHLAUF", 11, TEXT, True, anchor="w")
        self.scan_label.grid(row=0, column=0, sticky="ew", padx=15, pady=(13, 0))
        self.scan_hint = self.label(action, "Noch kein Scan · öffentliche Profilprüfung", 10, MUTED, anchor="w")
        self.scan_hint.grid(row=1, column=0, sticky="ew", padx=15, pady=(3, 0))
        self.start_button = self.button(action, "▶  Scan starten", self._start, primary=True, width=125)
        self.start_button.grid(row=0, column=1, rowspan=2, padx=(5, 5), pady=(13, 0))
        self.pause_button = self.button(action, "Ⅱ", self._pause, width=34, state="disabled")
        self.pause_button.grid(row=0, column=2, rowspan=2, pady=(13, 0), padx=(0, 5))
        self.stop_button = self.button(action, "■", self._stop, width=34, state="disabled")
        self.stop_button.grid(row=0, column=3, rowspan=2, pady=(13, 0), padx=(0, 15))
        self.progress = ctk.CTkProgressBar(action, height=4, fg_color=BORDER, progress_color=ACCENT)
        self.progress.grid(row=2, column=0, columnspan=4, sticky="ew", padx=15, pady=(14, 14))
        self.progress.set(0)
        toolbar = ctk.CTkFrame(right, fg_color="transparent")
        toolbar.grid(row=2, column=0, sticky="ew", pady=(0, 8))
        toolbar.grid_columnconfigure(0, weight=1)
        self.label(toolbar, "SUCHE", 10, MUTED, True).grid(row=0, column=0, padx=(0, 8))
        toolbar.grid_columnconfigure(0, weight=0)
        toolbar.grid_columnconfigure(1, weight=1)
        self.search_entry = self.entry(toolbar, self.search_var)
        self.search_entry.grid(row=0, column=1, sticky="ew", padx=(0, 8))
        self.combo(toolbar, self.filter_var, ["Alle", "Ungeprüft", "Unbelegt*", "Verfügbar ✓", "Belegt", "Gesperrt", "Fehler", "Favoriten"], width=145).grid(row=0, column=2)
        table_card = ctk.CTkFrame(right, fg_color=CARD, corner_radius=10, border_width=1, border_color=BORDER)
        table_card.grid(row=3, column=0, sticky="nsew")
        table_card.grid_columnconfigure(0, weight=1)
        table_card.grid_rowconfigure(1, weight=1)
        table_header = ctk.CTkFrame(table_card, fg_color="transparent")
        table_header.grid(row=0, column=0, sticky="ew", padx=15, pady=(12, 10))
        self.label(table_header, "DEINE NAMEN", 11, TEXT, True).pack(side="left")
        self.table_count = self.label(table_header, "", 10, MUTED)
        self.table_count.pack(side="right")
        self.table = self._tree(table_card, ("favorite", "name", "type", "status"), ("☆", "USERNAME", "TYP", "STATUS"), (35, 160, 115, 145))
        self.table.grid(row=1, column=0, sticky="nsew", padx=(8, 0), pady=(0, 8))
        scroll = ctk.CTkScrollbar(table_card, command=self.table.yview, width=12, button_color=BORDER)
        scroll.grid(row=1, column=1, sticky="ns", pady=(0, 8))
        self.table.configure(yscrollcommand=scroll.set)
        self.table.bind("<<TreeviewSelect>>", self._select_name)
        self.table.bind("<Double-1>", lambda _: self._name_action("open"))
        self.table.bind("<Button-1>", self._table_click)
        self.table.bind("<Return>", lambda _: self._name_action("open"))
        self.table.bind("<space>", lambda _: self._name_action("favorite"))
        for column in ("name", "type", "status"):
            self.table.heading(column, command=lambda c=column: self._sort_table(c))
        details = ctk.CTkFrame(right, fg_color=CARD, corner_radius=10, border_width=1, border_color=BORDER)
        details.grid(row=4, column=0, sticky="ew", pady=(10, 0))
        details.grid_columnconfigure(0, weight=1)
        self.selected_name = self.label(details, "Dein nächster Fund wartet.", 17, TEXT, True, anchor="w")
        self.selected_name.grid(row=0, column=0, sticky="ew", padx=14, pady=(12, 0))
        self.selected_detail = self.label(details, "Namen auswählen für Details und NameMC.", 10, MUTED, wraplength=370, justify="left", anchor="w")
        self.selected_detail.grid(row=1, column=0, sticky="ew", padx=14, pady=(2, 12))
        buttons = ctk.CTkFrame(details, fg_color="transparent")
        buttons.grid(row=0, column=1, rowspan=2, padx=12, pady=12)
        for text, action, width in (("☆", "favorite", 32), ("Kopieren", "copy", 72), ("NameMC ↗", "open", 95)):
            self.button(buttons, text, lambda a=action: self._name_action(a), width=width).pack(side="left", padx=(0, 5))
        export = ctk.CTkFrame(right, fg_color="transparent")
        export.grid(row=5, column=0, sticky="ew", pady=(10, 0))
        self.button(export, "↗  Ergebnisordner", self._open_folder, width=138).pack(side="left", padx=(0, 7))
        self.button(export, "Export", self._export, width=75).pack(side="left", padx=(0, 7))
        self.button(export, "Kandidaten als TXT", self._export_candidates, width=145).pack(side="right")
        self.label(right, "* Unbelegt = kein Profil gefunden. Sperren / Reservierungen möglich.\nBestätigt frei nur mit optionalem Token. Alle Ergebnisse sind Momentaufnahmen.",
                   10, MUTED, anchor="w", justify="left").grid(row=6, column=0, sticky="ew", pady=(10, 0))

    def _mode_key(self):
        return next((key for key, value in MODES.items() if value == self.config_vars["mode"].get()), "letters")

    def _mode_changed(self, *_):
        for widget in self.dynamic.winfo_children():
            widget.destroy()
        mode = self._mode_key()
        if mode in ("words", "compound"):
            self._field(self.dynamic, "Sprache", "language", list(LANGUAGES))
            self.label(self.dynamic, "Kategorien · keine Auswahl = alle", 11, MUTED).pack(anchor="w", pady=(10, 5))
            cats = ctk.CTkFrame(self.dynamic, fg_color="transparent")
            cats.pack(fill="x")
            for i, (key, title) in enumerate(CATEGORIES.items()):
                ctk.CTkCheckBox(cats, text=title, variable=self.category_vars[key], width=125, font=("Segoe UI", 10),
                                checkbox_width=16, checkbox_height=16, fg_color="#79ad69", border_color=MUTED).grid(row=i // 2, column=i % 2, sticky="w", pady=4)
        elif mode == "custom":
            self._field(self.dynamic, "Eigener Zeichensatz · a–z, 0–9, _", "charset")
        elif mode == "mask":
            self._field(self.dynamic, "Muster · z. B. Zen{n}{n}", "mask")
            self.label(self.dynamic, "{l} Buchstabe   {c} Zeichen   {n} Ziffer\n{v} Vokal   {k} Konsonant\nAndere Zeichen bleiben fest. Länge inkl. Anhängen.", 10, MUTED, justify="left").pack(anchor="w", pady=(6, 0))
        elif mode == "list":
            self.button(self.dynamic, "TXT / CSV importieren", self._import_names).pack(fill="x", pady=(12, 0))
            self.label(self.dynamic, f"{len(self.custom_names):,} Namen geladen · UTF-8\nCSV: Username/name-Spalte oder erste Spalte", 10, MUTED, justify="left").pack(anchor="w", pady=(6, 0))

    def _config(self):
        data = {key: var.get() for key, var in self.config_vars.items()}
        data["mode"] = self._mode_key()
        for key in ("min_length", "max_length", "count", "max_repeat", "offset"):
            try:
                data[key] = int(data[key])
            except ValueError:
                raise ValueError(f"Bitte eine ganze Zahl bei {key} eingeben.") from None
        data.update(language=LANGUAGES[data["language"]], case=CASES[data["case"]],
                    order="random" if data["order"] == "Zufällig" else "sequential",
                    categories=[key for key, var in self.category_vars.items() if var.get()])
        return GeneratorConfig(**data)

    def _apply_config(self, data):
        c = GeneratorConfig(**{key: value for key, value in data.items() if key in {f.name for f in fields(GeneratorConfig)}})
        mapped = asdict(c)
        mapped.update(mode=MODES[c.mode], language=next(k for k, v in LANGUAGES.items() if v == c.language),
                      case=next(k for k, v in CASES.items() if v == c.case), order="Zufällig" if c.order == "random" else "Fortlaufend")
        for key, var in self.config_vars.items():
            var.set(mapped[key])
        for key, var in self.category_vars.items():
            var.set(key in c.categories)
        self._mode_changed()

    def _preset(self, mode, length):
        if self.busy or self.generating:
            return self._notify("Zuerst den laufenden Vorgang beenden.")
        self._apply_config(asdict(GeneratorConfig(mode=mode, min_length=length, max_length=length)))
        self._generate()

    def _generate(self):
        if self.busy or self.generating:
            return self._notify("Zuerst den laufenden Vorgang beenden.")
        try:
            config = self._config()
        except (ValueError, KeyError) as exc:
            return messagebox.showerror("Generator prüfen", str(exc), parent=self)
        self.pending_generation_config = asdict(config)
        self.generating = True
        self.generate_button.configure(state="disabled", text="Wird generiert …")
        self.start_button.configure(state="disabled")
        self._notify("Deine nächste Auswahl entsteht …")
        custom = tuple(self.custom_names)
        def work():
            try:
                self.events.put(("generated", generate(config, custom)))
            except Exception as exc:
                self.events.put(("generation_error", str(exc)))
        threading.Thread(target=work, daemon=True).start()

    def _generated(self, generation):
        self.generated_config = self.pending_generation_config
        self.names, self.results, self.scan_id = generation.names, {}, None
        self.progress.set(0)
        self.scan_label.configure(text="DEINE VORSCHAU")
        self.scan_hint.configure(text=f"{len(self.names):,} Namen bereit · noch ungeprüft".replace(",", "."))
        self.selected_name.configure(text="Dein nächster Fund wartet.")
        self.selected_detail.configure(text="Namen auswählen für Details und NameMC.")
        self._render_table()
        self._update_stats()
        self._notify(f"Suchraum: {generation.space:,} · {generation.note}".replace(",", "."))

    def _start(self, existing=None):
        if self.busy or self.generating:
            return self._notify("Es läuft bereits ein Vorgang.")
        if not self.names and not existing:
            return self._notify("Zuerst Namen generieren oder importieren.")
        try:
            delay = float(self.delay_var.get())
            if not 1 <= delay <= 60:
                raise ValueError("API-Abstand: 1 bis 60 Sekunden.")
            if existing:
                scan_id, names = existing, self.store.pending(existing)
            else:
                scan_id = self.store.create_scan(GeneratorConfig(**self.generated_config), self.names, self.output_var.get())
                names = self.names.copy()
                self.results = {}
            if not names:
                return self._notify("Dieser Scan ist vollständig. Keine offenen Namen oder Prüffehler.")
            self.store.set_state(scan_id, "running")
        except (OSError, ValueError) as exc:
            return messagebox.showerror("Scan konnte nicht starten", str(exc), parent=self)
        self.scan_id, self.busy = scan_id, True
        self.checker = checker = NameChecker(delay, self.token_var.get(), on_notice=lambda text: self.events.put(("notice", text)))
        self._set_running(True)
        self._render_table()
        self._update_stats()
        self.scan_label.configure(text="SCAN LÄUFT  /  MOJANG API")
        self.scan_hint.configure(text=f"{len(names):,} Namen · " + ("Token-Prüfung, mind. 16 s" if self.token_var.get().strip() else f"{delay:g} s API-Abstand"))
        self._notify("Ergebnisordner erstellt. Jeder Treffer wird sofort gespeichert.")
        root = self.store.root
        def work():
            store, error = None, ""
            try:
                store = Store(root)
                def record(result):
                    store.record(scan_id, result)
                    self.events.put(("result", result))
                checker.run(names, record)
            except Exception as exc:
                error = str(exc)
            finally:
                if store:
                    try:
                        store.set_state(scan_id, "interrupted" if error or checker.stop_event.is_set() or checker.auth_failed else "complete")
                        store.export(scan_id)
                    except Exception as exc:
                        error = str(exc)
                    store.close()
                self.events.put(("done", error))
        threading.Thread(target=work, daemon=True).start()

    def _set_running(self, running):
        self.start_button.configure(state="disabled" if running else "normal")
        self.generate_button.configure(state="disabled" if running else "normal")
        self.pause_button.configure(state="normal" if running else "disabled", text="Ⅱ")
        self.stop_button.configure(state="normal" if running else "disabled")

    def _pause(self):
        if not self.busy:
            return
        paused = self.checker.pause_event.is_set()
        self.checker.pause() if paused else self.checker.resume()
        self.pause_button.configure(text="▶" if paused else "Ⅱ")
        self.scan_label.configure(text="SCAN PAUSIERT" if paused else "SCAN LÄUFT  /  MOJANG API")
        self._notify("Pausiert. Laufende Anfrage wird noch gesichert." if paused else "Scan fortgesetzt.")

    def _stop(self):
        if self.busy:
            self.checker.stop()
            self.scan_label.configure(text="SCAN WIRD GESPEICHERT …")
            self._notify("Stop angefordert. Fortsetzen ist über den Verlauf möglich.")

    def _poll(self):
        try:
            for _ in range(200):
                kind, data = self.events.get_nowait()
                if kind in ("generated", "generation_error"):
                    self.generating = False
                    self.generate_button.configure(state="normal", text="✦   Namen generieren")
                    self.start_button.configure(state="normal")
                    if kind == "generated":
                        self._generated(data)
                    else:
                        messagebox.showerror("Generator prüfen", data, parent=self)
                elif kind == "result":
                    self.results[data.name.lower()] = data
                    self.dirty = True
                elif kind == "notice":
                    self._notify(data)
                elif kind == "done":
                    self.busy = False
                    self._set_running(False)
                    self.scan_label.configure(text="SCAN GESPEICHERT")
                    self.scan_hint.configure(text=f"{len(self.results)} geprüft · {len(self.store.pending(self.scan_id))} offen / erneut prüfbar")
                    self._notify("Fehler: " + data if data else "Gespeichert: TXT, CSV, JSON und klickbare NameMC-Liste.")
                    if data:
                        messagebox.showerror("Scan unterbrochen", data, parent=self)
                    self.dirty = True
                    if self.closing:
                        return self._finish_close()
        except queue.Empty:
            pass
        if self.dirty:
            self._render_table()
            self._update_stats()
            self._select_name()
            self.dirty = False
        self.after(150, self._poll)

    def _update_stats(self):
        counts = Counter(r.status for r in self.results.values())
        for widget, value in zip(self.stat_values, (len(self.names), counts["unclaimed"], counts["available"], len(self.results))):
            widget.configure(text=f"{value:,}".replace(",", "."))
        self.progress.set(len(self.results) / len(self.names) if self.names else 0)

    def _render_table(self):
        selected = self.table.selection()
        query, filter_value = self.search_var.get().lower().strip(), self.filter_var.get()
        favorites = {n.lower() for n in self.store.favorites()}
        mapping = {"Unbelegt*": "unclaimed", "Verfügbar ✓": "available", "Belegt": "taken", "Gesperrt": "blocked", "Fehler": "error", "Ungeprüft": "pending"}
        wanted = []
        for name in self.names:
            result = self.results.get(name.lower())
            status = result.status if result else "pending"
            if query and query not in name.lower():
                continue
            if filter_value == "Favoriten" and name.lower() not in favorites:
                continue
            if filter_value in mapping and mapping[filter_value] != status:
                continue
            wanted.append((name, status))
        visible = wanted[:2000]
        visible_ids = {name.lower() for name, _ in visible}
        old_ids = set(self.table.get_children())
        for iid in old_ids - visible_ids:
            self.table.delete(iid)
        for index, (name, status) in enumerate(visible):
            iid = name.lower()
            values = ("★" if iid in favorites else "☆", name, describe(name), STATUSES.get(status, "Ungeprüft"))
            if iid in old_ids:
                self.table.item(iid, values=values, tags=(status,))
            else:
                self.table.insert("", "end", iid=iid, values=values, tags=(status,))
            self.table.move(iid, "", index)
        if selected and selected[0] in visible_ids:
            self.table.selection_set(selected[0])
        self.table_count.configure(text=f"{len(wanted):,} Treffer" + (" · erste 2.000 sichtbar" if len(wanted) > 2000 else ""))

    def _sort_table(self, column):
        reverse = getattr(self, "last_sort", None) == (column, False)
        self.last_sort = (column, reverse)
        if column == "status":
            key = lambda n: STATUSES.get(self.results[n.lower()].status, "") if n.lower() in self.results else "Ungeprüft"
        elif column == "type":
            key = lambda n: (len(n), describe(n), n.lower())
        else:
            key = str.lower
        self.names.sort(key=key, reverse=reverse)
        self._render_table()

    def _selected(self):
        selection = self.table.selection()
        return self.table.item(selection[0], "values")[1] if selection else None

    def _select_name(self, *_):
        name = self._selected()
        if name:
            result = self.results.get(name.lower())
            self.selected_name.configure(text=name)
            detail = result.detail + " · " + result.checked_at.replace("T", " ").replace("+00:00", " UTC") if result else f"{describe(name)} · noch ungeprüft"
            self.selected_detail.configure(text=detail)

    def _table_click(self, event):
        if self.table.identify_column(event.x) == "#1":
            row = self.table.identify_row(event.y)
            if row:
                self.table.selection_set(row)
                self.after_idle(lambda: self._name_action("favorite"))

    def _name_action(self, action):
        name = self._selected()
        if not name:
            return self._notify("Bitte zuerst einen Namen auswählen.")
        if action == "favorite":
            self.store.toggle_favorite(name)
            self._render_table()
            self._notify(f"Favoriten aktualisiert: {name}")
        elif action == "copy":
            self.clipboard_clear()
            self.clipboard_append(name)
            self._notify(f"{name} kopiert.")
        elif action == "open":
            webbrowser.open(f"https://namemc.com/profile/{name}")

    def _open_folder(self):
        try:
            path = self.store.folder(self.scan_id) if self.scan_id else Path(self.output_var.get())
            path.mkdir(parents=True, exist_ok=True)
            os.startfile(str(path.resolve()))
        except OSError as exc:
            messagebox.showerror("Ordner öffnen", str(exc), parent=self)

    def _export(self):
        if not self.scan_id:
            return self._notify("Für Ergebnisse zuerst einen Scan starten. Vorschau über Kandidaten als TXT speichern.")
        if self.busy:
            return self._notify("Treffer werden laufend gespeichert. Gesamtexport ist nach Stoppen bereit.")
        try:
            self.store.export(self.scan_id)
            self._open_folder()
        except OSError as exc:
            messagebox.showerror("Export fehlgeschlagen", str(exc), parent=self)

    def _export_candidates(self):
        if not self.names:
            return self._notify("Zuerst Namen generieren.")
        path = filedialog.asksaveasfilename(parent=self, title="Kandidaten speichern", defaultextension=".txt", initialfile="kandidaten.txt", filetypes=[("Text", "*.txt")])
        if path:
            try:
                Path(path).write_text("\n".join(self.names) + "\n", encoding="utf-8")
                self._notify(f"{len(self.names)} Kandidaten gespeichert.")
            except OSError as exc:
                messagebox.showerror("Speichern fehlgeschlagen", str(exc), parent=self)

    def _import_names(self):
        path = filedialog.askopenfilename(parent=self, title="Eigene Namen laden", filetypes=[("Namenslisten", "*.txt *.csv"), ("Alle Dateien", "*.*")])
        if not path:
            return
        try:
            if Path(path).stat().st_size > 10 * 1024 * 1024:
                raise ValueError("Bitte eine Datei unter 10 MB verwenden.")
            text = Path(path).read_text(encoding="utf-8-sig")
            if Path(path).suffix.lower() == ".csv":
                try:
                    dialect = csv.Sniffer().sniff(text[:4096], delimiters=",;\t")
                except csv.Error:
                    dialect = csv.excel
                rows = list(csv.reader(text.splitlines(), dialect))
                index = next((i for i, cell in enumerate(rows[0]) if cell.lower().strip() in ("username", "name")), 0) if rows else 0
                has_header = bool(rows and rows[0][index].lower().strip() in ("username", "name"))
                self.custom_names = [row[index].strip() for row in rows[int(has_header):] if len(row) > index]
            else:
                self.custom_names = [line.split("\t")[0].strip() for line in text.splitlines() if line.strip()]
            self._mode_changed()
            self._notify(f"{len(self.custom_names)} Ausgangsnamen geladen. Mit Generieren werden Filter angewendet.")
        except (OSError, ValueError) as exc:
            messagebox.showerror("Import fehlgeschlagen", str(exc), parent=self)

    def _save_preset(self):
        try:
            config = self._config()
            path = filedialog.asksaveasfilename(parent=self, title="Generator-Preset speichern", defaultextension=".json", initialfile="mein-preset.json", filetypes=[("Preset", "*.json")])
            if path:
                atomic_json(path, asdict(config))
                self._notify("Preset gespeichert. Importierte Namenslisten sind separat zu laden.")
        except (OSError, ValueError) as exc:
            messagebox.showerror("Preset speichern", str(exc), parent=self)

    def _load_preset(self):
        path = filedialog.askopenfilename(parent=self, title="Generator-Preset laden", filetypes=[("Preset", "*.json")])
        if path:
            try:
                if Path(path).stat().st_size > 65536:
                    raise ValueError("Preset ist zu groß.")
                data = json.loads(Path(path).read_text(encoding="utf-8"))
                generate(GeneratorConfig(**data))
                self._apply_config(data)
                self._notify("Preset geladen. Generieren aktualisiert die Vorschau.")
            except (OSError, ValueError, KeyError, TypeError, StopIteration) as exc:
                messagebox.showerror("Ungültiges Preset", str(exc), parent=self)

    def _build_collection(self, page, kind):
        page.grid_columnconfigure(0, weight=1)
        page.grid_rowconfigure(1, weight=1)
        if kind == "favorites":
            text = "Deine Shortlist bleibt über alle Scans erhalten. Ein Stern speichert einen Namen, keinen Verfügbarkeitsstatus."
            columns, titles, widths = ("name", "type", "link"), ("USERNAME", "TYP", "NAMEMC"), (240, 180, 400)
            actions = (("NameMC ↗", "open"), ("Aus Favoriten entfernen", "remove"), ("Alle erneut prüfen", "check"), ("Alle mit Links kopieren", "copy"))
            callback = self._favorite_action
        else:
            text = "Jeder Check wird sofort gesichert. Offene Namen und Prüffehler kannst du hier fortsetzen."
            columns, titles, widths = ("created", "mode", "state", "checked", "found"), ("ERSTELLT", "GENERATOR", "STATUS", "GEPRÜFT", "FUNDE"), (180, 200, 150, 85, 85)
            actions = (("Ergebnisse ansehen", "load"), ("Offene / Fehler fortsetzen", "resume"), ("Ordner öffnen", "folder"), ("Export wiederherstellen", "export"))
            callback = self._history_action
        self.label(page, text, 12, MUTED, anchor="w").grid(row=0, column=0, sticky="ew", pady=(0, 15))
        tree = self._tree(page, columns, titles, widths)
        tree.grid(row=1, column=0, sticky="nsew")
        scroll = ctk.CTkScrollbar(page, command=tree.yview, width=12)
        scroll.grid(row=1, column=1, sticky="ns")
        tree.configure(yscrollcommand=scroll.set)
        setattr(self, kind + "_table", tree)
        tree.bind("<Double-1>", lambda _: callback("open" if kind == "favorites" else "load"))
        row = ctk.CTkFrame(page, fg_color="transparent")
        row.grid(row=2, column=0, sticky="ew", pady=15)
        for text, action in actions:
            self.button(row, text, lambda a=action: callback(a)).pack(side="left", padx=(0, 8))

    def _refresh_favorites(self):
        self.favorites_table.delete(*self.favorites_table.get_children())
        for name in self.store.favorites():
            self.favorites_table.insert("", "end", values=(name, describe(name), f"https://namemc.com/profile/{name}"))

    def _favorite_action(self, action):
        selection = self.favorites_table.selection()
        name = self.favorites_table.item(selection[0], "values")[0] if selection else None
        if action == "open" and name:
            webbrowser.open(f"https://namemc.com/profile/{name}")
        elif action == "remove" and name:
            self.store.toggle_favorite(name)
            self._refresh_favorites()
            self._render_table()
        elif action == "copy":
            self.clipboard_clear()
            self.clipboard_append("\n".join(f"{n}\thttps://namemc.com/profile/{n}" for n in self.store.favorites()))
            self._notify("Favoriten mit NameMC-Links kopiert.")
        elif action == "check":
            if self.busy or self.generating:
                return self._notify("Zuerst den laufenden Vorgang beenden.")
            names = self.store.favorites()
            if not names:
                return self._notify("Noch keine Favoriten. Sterne in der Namensliste anklicken.")
            self.names, self.results, self.scan_id = names, {}, None
            self.generated_config = asdict(GeneratorConfig(mode="list", max_length=16))
            self._show("studio")
            self._render_table()
            self._update_stats()
            self._start()

    def _refresh_history(self):
        self.history_table.delete(*self.history_table.get_children())
        for scan_id, created, mode, state, checked, found in self.store.history():
            state_label = {"complete": "Abgeschlossen", "interrupted": "Unterbrochen", "running": "Läuft / pausiert" if self.busy and scan_id == self.scan_id else "Unterbrochen"}.get(state, state)
            self.history_table.insert("", "end", iid=scan_id, values=(created.replace("T", " "), MODES.get(mode, mode), state_label, checked, found or 0))

    def _history_action(self, action):
        selection = self.history_table.selection()
        if not selection:
            return self._notify("Bitte einen Scan im Verlauf auswählen.")
        scan_id = selection[0]
        try:
            if action == "folder":
                return os.startfile(str(self.store.folder(scan_id)))
            if action == "export":
                if self.busy:
                    return self._notify("Für den Gesamtexport laufenden Scan zuerst stoppen.")
                self.store.export(scan_id)
                return self._notify("Export aus der lokalen Datenbank wiederhergestellt.")
            if self.busy or self.generating:
                return self._notify("Zuerst den laufenden Vorgang beenden.")
            row = self.store.db.execute("SELECT config,names FROM scans WHERE id=?", (scan_id,)).fetchone()
            self.generated_config = json.loads(row[0])
            self._apply_config(self.generated_config)
            self.names = json.loads(row[1])
            self.results = {r.name.lower(): r for r in self.store.results(scan_id)}
            self.scan_id = scan_id
            self.scan_label.configure(text="GESPEICHERTER SCAN")
            self.scan_hint.configure(text=scan_id)
            self._show("studio")
            self._render_table()
            self._update_stats()
            if action == "resume":
                self._start(existing=scan_id)
        except (OSError, ValueError) as exc:
            messagebox.showerror("Scan öffnen", str(exc), parent=self)

    def _build_settings(self, page):
        scroll = ctk.CTkScrollableFrame(page, fg_color=CARD, corner_radius=12, border_width=1, border_color=BORDER)
        scroll.pack(fill="both", expand=True)
        inner = ctk.CTkFrame(scroll, fg_color="transparent")
        inner.pack(anchor="w", fill="x", padx=24, pady=(0, 25))
        self._section(inner, "DEIN WORKSPACE")
        self.label(inner, "Automatischer Ergebnisordner", 13, TEXT, True).pack(anchor="w", pady=(2, 6))
        row = ctk.CTkFrame(inner, fg_color="transparent")
        row.pack(fill="x")
        self.entry(row, self.output_var).pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.button(row, "Auswählen", self._choose_output, width=110).pack(side="right")
        self.label(inner, "Pro Scan: verfügbare und unbelegte Namen getrennt, CSV, JSON und eine klickbare NameMC-Liste.\nJeder Check landet sofort in der lokalen Datenbank. Offene Scans lassen sich nach einem Neustart fortsetzen.",
                   12, MUTED, justify="left").pack(anchor="w", pady=(8, 12))
        self._section(inner, "DEIN LOOK")
        self.label(inner, "Akzentfarbe", 12, MUTED).pack(anchor="w", pady=(0, 5))
        self.combo(inner, self.theme_var, ["Mint", "Ice", "Lavender", "Amber"], lambda _: self._apply_theme(), width=240).pack(anchor="w")
        ctk.CTkSwitch(inner, text="Kompakte Ergebnistabelle", variable=self.compact_var, command=self._apply_theme, progress_color="#79ad69").pack(anchor="w", pady=15)
        self._section(inner, "API & PRÜFGENAUIGKEIT")
        self.label(inner, "Abstand zwischen Anfragen · 1–60 Sekunden", 12, MUTED).pack(anchor="w", pady=(0, 5))
        self.entry(inner, self.delay_var, width=240).pack(anchor="w")
        self.label(inner, "Ein Worker, automatische Wiederholungen, Retry-After und abbrechbare Wartezeiten.\nFür die Token-Prüfung gelten mindestens 16 Sekunden Abstand. Keine Proxy-Rotation.", 12, MUTED, justify="left").pack(anchor="w", pady=(8, 12))
        self.label(inner, "Minecraft-Access-Token · optional, nur für diese Sitzung", 12, TEXT, True).pack(anchor="w", pady=(7, 5))
        self.entry(inner, self.token_var, show="•", width=600).pack(anchor="w", fill="x")
        self.label(inner, "Ohne Token: Profil-Lookup → Unbelegt* oder Belegt.\nMit gültigem Java-Access-Token: Minecraft Services → Verfügbar, Belegt oder Gesperrt / reserviert.\nDer Token wird nur an api.minecraftservices.com geschickt und weder gespeichert noch exportiert.\nEs wird kein Name beansprucht oder geändert. Dieser Checker ist für Minecraft Java Edition.",
                   12, MUTED, justify="left").pack(anchor="w", pady=(8, 15))
        self.button(inner, "Token aus Sitzung entfernen", lambda: self.token_var.set(""), width=240).pack(anchor="w")
        self._section(inner, "LOKALE DATEN")
        self.label(inner, str(self.store.root), 12, MUTED).pack(anchor="w")
        self.label(inner, f"{len(dictionary()):,} kuratierte DE/EN-Ausgangswörter · Namen werden ohne Beachtung der Großschreibung dedupliziert.\nNameMC öffnet sich auf deinen Klick. Keine NameMC-Abfragen im Hintergrund.", 12, MUTED, justify="left").pack(anchor="w", pady=(8, 15))
        self.button(inner, "Einstellungen speichern", self._save_settings, primary=True, width=240).pack(anchor="w", pady=(7, 0))

    def _choose_output(self):
        path = filedialog.askdirectory(parent=self, title="Ordner für Scan-Ergebnisse")
        if path:
            self.output_var.set(path)

    def _apply_theme(self):
        accent = {"Mint": ACCENT, "Ice": "#9cdaff", "Lavender": "#cfb7ff", "Amber": "#ffd18a"}.get(self.theme_var.get(), ACCENT)
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("Studio.Treeview", background=CARD, fieldbackground=CARD, foreground=TEXT, borderwidth=0,
                        lightcolor=CARD, darkcolor=CARD, bordercolor=CARD,
                        rowheight=29 if self.compact_var.get() else 39, font=("Segoe UI", 11))
        style.configure("Studio.Treeview.Heading", background=CARD, foreground=MUTED, relief="flat", borderwidth=0,
                        padding=(8, 9), font=("Segoe UI", 9, "bold"))
        style.map("Studio.Treeview", background=[("selected", "#2c4234")], foreground=[("selected", "#e7ffec")])
        style.map("Studio.Treeview.Heading", background=[("active", "#223128")])
        self.generate_button.configure(fg_color=accent, hover_color=accent)
        self.start_button.configure(fg_color=accent, hover_color=accent)
        self.progress.configure(progress_color=accent)
        self.stat_values[1].configure(text_color=accent)

    def _save_settings(self):
        try:
            delay = float(self.delay_var.get())
            if not 1 <= delay <= 60:
                raise ValueError("API-Abstand: 1–60 Sekunden.")
            Path(self.output_var.get()).mkdir(parents=True, exist_ok=True)
            self.store.save_settings({"output": self.output_var.get(), "delay": delay, "accent": self.theme_var.get(), "compact": self.compact_var.get()})
            self._notify("Einstellungen gespeichert.")
        except (OSError, ValueError) as exc:
            messagebox.showerror("Einstellungen prüfen", str(exc), parent=self)

    def _show(self, name):
        for key, page in self.pages.items():
            page.grid_forget()
            self.nav[key].configure(fg_color="#263d2d" if key == name else "transparent", text_color=ACCENT if key == name else MUTED)
        self.pages[name].grid(row=1, column=0, sticky="nsew")
        titles = {"studio": ("Kleine Namen. Große Funde.", "Generieren. Prüfen. Sammeln. Dein neuer Name beginnt hier."),
                  "favorites": ("Nur die besten bleiben.", "Deine persönliche Sammlung – über alle Scans hinweg."),
                  "history": ("Kein Fund geht verloren.", "Gesicherte Suchläufe, offene Namen und alle Exporte an einem Ort."),
                  "settings": ("Dein Studio. Deine Regeln.", "Passe deinen Workspace, deinen Look und deine Prüfung an.")}
        self.heading.configure(text=titles[name][0])
        self.subheading.configure(text=titles[name][1])
        if name == "favorites":
            self._refresh_favorites()
        elif name == "history":
            self._refresh_history()

    def _notify(self, text):
        self.status_var.set(text)

    def _close(self):
        if self.busy:
            self.closing = True
            self._stop()
            self._notify("Daten werden gesichert. Das Fenster schließt nach der laufenden Anfrage.")
        else:
            self._finish_close()

    def _finish_close(self):
        self.store.close()
        self.destroy()


def main():
    ZenMcCheckerApp().mainloop()


if __name__ == "__main__":
    main()
