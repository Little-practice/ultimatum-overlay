"""Трей, автозапуск с Windows и автообновление."""
import os
import subprocess
import sys
import tempfile
import threading

import requests

FROZEN = getattr(sys, "frozen", False)
EXE = os.path.abspath(sys.executable) if FROZEN else None
RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
APP_NAME = "UltimatumOverlay"

# ---------------- автообновление ----------------
# Заполнить, когда программа будет на GitHub: "владелец/репозиторий".
# Пока пусто — проверка обновлений выключена.
GITHUB_REPO = "Little-practice/ultimatum-overlay"


def _ver(s):
    s = s.strip().lstrip("vV")
    return tuple(int(x) for x in s.split(".") if x.isdigit())


def check_update(current):
    """-> (новая версия, ссылка на exe) или None. Без GITHUB_REPO всегда None."""
    if not GITHUB_REPO or not FROZEN:
        return None
    try:
        r = requests.get(f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest",
                         headers={"User-Agent": "ultimatum-overlay"}, timeout=15).json()
        tag = r.get("tag_name", "")
        if not tag or _ver(tag) <= _ver(current):
            return None
        exe = sha = None
        for a in r.get("assets", []):
            n = a.get("name", "").lower()
            if n.endswith(".exe"):
                exe = a["browser_download_url"]
            elif n.endswith(".sha256"):
                sha = a["browser_download_url"]
        if exe:
            return tag.lstrip("vV"), exe, sha
    except Exception:
        pass
    return None


def install_update(url, sha_url=None, progress=lambda p: None):
    """Скачать новый exe и заменить им текущий: маленький .bat ждёт закрытия программы,
    подменяет файл и запускает новую версию. Вызывающий должен сразу закрыть программу."""
    tmp = os.path.join(tempfile.gettempdir(), APP_NAME + "_new.exe")
    with requests.get(url, headers={"User-Agent": "ultimatum-overlay"}, stream=True, timeout=120) as r:
        r.raise_for_status()
        total = int(r.headers.get("content-length", 0)) or None
        done = 0
        with open(tmp, "wb") as f:
            for chunk in r.iter_content(1 << 16):
                f.write(chunk)
                done += len(chunk)
                if total:
                    progress(done / total)
    if total and done != total:
        raise RuntimeError("download incomplete")
    if sha_url:   # сверить контрольную сумму из выпуска
        import hashlib
        want = requests.get(sha_url, headers={"User-Agent": "ultimatum-overlay"}, timeout=30).text.split()[0].lower()
        h = hashlib.sha256()
        with open(tmp, "rb") as f:
            for chunk in iter(lambda: f.read(1 << 20), b""):
                h.update(chunk)
        if h.hexdigest().lower() != want:
            os.remove(tmp)
            raise RuntimeError("checksum mismatch")
    bat = os.path.join(tempfile.gettempdir(), APP_NAME + "_update.bat")
    import ctypes
    oem = f"cp{ctypes.windll.kernel32.GetOEMCP()}"
    # ждём, пока exe освободится (у onefile-сборки два процесса), подменяем — до 60 попыток
    with open(bat, "w", encoding=oem, errors="replace") as f:
        f.write(f'''@echo off
set n=0
:retry
timeout /t 1 /nobreak >nul
move /y "{tmp}" "{EXE}" >nul 2>&1
if errorlevel 1 (
  set /a n+=1
  if %n% lss 60 goto retry
  start "" "{EXE}"
  goto end
)
start "" "{EXE}"
:end
del "%~f0"
''')
    subprocess.Popen(["cmd", "/c", bat], creationflags=0x08000000)  # CREATE_NO_WINDOW


# ---------------- автозапуск ----------------
def autostart_enabled():
    if not FROZEN:
        return False
    import winreg
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as k:
            val, _ = winreg.QueryValueEx(k, APP_NAME)
            return EXE.lower() in val.lower()
    except OSError:
        return False


def set_autostart(on):
    """Запуск с Windows (свёрнутым в трей). Работает только у собранного exe."""
    if not FROZEN:
        return False
    import winreg
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE) as k:
        if on:
            winreg.SetValueEx(k, APP_NAME, 0, winreg.REG_SZ, f'"{EXE}" --tray')
        else:
            try:
                winreg.DeleteValue(k, APP_NAME)
            except OSError:
                pass
    return True


# ---------------- трей ----------------
class Tray:
    """Значок в трее: открыть окно, скрыть/показать оверлей, выход."""

    def __init__(self, png_bytes, title, on_open, on_toggle, on_quit, labels):
        import io
        import pystray
        from PIL import Image
        import base64
        data = base64.b64decode(png_bytes) if isinstance(png_bytes, str) else png_bytes
        img = Image.open(io.BytesIO(data))
        menu = pystray.Menu(
            pystray.MenuItem(labels["open"], lambda: on_open(), default=True),
            pystray.MenuItem(labels["toggle"], lambda: on_toggle()),
            pystray.MenuItem(labels["quit"], lambda: on_quit()),
        )
        self.icon = pystray.Icon(APP_NAME, img, title, menu)
        threading.Thread(target=self.icon.run, daemon=True).start()

    def stop(self):
        try:
            self.icon.stop()
        except Exception:
            pass
