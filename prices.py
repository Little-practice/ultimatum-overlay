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
FOULBORN_PREFIX_RE = re.compile(r"^(?:нечестивый|нечестивая|нечестивое|нечестивые|foulborn)\s*[:\-]?\s*", re.I)


def normalize_item_name(name):
    """Очищает имя предмета от кавычек, количества и префиксов (карт, уников, качества)."""
    if not name:
        return ""
    n = name.strip().replace("\xa0", " ").lower()
    # Убираем количество в начале (например, "2x ", "8× ", "1 х ")
    n = re.sub(r"^\d+\s*[xх×]\s*", "", n).strip()
    # Убираем любые виды кавычек и спецсимволы по краям
    n = re.sub(r"^[\"'«»“”„‘’`\s]+|[\"'«»“”„‘’`\s]+$", "", n).strip()

    changed = True
    while changed:
        changed = False
        patterns = [
            r"^(?:(?:дважды\s+оскверн[её]нн\w*|оскверн[её]нн\w*|зеркальн\w*|шестисвязн\w*|6-?связн\w*|double[- ]?corrupted|two[- ]?implicit\s+corrupted|corrupted|mirrored|six[- ]?linked|6[- ]?linked)\s+)?(?:гадальные\s+карты|гадальная\s+карта|карты\s+гадания|карта\s+гадания|карточка|карточки|divination\s+cards?)\s*[:\-]?\s*",
            r"^(?:(?:дважды\s+оскверн[её]нн\w*|оскверн[её]нн\w*|зеркальн\w*|шестисвязн\w*|6-?связн\w*|double[- ]?corrupted|two[- ]?implicit\s+corrupted|corrupted|mirrored|six[- ]?linked|6[- ]?linked)\s+)?(?:уникальный\s+предмет|уникальные\s+предметы|уникальный|уникальная|уникальное|unique\s+items?)\s*[:\-]?\s*",
            r"^(?:superior|качественный|качественная|качественное|превосходный|превосходная|превосходное)\s*[:\-]?\s*",
        ]
        for pat in patterns:
            m = re.match(pat, n, re.IGNORECASE)
            if m:
                n = n[m.end():].strip()
                n = re.sub(r"^[\"'«»“”„‘’`\s]+|[\"'«»“”„‘’`\s]+$", "", n).strip()
                changed = True
    return n


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
        self.variants = {}   # "name@variant" -> цена в хаосах (Voices, Forbidden Flesh/Flame, Mageblood и т.д.)
        self.low_variants = set()
        self.max_chaos = {}  # имя (lower) -> максимальная цена среди вариантов (для показа разброса)
        self.names = {}      # имя (lower) -> как пишется в игре
        self.cat = {}        # имя (lower) -> раздел poe.ninja
        self.custom = {}     # имя (lower) -> своя цена в хаосах
        self.lock = threading.Lock()   # одна загрузка цен за раз
        self.load_custom()
        # Сразу мгновенно загружаем локальный словарь и кэш (0мс задержки, офлайн-готовность с 1-й секунды)
        self._load_local_ru()
        self._from_cache(None, None)

    def _load_local_ru(self):
        """Мгновенно загружает локальный/вшитый словарь без сетевых запросов."""
        for p in (RU_CACHE, bundled_file("names_ru.json")):
            if os.path.exists(p):
                try:
                    with open(p, encoding="utf-8") as f:
                        c = json.load(f)
                    if "ru_names" in c and c.get("map"):
                        self.ru.update(c["map"])
                        self.ru_names.update(c["ru_names"])
                        break
                except Exception:
                    pass
        # Дополняем базой карточек и уников из items_preview.json (гарантирует перевод всех наград)
        try:
            for pp in (bundled_file("items_preview.json"), os.path.join(HERE, "items_preview.json")):
                if os.path.exists(pp):
                    with open(pp, encoding="utf-8") as f:
                        pdb = json.load(f)
                    for cat in ("cards", "uniques"):
                        for item in pdb.get(cat, {}).values():
                            r = item.get("name_ru", "").strip()
                            e = item.get("name_en", "").strip()
                            if r and e:
                                self.ru.setdefault(r.lower(), e)
                                self.ru_names.setdefault(e.lower(), r)
                    break
        except Exception:
            pass

    def _from_cache(self, league, max_age):
        paths_to_check = [CACHE, bundled_file("prices_cache.json")]
        c = None
        for p in paths_to_check:
            if os.path.exists(p):
                try:
                    with open(p, encoding="utf-8") as f:
                        data = json.load(f)
                    if league is None or data.get("league") == league:
                        c = data
                        break
                except Exception:
                    pass
        if not c:
            return False
        if max_age is not None and time.time() - c.get("updated", 0) >= max_age:
            return False
        self.league = c.get("league", league or "")
        self.chaos, self.divine, self.updated = c["chaos"], c["divine"], c["updated"]
        self.low = set(c.get("low", []))
        self.gems = c.get("gems", {})
        self.low_gems = set(c.get("low_gems", []))
        self.variants = c.get("variants", {})
        self.low_variants = set(c.get("low_variants", []))
        self.max_chaos = c.get("max_chaos", {})
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
        variants = {}
        low_variants = set()
        max_chaos = {}

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

                if t == "ForbiddenJewel":
                    jtype = (ln.get("variant") or "").strip().lower()
                    notable = (ln.get("name") or "").strip().lower()
                    if not jtype or not notable:
                        continue
                    count = int(ln.get("listingCount") or ln.get("count") or 0)
                    vk = f"{jtype}@{notable}"
                    if vk not in variants or v < variants[vk]:
                        variants[vk] = v
                        if count < 5:
                            low_variants.add(vk)
                        else:
                            low_variants.discard(vk)
                    max_chaos[jtype] = max(max_chaos.get(jtype, 0.0), v)
                    if jtype not in chaos or v < chaos[jtype]:
                        chaos[jtype] = v
                        disp[jtype] = ln.get("variant")
                        cat[jtype] = t
                        low.add(jtype)
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

                var_raw = ln.get("variant")
                if var_raw:
                    vk = f"{n}@{str(var_raw).strip().lower()}"
                    if vk not in variants or v < variants[vk]:
                        variants[vk] = v
                        count = int(ln.get("listingCount") or ln.get("count") or 0)
                        if count < 5:
                            low_variants.add(vk)
                        else:
                            low_variants.discard(vk)
                elif n == "voices":
                    for vk in ("voices@1 passives", "voices@1 passive"):
                        if vk not in variants or v < variants[vk]:
                            variants[vk] = v
                            count = int(ln.get("listingCount") or ln.get("count") or 0)
                            if count < 5:
                                low_variants.add(vk)
                            else:
                                low_variants.discard(vk)

                max_chaos[n] = max(max_chaos.get(n, 0.0), v)
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

        # Многовариантные предметы с сильным разбросом цен (Voices, Watcher's Eye, Forbidden Flesh и т.д.)
        # всегда помечаются как неточные, если вариант не уточнён
        for n, mv in max_chaos.items():
            if n in chaos and chaos[n] > 0 and mv > chaos[n] * 1.8:
                low.add(n)

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
        self.variants, self.low_variants, self.max_chaos = variants, low_variants, max_chaos
        self.names, self.cat = disp, cat
        self.divine = divine or chaos.get("divine orb", 0)
        write_json(CACHE, {"league": league, "chaos": chaos, "divine": self.divine, "updated": self.updated,
                           "low": sorted(low), "gems": gems, "low_gems": sorted(low_gems),
                           "variants": variants, "low_variants": sorted(low_variants), "max_chaos": max_chaos,
                           "names": disp, "cat": cat})
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
        # Сначала гарантируем, что локальный словарь полностью загружен
        self._load_local_ru()
        # Проверяем возраст сохранённого кэша
        need_net = True
        for p in (RU_CACHE, bundled_file("names_ru.json")):
            if os.path.exists(p):
                try:
                    with open(p, encoding="utf-8") as f:
                        c = json.load(f)
                    if "ru_names" in c and c.get("map"):
                        if time.time() - c.get("updated", 0) < max_age:
                            need_net = False
                            break
                except Exception:
                    pass
        if not need_net:
            return

        try:
            def get(host, what):
                time.sleep(0.3)  # пауза, чтобы избежать 429 Too Many Requests от GGG
                return requests.get(f"https://{host}.pathofexile.com/api/trade/data/{what}",
                                    headers=HEADERS, timeout=20).json()["result"]
            m, rn = dict(self.ru), dict(self.ru_names)
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
                b_entries = b.get("entries", [])
                if len(a_entries) != len(b_entries):
                    continue
                for x, y in zip(a_entries, b_entries):
                    for k in ("name", "type", "text"):
                        if x.get(k) and y.get(k):
                            m.setdefault(y[k].lower(), x[k])
                            rn.setdefault(x[k].lower(), y[k])

            # Нотаблы Forbidden Flame / Flesh из stats API
            try:
                en_notables = {}
                for grp in get("www", "stats"):
                    for e in grp.get("entries", []):
                        eid = e.get("id", "")
                        if eid.startswith("explicit.stat_2460506030|"):
                            mm = re.match(r"Allocates (.+?) if you have", e.get("text", ""))
                            if mm:
                                en_notables[eid] = mm.group(1).strip()
                for grp in get("ru", "stats"):
                    for e in grp.get("entries", []):
                        eid = e.get("id", "")
                        if eid in en_notables:
                            mm = re.match(r"Дарует умение (.+?),\s*если у вас", e.get("text", ""))
                            if mm:
                                ru_n = mm.group(1).strip()
                                en_n = en_notables[eid]
                                m.setdefault(ru_n.lower(), en_n)
                                rn.setdefault(en_n.lower(), ru_n)
            except Exception:
                pass

            if len(m) >= 100:
                self.ru, self.ru_names = m, rn
                self._ru_yo = None
                write_json(RU_CACHE, {"updated": time.time(), "map": m, "ru_names": rn})
                log(tr("ru_loaded", n=len(m)))
        except Exception as e:
            # При любой сетевой ошибке остаёмся на надёжном локальном словаре
            log(tr("ru_err", e=e))

    def to_en(self, name):
        if not name:
            return ""
        n = name.strip()
        nl = n.lower()
        if nl == "кровь мага":
            return "Mageblood"
        if nl in self.ru:
            return self.ru[nl]
        norm = normalize_item_name(n)
        is_foulborn = bool(FOULBORN_PREFIX_RE.match(norm))
        base_n = FOULBORN_PREFIX_RE.sub("", norm).strip() if is_foulborn else norm
        if base_n == "кровь мага":
            base_n = "волшебная кровь"
        if base_n in self.ru:
            en = self.ru[base_n]
            return f"Foulborn {en}" if is_foulborn else en
        if norm in self.ru:
            return self.ru[norm]
        if norm in self.chaos or norm in self.names:
            return self.names.get(norm, norm.title())
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
        """Имя для поиска: русское переводим в английское, убираем префиксы качества, карт, уников и фойлов."""
        n = normalize_item_name(name)
        if not n:
            return ""

        if n == "кровь мага":
            n = "волшебная кровь"

        # Проверяем наличие префикса Foulborn / Нечестивый
        is_foulborn = bool(FOULBORN_PREFIX_RE.match(n))
        base_n = FOULBORN_PREFIX_RE.sub("", n).strip() if is_foulborn else n
        if base_n == "кровь мага":
            base_n = "волшебная кровь"

        # Если точное совпадение со своей ценой
        if n in self.custom:
            return n
        if is_foulborn and base_n in self.custom:
            return base_n

        # Перевод базового имени (плюс O(1) кэш для ё/е)
        base_en = base_n
        if base_n in self.ru:
            base_en = self.ru[base_n].lower()
        else:
            yo_map = getattr(self, "_ru_yo", None)
            if yo_map is None or len(yo_map) == 0 and self.ru:
                yo_map = {k.replace("ё", "е"): v for k, v in self.ru.items() if "ё" in k}
                self._ru_yo = yo_map
            alt = base_n.replace("ё", "е")
            if alt in yo_map:
                base_en = yo_map[alt].lower()

        if is_foulborn:
            # Сначала ищем foulborn вариант на poe.ninja
            cand_fb = f"foulborn {base_en}"
            if cand_fb in self.custom:
                return cand_fb
            if cand_fb in self.chaos:
                return cand_fb
            # Если foulborn варианта нет на ninja — возвращаем базовый уник
            if base_en in self.chaos:
                return base_en

        # Обычный поиск
        if base_en in self.custom or base_en in self.chaos:
            return base_en

        # Если игрок скопировал английское имя с "foulborn "
        if n.startswith("foulborn "):
            fb_base = n[9:].strip()
            if fb_base in self.chaos:
                return fb_base
        elif f"foulborn {base_en}" in self.chaos:
            return f"foulborn {base_en}"

        # Поддержка камней умений / поддержки в русском клиенте
        yo_map = getattr(self, "_ru_yo", None) or {}
        cand_ru = f"поддержка: {base_n}"
        if cand_ru in self.ru:
            return self.ru[cand_ru].lower()
        if cand_ru.replace("ё", "е") in yo_map:
            return yo_map[cand_ru.replace("ё", "е")].lower()

        m_aw = re.match(r"^пробужд[её]нн(?:ый|ая|ое)\s*[:\-]?\s*(.+)$", base_n)
        if m_aw:
            rest = m_aw.group(1).strip()
            for pfx in ("пробуждённый - поддержка: ", "пробужденный - поддержка: ",
                        "пробуждённый: ", "пробужденный: ", "пробуждённая: ", "пробужденная: ",
                        "пробуждённое: ", "пробужденное: "):
                cand2 = pfx + rest
                if cand2 in self.ru:
                    return self.ru[cand2].lower()
                alt2 = cand2.replace("ё", "е")
                if alt2 in yo_map:
                    return yo_map[alt2].lower()

        # Английский без 'support': 'empower' -> 'empower support'
        if f"{base_en} support" in self.chaos or any(k.startswith(f"{base_en} support@") for k in self.gems):
            return f"{base_en} support"

        return self.ru.get(base_n, base_en)

    def display(self, key, lang="en"):
        """Название для показа: по-английски как в игре или по-русски, если есть перевод."""
        if "@" in key:
            base_k, var_k = key.split("@", 1)
            base_d = self.display(base_k, lang)
            var_d = self.ru_names.get(var_k, var_k) if lang == "ru" else var_k
            return f"{base_d} [{var_d}]"
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

        # 4. Ближайший стандартный уровень, если текущий не найден
        alt_lvls = []
        if "awakened " in key:
            alt_lvls = [x for x in (5, 6, 4, 1) if x != lvl]
        elif key in ("enlighten support", "empower support", "enhance support"):
            alt_lvls = [x for x in (3, 4, 2, 1) if x != lvl]
        elif lvl not in (1, 20, 21):
            alt_lvls = [20, 21, 1] if lvl >= 20 else [1, 20]
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
        m = re.match(r"(?:Requires\s+Sacrifice|[^:]*жертво[^:]*|[^:]*пожертв[^:]*|[^:]*sacrifice[^:]*):\s*(?:([\d\s,]+)\s*[xх×]\s*)?(.+?)(?:\s+[xх×]\s*([\d\s,]+))?$", l, re.I)
        if m:
            qty_pre, sac_name, qty_post = m.group(1), m.group(2).strip(), m.group(3)
            q = _num(qty_pre) if qty_pre else (_num(qty_post) if qty_post else 1)
            it["sacrifice"] = normalize_item_name(sac_name)
            it["sacrifice_qty"] = max(1, q)
        m = re.match(r"(?:Reward|Награда):\s*(?:([\d\s,]+)\s*[xх×]\s*)?(.+?)(?:\s+[xх×]\s*([\d\s,]+))?$", l, re.I)
        if m:
            qty_pre, rw_name, qty_post = m.group(1), m.group(2).strip(), m.group(3)
            q = _num(qty_pre) if qty_pre else (_num(qty_post) if qty_post else 1)
            it["reward"] = normalize_item_name(rw_name)
            it["reward_qty"] = max(1, q)
        # «На 200% больше здоровья монстров» / «200% more Monster Life»
        m = (re.search(r"(\d+)%\s+more\s+Monster\s+Life", l, re.I) or
             re.search(r"(?:на\s+)?(\d+)%\s+больше\s+(?:здоровь|жизн)\w*\s+монстр", l, re.I) or
             re.search(r"(\d+)%.*(?:здоровь|жизн).*монстр", l, re.I) or
             re.search(r"монстр.*?(\d+)%.*(?:здоровь|жизн)", l, re.I))
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
    it["unidentified"] = bool(re.search(r"^(?:Unidentified|Не опознано|Неопознанный)\s*$", cleaned, re.I | re.M))
    it["is_ru"] = bool(re.search(r"[а-яА-Я]", cleaned))

    m_v = (re.search(r"Adds\s+(\d+)\s+Small\s+Passive\s+Skills?\s+which\s+grants?\s+nothing", cleaned, re.I) or
           re.search(r"Добавляет\s+малых\s+пассивных\s+умений,\s+которые\s+ничего\s+не\s+дают:\s*(\d+)", cleaned, re.I) or
           re.search(r"Добавляет\s+(\d+)\s+мал\w+\s+пассивн\w+\s+умен\w+.*ничего\s+не\s+да", cleaned, re.I))
    if m_v:
        it["voices_passives"] = int(m_v.group(1))

    m_f = (re.search(r"Allocates\s+(.+?)\s+if\s+you\s+have\s+the\s+matching\s+modifier\s+on\s+Forbidden\s+(?:Flame|Flesh)", cleaned, re.I) or
           re.search(r"Дарует\s+умение\s+(.+?),\s*если\s+у\s+вас\s+есть\s+аналогичное\s+свойство\s+на\s+Запретн(?:ом\s+пламени|ой\s+плоти)", cleaned, re.I))
    if m_f:
        it["forbidden_notable"] = m_f.group(1).strip()

    m_mb = (re.search(r"Leftmost\s+(\d+)\s+Magic\s+Utility\s+Flasks", cleaned, re.I) or
            re.search(r"(\d+)\s+магическ\w+\s+особ\w+\s+флакон", cleaned, re.I))
    if m_mb:
        it["mageblood_flasks"] = int(m_mb.group(1))

    return it


def _fmt_range(v):
    return f"{v:.1f}" if v < 10 else f"{v:,.0f}".replace(",", " ")


def value_of(text, prices):
    """-> (цена в хаосах или None, пояснение)"""
    it = parse_item(text)
    name = it["name"]
    if it["unidentified"] and it["rarity"].lower() in ("unique", "уникальный"):
        return None, tr("unidentified_unique", base=name)

    if it["reward"] is not None:  # Inscribed Ultimatum — считаем только чистую прибыль
        rw = it["reward"]
        low = rw.lower()
        sac, n = it["sacrifice"], it["sacrifice_qty"]
        if sac and any(w in sac.lower() for w in ("no cost", "без жертв", "не требует жертв")):
            sac = None
        mark = lambda nm: "✎" if prices.is_custom(nm) else "?" if prices.unreliable(nm) else ""
        mult = (2 if any(w in low for w in ("double", "удваива", "удвоени")) else
                3 if any(w in low for w in ("triple", "утраива", "утроени")) else None)
        if mult and sac:
            if any(w in sac.lower() for w in ("rare ", "редк")):
                return None, "SPECIAL:" + tr("ult_special_rare")
            # «удваивает» 8 штук: вернут 16, из них 8 своих — прибыль 8 штук
            p = prices.price(sac)
            if p is None:
                return None, tr("no_price", name=sac)
            extra = (mult - 1) * n
            k_sac = prices._key(sac)
            disp_sac = prices.display(k_sac, lang="ru" if it.get("is_ru") else "en") or sac
            rng = ""
            mv = prices.max_chaos.get(k_sac, 0)
            if not prices.is_custom(sac) and mv > p * 1.8:
                rng = f" · {tr('up_to', c=_fmt_range(mv * extra * it['qty']))}"
            return extra * p * it["qty"], f"{extra} × {disp_sac} ({p:.1f}c{mark(sac)}){rng}"

        if any(w in low for w in ("mirror", "отража", "зеркал")) and any(w in low for w in ("rare", "редк")):
            return None, "SPECIAL:" + tr("ult_special_mirror")
        if any(w in low for w in ("rare ", "редк")) and "scarab" not in low:
            return None, "SPECIAL:" + tr("ult_special_rare")

        p = prices.price(rw)
        if p is None:
            return None, tr("no_reward_price", name=rw)
        rw_qty = it.get("reward_qty", 1)
        k_rw = prices._key(rw)
        disp_rw = prices.display(k_rw, lang="ru" if it.get("is_ru") else "en") or rw
        rng = ""
        mv = prices.max_chaos.get(k_rw, 0)
        if not prices.is_custom(rw) and mv > p * 1.8:
            rng = f" · {tr('up_to', c=_fmt_range(mv * rw_qty * it['qty']))}"
        if sac:
            # награда — другой предмет взамен пожертвованного: прибыль = награда − жертва
            ps = prices.price(sac)
            if ps is None:
                return None, tr("no_price", name=sac)
            disp_sac = prices.display(prices._key(sac), lang="ru" if it.get("is_ru") else "en") or sac
            net = p * rw_qty - ps * n
            return net * it["qty"], (f"{rw_qty} × {disp_rw} ({p:.1f}c{mark(rw)}) − {n} × {disp_sac} ({ps:.1f}c{mark(sac)}){rng}")
        return p * rw_qty * it["qty"], f"{rw_qty} × {disp_rw} ({p:.1f}c{mark(rw)}){rng}"

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

    key = prices._key(name)
    if key == "voices" and it.get("voices_passives") and not prices.is_custom(name):
        np = it["voices_passives"]
        for cand in (f"voices@{np} passives", f"voices@{np} passive"):
            if cand in prices.variants:
                pv = prices.variants[cand]
                q = "?" if cand in prices.low_variants else ""
                return pv * it["qty"], f"{it['qty']} × {name} ({np} passives) ({pv:.1f}c{q})"

    if key in ("forbidden flesh", "forbidden flame") and it.get("forbidden_notable") and not prices.is_custom(name):
        notable_raw = it["forbidden_notable"]
        notable_en = prices.to_en(notable_raw).lower()
        vk = f"{key}@{notable_en}"
        if vk in prices.variants:
            pv = prices.variants[vk]
            q = "?" if vk in prices.low_variants else ""
            return pv * it["qty"], f"{it['qty']} × {name} [{notable_raw}] ({pv:.1f}c{q})"

    if key in ("mageblood", "foulborn mageblood") and it.get("mageblood_flasks") and not prices.is_custom(name):
        nf = it["mageblood_flasks"]
        vk = f"{key}@{nf} flasks"
        if vk in prices.variants:
            pv = prices.variants[vk]
            q = "?" if vk in prices.low_variants else ""
            return pv * it["qty"], f"{it['qty']} × {name} ({nf} flasks) ({pv:.1f}c{q})"

    lookup = name
    p = prices.price(name)
    is_base = False
    if p is None and it["base"]:
        lookup, p = it["base"], prices.price(it["base"])
        is_base = True
    if p is None:
        return None, tr("no_price", name=name)
    is_shaky = prices.unreliable(lookup) or is_base
    q = "✎" if prices.is_custom(lookup) else "?" if is_shaky else ""
    note = f" ({tr('base_short')})" if is_base else ""
    k_eff = prices._key(lookup)
    mv = prices.max_chaos.get(k_eff, 0)
    rng = f" · {tr('up_to', c=_fmt_range(mv * it['qty']))}" if (not prices.is_custom(lookup) and mv > p * 1.8) else ""
    return p * it["qty"], f"{it['qty']} × {name}{note} ({p:.1f}c{q}){rng}"
