"""Обмен галочками модов: короткий код в буфере обмена.
Моды записываются по английским названиям, поэтому код из русской программы подходит и к английской."""
import base64
import json
import zlib

PREFIX = "ULTOV1:"
TIERS = ["Free", "Easy", "Moderate", "Annoying", "DO NOT TAKE", "Exception", "Mirage"]


def export_code(lib):
    """Список модов -> код: порядок, тир и галочка каждого мода с известным названием."""
    rows = [[e["name_en"], TIERS.index(e["tier"]) if e["tier"] in TIERS else 6, int(bool(e["allowed"]))]
            for e in lib if e.get("name_en")]
    raw = json.dumps(rows, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return PREFIX + base64.urlsafe_b64encode(zlib.compress(raw, 9)).decode("ascii")


def import_code(lib, code):
    """Применить код к своему списку. -> (сколько модов применено, сколько из кода не нашлось) или ошибка ValueError.
    Моды, которых нет в коде, остаются как были и встают в конец своего тира."""
    code = (code or "").strip()
    if not code.startswith(PREFIX):
        raise ValueError("not a code")
    try:
        rows = json.loads(zlib.decompress(base64.urlsafe_b64decode(code[len(PREFIX):].encode("ascii"))))
        rows = [(str(n), int(t), int(a)) for n, t, a in rows]
    except Exception:
        raise ValueError("broken code")
    # одинаковые названия (Stormcaller Runes в двух тирах) различаем по порядку появления
    by_name = {}
    for e in lib:
        if e.get("name_en"):
            by_name.setdefault(e["name_en"], []).append(e)
    applied, missing = [], 0
    for name, tier_i, allowed in rows:
        lst = by_name.get(name)
        if not lst:
            missing += 1
            continue
        e = lst.pop(0)
        e["tier"] = TIERS[tier_i] if 0 <= tier_i < len(TIERS) else e["tier"]
        e["allowed"] = bool(allowed)
        applied.append(e)
    # порядок: как в коде; моды не из кода — после, в своём тире
    order = {id(e): i for i, e in enumerate(applied)}
    tier_pos = {t: i for i, t in enumerate(TIERS)}
    lib.sort(key=lambda e: (tier_pos.get(e["tier"], 99), order.get(id(e), 10 ** 6)))
    return len(applied), missing
