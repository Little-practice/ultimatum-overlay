"""Прозрачное окно поверх игры. Клики проходят сквозь него в игру."""
import ctypes
import re
import time
import tkinter as tk

import preview
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
        self._img_refs = []
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

    def _box(self, item_id, default=(0, 0, 0, 0)):
        return self.cv.bbox(item_id) or default

    # ---------- API ----------
    def price_card(self, key, sx, sy, info, seconds=8.0):
        self.cards[key] = (sx, sy, info, time.time() + seconds)
        self.redraw()

    def set_box(self, key, x1, y1, x2, y2, text="", color=T.GREEN, blink=False, shape="rect", seconds=3.5):
        expires_at = (time.time() + seconds) if seconds else None
        val = (x1, y1, x2, y2, text, color, blink, shape, expires_at)
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
        expired_boxes = [k for k, v in self.boxes.items() if len(v) > 8 and v[8] is not None and v[8] < now]
        for k in expired_boxes:
            del self.boxes[k]
        if any(b[6] for b in self.boxes.values()):
            self.phase = (self.phase + 1) % 2
            self.redraw()
        elif expired or expired_boxes:
            self.redraw()
        else:
            self._place()  # окно игры могли передвинуть

    # ---------- рисование ----------
    def redraw(self):
        self._place()
        self.cv.delete("all")
        self._img_refs = []
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

    def _draw_preview_card(self, k, x0, y, prev, ids):
        """Отрисовка карточки гадальной карты в стиле PoE (как в игре)."""
        card_w = max(int(290 * k), 270)
        start_y = y
        h_h = 32 * k
        banner = T.round_rect(self.cv, x0, y, x0 + card_w, y + h_h, 4 * k, fill="#ded6c4", outline="#2b2620", width=1)
        name_clean = re.sub(r'<[^>]+>', '', prev.get("name", "")).strip()
        t_name = self.cv.create_text(x0 + card_w / 2, y + h_h / 2, text=name_clean.upper(),
                                     font=(T.SERIF, max(10, int(12 * k)), "bold"), fill="#1a1612", anchor="center")
        ids += [banner, t_name]
        y += h_h + 8 * k

        art_w, art_h = int(240 * k), int(144 * k)
        photo = preview.get_image(prev.get("art_url"), art_w, art_h, on_ready=lambda: self.win.after(0, self.redraw),
                                  image_file=prev.get("image_file"), item_type="cards")
        if photo:
            self._img_refs.append(photo)
            pw, ph = photo.width(), photo.height()
            frame = self.cv.create_rectangle(x0 + card_w / 2 - pw / 2 - 2, y - 2,
                                            x0 + card_w / 2 + pw / 2 + 2, y + ph + 2,
                                            fill="#000000", outline="#4a5260", width=1)
            img_id = self.cv.create_image(x0 + card_w / 2, y, image=photo, anchor="n")
            ids += [frame, img_id]
            y += ph + 10 * k
        else:
            y += 4 * k

        stk = prev.get("stack", 1)
        bx_w, bx_h = 28 * k, 26 * k
        stk_bg = T.round_rect(self.cv, x0 + 14 * k, y, x0 + 14 * k + bx_w, y + bx_h, 3 * k,
                              fill="#1c2028", outline="#7a8494", width=1)
        stk_t = self.cv.create_text(x0 + 14 * k + bx_w / 2, y + bx_h / 2, text=str(stk),
                                    font=(T.SANS, max(10, int(11 * k)), "bold"), fill="#ffffff", anchor="center")
        ids += [stk_bg, stk_t]

        r_col = T.RARITY_COLORS.get(prev.get("reward_type", "unique"), T.GOLD)
        rw_clean = re.sub(r'<[^>]+>', '', prev.get("reward", "")).strip()
        rw_t = self.cv.create_text(x0 + 14 * k + bx_w + 10 * k, y + 2 * k, text=rw_clean,
                                   anchor="nw", font=(T.SERIF, max(11, int(12 * k)), "bold"), fill=r_col,
                                   width=int(card_w - (bx_w + 32 * k)))
        ids.append(rw_t)
        rw_bbox = self._box(rw_t)
        y = max(y + bx_h, rw_bbox[3] if rw_bbox else y + bx_h) + 10 * k

        flav = prev.get("flavour")
        if flav:
            flav_clean = re.sub(r'<[^>]+>', '', flav).strip()
            div_l = self.cv.create_line(x0 + 14 * k, y, x0 + card_w - 14 * k, y, fill="#2a303a")
            ids.append(div_l)
            y += 8 * k
            fl_t = self.cv.create_text(x0 + card_w / 2, y, text=flav_clean, anchor="n",
                                       font=(T.SERIF, max(8, int(9 * k)), "italic"), fill="#8a94a4",
                                       width=int(card_w - 28 * k), justify="center")
            ids.append(fl_t)
            y = self._box(fl_t, (0, 0, 0, y))[3] + 8 * k

        card_bg = T.round_rect(self.cv, x0 - 4 * k, start_y - 4 * k, x0 + card_w + 4 * k, y, 6 * k,
                               fill="#121316", outline="#3d4450", width=max(1, int(2 * k)))
        self.cv.tag_lower(card_bg, banner)
        ids.append(card_bg)
        return card_w + 8 * k, y - start_y + 4 * k

    def _draw_preview_unique(self, k, x0, y, prev, ids):
        """Отрисовка карточки уникального предмета в стиле PoE (как в игре)."""
        box_w = max(int(320 * k), 280)
        start_y = y

        col_u = "#af6025"
        name_clean = re.sub(r'<[^>]+>', '', prev.get("name", "")).strip()
        base_clean = re.sub(r'<[^>]+>', '', prev.get("base", "")).strip()

        t_name = self.cv.create_text(x0 + box_w / 2, y, text=name_clean.upper(), anchor="n",
                                     font=(T.SERIF, max(11, int(13 * k)), "bold"), fill=col_u)
        ids.append(t_name)
        y = self._box(t_name, (0, 0, 0, y))[3] + 2 * k

        t_base = self.cv.create_text(x0 + box_w / 2, y, text=base_clean.upper(), anchor="n",
                                     font=(T.SANS, max(9, int(10 * k)), "bold"), fill="#c87030")
        ids.append(t_base)
        y = self._box(t_base, (0, 0, 0, y))[3] + 8 * k

        div1 = self.cv.create_line(x0 + 16 * k, y, x0 + box_w - 16 * k, y, fill="#3d2812")
        ids.append(div1)
        y += 8 * k

        lvl = prev.get("level")
        if lvl:
            req_str = f"{tr('req_level')} {lvl}" if prev.get("lang") == "ru" else f"Requires Level {lvl}"
            t_req = self.cv.create_text(x0 + box_w / 2, y, text=req_str, anchor="n",
                                        font=(T.SANS, max(9, int(10 * k))), fill="#7e7468")
            ids.append(t_req)
            y = self._box(t_req, (0, 0, 0, y))[3] + 6 * k
            div2 = self.cv.create_line(x0 + 16 * k, y, x0 + box_w - 16 * k, y, fill="#3d2812")
            ids.append(div2)
            y += 8 * k

        imps = prev.get("implicits") or []
        for imp in imps:
            imp_clean = re.sub(r'<[^>]+>', '', imp).strip()
            t_imp = self.cv.create_text(x0 + box_w / 2, y, text=imp_clean, anchor="n",
                                        font=(T.SANS, max(9, int(10 * k))), fill="#7e9cff",
                                        width=int(box_w - 24 * k), justify="center")
            ids.append(t_imp)
            y = self._box(t_imp, (0, 0, 0, y))[3] + 4 * k
        if imps:
            div3 = self.cv.create_line(x0 + 16 * k, y, x0 + box_w - 16 * k, y, fill="#3d2812")
            ids.append(div3)
            y += 8 * k

        exps = prev.get("explicits") or []
        for exp in exps:
            exp_clean = re.sub(r'<[^>]+>', '', exp).strip()
            t_exp = self.cv.create_text(x0 + box_w / 2, y, text=exp_clean, anchor="n",
                                        font=(T.SANS, max(9, int(10 * k))), fill="#7e9cff",
                                        width=int(box_w - 24 * k), justify="center")
            ids.append(t_exp)
            y = self._box(t_exp, (0, 0, 0, y))[3] + 4 * k

        flav = prev.get("flavour")
        if flav:
            flav_clean = re.sub(r'<[^>]+>', '', flav).strip()
            div4 = self.cv.create_line(x0 + 16 * k, y, x0 + box_w - 16 * k, y, fill="#3d2812")
            ids.append(div4)
            y += 8 * k
            for fl in flav_clean.splitlines():
                if fl.strip():
                    t_fl = self.cv.create_text(x0 + box_w / 2, y, text=fl.strip(), anchor="n",
                                               font=(T.SERIF, max(8, int(9 * k)), "italic"), fill="#8a4f1e",
                                               width=int(box_w - 24 * k), justify="center")
                    ids.append(t_fl)
                    y = self._box(t_fl, (0, 0, 0, y))[3] + 3 * k
            y += 4 * k

        icon_url = prev.get("icon_url")
        if icon_url:
            max_iw, max_ih = int(120 * k), int(130 * k)
            photo = preview.get_image(icon_url, max_iw, max_ih, on_ready=lambda: self.win.after(0, self.redraw),
                                      image_file=prev.get("image_file"), item_type="uniques")
            if photo:
                self._img_refs.append(photo)
                img_id = self.cv.create_image(x0 + box_w / 2, y, image=photo, anchor="n")
                ids.append(img_id)
                y = self._box(img_id, (0, 0, 0, y))[3] + 8 * k
            else:
                y += 4 * k

        box_bg = T.round_rect(self.cv, x0 - 4 * k, start_y - 4 * k, x0 + box_w + 4 * k, y, 6 * k,
                              fill="#0c0a08", outline="#5a3d1c", width=max(1, int(2 * k)))
        self.cv.tag_lower(box_bg, t_name)
        ids.append(box_bg)
        return box_w + 8 * k, y - start_y + 4 * k

    def _card(self, s, sx, sy, info):
        """Карточка цены у курсора."""
        L, T_, W, H = self.rect
        k = max(1.0, s)
        pad = 12 * k
        name_col = T.RARITY_COLORS.get(info.get("rarity", "").lower(), T.TXT)
        good = info.get("good")
        border = T.GOLD if good else "#5a4630"
        x0, y0 = sx - L + 22 * k, sy - T_ + 22 * k
        ids, y, width = [], y0 + pad + 3 * k, 0

        prev = info.get("preview") if not info.get("error") else None
        if prev:
            # 1. Заголовок Ультиматума
            t_title = self.cv.create_text(x0 + pad, y, text=info["name"], anchor="nw",
                                          font=(T.SERIF, max(11, int(13 * k)), "bold"), fill=name_col)
            ids.append(t_title)
            bx1, by1, bx2, by2 = self._box(t_title, (x0, y, x0 + 100, y + 20))
            width = max(width, bx2 - x0 - pad)
            y = by2 + 8 * k

            # 2. Карточка предмета-награды (гадание или уник)
            ptype = prev.get("type")
            if ptype == "card":
                pw, ph = self._draw_preview_card(k, x0 + pad, y, prev, ids)
            elif ptype == "unique":
                pw, ph = self._draw_preview_unique(k, x0 + pad, y, prev, ids)
            else:
                pw, ph = 0, 0

            width = max(width, pw)
            y += ph + 10 * k

            # 3. Модификатор здоровья монстров (если есть)
            if info.get("life"):
                pct = info["life"]
                col = T.RED if pct >= 200 else T.ORANGE if pct >= 120 else T.GREEN
                life_txt = (f"{pct}% больше здоровья монстров" if info.get("life_lang") == "ru"
                            else f"{pct}% more Monster Life")
                t = self.cv.create_text(x0 + pad + 10 * k, y + 3 * k, text=life_txt.upper(),
                                        anchor="nw", font=(T.SANS, max(9, int(10 * k)), "bold"), fill=INK)
                bx1, by1, bx2, by2 = self._box(t, (x0, y, x0 + 100, y + 20))
                chip = T.round_rect(self.cv, bx1 - 8 * k, by1 - 3 * k, bx2 + 8 * k, by2 + 3 * k, 5 * k,
                                    fill=col, outline="")
                self.cv.tag_lower(chip, t)
                ids += [chip, t]
                width = max(width, bx2 + 8 * k - x0 - pad)
                y = by2 + 8 * k

            # 4. Детали ультиматума (Жертва / Награда)
            if info.get("detail"):
                t_det = self.cv.create_text(x0 + pad, y, text=info["detail"], anchor="nw",
                                            font=(T.SANS, max(9, int(10 * k))), fill=T.MUTED)
                ids.append(t_det)
                bx1, by1, bx2, by2 = self._box(t_det, (x0, y, x0 + 100, y + 20))
                width = max(width, bx2 - x0 - pad)
                y = by2 + 6 * k

            # 5. Разделитель
            div_line = self.cv.create_line(x0 + pad, y, x0 + pad + max(width, 260 * k), y, fill="#3d3428")
            ids.append(div_line)
            y += 8 * k

            # 6. Блок цены и профита
            big = (T.SERIF, int(20 * k), "bold")
            c_id = self.cv.create_text(x0 + pad, y, text=f"{info['chaos_text']} c", anchor="nw", font=big,
                                       fill=T.GOLD_HI if good else T.TXT)
            bx1, by1, bx2, by2 = self._box(c_id, (x0, y, x0 + 60, y + 20))
            d_id = self.cv.create_text(bx2 + 10 * k, by2 - 4 * k, text=f"≈ {info['div']:.2f} div", anchor="sw",
                                       font=(T.SANS, int(12 * k), "bold"), fill=T.GOLD if good else T.MUTED)
            ids += [c_id, d_id]
            last_id = d_id
            if info.get("net"):
                d_box = self._box(d_id, (bx2, by2, bx2 + 50, by2))
                n_id = self.cv.create_text(d_box[2] + 10 * k, by2 - 5 * k, text=tr("net_profit"),
                                           anchor="sw", font=(T.SANS, max(9, int(10 * k))), fill=T.MUTED)
                ids.append(n_id)
                last_id = n_id
            last_box = self._box(last_id, (x0, y, x0 + 100, y))
            width = max(width, last_box[2] - x0 - pad)
            y = by2 + 2 * k

            if info.get("mine"):
                m_id = self.cv.create_text(x0 + pad, y + 2 * k, text=tr("your_price"), anchor="nw",
                                           font=(T.SANS, max(9, int(9 * k)), "bold"), fill=T.GREEN)
                ids.append(m_id)
                m_box = self._box(m_id, (x0, y, x0 + 50, y + 15))
                width = max(width, m_box[2] - x0 - pad)
                y = m_box[3] + 2 * k

            if info.get("shaky"):
                w_id = self.cv.create_text(x0 + pad, y + 2 * k, text=tr("low_data"),
                                           anchor="nw", font=(T.SANS, int(9 * k), "bold"), fill=T.ORANGE)
                ids.append(w_id)
                w_box = self._box(w_id, (x0, y, x0 + 50, y + 15))
                width = max(width, w_box[2] - x0 - pad)
                y = w_box[3] + 2 * k

        else:
            # Обычный режим без карточки предпросмотра
            items = []
            items.append((info["name"], (T.SERIF, int(14 * k), "bold"), name_col))
            if info.get("life"):
                items.append(("life", None, None))
            if info.get("error"):
                items.append((info["error"], (T.SANS, int(10 * k)), "#ff9a8a"))
            else:
                if info.get("detail"):
                    items.append((info["detail"], (T.SANS, max(9, int(10 * k))), T.MUTED))
                items.append(("price", None, None))

            for text, font, col in items:
                if text == "life":
                    pct = info["life"]
                    col = T.RED if pct >= 200 else T.ORANGE if pct >= 120 else T.GREEN
                    life_txt = (f"{pct}% больше здоровья монстров" if info.get("life_lang") == "ru"
                                else f"{pct}% more Monster Life")
                    t = self.cv.create_text(x0 + pad + 10 * k, y + 3 * k, text=life_txt.upper(),
                                            anchor="nw", font=(T.SANS, max(9, int(11 * k)), "bold"), fill=INK)
                    bx1, by1, bx2, by2 = self._box(t, (x0, y, x0 + 100, y + 20))
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
                    bx1, by1, bx2, by2 = self._box(c_id, (x0, y, x0 + 60, y + 20))
                    d_id = self.cv.create_text(bx2 + 10 * k, by2 - 4 * k, text=f"≈ {info['div']:.2f} div", anchor="sw",
                                               font=(T.SANS, int(12 * k), "bold"), fill=T.GOLD if good else T.MUTED)
                    ids += [c_id, d_id]
                    if info.get("net"):
                        d_box = self._box(d_id, (bx2, by2, bx2 + 50, by2))
                        n_id = self.cv.create_text(d_box[2] + 10 * k, by2 - 5 * k, text=tr("net_profit"),
                                                   anchor="sw", font=(T.SANS, max(9, int(10 * k))), fill=T.MUTED)
                        ids.append(n_id)
                        d_id = n_id
                    d_box = self._box(d_id, (bx2, by2, bx2 + 50, by2))
                    width = max(width, d_box[2] - x0 - pad)
                    y = by2 + 2 * k
                    if info.get("mine"):
                        m_id = self.cv.create_text(x0 + pad, y + 2 * k, text=tr("your_price"), anchor="nw",
                                                   font=(T.SANS, max(9, int(9 * k)), "bold"), fill=T.GREEN)
                        ids.append(m_id)
                        m_box = self._box(m_id, (x0, y, x0 + 50, y + 15))
                        width = max(width, m_box[2] - x0 - pad)
                        y = m_box[3] + 2 * k
                    if info.get("shaky"):
                        w_id = self.cv.create_text(x0 + pad, y + 2 * k, text=tr("low_data"),
                                                   anchor="nw", font=(T.SANS, int(9 * k), "bold"), fill=T.ORANGE)
                        ids.append(w_id)
                        w_box = self._box(w_id, (x0, y, x0 + 50, y + 15))
                        width = max(width, w_box[2] - x0 - pad)
                        y = w_box[3] + 2 * k
                else:
                    t = self.cv.create_text(x0 + pad, y, text=text, anchor="nw", font=font, fill=col)
                    ids.append(t)
                    bx1, by1, bx2, by2 = self._box(t, (x0, y, x0 + 100, y + 20))
                    width = max(width, bx2 - x0 - pad)
                    y = by2 + 4 * k

        x1, y1, x2, y2 = x0, y0, x0 + width + 2 * pad, y + pad - 2 * k
        # не вылезать за край окна игры: справа — ставим слева от курсора, снизу — поднимаем
        dx = -(x2 - x1) - 44 * k if x2 > W - 8 else 0
        dy = (H - 8 - y2) if y2 > H - 8 else 0
        if x1 + dx < 8:
            dx = 8 - x1
        if y1 + dy < 8:
            dy = 8 - y1
        for i in ids:
            self.cv.move(i, dx, dy)
        x1, x2, y1, y2 = x1 + dx, x2 + dx, y1 + dy, y2 + dy
        bg = T.round_rect(self.cv, x1, y1, x2, y2, 8 * k, fill=INK, outline=border, width=max(1, int(2 * k)))
        bar = self.cv.create_rectangle(x1 + 10 * k, y1, x2 - 10 * k, y1 + 3 * k, fill=border, outline="")
        if ids:
            self.cv.tag_lower(bar, ids[0])  # подложка под текстом, но над рамками модов
        self.cv.tag_lower(bg, bar)
