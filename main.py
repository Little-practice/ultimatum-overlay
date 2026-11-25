"""Ultimatum оверлей (PoE 1): только подсказки поверх игры, ничего не нажимает.
- Ctrl+C на предмете в игре -> у курсора карточка с ценой poe.ninja.
- Окно ультиматума -> кольцо на самом простом разрешённом моде (или «НЕЛЬЗЯ»).
- Кнопка Double Down -> мигающая рамка.
Запуск: python main.py"""
import copy
import json
import os
import queue
import sys
import threading
import time
import tkinter as tk
import webbrowser
from tkinter import filedialog, ttk

import pyperclip

import i18n
import icon_data
import icons
import theme as T
from hotkeys import MOD_CTRL, MOD_SHIFT, Hotkey, KeyWatch, beep, custom_sound_path, key_name
from i18n import tr
from overlay import Overlay
from paths import APP_DIR, ensure_initial_file, restore_default_icons, write_json
from prices import Prices
from prices_window import PricesWindow
import share
import system
from whats_new import show_whats_new
from screen import DD_BOX, Screen, clipboard_seq, cursor_pos, poe_running
from watcher import GREEN, ModAdvisor, is_item_text, mod_box, price_info

VERSION = "1.4.2"
CFG_FILE = os.path.join(APP_DIR, "config.json")
DEFAULT_CFG = {
    "lang": "ru",
    "names_lang": "",           # язык названий в списке цен ("" — как у программы)
    "league": "Covens",
    "div_threshold": 1.0,       # дороже — цена золотая
    "label_seconds": 8.0,       # сколько держать карточку цены
    "show_reward_preview": True,# карточка награды ультиматума (уники и карты)
    "waves": "auto",            # auto | 13 | 10
    "mods_enabled": True,       # подсказывать ли сложность модов
    "mod_seconds": 3.5,         # сколько секунд держать рамки модов (исчезают сами)
    "life_alert": True,         # метка «% Monster Life» у Inscribed Ultimatum
    "dd_enabled": True,         # рамка вокруг кнопки «Удвоить» (Double Down)
    "sound": False,             # звук на Double Down и запрещённый мод
    "hide_key": [0x48, MOD_CTRL | MOD_SHIFT],   # Ctrl+Shift+H — скрыть/показать оверлей
    "scan_key": [0x71, 0],       # F2 — ручной скан алтаря ультиматума (100% ToS Safe)
    "sat_threshold": 60,
    "match_threshold": 0.4,
    "offset_x": 0,
    "offset_y": 0,
}
WAVES = [("mode_auto", "auto"), ("mode_13", 13), ("mode_10", 10)]
LINKS = [("Twitch", "#9146ff", "https://www.twitch.tv/little_practice"),
         ("YouTube", "#e62117", "https://www.youtube.com/@Little_practice232"),
         ("Telegram", "#229ed9", "https://t.me/little_practice_there")]
DONATE = "https://www.donationalerts.com/r/little_practice"


def system_lang():
    """Язык Windows: русский (и украинский, белорусский, казахский) -> "ru", остальные -> "en"."""
    try:
        import ctypes
        primary = ctypes.windll.kernel32.GetUserDefaultUILanguage() & 0x3FF
        return "ru" if primary in (0x19, 0x22, 0x23, 0x3F) else "en"
    except Exception:
        return "en"


def load_cfg():
    cfg = copy.deepcopy(DEFAULT_CFG)
    saved = {}
    if os.path.exists(CFG_FILE):
        try:
            with open(CFG_FILE, encoding="utf-8") as f:
                saved = json.load(f)
        except Exception:
            pass
    cfg.update(saved)
    if "lang" not in saved:          # первый запуск — язык как у Windows
        cfg["lang"] = system_lang()
    return cfg


def thumb(img, size, dim=False):
    """Иконка для списка; запрещённые — приглушённые и обесцвеченные."""
    cv2 = icons.cv2
    im = cv2.resize(img, (size, size), interpolation=cv2.INTER_AREA)
    if dim:
        g = cv2.cvtColor(cv2.cvtColor(im, cv2.COLOR_BGR2GRAY), cv2.COLOR_GRAY2BGR)
        im = (g * 0.45).astype("uint8")
    ok, buf = cv2.imencode(".png", im)
    return tk.PhotoImage(data=buf.tobytes())


def mod_name(e):
    """Название мода на языке программы (у новых модов — «Новый мод»)."""
    n = e.get("name_ru" if i18n.LANG == "ru" else "name_en") or e.get("name")
    return n or ("Мод Миража" if i18n.LANG == "ru" else "Mirage modifier")


def mix(c1, c2, t):
    """Цвет между c1 и c2 (t от 0 до 1) — для плавной анимации."""
    a = [int(c1[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(c2[i:i + 2], 16) for i in (1, 3, 5)]
    return "#%02x%02x%02x" % tuple(round(x + (y - x) * t) for x, y in zip(a, b))


class ModRow:
    """Строка мода. Переключение «можно/нельзя» меняет только эту строку, с плавным переходом цвета."""
    STEPS = 8

    def __init__(self, app, parent, n, e, tier_col):
        self.app, self.e, self.tier_col = app, e, tier_col
        bg = T.CARD2
        self.ph_on = thumb(e["img"], 34, dim=False)
        self.ph_off = thumb(e["img"], 34, dim=True)
        f = self.frame = tk.Frame(parent, bg=bg, cursor="hand2")
        self.stripe = tk.Frame(f, width=3)
        self.stripe.pack(side="left", fill="y")
        self.icon = tk.Label(f, bg=bg, cursor="hand2")
        self.icon.pack(side="left", padx=(6, 6), pady=3)
        self.state = tk.Label(f, width=7, bg=bg, cursor="hand2", font=(T.SANS, 8, "bold"), anchor="w")
        self.state.pack(side="left")
        # width=1: название может сжиматься — кнопки справа всегда видны, длинный текст обрезается
        self.name = tk.Label(f, text=mod_name(e), bg=bg, anchor="w", font=(T.SANS, 9), cursor="hand2", width=1)
        for txt, cmd in (("✕", lambda: app.remove(e)), ("▼", lambda: app.move(e, 1)),
                         ("▲", lambda: app.move(e, -1))):
            b = tk.Label(f, text=txt, bg=bg, fg=T.MUTED, cursor="hand2", font=(T.SANS, 9), padx=4)
            b.pack(side="right")
            b.bind("<Enter>", lambda ev, b=b: b.configure(fg=T.GOLD_HI))
            b.bind("<Leave>", lambda ev, b=b: b.configure(fg=T.MUTED))
            b.bind("<Button-1>", lambda ev, c=cmd: c())
        self.name.pack(side="left", fill="x", expand=True, padx=(2, 4))
        for w in (f, self.icon, self.state, self.name):
            w.bind("<Button-1>", lambda ev: self.toggle())
            w.bindtags(("UltModsScroll",) + w.bindtags())
        self.paint(1.0)

    def colors(self, on):
        return (self.tier_col if on else "#3a332c", T.GREEN if on else T.RED, T.TXT if on else T.MUTED)

    def paint(self, t, frm=None):
        if not self.frame.winfo_exists():
            return
        on = self.e["allowed"]
        to = self.colors(on)
        cur = to if frm is None else tuple(mix(a, b, t) for a, b in zip(frm, to))
        self.stripe.configure(bg=cur[0])
        self.state.configure(fg=cur[1], text=tr("allow") if on else tr("forbid"))
        self.name.configure(fg=cur[2])
        self.icon.configure(image=self.ph_on if (on if t >= 0.5 else not on) else self.ph_off)

    def toggle(self):
        frm = self.colors(self.e["allowed"])
        self.app.set_allowed(self.e, not self.e["allowed"])
        for k in range(1, self.STEPS + 1):
            self.frame.after(18 * k, lambda k=k: self.paint(k / self.STEPS, frm))


class App:
    def __init__(self, root):
        self.root = root
        root.title("Ultimatum overlay")
        sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
        root.geometry(f"{min(1100, max(660, sw - 40))}x{min(940, max(540, sh - 80))}")
        root.minsize(min(660, max(500, sw - 40)), min(540, max(420, sh - 80)))
        root.configure(bg=T.BG)
        T.apply_ttk(root)
        self.cfg = load_cfg()
        ensure_initial_file("names_ru.json", overwrite_if_newer=True)
        ensure_initial_file("prices_cache.json", overwrite_if_newer=True)
        ensure_initial_file("leagues.json", overwrite_if_newer=True)
        ensure_initial_file("items_preview.json", overwrite_if_newer=True)
        i18n.set_lang(self.cfg["lang"])
        self.scr = Screen()
        self.scr.dx, self.scr.dy = self.cfg["offset_x"], self.cfg["offset_y"]
        self.prices = Prices()
        self.advisor = ModAdvisor(self.scr, self.cfg)
        self.ui = queue.Queue()   # задания для окна из рабочего потока
        self.started = time.time()
        self._last_check_update = self.started
        self._updating = False
        self._ui_cache = {}
        self.status = ""
        self.pw = None            # окно «Цены»
        self.redraw_marks = False
        self.log_lines = []       # чтобы лог пережил смену языка
        self.container = None
        self.leagues = [self.cfg["league"]]
        self.hidden = False
        self.hk_hide = None
        self.hk_scan = None
        self._icon = tk.PhotoImage(data=icon_data.PNG)
        root.iconphoto(True, self._icon)
        self.build()
        self.overlay = Overlay(root, self.scr)
        self.start_hotkey()
        self.kw = KeyWatch(on_dismiss=lambda: self.overlay.boxes and self.ui.put(("dismiss_altar",)))  # Esc/Пробел снимают оверлей
        self.kw.start()
        self.tray = None
        self.tray_hint_shown = False
        self.make_tray()
        root.protocol("WM_DELETE_WINDOW", self.to_tray if self.tray else self.quit)
        if "--tray" in __import__("sys").argv and self.tray:
            root.after(10, root.withdraw)
        threading.Thread(target=self.check_update, daemon=True).start()
        threading.Thread(target=self.load_leagues, daemon=True).start()
        root.after(50, lambda: T.dark_titlebar(root))
        if self.cfg.get("last_seen_version") != VERSION:
            self.cfg["last_seen_version"] = VERSION
            write_json(CFG_FILE, self.cfg, indent=2)
            root.after(400, lambda: self.show_whats_new())
        threading.Thread(target=self.load_prices, daemon=True).start()
        threading.Thread(target=self.watch, daemon=True).start()
        self.root.after(100, self.pump)

    # ================= окно настроек =================
    def field(self, parent, text, key, width=7):
        T.label(parent, text, fg=T.MUTED).pack(side="left")
        v = self.cfg[key]
        if isinstance(v, float) and v.is_integer():
            v = int(v)                      # 8.0 -> «8»
        var = tk.StringVar(value=str(v))
        T.entry(parent, var, width).pack(side="left", padx=(6, 14), ipady=3)
        self.v[key] = var
        var.trace_add("write", self.changed)

    def build(self):
        if self.container is not None:
            self.container.destroy()
        self.v = {}
        self.rows = {}
        self._ui_cache = {}
        root = self.container = tk.Frame(self.root, bg=T.BG)
        root.pack(fill="both", expand=True)

        # --- шапка: название, языки ---
        head = tk.Frame(root, bg=T.BG, padx=16, pady=12)
        head.pack(fill="x")
        tk.Label(head, text="ULTIMATUM", bg=T.BG, fg=T.GOLD_HI, font=(T.SERIF, 22, "bold")).pack(side="left")
        tk.Label(head, text=" " + tr("subtitle"), bg=T.BG, fg=T.GOLD_HI, font=(T.SERIF, 22, "bold")).pack(
            side="left")
        langs = tk.Frame(head, bg=T.BG)
        langs.pack(side="right", pady=(6, 0))
        for code in ("ru", "en"):
            on = i18n.LANG == code
            b = tk.Label(langs, text=code.upper(), bg=T.GOLD if on else T.CARD2, fg=T.BG if on else T.MUTED,
                         font=(T.SANS, 9, "bold"), padx=9, pady=2, cursor="hand2")
            b.pack(side="left", padx=(2, 0))
            b.bind("<Button-1>", lambda e, c=code: self.set_lang(c))
        hb = tk.Label(langs, text="?", bg=T.CARD2, fg=T.GOLD_HI, font=(T.SANS, 9, "bold"), padx=9, pady=2,
                      cursor="hand2")
        hb.pack(side="left", padx=(8, 0))
        hb.bind("<Button-1>", lambda e: self.show_help())
        self.price_lbl = tk.Label(head, text=tr("prices_loading"), bg=T.BG, fg=T.MUTED, font=(T.SANS, 9))
        self.price_lbl.pack(side="right", pady=(8, 0), padx=12)
        self.poe_lbl = tk.Label(head, text="", bg=T.BG, font=(T.SANS, 9, "bold"))
        self.poe_lbl.pack(side="right", pady=(8, 0), padx=(12, 0))
        tk.Frame(root, bg=T.GOLD, height=1).pack(fill="x", padx=16)

        # --- подвал: автор, ссылки, поддержать ---
        foot = tk.Frame(root, bg=T.CARD, padx=16, pady=12)
        foot.pack(side="bottom", fill="x")
        tk.Label(foot, text=tr("made_by"), bg=T.CARD, fg=T.MUTED, font=(T.SANS, 11)).pack(side="left", pady=(4, 0))
        tk.Label(foot, text=" Little_practice", bg=T.CARD, fg=T.GOLD_HI, font=(T.SERIF, 17, "bold")).pack(side="left")
        ver_b = tk.Label(foot, text=f"   v{VERSION}", bg=T.CARD, fg=T.MUTED, font=(T.SANS, 9), cursor="hand2")
        ver_b.pack(side="left", pady=(6, 0))
        ver_b.bind("<Button-1>", lambda e: self.show_whats_new(force=True))
        wn_b = tk.Label(foot, text=f"({tr('whats_new_link')})", bg=T.CARD, fg=T.GOLD, font=(T.SANS, 9), cursor="hand2")
        wn_b.pack(side="left", pady=(6, 0), padx=(4, 0))
        wn_b.bind("<Button-1>", lambda e: self.show_whats_new(force=True))
        T.button(foot, "$  " + tr("support"), lambda: webbrowser.open(DONATE), fg=T.BG, bg=T.GOLD,
                 hover=T.GOLD_HI).pack(side="right", padx=(10, 0))
        for name, color, url in reversed(LINKS):
            T.button(foot, name, lambda u=url: webbrowser.open(u), fg="white", bg=color,
                     hover=mix(color, "#ffffff", 0.2)).pack(side="right", padx=(6, 0))
        tk.Frame(root, bg=T.LINE, height=1).pack(side="bottom", fill="x")

        body = tk.Frame(root, bg=T.BG, padx=16, pady=10)
        body.pack(fill="both", expand=True)
        top = tk.Frame(body, bg=T.BG)
        top.pack(fill="x")
        top.columnconfigure(0, weight=1, uniform="c")
        top.columnconfigure(1, weight=1, uniform="c")

        # --- карточка: прайсчек ---
        o, c = T.card(top, tr("pc_title"))
        o.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        T.wrap_label(c, tr("pc_hint")).pack(fill="x", pady=(0, 8))
        r = tk.Frame(c, bg=T.CARD); r.pack(fill="x", pady=2)
        T.label(r, tr("league"), fg=T.MUTED).pack(side="left")
        lv = tk.StringVar(value=self.cfg["league"])
        self.league_cb = ttk.Combobox(r, textvariable=lv, values=self.leagues, state="readonly", width=15)
        self.league_cb.pack(side="left", padx=(6, 10))
        self.league_cb.bind("<<ComboboxSelected>>", lambda e: self.league_changed(lv.get()))
        T.button(r, tr("refresh"),
                 lambda: threading.Thread(target=self.load_prices, args=(True,), daemon=True).start(),
                 small=True).pack(side="left")
        T.button(r, tr("price_list"), self.open_prices, small=True).pack(side="left", padx=6)
        r = tk.Frame(c, bg=T.CARD); r.pack(fill="x", pady=(8, 2))
        self.field(r, tr("gold_from"), "div_threshold", 5)
        r = tk.Frame(c, bg=T.CARD); r.pack(fill="x", pady=2)
        self.field(r, tr("show_sec"), "label_seconds", 5)
        r = tk.Frame(c, bg=T.CARD); r.pack(fill="x", pady=(8, 0))
        T.Toggle(r, self.cfg["life_alert"], lambda v: self.set_flag("life_alert", v)).pack(side="left")
        T.label(r, tr("life_toggle"), size=9).pack(side="left", padx=8)
        r = tk.Frame(c, bg=T.CARD); r.pack(fill="x", pady=(6, 0))
        T.Toggle(r, self.cfg.get("show_reward_preview", True),
                 lambda v: self.set_flag("show_reward_preview", v)).pack(side="left")
        T.label(r, tr("show_reward_preview"), size=9).pack(side="left", padx=8)

        # --- карточка: подсказка модов ---
        o, c = T.card(top, tr("mods_title"))
        o.grid(row=0, column=1, sticky="nsew", padx=(6, 0))
        r = tk.Frame(c, bg=T.CARD); r.pack(fill="x")
        T.Toggle(r, self.cfg["mods_enabled"], self.mods_toggled).pack(side="left")
        self.mods_state = T.label(r, "", bold=True)
        self.mods_state.pack(side="left", padx=8)
        self._mods_state_text()

        # Кнопка сканирования модов алтаря (ручной вызов — 100% GGG ToS Safe)
        r = tk.Frame(c, bg=T.CARD); r.pack(fill="x", pady=(8, 0))
        T.label(r, tr("scan_key"), fg=T.MUTED).pack(side="left")
        self.scan_key_btn = T.button(r, key_name(*self.cfg.get("scan_key", [0x71, 0])),
                                     lambda: self.capture_key("scan_key"), small=True)
        self.scan_key_btn.pack(side="left", padx=(8, 6))
        T.label(r, tr("scan_safe_badge"), size=8, fg=T.GREEN).pack(side="left")

        # Время показа подсказки (исчезает сама до начала боя)
        r = tk.Frame(c, bg=T.CARD); r.pack(fill="x", pady=(8, 0))
        T.label(r, tr("mod_seconds_lbl"), fg=T.MUTED).pack(side="left")
        dur_opts = {tr("dur_2_5"): 2.5, tr("dur_3_5"): 3.5, tr("dur_5"): 5.0}
        dur_rev = {v: k for k, v in dur_opts.items()}
        cur_dur = float(self.cfg.get("mod_seconds", 3.5))
        dur_v = tk.StringVar(value=dur_rev.get(cur_dur, list(dur_opts)[1]))
        ttk.Combobox(r, textvariable=dur_v, values=list(dur_opts), state="readonly", width=18).pack(side="left", padx=(6, 0))
        self.v["mod_seconds"] = (dur_v, dur_opts)
        dur_v.trace_add("write", self.changed)

        r = tk.Frame(c, bg=T.CARD); r.pack(fill="x", pady=(8, 2))
        T.label(r, tr("mode"), fg=T.MUTED).pack(side="left")
        opts = {tr(k): v for k, v in WAVES}
        rev = {v: k for k, v in opts.items()}
        wv = tk.StringVar(value=rev.get(self.cfg["waves"], list(opts)[0]))
        ttk.Combobox(r, textvariable=wv, values=list(opts), state="readonly", width=26).pack(side="left",
                                                                                           padx=(6, 0))
        self.v["waves"] = (wv, opts)
        wv.trace_add("write", self.changed)
        r = tk.Frame(c, bg=T.CARD); r.pack(fill="x", pady=(8, 0))
        T.Toggle(r, self.cfg["dd_enabled"], lambda v: self.set_flag("dd_enabled", v)).pack(side="left")
        T.label(r, tr("dd_toggle"), size=9).pack(side="left", padx=8)
        self.status_lbl = T.wrap_label(c, "", fg=T.GOLD_HI, bold=True)
        self.status_lbl.pack(fill="x", pady=(4, 0))

        # --- карточка: оверлей (клавиша скрытия, звук) ---
        o, c = T.card(top, tr("overlay_card"))
        o.grid(row=1, column=0, columnspan=2, sticky="nsew", pady=(12, 0))
        r = tk.Frame(c, bg=T.CARD); r.pack(fill="x")
        T.label(r, tr("hide_key"), fg=T.MUTED).pack(side="left")
        self.key_btn = T.button(r, key_name(*self.cfg["hide_key"]), lambda: self.capture_key("hide_key"), small=True)
        self.key_btn.pack(side="left", padx=(8, 8))
        self.hidden_lbl = T.label(r, "", size=9, bold=True)
        self.hidden_lbl.pack(side="left")
        T.Toggle(r, self.cfg["sound"], lambda v: (self.set_flag("sound", v), v and beep("info"))).pack(
            side="left", padx=(30, 0))
        T.label(r, tr("sound"), size=9).pack(side="left", padx=8)
        T.button(r, tr("own_sound"), self.pick_sound, small=True).pack(side="left", padx=(4, 0))
        T.button(r, tr("std_sound"), self.reset_sound, small=True, fg=T.MUTED).pack(side="left", padx=(6, 0))
        T.wrap_label(c, tr("key_hint"), size=8).pack(fill="x", pady=(6, 0))
        r = tk.Frame(c, bg=T.CARD); r.pack(fill="x", pady=(10, 0))
        T.Toggle(r, system.autostart_enabled(), self.autostart_toggled).pack(side="left")
        T.label(r, tr("autostart"), size=9).pack(side="left", padx=8)

        # --- тонкая настройка (свёрнута) ---
        self.fine = tk.Frame(body, bg=T.BG)
        self.fine_btn = tk.Label(body, text="▸  " + tr("fine"), bg=T.BG, fg=T.MUTED, cursor="hand2",
                                 font=(T.SANS, 9))
        self.fine_btn.pack(anchor="w", pady=(8, 0))
        self.fine_btn.bind("<Button-1>", lambda e: self.toggle_fine())
        o, c = T.card(self.fine)
        o.pack(fill="x")
        r = tk.Frame(c, bg=T.CARD); r.pack(fill="x")
        self.field(r, tr("sat"), "sat_threshold", 4)
        self.field(r, tr("match"), "match_threshold", 5)
        self.field(r, tr("shift") + " X", "offset_x", 4)
        self.field(r, "Y", "offset_y", 4)

        # --- последние цены (внизу, над подвалом) ---
        o, c = T.card(body, tr("last_prices"))
        o.pack(side="bottom", fill="x", pady=(10, 0))
        self.logbox = tk.Text(c, height=4, wrap="word", state="disabled", bg=T.CARD, fg=T.TXT, relief="flat",
                              font=(T.SANS, 9), highlightthickness=0, padx=0, pady=0)
        self.logbox.pack(fill="x")
        self.logbox.tag_configure("time", foreground=T.MUTED)
        self.logbox.tag_configure("gold", foreground=T.GOLD_HI)
        for t, msg, gold in self.log_lines[-30:]:   # прошлые сообщения — на новом языке
            self._log_insert(t, i18n.retr(msg), gold)

        # --- карточка: список модов ---
        self.mods_card, c = T.card(body, None)
        self.mods_card.pack(fill="both", expand=True, pady=(10, 0))
        h = tk.Frame(c, bg=T.CARD); h.pack(fill="x", pady=(0, 6))
        tk.Label(h, text=tr("mods_list").upper(), bg=T.CARD, fg=T.GOLD, font=(T.SERIF, 10, "bold")).pack(side="left")
        self.count_lbl = T.label(h, "", fg=T.MUTED, size=9)
        self.count_lbl.pack(side="left", padx=10)
        T.button(h, tr("reset_tier"), self.default_tierlist, small=True).pack(side="right")
        T.button(h, tr("paste"), self.paste_mods, small=True).pack(side="right", padx=(0, 6))
        T.button(h, tr("copy"), self.copy_mods, small=True).pack(side="right", padx=(0, 6))
        T.wrap_label(c, tr("mods_hint")).pack(fill="x", pady=(0, 6))
        wrap = tk.Frame(c, bg=T.CARD)
        wrap.pack(fill="both", expand=True)
        self.canvas = tk.Canvas(wrap, bg=T.CARD, highlightthickness=0)
        sb = ttk.Scrollbar(wrap, orient="vertical", command=self.canvas.yview)
        self.inner = tk.Frame(self.canvas, bg=T.CARD)
        self.inner.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.inner_id = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")
        self.canvas.bind("<Configure>", self._canvas_resized)
        self.canvas.configure(yscrollcommand=sb.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        # колесо мыши крутит список независимо от вложенных виджетов и не мешает другим окнам
        self.root.bind_class("UltModsScroll", "<MouseWheel>",
                             lambda e: self.canvas.yview_scroll(-e.delta // 120, "units")
                             if self.canvas.winfo_exists() else None)
        for w in (self.canvas, self.inner):
            w.bindtags(("UltModsScroll",) + w.bindtags())
        self.render_icons()

    def _canvas_resized(self, e):
        """При растягивании окна перестраиваем список один раз, когда размер перестал меняться."""
        if getattr(self, "_rs_job", None):
            self.root.after_cancel(self._rs_job)
        self._rs_job = self.root.after(120, lambda: self.canvas.itemconfigure(self.inner_id, width=e.width))

    def set_lang(self, code):
        if code == i18n.LANG:
            return
        i18n.set_lang(code)
        self.cfg["lang"] = code
        self.save_cfg()
        reopen = self.pw is not None and self.pw.win.winfo_exists()
        if reopen:
            self.pw.win.destroy()
            self.pw = None
        self.build()
        self.redraw_marks = True  # подписи над модами — на новом языке
        if self.tray:
            self.make_tray()
        if reopen:
            self.open_prices()

    def toggle_fine(self):
        if self.fine.winfo_ismapped():
            self.fine.pack_forget()
            self.fine_btn.configure(text="▸  " + tr("fine"))
        else:
            self.fine.pack(fill="x", pady=(4, 0), before=self.mods_card)
            self.fine_btn.configure(text="▾  " + tr("fine"))

    def _mods_state_text(self):
        on = self.cfg["mods_enabled"]
        self.mods_state.configure(text=tr("on") if on else tr("off"), fg=T.GREEN if on else T.MUTED)

    # ---------------- список модов по тирам ----------------
    def render_icons(self):
        y = self.canvas.yview()[0] if self.inner.winfo_children() else 0
        for w in self.inner.winfo_children():
            w.destroy()
        self.rows = {}
        self.tier_lbls = {}
        lib = self.advisor.lib
        tiers = []
        for e in lib:
            if e["tier"] not in tiers:
                tiers.append(e["tier"])
        for tier in tiers:
            items = [e for e in lib if e["tier"] == tier]
            col = T.TIER_COLORS.get(tier, "#9a9a9a")
            hdr = tk.Frame(self.inner, bg=T.CARD)
            hdr.pack(fill="x", pady=(8, 3))
            tk.Frame(hdr, bg=col, width=4, height=16).pack(side="left")
            tk.Label(hdr, text=f"  {i18n.tier(tier)}", bg=T.CARD, fg=col, font=(T.SERIF, 10, "bold")).pack(side="left")
            self.tier_lbls[tier] = tk.Label(hdr, bg=T.CARD, fg=T.MUTED, font=(T.SANS, 9))
            self.tier_lbls[tier].pack(side="left")
            grid = tk.Frame(self.inner, bg=T.CARD)
            grid.pack(fill="x")
            grid.columnconfigure(0, weight=1, uniform="m")
            grid.columnconfigure(1, weight=1, uniform="m")
            for k, e in enumerate(items):
                row = ModRow(self, grid, k, e, col)
                row.frame.grid(row=k // 2, column=k % 2, sticky="ew", padx=(0, 6), pady=2)
                self.rows[id(e)] = row
        self.update_counts()
        self.root.after_idle(lambda: self.canvas.yview_moveto(y))

    def update_counts(self):
        lib = self.advisor.lib
        self.count_lbl.configure(text=tr("allowed_n", a=sum(e["allowed"] for e in lib), n=len(lib)))
        for tier, lbl in self.tier_lbls.items():
            items = [e for e in lib if e["tier"] == tier]
            lbl.configure(text=f"   {sum(e['allowed'] for e in items)}/{len(items)}")

    def set_allowed(self, e, value):
        e["allowed"] = bool(value)
        icons.save_library(self.advisor.lib)
        self.update_counts()
        self.redraw_marks = True

    def set_name(self, e, v):
        name = v.get().strip()
        if name != e.get("name", ""):
            e["name"] = name
            icons.save_library(self.advisor.lib)

    def move(self, e, d):
        """Сдвинуть мод выше/ниже внутри его тира (порядок = сложность)."""
        lib = self.advisor.lib
        n = lib.index(e)
        same = [i for i, x in enumerate(lib) if x["tier"] == e["tier"]]
        k = same.index(n) + d
        if 0 <= k < len(same):
            m = same[k]
            lib[n], lib[m] = lib[m], lib[n]
            icons.save_library(lib)
            self.render_icons()
            self.redraw_marks = True

    def remove(self, e):
        self.advisor.lib.remove(e)
        icons.save_library(self.advisor.lib)
        self.render_icons()

    def default_tierlist(self):
        """Вернуть встроенный тир-лист (39 модов, разрешены Free и Easy). Твои галочки сбросятся."""
        try:
            restore_default_icons(icons.ICON_DIR)
            self.advisor.lib = icons.load_library()
            self.log(tr("tier_reset_done", n=len(self.advisor.lib)))
        except Exception as ex:
            self.log(tr("tier_reset_err", e=ex))
        self.render_icons()

    def open_prices(self):
        if self.pw is not None and self.pw.win.winfo_exists():
            self.pw.win.deiconify()
            self.pw.win.lift()
            return
        self.pw = PricesWindow(self.root, self.prices, on_change=lambda: self.log(tr("custom_saved")),
                               names_lang=self.cfg.get("names_lang") or i18n.LANG,
                               on_names_lang=lambda c: (self.cfg.__setitem__("names_lang", c), self.save_cfg()))

    # ---------------- свой звук ----------------
    def pick_sound(self):
        path = filedialog.askopenfilename(title=tr("sound_pick"), filetypes=[("WAV", "*.wav")])
        if not path:
            return
        try:
            import shutil
            import wave
            with wave.open(path, "rb") as w:      # проверим, что это настоящий WAV
                w.getnframes()
            shutil.copyfile(path, custom_sound_path())
            self.log(tr("sound_set", n=os.path.basename(path)))
            beep("info")
        except Exception:
            self.log(tr("sound_bad"))

    def reset_sound(self):
        try:
            if os.path.exists(custom_sound_path()):
                os.remove(custom_sound_path())
        except OSError:
            pass
        self.log(tr("sound_reset"))
        beep("info")

    # ---------------- обмен галочками ----------------
    def copy_mods(self):
        try:
            self.root.clipboard_clear()
            self.root.clipboard_append(share.export_code(self.advisor.lib))
            self.log(tr("copied"))
        except Exception:
            pass

    def paste_mods(self):
        try:
            code = self.root.clipboard_get()
        except tk.TclError:
            code = ""
        try:
            n, miss = share.import_code(self.advisor.lib, code)
        except Exception:
            self.log(tr("paste_bad"))
            return
        icons.save_library(self.advisor.lib)
        self.render_icons()
        self.redraw_marks = True
        self.log(tr("pasted", n=n) + (tr("pasted_missing", m=miss) if miss else ""))

    # ---------------- справка ----------------
    def show_help(self):
        w = tk.Toplevel(self.root)
        w.title(tr("help_title"))
        w.configure(bg=T.BG)
        w.geometry("620x500")
        w.after(50, lambda: T.dark_titlebar(w))
        tk.Label(w, text=tr("help_title").upper(), bg=T.BG, fg=T.GOLD_HI, font=(T.SERIF, 16, "bold"),
                 padx=20, pady=12).pack(anchor="w")
        tk.Frame(w, bg=T.GOLD, height=1).pack(fill="x", padx=20)
        T.wrap_label(w, tr("help"), fg=T.TXT, size=10, bg=T.BG, padx=20, pady=12, anchor="nw").pack(
            fill="both", expand=True)

    def show_whats_new(self, force=False):
        show_whats_new(self.root, VERSION, lang=self.cfg.get("lang", "ru"), force=force)

    # ---------------- трей, автозапуск, обновления ----------------
    def make_tray(self):
        """Значок в трее (меню — на текущем языке)."""
        if self.tray:
            self.tray.stop()
            self.tray = None
        try:
            self.tray = system.Tray(icon_data.PNG, "Ultimatum overlay", lambda: self.ui.put(("show_window",)),
                                    lambda: self.ui.put(("toggle_overlay",)), lambda: self.ui.put(("quit",)),
                                    {"open": tr("tray_open"), "toggle": tr("tray_toggle"), "quit": tr("tray_quit")})
        except Exception as ex:
            self.log(tr("error", e=ex))

    def to_tray(self):
        self.root.withdraw()
        if not self.tray_hint_shown:
            self.tray_hint_shown = True
            self.log(tr("tray_hint"))

    def show_window(self):
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()

    def quit(self):
        try:
            if self.tray:
                self.tray.stop()
            if getattr(self, "hk_hide", None):
                self.hk_hide.stop()
            if getattr(self, "hk_scan", None):
                self.hk_scan.stop()
            if getattr(self, "kw", None):
                self.kw.stop()
        finally:
            try:
                h = getattr(single_instance, "handle", None)
                if h:
                    import ctypes
                    ctypes.windll.kernel32.CloseHandle(h)
                    single_instance.handle = None
            except Exception:
                pass
            try:
                pid_file = os.path.join(APP_DIR, "app.pid")
                if os.path.exists(pid_file):
                    os.remove(pid_file)
            except Exception:
                pass
            self.root.destroy()

    def autostart_toggled(self, value):
        try:
            if not system.set_autostart(value):
                self.log(tr("autostart_exe_only"))
        except OSError as ex:
            self.log(tr("error", e=ex))

    def check_update(self):
        found = system.check_update(VERSION)
        if found:
            self.ui.put(("update", *found))

    def run_update(self, ver, url, sha=None):
        if getattr(self, "_updating", False):
            return
        self._updating = True
        self.log(tr("updating", v=ver))

        def work():
            try:
                system.install_update(url, sha)
                self.ui.put(("quit",))
            except Exception as ex:
                self._updating = False
                self.log(tr("update_err", e=ex))
        threading.Thread(target=work, daemon=True).start()

    # ---------------- лиги ----------------
    def load_leagues(self):
        lst = Prices.fetch_leagues()
        if lst:
            self.ui.put(("leagues", lst))

    def apply_leagues(self, lst):
        self.leagues = lst
        if self.league_cb.winfo_exists():
            self.league_cb.configure(values=lst)
        if self.cfg["league"] not in lst:   # прошлая лига закончилась — берём текущую (первую в списке)
            old = self.cfg["league"]
            self.log(tr("league_switched", old=old, new=lst[0]))
            self.league_changed(lst[0])

    def league_changed(self, league):
        if league == self.cfg["league"] and self.prices.league == league:
            return
        self.cfg["league"] = league
        if self.league_cb.winfo_exists():
            self.league_cb.set(league)
        self.save_cfg()
        threading.Thread(target=self.load_prices, daemon=True).start()

    # ---------------- горячие клавиши ----------------
    def start_hide_hotkey(self):
        if getattr(self, "hk_hide", None):
            self.hk_hide.stop()
        vk, mods = self.cfg.get("hide_key", [0x48, MOD_CTRL | MOD_SHIFT])
        self.hk_hide = Hotkey(vk, mods, lambda: self.ui.put(("toggle_overlay",)))
        self.hk_hide.start()
        self.hk_hide.ready.wait(1)
        if not self.hk_hide.ok:
            self.log(tr("key_busy", k=key_name(vk, mods)))

    def start_scan_hotkey(self):
        if getattr(self, "hk_scan", None):
            self.hk_scan.stop()
        vk, mods = self.cfg.get("scan_key", [0x71, 0])
        self.hk_scan = Hotkey(vk, mods, lambda: self.ui.put(("scan_ultimatum",)))
        self.hk_scan.start()
        self.hk_scan.ready.wait(1)
        if not self.hk_scan.ok:
            self.log(tr("key_busy", k=key_name(vk, mods)))

    def start_hotkey(self):
        self.start_hide_hotkey()
        self.start_scan_hotkey()

    def toggle_overlay(self):
        self.hidden = not self.hidden
        if self.hidden:
            self.overlay.win.withdraw()
        else:
            self.overlay.win.deiconify()
            self.overlay.redraw()

    def scan_ultimatum(self):
        """Разовое ручное чтение экрана по нажатию клавиши (строго по правилам GGG: 1 нажатие = 1 чтение).
        Никакого фонового чтения экрана по таймеру."""
        if self.hidden:
            return
        try:
            is_open, has_rewards = self.advisor.scan_panel_state()
            if not is_open:
                self.ui.put(("clear", ""))
                self.status = ""
                self.log(tr("panel_not_found"))
                return

            dur = float(self.cfg.get("mod_seconds", 3.5))

            # Double Down бывает только на 2+ волне (когда уже есть награды / блок OR/Take)
            dd = self.cfg["dd_enabled"] and has_rewards and self.advisor.double_down()
            if dd:
                self.ui.put(("box", "dd", *DD_BOX, tr("dd_chip"), GREEN, True, "rect", dur))
                if self.cfg["sound"]:
                    beep("info")
            else:
                self.ui.put(("clear", "dd"))

            if not self.cfg["mods_enabled"]:
                self.ui.put(("clear", "mod"))
                self.status = ""
            else:
                mods = self.advisor.read()
                for img in self.advisor.unknown_icons(mods):
                    self.ui.put(("learn", img))
                marks, waves, status = self.advisor.advise(mods)
                self.ui.put(("clear", "mod"))
                for i, code, color in marks:
                    self.ui.put(("box", f"mod{i}", *mod_box(i), tr("chip_" + code), color, False, "ring", dur))
                self.status = status
                self.log(f"{tr('ultimatum_card')}: {status}")
        except Exception as ex:
            self.log(tr("error", e=repr(ex)))

    def capture_key(self, target="hide_key"):
        btn = self.scan_key_btn if target == "scan_key" else self.key_btn
        btn.configure(text=tr("press_key"))
        # Временно снимаем перехватываемый хоткей, чтобы старая клавиша (напр. F2) дошла до окна
        hk = self.hk_scan if target == "scan_key" else self.hk_hide
        if hk:
            hk.stop()
        self.root.focus_force()

        def finish(save=False, keycode=0, mods=0):
            self.root.unbind("<KeyPress>")
            self.root.unbind("<FocusOut>")
            if save:
                is_fn = (0x70 <= keycode <= 0x87) or (0x60 <= keycode <= 0x6F) or keycode in (
                    0x2D, 0x2E, 0x24, 0x23, 0x21, 0x22, 0x13, 0x91, 0xC0)
                bad = (not mods and not is_fn) or (mods == MOD_CTRL and keycode in (0x41, 0x43, 0x56, 0x58, 0x5A))
                if bad:
                    self.log(tr("key_bad"))
                else:
                    self.cfg[target] = [keycode, mods]
                    self.save_cfg()
            if target == "scan_key":
                self.start_scan_hotkey()
            else:
                self.start_hide_hotkey()
            if btn.winfo_exists():
                btn.configure(text=key_name(*self.cfg[target]))

        def on_key(ev):
            if ev.keycode in (16, 17, 18, 91, 92):  # одиночные Shift/Ctrl/Alt/Win — ждём основную клавишу
                return "break"
            if ev.keycode == 27:  # Esc — отмена
                finish(save=False)
                return "break"
            mods = (MOD_CTRL if ev.state & 0x4 else 0) | (MOD_SHIFT if ev.state & 0x1 else 0) | \
                   (1 if ev.state & 0x20000 else 0)
            finish(save=True, keycode=ev.keycode, mods=mods)
            return "break"

        def on_focus_out(ev):
            if ev.widget == self.root:
                finish(save=False)

        self.root.bind("<KeyPress>", on_key)
        self.root.bind("<FocusOut>", on_focus_out)

    def set_flag(self, key, value):
        self.cfg[key] = bool(value)
        self.save_cfg()

    def mods_toggled(self, value):
        self.cfg["mods_enabled"] = bool(value)
        self._mods_state_text()
        self.save_cfg()
        if not value:
            self.ui.put(("clear", "mod"))

    # ---------------- настройки ----------------
    def changed(self, *_):
        if getattr(self, "_job", None):
            self.root.after_cancel(self._job)
        self._job = self.root.after(500, self.save_cfg)

    def save_cfg(self):
        for k, var in self.v.items():
            if isinstance(var, tuple):
                if var[0].get() in var[1]:
                    self.cfg[k] = var[1][var[0].get()]
            else:
                s = var.get().strip().replace(",", ".")
                if isinstance(DEFAULT_CFG[k], (int, float)):
                    try:
                        s = type(DEFAULT_CFG[k])(float(s))
                    except (ValueError, OverflowError):
                        continue  # ещё печатают — оставляем прежнее значение
                self.cfg[k] = s
        self.scr.dx, self.scr.dy = self.cfg["offset_x"], self.cfg["offset_y"]
        try:
            write_json(CFG_FILE, self.cfg, indent=1)
        except OSError as ex:
            self.log(tr("error", e=ex))

    # ---------------- связь потоков с окном ----------------
    def log(self, msg, gold=False):
        self.ui.put(("log", time.strftime("%H:%M "), msg, gold))

    def _log_insert(self, t, msg, gold):
        self.logbox.configure(state="normal")
        self.logbox.insert("end", t, "time")
        self.logbox.insert("end", msg + "\n", "gold" if gold else ())
        if int(self.logbox.index("end-1c").split(".")[0]) > 500:
            self.logbox.delete("1.0", "100.0")
        self.logbox.see("end")
        self.logbox.configure(state="disabled")

    def pump(self):
        try:
            if self._pump_body() == "quit":
                return
        except Exception as ex:
            try:
                self._log_insert(time.strftime("%H:%M "), tr("error", e=repr(ex)), False)
            except Exception:
                pass
        self.root.after(100, self.pump)

    def _pump_body(self):
        while not self.ui.empty():
            kind, *a = self.ui.get()
            try:
                if self._handle(kind, a) == "quit":
                    return "quit"
            except Exception as ex:
                self.log(tr("error", e=repr(ex)))
        self._refresh_labels()

    def _handle(self, kind, a):
        if True:
            if kind == "log":
                self.log_lines.append(tuple(a))
                if len(self.log_lines) > 200:
                    self.log_lines = self.log_lines[-200:]
                self._log_insert(*a)
            elif kind == "price":
                self.overlay.price_card("price", *a, seconds=float(self.cfg["label_seconds"]))
            elif kind == "box":
                self.overlay.set_box(*a)
            elif kind == "clear":
                self.overlay.clear_boxes(a[0])
            elif kind == "dismiss_altar":
                if any(k.startswith("mod") or k == "dd" for k in self.overlay.boxes):
                    self.overlay.clear_boxes("")
            elif kind == "icons":
                self.render_icons()
            elif kind == "leagues":
                self.apply_leagues(a[0])
            elif kind == "toggle_overlay":
                self.toggle_overlay()
            elif kind == "scan_ultimatum":
                self.scan_ultimatum()
            elif kind == "show_window":
                self.show_window()
            elif kind == "quit":
                self.quit()
                return "quit"
            elif kind == "update":
                self.run_update(*a)
            elif kind == "learn":
                icons.add_icon(self.advisor.lib, a[0], tier="Mirage", allowed=False)
                icons.save_library(self.advisor.lib)
                self.render_icons()

    def _refresh_labels(self):
        cache = self._ui_cache
        if self.prices.divine:
            pt = tr("prices_info", league=self.prices.league,
                    div=f"{self.prices.divine:.0f}", n=len(self.prices.chaos))
            if cache.get("price") != pt:
                cache["price"] = pt
                self.price_lbl.configure(text=pt)
        if cache.get("status") != self.status:
            cache["status"] = self.status
            self.status_lbl.configure(text=self.status)
        found = poe_running()
        if cache.get("poe") != found:
            cache["poe"] = found
            self.poe_lbl.configure(text=tr("poe_found") if found else tr("poe_missing"),
                                   fg=T.GREEN if found else T.ORANGE)
        if cache.get("hid") != self.hidden:
            cache["hid"] = self.hidden
            self.hidden_lbl.configure(text=tr("overlay_hidden") if self.hidden else tr("overlay_shown"),
                                      fg=T.ORANGE if self.hidden else T.GREEN)
        if self.pw is not None and self.pw.win.winfo_exists():
            self.pw.refresh_if_needed()
        now = time.time()
        # периодическая проверка обновлений на GitHub (раз в 2 часа)
        if now - getattr(self, "_last_check_update", 0) > 7200:
            self._last_check_update = now
            threading.Thread(target=self.check_update, daemon=True).start()
        # раз в час — свежие цены с poe.ninja (в фоне); цен ещё нет (не было интернета) — пробуем раз в минуту
        stale = self.prices.updated and now - self.prices.updated > 3600
        never = not self.prices.updated and now - self.started > 20
        if (stale and now - getattr(self, "_last_try", 0) > 600) or \
                (never and now - getattr(self, "_last_try", 0) > 60):
            self._last_try = now
            threading.Thread(target=self.load_prices, args=(bool(stale),), daemon=True).start()

    # ================= рабочие потоки =================
    def load_prices(self, force=False):
        with self.prices.lock:
            try:
                lg = self.cfg["league"]
                if force:
                    self.prices.refresh(lg, log=self.log)
                else:
                    self.prices.load(lg, log=self.log)
            except Exception as ex:
                self.log(tr("prices_err", e=ex))

    def watch(self):
        """Фоновый цикл: ТОЛЬКО отслеживание Ctrl+C для прайсчека предметов.
        Скан экрана по таймеру ПОЛНОСТЬЮ ОТСУТСТВУЕТ (100% GGG ToS Safe).
        Скан ультиматума вызывается строго по ручному нажатию клавиши игроком."""
        seq = clipboard_seq()
        while True:
            try:
                # игрок нажал Ctrl+C на предмете -> карточка цены у курсора (ручное действие игрока)
                s = clipboard_seq()
                if s != seq:
                    seq = s
                    time.sleep(0.05)
                    try:
                        txt = pyperclip.paste()
                    except Exception:
                        txt = ""
                    # карточку показываем только на Ctrl+C самого игрока
                    if is_item_text(txt) and self.kw.user_copied(time.monotonic()):
                        x, y = cursor_pos()
                        info = price_info(txt, self.prices, float(self.cfg["div_threshold"]),
                                          life_alert=self.cfg["life_alert"],
                                          show_preview=self.cfg.get("show_reward_preview", True))
                        self.ui.put(("price", x, y, info))
                        self.log(info["line"], gold=info.get("good", False))
            except Exception as ex:
                self.log(tr("error", e=repr(ex)))
                time.sleep(1)
            time.sleep(0.05)


def _kill_pid(pid):
    try:
        import psutil
        try:
            p = psutil.Process(pid)
            for c in p.children(recursive=True):
                try:
                    c.kill()
                except Exception:
                    pass
            p.kill()
            return True
        except Exception:
            pass
    except ImportError:
        pass

    try:
        import subprocess
        subprocess.run(["taskkill", "/F", "/T", "/PID", str(pid)],
                       capture_output=True, timeout=2, creationflags=0x08000000)
        return True
    except Exception:
        pass

    try:
        import ctypes
        k32 = ctypes.windll.kernel32
        h = k32.OpenProcess(0x0001, False, pid)
        if h:
            k32.TerminateProcess(h, 0)
            k32.CloseHandle(h)
            return True
    except Exception:
        pass
    return False


def kill_previous_instances():
    """Завершает предыдущие копии программы, чтобы запустилась новая."""
    my_pid = os.getpid()
    my_ppid = os.getppid() if hasattr(os, "getppid") else 0
    safe_pids = {my_pid, my_ppid}

    # 1. По сохранённому pid-файлу
    pid_file = os.path.join(APP_DIR, "app.pid")
    if os.path.exists(pid_file):
        try:
            with open(pid_file, "r", encoding="utf-8") as f:
                old_pid = int(f.read().strip())
            if old_pid not in safe_pids:
                _kill_pid(old_pid)
        except Exception:
            pass

    # 2. По списку процессов через psutil
    try:
        import psutil
        is_frozen = getattr(sys, "frozen", False)
        for p in psutil.process_iter(["pid", "ppid", "name", "cmdline"]):
            try:
                pid = p.info["pid"]
                if pid in safe_pids:
                    continue
                name = (p.info["name"] or "").lower()
                if is_frozen:
                    if "ultimatumoverlay" in name:
                        _kill_pid(pid)
                else:
                    cmdline = p.info.get("cmdline") or []
                    cmd_str = " ".join(cmdline).lower()
                    if "main.py" in cmd_str and ("python" in name or "ultimatum" in cmd_str):
                        _kill_pid(pid)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
    except Exception:
        pass


def single_instance():
    """Если уже запущена копия программы, завершаем её и запускаем новую."""
    import ctypes
    k32 = ctypes.windll.kernel32
    single_instance.handle = k32.CreateMutexW(None, False, "Local\\UltimatumOverlaySingleInstance")
    if k32.GetLastError() == 183:  # ERROR_ALREADY_EXISTS
        k32.CloseHandle(single_instance.handle)
        kill_previous_instances()
        time.sleep(0.3)
        single_instance.handle = k32.CreateMutexW(None, False, "Local\\UltimatumOverlaySingleInstance")

    try:
        pid_file = os.path.join(APP_DIR, "app.pid")
        with open(pid_file, "w", encoding="utf-8") as f:
            f.write(str(os.getpid()))
    except Exception:
        pass
    return True


if __name__ == "__main__":
    single_instance()
    root = tk.Tk()
    App(root)
    root.mainloop()
