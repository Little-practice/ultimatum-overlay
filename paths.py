"""Где программа хранит свои данные.
- Собранный .exe: настройки, список модов и кэш цен — в %APPDATA%\\UltimatumOverlay
  (exe можно кинуть куда угодно, рядом с ним ничего не создаётся).
  Тир-лист по умолчанию и базовые файлы (словарь, цены, лиги) зашиты внутрь exe.
- Запуск из исходников: всё рядом с main.py."""
import json
import os
import shutil
import sys
import threading

if getattr(sys, "frozen", False):
    APP_DIR = os.path.join(os.environ.get("APPDATA") or os.path.expanduser("~"), "UltimatumOverlay")
    BUNDLE_DIR = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(sys.executable)))
    DEFAULT_ICONS = os.path.join(BUNDLE_DIR, "icons_default")
else:
    APP_DIR = os.path.dirname(os.path.abspath(__file__))
    BUNDLE_DIR = APP_DIR
    DEFAULT_ICONS = os.path.join(APP_DIR, "icons")
os.makedirs(APP_DIR, exist_ok=True)


def bundled_file(filename):
    """Путь к файлу, зашитому в сборку (или рядом с исходниками)."""
    return os.path.join(BUNDLE_DIR, filename)


def ensure_initial_file(filename):
    """Если файла нет в APPDATA, но он зашит в сборку — безопасно копируем его в APPDATA."""
    dst = os.path.join(APP_DIR, filename)
    src = bundled_file(filename)
    if not os.path.exists(dst) and os.path.exists(src):
        try:
            shutil.copyfile(src, dst)
        except Exception:
            pass
    return dst


_write_lock = threading.Lock()


def write_json(path, obj, **kw):
    """Записать json надёжно: сначала во временный файл, потом подменить. Если запись прервётся,
    старый файл останется целым. Безопасно из разных потоков."""
    with _write_lock:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(obj, f, ensure_ascii=False, **kw)
        os.replace(tmp, path)


def restore_default_icons(icon_dir):
    """Заменить список модов тир-листом, зашитым в программу."""
    if os.path.abspath(icon_dir) == os.path.abspath(DEFAULT_ICONS):
        return
    if os.path.isdir(icon_dir):
        shutil.rmtree(icon_dir)
    shutil.copytree(DEFAULT_ICONS, icon_dir)
