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


_SOUNDS = {}


def _render(samples, rate=44100):
    import io
    import struct
    import wave
    peak = max(1e-9, max(abs(s) for s in samples))
    frames = b"".join(struct.pack("<h", int(s / peak * 0.95 * 32767)) for s in samples)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(frames)
    return buf.getvalue()


def _tone(f, dur, square=False, attack=0.004, release=0.05, rate=44100):
    import math
    out = []
    for i in range(int(rate * dur)):
        t = i / rate
        env = min(1.0, t / attack, (dur - t) / release)
        ph = 2 * math.pi * f * t
        v = math.tanh(4 * math.sin(ph)) if square else (
            math.sin(ph) + 0.5 * math.sin(2 * ph) + 0.3 * math.sin(3 * ph) + 0.15 * math.sin(5 * ph))
        out.append(env * v)
    return out


def _match_found():
    """Громкий заметный сигнал «матч найден»: быстрая восходящая трель и высокая нота, дважды."""
    s = []
    for _ in range(2):
        for f in (784, 988, 1175):
            s += _tone(f, 0.07, release=0.02)
        s += _tone(1568, 0.22, release=0.12)
        s += [0.0] * int(44100 * 0.08)
    return _render(s)


def _alarm():
    """Резкий двухтоновый сигнал — запрещённый мод."""
    s = []
    for _ in range(3):
        s += _tone(1400, 0.11, square=True, release=0.01) + _tone(1050, 0.11, square=True, release=0.01)
    return _render(s)


def _harp3():
    """Стандартный звук «Удвоить»: глиссандо арфы вверх по 9 струнам, три раза подряд."""
    import numpy as np
    sr = 44100
    rng = np.random.default_rng(27)

    def pluck(f, d=1.0, damp=0.996):        # струна (алгоритм Карплуса-Стронга)
        n, p = int(sr * d), max(2, int(sr / f))
        buf = rng.uniform(-1, 1, p)
        out = np.zeros(n)
        for i in range(n):
            j = i % p
            out[i] = buf[j]
            buf[j] = damp * 0.5 * (buf[j] + buf[(i + 1) % p])
        return out

    notes = (392, 494, 587, 698, 784, 988, 1175, 1397, 1568)
    strings = [pluck(f) for f in notes]
    gliss = np.zeros(int(sr * 1.6))
    for k, st in enumerate(strings):
        i = int(sr * 0.045 * k)
        n = min(len(st), len(gliss) - i)
        gliss[i:i + n] += 0.45 * st[:n]
    total = np.zeros(int(sr * (0.62 * 2)) + len(gliss))
    for k in range(3):
        i = int(sr * 0.62 * k)
        total[i:i + len(gliss)] += gliss
    return _render(total.tolist())


def custom_sound_path():
    from paths import APP_DIR
    import os
    return os.path.join(APP_DIR, "custom_sound.wav")


def _chime(freqs, note=0.11, gap=0.03, volume=0.45, rate=44100):
    """Короткий сигнал из нескольких нот (WAV в памяти), с плавным началом и концом каждой ноты."""
    import io
    import math
    import struct
    import wave
    frames = bytearray()
    for f in freqs:
        n = int(rate * note)
        for i in range(n):
            env = min(1.0, i / (rate * 0.008), (n - i) / (rate * 0.04))
            v = volume * env * (math.sin(2 * math.pi * f * i / rate) + 0.3 * math.sin(4 * math.pi * f * i / rate))
            frames += struct.pack("<h", int(max(-1, min(1, v / 1.3)) * 32767))
        frames += b"\x00\x00" * int(rate * gap)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(bytes(frames))
    return buf.getvalue()


def beep(kind="alert"):
    """Свой короткий сигнал (не зависит от звуковой схемы Windows, не блокирует):
    "info" — вверх (появилась «Удвоить»), "alert" — вниз (запрещённый мод)."""
    def play():
        try:
            import os
            import winsound
            custom = custom_sound_path()
            if os.path.exists(custom):          # свой звук игрока
                winsound.PlaySound(custom, winsound.SND_FILENAME | winsound.SND_NODEFAULT)
                return
            if kind not in _SOUNDS:
                _SOUNDS[kind] = _harp3() if kind == "info" else _alarm()
            winsound.PlaySound(_SOUNDS[kind], winsound.SND_MEMORY | winsound.SND_NODEFAULT)
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
