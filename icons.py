"""Библиотека иконок усложнений: нарезка тир-листа, распознавание иконок из игры."""
import json
import os

import cv2
import numpy as np

from paths import APP_DIR as HERE
ICON_DIR = os.path.join(HERE, "icons")
LIB_FILE = os.path.join(ICON_DIR, "library.json")
N = 64  # все иконки приводятся к 64x64

TIERS = ["Free", "Easy", "Moderate", "Annoying", "DO NOT TAKE", "Exception"]
DEFAULT_ALLOWED = {"Free", "Easy", "Moderate", "Annoying"}


def imread(path):
    data = np.fromfile(path, dtype=np.uint8)  # работает с кириллицей в пути
    return cv2.imdecode(data, cv2.IMREAD_COLOR)


def imwrite(path, img):
    ok, buf = cv2.imencode(os.path.splitext(path)[1] or ".png", img)
    if ok:
        buf.tofile(path)


def norm(img):
    return cv2.resize(img, (N, N), interpolation=cv2.INTER_AREA)


def disc_mask(size, frac):
    m = np.zeros((size, size), np.uint8)
    cv2.circle(m, (size // 2, size // 2), int(size * frac / 2), 255, -1)
    return m


def saturation(img):
    """Средняя насыщенность внутренней части иконки (серые = недоступные)."""
    im = norm(img)
    hsv = cv2.cvtColor(im, cv2.COLOR_BGR2HSV)
    return float(cv2.mean(hsv[:, :, 1], mask=disc_mask(N, 0.65))[0])


# ---------------- библиотека ----------------
def _read_library():
    with open(LIB_FILE, encoding="utf-8") as f:
        lib = json.load(f)
    out = []
    for e in lib:
        if isinstance(e, dict) and e.get("file") and e.get("tier"):
            e["img"] = imread(os.path.join(ICON_DIR, e["file"]))
            if e["img"] is not None:
                e.setdefault("allowed", False)
                out.append(e)
    return out


def load_library():
    """Список модов. Первый запуск или испорченный файл — берём тир-лист, зашитый в программу."""
    from paths import restore_default_icons
    if os.path.exists(LIB_FILE):
        try:
            lib = _read_library()
            if lib:
                return lib
        except Exception:
            pass
    try:
        restore_default_icons(ICON_DIR)
        return _read_library()
    except Exception:
        return []


def save_library(lib):
    from paths import write_json
    write_json(LIB_FILE, [{k: v for k, v in e.items() if k != "img"} for e in lib], indent=1)


def add_icon(lib, img, tier="Mirage", allowed=False, name=""):
    os.makedirs(ICON_DIR, exist_ok=True)
    n = 1
    while os.path.exists(os.path.join(ICON_DIR, f"icon_{n:03d}.png")):
        n += 1
    fn = f"icon_{n:03d}.png"
    im = norm(img)
    imwrite(os.path.join(ICON_DIR, fn), im)
    e = {"id": fn[:-4], "file": fn, "name": name, "tier": tier, "allowed": allowed, "img": im}
    lib.append(e)
    return e


# ---------------- нарезка тир-листа ----------------
def slice_tierlist(path):
    """Возвращает [(tier, icon_bgr), ...] в порядке тир-листа (слева направо, сверху вниз)."""
    img = imread(path)
    if img is None:
        raise ValueError("Не удалось открыть картинку")
    H, W = img.shape[:2]
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # 1) полосы тиров по цвету левой колонки с подписями
    col = img[:, max(2, W // 100)].astype(int)
    bands, start = [], 0
    for y in range(1, H):
        if np.abs(col[y] - col[y - 1]).sum() > 60:
            if y - start > H * 0.05:
                bands.append((start, y))
            start = y
    if H - start > H * 0.05:
        bands.append((start, H))
    # тонкие разделители уже отфильтрованы; лишние полосы (если есть) отрезаем
    bands = bands[: len(TIERS)]

    # 2) правая граница колонки подписей: первая тёмная колонка
    row = img[bands[0][0] + (bands[0][1] - bands[0][0]) // 2]
    label_end = next((x for x in range(W) if row[x].mean() < 50), W // 10)

    # 3) иконки — круги
    min_band = min(b - a for a, b in bands)
    r_est = min_band * 0.46
    circles = cv2.HoughCircles(
        cv2.medianBlur(gray, 5), cv2.HOUGH_GRADIENT, dp=1, minDist=r_est * 1.6,
        param1=100, param2=22, minRadius=int(r_est * 0.8), maxRadius=int(r_est * 1.15))
    if circles is None:
        raise ValueError("Не нашёл иконки на картинке")
    res = []
    r_med = float(np.median(circles[0][:, 2]))
    h = int(r_med)
    pad = h + 2  # иконки у самого края картинки не должны теряться
    big = cv2.copyMakeBorder(img, pad, pad, pad, pad, cv2.BORDER_REPLICATE)
    for x, y, r in circles[0]:
        if x < label_end:
            continue
        band = next((i for i, (a, b) in enumerate(bands) if a <= y < b), None)
        if band is None:
            continue
        x1, y1 = int(x - h) + pad, int(y - h) + pad
        res.append((band, y, x, big[y1:y1 + 2 * h, x1:x1 + 2 * h].copy()))
    # сортировка: тир, потом строка внутри тира, потом x
    row_h = r_med * 2
    res.sort(key=lambda t: (t[0], round(t[1] / row_h), t[2]))
    return [(TIERS[b] if b < len(TIERS) else f"Tier{b+1}", ic) for b, _, _, ic in res]


def build_library_from_tierlist(path):
    import shutil
    if os.path.isdir(ICON_DIR):
        shutil.rmtree(ICON_DIR)
    lib = []
    for tier, ic in slice_tierlist(path):
        add_icon(lib, ic, tier=tier, allowed=tier in DEFAULT_ALLOWED)
    save_library(lib)
    return lib


# ---------------- распознавание ----------------
def _score(game, tpl, use_color):
    g = norm(game)
    t = norm(tpl)
    # шаблон — центр иконки без золотой рамки, ищем со сдвигом ±7 px
    tc = t[14:50, 14:50]
    gc = g[7:57, 7:57]
    if not use_color:
        tc = cv2.cvtColor(tc, cv2.COLOR_BGR2GRAY)
        gc = cv2.cvtColor(gc, cv2.COLOR_BGR2GRAY)
        return float(cv2.matchTemplate(gc, tc, cv2.TM_CCOEFF_NORMED).max())
    shape = float(cv2.matchTemplate(gc, tc, cv2.TM_CCOEFF_NORMED).max())
    # оттенок: у некоторых модов одна картинка разного цвета (Restless Ground: коричневая / синяя)
    return 0.75 * shape + 0.25 * _hue_sim(g, t)


def _hue_hist(img):
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    m = disc_mask(N, 0.65) & ((hsv[:, :, 1] > 60) & (hsv[:, :, 2] > 40)).astype(np.uint8) * 255
    h = cv2.calcHist([hsv], [0], m, [18], [0, 180])
    return cv2.normalize(h, h).flatten()


def _hue_sim(a, b):
    ha, hb = _hue_hist(a), _hue_hist(b)
    if not ha.any() or not hb.any():
        return 0.5
    return max(0.0, float(cv2.compareHist(ha, hb, cv2.HISTCMP_CORREL)))


def identify(game_icon, lib, colored=True):
    """-> (entry или None, score). Сравниваем с каждой иконкой библиотеки."""
    best, best_s = None, -1.0
    for e in lib:
        s = _score(game_icon, e["img"], use_color=colored)
        if s > best_s:
            best, best_s = e, s
    return best, best_s
