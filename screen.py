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

    def to_screen(self, x, y):
        L, T, W, H = self.rect()
        s = H / REF_H
        return int(round(L + W / 2 + (x - REF_W / 2 + self.dx) * s)), int(round(T + (y + self.dy) * s))

    def grab(self, x1, y1, x2, y2):
        if self.sct is None:
            self.sct = mss.mss()
        a, b = self.to_screen(x1, y1), self.to_screen(x2, y2)
        img = np.array(self.sct.grab({"left": a[0], "top": a[1],
                                      "width": max(1, b[0] - a[0]), "height": max(1, b[1] - a[1])}))
        return cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

    def grab_icon(self, i):
        x, y = MODS[i]
        h = MOD_ICON / 2
        return self.grab(x - h, y - h, x + h, y + h)


def poe_running():
    """Есть ли окно Path of Exile."""
    return bool(user32.FindWindowW("POEWindowClass", None) or user32.FindWindowW(None, "Path of Exile"))


def cursor_pos():
    pt = wt.POINT()
    user32.GetCursorPos(ctypes.byref(pt))
    return pt.x, pt.y


def clipboard_seq():
    """Номер изменения буфера обмена: дёшево проверять, не копировал ли игрок что-то новое."""
    return user32.GetClipboardSequenceNumber()
