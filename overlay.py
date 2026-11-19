"""Прозрачное окно поверх игры. Клики проходят сквозь него в игру."""
import ctypes
import time
import tkinter as tk

import theme as T
from i18n import tr
from screen import REF_H, REF_W, Screen

user32 = ctypes.windll.user32
KEY = "#ff00fe"  # этот цвет становится прозрачным
INK = "#0e0c0a"  # тёмная заливка карточек и текст на цветных плашках


def _dim(hex_color, k):
    """Темнее/приглушённее цвет (для «свечения» вокруг рамок)."""
    r, g, b = (int(hex_color[i:i + 2], 16) for i in (1, 3, 5))
    return "#%02x%02x%02x" % (int(r * k), int(g * k), int(b * k))


class Overlay:
    def __init__(self, root, scr: Screen):
        self.scr = scr
        self.win = tk.Toplevel(root)
        self.win.overrideredirect(True)
        self.win.attributes("-topmost", True)
        self.win.attributes("-transparentcolor", KEY)
        self.win.configure(bg=KEY)
        self.cv = tk.Canvas(self.win, bg=KEY, highlightthickness=0)
        self.cv.pack(fill="both", expand=True)
        self.cards = {}   # ключ -> (x, y экрана, info, до какого времени)
        self.boxes = {}   # ключ -> (x1, y1, x2, y2, подпись, цвет, мигать, форма)
        self.phase = 0
        self.rect = (0, 0, 1, 1)
        self.win.update_idletasks()
        self._click_through()
        self._tick()

    def _click_through(self):
        hwnd = user32.GetParent(self.win.winfo_id()) or self.win.winfo_id()
        style = user32.GetWindowLongW(hwnd, -20)  # GWL_EXSTYLE
        # LAYERED | TRANSPARENT (клики насквозь) | TOOLWINDOW | NOACTIVATE
        user32.SetWindowLongW(hwnd, -20, style | 0x80000 | 0x20 | 0x80 | 0x08000000)

    def _place(self):
        """Держать оверлей ровно над окном игры (сверяем реальное положение — первое
        перемещение Windows может проигнорировать, и окно игры могут двигать)."""
        r = self.scr.rect()
        self.rect = r
        L, T_, W, H = r
        if (self.win.winfo_rootx(), self.win.winfo_rooty(), self.win.winfo_width(),
                self.win.winfo_height()) != (L, T_, W, H):
            self.win.geometry(f"{W}x{H}+{L}+{T_}")

    def _xy(self, x, y):
        L, T_, W, H = self.rect
        s = H / REF_H
        return W / 2 + (x - REF_W / 2 + self.scr.dx) * s, (y + self.scr.dy) * s

    # ---------- API ----------
    def price_card(self, key, sx, sy, info, seconds=8.0):
        self.cards[key] = (sx, sy, info, time.time() + seconds)
        self.redraw()

    def set_box(self, key, x1, y1, x2, y2, text="", color=T.GREEN, blink=False, shape="rect"):
        val = (x1, y1, x2, y2, text, color, blink, shape)
        if self.boxes.get(key) != val:
            self.boxes[key] = val
            self.redraw()

    def clear_boxes(self, prefix=""):
        keys = [k for k in self.boxes if k.startswith(prefix)]
        for k in keys:
            del self.boxes[k]
        if keys:
            self.redraw()

    def _tick(self):
        try:
            self._tick_body()
        except Exception:
            pass
        finally:
            self.win.after(380, self._tick)

    def _tick_body(self):
        now = time.time()
        expired = [k for k, v in self.cards.items() if v[3] < now]
        for k in expired:
            del self.cards[k]
        if any(b[6] for b in self.boxes.values()):
            self.phase = (self.phase + 1) % 2
            self.redraw()
        elif expired:
            self.redraw()
        else:
            self._place()  # окно игры могли передвинуть

    # ---------- рисование ----------
    def redraw(self):
        self._place()
        self.cv.delete("all")
        s = self.rect[3] / REF_H
        for b in self.boxes.values():
            (self._ring if b[7] == "ring" else self._glow_rect)(s, *b[:7])
        for sx, sy, info, _ in self.cards.values():
            self._card(s, sx, sy, info)
        self.win.lift()
        self.win.attributes("-topmost", True)

    def _chip(self, s, cx, y, text, color, above=True):
        """Плашка с текстом: цветная заливка, тёмные буквы."""
        f = (T.SANS, max(9, int(13 * s)), "bold")
        t = self.cv.create_text(cx, 0, text=text, fill=INK, font=f)
        x1, y1, x2, y2 = self.cv.bbox(t)
        h, w = y2 - y1, x2 - x1
        pad_x, pad_y = 10 * s, 3 * s
        top = y - h - 2 * pad_y if above else y
        self.cv.coords(t, cx, top + pad_y + h / 2)
        bg = T.pill(self.cv, cx - w / 2 - pad_x, top, cx + w / 2 + pad_x, top + h + 2 * pad_y, fill=color,
                    outline="")
        self.cv.tag_lower(bg, t)

    def _ring(self, s, x1, y1, x2, y2, text, color, blink):
        ax, ay = self._xy(x1, y1)
        bx, by = self._xy(x2, y2)
        p = 5 * s
        w = max(3, int(4 * s))
        self.cv.create_oval(ax - p - 4 * s, ay - p - 4 * s, bx + p + 4 * s, by + p + 4 * s,
                            outline=_dim(color, 0.45), width=max(2, int(3 * s)))      # мягкое «свечение»
        self.cv.create_oval(ax - p, ay - p, bx + p, by + p, outline=color, width=w)
        if text:
            self._chip(s, (ax + bx) / 2, ay - p - 8 * s, text, color, above=True)

    def _glow_rect(self, s, x1, y1, x2, y2, text, color, blink):
        ax, ay = self._xy(x1, y1)
        bx, by = self._xy(x2, y2)
        col = (T.GOLD_HI if self.phase else color) if blink else color
        p = 7 * s
        for k, (grow, width, dim) in enumerate(((12, 2, 0.3), (6, 3, 0.55), (0, 5, 1.0))):
            g = grow * s
            T.round_rect(self.cv, ax - p - g, ay - p - g, bx + p + g, by + p + g, 10 * s + g,
                         outline=_dim(col, dim), fill="", width=max(1, int(width * s)))
        if text:
            self._chip(s, (ax + bx) / 2, by + p + 14 * s, f"▲  {text}  ▲", col, above=False)

    def _card(self, s, sx, sy, info):
        """Карточка цены у курсора."""
        L, T_, W, H = self.rect
        k = max(1.0, s)
        pad = 12 * k
        name_col = T.RARITY_COLORS.get(info.get("rarity", "").lower(), T.TXT)
        good = info.get("good")
        border = T.GOLD if good else "#5a4630"
        items = []  # (текст, шрифт, цвет)
        items.append((info["name"], (T.SERIF, int(14 * k), "bold"), name_col))
        if info.get("life"):
            items.append(("life", None, None))
        if info.get("error"):
            items.append((info["error"], (T.SANS, int(10 * k)), "#ff9a8a"))
        else:
            if info.get("detail"):
                items.append((info["detail"], (T.SANS, max(9, int(10 * k))), T.MUTED))
            items.append(("price", None, None))
        # измеряем
        x0, y0 = sx - L + 22 * k, sy - T_ + 22 * k
        ids, y, width = [], y0 + pad + 3 * k, 0
        for text, font, col in items:
            if text == "life":
                pct = info["life"]
                col = T.RED if pct >= 200 else T.ORANGE if pct >= 120 else T.GREEN
                life_txt = (f"{pct}% больше здоровья монстров" if info.get("life_lang") == "ru"
                            else f"{pct}% more Monster Life")
                t = self.cv.create_text(x0 + pad + 10 * k, y + 3 * k, text=life_txt.upper(),
                                        anchor="nw", font=(T.SANS, max(9, int(11 * k)), "bold"), fill=INK)
                bx1, by1, bx2, by2 = self.cv.bbox(t)
                chip = T.round_rect(self.cv, bx1 - 10 * k, by1 - 3 * k, bx2 + 10 * k, by2 + 3 * k, 6 * k,
                                    fill=col, outline="")
                self.cv.tag_lower(chip, t)
                ids += [chip, t]
                width = max(width, bx2 + 10 * k - x0 - pad)
                y = by2 + 9 * k
                continue
            if text == "price":
                big = (T.SERIF, int(22 * k), "bold")
                c_id = self.cv.create_text(x0 + pad, y, text=f"{info['chaos_text']} c", anchor="nw", font=big,
                                           fill=T.GOLD_HI if good else T.TXT)
                bx1, by1, bx2, by2 = self.cv.bbox(c_id)
                d_id = self.cv.create_text(bx2 + 10 * k, by2 - 4 * k, text=f"≈ {info['div']:.2f} div", anchor="sw",
                                           font=(T.SANS, int(12 * k), "bold"), fill=T.GOLD if good else T.MUTED)
                ids += [c_id, d_id]
                if info.get("net"):
                    n_id = self.cv.create_text(self.cv.bbox(d_id)[2] + 10 * k, by2 - 5 * k, text=tr("net_profit"),
                                               anchor="sw", font=(T.SANS, max(9, int(10 * k))), fill=T.MUTED)
                    ids.append(n_id)
                    d_id = n_id
                width = max(width, self.cv.bbox(d_id)[2] - x0 - pad)
                y = by2 + 2 * k
                if info.get("mine"):
                    m_id = self.cv.create_text(x0 + pad, y + 2 * k, text=tr("your_price"), anchor="nw",
                                               font=(T.SANS, max(9, int(9 * k)), "bold"), fill=T.GREEN)
                    ids.append(m_id)
                    width = max(width, self.cv.bbox(m_id)[2] - x0 - pad)
                    y = self.cv.bbox(m_id)[3] + 2 * k
                if info.get("shaky"):
                    w_id = self.cv.create_text(x0 + pad, y + 2 * k, text=tr("low_data"),
                                               anchor="nw", font=(T.SANS, int(9 * k), "bold"), fill=T.ORANGE)
                    ids.append(w_id)
                    width = max(width, self.cv.bbox(w_id)[2] - x0 - pad)
                    y = self.cv.bbox(w_id)[3] + 2 * k
            else:
                t = self.cv.create_text(x0 + pad, y, text=text, anchor="nw", font=font, fill=col)
                ids.append(t)
                bx1, by1, bx2, by2 = self.cv.bbox(t)
                width = max(width, bx2 - x0 - pad)
                y = by2 + 4 * k
        x1, y1, x2, y2 = x0, y0, x0 + width + 2 * pad, y + pad - 2 * k
        # не вылезать за край окна игры: справа — ставим слева от курсора, снизу — поднимаем
        dx = -(x2 - x1) - 44 * k if x2 > W - 8 else 0
        dy = (H - 8 - y2) if y2 > H - 8 else 0
        for i in ids:
            self.cv.move(i, dx, dy)
        x1, x2, y1, y2 = x1 + dx, x2 + dx, y1 + dy, y2 + dy
        bg = T.round_rect(self.cv, x1, y1, x2, y2, 8 * k, fill=INK, outline=border, width=max(1, int(2 * k)))
        bar = self.cv.create_rectangle(x1 + 10 * k, y1, x2 - 10 * k, y1 + 3 * k, fill=border, outline="")
        self.cv.tag_lower(bar, ids[0])  # подложка под текстом, но над рамками модов
        self.cv.tag_lower(bg, bar)
