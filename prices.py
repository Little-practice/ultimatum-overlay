"""Цены с poe.ninja и оценка предмета по тексту из Ctrl+C."""
import json
import os
import re
import time

import threading

import requests

from paths import APP_DIR as HERE, bundled_file, ensure_initial_file, write_json

from i18n import tr
CACHE = os.path.join(HERE, "prices_cache.json")
RU_CACHE = os.path.join(HERE, "names_ru.json")
CUSTOM_FILE = os.path.join(HERE, "my_prices.json")
LEAGUES_FILE = os.path.join(HERE, "leagues.json")   # цены, которые игрок вписал сам
BASE = "https://poe.ninja/poe1/api/economy"
EXCHANGE_TYPES = [
    # General
    "Currency", "Fragment", "Runegraft", "AllflameEmber", "Tattoo", "Omen",
    "DjinnCoin", "Ducat", "EnshroudingCrystal", "DivinationCard", "Artifact", "Oil",
    # Atlas & Crafting
    "DeliriumOrb", "Scarab", "Astrolabe", "Thread", "Fossil", "Resonator", "Essence"
]

STASH_TYPES = [
    # General
    "Wombgift", "Corpse", "Viscera", "Incubator",
    # Equipment & Gems
    "UniqueWeapon", "UniqueArmour", "UniqueAccessory", "UniqueFlask", "UniqueJewel",
    "ForbiddenJewel", "ShrineBelt", "UniqueTincture", "UniqueRelic",
    "SkillGem", "ImbuedGem", "ClusterJewel",
    # Atlas
    "Map", "BlightedMap", "BlightRavagedMap", "UniqueMap", "ValdoMap",
    "Invitation", "Memory", "IncursionTemple", "ScryingOrb",
    # Crafting
    "BaseType", "Flask", "Beast", "Vial"
]
HEADERS = {"User-Agent": "ultimatum-overlay/1.0"}


class Prices:
    def __init__(self):
        self.league = ""
        self.chaos = {}      # имя (lower) -> цена в хаосах
        self.divine = 0.0    # цена дивайна в хаосах
        self.updated = 0.0
        self.ru = {}         # русское название (lower) -> английское
        self.ru_names = {}   # английское (lower) -> русское, как пишется в игре
        self.low = set()     # названия (lower) с ненадёжной ценой: мало сделок/объявлений
        self.gems = {}       # "name@level@qual@corrupt" -> цена в хаосах
        self.low_gems = set()# варианты гемов с ненадёжной ценой
        self.names = {}      # имя (lower) -> как пишется в игре
        self.cat = {}        # имя (lower) -> раздел poe.ninja
        self.custom = {}     # имя (lower) -> своя цена в хаосах
        self.lock = threading.Lock()   # одна загрузка цен за раз
        self.load_custom()

    def _from_cache(self, league, max_age):
        paths_to_check = [CACHE, bundled_file("prices_cache.json")]
        c = None
        for p in paths_to_check:
            if os.path.exists(p):
                try:
                    with open(p, encoding="utf-8") as f:
                        data = json.load(f)
                    if data.get("league") == league:
                        c = data
                        break
                except Exception:
                    pass
        if not c:
            return False
        if max_age is not None and time.time() - c.get("updated", 0) >= max_age:
            return False
        self.league, self.chaos, self.divine, self.updated = league, c["chaos"], c["divine"], c["updated"]
        self.low = set(c.get("low", []))
        self.gems = c.get("gems", {})
        self.low_gems = set(c.get("low_gems", []))
        self.names = c.get("names", {})
        self.cat = c.get("cat", {})
        return True

    def load(self, league, max_age=3600, log=print):
        """Сначала сразу подгружаем имеющийся кэш (чтобы цены были доступны с первой секунды),
        а затем при необходимости обновляем с poe.ninja.
        Если скачать не вышло (нет интернета) — остаёмся на сохранённых ценах."""
        self.load_ru(log)
        has_cache = self._from_cache(league, None)
        if has_cache and (time.time() - self.updated < max_age):
            return
        try:
            self.refresh(league, log)
        except Exception as e:
            if has_cache:
                age = (time.time() - self.updated) / 3600
                log(tr("prices_stale", e=e, h=f"{age:.0f}"))
            else:
                raise

    def refresh(self, league, log=print):
        chaos = {}
        low = set()
        disp, cat = {}, {}
        divine = 0.0
        failed = []

        # Сохраняем также связанные предметы (на случай, если нет версии без связей)
        linked_chaos = {}
        linked_disp = {}
        linked_cat = {}
        gems = {}
        low_gems = set()

        for t in EXCHANGE_TYPES:
            try:
                r = requests.get(f"{BASE}/exchange/current/overview", params={"league": league, "type": t},
                                 headers=HEADERS, timeout=20)
                r.raise_for_status()
                d = r.json()
            except Exception as e:
                failed.append(t)
                log(tr("ninja_err", t=t, e=e))
                continue
            names = {i["id"]: i["name"] for i in d.get("items", [])}
            for ln in d.get("lines", []):
                n = names.get(ln["id"])
                if n and ln.get("primaryValue") is not None:
                    pv = float(ln["primaryValue"])
                    if pv > 0:
                        nl = n.lower()
                        chaos[nl] = pv
                        disp[nl] = n
                        cat[nl] = t
                        # Неточные данные: мало сделок на рынке или малый суточный объём
                        vol = float(ln.get("volumePrimaryValue") or 0)
                        cnt = float(ln.get("count") or 0)
                        if (vol / pv < 3) or (cnt > 0 and cnt < 3):
                            low.add(nl)
            rate = d.get("core", {}).get("rates", {}).get("divine")
            if rate:
                divine = 1.0 / rate

        for t in STASH_TYPES:
            try:
                r = requests.get(f"{BASE}/stash/current/item/overview", params={"league": league, "type": t},
                                 headers=HEADERS, timeout=30)
                r.raise_for_status()
                d = r.json()
            except Exception as e:
                failed.append(t)
                log(tr("ninja_err", t=t, e=e))
                continue
            for ln in d.get("lines", []):
                n = ln.get("name", "").lower()
                if not n:
                    continue
                v = float(ln.get("chaosValue") or 0)
                if not v:
                    continue
                is_linked = bool(ln.get("links"))
                if is_linked:
                    if n not in linked_chaos or v < linked_chaos[n]:
                        linked_chaos[n] = v
                        linked_disp[n] = ln.get("name")
                        linked_cat[n] = t
                    continue

                if t in ("SkillGem", "ImbuedGem"):
                    lvl = int(ln.get("gemLevel") or 1)
                    q = int(ln.get("gemQuality") or 0)
                    qb = 23 if q >= 21 else (20 if q >= 18 else 0)
                    isc = 1 if bool(ln.get("corrupted")) else 0
                    gk = f"{n}@{lvl}@{qb}@{isc}"
                    if gk not in gems or v < gems[gk]:
                        gems[gk] = v
                        count = int(ln.get("listingCount") or ln.get("count") or 0)
                        if count < 5:
                            low_gems.add(gk)
                        else:
                            low_gems.discard(gk)

                if n not in chaos or v < chaos[n]:  # для разных вариантов берём самый дешёвый
                    chaos[n] = v
                    disp[n] = ln.get("name")
                    cat[n] = t
                    # Неточные данные: меньше 5 предложений на рынке
                    count = int(ln.get("listingCount") or ln.get("count") or 0)
                    if count < 5:
                        low.add(n)
                    else:
                        low.discard(n)

        # Если для уникального предмета есть только варианты со связями (5L/6L),
        # всё равно сохраняем цену, но помечаем как "неточные данные"
        for n, v in linked_chaos.items():
            if n not in chaos:
                chaos[n] = v
                disp[n] = linked_disp[n]
                cat[n] = linked_cat[n]
                low.add(n)

        # без валюты (и курса дивайна) или почти без данных — старые цены лучше неполных
        if not chaos or "Currency" in failed or not (divine or chaos.get("divine orb")) or len(failed) > 20:
            raise RuntimeError(tr("ninja_empty"))
        self.league, self.chaos, self.updated, self.low = league, chaos, time.time(), low
        self.gems, self.low_gems = gems, low_gems
        self.names, self.cat = disp, cat
        self.divine = divine or chaos.get("divine orb", 0)
        write_json(CACHE, {"league": league, "chaos": chaos, "divine": self.divine, "updated": self.updated,
                           "low": sorted(low), "gems": gems, "low_gems": sorted(low_gems), "names": disp, "cat": cat})
        log(tr("prices_updated", n=len(chaos), div=f"{self.divine:.0f}"))

        self.load_ru(log)

    @staticmethod
    def fetch_leagues():
        """Текущие лиги с poe.ninja (раздел «Current leagues»). Список сохраняется на случай,
        если не будет интернета."""
        try:
            d = requests.get("https://poe.ninja/poe1/api/data/index-state", headers=HEADERS, timeout=20).json()
            out = [x["name"] for x in d.get("economyLeagues", []) if not x.get("isPrivate")]
            if out:
                write_json(LEAGUES_FILE, out)
                return out
        except Exception:
            pass
        for p in (LEAGUES_FILE, bundled_file("leagues.json")):
            if os.path.exists(p):
                try:
                    with open(p, encoding="utf-8") as f:
                        res = json.load(f)
                        if res:
                            return res
                except Exception:
                    pass
        return ["Covens", "Standard"]

    def load_ru(self, log=print, max_age=7 * 86400):
        """Словарь русское название -> английское (официальный API трейда, ru и www)."""
        cached = None
        for p in (RU_CACHE, bundled_file("names_ru.json")):
            if os.path.exists(p):
                try:
                    with open(p, encoding="utf-8") as f:
                        c = json.load(f)
                    if "ru_names" in c and c.get("map"):
                        cached = c
                        if time.time() - c.get("updated", 0) < max_age:
                            self.ru, self.ru_names = c["map"], c["ru_names"]
                            return
                        break
                except Exception:
                    pass
        if cached and not self.ru:
            self.ru, self.ru_names = cached["map"], cached["ru_names"]
        try:
            def get(host, what):
                time.sleep(0.3)  # пауза, чтобы избежать 429 Too Many Requests от GGG
                return requests.get(f"https://{host}.pathofexile.com/api/trade/data/{what}",
                                    headers=HEADERS, timeout=30).json()["result"]
            m, rn = {}, {}
            en_s = {e["id"]: e.get("text") for c in get("www", "static") for e in c.get("entries", []) if e.get("text")}
            for c in get("ru", "static"):
                for e in c.get("entries", []):
                    if e.get("id") in en_s and e.get("text"):
                        m[e["text"].lower()] = en_s[e["id"]]
                        rn.setdefault(en_s[e["id"]].lower(), e["text"])

            www_cats = {c["id"]: c.get("entries", []) for c in get("www", "items")}
            for b in get("ru", "items"):
                cid = b.get("id")
                a_entries = www_cats.get(cid, [])
                for x, y in zip(a_entries, b.get("entries", [])):
                    for k in ("name", "type", "text"):
                        if x.get(k) and y.get(k):
                            m.setdefault(y[k].lower(), x[k])
                            rn.setdefault(x[k].lower(), y[k])

            if len(m) < 100:
                raise RuntimeError("too few names")
            self.ru, self.ru_names = m, rn
            write_json(RU_CACHE, {"updated": time.time(), "map": m, "ru_names": rn})
            log(tr("ru_loaded", n=len(m)))
        except Exception as e:
            if cached:                       # нет интернета — старый словарь лучше пустого
                self.ru, self.ru_names = cached["map"], cached["ru_names"]
            else:
                log(tr("ru_err", e=e))

    def to_en(self, name):
        n = name.strip()
        nl = n.lower()
        if nl == "кровь мага":
            return "Mageblood"
        if nl in self.ru:
            return self.ru[nl]
        n_clean = re.sub(r"^[\"'«]+|[\"'»]+$", "", n).strip().lower()
        if n_clean in self.ru:
            return self.ru[n_clean]
        for pfx in ("карточка ", "гадальная карта ", "карта гадания ", "divination card "):
            if n_clean.startswith(pfx):
                stripped = n_clean[len(pfx):].strip()
                stripped = re.sub(r"^[\"'«]+|[\"'»]+$", "", stripped).strip()
                if stripped in self.ru:
                    return self.ru[stripped]
        return self.ru.get(nl, n)

    # ---------- свои цены ----------
    def load_custom(self):
        try:
            with open(CUSTOM_FILE, encoding="utf-8") as f:
                self.custom = {k.lower(): float(v) for k, v in json.load(f).items()}
        except Exception:
            self.custom = {}

    def set_custom(self, name, chaos):
        """Своя цена в хаосах; None — убрать и снова брать poe.ninja."""
        n = self._key(name)
        if chaos is None:
            self.custom.pop(n, None)
        else:
            self.custom[n] = float(chaos)
        write_json(CUSTOM_FILE, self.custom, indent=1)

    def _key(self, name):
        """Имя для поиска: русское переводим в английское, убираем префиксы качества."""
        n = name.strip().replace("\xa0", " ").lower()
        n = re.sub(r"^[\"'«]+|[\"'»]+$", "", n).strip()
        for pfx in ("карточка ", "гадальная карта ", "карта гадания ", "divination card "):
            if n.startswith(pfx):
                n = n[len(pfx):].strip()
                n = re.sub(r"^[\"'«]+|[\"'»]+$", "", n).strip()

        if n == "кровь мага":
            return "mageblood"

        if n in self.custom or n in self.chaos:
            return n
        if n in self.ru:
            en = self.ru[n].lower()
            if en in self.custom or en in self.chaos:
                return en

        # Пробуем без префикса качества (Superior / Качественный / Превосходный)
        for pfx in ("superior ", "качественный ", "качественная ", "качественное ",
                    "превосходный ", "превосходная ", "превосходное "):
            if n.startswith(pfx):
                stripped = n[len(pfx):].strip()
                if stripped in self.custom or stripped in self.chaos:
                    return stripped
                if stripped in self.ru:
                    en = self.ru[stripped].lower()
                    if en in self.custom or en in self.chaos:
                        return en

        if n in self.ru:
            return self.ru[n].lower()

        # Поддержка камней умений / поддержки в русском клиенте
        cand_ru = f"поддержка: {n}"
        if cand_ru in self.ru:
            en = self.ru[cand_ru].lower()
            return en

        for aw in ("пробуждённый ", "пробужденный "):
            if n.startswith(aw):
                rest = n[len(aw):].strip()
                for cand2 in (f"пробуждённый - поддержка: {rest}", f"пробужденный - поддержка: {rest}"):
                    if cand2 in self.ru:
                        return self.ru[cand2].lower()

        # Английский без 'support': 'empower' -> 'empower support'
        if f"{n} support" in self.chaos or any(k.startswith(f"{n} support@") for k in self.gems):
            return f"{n} support"

        return n

    def display(self, key, lang="en"):
        """Название для показа: по-английски как в игре или по-русски, если есть перевод."""
        if lang == "ru" and key in self.ru_names:
            return self.ru_names[key]
        return self.names.get(key, key.title())

    def is_custom(self, name):
        return self._key(name) in self.custom

    def unreliable(self, name):
        n = self._key(name)
        return n not in self.custom and n in self.low

    def price(self, name):
        n = self._key(name)
        if n in self.custom:
            return self.custom[n]
        return self.chaos.get(n)

    def gem_price(self, name, level=1, quality=0, corrupted=False):
        """Возвращает (цена в хаосах, ненадёжная ли цена) для указанного варианта камня."""
        key = self._key(name)
        if key in self.custom:
            return self.custom[key], False

        isc = 1 if corrupted else 0
        lvl = int(level or 1)
        q = int(quality or 0)
        qb = 23 if q >= 21 else (20 if q >= 18 else 0)

        # 1. Точное совпадение
        candidates = [f"{key}@{lvl}@{qb}@{isc}"]
        # 2. Меньшее качество при том же уровне и осквернении
        if qb == 23:
            candidates.append(f"{key}@{lvl}@20@{isc}")
        if qb > 0:
            candidates.append(f"{key}@{lvl}@0@{isc}")
        # 3. Другое состояние осквернения при том же уровне
        candidates.append(f"{key}@{lvl}@{qb}@{1 - isc}")
        if qb == 23:
            candidates.append(f"{key}@{lvl}@20@{1 - isc}")
        if qb > 0:
            candidates.append(f"{key}@{lvl}@0@{1 - isc}")

        # 4. Ближайший стандартный уровень, если текущий не найден (например, уровень 19 -> уровень 1)
        alt_lvls = []
        if lvl not in (1, 20, 21):
            if lvl >= 20:
                alt_lvls = [20, 21, 1]
            else:
                alt_lvls = [1, 20]
        for al in alt_lvls:
            candidates.append(f"{key}@{al}@{qb}@{isc}")
            if qb > 0:
                candidates.append(f"{key}@{al}@0@{isc}")
            candidates.append(f"{key}@{al}@{qb}@{1 - isc}")
            if qb > 0:
                candidates.append(f"{key}@{al}@0@{1 - isc}")

        for i, c in enumerate(candidates):
            if c in self.gems:
                is_shaky = (i > 0) or (c in self.low_gems)
                return self.gems[c], is_shaky

        # Резерв: базовая цена из общего списка цен
        base = self.chaos.get(key)
        if base is not None:
            return base, True

        return None, False


# ---------------- разбор текста предмета ----------------
def _num(s):
    return int(re.sub(r"[^\d]", "", s) or 0)


def parse_item(text):
    """-> dict(name, base, rarity, qty, sacrifice, sacrifice_qty, reward, reward_qty)"""
    cleaned = text.replace("\r", "").replace("\xa0", " ")
    secs = [s.strip().splitlines() for s in cleaned.split("--------")]
    head = [l.strip() for l in secs[0] if l.strip()]
    rarity = ""
    names = []
    for l in head:
        if re.match(r"(Rarity|Редкость):", l):
            rarity = l.split(":", 1)[1].strip()
        elif not re.match(r"(Item Class|Класс предмета):", l):
            names.append(l)
    it = {"rarity": rarity, "name": names[0] if names else "", "base": names[1] if len(names) > 1 else "",
          "qty": 1, "sacrifice": None, "sacrifice_qty": 1, "reward": None, "reward_qty": 1,
          "monster_life": None, "life_lang": "en"}
    for l in cleaned.splitlines():
        l = l.strip()
        m = re.match(r"(?:Stack Size|Размер стопки|Количество в стопке):\s*([\d\s,.]+)/", l)
        if m:
            it["qty"] = max(1, _num(m.group(1)))
        m = re.match(r"(?:Requires Sacrifice|[^:]*[Пп]ожертв[^:]*):\s*(?:([\d\s,]+)\s*[xх×]\s*)?(.+?)(?:\s+[xх×]\s*([\d\s,]+))?$", l)
        if m:
            qty_pre, sac_name, qty_post = m.group(1), m.group(2).strip(), m.group(3)
            q = _num(qty_pre) if qty_pre else (_num(qty_post) if qty_post else 1)
            it["sacrifice"] = sac_name
            it["sacrifice_qty"] = max(1, q)
        m = re.match(r"(?:Reward|Награда):\s*(?:([\d\s,]+)\s*[xх×]\s*)?(.+?)(?:\s+[xх×]\s*([\d\s,]+))?$", l)
        if m:
            qty_pre, rw_name, qty_post = m.group(1), m.group(2).strip(), m.group(3)
            q = _num(qty_pre) if qty_pre else (_num(qty_post) if qty_post else 1)
            it["reward"] = rw_name
            it["reward_qty"] = max(1, q)
        # «200% more Monster Life» (у Inscribed Ultimatum бывает 70 / 120 / 200 %)
        m = re.match(r"(\d+)%\s+more\s+Monster\s+Life", l, re.I) or \
            re.match(r"(\d+)%.*(?:здоровь|жизн).*монстр", l, re.I) or \
            re.match(r"(\d+)%.*монстр.*(?:здоровь|жизн)", l, re.I)
        if m:
            it["monster_life"] = int(m.group(1))
            it["life_lang"] = "ru" if re.search("[а-яА-Я]", l) else "en"   # язык клиента игры

    is_gem = (rarity.lower() in ("gem", "камень") or
              any(k in cleaned for k in ("Skill Gems", "Support Gems", "Камни умений", "Камни поддержки")))
    it["is_gem"] = is_gem

    if is_gem and it["name"]:
        for pfx in ("Superior ", "superior ", "Превосходный ", "превосходный ", "Превосходная ", "превосходная ",
                    "Превосходное ", "превосходное ", "Качественный ", "качественный ", "Качественная ", "качественная ",
                    "Качественное ", "качественное "):
            if it["name"].startswith(pfx):
                it["name"] = it["name"][len(pfx):].strip()
                break

    gem_level = 1
    m_lvl = re.search(r"(?:^|\n)\s*(?:Level|Уровень):\s*(\d+)", cleaned, re.I)
    if m_lvl:
        gem_level = int(m_lvl.group(1))
    it["gem_level"] = gem_level

    gem_quality = 0
    m_q = re.search(r"(?:^|\n)\s*(?:Quality|Качество):\s*\+?(\d+)%", cleaned, re.I)
    if m_q:
        gem_quality = int(m_q.group(1))
    it["gem_quality"] = gem_quality

    it["corrupted"] = bool(re.search(r"^(?:Corrupted|Осквернено)\s*$", cleaned, re.I | re.M))
    it["is_ru"] = bool(re.search(r"[а-яА-Я]", cleaned))

    return it


def value_of(text, prices):
    """-> (цена в хаосах или None, пояснение)"""
    it = parse_item(text)
    name = it["name"]
    if it["reward"] is not None:  # Inscribed Ultimatum — считаем только чистую прибыль
        rw = it["reward"]
        low = rw.lower()
        sac, n = it["sacrifice"], it["sacrifice_qty"]
        mark = lambda nm: "✎" if prices.is_custom(nm) else "?" if prices.unreliable(nm) else ""
        mult = (2 if any(w in low for w in ("double", "удваива", "удвоени")) else
                3 if any(w in low for w in ("triple", "утраива", "утроени")) else None)
        if mult and sac:
            # «удваивает» 8 штук: вернут 16, из них 8 своих — прибыль 8 штук
            p = prices.price(sac)
            if p is None:
                return None, tr("no_price", name=sac)
            extra = (mult - 1) * n
            return extra * p * it["qty"], f"{extra} × {sac} ({p:.1f}c{mark(sac)})"
        p = prices.price(rw)
        if p is None:
            return None, tr("no_reward_price", name=rw)
        rw_qty = it.get("reward_qty", 1)
        if sac:
            # награда — другой предмет взамен пожертвованного: прибыль = награда − жертва
            ps = prices.price(sac)
            if ps is None:
                return None, tr("no_price", name=sac)
            net = p * rw_qty - ps * n
            return net * it["qty"], (f"{rw_qty} × {rw} ({p:.1f}c{mark(rw)}) − {n} × {sac} ({ps:.1f}c{mark(sac)})")
        return p * rw_qty * it["qty"], f"{rw_qty} × {rw} ({p:.1f}c{mark(rw)})"

    if it.get("is_gem"):
        lvl = it["gem_level"]
        q = it["gem_quality"]
        corrupt = it["corrupted"]
        p, is_shaky = prices.gem_price(name, level=lvl, quality=q, corrupted=corrupt)
        if p is None:
            return None, tr("no_price", name=name)
        q_mark = "✎" if prices.is_custom(name) else "?" if is_shaky else ""
        c_tag = (" (осквернено)" if it.get("is_ru") else " (corrupted)") if corrupt else ""
        desc = f"{lvl}/{q}%{c_tag}"
        return p * it["qty"], f"{it['qty']} × {name} {desc} ({p:.1f}c{q_mark})"

    key = name
    p = prices.price(name)
    is_base = False
    if p is None and it["base"]:
        key, p = it["base"], prices.price(it["base"])
        is_base = True
    if p is None:
        return None, tr("no_price", name=name)
    is_shaky = prices.unreliable(key) or is_base
    q = "✎" if prices.is_custom(key) else "?" if is_shaky else ""
    note = " (база)" if is_base else ""
    return p * it["qty"], f"{it['qty']} × {name}{note} ({p:.1f}c{q})"
