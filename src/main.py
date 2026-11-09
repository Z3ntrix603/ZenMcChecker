#!/usr/bin/env python3
"""
ZenMcChecker — Advanced Minecraft Rare Username Availability Checker
Version: 1.0.1
Author: Z3ntrix603
License: MIT

Checks username availability against the official Mojang API and NameMC.
Features borderless, modern dark GUI with zero unnecessary clutter.
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
import threading
import requests
import csv
import os
import sys
import time
import string
import itertools
import random
import re
import webbrowser
import queue
from datetime import datetime
from typing import List

# Setup import path for wordlists
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

try:
    from wordlists import WORDLISTS
except ImportError:
    from src.wordlists import WORDLISTS

# ═══════════════════════════════════════════════════════════════
# DESIGN SYSTEM (Borderless, Minimalist, Dark Slate)
# ═══════════════════════════════════════════════════════════════
BG_APP      = "#0b0c10"  # Deep midnight background
BG_SIDEBAR  = "#12131a"  # Sidebar panel
BG_CARD     = "#181924"  # Cards and containers
BG_INPUT    = "#101118"  # Textboxes and input fields
BG_BUTTON   = "#222433"  # Standard secondary button

ACCENT      = "#3b82f6"  # Vibrant Electric Blue
ACCENT_HOV  = "#2563eb"
GREEN       = "#10b981"  # Available / Unclaimed
GREEN_BG    = "#06281e"
RED         = "#ef4444"  # Taken / Claimed
RED_BG      = "#2d0d12"
ORANGE      = "#f59e0b"

TEXT_MAIN   = "#f3f4f6"  # Primary white
TEXT_MUTED  = "#9ca3af"  # Secondary muted grey
TEXT_DARK   = "#4b5563"

FONT_FAMILY = "Segoe UI"
MOJANG_API  = "https://api.mojang.com/users/profiles/minecraft/{}"
NAMEMC_URL  = "https://namemc.com/profile/{}"
MC_NAME_RE  = re.compile(r"^[a-zA-Z0-9_]{3,16}$")
VERSION     = "1.0.1"


# ═══════════════════════════════════════════════════════════════
# BACKEND: NAME GENERATOR
# ═══════════════════════════════════════════════════════════════
class NameGenerator:
    """Generates rare, high-value Minecraft usernames based on curated wordlists."""

    def __init__(self):
        self.wl = WORDLISTS

    def filter_len(self, names, min_len, max_len):
        """Filter names by length and Minecraft regex validity."""
        return [n for n in names if min_len <= len(n) <= max_len and MC_NAME_RE.match(n)]

    def english_words(self, categories, min_len, max_len):
        """Curated English words from specific categories."""
        res = []
        for cat in categories:
            if cat in self.wl["en"]:
                res.extend(self.wl["en"][cat])
        return sorted(set(self.filter_len(res, min_len, max_len)))

    def german_words(self, categories, min_len, max_len):
        """Curated German words (ASCII-safe)."""
        res = []
        for cat in categories:
            if cat in self.wl["de"]:
                res.extend(self.wl["de"][cat])
        return sorted(set(self.filter_len(res, min_len, max_len)))

    def og_names(self, min_len, max_len):
        """Ultra-rare 2-3 letter dictionary words."""
        names = list(self.wl["en"].get("og_elite", []))
        return sorted(set(self.filter_len(names, min_len, max_len)))

    def semi_og(self, min_len, max_len, limit=1500):
        """Clean two-word compound names (e.g. DarkBlade, FrostKing)."""
        px = self.wl.get("semi_og_prefixes", [])
        sx = self.wl.get("semi_og_suffixes", [])
        res = []
        for p in px:
            for s in sx:
                if p.lower() != s.lower():
                    combo = p + s
                    if min_len <= len(combo) <= max_len and MC_NAME_RE.match(combo):
                        res.append(combo)
                        if len(res) >= limit:
                            return sorted(set(res))
        return sorted(set(res))

    def leet_speak(self, base_list, min_len, max_len):
        """Convert words to clean leet speak (e.g. Blade -> 8l4d3)."""
        m = self.wl.get("leet_map", {})
        res = []
        for name in base_list:
            leet = "".join(m.get(c.lower(), c) for c in name)
            if leet != name and MC_NAME_RE.match(leet):
                res.append(leet)
        return sorted(set(self.filter_len(res, min_len, max_len)))

    def brute_force(self, length, charset="lower", limit=3000):
        """Generate all combinations of a specific character set and length."""
        ch = string.ascii_lowercase
        if charset == "upper":
            ch = string.ascii_uppercase
        elif charset == "alnum":
            ch = string.ascii_lowercase + string.digits

        length = max(3, length)
        res = []
        for combo in itertools.product(ch, repeat=length):
            res.append("".join(combo))
            if len(res) >= limit:
                break
        return res

    def patterns(self, ptype, min_len, max_len):
        """Palindromes, repeating, or sequential character patterns."""
        res = self.wl.get("patterns", {}).get(ptype, [])
        return sorted(set(self.filter_len(res, min_len, max_len)))

    def from_file(self, path, min_len, max_len):
        """Load external custom list from file."""
        res = []
        try:
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    name = line.strip()
                    if name:
                        res.append(name)
        except Exception:
            pass
        return sorted(set(self.filter_len(res, min_len, max_len)))


# ═══════════════════════════════════════════════════════════════
# BACKEND: NAME CHECKER (Mojang API)
# ═══════════════════════════════════════════════════════════════
class NameChecker:
    """Checks Minecraft username availability via Mojang API with rate-limiting."""

    def __init__(self, delay=0.6):
        self.delay = delay
        self.session = requests.Session()
        self.session.headers["User-Agent"] = f"ZenMcChecker/{VERSION}"
        self._stop = threading.Event()
        self._pause = threading.Event()
        self._pause.set()

    def check_one(self, name):
        """Returns True if available, False if taken, None if rate-limited or error."""
        try:
            r = self.session.get(MOJANG_API.format(name), timeout=8)
            if r.status_code == 200:
                return False  # Taken
            elif r.status_code in (204, 404):
                return True   # Available!
            return None       # Rate limit (429) or temporary server issue
        except Exception:
            return None

    def check_batch(self, names, on_result=None, on_progress=None):
        """Iterate over list with exponential backoff retry on rate limit."""
        total = len(names)
        retries = 0
        for i, name in enumerate(names):
            if self._stop.is_set():
                break
            self._pause.wait()

            res = self.check_one(name)
            if res is None:
                retries += 1
                if retries <= 4:
                    wait = min(2 ** retries, 20)
                    time.sleep(wait)
                    res = self.check_one(name)
                if res is None:
                    if on_result:
                        on_result(name, None)
                    if on_progress:
                        on_progress(i + 1, total)
                    continue

            retries = 0
            if on_result:
                on_result(name, res)
            if on_progress:
                on_progress(i + 1, total)

            time.sleep(self.delay)

    def stop(self):
        self._stop.set()

    def pause(self):
        self._pause.clear()

    def resume(self):
        self._pause.set()

    def reset(self):
        self._stop.clear()
        self._pause.set()


# ═══════════════════════════════════════════════════════════════
# GUI APPLICATION
# ═══════════════════════════════════════════════════════════════
class ZenMcCheckerApp(ctk.CTk):
    """Modern borderless desktop GUI application."""

    def __init__(self):
        super().__init__()

        # Window Configuration
        self.title("ZenMcChecker")
        self.geometry("1000x680")
        self.minsize(880, 580)
        self.configure(fg_color=BG_APP)
        ctk.set_appearance_mode("dark")

        # Core State
        self.gen = NameGenerator()
        self.chk = NameChecker()
        self.names: List[str] = []
        self.avail: List[str] = []
        self.taken: List[str] = []
        self.is_checking = False
        self.is_paused = False
        self.q = queue.Queue()

        # Results Directory
        base_dir = os.path.dirname(os.path.abspath(__file__))
        if os.path.basename(base_dir) == "src":
            base_dir = os.path.dirname(base_dir)
        self.results_dir = os.path.join(base_dir, "results")
        os.makedirs(self.results_dir, exist_ok=True)

        # Main Layout Grid
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Build Interface
        self._build_sidebar()
        self._build_content_views()

        # Initialize View
        self._switch_view("gen")
        self._queue_listener()

    # ───────────────────────────────────────────────────────────
    # SIDEBAR
    # ───────────────────────────────────────────────────────────
    def _build_sidebar(self):
        self.sidebar = ctk.CTkFrame(
            self, width=200, corner_radius=0, fg_color=BG_SIDEBAR, border_width=0
        )
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)
        self.sidebar.grid_rowconfigure(5, weight=1)

        # App Title Header
        title_box = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        title_box.grid(row=0, column=0, padx=20, pady=(24, 20), sticky="w")

        ctk.CTkLabel(
            title_box, text="ZenMcChecker",
            font=ctk.CTkFont(family=FONT_FAMILY, size=18, weight="bold"),
            text_color=TEXT_MAIN
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_box, text=f"v{VERSION} • Minecraft Tool",
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
            text_color=TEXT_MUTED
        ).pack(anchor="w", pady=(2, 0))

        # Navigation Buttons
        self.nav_buttons = {}
        nav_items = [
            ("gen", "🎲  Generator"),
            ("chk", "⚡  Checker"),
            ("res", "📁  Results"),
        ]

        for i, (key, label) in enumerate(nav_items):
            btn = ctk.CTkButton(
                self.sidebar, text=label, anchor="w", height=40,
                corner_radius=8, border_width=0,
                font=ctk.CTkFont(family=FONT_FAMILY, size=13),
                fg_color="transparent",
                hover_color=BG_CARD,
                text_color=TEXT_MUTED,
                command=lambda k=key: self._switch_view(k)
            )
            btn.grid(row=i + 1, column=0, padx=12, pady=4, sticky="ew")
            self.nav_buttons[key] = btn

        # Live Status in Sidebar Bottom
        stats_box = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        stats_box.grid(row=6, column=0, padx=20, pady=20, sticky="sew")

        self.sb_stat_gen = ctk.CTkLabel(
            stats_box, text="Generated: 0", font=ctk.CTkFont(family=FONT_FAMILY, size=11),
            text_color=TEXT_MUTED, anchor="w"
        )
        self.sb_stat_gen.pack(fill="x", pady=1)

        self.sb_stat_avail = ctk.CTkLabel(
            stats_box, text="Available: 0", font=ctk.CTkFont(family=FONT_FAMILY, size=11),
            text_color=GREEN, anchor="w"
        )
        self.sb_stat_avail.pack(fill="x", pady=1)

        self.sb_stat_taken = ctk.CTkLabel(
            stats_box, text="Taken: 0", font=ctk.CTkFont(family=FONT_FAMILY, size=11),
            text_color=RED, anchor="w"
        )
        self.sb_stat_taken.pack(fill="x", pady=1)

    def _switch_view(self, key):
        for k, btn in self.nav_buttons.items():
            if k == key:
                btn.configure(fg_color=BG_CARD, text_color=TEXT_MAIN)
            else:
                btn.configure(fg_color="transparent", text_color=TEXT_MUTED)

        self.view_gen.grid_forget()
        self.view_chk.grid_forget()
        self.view_res.grid_forget()

        if key == "gen":
            self.view_gen.grid(row=0, column=0, sticky="nsew")
        elif key == "chk":
            self.view_chk.grid(row=0, column=0, sticky="nsew")
            self.chk_lbl_count.configure(text=f"{len(self.names)} names loaded")
        elif key == "res":
            self.view_res.grid(row=0, column=0, sticky="nsew")
            self._update_results_view()

    # ───────────────────────────────────────────────────────────
    # CONTENT CONTAINER
    # ───────────────────────────────────────────────────────────
    def _build_content_views(self):
        self.content_area = ctk.CTkFrame(self, fg_color=BG_APP, corner_radius=0, border_width=0)
        self.content_area.grid(row=0, column=1, sticky="nsew")
        self.content_area.grid_rowconfigure(0, weight=1)
        self.content_area.grid_columnconfigure(0, weight=1)

        self._build_gen_view()
        self._build_chk_view()
        self._build_res_view()

    # ───────────────────────────────────────────────────────────
    # VIEW 1: GENERATOR
    # ───────────────────────────────────────────────────────────
    def _build_gen_view(self):
        self.view_gen = ctk.CTkFrame(self.content_area, fg_color=BG_APP, border_width=0)
        self.view_gen.grid_columnconfigure(0, weight=1)
        self.view_gen.grid_columnconfigure(1, weight=1)
        self.view_gen.grid_rowconfigure(1, weight=1)

        # Header
        header = ctk.CTkFrame(self.view_gen, fg_color="transparent")
        header.grid(row=0, column=0, columnspan=2, padx=24, pady=(20, 12), sticky="w")
        ctk.CTkLabel(
            header, text="Name Generator",
            font=ctk.CTkFont(family=FONT_FAMILY, size=20, weight="bold"),
            text_color=TEXT_MAIN
        ).pack(anchor="w")

        # LEFT COLUMN: Configuration Card
        left_card = ctk.CTkFrame(self.view_gen, fg_color=BG_CARD, corner_radius=12, border_width=0)
        left_card.grid(row=1, column=0, padx=(24, 10), pady=(0, 24), sticky="nsew")

        # Generation Mode
        ctk.CTkLabel(
            left_card, text="Generation Mode",
            font=ctk.CTkFont(family=FONT_FAMILY, size=13, weight="bold"),
            text_color=TEXT_MAIN
        ).pack(anchor="w", padx=20, pady=(18, 6))

        self.mode_var = ctk.StringVar(value="English Dictionary Words")
        modes = [
            "English Dictionary Words",
            "German Dictionary Words",
            "Combined Words (EN + DE)",
            "OG Names (3-Letter Rare)",
            "Semi-OG Combos (DarkBlade...)",
            "Leet Speak (8l4d3...)",
            "Patterns & Palindromes (aba...)",
            "Brute Force Combinations",
            "Custom Text File"
        ]
        self.cb_mode = ctk.CTkComboBox(
            left_card, values=modes, variable=self.mode_var,
            corner_radius=8, border_width=0, height=36,
            fg_color=BG_INPUT, text_color=TEXT_MAIN,
            dropdown_fg_color=BG_CARD, dropdown_text_color=TEXT_MAIN,
            state="readonly", command=self._on_gen_mode_change
        )
        self.cb_mode.pack(fill="x", padx=20, pady=(0, 14))

        # Length Range (Min & Max)
        ctk.CTkLabel(
            left_card, text="Name Length (Characters)",
            font=ctk.CTkFont(family=FONT_FAMILY, size=13, weight="bold"),
            text_color=TEXT_MAIN
        ).pack(anchor="w", padx=20, pady=(0, 6))

        len_box = ctk.CTkFrame(left_card, fg_color="transparent")
        len_box.pack(fill="x", padx=20, pady=(0, 14))
        len_box.grid_columnconfigure((1, 3), weight=1)

        ctk.CTkLabel(len_box, text="Min:", text_color=TEXT_MUTED).grid(row=0, column=0, padx=(0, 6))
        self.ent_min_len = ctk.CTkEntry(
            len_box, width=50, height=32, corner_radius=6, border_width=0,
            fg_color=BG_INPUT, text_color=TEXT_MAIN, justify="center"
        )
        self.ent_min_len.insert(0, "3")
        self.ent_min_len.grid(row=0, column=1, padx=(0, 14), sticky="w")

        ctk.CTkLabel(len_box, text="Max:", text_color=TEXT_MUTED).grid(row=0, column=2, padx=(0, 6))
        self.ent_max_len = ctk.CTkEntry(
            len_box, width=50, height=32, corner_radius=6, border_width=0,
            fg_color=BG_INPUT, text_color=TEXT_MAIN, justify="center"
        )
        self.ent_max_len.insert(0, "5")
        self.ent_max_len.grid(row=0, column=3, sticky="w")

        # Quick Length Buttons
        len_quick = ctk.CTkFrame(left_card, fg_color="transparent")
        len_quick.pack(fill="x", padx=20, pady=(0, 16))
        for (label, mn, mx) in [("3-Letter (OG)", 3, 3), ("3 to 4", 3, 4), ("3 to 5", 3, 5), ("4 to 6", 4, 6)]:
            btn = ctk.CTkButton(
                len_quick, text=label, height=26, corner_radius=6, border_width=0,
                font=ctk.CTkFont(family=FONT_FAMILY, size=10),
                fg_color=BG_BUTTON, hover_color="#2b2d3f", text_color=TEXT_MUTED,
                command=lambda a=mn, b=mx: self._set_len(a, b)
            )
            btn.pack(side="left", padx=2)

        # Dynamic Options Area
        self.dyn_container = ctk.CTkFrame(left_card, fg_color="transparent")
        self.dyn_container.pack(fill="both", expand=True, padx=20, pady=(0, 14))
        self.custom_file_path = ctk.StringVar()
        self._setup_categories_dyn()

        # Primary Generate Button
        btn_gen = ctk.CTkButton(
            left_card, text="⚡ Generate Names", height=42, corner_radius=8, border_width=0,
            font=ctk.CTkFont(family=FONT_FAMILY, size=13, weight="bold"),
            fg_color=ACCENT, hover_color=ACCENT_HOV, text_color="#ffffff",
            command=self._do_generate
        )
        btn_gen.pack(fill="x", padx=20, pady=(0, 20), side="bottom")

        # RIGHT COLUMN: Preview Card
        right_card = ctk.CTkFrame(self.view_gen, fg_color=BG_CARD, corner_radius=12, border_width=0)
        right_card.grid(row=1, column=1, padx=(10, 24), pady=(0, 24), sticky="nsew")
        right_card.grid_rowconfigure(1, weight=1)
        right_card.grid_columnconfigure(0, weight=1)

        # Preview Header
        pv_top = ctk.CTkFrame(right_card, fg_color="transparent")
        pv_top.grid(row=0, column=0, padx=20, pady=(16, 10), sticky="ew")
        pv_top.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            pv_top, text="Preview List",
            font=ctk.CTkFont(family=FONT_FAMILY, size=13, weight="bold"),
            text_color=TEXT_MAIN
        ).grid(row=0, column=0, sticky="w")

        self.lbl_pv_count = ctk.CTkLabel(
            pv_top, text="0 Names",
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
            text_color=TEXT_MUTED
        )
        self.lbl_pv_count.grid(row=0, column=1, sticky="e")

        # Names Textbox
        self.txt_preview = ctk.CTkTextbox(
            right_card, corner_radius=8, border_width=0,
            font=ctk.CTkFont(family="Consolas", size=13),
            fg_color=BG_INPUT, text_color=TEXT_MAIN
        )
        self.txt_preview.grid(row=1, column=0, padx=20, pady=(0, 12), sticky="nsew")

        # Preview Actions
        pv_bottom = ctk.CTkFrame(right_card, fg_color="transparent")
        pv_bottom.grid(row=2, column=0, padx=20, pady=(0, 20), sticky="ew")
        pv_bottom.grid_columnconfigure(2, weight=1)

        ctk.CTkButton(
            pv_bottom, text="🔀 Shuffle", width=85, height=34, corner_radius=6, border_width=0,
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
            fg_color=BG_BUTTON, hover_color="#2b2d3f", text_color=TEXT_MAIN,
            command=self._shuffle_names
        ).grid(row=0, column=0, padx=(0, 6))

        ctk.CTkButton(
            pv_bottom, text="🗑️ Clear", width=75, height=34, corner_radius=6, border_width=0,
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
            fg_color=BG_BUTTON, hover_color="#2b2d3f", text_color=TEXT_MAIN,
            command=self._clear_names
        ).grid(row=0, column=1, padx=(0, 6))

        ctk.CTkButton(
            pv_bottom, text="➡️ Send to Checker", height=34, corner_radius=6, border_width=0,
            font=ctk.CTkFont(family=FONT_FAMILY, size=12, weight="bold"),
            fg_color="#0d9488", hover_color="#0f766e", text_color="#ffffff",
            command=lambda: self._switch_view("chk")
        ).grid(row=0, column=2, sticky="ew")

    def _set_len(self, mn, mx):
        self.ent_min_len.delete(0, "end")
        self.ent_min_len.insert(0, str(mn))
        self.ent_max_len.delete(0, "end")
        self.ent_max_len.insert(0, str(mx))

    def _setup_categories_dyn(self):
        for w in self.dyn_container.winfo_children():
            w.destroy()

        mode = self.mode_var.get()

        if "Custom Text File" in mode:
            ctk.CTkLabel(self.dyn_container, text="Select text file:", text_color=TEXT_MUTED).pack(anchor="w", pady=(4, 4))
            row = ctk.CTkFrame(self.dyn_container, fg_color="transparent")
            row.pack(fill="x")
            row.grid_columnconfigure(0, weight=1)
            ctk.CTkEntry(
                row, textvariable=self.custom_file_path, height=32, corner_radius=6, border_width=0,
                fg_color=BG_INPUT, text_color=TEXT_MAIN
            ).grid(row=0, column=0, sticky="ew", padx=(0, 6))
            ctk.CTkButton(
                row, text="Browse...", width=80, height=32, corner_radius=6, border_width=0,
                fg_color=BG_BUTTON, hover_color="#2b2d3f", text_color=TEXT_MAIN,
                command=self._pick_file
            ).grid(row=0, column=1)

        elif "Patterns" in mode:
            ctk.CTkLabel(self.dyn_container, text="Pattern Type:", text_color=TEXT_MUTED).pack(anchor="w", pady=(4, 4))
            self.pat_type_var = ctk.StringVar(value="palindromes")
            ctk.CTkComboBox(
                self.dyn_container, values=["palindromes", "repeating", "sequential"],
                variable=self.pat_type_var, height=32, corner_radius=6, border_width=0,
                fg_color=BG_INPUT, dropdown_fg_color=BG_CARD, text_color=TEXT_MAIN, state="readonly"
            ).pack(fill="x")

        elif "Brute Force" in mode:
            ctk.CTkLabel(self.dyn_container, text="Character Set:", text_color=TEXT_MUTED).pack(anchor="w", pady=(4, 4))
            self.bf_charset = ctk.StringVar(value="lower (a-z)")
            ctk.CTkComboBox(
                self.dyn_container, values=["lower (a-z)", "upper (A-Z)", "alnum (a-z, 0-9)"],
                variable=self.bf_charset, height=32, corner_radius=6, border_width=0,
                fg_color=BG_INPUT, dropdown_fg_color=BG_CARD, text_color=TEXT_MAIN, state="readonly"
            ).pack(fill="x")

        else:
            info_text = "Curated words across high-demand themes (animals, mythical, nature, weapons, colors, gaming, materials)."
            if "OG Names" in mode:
                info_text = "High-tier 2 to 3 letter real English words (e.g. Ace, Zen, Fox, Bat, Sky)."
            elif "Semi-OG" in mode:
                info_text = "Clean compound combinations like DarkBlade, FrostKing, StormAxe."
            elif "Leet" in mode:
                info_text = "Transforms clean dictionary words into authentic leet forms (e.g. Blade -> 8l4d3)."

            ctk.CTkLabel(
                self.dyn_container, text=info_text,
                font=ctk.CTkFont(family=FONT_FAMILY, size=11),
                text_color=TEXT_MUTED, justify="left", wraplength=280
            ).pack(anchor="w", pady=4)

    def _on_gen_mode_change(self, _):
        self._setup_categories_dyn()

    def _pick_file(self):
        p = filedialog.askopenfilename(filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        if p:
            self.custom_file_path.set(p)

    def _get_len_range(self):
        try:
            mn = max(3, int(self.ent_min_len.get().strip()))
            mx = min(16, int(self.ent_max_len.get().strip()))
            if mn > mx:
                mn, mx = mx, mn
            return mn, mx
        except Exception:
            return 3, 5

    def _do_generate(self):
        mode = self.mode_var.get()
        mn, mx = self._get_len_range()
        res = []

        if "English Dictionary" in mode:
            cats = list(self.gen.wl["en"].keys())
            res = self.gen.english_words(cats, mn, mx)
        elif "German Dictionary" in mode:
            cats = list(self.gen.wl["de"].keys())
            res = self.gen.german_words(cats, mn, mx)
        elif "Combined Words" in mode:
            en = self.gen.english_words(list(self.gen.wl["en"].keys()), mn, mx)
            de = self.gen.german_words(list(self.gen.wl["de"].keys()), mn, mx)
            res = sorted(set(en + de))
        elif "OG Names" in mode:
            res = self.gen.og_names(mn, mx)
        elif "Semi-OG" in mode:
            res = self.gen.semi_og(mn, mx)
        elif "Leet" in mode:
            base = self.gen.english_words(list(self.gen.wl["en"].keys()), mn, mx)
            res = self.gen.leet_speak(base, mn, mx)
        elif "Patterns" in mode:
            pt = getattr(self, "pat_type_var", None)
            ptype = pt.get() if pt else "palindromes"
            res = self.gen.patterns(ptype, mn, mx)
        elif "Brute Force" in mode:
            cs = "lower"
            if hasattr(self, "bf_charset"):
                if "upper" in self.bf_charset.get():
                    cs = "upper"
                elif "alnum" in self.bf_charset.get():
                    cs = "alnum"
            res = self.gen.brute_force(mn, charset=cs, limit=2500)
        elif "Custom" in mode:
            p = self.custom_file_path.get()
            if p and os.path.isfile(p):
                res = self.gen.from_file(p, mn, mx)
            else:
                messagebox.showwarning("ZenMcChecker", "Please select a valid text file first.")
                return

        self.names = res
        self._refresh_preview()
        self.sb_stat_gen.configure(text=f"Generated: {len(res)}")

    def _refresh_preview(self):
        self.txt_preview.delete("1.0", "end")
        for n in self.names:
            self.txt_preview.insert("end", n + "\n")
        self.lbl_pv_count.configure(text=f"{len(self.names)} Names")

    def _shuffle_names(self):
        if self.names:
            random.shuffle(self.names)
            self._refresh_preview()

    def _clear_names(self):
        self.names.clear()
        self._refresh_preview()
        self.sb_stat_gen.configure(text="Generated: 0")

    # ───────────────────────────────────────────────────────────
    # VIEW 2: CHECKER
    # ───────────────────────────────────────────────────────────
    def _build_chk_view(self):
        self.view_chk = ctk.CTkFrame(self.content_area, fg_color=BG_APP, border_width=0)
        self.view_chk.grid_columnconfigure((0, 1), weight=1)
        self.view_chk.grid_rowconfigure(2, weight=1)

        # Header
        header = ctk.CTkFrame(self.view_chk, fg_color="transparent")
        header.grid(row=0, column=0, columnspan=2, padx=24, pady=(20, 12), sticky="w")
        ctk.CTkLabel(
            header, text="Live Availability Checker",
            font=ctk.CTkFont(family=FONT_FAMILY, size=20, weight="bold"),
            text_color=TEXT_MAIN
        ).pack(anchor="w")

        # Control Bar Card
        ctrl_card = ctk.CTkFrame(self.view_chk, fg_color=BG_CARD, corner_radius=12, border_width=0)
        ctrl_card.grid(row=1, column=0, columnspan=2, padx=24, pady=(0, 14), sticky="ew")
        ctrl_card.grid_columnconfigure(5, weight=1)

        # Delay Setting
        ctk.CTkLabel(ctrl_card, text="Delay (Sec):", text_color=TEXT_MUTED).grid(row=0, column=0, padx=(18, 6), pady=14)
        self.ent_delay = ctk.CTkEntry(
            ctrl_card, width=50, height=32, corner_radius=6, border_width=0,
            fg_color=BG_INPUT, text_color=TEXT_MAIN, justify="center"
        )
        self.ent_delay.insert(0, "0.6")
        self.ent_delay.grid(row=0, column=1, padx=(0, 16), pady=14)

        # Action Buttons
        self.btn_chk_start = ctk.CTkButton(
            ctrl_card, text="▶ Start", width=95, height=34, corner_radius=6, border_width=0,
            font=ctk.CTkFont(family=FONT_FAMILY, size=12, weight="bold"),
            fg_color=GREEN, hover_color="#059669", text_color="#ffffff",
            command=self._start_checking
        )
        self.btn_chk_start.grid(row=0, column=2, padx=4, pady=14)

        self.btn_chk_pause = ctk.CTkButton(
            ctrl_card, text="⏸ Pause", width=90, height=34, corner_radius=6, border_width=0,
            font=ctk.CTkFont(family=FONT_FAMILY, size=12),
            fg_color=ORANGE, hover_color="#d97706", text_color="#ffffff",
            command=self._toggle_pause, state="disabled"
        )
        self.btn_chk_pause.grid(row=0, column=3, padx=4, pady=14)

        self.btn_chk_stop = ctk.CTkButton(
            ctrl_card, text="⏹ Stop", width=90, height=34, corner_radius=6, border_width=0,
            font=ctk.CTkFont(family=FONT_FAMILY, size=12),
            fg_color=RED, hover_color="#dc2626", text_color="#ffffff",
            command=self._stop_checking, state="disabled"
        )
        self.btn_chk_stop.grid(row=0, column=4, padx=4, pady=14)

        self.chk_lbl_count = ctk.CTkLabel(
            ctrl_card, text="0 names loaded",
            font=ctk.CTkFont(family=FONT_FAMILY, size=12),
            text_color=TEXT_MUTED
        )
        self.chk_lbl_count.grid(row=0, column=5, padx=18, pady=14, sticky="e")

        # Flat Progress Bar on bottom of control card
        self.chk_prog_bar = ctk.CTkProgressBar(
            ctrl_card, height=4, corner_radius=0, fg_color=BG_INPUT, progress_color=ACCENT
        )
        self.chk_prog_bar.set(0)
        self.chk_prog_bar.grid(row=1, column=0, columnspan=6, sticky="ew")

        # Split Result Displays: Available vs Taken
        # Available Column
        card_avail = ctk.CTkFrame(self.view_chk, fg_color=BG_CARD, corner_radius=12, border_width=0)
        card_avail.grid(row=2, column=0, padx=(24, 8), pady=(0, 24), sticky="nsew")
        card_avail.grid_rowconfigure(1, weight=1)
        card_avail.grid_columnconfigure(0, weight=1)

        avail_top = ctk.CTkFrame(card_avail, fg_color="transparent")
        avail_top.grid(row=0, column=0, padx=18, pady=(14, 8), sticky="ew")
        avail_top.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            avail_top, text="✅ Available (Unclaimed)",
            font=ctk.CTkFont(family=FONT_FAMILY, size=13, weight="bold"),
            text_color=GREEN
        ).grid(row=0, column=0, sticky="w")

        self.lbl_avail_cnt = ctk.CTkLabel(avail_top, text="0", text_color=TEXT_MUTED)
        self.lbl_avail_cnt.grid(row=0, column=1, sticky="e")

        self.txt_avail = ctk.CTkTextbox(
            card_avail, corner_radius=8, border_width=0,
            font=ctk.CTkFont(family="Consolas", size=13),
            fg_color=GREEN_BG, text_color=GREEN
        )
        self.txt_avail.grid(row=1, column=0, padx=18, pady=(0, 14), sticky="nsew")

        # Taken Column
        card_taken = ctk.CTkFrame(self.view_chk, fg_color=BG_CARD, corner_radius=12, border_width=0)
        card_taken.grid(row=2, column=1, padx=(8, 24), pady=(0, 24), sticky="nsew")
        card_taken.grid_rowconfigure(1, weight=1)
        card_taken.grid_columnconfigure(0, weight=1)

        taken_top = ctk.CTkFrame(card_taken, fg_color="transparent")
        taken_top.grid(row=0, column=0, padx=18, pady=(14, 8), sticky="ew")
        taken_top.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            taken_top, text="❌ Taken (Claimed)",
            font=ctk.CTkFont(family=FONT_FAMILY, size=13, weight="bold"),
            text_color=RED
        ).grid(row=0, column=0, sticky="w")

        self.lbl_taken_cnt = ctk.CTkLabel(taken_top, text="0", text_color=TEXT_MUTED)
        self.lbl_taken_cnt.grid(row=0, column=1, sticky="e")

        self.txt_taken = ctk.CTkTextbox(
            card_taken, corner_radius=8, border_width=0,
            font=ctk.CTkFont(family="Consolas", size=13),
            fg_color=RED_BG, text_color=RED
        )
        self.txt_taken.grid(row=1, column=0, padx=18, pady=(0, 14), sticky="nsew")

    def _start_checking(self):
        if not self.names:
            messagebox.showinfo("ZenMcChecker", "No names loaded! Generate a list first.")
            return

        if self.is_checking:
            return

        try:
            d = float(self.ent_delay.get().strip())
        except Exception:
            d = 0.6
        self.chk.delay = max(0.2, d)

        self.avail.clear()
        self.taken.clear()
        self.txt_avail.delete("1.0", "end")
        self.txt_taken.delete("1.0", "end")
        self.lbl_avail_cnt.configure(text="0")
        self.lbl_taken_cnt.configure(text="0")
        self.chk_prog_bar.set(0)

        self.is_checking = True
        self.is_paused = False
        self.chk.reset()

        self.btn_chk_start.configure(state="disabled")
        self.btn_chk_pause.configure(state="normal", text="⏸ Pause")
        self.btn_chk_stop.configure(state="normal")

        threading.Thread(target=self._worker_thread, daemon=True).start()

    def _worker_thread(self):
        def on_res(name, ok):
            self.q.put(("res", name, ok))

        def on_prog(done, total):
            self.q.put(("prog", done, total))

        self.chk.check_batch(self.names, on_res, on_prog)
        self.q.put(("done",))

    def _queue_listener(self):
        try:
            while True:
                item = self.q.get_nowait()
                msg = item[0]

                if msg == "res":
                    _, name, ok = item
                    if ok is True:
                        self.avail.append(name)
                        self.txt_avail.insert("end", f"{name}\n")
                        self.txt_avail.see("end")
                        self.lbl_avail_cnt.configure(text=str(len(self.avail)))
                        self.sb_stat_avail.configure(text=f"Available: {len(self.avail)}")
                    elif ok is False:
                        self.taken.append(name)
                        self.txt_taken.insert("end", f"{name}\n")
                        self.txt_taken.see("end")
                        self.lbl_taken_cnt.configure(text=str(len(self.taken)))
                        self.sb_stat_taken.configure(text=f"Taken: {len(self.taken)}")

                elif msg == "prog":
                    _, done, total = item
                    pct = done / total if total else 0
                    self.chk_prog_bar.set(pct)
                    self.chk_lbl_count.configure(
                        text=f"{done}/{total} checked ({pct*100:.0f}%)"
                    )

                elif msg == "done":
                    self.is_checking = False
                    self.btn_chk_start.configure(state="normal")
                    self.btn_chk_pause.configure(state="disabled")
                    self.btn_chk_stop.configure(state="disabled")
                    self.chk_lbl_count.configure(
                        text=f"Complete! {len(self.avail)} available, {len(self.taken)} taken"
                    )
                    if self.avail:
                        self._auto_save_findings()

        except queue.Empty:
            pass

        self.after(60, self._queue_listener)

    def _toggle_pause(self):
        if self.is_paused:
            self.chk.resume()
            self.is_paused = False
            self.btn_chk_pause.configure(text="⏸ Pause")
        else:
            self.chk.pause()
            self.is_paused = True
            self.btn_chk_pause.configure(text="▶ Resume")

    def _stop_checking(self):
        self.chk.stop()
        self.chk_lbl_count.configure(text="Stopped")

    # ───────────────────────────────────────────────────────────
    # VIEW 3: RESULTS & OUTPUT FOLDER
    # ───────────────────────────────────────────────────────────
    def _build_res_view(self):
        self.view_res = ctk.CTkFrame(self.content_area, fg_color=BG_APP, border_width=0)
        self.view_res.grid_columnconfigure(0, weight=1)
        self.view_res.grid_rowconfigure(2, weight=1)

        # Header
        header = ctk.CTkFrame(self.view_res, fg_color="transparent")
        header.grid(row=0, column=0, padx=24, pady=(20, 12), sticky="w")
        ctk.CTkLabel(
            header, text="Results & Output Management",
            font=ctk.CTkFont(family=FONT_FAMILY, size=20, weight="bold"),
            text_color=TEXT_MAIN
        ).pack(anchor="w")

        # Folder Management Card
        folder_card = ctk.CTkFrame(self.view_res, fg_color=BG_CARD, corner_radius=12, border_width=0)
        folder_card.grid(row=1, column=0, padx=24, pady=(0, 14), sticky="ew")
        folder_card.grid_columnconfigure(0, weight=1)

        f_top = ctk.CTkFrame(folder_card, fg_color="transparent")
        f_top.pack(fill="x", padx=18, pady=(14, 6))
        f_top.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            f_top, text="Output Directory:",
            font=ctk.CTkFont(family=FONT_FAMILY, size=13, weight="bold"),
            text_color=TEXT_MAIN
        ).grid(row=0, column=0, sticky="w")

        self.lbl_folder_path = ctk.CTkLabel(
            f_top, text=self.results_dir,
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
            text_color=TEXT_MUTED
        )
        self.lbl_folder_path.grid(row=1, column=0, sticky="w", pady=(2, 0))

        # Folder Actions
        f_acts = ctk.CTkFrame(folder_card, fg_color="transparent")
        f_acts.pack(fill="x", padx=18, pady=(0, 14))

        ctk.CTkButton(
            f_acts, text="📁 Change Folder", height=32, corner_radius=6, border_width=0,
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
            fg_color=BG_BUTTON, hover_color="#2b2d3f", text_color=TEXT_MAIN,
            command=self._change_folder
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            f_acts, text="📂 Open in Explorer", height=32, corner_radius=6, border_width=0,
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
            fg_color=BG_BUTTON, hover_color="#2b2d3f", text_color=TEXT_MAIN,
            command=self._open_in_explorer
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            f_acts, text="💾 Save TXT", height=32, corner_radius=6, border_width=0,
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
            fg_color=BG_BUTTON, hover_color="#2b2d3f", text_color=TEXT_MAIN,
            command=self._export_txt
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            f_acts, text="📊 Save CSV", height=32, corner_radius=6, border_width=0,
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
            fg_color=BG_BUTTON, hover_color="#2b2d3f", text_color=TEXT_MAIN,
            command=self._export_csv
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            f_acts, text="📋 Copy Available", height=32, corner_radius=6, border_width=0,
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
            fg_color=BG_BUTTON, hover_color="#2b2d3f", text_color=TEXT_MAIN,
            command=self._copy_avail
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            f_acts, text="🌐 Open NameMC", height=32, corner_radius=6, border_width=0,
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
            fg_color="#dc2626", hover_color="#b91c1c", text_color="#ffffff",
            command=self._open_namemc_links
        ).pack(side="left")

        # Results Display Card
        res_card = ctk.CTkFrame(self.view_res, fg_color=BG_CARD, corner_radius=12, border_width=0)
        res_card.grid(row=2, column=0, padx=24, pady=(0, 24), sticky="nsew")
        res_card.grid_rowconfigure(1, weight=1)
        res_card.grid_columnconfigure(0, weight=1)

        r_top = ctk.CTkFrame(res_card, fg_color="transparent")
        r_top.grid(row=0, column=0, padx=18, pady=(14, 8), sticky="ew")
        r_top.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            r_top, text="Discovered Available Usernames",
            font=ctk.CTkFont(family=FONT_FAMILY, size=13, weight="bold"),
            text_color=TEXT_MAIN
        ).grid(row=0, column=0, sticky="w")

        self.lbl_res_summary = ctk.CTkLabel(r_top, text="No names discovered yet", text_color=TEXT_MUTED)
        self.lbl_res_summary.grid(row=0, column=1, sticky="e")

        self.txt_results = ctk.CTkTextbox(
            res_card, corner_radius=8, border_width=0,
            font=ctk.CTkFont(family="Consolas", size=13),
            fg_color=BG_INPUT, text_color=TEXT_MAIN
        )
        self.txt_results.grid(row=1, column=0, padx=18, pady=(0, 18), sticky="nsew")

    def _update_results_view(self):
        self.txt_results.delete("1.0", "end")
        if self.avail:
            self.lbl_res_summary.configure(text=f"{len(self.avail)} available names")
            for n in sorted(self.avail):
                self.txt_results.insert("end", f"{n:<16}  —  https://namemc.com/profile/{n}\n")
        else:
            self.lbl_res_summary.configure(text="No names discovered yet")
            self.txt_results.insert(
                "end",
                "No available usernames found yet.\n\n"
                "1. Go to the Generator and create a list of names.\n"
                "2. Click 'Send to Checker'.\n"
                "3. Press 'Start' to query the Mojang API live!"
            )

    def _change_folder(self):
        d = filedialog.askdirectory(title="Select Output Directory", initialdir=self.results_dir)
        if d:
            self.results_dir = d
            self.lbl_folder_path.configure(text=d)

    def _open_in_explorer(self):
        os.makedirs(self.results_dir, exist_ok=True)
        if os.name == "nt":
            os.startfile(self.results_dir)
        else:
            webbrowser.open(f"file://{self.results_dir}")

    def _auto_save_findings(self):
        os.makedirs(self.results_dir, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        fpath = os.path.join(self.results_dir, f"available_{ts}.txt")
        try:
            with open(fpath, "w", encoding="utf-8") as f:
                f.write("ZenMcChecker — Available Usernames\n")
                f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("=" * 45 + "\n\n")
                for n in sorted(self.avail):
                    f.write(f"{n}\n")
        except Exception:
            pass

    def _export_txt(self):
        if not self.avail:
            messagebox.showinfo("ZenMcChecker", "No available usernames to save.")
            return
        fpath = filedialog.asksaveasfilename(
            title="Save as TXT", defaultextension=".txt",
            initialdir=self.results_dir,
            initialfile=f"mc_names_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
            filetypes=[("Text file", "*.txt")]
        )
        if fpath:
            with open(fpath, "w", encoding="utf-8") as f:
                for n in sorted(self.avail):
                    f.write(n + "\n")
            messagebox.showinfo("ZenMcChecker", f"Exported successfully:\n{fpath}")

    def _export_csv(self):
        if not self.avail and not self.taken:
            messagebox.showinfo("ZenMcChecker", "No results to export.")
            return
        fpath = filedialog.asksaveasfilename(
            title="Save as CSV", defaultextension=".csv",
            initialdir=self.results_dir,
            initialfile=f"mc_names_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            filetypes=[("CSV file", "*.csv")]
        )
        if fpath:
            with open(fpath, "w", encoding="utf-8", newline="") as f:
                w = csv.writer(f)
                w.writerow(["Username", "Status", "Length", "NameMC URL"])
                for n in sorted(self.avail):
                    w.writerow([n, "Available", len(n), NAMEMC_URL.format(n)])
                for n in sorted(self.taken):
                    w.writerow([n, "Taken", len(n), NAMEMC_URL.format(n)])
            messagebox.showinfo("ZenMcChecker", f"Exported CSV successfully:\n{fpath}")

    def _copy_avail(self):
        if not self.avail:
            messagebox.showinfo("ZenMcChecker", "No available names to copy.")
            return
        self.clipboard_clear()
        self.clipboard_append("\n".join(sorted(self.avail)))
        messagebox.showinfo("ZenMcChecker", f"Copied {len(self.avail)} names to clipboard!")

    def _open_namemc_links(self):
        if not self.avail:
            messagebox.showinfo("ZenMcChecker", "No available names to open.")
            return
        top = self.avail[:5]
        for n in top:
            webbrowser.open(NAMEMC_URL.format(n))
        if len(self.avail) > 5:
            messagebox.showinfo("ZenMcChecker", f"Opened the first {len(top)} names in NameMC.")


def main():
    app = ZenMcCheckerApp()
    app.mainloop()


if __name__ == "__main__":
    main()
