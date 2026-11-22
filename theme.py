"""Оформление: тёмная тема в цветах PoE и простые плоские виджеты на tkinter."""
import tkinter as tk
from tkinter import ttk

BG = "#0e0c0a"        # фон окна
CARD = "#191511"      # фон карточек
CARD2 = "#211b15"     # поля ввода, строки списка
LINE = "#3b2f22"      # рамки
TXT = "#e0d6c6"       # основной текст
MUTED = "#8f8473"     # второстепенный текст
GOLD = "#c9a14a"
GOLD_HI = "#ecc87a"
GREEN = "#55d46f"
RED = "#e2574c"
ORANGE = "#f0a040"

SERIF = "Georgia"
SANS = "Segoe UI"

# цвета тиров как на тир-листе
TIER_COLORS = {"Free": "#ff7f7f", "Easy": "#ffbf7f", "Moderate": "#ffdf7f", "Annoying": "#ffff7f",
               "DO NOT TAKE": "#bfff7f", "Exception": "#f0f0f0", "Mirage": "#b48cff"}

# цвета названий предметов как в игре
RARITY_COLORS = {"currency": "#aa9e82", "валюта": "#aa9e82", "unique": "#af6025", "уникальный": "#af6025",
                 "divination card": "#d8e6f0", "divination": "#d8e6f0", "card": "#d8e6f0", "гадальная карта": "#d8e6f0",
                 "gem": "#1ba29b", "камень": "#1ba29b",
                 "rare": "#ffff77", "редкий": "#ffff77", "magic": "#8888ff", "магический": "#8888ff",
                 "normal": "#c8c8c8", "white": "#c8c8c8", "обычный": "#c8c8c8"}


def apply_ttk(root):
    """Тёмный вид для выпадающих списков и полос прокрутки."""
    st = ttk.Style(root)
    st.theme_use("clam")
    st.configure("TCombobox", fieldbackground=CARD2, background=CARD2, foreground=TXT, arrowcolor=GOLD,
                 bordercolor=LINE, lightcolor=CARD2, darkcolor=CARD2, padding=4)
    st.map("TCombobox", fieldbackground=[("readonly", CARD2)], foreground=[("readonly", TXT)],
           selectbackground=[("readonly", CARD2)], selectforeground=[("readonly", TXT)])
    root.option_add("*TCombobox*Listbox.background", CARD2)
    root.option_add("*TCombobox*Listbox.foreground", TXT)
    root.option_add("*TCombobox*Listbox.selectBackground", GOLD)
    root.option_add("*TCombobox*Listbox.selectForeground", BG)
    st.configure("Vertical.TScrollbar", background=CARD2, troughcolor=BG, bordercolor=BG, arrowcolor=GOLD,
                 lightcolor=CARD2, darkcolor=CARD2)
    st.map("Vertical.TScrollbar", background=[("disabled", BG), ("active", "#3a2e20")],
           troughcolor=[("disabled", BG)], arrowcolor=[("disabled", LINE)])


def card(parent, title=None, pad=12):
    """Карточка: тёмный блок с тонкой рамкой и золотым заголовком."""
    outer = tk.Frame(parent, bg=LINE)
    inner = tk.Frame(outer, bg=CARD, padx=pad, pady=pad - 2)
    inner.pack(fill="both", expand=True, padx=1, pady=1)
    if title:
        tk.Label(inner, text=title.upper(), bg=CARD, fg=GOLD, font=(SERIF, 10, "bold")).pack(anchor="w",
                                                                                            pady=(0, 6))
    return outer, inner


def label(parent, text, fg=TXT, size=10, bold=False, bg=CARD, **kw):
    return tk.Label(parent, text=text, bg=bg, fg=fg, font=(SANS, size, "bold" if bold else "normal"), **kw)


def wrap_label(parent, text, fg=MUTED, size=9, bold=False, bg=CARD, anchor="w", **kw):
    """Надпись, которая переносится по ширине места: растянул окно — строка стала длиннее.
    Упаковывать с fill="x"."""
    lbl = tk.Label(parent, text=text, bg=bg, fg=fg, font=(SANS, size, "bold" if bold else "normal"),
                   justify="left", anchor=anchor, **kw)
    lbl.bind("<Configure>", lambda e: lbl.configure(
        wraplength=max(60, e.width - 2 * int(float(str(lbl.cget("padx")))) - 2)))
    return lbl


def entry(parent, var, width=8, bg=CARD2):
    return tk.Entry(parent, textvariable=var, width=width, bg=bg, fg=TXT, insertbackground=GOLD,
                    relief="flat", highlightthickness=1, highlightbackground=LINE, highlightcolor=GOLD,
                    font=(SANS, 10))


def button(parent, text, command, fg=GOLD, bg="#2a2219", small=False, width=None, hover="#3a2e20"):
    b = tk.Label(parent, text=text, bg=bg, fg=fg, cursor="hand2",
                 font=(SANS, 9 if small else 10, "bold"), padx=6 if small else 12, pady=1 if small else 4)
    if width:
        b.configure(width=width)
    b.bind("<Enter>", lambda e: b.configure(bg=hover))
    b.bind("<Leave>", lambda e: b.configure(bg=bg))
    b.bind("<Button-1>", lambda e: command())
    return b


class Toggle(tk.Canvas):
    """Переключатель-«пилюля»: вкл (зелёный) / выкл (серый)."""

    def __init__(self, parent, value, command, bg=CARD, on_text="", off_text=""):
        super().__init__(parent, width=46, height=24, bg=bg, highlightthickness=0, cursor="hand2")
        self.value = bool(value)
        self.command = command
        self.bind("<Button-1>", self._click)
        self.draw()

    def _click(self, _):
        self.value = not self.value
        self.draw()
        self.command(self.value)

    def draw(self):
        self.delete("all")
        col = GREEN if self.value else "#4a4038"
        pill(self, 2, 3, 44, 21, fill=col, outline="")
        x = 33 if self.value else 13
        self.create_oval(x - 8, 4, x + 8, 20, fill="#f4efe6", outline="")


def dark_titlebar(win):
    """Шапка окна Windows в цвет окна (Windows 10 20H1+ / 11): тёмный режим + цвет заголовка."""
    import ctypes
    try:
        win.update_idletasks()
        hwnd = ctypes.windll.user32.GetParent(win.winfo_id()) or win.winfo_id()
        dwm = ctypes.windll.dwmapi
        on = ctypes.c_int(1)
        for attr in (20, 19):  # DWMWA_USE_IMMERSIVE_DARK_MODE (новые и старые сборки)
            if dwm.DwmSetWindowAttribute(hwnd, attr, ctypes.byref(on), ctypes.sizeof(on)) == 0:
                break
        def colorref(h):
            r, g, b = int(h[1:3], 16), int(h[3:5], 16), int(h[5:7], 16)
            return ctypes.c_int(r | (g << 8) | (b << 16))
        for attr, col in ((35, BG), (36, GOLD_HI), (34, LINE)):  # цвет шапки, текста, рамки (Windows 11)
            c = colorref(col)
            dwm.DwmSetWindowAttribute(hwnd, attr, ctypes.byref(c), ctypes.sizeof(c))
        # перерисовать рамку, чтобы цвет применился сразу
        ctypes.windll.user32.SetWindowPos(hwnd, 0, 0, 0, 0, 0, 0x0001 | 0x0002 | 0x0004 | 0x0020)
    except Exception:
        pass


def pill(cv, x1, y1, x2, y2, **kw):
    """Скруглённый прямоугольник (радиус = половина высоты)."""
    r = (y2 - y1) / 2
    return round_rect(cv, x1, y1, x2, y2, r, **kw)


def round_rect(cv, x1, y1, x2, y2, r, **kw):
    """Скруглённый прямоугольник: ровные стороны и дуги по 10 точек в каждом углу."""
    import math
    r = max(0, min(r, (x2 - x1) / 2, (y2 - y1) / 2))
    pts = []
    for cx, cy, a0 in ((x2 - r, y1 + r, -90), (x2 - r, y2 - r, 0), (x1 + r, y2 - r, 90), (x1 + r, y1 + r, 180)):
        for i in range(11):
            a = math.radians(a0 + 9 * i)
            pts += [cx + r * math.cos(a), cy + r * math.sin(a)]
    return cv.create_polygon(pts, smooth=False, **kw)
