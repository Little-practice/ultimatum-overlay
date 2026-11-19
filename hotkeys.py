"""Глобальные горячие клавиши через RegisterHotKey (без сторонних библиотек) и короткий звук."""
import ctypes
import ctypes.wintypes as wt
import threading

user32 = ctypes.windll.user32
MOD_ALT, MOD_CTRL, MOD_SHIFT = 0x1, 0x2, 0x4
VK_NAMES = {**{0x6F + i: f"F{i}" for i in range(1, 25)}, **{c: chr(c) for c in range(0x30, 0x3A)},
            **{c: chr(c) for c in range(0x41, 0x5B)}, **{0x60 + i: f"Num{i}" for i in range(10)},
            0x2D: "Insert", 0x2E: "Delete", 0x24: "Home", 0x23: "End", 0x21: "PageUp", 0x22: "PageDown",
            0x13: "Pause", 0x91: "ScrollLock", 0xC0: "`", 0x6A: "Num*", 0x6B: "Num+", 0x6D: "Num-",
            0x6F: "Num/", 0x20: "Space"}


def key_name(vk, mods):
    parts = [n for m, n in ((MOD_CTRL, "Ctrl"), (MOD_SHIFT, "Shift"), (MOD_ALT, "Alt")) if mods & m]
    return "+".join(parts + [VK_NAMES.get(vk, f"VK{vk}")])


class Hotkey(threading.Thread):
    """Одна горячая клавиша. Сменить клавишу: stop() и создать новую."""

    def __init__(self, vk, mods, callback):
        super().__init__(daemon=True)
        self.vk, self.mods, self.cb = vk, mods, callback
        self.ok = False
        self.tid = None
        self.ready = threading.Event()

    def run(self):
        self.tid = ctypes.windll.kernel32.GetCurrentThreadId()
        self.ok = bool(user32.RegisterHotKey(None, 1, self.mods | 0x4000, self.vk))  # 0x4000 = MOD_NOREPEAT
        self.ready.set()
        msg = wt.MSG()
        while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
            if msg.message == 0x0312:  # WM_HOTKEY
                try:
                    self.cb()
                except Exception:
                    pass
        if self.ok:
            user32.UnregisterHotKey(None, 1)

    def stop(self):
        if self.tid:
            user32.PostThreadMessageW(self.tid, 0x0012, 0, 0)  # WM_QUIT
            self.join(timeout=1)


def beep(kind="alert"):
    """Короткий системный звук (не блокирует)."""
    def play():
        try:
            import winsound
            winsound.MessageBeep(winsound.MB_ICONEXCLAMATION if kind == "alert" else winsound.MB_ICONASTERISK)
        except Exception:
            pass
    threading.Thread(target=play, daemon=True).start()


# ---------- кто нажал Ctrl+C: человек или другой прайсчекер ----------
class _KBD(ctypes.Structure):
    _fields_ = [("vkCode", wt.DWORD), ("scanCode", wt.DWORD), ("flags", wt.DWORD), ("time", wt.DWORD),
                ("dwExtraInfo", ctypes.c_size_t)]


_HOOKPROC = ctypes.WINFUNCTYPE(ctypes.c_ssize_t, ctypes.c_int, wt.WPARAM, wt.LPARAM)
_MODIFIERS = {0x10, 0x11, 0x12, 0xA0, 0xA1, 0xA2, 0xA3, 0xA4, 0xA5, 0x5B, 0x5C}


class KeyWatch(threading.Thread):
    """Только слушает клавиатуру (ничего не нажимает и не блокирует).
    Нужен, чтобы отличить Ctrl+C, нажатый человеком, от Ctrl+C, который сделал другой прайсчекер
    после своей комбинации (Ctrl+D, Ctrl+Shift+…, Alt+D и т. п.)."""
    COPY_WINDOW = 1.5   # Ctrl+C должен быть не раньше стольких секунд до изменения буфера
    OTHER_WINDOW = 0.8  # другая комбинация незадолго до Ctrl+C — значит, копировал чужой прайсчекер
    BLIND = 3.0         # хук не видел вообще никаких нажатий столько секунд — значит, он «слепой»

    def __init__(self):
        super().__init__(daemon=True)
        self.ok = False
        self.last_c = None       # (время, нажато программой?)
        self.last_other = 0.0    # время последней Ctrl/Alt+клавиша (не C)
        self.last_any = 0.0      # время любого нажатия
        self._proc = _HOOKPROC(self._hook)

    def run(self):
        import time as _t
        self._time = _t.monotonic
        user32.SetWindowsHookExW.restype = wt.HHOOK
        user32.SetWindowsHookExW.argtypes = [ctypes.c_int, _HOOKPROC, wt.HINSTANCE, wt.DWORD]
        user32.CallNextHookEx.argtypes = [wt.HHOOK, ctypes.c_int, wt.WPARAM, wt.LPARAM]
        user32.CallNextHookEx.restype = ctypes.c_ssize_t
        h = user32.SetWindowsHookExW(13, self._proc, None, 0)  # WH_KEYBOARD_LL
        self.ok = bool(h)
        msg = wt.MSG()
        while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
            pass

    def _hook(self, code, wparam, lparam):
        try:
            if code == 0 and wparam in (0x100, 0x104):  # WM_KEYDOWN / WM_SYSKEYDOWN
                k = ctypes.cast(lparam, ctypes.POINTER(_KBD)).contents
                self.on_key(k.vkCode, bool(k.flags & 0x10), self._time())
        except Exception:
            pass
        return user32.CallNextHookEx(None, code, wparam, lparam)

    def on_key(self, vk, injected, now):
        self.last_any = now
        if vk in _MODIFIERS:
            return
        ctrl = user32.GetAsyncKeyState(0x11) & 0x8000
        alt = user32.GetAsyncKeyState(0x12) & 0x8000
        if ctrl and vk == 0x43 and not alt:   # Ctrl+C (физически та же клавиша и в русской раскладке)
            self.last_c = (now, injected)
        elif ctrl or alt:
            self.last_other = now

    def user_copied(self, now):
        """Буфер изменился в момент now: это Ctrl+C самого игрока?"""
        if not self.ok:
            return True  # слушать клавиатуру не вышло — работаем как раньше
        if now - self.last_any > self.BLIND:
            # нажатий не видно: игра запущена от имени администратора и Windows их не показывает —
            # тогда показываем карточку на любое копирование, как без этой защиты
            return True
        if self.last_c is None:
            return False
        t, injected = self.last_c
        if now - t > self.COPY_WINDOW or injected:
            return False
        return not (0 <= t - self.last_other <= self.OTHER_WINDOW)
