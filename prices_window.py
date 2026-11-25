"""Окно «Цены»: все цены poe.ninja, ненадёжные (с «?») и свои. Тут же можно вписать свою цену."""
import re
import tkinter as tk
from tkinter import ttk

import i18n
import theme as T
from i18n import tr

TABS = [("all", "tab_all"), ("low", "tab_low"), ("mine", "tab_mine")]


def parse_price(text, divine):
    """'150' / '150c' -> хаосы; '2div' / '2 д' / '1.5d' -> дивайны в хаосах. None — не понял."""
    t = text.strip().lower().replace(",", ".").replace(" ", "")
    m = re.fullmatch(r"(\d+(?:\.\d+)?)(c|с|ch|chaos|хаос)?", t)
    if m:
        return float(m.group(1))
    m = re.fullmatch(r"(\d+(?:\.\d+)?)(d|div|divine|д|див)", t)
    if m and divine:
        return float(m.group(1)) * divine
    return None


def fmt_c(v):
    return "" if v is None else (f"{v:.1f}" if v < 10 else f"{v:,.0f}".replace(",", " "))


class PricesWindow:
    def __init__(self, root, prices, on_change=None, names_lang="en", on_names_lang=None):
        self.names_lang = names_lang                       # язык названий предметов — свой, не как у программы
        self.on_names_lang = on_names_lang or (lambda lang: None)
        self.p = prices
        self.on_change = on_change or (lambda: None)
        self.tab = "low"
        self.shown_at = None
        w = self.win = tk.Toplevel(root)
        w.title(tr("pw_title"))
        w.geometry("780x640")
        w.minsize(600, 420)
        w.configure(bg=T.BG)
        self._style(w)
        w.after(50, lambda: T.dark_titlebar(w))

        head = tk.Frame(w, bg=T.BG, padx=16, pady=12)
        head.pack(fill="x")
        tk.Label(head, text=tr("pw_title").upper(), bg=T.BG, fg=T.GOLD_HI, font=(T.SERIF, 18, "bold")).pack(side="left")
        self.info = tk.Label(head, text="", bg=T.BG, fg=T.MUTED, font=(T.SANS, 9))
        self.info.pack(side="left", padx=12, pady=(6, 0))
        tk.Frame(w, bg=T.GOLD, height=1).pack(fill="x", padx=16)

        bar = tk.Frame(w, bg=T.BG, padx=16, pady=10)
        bar.pack(fill="x")
        self.tab_btns = {}
        for key, title in TABS:
            b = tk.Label(bar, text=tr(title), bg=T.CARD2, fg=T.MUTED, cursor="hand2", font=(T.SANS, 10, "bold"),
                         padx=14, pady=5)
            b.pack(side="left", padx=(0, 4))
            b.bind("<Button-1>", lambda e, k=key: self.set_tab(k))
            self.tab_btns[key] = (b, title)
        self.q = tk.StringVar()
        self.q.trace_add("write", lambda *a: self.fill())
        T.entry(bar, self.q, 24).pack(side="right", ipady=4)
        tk.Label(bar, text=tr("search"), bg=T.BG, fg=T.MUTED, font=(T.SANS, 9)).pack(side="right", padx=6)
        # язык названий предметов
        self.nl_btns = {}
        for code in ("en", "ru"):
            b = tk.Label(bar, text=code.upper(), font=(T.SANS, 9, "bold"), padx=8, pady=3, cursor="hand2")
            b.pack(side="right", padx=(0, 2))
            b.bind("<Button-1>", lambda e, c=code: self.set_names_lang(c))
            self.nl_btns[code] = b
        tk.Label(bar, text=tr("item_names"), bg=T.BG, fg=T.MUTED, font=(T.SANS, 9)).pack(side="right", padx=(16, 6))
        self._paint_nl()

        self.hint = T.wrap_label(w, "", bg=T.BG, padx=16)
        self.hint.pack(fill="x")

        mid = tk.Frame(w, bg=T.BG, padx=16, pady=6)
        mid.pack(fill="both", expand=True)
        cols = ("name", "cat", "ninja", "mine", "div")
        self.tv = ttk.Treeview(mid, columns=cols, show="headings", style="Dark.Treeview", selectmode="browse")
        for c, t, wd, anchor in (("name", tr("col_item"), 260, "w"), ("cat", tr("col_cat"), 140, "w"),
                                 ("ninja", tr("col_ninja"), 100, "e"), ("mine", tr("col_mine"), 90, "e"),
                                 ("div", "≈ div", 70, "e")):
            self.tv.heading(c, text=t, anchor=anchor)
            self.tv.column(c, width=wd, anchor=anchor, stretch=(c == "name"))
        self.tv.tag_configure("low", foreground=T.ORANGE)
        self.tv.tag_configure("mine", foreground=T.GREEN)
        sb = ttk.Scrollbar(mid, orient="vertical", command=self.tv.yview)
        self.tv.configure(yscrollcommand=sb.set)
        self.tv.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        self.tv.bind("<<TreeviewSelect>>", lambda e: self.select())
        self.tv.bind("<Double-1>", lambda e: self.price_entry.focus_set())

        # --- своя цена ---
        o, c = T.card(w, None, pad=12)
        o.pack(fill="x", padx=16, pady=(4, 14))
        self.sel_lbl = tk.Label(c, text=tr("pick_item"), bg=T.CARD, fg=T.TXT,
                                font=(T.SERIF, 12, "bold"), anchor="w")
        self.sel_lbl.pack(fill="x")
        r = tk.Frame(c, bg=T.CARD)
        r.pack(fill="x", pady=(8, 0))
        T.label(r, tr("own_price"), fg=T.MUTED).pack(side="left")
        self.pv = tk.StringVar()
        self.price_entry = T.entry(r, self.pv, 12)
        self.price_entry.pack(side="left", padx=8, ipady=3)
        self.price_entry.bind("<Return>", lambda e: self.save())
        T.label(r, tr("own_hint"), fg=T.MUTED, size=9).pack(side="left")
        T.button(r, tr("remove_own"), self.clear, small=True, fg=T.MUTED).pack(side="right")
        T.button(r, tr("save"), self.save, small=True).pack(side="right", padx=6)
        self.msg = T.label(c, "", fg=T.MUTED, size=9)
        self.msg.pack(anchor="w", pady=(6, 0))
        self.key = None
        self.set_tab(self.tab)

    @staticmethod
    def _style(w):
        st = ttk.Style(w)
        st.configure("Dark.Treeview", background=T.CARD, fieldbackground=T.CARD, foreground=T.TXT,
                     rowheight=24, bordercolor=T.LINE, font=(T.SANS, 10))
        st.configure("Dark.Treeview.Heading", background=T.CARD2, foreground=T.GOLD, relief="flat",
                     font=(T.SANS, 9, "bold"))
        st.map("Dark.Treeview", background=[("selected", "#3a2e20")], foreground=[("selected", T.GOLD_HI)])
        st.map("Dark.Treeview.Heading", background=[("active", "#2a2219")])

    # ---------- список ----------
    def set_tab(self, key):
        self.tab = key
        for k, (b, title) in self.tab_btns.items():
            on = k == key
            b.configure(bg=T.GOLD if on else T.CARD2, fg=T.BG if on else T.MUTED)
        self.hint.configure(text=tr("hint_" + key))
        self.fill()

    def rows(self):
        p = self.p
        keys = set(p.chaos) | set(p.custom)
        if self.tab == "low":
            keys = {k for k in keys if k in p.low}
        elif self.tab == "mine":
            keys = {k for k in keys if k in p.custom}
        q = self.q.get().strip().lower()
        if q:
            q_yo = q.replace("ё", "е")
            # по-русски ищем через словарь русских названий (учитывая ё/е)
            en = {k for k, r in p.ru_names.items() if q_yo in r.lower().replace("ё", "е")} if not q.isascii() else set()
            keys = {k for k in keys if q in k or k in en}
        return sorted(keys, key=lambda k: -(p.custom.get(k) or p.chaos.get(k) or 0))

    def fill(self):
        p = self.p
        self.tv.delete(*self.tv.get_children())
        for k in self.rows()[:3000]:
            ninja, mine = p.chaos.get(k), p.custom.get(k)
            val = mine if mine is not None else ninja
            div = f"{val / p.divine:.2f}" if val is not None and p.divine else ""
            tag = "mine" if mine is not None else "low" if k in p.low else ""
            self.tv.insert("", "end", iid=k, tags=(tag,),
                           values=(p.display(k, self.names_lang) + ("  ?" if tag == "low" else ""), i18n.cat(p.cat.get(k)),
                                   fmt_c(ninja), fmt_c(mine), div))
        n_low = sum(1 for k in p.chaos if k in p.low)
        for k, (b, title) in self.tab_btns.items():
            cnt = {"all": len(p.chaos), "low": n_low, "mine": len(p.custom)}[k]
            b.configure(text=f"{tr(title)}  {cnt}")
        self.info.configure(text=f"{p.league}  ·  1 div = {p.divine:.0f} c" if p.divine else tr("prices_loading"))
        self.shown_at = p.updated
        if self.key and self.tv.exists(self.key):
            self.tv.selection_set(self.key)
            self.tv.see(self.key)

    # ---------- своя цена ----------
    def select(self):
        sel = self.tv.selection()
        if not sel:
            return
        self.key = sel[0]
        p = self.p
        ninja = p.chaos.get(self.key)
        self.sel_lbl.configure(text=p.display(self.key, self.names_lang))
        self.pv.set(fmt_c(p.custom[self.key]).replace(" ", "") if self.key in p.custom else "")
        self.msg.configure(text=f"poe.ninja: {fmt_c(ninja)} c" + (f"  ·  {tr('low_data_short')}" if self.key in p.low
                                                                    else "")
                           if ninja is not None else tr("not_on_ninja"), fg=T.MUTED)

    def save(self):
        if not self.key:
            return
        v = parse_price(self.pv.get(), self.p.divine)
        if v is None:
            self.msg.configure(text=tr("bad_price"), fg=T.RED)
            return
        self.p.set_custom(self.key, v)
        self.msg.configure(text=tr("saved_price", c=fmt_c(v)), fg=T.GREEN)
        self.fill()
        self.on_change()

    def clear(self):
        if not self.key or self.key not in self.p.custom:
            return
        self.p.set_custom(self.key, None)
        self.pv.set("")
        self.msg.configure(text=tr("removed_price"), fg=T.MUTED)
        self.fill()
        self.on_change()

    def _paint_nl(self):
        for c, b in self.nl_btns.items():
            on = c == self.names_lang
            b.configure(bg=T.GOLD if on else T.CARD2, fg=T.BG if on else T.MUTED)

    def set_names_lang(self, code):
        if code != self.names_lang:
            self.names_lang = code
            self._paint_nl()
            self.on_names_lang(code)
            self.fill()
            if self.key:
                self.sel_lbl.configure(text=self.p.display(self.key, code))

    def refresh_if_needed(self):
        """Цены обновились — перерисовать список."""
        if self.p.updated != self.shown_at:
            self.fill()
