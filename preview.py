"""Предпросмотр наград ультиматума: карточки и уникальные предметы.
Хранит данные (уровень, моды, база, флейвор, иконки) и кэширует картинки."""
import json
import os
import re
import threading
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
_IMG_CACHE = {}         # (cache_key, w, h) -> ImageTk.PhotoImage
_PENDING_DOWNLOADS = set()
_LOCK = threading.Lock()


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
    if not name:
        return ""
    n = name.strip().replace("\xa0", " ").lower()
    # Убираем количество в начале (например, "2x ", "8× "):
    n = re.sub(r"^\d+\s*[xх×]\s*", "", n).strip()
    for pfx in ("superior ", "качественный ", "качественная ", "качественное ",
                "превосходный ", "превосходная ", "превосходное "):
        if n.startswith(pfx):
            n = n[len(pfx):].strip()
    n = re.sub(r"^[\"'«]+|[\"'»]+$", "", n).strip()
    for pfx in ("карточка ", "гадальная карта ", "карта гадания ", "divination card "):
        if n.startswith(pfx):
            n = n[len(pfx):].strip()
            n = re.sub(r"^[\"'«]+|[\"'»]+$", "", n).strip()
    return n


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
        for u_data in db.get("uniques", {}).values():
            if u_data.get("name_ru", "").lower() == raw or u_data.get("name_en", "").lower() == raw:
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
    # 1. Сначала проверяем вшитые/локальные файлы программы
    if image_file:
        local_bundled = bundled_file(os.path.join("preview_images", item_type, image_file))
        if os.path.exists(local_bundled):
            size_key = (f"bundled_{item_type}_{image_file}", max_w, max_h)
            with _LOCK:
                if size_key in _IMG_CACHE:
                    return _IMG_CACHE[size_key]
            try:
                im = Image.open(local_bundled)
                im.thumbnail((max_w, max_h), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(im)
                with _LOCK:
                    _IMG_CACHE[size_key] = photo
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

    with _LOCK:
        if size_key in _IMG_CACHE:
            return _IMG_CACHE[size_key]

    local_path = os.path.join(CACHE_DIR, cache_key)
    if os.path.exists(local_path):
        try:
            im = Image.open(local_path)
            im.thumbnail((max_w, max_h), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(im)
            with _LOCK:
                _IMG_CACHE[size_key] = photo
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
