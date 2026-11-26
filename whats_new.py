"""Окно «Что нового»: показывает игроку описание патча при первом запуске после обновления."""
import tkinter as tk
from tkinter import ttk

import i18n
import theme as T
from i18n import tr

NOTES = {
    "1.4.3": {
        "title_ru": "Что нового в версии 1.4.3",
        "title_en": "What's New in version 1.4.3",
        "ru": [
            ("🛡️ Пассивный F2 (без блокировки в Windows) и мышь Mouse4/Mouse5",
             "• Клавиша сканирования (по умолчанию F2) больше не перехватывается глобально — она свободно работает в Проводнике, Excel и браузере, а оверлей срабатывает только внутри окна PoE.\n"
             "• Добавлена поддержка боковых кнопок мыши (Mouse3 / Mouse4 / Mouse5) и одиночных клавиш для скана.\n"
             "• Предупреждение в шапке, если PoE запущен от имени Администратора, а оверлей — нет."),

            ("💎 Точная оценка Voices, Forbidden Flesh/Flame, Mageblood и камней",
             "• Прайсчекер теперь различает количество малых пассивок на Voices (1 / 3 / 5 / 7), нотаблы на Forbidden Flesh / Forbidden Flame (на RU и EN) и число флаконов на Mageblood.\n"
             "• Многовариантные предметы без точного варианта помечаются как неточные с указанием разброса цен («до …c»), а неопознанные уники больше не оцениваются как белая база.\n"
             "• Исправлен прайсчек русских Пробуждённых камней («Пробуждённый: Наставник» и др.)."),

            ("🔥 Начертанные ультиматумы, 10 волн, звук и автообновление",
             "• Исправлена плашка «На X% больше здоровья монстров» в русском клиенте и разделены цвета тиров (30% / 70% / 120% / 200%).\n"
             "• Цена и прибыль перенесены в верхнюю часть карточки предпросмотра — больше не обрезаются на длинных униках.\n"
             "• В режиме «10 волн» оверлей больше не советует неактивные (серые) моды, а при запрещённом моде звучит сигнал тревоги.\n"
             "• Автообновление больше не перезапускает программу посреди боя: скачивается тихо и устанавливается при следующем запуске (или по кнопке вверху).\n"
             "• Картинки предпросмотра упакованы в единый ZIP-архив для ускорения старта .exe.")
        ],
        "en": [
            ("🛡️ Passive F2 (No Global Block) & Mouse4/Mouse5 Support",
             "• The scan hotkey (default F2) is no longer swallowed globally — it works normally in Explorer, Excel, and browsers, triggering only when PoE is focused.\n"
             "• Added support for Mouse3 / Mouse4 / Mouse5 and standalone keys for altar scanning.\n"
             "• Header warning when PoE is running as Administrator while the overlay is not."),

            ("💎 Exact Pricing for Voices, Forbidden Flesh/Flame, Mageblood & Gems",
             "• Distinguishes Voices passive counts (1 / 3 / 5 / 7), Forbidden Flesh / Forbidden Flame notables (EN & RU), and Mageblood flask counts.\n"
             "• Multi-variant items without a specific variant are flagged as approximate with a price range ('up to …c'), and unidentified uniques are no longer priced as white bases.\n"
             "• Fixed Russian Awakened gem lookups and fallback gem levels."),

            ("🔥 Inscribed Ultimatums, 10-Wave Logic, Sound & Safe Updates",
             "• Fixed '% more Monster Life' detection on the Russian client ('На X% больше здоровья монстров') with 4-tier color coding (30% / 70% / 120% / 200%).\n"
             "• Price & net profit moved to the top of preview cards so they never clip on tall unique tooltips.\n"
             "• 10-wave advisor ignores greyed-out unavailable modifiers and plays the alert sound on forbidden modifiers.\n"
             "• Auto-updates no longer restart mid-combat: updates stage silently and apply on next launch (or via the header button).\n"
             "• Preview images are bundled in a single ZIP archive for faster .exe startup.")
        ]
    },
    "1.4.2": {
        "title_ru": "Что нового в версии 1.4.2",
        "title_en": "What's New in version 1.4.2",
        "ru": [
            ("🔧 Критический фикс автообновления (ошибка python313.dll)",
             "• Устранена причина вылета после автообновления («Не найден указанный модуль Temp\\_MEI...\\python313.dll»): новый процесс больше не наследует старую временную папку PyInstaller.\n"
             "• Исправлен редкий двойной запуск проверки обновлений при старте программы."),

            ("⚔️ Исправлено распознавание алтаря на 1-й волне Ультиматума",
             "• Теперь нажатие F2 корректно находит алтарь уже на самой первой волне (до начала испытания, когда ещё нет кнопок «Забрать награды» и «ИЛИ»).\n"
             "• Повторное нажатие F2 всегда заново сканирует алтарь (удобно, если случайно закрыли иконку всплывающей подсказкой или перешли к следующей волне)."),

            ("💰 Улучшения прайсчека, мультимониторов и интерфейса",
             "• Поддержка осквернённых/шестисвязных префиксов в Начертанных ультиматумах и поиск с «ё»/«е» в списке цен.\n"
             "• Корректная работа оверлея на втором мониторе слева/сверху от основного и адаптация размера окна под ноутбуки (720p/125% DPI).\n"
             "• Разрешена привязка клавиш NumPad (Num0–Num9) для сканирования без модификаторов.")
        ],
        "en": [
            ("🔧 Critical Auto-Update Fix (python313.dll Missing Module)",
             "• Fixed the crash after auto-updating where the restarted exe inherited the old PyInstaller _MEI temp directory.\n"
             "• Fixed duplicate startup update check threads racing on the downloaded binary."),

            ("⚔️ Fixed Ultimatum Altar Detection on Wave 1 (Before Starting Trial)",
             "• Pressing F2 now properly detects the Ultimatum altar on Wave 1 before any rewards exist (when 'Take Rewards' and 'OR' are not yet shown).\n"
             "• Pressing F2 again always triggers a fresh scan cleanly."),

            ("💰 Price Check, Multi-Monitor & UI Improvements",
             "• Support for Corrupted/Two-Implicit/6-Linked prefixes in Inscribed Ultimatums and Russian ё/е search fallback.\n"
             "• Fixed overlay geometry on secondary monitors with negative coordinates and adapted main window sizing for 720p/DPI-scaled screens.\n"
             "• Standalone NumPad keys (Num0–Num9) can now be bound for Ultimatum scanning.")
        ]
    },
    "1.4.1": {
        "title_ru": "Что нового в версии 1.4.1",
        "title_en": "What's New in version 1.4.1",
        "ru": [
            ("⚡ Исправление зависания круга «БРАТЬ» (исчезает до начала боя)",
             "• Устранена проблема, когда зелёный круг «БРАТЬ» оставался висеть на экране во время боя с монстрами.\n"
             "• Теперь подсказка исчезает автоматически через 3.5 сек (настраивается в меню: 2.5 с / 3.5 с / 5 с) — задолго до спавна монстров.\n"
             "• Мгновенное снятие: повторное нажатие F2, Esc или Пробел сразу убирает рамки с экрана."),

            ("🛡️ 100% честное соответствие правилам GGG (Zero Timer Reading)",
             "• В коде полностью отсутствует фоновое чтение экрана по таймеру.\n"
             "• Скан алтаря запускается строго разово по ручному нажатию горячей клавиши (по умолчанию F2).\n"
             "• 1 нажатие клавиши = 1 снимок экрана. Нулевой риск для игроков и блоггеров.")
        ],
        "en": [
            ("⚡ Fixed Lingering 'TAKE' Circle (Auto-Dismiss Before Combat)",
             "• Resolved the issue where the green 'TAKE' circle remained on screen during monster combat.\n"
             "• Marks now automatically disappear after 3.5 sec (configurable: 2.5s / 3.5s / 5s) — well before monsters spawn.\n"
             "• Instant dismiss: pressing F2 again, Esc, or Space immediately clears overlay marks."),

            ("🛡️ 100% GGG Developer Policy Compliant (Zero Timer Reading)",
             "• Completely eliminates any background timer-based screen reading.\n"
             "• Screen capture is performed strictly once per manual keypress (default: F2).\n"
             "• 1 keypress = 1 screen read. Zero risk for players and content creators.")
        ]
    },
    "1.4.0": {
        "title_ru": "Что нового в версии 1.4.0",
        "title_en": "What's New in version 1.4.0",
        "ru": [
            ("🛡️ 100% защита аккаунта и соответствие правилам GGG (ToS Safe)",
             "• Полностью исключено автоматическое чтение экрана по таймеру.\n"
             "• Сканирование алтаря ультиматума теперь запускается строго вручную по нажатию горячей клавиши (по умолчанию F2).\n"
             "• Правило «1 ручное нажатие = 1 чтение экрана» соблюдено на 100% — нулевой риск блокировки для игроков и стримеров.\n"
             "• Значительное снижение нагрузки: программа теперь потребляет 0% CPU в режиме ожидания."),

            ("⌨️ Настраиваемая горячая клавиша сканирования",
             "• В блок «Подсказка модов» добавлена кнопка настройки клавиши сканирования ультиматума.\n"
             "• Поддерживаются как одиночные клавиши (F1–F12, Home, End и др.), так и любые комбинации с Ctrl, Shift, Alt."),

            ("💰 Полная поддержка ультиматумов на удвоение валюты и карт в русском клиенте",
             "• Исправлено распознавание строчки «Требуется жертвоприношение: ...» в русской версии игры.\n"
             "• Корректно рассчитывается прибыль ультиматумов с удвоением валюты (Сферы хаоса X10) и карт (Неожиданная награда x1) с выводом карточки предпросмотра."),

            ("🖱️ Исправление прокрутки колесиком мыши в окне «Что нового»",
             "• Плавный скролл из любой точки окна и автоперенос строк внутри карточек.")
        ],
        "en": [
            ("🛡️ 100% GGG ToS Compliant & Zero Account Risk",
             "• Fully eliminated all background/timer-based screen reading.\n"
             "• Ultimatum altar modifier scanning is now triggered strictly on manual hotkey press (default: F2).\n"
             "• Fully adheres to GGG's '1 manual key press = 1 screen read' policy — safe for all players and streamers.\n"
             "• Massive performance gain: 0% CPU consumption in idle mode."),

            ("⌨️ Customizable Scan Hotkey",
             "• Added hotkey configuration for Ultimatum scan in the settings panel.\n"
             "• Supports standalone function keys (F1–F12, Home, End, etc.) as well as modifier combinations (Ctrl/Shift/Alt)."),

            ("💰 Full Fix for Currency & Card Doubling Inscribed Ultimatums (RU Client)",
             "• Fixed recognition of 'Требуется жертвоприношение: ...' in the Russian game client.\n"
             "• Net profit and card previews now display accurately for doubled currency and card ultimatums."),

            ("🖱️ Smooth Mousewheel Scrolling in What's New Modal",
             "• Responsive scrolling anywhere in the modal with dynamic text wrapping.")
        ]
    },
    "1.3.3": {
        "title_ru": "Что нового в версии 1.3.3",
        "title_en": "What's New in version 1.3.3",
        "ru": [
            ("💰 Полная поддержка ультиматумов на удвоение валюты и карт в русском клиенте",
             "• Исправлено распознавание строчки «Требуется жертвоприношение: ...» в русской версии игры.\n"
             "• Теперь корректно рассчитывается прибыль ультиматумов с удвоением валюты («Удваивает принесённую в жертву валюту», например Сферы хаоса X10) и карт («Удваивает принесённые в жертву гадальные карты», например Неожиданная награда x1).\n"
             "• Поддержка заглавной буквы «X» и любых форматов множителей (X10, x1, 10x).\n"
             "• Для ультиматумов с удвоением карт сразу выводится карточка предпросмотра с артом."),

            ("🖱️ Исправление прокрутки колесиком мыши",
             "• Окно «Что нового» теперь плавно и быстро прокручивается колесиком мыши из любого места окна (над текстом, карточками или фоном).\n"
             "• Автоматический перенос строк по ширине карточек — длинные строки больше не обрезаются по правому краю."),

            ("🎴 Полное исправление прайсчека и предпросмотра на русском клиенте",
             "• Поддержка всех форм написания карт в Начертанных ультиматумах: множественное число, двоеточия, любые виды кавычек («Доктор», Гадальные карты: Доктор, Гадальные карты “Доктор”, 2x Гадальные карты «...»).\n"
             "• Ультиматумы с картами в награде или жертве теперь безошибочно рассчитывают чистую прибыль и выводят визуальную карточку предпросмотра."),

            ("⚡ Поддержка изменённых предметов Foulborn («Нечестивый...»)",
             "• Чекер теперь различает обычные и Foulborn-уники/валюту (Нечестивый Охотник за головами, Нечестивая Волшебная кровь / Кровь мага, Нечестивая сфера возвышения и др.) и показывает точные цены их изменённых версий с poe.ninja.\n"
             "• Если на рынке нет отдельной цены для Foulborn-версии, автоматически подтягивается цена базового уника."),

            ("🚀 Мгновенная готовность к оценке при старте (28 мс)",
             "Локальный словарь и кэш цен теперь загружаются синхронно при запуске приложения — прайсчек готов к работе с первой миллисекунды без ожидания сетевых запросов и блокировок.")
        ],
        "en": [
            ("💰 Full Fix for Currency & Card Doubling Inscribed Ultimatums (RU Client)",
             "• Fixed recognition of 'Требуется жертвоприношение: ...' in the Russian game client.\n"
             "• Inscribed Ultimatums that double sacrificed currency (e.g., Chaos Orb X10) or divination cards (e.g., The Unexpected Prize x1) now calculate net profit accurately.\n"
             "• Support for uppercase 'X' and all quantity notations (X10, x1, 10x).\n"
             "• Divination card preview popup displays authentic card artwork immediately for doubled card ultimatums."),

            ("🖱️ Mousewheel Scrolling & Card Layout Fix",
             "• The 'What's New' modal now scrolls smoothly and responsively using the mouse wheel anywhere over the cards, text, or background.\n"
             "• Dynamic text wrapping per card width — long lines and paragraphs no longer clip past the right edge."),

            ("🎴 Full Fix for Russian Client Price Check & Inscribed Ultimatum Previews",
             "• Robust handling of plural forms, colons, quotes, and leading counts in Inscribed Ultimatum card rewards/sacrifices (Гадальные карты «...», Гадальная карта: ...).\n"
             "• Cards in Inscribed Ultimatums now accurately compute profit and display the authentic card artwork preview."),

            ("⚡ Support for Foulborn / Mutated Items",
             "• Accurate pricing and preview tooltips for Foulborn uniques and currency (Foulborn Headhunter, Foulborn Mageblood, Foulborn Exalted Orb, etc.) on both English and Russian clients (Нечестивый...).\n"
             "• Graceful fallback to base unique price if a Foulborn variant is not listed separately on poe.ninja."),

            ("🚀 Instant Offline Startup (28 ms)",
             "Dictionaries and price cache are loaded synchronously into memory on launch, ensuring instant price checking without blocking on network requests.")
        ]
    },
    "1.3.2": {
        "title_ru": "Что нового в версии 1.3.2",
        "title_en": "What's New in version 1.3.2",
        "ru": [
            ("🖱️ Исправление прокрутки колесиком мыши",
             "• Окно «Что нового» теперь плавно и быстро прокручивается колесиком мыши из любого места окна (над текстом, карточками или фоном).\n"
             "• Автоматический перенос строк по ширине карточек — длинные строки больше не обрезаются по правому краю."),

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
            ("🖱️ Mousewheel Scrolling & Card Layout Fix",
             "• The 'What's New' modal now scrolls smoothly and responsively using the mouse wheel anywhere over the cards, text, or background.\n"
             "• Dynamic text wrapping per card width — long lines and paragraphs no longer clip past the right edge."),

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

    # Сохраняем все метки карточек для динамического переноса строк (wraplength)
    card_labels = []

    def _on_canvas_configure(event):
        cw = event.width
        cv.itemconfig(win_id, width=cw)
        wrap_w = max(200, cw - 45)
        for lbl in card_labels:
            try:
                lbl.configure(wraplength=wrap_w)
            except Exception:
                pass
        content.update_idletasks()
        cv.configure(scrollregion=cv.bbox("all"))

    content.bind("<Configure>", lambda e: cv.configure(scrollregion=cv.bbox("all")))
    cv.bind("<Configure>", _on_canvas_configure)
    cv.pack(side="left", fill="both", expand=True)
    sb.pack(side="right", fill="y")

    # Колесико мыши (Windows delta / Linux Button-4/5)
    def _on_mousewheel(event):
        if not cv.winfo_exists():
            return "break"
        if getattr(event, "num", None) == 4:
            cv.yview_scroll(-2, "units")
        elif getattr(event, "num", None) == 5:
            cv.yview_scroll(2, "units")
        elif getattr(event, "delta", None):
            delta = event.delta
            step = -int(delta / 120) if abs(delta) >= 120 else (-1 if delta > 0 else 1)
            cv.yview_scroll(step * 2, "units")
        return "break"

    items = note_data.get("ru" if is_ru else "en", []) if note_data else []
    for h_txt, b_txt in items:
        o, c = T.card(content, None, pad=10)
        o.pack(fill="x", pady=(0, 10))
        h_lbl = tk.Label(c, text=h_txt, bg=T.CARD, fg=T.GOLD, font=(T.SERIF, 11, "bold"),
                         anchor="w", justify="left")
        h_lbl.pack(fill="x", anchor="w")
        b_lbl = tk.Label(c, text=b_txt, bg=T.CARD, fg=T.TXT, font=(T.SANS, 9),
                         anchor="w", justify="left")
        b_lbl.pack(fill="x", anchor="w", pady=(4, 0))
        card_labels.append(h_lbl)
        card_labels.append(b_lbl)

    # Первичный расчет переноса строк и скролл-области
    content.update_idletasks()
    init_cw = cv.winfo_reqwidth() if cv.winfo_width() <= 1 else cv.winfo_width()
    wrap_w = max(200, init_cw - 45)
    for lbl in card_labels:
        lbl.configure(wraplength=wrap_w)
    content.update_idletasks()
    cv.configure(scrollregion=cv.bbox("all"))

    # Подвал с кнопкой
    def _close():
        w.destroy()

    w.protocol("WM_DELETE_WINDOW", _close)

    foot = tk.Frame(w, bg=T.BG, padx=20, pady=14)
    foot.pack(fill="x")
    btn_txt = "Отлично, понятно!" if is_ru else "Got it!"
    T.button(foot, btn_txt, _close, fg=T.BG, bg=T.GOLD, hover=T.GOLD_HI).pack(side="right")

    # Привязываем колесико мыши только к виджетам этого окна (не перехватывает скролл у «Цен»)
    w.bind_class("UltWhatsNewScroll", "<MouseWheel>", _on_mousewheel)
    w.bind_class("UltWhatsNewScroll", "<Button-4>", _on_mousewheel)
    w.bind_class("UltWhatsNewScroll", "<Button-5>", _on_mousewheel)

    def _bind_mouse_recursive(widget):
        try:
            widget.bindtags(("UltWhatsNewScroll",) + widget.bindtags())
        except Exception:
            pass
        for child in widget.winfo_children():
            _bind_mouse_recursive(child)

    _bind_mouse_recursive(w)
    w.focus_set()

    return w
