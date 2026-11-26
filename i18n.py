"""Тексты интерфейса на русском и английском. tr("ключ", **параметры)."""

LANG = "ru"

S = {
    # шапка и подвал
    "subtitle": ("OVERLAY", "OVERLAY"),
    "prices_loading": ("цены загружаются…", "loading prices…"),
    "prices_info": ("{league}  ·  1 div = {div} c  ·  {n} предметов", "{league}  ·  1 div = {div} c  ·  {n} items"),
    "made_by": ("made by", "made by"),
    "support": ("Поддержать", "Support"),
    "whats_new_link": ("Что нового", "What's new"),
    # прайсчек
    "pc_title": ("Прайсчек", "Price check"),
    "pc_hint": ("Наведи на предмет в игре и нажми Ctrl+C — рядом с курсором появится цена.",
                "Hover an item in game and press Ctrl+C — its price appears next to the cursor."),
    "league": ("Лига", "League"),
    "refresh": ("Обновить", "Refresh"),
    "price_list": ("Список цен", "Price list"),
    "gold_from": ("Золотая цена от, div", "Gold price from, div"),
    "show_sec": ("Показывать, сек", "Show for, sec"),
    # подсказка модов
    "mods_title": ("Подсказка модов", "Modifier hints"),
    "on": ("включена", "on"),
    "off": ("выключена", "off"),
    "mode": ("Режим", "Mode"),
    "mode_auto": ("Авто (по иконкам)", "Auto (by icons)"),
    "mode_13": ("13 волн (мод выдают)", "13 waves (mod is given)"),
    "mode_10": ("10 волн (выбираешь сам)", "10 waves (you choose)"),
    "dd_toggle": ("Рамка вокруг «Удвоить»", "Double Down highlight"),
    "dd_chip": ("УДВОИТЬ", "DOUBLE DOWN"),
    "fine": ("Тонкая настройка", "Fine tuning"),
    "sat": ("Порог цвета", "Colour threshold"),
    "match": ("Похожесть", "Similarity"),
    "shift": ("Сдвиг", "Offset"),
    # список модов
    "mods_list": ("Усложнения", "Modifiers"),
    "allowed_n": ("разрешено {a} из {n}", "{a} of {n} allowed"),
    "reset_tier": ("Сбросить", "Reset"),
    "mods_hint": ("Нажми на строку — можно / нельзя. Внутри тира сверху самые простые; "
                  "оверлей советует самый верхний разрешённый.",
                  "Click a row to allow / forbid. Within a tier the easiest are on top; "
                  "the overlay suggests the topmost allowed one."),
    "allow": ("МОЖНО", "ALLOW"),
    "forbid": ("НЕЛЬЗЯ", "FORBID"),
    "tier_reset_done": ("Восстановлен тир-лист: {n} модов", "Tier list restored: {n} modifiers"),
    "tier_reset_err": ("Не удалось восстановить тир-лист: {e}", "Could not restore tier list: {e}"),
    # лог
    "last_prices": ("Последние цены", "Recent prices"),
    "custom_saved": ("Своя цена сохранена — оверлей считает по ней", "Custom price saved — the overlay uses it"),
    "error": ("Ошибка: {e}", "Error: {e}"),
    "prices_err": ("Цены: ошибка {e}", "Prices: error {e}"),
    # оверлей
    "chip_take": ("БРАТЬ", "TAKE"),
    "chip_ok": ("МОЖНО", "OK"),
    "chip_no": ("НЕЛЬЗЯ", "NO"),
    "chip_unknown": ("НЕ ЗНАЮ", "UNKNOWN"),
    "your_price": ("✎  твоя цена", "✎  your price"),
    "low_data": ("?  неточные данные (мало сделок на рынке)", "?  approximate data (few market trades)"),
    "low_data_short": ("неточные данные", "approximate"),
    "net_profit": ("чистая прибыль", "net profit"),
    "poe_found": ("● PoE найден", "● PoE found"),
    "poe_missing": ("● PoE не найден", "● PoE not found"),
    "copy": ("Копировать", "Copy"),
    "own_sound": ("Свой звук…", "Custom sound…"),
    "std_sound": ("Стандартный", "Default"),
    "sound_pick": ("Выбери звук (WAV)", "Pick a sound (WAV)"),
    "sound_set": ("Свой звук установлен: {n}", "Custom sound set: {n}"),
    "sound_bad": ("Не удалось открыть звук — нужен WAV-файл (PCM)", "Could not open the sound — a WAV (PCM) file is needed"),
    "sound_reset": ("Звук — стандартный", "Sound — default"),
    "key_bad": ("Нужна клавиша с Ctrl, Alt или Shift (и не Ctrl+C / V / X / A / Z)",
                "Use a key with Ctrl, Alt or Shift (and not Ctrl+C / V / X / A / Z)"),
    "key_bad_scan": ("Выбери клавишу или Mouse3/4/5 (не Esc/Пробел/Enter и не Ctrl+C/V/X/A/Z)",
                     "Pick a key or Mouse3/4/5 (not Esc/Space/Enter or Ctrl+C/V/X/A/Z)"),
    "already_running": ("Ultimatum overlay уже запущен — его значок в трее (возле часов).",
                        "Ultimatum overlay is already running — its icon is in the tray (near the clock)."),
    "paste": ("Вставить", "Paste"),
    "copied": ("Галочки модов скопированы — отправь этот текст другу, он нажмёт «Вставить»",
               "Modifier settings copied — send the text to a friend, they press “Paste”"),
    "pasted": ("Галочки применены: {n} модов", "Settings applied: {n} modifiers"),
    "pasted_missing": (" (не нашлось у тебя: {m})", " (not in your list: {m})"),
    "paste_bad": ("В буфере обмена нет кода — сначала скопируй код, который тебе прислали",
                  "No code in the clipboard — copy the code you were sent first"),
    "autostart": ("Запускать вместе с Windows (свёрнутым в трей)", "Start with Windows (minimised to tray)"),
    "autostart_exe_only": ("Автозапуск работает только в собранном exe", "Autostart works only in the built exe"),
    "tray_open": ("Открыть", "Open"),
    "tray_toggle": ("Скрыть / показать оверлей", "Hide / show overlay"),
    "tray_quit": ("Выход", "Quit"),
    "tray_hint": ("Программа свёрнута в трей и продолжает работать. Выход — правой кнопкой по значку в трее.",
                  "The program is minimised to the tray and keeps working. Quit — right-click the tray icon."),
    "updating": ("Обновляю до версии {v}…", "Updating to version {v}…"),
    "update_err": ("Не удалось обновиться: {e}", "Update failed: {e}"),
    "update_staged": ("Доступно обновление v{v} — установится при следующем запуске (или нажми кнопку вверху)",
                      "Update v{v} ready — installs on next launch (or click button above)"),
    "update_badge": ("⬆ Обновить до v{v}", "⬆ Update to v{v}"),
    "poe_admin_warn": ("⚠ PoE от Админа — перезапусти оверлей от Администратора",
                       "⚠ PoE runs as Admin — restart overlay as Administrator"),
    "base_short": ("база", "base"),
    "item_fallback": ("Предмет", "Item"),
    "unidentified_unique": ("неопознанный уник (база: {base})", "unidentified unique (base: {base})"),
    "up_to": ("до {c}c", "up to {c}c"),
    "ult_special_mirror": ("Зеркалит редкий предмет (цена зависит от вещи)", "Mirrors Rare Item (value depends on item)"),
    "ult_special_rare": ("Обмен редкого предмета", "Rare item exchange"),
    "help_title": ("Как пользоваться", "How to use"),
    "help": ((
        "1. Игру нужно запустить в оконном режиме или «оконном без рамки» (Windowed Fullscreen). "
        "В полноэкранном режиме оверлей поверх игры не виден. Вверху окна программы видно, нашла ли она игру.\n\n"
        "2. Цена предмета: наведи на него курсор в игре и нажми Ctrl+C — рядом появится карточка с ценой "
        "poe.ninja. Если копирует другой прайсчекер (Ctrl+D и т. п.), карточка не появится.\n\n"
        "3. Моды ультиматума: в списке «Усложнения» нажми на строку, чтобы разрешить или запретить мод. "
        "Когда в игре откроется алтарь ультиматума, нажми F2 (клавишу или боковую кнопку мыши можно сменить в настройках) — "
        "оверлей разово обведёт самый простой разрешённый мод («БРАТЬ» / «МОЖНО») или запрещённый («НЕЛЬЗЯ»). Клавиша "
        "работает только внутри игры и не мешает в других программах Windows. Подсказка исчезает сама через 3.5 сек, "
        "сразу по Esc/Пробелу, а повторное нажатие F2 заново сканирует открытый алтарь.\n\n"
        "4. Ctrl+Shift+H — скрыть / показать оверлей (клавишу можно сменить). Крестик окна сворачивает "
        "программу в трей, выход — через значок в трее."
    ), (
        "1. Run the game in Windowed or Windowed Fullscreen mode. In exclusive Fullscreen the overlay is not "
        "visible over the game. The top of the program window shows whether the game was found.\n\n"
        "2. Item price: hover an item in game and press Ctrl+C — a price card from poe.ninja appears next to "
        "it. If another price checker copies the item (Ctrl+D etc.), the card does not appear.\n\n"
        "3. Ultimatum modifiers: click a row in the “Modifiers” list to allow or forbid it. When the Ultimatum "
        "altar opens in game, press F2 (the hotkey or mouse button can be customized) — the overlay circles the easiest "
        "allowed modifier (“TAKE” / “OK”) or a forbidden one (“NO”). The hotkey only triggers inside PoE and never "
        "blocks F2 in other Windows apps. Hints auto-hide after 3.5 sec or immediately on Esc/Space; pressing F2 again "
        "rescans an open altar.\n\n"
        "4. Ctrl+Shift+H — hide / show the overlay (the key can be changed). The window close button minimises "
        "the program to the tray; quit via the tray icon."
    )),
    "overlay_card": ("Оверлей", "Overlay"),
    "hide_key": ("Скрыть / показать", "Hide / show"),
    "scan_key": ("Скан ультиматума", "Scan Ultimatum"),
    "scan_safe_badge": ("(100% по правилам GGG)", "(100% GGG Safe)"),
    "mod_seconds_lbl": ("Время показа", "Display duration"),
    "dur_2_5": ("2.5 сек", "2.5 sec"),
    "dur_3_5": ("3.5 сек (реком.)", "3.5 sec (recom.)"),
    "dur_5": ("5.0 сек", "5.0 sec"),
    "panel_not_found": ("Окно алтаря ультиматума не найдено на экране", "Ultimatum altar window not found on screen"),
    "press_key": ("нажми клавишу…", "press a key…"),
    "key_busy": ("Клавиша {k} занята другой программой — назначь другую", "Key {k} is taken by another program — pick another one"),
    "key_hint": ("Нажми на кнопку и затем нужную клавишу или Mouse3/4/5 (можно с Ctrl/Shift/Alt). Esc — отмена.",
                 "Click the button, then press a key or Mouse3/4/5 (Ctrl/Shift/Alt allowed). Esc cancels."),
    "overlay_hidden": ("скрыт", "hidden"),
    "overlay_shown": ("показан", "shown"),
    "sound": ("Звук на «Удвоить»", "Sound on Double Down"),
    "life_toggle": ("Метка здоровья монстров у Начертанных", "Monster Life tag on Inscribed"),
    "show_reward_preview": ("Карточка награды ультиматума (уники и карты)", "Ultimatum reward preview (uniques & cards)"),
    "req_level": ("Требуется Уровень", "Requires Level"),
    "sacrifice_label": ("Жертва", "Sacrifice"),
    "reward_label": ("Награда", "Reward"),
    "league_switched": ("Лига «{old}» закончилась — переключаюсь на «{new}»", "League “{old}” has ended — switching to “{new}”"),
    "monster_life": ("{p}% больше здоровья монстров", "{p}% more Monster Life"),
    "own_short": ("своя цена", "custom price"),
    "still_loading": ("цены ещё загружаются", "prices are still loading"),
    "unknown_mod": ("неизвестный", "unknown"),
    "st_10_take": ("10 волн: брать #{i} ({name})", "10 waves: take #{i} ({name})"),
    "st_10_none": ("10 волн: все три запрещены", "10 waves: all three are forbidden"),
    "st_13_ok": ("13 волн: выданный мод разрешён — {names}", "13 waves: the given mod is allowed — {names}"),
    "st_13_no": ("13 волн: выданный мод запрещён — {names}", "13 waves: the given mod is forbidden — {names}"),
    # цены (prices.py)
    "no_price": ("нет цены для «{name}»", "no price for “{name}”"),
    "no_reward_price": ("награду «{name}» оценить не могу", "can't price reward “{name}”"),
    "ninja_err": ("poe.ninja {t}: ошибка {e}", "poe.ninja {t}: error {e}"),
    "ninja_empty": ("poe.ninja не вернул цены — проверь название лиги", "poe.ninja returned no prices — check the league name"),
    "prices_updated": ("Цены обновлены: {n} предметов, 1 div = {div} c", "Prices updated: {n} items, 1 div = {div} c"),
    "prices_stale": ("Не удалось обновить цены ({e}) — использую сохранённые, им {h} ч",
                     "Could not update prices ({e}) — using saved ones, {h} h old"),
    "ru_loaded": ("Русские названия загружены: {n}", "Russian names loaded: {n}"),
    "ru_err": ("Не удалось загрузить русские названия: {e}", "Could not load Russian names: {e}"),
    # окно цен
    "pw_title": ("Цены", "Prices"),
    "tab_all": ("Все", "All"),
    "tab_low": ("Мало данных", "Little data"),
    "tab_mine": ("Свои", "Custom"),
    "search": ("Поиск", "Search"),
    "item_names": ("Названия", "Names"),
    "hint_all": ("Все цены poe.ninja для лиги. Свою цену можно задать любому предмету.",
                 "All poe.ninja prices for the league. You can set a custom price for any item."),
    "hint_low": ("Цены по малому числу сделок (меньше 3 продаж за день или 5 объявлений) — на них могут быть "
                 "выбросы. Если знаешь реальную цену, впиши свою: она заменит poe.ninja и в оверлее.",
                 "Prices based on few trades (under 3 sales a day or 5 listings) — they may be outliers. "
                 "If you know the real price, enter your own: it replaces poe.ninja in the overlay too."),
    "hint_mine": ("Цены, которые ты вписал сам. Они важнее poe.ninja и сохраняются между запусками.",
                  "Prices you entered yourself. They override poe.ninja and are kept between launches."),
    "col_item": ("Предмет", "Item"),
    "col_cat": ("Раздел", "Category"),
    "col_ninja": ("poe.ninja, c", "poe.ninja, c"),
    "col_mine": ("Своя, c", "Custom, c"),
    "pick_item": ("Выбери предмет в списке", "Pick an item in the list"),
    "own_price": ("Своя цена", "Custom price"),
    "own_hint": ("в хаосах, или «2div»", "in chaos, or “2div”"),
    "save": ("Сохранить", "Save"),
    "remove_own": ("Убрать свою", "Remove custom"),
    "bad_price": ("Не понял цену. Примеры: 150, 150c, 2div, 1.5d", "Can't read the price. Examples: 150, 150c, 2div, 1.5d"),
    "saved_price": ("Сохранено: {c} c — оверлей будет считать по ней", "Saved: {c} c — the overlay will use it"),
    "removed_price": ("Своя цена убрана — снова poe.ninja", "Custom price removed — back to poe.ninja"),
    "not_on_ninja": ("На poe.ninja этого предмета нет", "This item is not on poe.ninja"),
}

CATS = {
    # General
    "Currency": ("Валюта", "Currency"), "Fragment": ("Фрагменты", "Fragments"),
    "Runegraft": ("Рунограммы", "Runegrafts"), "AllflameEmber": ("Угли Всепламени", "Allflame Embers"),
    "Tattoo": ("Татуировки", "Tattoos"), "Omen": ("Знамения", "Omens"),
    "DjinnCoin": ("Монеты джиннов", "Djinn Coins"), "Ducat": ("Дукаты", "Ducats"),
    "EnshroudingCrystal": ("Затуманивающие кристаллы", "Enshrouding Crystals"),
    "DivinationCard": ("Гадальные карты", "Divination cards"), "Artifact": ("Артефакты", "Artifacts"),
    "Oil": ("Масла", "Oils"), "Incubator": ("Инкубаторы", "Incubators"),
    "Wombgift": ("Дары утробы", "Wombgifts"), "Corpse": ("Трупы", "Corpses"),
    "Viscera": ("Внутренности", "Viscera"),

    # Equipment & Gems
    "UniqueWeapon": ("Уник. оружие", "Unique weapons"), "UniqueArmour": ("Уник. броня", "Unique armour"),
    "UniqueAccessory": ("Уник. бижутерия", "Unique accessories"), "UniqueFlask": ("Уник. флаконы", "Unique flasks"),
    "UniqueJewel": ("Уник. самоцветы", "Unique jewels"), "ForbiddenJewel": ("Запретные самоцветы", "Forbidden jewels"),
    "ShrineBelt": ("Пояса святилища", "Shrine belts"), "UniqueTincture": ("Уник. настойки", "Unique tinctures"),
    "UniqueRelic": ("Уник. реликвии", "Unique relics"), "SkillGem": ("Камни умений", "Skill gems"),
    "ImbuedGem": ("Насыщенные камни", "Imbued gems"), "ClusterJewel": ("Кластерные самоцветы", "Cluster jewels"),

    # Atlas
    "Map": ("Карты", "Maps"), "BlightedMap": ("Заражённые карты", "Blighted maps"),
    "BlightRavagedMap": ("Разорённые карты", "Blight-ravaged maps"), "UniqueMap": ("Уник. карты", "Unique maps"),
    "ValdoMap": ("Карты Валдо", "Valdo maps"), "DeliriumOrb": ("Сферы Делириума", "Delirium orbs"),
    "Invitation": ("Приглашения", "Invitations"), "Scarab": ("Скарабеи", "Scarabs"),
    "Astrolabe": ("Астролябии", "Astrolabes"), "Thread": ("Нити", "Threads"),
    "Memory": ("Воспоминания", "Memories"), "IncursionTemple": ("Храмы Ацоатль", "Incursion temples"),
    "ScryingOrb": ("Сферы гадания", "Scrying orbs"),

    # Crafting
    "BaseType": ("Базовые предметы", "Base types"), "Flask": ("Флаконы", "Flasks"),
    "Fossil": ("Ископаемые", "Fossils"), "Resonator": ("Резонаторы", "Resonators"),
    "Beast": ("Звери", "Beasts"), "Essence": ("Сущности", "Essences"),
    "Vial": ("Флаконы жертвоприношения", "Vials"),
}


TIERS = {"Free": ("Не мешает", "Free"), "Easy": ("Легко", "Easy"), "Moderate": ("Средне", "Moderate"),
         "Annoying": ("Неприятно", "Annoying"), "DO NOT TAKE": ("НЕ БРАТЬ", "DO NOT TAKE"),
         "Exception": ("Исключения", "Exception"), "Mirage": ("Мираж", "Mirage")}


def tier(name):
    pair = TIERS.get(name)
    return name if pair is None else pair[1 if LANG == "en" else 0]


def set_lang(lang):
    global LANG
    LANG = "en" if lang == "en" else "ru"


class Msg(str):
    """Переведённая строка, которая помнит, что это за сообщение — чтобы при смене языка
    уже показанный текст (например, в «Последних ценах») можно было перевести заново."""
    def __new__(cls, text, key, kw):
        obj = super().__new__(cls, text)
        obj.key, obj.kw = key, kw
        return obj


def tr(key, **kw):
    pair = S.get(key)
    if pair is None:
        return key
    text = pair[1 if LANG == "en" else 0]
    return Msg(text.format(**kw) if kw else text, key, kw)


def retr(text):
    """Перевести на текущий язык строку, полученную раньше через tr()."""
    return tr(text.key, **text.kw) if isinstance(text, Msg) else text


def cat(name):
    pair = CATS.get(name)
    return "—" if pair is None else pair[1 if LANG == "en" else 0]
