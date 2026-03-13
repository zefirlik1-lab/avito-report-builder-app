
# Project Rules

## 1. Project Overview
- Проект: **Avito Report Builder**
- Тип продукта: внутреннее desktop-first web-приложение для агентства
- Цель MVP: принимать один `.xlsx` файл выгрузки Авито, валидировать его, нормализовать данные, рассчитывать производные поля, собирать итоговую Excel-книгу фиксированного формата и отдавать её пользователю на скачивание
- Система не является универсальным Excel-конструктором. Это шаблонный генератор одного типа отчёта под один входной формат

## 2. Tech Stack
- Language: **Python 3.11+**
- UI: **Streamlit**
- Data processing: **pandas**
- Excel read/write: **openpyxl**
- Configs: **YAML + PyYAML**
- Models and config validation: **pydantic v2**
- Tests: **pytest**
- Lint/format: **ruff**
- Typing: встроенные type hints + `mypy` optional, но код писать с расчётом на строгую типизацию
- Package/dependency management: **uv** или **poetry**; для MVP по умолчанию **uv**
- Database: **не используется**
- ORM / data layer: **не используется**

## 3. Architecture Style
- Архитектура: **modular monolith**
- Один deployable unit
- Один runtime process Streamlit
- Без отдельного backend API в MVP
- UI не должен содержать бизнес-логику обработки Excel
- Вся логика генерации отчёта должна вызываться через единый application entry point: `generate_report(...)`

### Слои
- `ui` — Streamlit-экран, загрузка файла, показ статуса, ошибок, скачивание результата
- `application` — orchestration pipeline, сценарий генерации, статусные этапы
- `domain` — правила валидации, нормализации, классификации, enrichment, расчётов, sheet building
- `infrastructure` — Excel I/O, YAML loader, workbook formatting, file/temp helpers

## 4. Storage
- Постоянное хранение файлов: **нет**
- БД: **нет**
- История генераций: **нет**
- Обработка файла: в памяти; при необходимости допустим временный файл в temp directory на время одного запуска
- После формирования результата входной и выходной файл не сохраняются как постоянные артефакты приложения
- Конфиги хранятся в репозитории в виде YAML-файлов

## 5. Auth and Access
- Аутентификация: **нет в MVP**
- Роли: **нет**
- Все пользователи MVP имеют одинаковый доступ ко всем функциям приложения
- UI не должен содержать логику разграничения прав
- Возможное будущее SSO/авторизация не учитывать в текущей архитектуре как обязательную зависимость

## 6. API Conventions
- Внешний HTTP API: **не реализуется в MVP**
- Основной публичный entry point приложения:
  - `generate_report(input_bytes: bytes, filename: str, cabinet_name: str | None = None) -> ReportWorkbook`
- Отдельные внутренние entry points:
  - `validate_input_file(...)`
  - `read_source_workbook(...)`
  - `normalize_dataset(...)`
  - `enrich_dataset(...)`
  - `build_report_workbook(...)`
- Все модули должны взаимодействовать через Python objects / DataFrame / typed models, а не через Streamlit state
- Streamlit вызывает только application service, но не domain-функции напрямую пачкой из UI

## 7. Validation
- Принимается только **один** файл за один запуск
- Разрешён только формат **`.xlsx`**
- Валидация выполняется до запуска основной обработки
- Критические ошибки валидации останавливают процесс и не формируют итоговый файл
- Проверять:
  - файл не пустой
  - расширение и читаемость workbook
  - наличие ожидаемого листа данных
  - наличие обязательных колонок
  - корректность шапки, если строка заголовка зафиксирована
- Заголовки колонок нормализуются перед mapping
- Лишние колонки игнорируются, если не мешают обработке
- Для строковых полей применять `strip()`
- Числовые поля приводить к numeric с безопасной обработкой ошибок
- Даты приводить к согласованному формату даты
- Политика частично пустых строк:
  - полностью пустые строки удалять
  - строки без `ad_id` и без `title` удалять
  - остальные строки оставлять и применять safe defaults

## 8. Error Handling
- Использовать единый набор доменных исключений
- Минимальные коды ошибок:
  - `INVALID_FILE_TYPE`
  - `EMPTY_FILE`
  - `BROKEN_EXCEL`
  - `REQUIRED_SHEET_MISSING`
  - `REQUIRED_COLUMNS_MISSING`
  - `DATA_NORMALIZATION_ERROR`
  - `REPORT_BUILD_ERROR`
- Ошибки разделять на:
  - validation errors
  - normalization/data errors
  - business rule errors
  - unexpected internal errors
- Для UI показывать короткие и понятные сообщения без stack trace
- Для технического лога сохранять полный контекст ошибки
- Некритичные проблемы значений не должны падать весь pipeline; они должны превращаться в warnings, если обработку можно продолжить
- Деление на ноль всегда даёт безопасное значение `0`

## 9. Logging
- Логировать этапы pipeline:
  - uploaded
  - validating
  - validation_failed
  - reading
  - normalizing
  - enriching
  - building_sheets
  - writing_workbook
  - formatting_workbook
  - completed
  - failed
- Логировать:
  - имя файла
  - размер файла
  - имя исходного листа
  - количество строк до и после нормализации
  - warnings count
  - причины ошибок
  - длительность генерации
- Не логировать содержимое всего файла целиком
- Не логировать персональные/чувствительные данные без необходимости
- Формат логов: структурированный text/JSON; для MVP допустим стандартный `logging` с единым formatter
- Уровни логирования:
  - `INFO` — этапы и успешные действия
  - `WARNING` — безопасно обработанные проблемы данных
  - `ERROR` — критические ошибки и падения pipeline

## 10. Environment and Config
- Все runtime-настройки должны приходить через env variables или конфиг-файлы
- Секреты в репозиторий не коммитить
- Минимальные env-переменные:
  - `APP_ENV`
  - `LOG_LEVEL`
  - `STREAMLIT_SERVER_PORT`
  - `DEFAULT_CABINET_NAME` optional
- Конфиги, которые должны лежать отдельно от кода:
  - column mapping
  - type rules
  - redirect mapping
  - workbook layout / formatting presets
- Формат конфигов: **YAML**
- Изменение бизнес-правил должно происходить через конфиг, а не через хаотичные правки sheet builder-кода
- Окружения:
  - `local`
  - `dev`
  - `prod` optional later
- Для MVP локальный запуск обязателен; контейнеризация допустима, но не должна усложнять старт разработки

## 11. Folder Structure
```text
app/
  ui/
    main.py

  application/
    services/
      report_generation.py
    dto/
    exceptions.py
    status.py

  domain/
    validation/
    transformations/
    classification/
    enrichment/
    summary/
    sheet_builders/
    models/
    rules/

  infrastructure/
    excel/
      reader.py
      writer.py
      formatter.py
    config/
      loader.py
    storage/
      temp_files.py
    logging/

  configs/
    column_mapping.yaml
    type_rules.yaml
    redirect_mapping.yaml
    workbook_layout.yaml

  tests/
    fixtures/
      input/
      expected/
    unit/
    integration/

  pyproject.toml
  README.md
````

## 12. Development Conventions

* Код писать на **Python only**
* Streamlit использовать только как UI-слой
* Не смешивать:

  * UI callbacks
  * orchestration
  * domain rules
  * Excel formatting
* Основной pipeline должен быть пошаговым и явным
* Предпочтительный стиль:

  * небольшие чистые функции
  * понятные имена
  * минимум магии
  * без преждевременных абстракций
* Naming:

  * `snake_case` — функции, переменные, файлы
  * `PascalCase` — классы, pydantic models, custom exceptions
  * `UPPER_SNAKE_CASE` — константы
* Все правила маппинга и классификации хранить в конфиге
* Не зашивать employee-to-redirect mapping прямо в builder-код
* Все расчёты делать в Python, а не формулами Excel, если нет отдельного требования
* Для новых фич сначала добавлять/обновлять fixture-based tests
* Каждый модуль должен быть тестируем независимо от Streamlit
* Код форматировать и проверять через `ruff format` и `ruff check`

## 13. Domain Rules

### 13.1 Source file

* Входной файл всегда один
* Поддерживается только `.xlsx`
* `.xls`, `.csv`, multi-file режим не поддерживать

### 13.2 Canonical dataset

* Внутренняя каноническая схема должна строиться вокруг `NormalizedRow`
* Основной runtime dataset — `pandas.DataFrame`
* Канонические поля должны соответствовать ТЗ и быть едиными для всех downstream sheet builders

### 13.3 Safe defaults

* Пустые агрегируемые числовые значения по умолчанию: `0`
* Неуспешное деление: `0`
* Неизвестный `type`: **`Не определено`**
* Неизвестный `redirect_target`: пустое значение + warning
* `avito_number_display` хранить как string
* `cabinet_name` брать из UI; если пользователь не ввёл и есть `DEFAULT_CABINET_NAME`, использовать его

### 13.4 Type classification

* `type` вычисляется по полю `title`
* Источник правил: `type_rules.yaml`
* Поддерживаемые match types:

  * `contains`
  * `regex`
  * `exact`
* При конфликте использовать правило с наибольшим приоритетом
* Если ничего не совпало, ставить `Не определено`
* Нераспознанные заголовки собирать в warnings/logs

### 13.5 Redirect target

* `redirect_target` заполнять через YAML mapping
* Источник правил: `redirect_mapping.yaml`
* Mapping должен быть детерминированным и не зависеть от порядка sheet builders
* Если маппинг не найден, ставить пустое значение и добавлять warning

### 13.6 Summary calculations

* `конверсия = contacts * 100 / views`
* `средняя стоимость заявки = ad_spend / contacts`, пока не утверждено другое правило
* Комментарий в `Сводная` оставлять пустым
* Все метрики `Сводная` считать только по текущему файлу
* Если позже подтвердится, что расход должен считаться как сумма нескольких spend-полей, изменить правило централизованно в summary module, а не точечно по листам

## 14. UI Rules

* Один основной экран
* Элементы экрана:

  * заголовок инструмента
  * file uploader
  * optional input `Кабинет Авито`
  * кнопка `Сформировать отчёт`
  * блок статуса
  * блок ошибок/предупреждений
  * кнопка скачивания результата
* UI должен быть desktop-first
* Мобильная адаптация не обязательна
* UI не должен показывать технические traceback пользователю
* После успешной генерации пользователь должен скачать готовый файл сразу в текущей сессии
* Не реализовывать отдельные экраны настроек правил в MVP

## 15. Excel Output Rules

* Итоговая книга должна содержать листы в фиксированном порядке:

  * `Админ панель`
  * `Диаграмма`
  * `Недельный`
  * `Сводная`
* Builder каждого листа отвечает только за подготовку данных листа
* Formatter отвечает только за визуальное оформление workbook
* Минимально поддерживаемое форматирование:

  * sheet order
  * sheet titles
  * header style
  * freeze panes
  * autofilter
  * column widths
  * number/date/currency/percent formats
  * alignment
* Не смешивать расчёты и визуальное форматирование в одном месте
* Не использовать сложные Excel charts, пока не будет точного описания листа `Диаграмма`
* Если содержание `Диаграмма` не утверждено, сначала реализовать этот лист как табличные данные для будущих графиков

## 16. Testing Strategy

* Unit tests обязательны для:

  * validators
  * transformers
  * classifiers
  * enrichment
  * summary calculations
  * sheet builders
* Integration tests обязательны для полного `generate_report(...)` на fixture-based sample input
* Должны существовать фикстуры:

  * sample input workbook
  * expected output workbook or expected sheet data
* При изменении column mapping/type rules/sheet layout обновлять фикстуры и тесты
* Минимум один regression test на каждый ранее найденный edge case

## 17. MVP Simplifications

* Без БД
* Без авторизации
* Без API
* Без истории
* Без редактирования правил через UI
* Без нескольких шаблонов
* Без мультифайловой обработки
* Без интеграций с Avito API
* Без универсального rule engine
* Без сложного DSL для layout builder
* Без микросервисов и фоновых очередей
* Без хранения артефактов после завершения ответа пользователю

## 18. Open Questions

* Точное имя обязательного входного листа
* Точный список обязательных колонок
* Финальный column mapping: входные колонки → канонические поля
* Точный состав и порядок колонок для листов:

  * `Админ панель`
  * `Диаграмма`
  * `Недельный`
  * `Сводная`
* Что именно должно быть на листе `Диаграмма`: таблицы-источники или готовые Excel charts
* Точное правило расчёта общего расхода для `Сводная`: только `ad_spend` или сумма нескольких spend-полей
* Нужна ли фиксированная строка шапки и какая именно
* Как обрабатывать дубли объявлений
* Нужно ли отображать warnings пользователю в UI или только писать в лог
* Как формировать имя итогового файла
* Точные formatting rules по каждому листу

## 19. Decision Defaults for MVP

* Один входной лист данных
* Один сценарий генерации
* `cabinet_name` вводится через UI, с optional дефолтом из env/config
* `type` по YAML rules
* `redirect_target` по YAML mapping
* Safe default для неизвестного `type`: `Не определено`
* Safe default для unknown `redirect_target`: пусто + warning
* Деление на ноль: `0`
* Числовые пустые значения в агрегируемых полях: `0`
* Лист `Диаграмма` в первой реализации делать максимально простым, без сложных встроенных Excel chart objects, пока бизнес не даст точную спецификацию

```
```
