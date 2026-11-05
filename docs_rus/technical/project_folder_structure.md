# Структура папок проекта
Где расположены все части проекта?

## Дерево
.
├── archive
├── db
│   ├── backup_tsv
│   ├── bold_definitions
│   ├── epd
│   ├── families
│   ├── grammar
│   ├── inflections
│   ├── lookup
│   ├── sanskrit
│   ├── suttas
│   └── variants
├── db_tests
│   └── single
├── docs
├── exporter
│   ├── apple_dictionary
│   ├── deconstructor
│   ├── goldendict
│   ├── grammar_dict
│   ├── kindle
│   ├── kobo
│   ├── mobile
│   ├── pdf
│   ├── share
│   ├── sutta_central
│   ├── tbw
│   ├── tpr
│   ├── variants
│   ├── webapp
│   └── wxt_extension
├── go_modules
│   ├── deconstructor
│   ├── dpdDb
│   ├── frequency
│   ├── tools
├── gui2
├── newsletter
├── resources
├── scripts
│   ├── add
│   ├── bash
│   ├── build
│   ├── export
│   ├── extractor
│   ├── find
│   ├── fix
│   ├── info
│   ├── onboarding
│   ├── patch
│   ├── project_management
│   ├── repo_maintenance
│   ├── server_contrib
│   ├── server_dpdict
│   ├── suttas
│   ├── tutorial
├── shared_data
├── temp
├── tests
└── tools

## Структура кода

Код состоит из четырёх основных частей:

1. __db__: Создание базы данных и построение таблиц производных данных.
2. __db_tests__: Запуск тестов целостности данных в базе данных.
3. __gui2__: Добавление новых слов, редактирование и обновление базы данных через графический интерфейс.
4. __exporter__: Сборка всех частей и экспорт в различные форматы словарей.

## Описание папок

- **archive/** Устаревший код, сохранённый для справки, например MCP-сервер (`archive/exporter/mcp/`, архивирован 2026-09-27).

- **db/** Весь код, связанный с построением и наполнением различных таблиц и столбцов базы данных.

    - **models.py** Модель базы данных на SQLAlchemy.

    - **db_helpers.py** Вспомогательные функции для создания базы данных, получения сессии, получения названий столбцов и т. д.

    - **backup_tsv/** TSV-резервные копии исходных таблиц базы данных

    - **bold_definitions/** Извлечение определений, выделенных жирным шрифтом, из текстов CST и их компиляция для удобного поиска.

	- **db/epd/** Компиляция данных для англо-пали словаря.

	- **families/** Компиляция HTML- и JSON-списков для наполнения таблиц `family_compound`, `family_idiom`, `family_root`, `family_word` и `family_set` в базе данных для удобного доступа.

	- **grammar/** Грамматические данные и их обработка.

	- **inflections/** Наполнение таблицы `inflection_templates` и создание на её основе HTML-таблиц словоизменения для каждого слова. Источники: `templates_index.tsv` (одна строка на шаблон: pattern, like, group) и `templates/<pattern>.tsv` (один файл сетки на шаблон).

	- **lookup/** Наполнение таблицы `lookup` для мгновенного доступа к каждому слову словаря.

	- **sanskrit/** Данные для обновления столбца `sanskrit` в таблице `dpd_headwords`.

	- **suttas/** Метаданные сутт и их обработка.

	- **variants/** Данные о вариантных чтениях и их обработка.

- **db_tests/** Тесты для проверки полноты и точности базы данных пали.

	- **single/** Отдельные узконаправленные скрипты аудита — по одному скрипту на каждое лингвистическое или структурное правило. Скрипты `add_*` также позволяют просматривать и утверждать массовые исправления данных в терминале (антонимы, составные слова семейств, расстановка дефисов).

- **docs/** Полезная документация проекта.

	- **project_folder_structure.md** То, что вы читаете прямо сейчас.

	- **dpd_headwords_table.md** Описание реальных и виртуальных столбцов таблицы `dpd_headwords`.

- **exporter/** Экспорт базы данных DPD в различные форматы.

	- **apple_dictionary/** Экспорт DPD для Apple Dictionary.

	- **deconstructor/** Экспорт деконструктора DPD в GoldenDict и MDict

	- **epitaka/** Копирование мобильной базы данных DPD в локальное приложение ePitaka (только локально).

	- **goldendict/** Экспорт DPD, EPD, справки и сокращений в GoldenDict и MDict

	- **grammar_dict/** Экспорт грамматики DPD в GoldenDict и MDict

	- **kindle/** Экспорт облегчённой версии DPD для Kindle.

	- **kobo/** Экспорт облегчённой версии DPD для Kobo eReader.

	- **mobile/** Экспорт облегчённой версии DPD для мобильных устройств.

	- **pdf/** Экспорт DPD в формат PDF.

	- **sutta_central/** Экспорт данных DPD для интеграции с SuttaCentral.

	- **tbw/** Экспорт облегчённой версии DPD для интеграции с [сайтом The Buddha's Words](https://thebuddhaswords.net/mn/mn1.html){target="_blank"}.

	- **tpr/** Экспорт данных грамматического деконструктора DPD для интеграции с приложением Tipitaka Pali Reader

	- **variants/** Экспорт данных о вариантных чтениях.

	- **webapp/** Веб-приложение на основе базы данных DPD и FastApi, размещённое на [www.dpdict.net](https://ru.dpdict.net){target="_blank"}

	- **wxt_extension/** Экспорт DPD как кроссбраузерного расширения на фреймворке WXT.

- **go_modules/** Когда Python слишком медленный, пишем на GO

	- **deconstructor/** Разбор более миллиона составных слов

	- **dpdDb/** Доступ к базе данных через GORM

	- **frequency/** Создание таблиц частотности и списков данных для каждого слова

	- **tools/** GO-пакеты, используемые в проекте

- **gui2/** Графический интерфейс для ввода данных и запуска тестов базы данных

- **newsletter/** Ежемесячная рассылка: одна папка на месяц (`<YYYY-MM>/newsletter.md` + `pics/`), общий нижний колонтитул и сборщик, на котором основаны `just newsletter-new`, `newsletter-preview` и `newsletter-publish`.

- **resources/** Все внешние ресурсы, используемые проектом, подключённые как подмодули

- **scripts/** Полезные скрипты для обслуживания проекта.

	см. [readme скриптов](https://github.com/sasanarakkha/dpd-db-sbs/tree/main/scripts#readme){target="_blank"} для получения дополнительной информации.

- **shared_data/** Данные, используемые во всём проекте.

- **tests/** Автоматические тесты проекта.

- **tools/** Модули Python, используемые во всём проекте.
