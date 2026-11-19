"""Цены с poe.ninja и оценка предмета по тексту из Ctrl+C."""
import json
import os
import re
import time

import threading

import requests

from paths import write_json

from i18n import tr

from paths import APP_DIR as HERE
CACHE = os.path.join(HERE, "prices_cache.json")
RU_CACHE = os.path.join(HERE, "names_ru.json")
CUSTOM_FILE = os.path.join(HERE, "my_prices.json")
LEAGUES_FILE = os.path.join(HERE, "leagues.json")   # цены, которые игрок вписал сам
BASE = "https://poe.ninja/poe1/api/economy"
EXCHANGE_TYPES = ["Currency", "Fragment", "DivinationCard", "Scarab", "Essence", "Fossil",
                  "Resonator", "Oil", "Omen", "DeliriumOrb", "Tattoo", "Artifact"]
STASH_TYPES = ["UniqueWeapon", "UniqueArmour", "UniqueAccessory", "UniqueJewel",
               "UniqueFlask", "UniqueMap", "Map", "Invitation", "Beast"]
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
        self.names = {}      # имя (lower) -> как пишется в игре
        self.cat = {}        # имя (lower) -> раздел poe.ninja
        self.custom = {}     # имя (lower) -> своя цена в хаосах
        self.lock = threading.Lock()   # одна загрузка цен за раз
        self.load_custom()

    def _from_cache(self, league, max_age):
        try:
            with open(CACHE, encoding="utf-8") as f:
                c = json.load(f)
        except Exception:
            return False
        if c.get("league") != league or (max_age is not None and time.time() - c["updated"] >= max_age):
            return False
        self.league, self.chaos, self.divine, self.updated = league, c["chaos"], c["divine"], c["updated"]
        self.low = set(c.get("low", []))
        self.names = c.get("names", {})
        self.cat = c.get("cat", {})
        return True

    def load(self, league, max_age=3600, log=print):
        """Свежий кэш (меньше часа) — берём его, иначе качаем с poe.ninja.
        Если скачать не вышло (нет интернета) — работаем на последних сохранённых ценах."""
        if self._from_cache(league, max_age):
            self.load_ru(log)
            return
        try:
            self.refresh(league, log)
        except Exception as e:
            if self._from_cache(league, None):
                age = (time.time() - self.updated) / 3600
                log(tr("prices_stale", e=e, h=f"{age:.0f}"))
                self.load_ru(log)
            else:
                raise

    def refresh(self, league, log=print):
        chaos = {}
        low = set()
        disp, cat = {}, {}
        divine = 0.0
        failed = []
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
                    chaos[n.lower()] = pv
                    disp[n.lower()] = n
                    cat[n.lower()] = t
                    # объём торгов в хаосах / цена = сколько штук продано; меньше 3 — цена ненадёжна
                    if pv > 0 and (ln.get("volumePrimaryValue") or 0) / pv < 3:
                        low.add(n.lower())
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
                if ln.get("links"):          # 5-6 линков пропускаем: в награде обычно без линков
                    continue
                n = ln["name"].lower()
                v = float(ln.get("chaosValue") or 0)
                if n not in chaos or v < chaos[n]:  # для разных вариантов берём самый дешёвый
                    chaos[n] = v
                    disp[n] = ln["name"]
                    cat[n] = t
                    if (ln.get("listingCount") or ln.get("count") or 0) < 5:
                        low.add(n)
                    else:
                        low.discard(n)
        # без валюты (и курса дивайна) или почти без данных — старые цены лучше неполных
        if not chaos or "Currency" in failed or not (divine or chaos.get("divine orb")) or len(failed) > 6:
            raise RuntimeError(tr("ninja_empty"))
        self.league, self.chaos, self.updated, self.low = league, chaos, time.time(), low
        self.names, self.cat = disp, cat
        self.divine = divine or chaos.get("divine orb", 0)
        write_json(CACHE, {"league": league, "chaos": chaos, "divine": self.divine, "updated": self.updated,
                           "low": sorted(low), "names": disp, "cat": cat})
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
        try:
            with open(LEAGUES_FILE, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    def load_ru(self, log=print, max_age=7 * 86400):
        """Словарь русское название -> английское (официальный API трейда, ru и www)."""
        cached = None
        if os.path.exists(RU_CACHE):
            try:
                with open(RU_CACHE, encoding="utf-8") as f:
                    c = json.load(f)
                if "ru_names" in c:
                    cached = c
                    if time.time() - c["updated"] < max_age:
                        self.ru, self.ru_names = c["map"], c["ru_names"]
                        return
            except Exception:
                pass
        try:
            def get(host, what):
                return requests.get(f"https://{host}.pathofexile.com/api/trade/data/{what}",
                                    headers=HEADERS, timeout=30).json()["result"]
            m, rn = {}, {}
            en_s = {e["id"]: e["text"] for c in get("www", "static") for e in c["entries"] if e.get("text")}
            for c in get("ru", "static"):
                for e in c["entries"]:
                    if e["id"] in en_s and e.get("text"):
                        m[e["text"].lower()] = en_s[e["id"]]
                        rn.setdefault(en_s[e["id"]].lower(), e["text"])
            for a, b in zip(get("www", "items"), get("ru", "items")):
                if a["id"] != b["id"] or len(a["entries"]) != len(b["entries"]):
                    continue
                for x, y in zip(a["entries"], b["entries"]):
                    for k in ("name", "type"):
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
        return self.ru.get(n.lower(), n)

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
        """Имя для поиска: русское переводим в английское."""
        n = name.strip().lower()
        if n not in self.chaos and n not in self.custom and n in self.ru:
            n = self.ru[n].lower()
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


# ---------------- разбор текста предмета ----------------
def _num(s):
    return int(re.sub(r"[^\d]", "", s) or 0)


def parse_item(text):
    """-> dict(name, base, rarity, qty, sacrifice, sacrifice_qty, reward)"""
    secs = [s.strip().splitlines() for s in text.replace("\r", "").split("--------")]
    head = [l.strip() for l in secs[0] if l.strip()]
    rarity = ""
    names = []
    for l in head:
        if re.match(r"(Rarity|Редкость):", l):
            rarity = l.split(":", 1)[1].strip()
        elif not re.match(r"(Item Class|Класс предмета):", l):
            names.append(l)
    it = {"rarity": rarity, "name": names[0] if names else "", "base": names[1] if len(names) > 1 else "",
          "qty": 1, "sacrifice": None, "sacrifice_qty": 1, "reward": None, "monster_life": None,
          "life_lang": "en"}
    for l in text.replace(chr(13), "").splitlines():
        l = l.strip()
        m = re.match(r"(?:Stack Size|Размер стопки|Количество в стопке):\s*([\d\s,.]+)/", l)
        if m:
            it["qty"] = max(1, _num(m.group(1)))
        m = re.match(r"(?:Requires Sacrifice|[^:]*[Пп]ожертв[^:]*):\s*(.+?)(?:\s+[xх×]\s*([\d\s,]+))?$", l)
        if m:
            it["sacrifice"] = m.group(1).strip()
            it["sacrifice_qty"] = _num(m.group(2)) if m.group(2) else 1
        m = re.match(r"(?:Reward|Награда):\s*(.+)$", l)
        if m:
            it["reward"] = m.group(1).strip()
        # «200% more Monster Life» (у Inscribed Ultimatum бывает 70 / 120 / 200 %)
        m = re.match(r"(\d+)%\s+more\s+Monster\s+Life", l, re.I) or \
            re.match(r"(\d+)%.*(?:здоровь|жизн).*монстр", l, re.I) or \
            re.match(r"(\d+)%.*монстр.*(?:здоровь|жизн)", l, re.I)
        if m:
            it["monster_life"] = int(m.group(1))
            it["life_lang"] = "ru" if re.search("[а-яА-Я]", l) else "en"   # язык клиента игры
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
        mult = (2 if low.startswith(("doubles", "удваивает")) else
                3 if low.startswith(("triples", "утраивает")) else None)
        if mult and sac:
            # «удваивает» 8 штук: вернут 16, из них 8 своих — прибыль 8 штук
            p = prices.price(sac)
            if p is None:
                return None, tr("no_price", name=sac)
            extra = (mult - 1) * n
            return extra * p * it["qty"], f"{extra} x {sac} ({p:.1f}c{mark(sac)})"
        p = prices.price(rw)
        if p is None:
            return None, tr("no_reward_price", name=rw)
        if sac:
            # награда — другой предмет взамен пожертвованного: прибыль = награда − жертва
            ps = prices.price(sac)
            if ps is None:
                return None, tr("no_price", name=sac)
            net = p - ps * n
            return net * it["qty"], (f"{rw} ({p:.1f}c{mark(rw)}) − {n} x {sac} ({ps:.1f}c{mark(sac)})")
        return p * it["qty"], f"→ {rw} ({p:.1f}c{mark(rw)})"
    key = name
    p = prices.price(name)
    if p is None and it["base"]:
        key, p = it["base"], prices.price(it["base"])
    if p is None:
        return None, tr("no_price", name=name)
    q = "✎" if prices.is_custom(key) else "?" if prices.unreliable(key) else ""
    return p * it["qty"], f"{it['qty']} x {name} ({p:.1f}c{q})"
