"""Что видно на экране и в буфере обмена -> что нарисовать. Ничего не нажимает."""
import base64
import re

import cv2
import numpy as np

import icons
import preview
import refs_data
import i18n
from i18n import tr
from prices import parse_item, value_of
from screen import DD_BOX, MOD_ICON, MODS, gold_share

# эталонные кусочки окна ультиматума: эмблема OR, Take Rewards, Accept Trial
REFS = {k: cv2.imdecode(np.frombuffer(base64.b64decode(v), np.uint8), cv2.IMREAD_GRAYSCALE)
        for k, v in refs_data.PNG.items()}
MARGIN = 12  # запас на небольшой сдвиг интерфейса
# где на кусочках надписи («OR», «TAKE REWARDS», «ACCEPT TRIAL») — их не сравниваем, только рамки и стрелки,
# чтобы окно узнавалось и в русском клиенте («ИЛИ», «Забрать награды»…)
TEXT_AREA = {"or": (55, 28, 135, 78), "take": (18, 10, 172, 38), "accept": (18, 10, 172, 38)}
MASKS = {}
for _k, _r in REFS.items():
    _m = np.full(_r.shape, 255, np.uint8)
    _x1, _y1, _x2, _y2 = TEXT_AREA[_k]
    _m[_y1:_y2, _x1:_x2] = 0
    MASKS[_k] = _m

GREEN, RED, ORANGE = "#00ff3c", "#ff3030", "#ffa020"


def is_item_text(txt):
    return bool(txt) and any(k in txt for k in ("Rarity:", "Редкость:", "Item Class:", "Класс предмета:"))


def price_info(txt, prices, div_threshold, life_alert=True, show_preview=True):
    """Текст предмета из Ctrl+C -> всё для карточки цены у курсора."""
    it = parse_item(txt)
    client_lang = "ru" if re.search(r"[\u0400-\u04ff]", txt) else "en"
    info = {"name": it["name"] or "Предмет", "rarity": it["rarity"], "qty": it["qty"],
            "detail": "", "chaos": None, "div": None, "good": False, "shaky": False, "mine": False,
            "net": it["reward"] is not None, "life": it["monster_life"] if life_alert else None,
            "life_lang": client_lang,
            "error": None,
            "preview": None,
            "sacrifice_text": it.get("sacrifice"),
            "sacrifice_qty": it.get("sacrifice_qty", 1),
            "reward_text": it.get("reward"),
            "reward_qty": it.get("reward_qty", 1)}
    if not prices.chaos:
        info["error"] = tr("still_loading")
    else:
        chaos, why = value_of(txt, prices)
        if chaos is None:
            info["error"] = why
        else:
            div = chaos / prices.divine if prices.divine else 0.0
            info.update(chaos=chaos, div=div, good=div >= div_threshold, shaky="c?)" in why, mine="c✎)" in why,
                        detail=why.replace("Inscribed Ultimatum: ", "").replace(" x ", " × "))
            # Если это Начертанный ультиматум и включен показ карточки награды
            if show_preview and it.get("reward") is not None:
                rw = it["reward"]
                low_rw = rw.lower()
                mult = (2 if any(w in low_rw for w in ("double", "удваива", "удвоени")) else
                        3 if any(w in low_rw for w in ("triple", "утраива", "утроени")) else None)
                target_item = it["sacrifice"] if (mult and it.get("sacrifice")) else rw
                if mult:
                    info["reward_qty"] = mult * it.get("sacrifice_qty", 1)
                if target_item:
                    prev = preview.get_preview(target_item, client_lang, prices.to_en)
                    if prev:
                        info["preview"] = prev
    if info["error"]:
        info["line"] = f"{info['name']}: {info['error']}"
    else:
        c = f"{info['chaos']:.1f}" if info["chaos"] < 10 else f"{info['chaos']:,.0f}".replace(",", " ")
        info["chaos_text"] = c
        prev_name = f" [{info['preview']['name']}]" if info.get("preview") else ""
        info["line"] = (f"{info['name']}{prev_name} — {info['detail']} = {c} c ≈ {info['div']:.2f} div"
                        + (f" ({tr('low_data_short')})" if info["shaky"] else "")
                        + (f" ({tr('own_short')})" if info["mine"] else ""))
    return info


class ModAdvisor:
    def __init__(self, scr, cfg):
        self.scr = scr
        self.cfg = cfg
        self.lib = icons.load_library()

    def panel_scores(self):
        """Похожесть трёх кусочков экрана на эталоны (0..1)."""
        out = {}
        for k, (x1, y1, x2, y2) in refs_data.BOXES.items():
            reg = self.scr.grab(x1 - MARGIN, y1 - MARGIN, x2 + MARGIN, y2 + MARGIN)
            reg = cv2.resize(reg, (x2 - x1 + 2 * MARGIN, y2 - y1 + 2 * MARGIN))
            g = cv2.cvtColor(reg, cv2.COLOR_BGR2GRAY)
            res = cv2.matchTemplate(g, REFS[k], cv2.TM_CCOEFF_NORMED, mask=MASKS[k])
            res = res[np.isfinite(res)]           # на ровной картинке бывает «не число»
            out[k] = float(res.max()) if res.size else 0.0
        return out

    def panel_open(self):
        """Окно открыто, если узнаются хотя бы 2 из 3 кусочков (один может закрыть подсказка)."""
        return sum(v >= 0.6 for v in self.panel_scores().values()) >= 2

    def read(self):
        """-> None, если окна ультиматума нет; иначе список из 3 dict по иконкам."""
        mods = []
        for i in range(3):
            img = self.scr.grab_icon(i)
            sat = icons.saturation(img)
            col = sat >= self.cfg["sat_threshold"]
            e, sc = icons.identify(img, self.lib, colored=col) if self.lib else (None, 0.0)
            mods.append({"i": i, "img": img, "colored": col, "entry": e if sc >= self.cfg["match_threshold"] else None,
                         "score": sc})
        return mods

    def advise(self, mods):
        """-> (список рамок [(индекс, подпись, цвет)], режим, текст для статуса)"""
        n_col = sum(m["colored"] for m in mods)
        mode = self.cfg["waves"]
        waves = (10 if n_col >= 2 else 13) if mode == "auto" else int(mode)
        order = {id(e): n for n, e in enumerate(self.lib)}
        ok = lambda m: m["entry"] is not None and m["entry"]["allowed"]

        def name(m):
            e = m["entry"]
            if e is None:
                return tr("unknown_mod")
            return (e.get("name_ru" if i18n.LANG == "ru" else "name_en") or e.get("name")
                    or f"{e['tier']} #{order[id(e)] + 1}")

        if waves == 10:
            cands = mods
            good = [m for m in cands if ok(m)]
            if good:
                pick = min(good, key=lambda m: order[id(m["entry"])])
                return [(pick["i"], "take", GREEN)], waves, tr("st_10_take", i=pick["i"] + 1, name=name(pick))
            return [(m["i"], "no", RED) for m in cands], waves, tr("st_10_none")
        given = [m for m in mods if m["colored"]]
        if given and all(ok(m) for m in given):
            return ([(m["i"], "ok", GREEN) for m in given], waves,
                    tr("st_13_ok", names=", ".join(name(m) for m in given)))
        return ([(m["i"], "no" if m["entry"] else "unknown", RED if m["entry"] else ORANGE) for m in given],
                waves, tr("st_13_no", names=", ".join(name(m) for m in given)))

    def unknown_icons(self, mods):
        """Цветные нераспознанные иконки, которые видны 3 чтения подряд на одном месте (не кадр перехода).
        -> список картинок, которые стоит добавить в раздел «Мираж». Сам список меняет окно программы."""
        if not hasattr(self, "_pending"):
            self._pending = {}
        out = []
        for m in mods:
            i = m["i"]
            if not (m["colored"] and m["entry"] is None):
                self._pending.pop(i, None)
                continue
            prev = self._pending.get(i)
            if prev is not None and icons._score(m["img"], prev[0], True) > 0.8:
                cnt = prev[1] + 1
            else:
                cnt = 1
            self._pending[i] = (m["img"], cnt)
            if cnt == 3:
                out.append(m["img"])
        return out

    def double_down(self):
        img = self.scr.grab(*DD_BOX)
        return gold_share(img) >= 0.02


def mod_box(i):
    x, y = MODS[i]
    h = MOD_ICON / 2
    return x - h, y - h, x + h, y + h
