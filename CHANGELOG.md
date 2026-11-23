# Changelog / Список изменений

## 1.4.0

**RU**
- **100% соответствие правилам GGG (ToS Safe, нулевой риск бана)**:
  - Полностью исключено любое автоматическое чтение экрана по таймеру в фоне.
  - Сканирование окна алтаря ультиматума теперь работает строго по ручному нажатию горячей клавиши (по умолчанию `F2`).
  - Соблюдено правило разработчиков GGG: «Одно ручное нажатие = одно чтение экрана». Безопасно для использования на стримах и видео.
- **Настраиваемая клавиша сканирования**:
  - В настройках («Подсказка модов») добавлена кнопка настройки клавиши сканирования ультиматума. Поддерживаются функциональные клавиши `F1..F12`, а также комбинации с `Ctrl`, `Alt`, `Shift`.
- **Нулевая нагрузка на CPU**:
  - Без циклического снятия скриншотов программа в режиме ожидания потребляет 0% процессора.

**EN**
- **100% GGG ToS Compliant & Zero Account Risk**:
  - Fully eliminated all automatic background timer-based screen reading.
  - Ultimatum altar modifier scanning is now triggered strictly on manual hotkey press (default: `F2`).
  - Fully adheres to GGG's developer policy: "One manual key press = one screen read". Completely safe for streaming.
- **Customizable Scan Hotkey**:
  - Added hotkey configuration for Ultimatum scan in the settings panel. Supports function keys `F1..F12` and combinations with `Ctrl`, `Alt`, `Shift`.
- **Zero CPU Idle Load**:
  - Without continuous screen capture loops, background CPU usage is 0%.

## 1.3.3

**RU**
- **Полное исправление Начертанных ультиматумов в русском клиенте (валюта и карты)**:
  - Исправлен разбор строки жертвы: в русском клиенте используется `Требуется жертвоприношение:` (ранее регулярное выражение ошибочно искало только корень с приставкой `пожертв...`).
  - Ультиматумы на удвоение валюты (`Удваивает принесённую в жертву валюту`, например `Сфера хаоса X10`) теперь правильно рассчитывают чистую прибыль.
  - Ультиматумы на удвоение карт (`Удваивает принесённые в жертву гадальные карты`, например `Неожиданная награда x1`) рассчитывают прибыль и выводят предпросмотр карточки с артом.
  - Поддержка заглавной буквы «X» и любых форматов множителей (`X10`, `x1`, `10x`).

**EN**
- **Full Fix for Inscribed Ultimatums on Russian Client (Currency & Divination Cards)**:
  - Fixed sacrifice line parsing for Russian client: `Требуется жертвоприношение: ...` is now correctly parsed.
  - Currency-doubling ultimatums (`Удваивает принесённую в жертву валюту`, e.g., `Chaos Orb X10`) now accurately calculate net profit.
  - Divination card doubling ultimatums (`Удваивает принесённые в жертву гадальные карты`, e.g., `The Unexpected Prize x1`) calculate net profit and display card artwork preview.
  - Case-insensitive quantity multiplier matching (`X10`, `x1`, `10x`).

## 1.3.2

**RU**
- **Исправление прокрутки колесиком мыши в окне «Что нового»**:
  - Окно теперь плавно и быстро прокручивается колесиком мыши из любого места окна (над текстом, карточками или фоном).
  - Автоматический перенос строк по ширине карточек — длинные строки больше не обрезаются по правому краю.

**EN**
- **Mousewheel Scrolling & Card Layout Fix in 'What's New' Modal**:
  - The 'What's New' modal now scrolls smoothly and responsively using the mouse wheel anywhere over the cards, text, or background.
  - Dynamic text wrapping per card width — long lines and paragraphs no longer clip past the right edge.

## 1.3.1

**RU**
- **Полное исправление прайсчека и предпросмотра на русском клиенте**:
  - Поддержка всех форм написания карт в Начертанных ультиматумах: множественное число, двоеточия, любые виды кавычек (`«Доктор»`, `Гадальные карты: Доктор`, `Гадальные карты “Доктор”`, `2x Гадальные карты «...»`).
  - Ультиматумы с картами в награде или жертве теперь безошибочно рассчитывают чистую прибыль и выводят визуальную карточку предпросмотра.
- **Поддержка изменённых предметов Foulborn («Нечестивый...»)**:
  - Чекер теперь различает обычные и Foulborn-уники/валюту (`Нечестивый Охотник за головами`, `Нечестивая Волшебная кровь` / `Кровь мага`, `Нечестивая сфера возвышения` и др.) и показывает точные цены их изменённых версий с poe.ninja.
  - Если на рынке нет отдельной цены для Foulborn-версии, автоматически подтягивается цена базового уника.
- **Мгновенная готовность к оценке при старте (28 мс)**:
  - Локальный словарь и кэш цен теперь загружаются синхронно при запуске приложения — прайсчек готов к работе с первой миллисекунды без ожидания сетевых запросов и блокировок.
- **Словарь русских названий расширен до 8 442 предметов**:
  - Синхронизированы абсолютно все гадальные карты и уникальные предметы базы предпросмотра.
- **Автоматическое обновление кэша цен при установке патча**:
  - Файл кэша цен в `%APPDATA%` теперь корректно обновляется у игроков, перешедших со старых версий.

**EN**
- **Full Fix for Russian Client Price Check & Inscribed Ultimatum Previews**:
  - Robust handling of plural forms, colons, quotes, and leading counts in Inscribed Ultimatum card rewards/sacrifices (`Гадальные карты «...»`, `Гадальная карта: ...`).
  - Cards in Inscribed Ultimatums now accurately compute profit and display the authentic card artwork preview.
- **Support for Foulborn / Mutated Items**:
  - Accurate pricing and preview tooltips for Foulborn uniques and currency (`Foulborn Headhunter`, `Foulborn Mageblood`, `Foulborn Exalted Orb`, etc.) on both English and Russian clients (`Нечестивый...`).
  - Graceful fallback to base unique price if a Foulborn variant is not listed separately on poe.ninja.
- **Instant Offline Startup (28 ms)**:
  - Dictionaries and price cache are loaded synchronously into memory on launch, ensuring instant price checking without blocking on network requests.
- **Russian Translation Dictionary Expanded to 8,442 Items**:
  - Full bidirectional synchronization for all divination cards and unique items.
- **Automatic Price Cache Refresh on Update**:
  - Automatically overwrites older cached files in `%APPDATA%` when a newer bundled version is detected.

## 1.3.0

**RU**
- **Встроенный предпросмотр наград Начертанного ультиматума (Inscribed Ultimatum)**:
  - Для гадальных карт отображается аутентичная карточка в стиле Path of Exile: название, арт карты, размер стопки, награда и художественный текст (flavour).
  - Для уникальных предметов отображается полный тултип предмета: база, требуемый уровень, собственные (implicits) и основные (explicits) свойства, художественный текст и иконка.
  - В настройки добавлен чекбокс «Карточка награды ультиматума (уники и карты)».
- **Все изображения полностью вшиты в клиент**:
  - Все 471 гадальных карт и 1 594 уникальных предметов упакованы прямо в программу — картинки отображаются мгновенно и работают без подключения к интернету.
- **Точная оценка камней умений (Gems)**:
  - Прайсчекер теперь определяет точный уровень камня (1–21), качество (+0–23%) и статус осквернения (Corrupted), показывая актуальную цену нужного варианта с poe.ninja.
- **Умный перезапуск без ошибок**:
  - Если программа уже была запущена, при открытии нового экземпляра старый процесс завершается автоматически и бесшовно уступает место новому.
- **Исправление данных и редкостей карт**:
  - Исправлены ошибки в стопках и наградах карт (Costly Curio, Demigod's Wager, Guardian's Challenge, Friendship и др.). Все уникальные награды теперь подсвечиваются правильным оранжевым цветом.
- **Окно «Что нового»**:
  - При первом запуске после обновления игроки сразу видят красивое окно со списком изменений патча (также доступно по клику на версию в подвале программы).

**EN**
- **Inscribed Ultimatum Reward Preview**:
  - Divination cards: authentic in-game style card display with header banner, card art, stack size badge, reward text, and flavour quote.
  - Unique items: complete tooltip with base item, required level, implicits, explicits, flavour text, and item icon.
  - Settings toggle: "Ultimatum reward preview (uniques & cards)".
- **All Images Bundled Offline**:
  - All 471 divination cards and 1,594 unique items are bundled directly into the executable for instant offline display.
- **Accurate Skill & Support Gem Pricing**:
  - Detects exact gem level (1–21), quality (+0–23%), and corrupted status, showing specific variant market prices.
- **Seamless Relaunch**:
  - Automatically terminates old instances on launch without "already running" errors.
- **Card Data & Rarity Fixes**:
  - Synchronized official card stack sizes and reward descriptions; fixed unique reward color highlighting.
- **What's New Window**:
  - Automatically displays patch notes on first launch after updating; clickable anytime via the version tag in the footer.

## 1.2.0

**RU**
- Поддержка ВСЕХ 48 категорий poe.ninja (более 41 000 предметов): Валюта, Фрагменты, Угли, Руны, Тату, Знамения, Монеты джиннов, Дукаты, Кристаллы, Карты, Масла, Инкубаторы, Трупы, Дары утробы, Внутренности, Уник. оружие/броня/бижутерия/флаконы/самоцветы, Запретные самоцветы, Пояса святилища, Настойки, Реликвии, Камни умений и Насыщенные камни, Кластеры, Карты, Валдо, Делириум, Скарабеи, Астролябии, Нити, Воспоминания, Храмы Ацоатль, Сферы гадания, Базовые предметы (болванки), Флаконы, Ископаемые, Резонаторы, Звери, Сущности, Жертвенные флаконы.
- Цены с малым числом сделок на рынке теперь гарантированно показываются с пометкой `? неточные данные (мало сделок на рынке)` вместо «нет цены».
- Для уникальной брони и оружия, у которых на poe.ninja есть только 5L/6L варианты, теперь берется цена с пометкой о неточности вместо отсутствия цены.
- Для редких предметов или баз при отсутствии точной цены оценивается болванка (`(база)`).
- Словарь русских названий расширен до 8 035 предметов (+2 500 новых переводов, включая внутренности, настойки и др.).

**EN**
- Full support for ALL 48 poe.ninja economy categories (41,000+ items).
- Items with low market trade volume now always display an approximate price with `? approximate data (few market trades)` tag instead of showing no price.
- Uniques with only 5L/6L listings are now priced with approximate tag instead of being ignored.
- Base item price fallback for rare/magic bases (`(base)`).
- Russian translation dictionary expanded to 8,035 items (+2,500 new translations).

## 1.1.0

**RU**
- В сборку (.exe) зашит полный словарь русских названий предметов (5 546 названий) — русский клиент работает сразу без скачивания из сети.
- В сборку зашит базовый кэш цен текущей лиги и список лиг — программа готова к оценке с первой миллисекунды запуска.
- Расширен список категорий poe.ninja: добавлены камни умений (SkillGem), кластерные самоцветы (ClusterJewel), уникальные реликвии (UniqueRelic) и заражённые карты (BlightedMap) — база выросла с 2 280 до 3 200+ предметов.
- Автоматическая очистка префиксов качества («Качественный», «Превосходный», «Superior») для камней умений и фласок при проверке цены.
- Исправлен парсинг начертанных ультиматумов с количеством предмета до названия («1x Сфера хаоса», «2x Сфера возвышения»).
- Добавлена задержка при плановом обновлении словаря для защиты от превышения лимитов API PoE (HTTP 429).
- Автоматическая нормализация неразрывных пробелов (\xa0) из буфера обмена.

**EN**
- Bundled full Russian item translation dictionary (5,546 items) — works out-of-the-box offline.
- Bundled baseline price cache and league list — instant price checks on startup.
- Expanded poe.ninja categories: SkillGem, ClusterJewel, UniqueRelic, BlightedMap (3,200+ items indexed).
- Quality prefix stripping (Superior / Quality) for gems and flasks.
- Inscribed Ultimatum parser support for prefix quantities (e.g. "1x Chaos Orb", "2x Exalted Orb").
- Rate-limit protection (HTTP 429) when fetching from official PoE trade API.
- Non-breaking space normalization (\xa0).

## 1.0.0 — первый выпуск / first release

**RU**
- Цена предмета по Ctrl+C рядом с курсором (poe.ninja), с учётом стопки; «мало данных» для ненадёжных цен; свои цены.
- Начертанный ультиматум: чистая прибыль и метка «% больше здоровья монстров» на языке клиента.
- Подсказка модов ультиматума: кольцо на самом простом разрешённом моде (10 волн) или «можно / нельзя» на выданном (13 волн).
- Рамка вокруг кнопки «Удвоить» (Double Down).
- Тир-лист из 47 модов, включая моды Миража; галочки, порядок, обмен настройками (Копировать / Вставить).
- Интерфейс RU / EN (по умолчанию — язык Windows), русский и английский клиент игры.
- Карточка не появляется, если предмет скопировал другой прайсчекер.
- Трей, автозапуск с Windows, горячая клавиша скрытия оверлея, звук.

**EN**
- Item price on Ctrl+C next to the cursor (poe.ninja), stack-aware; “little data” mark; custom prices.
- Inscribed Ultimatum: net profit and the “% more Monster Life” tag in the client language.
- Ultimatum modifier hints: ring on the easiest allowed modifier (10 waves) or allowed / forbidden on the given one (13 waves).
- Double Down button highlight.
- 47-modifier tier list incl. Mirage modifiers; toggles, order, settings sharing (Copy / Paste).
- RU / EN interface (defaults to the Windows language), Russian and English game clients.
- The card does not pop up when another price checker copies the item.
- Tray, start with Windows, hide-overlay hotkey, sound.
