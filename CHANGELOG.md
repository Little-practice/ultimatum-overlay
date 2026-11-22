# Changelog / Список изменений

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
