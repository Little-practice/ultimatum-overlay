"""Окно игры, координаты и снимки экрана. Никакого управления мышью и клавиатурой."""
import ctypes
import ctypes.wintypes as wt

import cv2
import mss
import numpy as np

try:  # реальные пиксели при масштабе Windows 125%/150%
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

user32 = ctypes.windll.user32

# Точки в эталонных координатах 2000x1125; интерфейс PoE масштабируется по высоте и центрируется.
REF_W, REF_H = 2000, 1125
MODS = [(1228, 690), (1294, 690), (1360, 690)]  # три иконки усложнений
MOD_ICON = 62                                    # диаметр иконки
ACCEPT_BOX = (1200, 742, 1390, 790)              # кнопка Accept Trial
TAKE_BOX = (605, 742, 795, 790)                  # кнопка Take Rewards
DD_BOX = (920, 747, 1080, 789)                   # кнопка Double Down (появляется не всегда)


def gold_share(img):
    """Доля «золотых» пикселей — так выглядят активные кнопки окна ультиматума."""
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    return float(((hsv[..., 0] >= 8) & (hsv[..., 0] <= 30) & (hsv[..., 1] > 70) & (hsv[..., 2] > 110)).mean())


class Screen:
    def __init__(self):
        self.sct = None  # mss создаётся в том потоке, где снимаем
        self.dx = 0.0
        self.dy = 0.0

    @staticmethod
    def rect():
        """(left, top, width, height) клиентской области PoE или основного монитора."""
        hwnd = user32.FindWindowW("POEWindowClass", None) or user32.FindWindowW(None, "Path of Exile")
        if hwnd:
            r = wt.RECT()
            user32.GetClientRect(hwnd, ctypes.byref(r))
            pt = wt.POINT(0, 0)
            user32.ClientToScreen(hwnd, ctypes.byref(pt))
            if r.right > 0 and r.bottom > 0:
                return pt.x, pt.y, r.right, r.bottom
        return 0, 0, user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)

    @staticmethod
    def scale_and_origin(W, H):
        """Масштаб интерфейса PoE 1: на 16:9 и шире — по высоте; на 16:10 / 4:3 — сжат по ширине."""
        return min(H / REF_H, W / REF_W)

    def to_screen(self, x, y):
        L, T, W, H = self.rect()
        s = self.scale_and_origin(W, H)
        return (int(round(L + W / 2 + (x - REF_W / 2 + self.dx) * s)),
                int(round(T + H / 2 + (y - REF_H / 2 + self.dy) * s)))

    def grab(self, x1, y1, x2, y2):
        if self.sct is None:
            self.sct = mss.mss()
        a, b = self.to_screen(x1, y1), self.to_screen(x2, y2)
        w, h = max(1, b[0] - a[0]), max(1, b[1] - a[1])
        try:
            img = np.array(self.sct.grab({"left": a[0], "top": a[1], "width": w, "height": h}))
        except Exception:
            try:
                self.sct = mss.mss()
                img = np.array(self.sct.grab({"left": a[0], "top": a[1], "width": w, "height": h}))
            except Exception:
                return np.zeros((h, w, 3), dtype=np.uint8)
        return cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

    def grab_icon(self, i):
        x, y = MODS[i]
        h = MOD_ICON / 2
        return self.grab(x - h, y - h, x + h, y + h)


_elev_cache = {"hwnd": 0, "mismatch": False}


def poe_hwnd():
    """HWND окна Path of Exile (или 0)."""
    return user32.FindWindowW("POEWindowClass", None) or user32.FindWindowW(None, "Path of Exile")


def poe_running():
    """Есть ли окно Path of Exile."""
    return bool(poe_hwnd())


def poe_foreground():
    """Активно ли сейчас окно Path of Exile."""
    hwnd = poe_hwnd()
    return bool(hwnd and user32.GetForegroundWindow() == hwnd)


def poe_is_elevated_mismatch():
    """True, если PoE запущен от имени Администратора, а оверлей — нет (UIPI блокирует хоткеи)."""
    hwnd = poe_hwnd()
    if not hwnd:
        return False
    if _elev_cache["hwnd"] == hwnd:
        return _elev_cache["mismatch"]
    mismatch = False
    try:
        is_admin = bool(ctypes.windll.shell32.IsUserAnAdmin())
        if not is_admin:
            pid = wt.DWORD(0)
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            if pid.value:
                k32 = ctypes.windll.kernel32
                adv = ctypes.windll.advapi32
                h_proc = k32.OpenProcess(0x1000, False, pid.value)  # PROCESS_QUERY_LIMITED_INFORMATION
                if not h_proc:
                    if k32.GetLastError() == 5:  # ERROR_ACCESS_DENIED
                        mismatch = True
                else:
                    try:
                        h_tok = wt.HANDLE()
                        if adv.OpenProcessToken(h_proc, 0x0008, ctypes.byref(h_tok)):  # TOKEN_QUERY
                            try:
                                elev = wt.DWORD(0)
                                ret_len = wt.DWORD(0)
                                if adv.GetTokenInformation(h_tok, 20, ctypes.byref(elev), ctypes.sizeof(elev), ctypes.byref(ret_len)):
                                    mismatch = bool(elev.value)
                            finally:
                                k32.CloseHandle(h_tok)
                        elif k32.GetLastError() == 5:
                            mismatch = True
                    finally:
                        k32.CloseHandle(h_proc)
    except Exception:
        mismatch = False
    _elev_cache["hwnd"] = hwnd
    _elev_cache["mismatch"] = mismatch
    return mismatch


def cursor_pos():
    pt = wt.POINT()
    user32.GetCursorPos(ctypes.byref(pt))
    return pt.x, pt.y


def clipboard_seq():
    """Номер изменения буфера обмена: дёшево проверять, не копировал ли игрок что-то новое."""
    return user32.GetClipboardSequenceNumber()
