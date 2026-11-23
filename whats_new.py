"""Окно «Что нового»: показывает игроку описание патча при первом запуске после обновления."""
import tkinter as tk
from tkinter import ttk

import i18n
import theme as T
from i18n import tr

NOTES = {
    "1.3.1": {
        "title_ru": "Что нового в версии 1.3.1",
        "title_en": "What's New in version 1.3.1",
        "ru": [
            ("🎴 Полное исправление прайсчека и предпросмотра на русском клиенте",
             "• Поддержка всех форм написания карт в Начертанных ультиматумах: множественное число, двоеточия, любые виды кавычек («Доктор», Гадальные карты: Доктор, Гадальные карты “Доктор”, 2x Гадальные карты «...»).\n"
             "• Ультиматумы с картами в награде или жертве теперь безошибочно рассчитывают чистую прибыль и выводят визуальную карточку предпросмотра."),

            ("⚡ Поддержка изменённых предметов Foulborn («Нечестивый...»)",
             "• Чекер теперь различает обычные и Foulborn-уники/валюту (Нечестивый Охотник за головами, Нечестивая Волшебная кровь / Кровь мага, Нечестивая сфера возвышения и др.) и показывает точные цены их изменённых версий с poe.ninja.\n"
             "• Если на рынке нет отдельной цены для Foulborn-версии, автоматически подтягивается цена базового уника."),

            ("🚀 Мгновенная готовность к оценке при старте (28 мс)",
             "Локальный словарь и кэш цен теперь загружаются синхронно при запуске приложения — прайсчек готов к работе с первой миллисекунды без ожидания сетевых запросов и блокировок."),

            ("📖 Словарь русских названий расширен до 8 442 предметов",
             "Синхронизированы абсолютно все гадальные карты и уникальные предметы базы предпросмотра."),

            ("🔄 Автоматическое обновление кэша цен при установке патча",
             "Файл кэша цен в %APPDATA% теперь корректно обновляется у игроков, перешедших со старых версий.")
        ],
        "en": [
            ("🎴 Full Fix for Russian Client Price Check & Inscribed Ultimatum Previews",
             "• Robust handling of plural forms, colons, quotes, and leading counts in Inscribed Ultimatum card rewards/sacrifices (Гадальные карты «...», Гадальная карта: ...).\n"
             "• Cards in Inscribed Ultimatums now accurately compute profit and display the authentic card artwork preview."),

            ("⚡ Support for Foulborn / Mutated Items",
             "• Accurate pricing and preview tooltips for Foulborn uniques and currency (Foulborn Headhunter, Foulborn Mageblood, Foulborn Exalted Orb, etc.) on both English and Russian clients (Нечестивый...).\n"
             "• Graceful fallback to base unique price if a Foulborn variant is not listed separately on poe.ninja."),

            ("🚀 Instant Offline Startup (28 ms)",
             "Dictionaries and price cache are loaded synchronously into memory on launch, ensuring instant price checking without blocking on network requests."),

            ("📖 Russian Translation Dictionary Expanded to 8,442 Items",
             "Full bidirectional synchronization for all divination cards and unique items."),

            ("🔄 Automatic Price Cache Refresh on Update",
             "Automatically overwrites older cached files in %APPDATA% when a newer bundled version is detected.")
        ]
    },
    "1.3.0": {
        "title_ru": "Что нового в версии 1.3.0",
        "title_en": "What's New in version 1.3.0",
        "ru": [
            ("🎴 Встроенный предпросмотр наград Начертанных ультиматумов",
             "При оценке Inscribed Ultimatum у курсора сразу появляется карточка предмета-награды в стиле Path of Exile:\n"
             "• Для гадальных карт — аутентичная карточка (арт, размер стопки, награда, цитата).\n"
             "• Для уникальных предметов — полный тултип с базой, уровнем, свойствами (implicits/explicits) и иконкой.\n"
             "• В настройки добавлен переключатель для включения/выключения карточки награды."),

            ("🖼️ Все картинки вшиты в программу (офлайн)",
             "Все 471 гадальных карт и 1 594 уникальных предметов упакованы прямо в .exe. Картинки отображаются мгновенно и доступны без обращения к интернету."),

            ("💎 Точная оценка камней умений (Gems)",
             "Прайсчекер теперь определяет точный уровень камня (1–21), качество (+0–23%) и осквернение (Corrupted), показывая актуальную цену конкретного варианта."),

            ("⚡ Умный перезапуск без ошибок",
             "Если программа уже была запущена, при открытии нового экземпляра старый процесс завершается автоматически и бесшовно уступает место новому."),

            ("🛡️ Исправление данных и редкости карт",
             "Синхронизированы официальные стопки и полные награды карт (Ценный раритет, Пари полубога, Испытание Хранителя и др.). Все уникальные награды теперь подсвечиваются правильным оранжевым цветом."),

            ("🌐 Полная поддержка русского и английского клиентов",
             "Автоматический перевод названий и описаний под язык клиента игры.")
        ],
        "en": [
            ("🎴 Inscribed Ultimatum Reward Preview",
             "When price checking an Inscribed Ultimatum, an authentic PoE-style preview card appears next to the cursor:\n"
             "• Divination Cards: authentic card artwork, stack size badge, reward text, and flavour quote.\n"
             "• Unique Items: full item tooltip with base, required level, implicits, explicits, and icon.\n"
             "• Settings toggle available to enable or disable the reward preview."),

            ("🖼️ All Images Bundled (Offline)",
             "All 471 divination cards and 1,594 unique items are bundled directly into the executable for instant offline display."),

            ("💎 Accurate Skill & Support Gem Pricing",
             "The price checker now detects gem level (1–21), quality (+0–23%), and corrupted status, returning the exact price for that variant."),

            ("⚡ Seamless Relaunch",
             "If the application is already running, launching it again automatically terminates the old instance and starts the new one."),

            ("🛡️ Card Data & Rarity Corrections",
             "Synchronized official card stack sizes and complete reward text (Costly Curio, Demigod's Wager, Guardian's Challenge, etc.). Unique rewards are now properly colored unique orange."),

            ("🌐 Full Bilingual Support",
             "Seamless adaptation to both Russian and English game clients.")
        ]
    }
}


def show_whats_new(root, version, lang="ru", force=False):
    """Открывает красивое окно с описанием патча."""
    note_data = NOTES.get(version)
    if not note_data and not force:
        return None

    w = tk.Toplevel(root)
    is_ru = (lang == "ru")
    title_text = (note_data.get("title_ru" if is_ru else "title_en")
                  if note_data else (f"Что нового в версии {version}" if is_ru else f"What's New in {version}"))
    w.title(title_text)
    w.geometry("640x580")
    w.minsize(520, 420)
    w.configure(bg=T.BG)
    w.transient(root)
    w.after(50, lambda: T.dark_titlebar(w))

    # Шапка
    head = tk.Frame(w, bg=T.BG, padx=20, pady=16)
    head.pack(fill="x")
    tk.Label(head, text=title_text.upper(), bg=T.BG, fg=T.GOLD_HI,
             font=(T.SERIF, 15, "bold")).pack(anchor="w")
    sub = "Ultimatum Overlay — список изменений" if is_ru else "Ultimatum Overlay — changelog"
    tk.Label(head, text=sub, bg=T.BG, fg=T.MUTED, font=(T.SANS, 9)).pack(anchor="w", pady=(2, 0))
    tk.Frame(w, bg=T.GOLD, height=1).pack(fill="x", padx=20)

    # Список изменений (скроллируемый)
    mid = tk.Frame(w, bg=T.BG, padx=20, pady=12)
    mid.pack(fill="both", expand=True)

    cv = tk.Canvas(mid, bg=T.BG, highlightthickness=0)
    sb = ttk.Scrollbar(mid, orient="vertical", command=cv.yview)
    cv.configure(yscrollcommand=sb.set)

    content = tk.Frame(cv, bg=T.BG)
    win_id = cv.create_window((0, 0), window=content, anchor="nw")

    def _on_configure(event):
        cv.configure(scrollregion=cv.bbox("all"))
        cv.itemconfig(win_id, width=event.width)

    cv.bind("<Configure>", _on_configure)
    cv.pack(side="left", fill="both", expand=True)
    sb.pack(side="right", fill="y")

    # Колесико мыши
    def _on_mousewheel(event):
        cv.yview_scroll(int(-1 * (event.delta / 120)), "units")
    cv.bind_all("<MouseWheel>", _on_mousewheel)

    items = note_data.get("ru" if is_ru else "en", []) if note_data else []
    for h_txt, b_txt in items:
        o, c = T.card(content, None, pad=10)
        o.pack(fill="x", pady=(0, 10))
        tk.Label(c, text=h_txt, bg=T.CARD, fg=T.GOLD, font=(T.SERIF, 11, "bold"),
                 anchor="w", justify="left").pack(fill="x", anchor="w")
        tk.Label(c, text=b_txt, bg=T.CARD, fg=T.TXT, font=(T.SANS, 9),
                 anchor="w", justify="left").pack(fill="x", anchor="w", pady=(4, 0))

    # Подвал с кнопкой
    def _close():
        try:
            cv.unbind_all("<MouseWheel>")
        except Exception:
            pass
        w.destroy()

    w.protocol("WM_DELETE_WINDOW", _close)

    foot = tk.Frame(w, bg=T.BG, padx=20, pady=14)
    foot.pack(fill="x")
    btn_txt = "Отлично, понятно!" if is_ru else "Got it!"
    T.button(foot, btn_txt, _close, fg=T.BG, bg=T.GOLD, hover=T.GOLD_HI).pack(side="right")

    return w
