"""Предпросмотр наград ультиматума: карточки и уникальные предметы.
Хранит данные (уровень, моды, база, флейвор, иконки) и кэширует картинки."""
import collections
import io
import json
import os
import re
import threading
import zipfile
from urllib.parse import urlparse
import requests
from PIL import Image, ImageTk

from paths import APP_DIR, bundled_file

CACHE_DIR = os.path.join(APP_DIR, "cache", "images")
try:
    os.makedirs(CACHE_DIR, exist_ok=True)
except Exception:
    pass

_DB = None
_IMG_CACHE = collections.OrderedDict()  # (cache_key, w, h) -> ImageTk.PhotoImage (LRU)
MAX_IMG_CACHE = 150
_ZIP_ARC = None
_ZIP_CHECKED = False
_PENDING_DOWNLOADS = set()
_LOCK = threading.Lock()


def _cache_put(key, photo):
    with _LOCK:
        _IMG_CACHE[key] = photo
        _IMG_CACHE.move_to_end(key)
        while len(_IMG_CACHE) > MAX_IMG_CACHE:
            _IMG_CACHE.popitem(last=False)


def _cache_get(key):
    with _LOCK:
        if key in _IMG_CACHE:
            _IMG_CACHE.move_to_end(key)
            return _IMG_CACHE[key]
    return None


def _read_from_zip(item_type, image_file):
    global _ZIP_ARC, _ZIP_CHECKED
    with _LOCK:
        if not _ZIP_CHECKED:
            _ZIP_CHECKED = True
            for zp in (bundled_file("preview_images.zip"), os.path.join(APP_DIR, "preview_images.zip")):
                if os.path.exists(zp):
                    try:
                        _ZIP_ARC = zipfile.ZipFile(zp, "r")
                        break
                    except Exception:
                        _ZIP_ARC = None
        arc = _ZIP_ARC
        if arc is None:
            return None
        try:
            data = arc.read(f"{item_type}/{image_file}")
            return Image.open(io.BytesIO(data))
        except Exception:
            return None


def load_db():
    global _DB
    if _DB is not None:
        return _DB
    for p in (bundled_file("items_preview.json"), DB_FILE_PATH()):
        if os.path.exists(p):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    _DB = json.load(f)
                    return _DB
            except Exception:
                pass
    _DB = {"cards": {}, "uniques": {}}
    return _DB


def DB_FILE_PATH():
    return os.path.join(APP_DIR, "items_preview.json")


def _clean_name(name):
    from prices import normalize_item_name
    return normalize_item_name(name)


def get_preview(item_name, client_lang="ru", to_en_fn=None):
    """Ищет предмет в базе карточек и уников. Возвращает dict с данными для отрисовки
    на языке client_lang ('ru' или 'en')."""
    db = load_db()
    raw = _clean_name(item_name)
    if not raw:
        return None

    # Английский ключ
    en_key = to_en_fn(raw).lower() if to_en_fn else raw
    en_key = _clean_name(en_key)

    # 1. Проверяем карточки
    c = db.get("cards", {}).get(en_key) or db.get("cards", {}).get(raw)
    if not c:
        # Поиск по русскому названию
        for card_data in db.get("cards", {}).values():
            if card_data.get("name_ru", "").lower() == raw or card_data.get("name_en", "").lower() == raw:
                c = card_data
                break
    if c:
        is_ru = client_lang == "ru"
        return {
            "type": "card",
            "name": c.get("name_ru" if is_ru else "name_en") or c.get("name_en"),
            "name_alt": c.get("name_en" if is_ru else "name_ru"),
            "stack": c.get("stack", 1),
            "reward": c.get("reward_ru" if is_ru else "reward_en") or c.get("reward_en"),
            "reward_type": c.get("reward_type", "unique"),
            "flavour": c.get("flavour_en", ""),
            "art_url": c.get("art_url", ""),
            "image_file": c.get("image_file", ""),
            "lang": client_lang
        }

    # 2. Проверяем уники
    u = db.get("uniques", {}).get(en_key) or db.get("uniques", {}).get(raw)
    if not u:
        from prices import FOULBORN_PREFIX_RE
        fb_raw = FOULBORN_PREFIX_RE.sub("", raw).strip()
        fb_en = FOULBORN_PREFIX_RE.sub("", en_key).strip()
        u = db.get("uniques", {}).get(fb_en) or db.get("uniques", {}).get(fb_raw)
        if not u:
            for u_data in db.get("uniques", {}).values():
                nr = u_data.get("name_ru", "").lower()
                ne = u_data.get("name_en", "").lower()
                if nr in (raw, fb_raw) or ne in (raw, fb_en, en_key):
                    u = u_data
                    break
    if u:
        is_ru = client_lang == "ru"
        imps = u.get("implicits_ru" if is_ru else "implicits_en") or u.get("implicits_en", [])
        exps = u.get("explicits_ru" if is_ru else "explicits_en") or u.get("explicits_en", [])
        return {
            "type": "unique",
            "name": u.get("name_ru" if is_ru else "name_en") or u.get("name_en"),
            "name_alt": u.get("name_en" if is_ru else "name_ru"),
            "base": u.get("base_ru" if is_ru else "base_en") or u.get("base_en"),
            "level": u.get("level", 0),
            "implicits": imps,
            "explicits": exps,
            "flavour": u.get("flavour_en", ""),
            "icon_url": u.get("icon_url", ""),
            "image_file": u.get("image_file", ""),
            "lang": client_lang
        }

    return None


def get_image(url, max_w=200, max_h=150, on_ready=None, image_file=None, item_type="cards"):
    """Возвращает PhotoImage из локального хранилища preview_images или кэша.
    Если файла нет — запускает фоновую загрузку."""
    # 1. Сначала проверяем вшитый ZIP-архив или локальные файлы программы
    if image_file:
        size_key = (f"bundled_{item_type}_{image_file}", max_w, max_h)
        cached = _cache_get(size_key)
        if cached is not None:
            return cached
        im = _read_from_zip(item_type, image_file)
        if im is None:
            local_bundled = bundled_file(os.path.join("preview_images", item_type, image_file))
            if os.path.exists(local_bundled):
                try:
                    im = Image.open(local_bundled)
                except Exception:
                    im = None
        if im is not None:
            try:
                im.thumbnail((max_w, max_h), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(im)
                _cache_put(size_key, photo)
                return photo
            except Exception:
                pass

    if not url:
        return None

    # 2. Кэш по URL (если файл скачивался динамически)
    cache_key = re.sub(r"[^a-zA-Z0-9_-]", "_", urlparse(url).path)
    if not cache_key.endswith(".png") and not cache_key.endswith(".jpg"):
        cache_key += ".png"
    size_key = (cache_key, max_w, max_h)

    cached = _cache_get(size_key)
    if cached is not None:
        return cached

    local_path = os.path.join(CACHE_DIR, cache_key)
    if os.path.exists(local_path):
        try:
            im = Image.open(local_path)
            im.thumbnail((max_w, max_h), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(im)
            _cache_put(size_key, photo)
            return photo
        except Exception:
            pass

    # Фоновое скачивание
    def _download():
        try:
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) PoE-Ultimatum/1.0"}
            r = requests.get(url, headers=headers, timeout=12)
            if r.status_code == 200 and len(r.content) > 100:
                with open(local_path, "wb") as f:
                    f.write(r.content)
                if on_ready:
                    on_ready()
        except Exception:
            pass
        finally:
            with _LOCK:
                _PENDING_DOWNLOADS.discard(url)

    with _LOCK:
        if url not in _PENDING_DOWNLOADS:
            _PENDING_DOWNLOADS.add(url)
            threading.Thread(target=_download, daemon=True).start()

    return None
