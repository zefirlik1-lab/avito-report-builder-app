# План реализации MVP и структура backend-проекта

## 1. Анализ документации и примеров Excel

### Итоги анализа
- **Продукт:** Avito Report Builder — внутренний web-инструмент для обработки одной Excel-выгрузки Авито и генерации одного итогового .xlsx в фиксированном формате.
- **Стек:** Python 3.11+, Streamlit, pandas, openpyxl, YAML, pydantic v2, pytest, ruff; менеджер зависимостей — uv.
- **Архитектура:** modular monolith; слои — UI → Application → Domain → Infrastructure. Единая точка входа: `generate_report(input_bytes, filename, cabinet_name?) → ReportWorkbook`.
- **Вход:** один .xlsx, один лист с данными, обязательные колонки (точный список — в Open Questions).
- **Выход:** книга с листами в порядке: **Админ панель** → **Диаграмма** → **Недельный** → **Сводная**; форматирование (шапки, freeze, автофильтр, ширины, форматы чисел/даты/валюта/проценты).
- **Excel-примеры:** `data/input_example.xlsx` и `data/expected_report.xlsx` — бинарные; при реализации нужно вручную выписать из них: имена и порядок колонок входа, имена и порядок колонок по каждому выходному листу, примеры строк. Это станет основой для `column_mapping.yaml` и `workbook_layout.yaml`.

---

## 2. Пошаговый план реализации MVP

### Фаза 0. Подготовка (до кода)
| Шаг | Действие |
|-----|----------|
| 0.1 | Открыть `input_example.xlsx` и `expected_report.xlsx`, зафиксировать: имя входного листа, список колонок входа, порядок и названия колонок на каждом выходном листе. |
| 0.2 | Заполнить конфиги-заглушки: `column_mapping.yaml`, `type_rules.yaml`, `redirect_mapping.yaml`, `workbook_layout.yaml` (минимально по структуре из project_rules). |
| 0.3 | Зафиксировать список обязательных колонок и имя обязательного листа (или взять из примера). |

### Фаза 1. Инфраструктура и конфиги
| Шаг | Действие |
|-----|----------|
| 1.1 | Инициализировать проект: `pyproject.toml`, uv, зависимости (streamlit, pandas, openpyxl, pyyaml, pydantic, pytest, ruff). |
| 1.2 | Реализовать загрузку конфигов: `config/loader.py` — чтение YAML, валидация через pydantic-схемы где нужно. |
| 1.3 | Реализовать Excel I/O: `excel/reader.py` (чтение листа в DataFrame), `excel/writer.py` (создание книги, запись листов в bytes). |
| 1.4 | Ввести единые исключения: `exceptions.py` с кодами INVALID_FILE_TYPE, EMPTY_FILE, BROKEN_EXCEL, REQUIRED_SHEET_MISSING, REQUIRED_COLUMNS_MISSING, DATA_NORMALIZATION_ERROR, REPORT_BUILD_ERROR. |
| 1.5 | Настроить логирование: этапы pipeline (uploaded, validating, … completed/failed), без вывода сырых данных и PII. |

### Фаза 2. Домен: валидация и нормализация
| Шаг | Действие |
|-----|----------|
| 2.1 | Валидация: проверка расширения, непустой файл, читаемость workbook, наличие нужного листа, наличие обязательных колонок. Вход: bytes; выход: успех или выброс доменного исключения. |
| 2.2 | Нормализация: нормализация заголовков по column_mapping, strip() для строк, приведение числовых полей к numeric (с safe defaults), дат — к единому формату. |
| 2.3 | Фильтрация строк: удалить полностью пустые; удалить строки без ad_id и без title; остальные оставить с safe defaults (числа → 0 где нужно). |
| 2.4 | Модель данных: определить NormalizedRow (pydantic или типизированный датакласс) и убедиться, что канонический DataFrame соответствует этой схеме. |

### Фаза 3. Домен: классификация и обогащение
| Шаг | Действие |
|-----|----------|
| 3.1 | Классификация Тип: загрузка правил из `type_rules.yaml` (contains/regex/exact, priority), применение к полю title; при отсутствии совпадения — «Не определено»; нераспознанные заголовки — в warnings. |
| 3.2 | Enrichment: заполнение cabinet_name (из аргумента/UI или DEFAULT_CABINET_NAME), redirect_target по `redirect_mapping.yaml` от employee (если не найден — пусто + warning), avito_number_display как string из исходного номера объявления. |

### Фаза 4. Домен: сборка листов и сводная
| Шаг | Действие |
|-----|----------|
| 4.1 | Summary: расчёт по текущему датасету — суммы (views, contacts, ad_spend и т.д.), конверсия = contacts*100/views, средняя стоимость заявки = ad_spend/contacts; деление на ноль → 0; комментарий пустой. |
| 4.2 | Sheet builders: отдельные функции (или мелкие модули) для подготовки данных: Админ панель, Диаграмма, Недельный, Сводная. Каждый только данные; порядок колонок — по workbook_layout. |
| 4.3 | Лист «Диаграмма»: в MVP — табличные данные для будущих графиков (без сложных Excel charts), если точная спецификация ещё не утверждена. |

### Фаза 5. Application и Excel-экспорт
| Шаг | Действие |
|-----|----------|
| 5.1 | Pipeline в application: `generate_report(input_bytes, filename, cabinet_name?)` по шагам: validate → read → normalize → enrich → build_sheets → write_workbook → format_workbook; статусы для логов; при ошибке — выброс исключения с кодом, без проброса сырого traceback в UI. |
| 5.2 | Writer: создание workbook, запись листов в фиксированном порядке (Админ панель, Диаграмма, Недельный, Сводная), сохранение в bytes. |
| 5.3 | Formatter: применение оформления из конфига/кода — порядок листов, имена, шапка, freeze panes, autofilter, ширины колонок, форматы чисел/даты/валюта/проценты, выравнивание. |

### Фаза 6. UI
| Шаг | Действие |
|-----|----------|
| 6.1 | Один экран: заголовок, file uploader (.xlsx), опциональное поле «Кабинет Авито», кнопка «Сформировать отчёт». |
| 6.2 | Вызов только `generate_report(...)` из application; отображение статуса и ошибок (короткие сообщения по коду/типу ошибки, без stack trace). |
| 6.3 | После успешной генерации — кнопка/ссылка скачивания итогового файла (имя файла — по решению из Open Questions). |

### Фаза 7. Тесты и отладка
| Шаг | Действие |
|-----|----------|
| 7.1 | Unit-тесты: validators, transformers, type classifier, enrichment, summary_calculator, каждый sheet builder. |
| 7.2 | Фикстуры: скопировать/зафиксировать `input_example.xlsx` и эталонный фрагмент `expected_report.xlsx` (или ожидаемые данные по листам) в `tests/fixtures/`. |
| 7.3 | Интеграционный тест: `generate_report()` на фикстурном входе, проверка наличия листов, порядка и ключевых значений (или сравнение с эталоном). |
| 7.4 | Ruff: format + check; при необходимости — mypy. |

---

## 3. Структура backend-проекта (папки и файлы)

Ниже — структура в соответствии с **project_rules.md** (раздел 11), с уточнением имён и добавлением недостающих модулей.

```
app/
  ui/
    main.py

  application/
    services/
      report_generation.py
    dto/
      __init__.py
    exceptions.py
    status.py

  domain/
    validation/
      __init__.py
      input_validator.py
    transformations/
      __init__.py
      normalizer.py
    classification/
      __init__.py
      type_classifier.py
    enrichment/
      __init__.py
      enricher.py
    summary/
      __init__.py
      calculator.py
    sheet_builders/
      __init__.py
      admin_sheet.py
      chart_sheet.py
      weekly_sheet.py
      summary_sheet.py
    models/
      __init__.py
      normalized_row.py
      report_dataset.py
      sheet_data.py
    rules/
      __init__.py

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
      __init__.py
      setup.py

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
.env.example
```

---

## 4. Назначение файлов (кратко)

### UI
| Файл | Назначение |
|------|------------|
| `app/ui/main.py` | Точка входа Streamlit: один экран — заголовок, загрузка .xlsx, поле «Кабинет Авито», кнопка «Сформировать отчёт», блок статуса/ошибок, кнопка скачивания. Вызывает только application service. |

### Application
| Файл | Назначение |
|------|------------|
| `app/application/services/report_generation.py` | Единая точка входа: `generate_report(input_bytes, filename, cabinet_name?)` — оркестрация шагов валидации, чтения, нормализации, enrichment, сборки листов, записи и форматирования workbook; возврат ReportWorkbook. |
| `app/application/dto/__init__.py` | Реэкспорт DTO (например, обёртки для входа/выхода сервиса, если появятся). |
| `app/application/exceptions.py` | Доменные исключения с кодами: INVALID_FILE_TYPE, EMPTY_FILE, BROKEN_EXCEL, REQUIRED_SHEET_MISSING, REQUIRED_COLUMNS_MISSING, DATA_NORMALIZATION_ERROR, REPORT_BUILD_ERROR. |
| `app/application/status.py` | Перечисление/константы статусов pipeline: uploaded, validating, validation_failed, reading, normalizing, enriching, building_sheets, writing_workbook, formatting_workbook, completed, failed. |

### Domain
| Файл | Назначение |
|------|------------|
| `app/domain/validation/input_validator.py` | Валидация входного файла: расширение .xlsx, непустой, читаемость, наличие ожидаемого листа и обязательных колонок. |
| `app/domain/transformations/normalizer.py` | Нормализация: маппинг колонок по конфигу, strip строк, приведение типов (numeric, date), удаление пустых/невалидных строк, сборка канонического DataFrame. |
| `app/domain/classification/type_classifier.py` | Классификация поля type по title по правилам из type_rules.yaml (contains/regex/exact, priority); дефолт «Не определено». |
| `app/domain/enrichment/enricher.py` | Заполнение производных полей: type, cabinet_name, redirect_target (из redirect_mapping по employee), avito_number_display. |
| `app/domain/summary/calculator.py` | Расчёт метрик для листа Сводная: суммы, конверсия, средняя стоимость заявки; деление на ноль → 0; комментарий пустой. |
| `app/domain/sheet_builders/admin_sheet.py` | Подготовка данных для листа «Админ панель» (выбор и порядок колонок по конфигу). |
| `app/domain/sheet_builders/chart_sheet.py` | Подготовка данных для листа «Диаграмма» (табличные данные для будущих графиков в MVP). |
| `app/domain/sheet_builders/weekly_sheet.py` | Подготовка данных для листа «Недельный». |
| `app/domain/sheet_builders/summary_sheet.py` | Сборка данных листа «Сводная» из summary calculator (метрики + пустой комментарий). |
| `app/domain/models/normalized_row.py` | Модель одной нормализованной строки (pydantic/dataclass) — канонические поля. |
| `app/domain/models/report_dataset.py` | Модель ReportDataset: DataFrame + row_count, source_sheet_name, warnings. |
| `app/domain/models/sheet_data.py` | Модели/типы для AdminSheetData, ChartSheetData, WeeklySheetData, SummarySheetData (данные для каждого листа). |
| `app/domain/rules/__init__.py` | Реэкспорт или заглушка для правил, если вынесут из конфигов в код. |

### Infrastructure
| Файл | Назначение |
|------|------------|
| `app/infrastructure/excel/reader.py` | Чтение .xlsx из bytes: открытие workbook, чтение указанного листа в pandas DataFrame. |
| `app/infrastructure/excel/writer.py` | Создание Excel-книги, запись листов (по данным из sheet builders), сохранение в bytes (ReportWorkbook). |
| `app/infrastructure/excel/formatter.py` | Применение оформления к workbook: порядок листов, имена, стиль шапки, freeze panes, autofilter, ширины колонок, форматы чисел/даты/валюта/проценты, выравнивание (по workbook_layout/конфигу). |
| `app/infrastructure/config/loader.py` | Загрузка и парсинг YAML-конфигов (column_mapping, type_rules, redirect_mapping, workbook_layout); при необходимости валидация через pydantic. |
| `app/infrastructure/storage/temp_files.py` | Вспомогательные функции для временных файлов (если понадобится писать во временный файл на время одной генерации). |
| `app/infrastructure/logging/setup.py` | Инициализация логгера, formatter, уровни (INFO/WARNING/ERROR) для этапов pipeline. |

### Configs
| Файл | Назначение |
|------|------------|
| `app/configs/column_mapping.yaml` | Соответствие имён колонок входа и канонических полей (внутренняя схема). |
| `app/configs/type_rules.yaml` | Правила классификации type по title: pattern, match_type (contains/regex/exact), result_type, priority, enabled, case_sensitive, comment. |
| `app/configs/redirect_mapping.yaml` | Маппинг employee → redirect_target. |
| `app/configs/workbook_layout.yaml` | Порядок листов, имена, порядок колонок по листам, параметры форматирования (ширины, форматы чисел и т.д.). |

### Tests
| Файл/папка | Назначение |
|------------|------------|
| `tests/fixtures/input/` | Тестовые входные файлы (например, копия input_example.xlsx или минимальный валидный .xlsx). |
| `tests/fixtures/expected/` | Эталонный выход или ожидаемые фрагменты по листам для сравнения. |
| `tests/unit/` | Модульные тесты: validators, normalizer, type_classifier, enricher, summary calculator, каждый sheet builder. |
| `tests/integration/` | Интеграционный тест полного `generate_report()` на фикстурном входе. |

### Корень проекта
| Файл | Назначение |
|------|------------|
| `pyproject.toml` | Зависимости (Python 3.11+), uv/poetry, pytest, ruff, точки входа (streamlit run app.ui.main). |
| `README.md` | Описание проекта, как запустить локально, как запустить тесты. |
| `.env.example` | Пример переменных: APP_ENV, LOG_LEVEL, STREAMLIT_SERVER_PORT, DEFAULT_CABINET_NAME. |

---

## 5. Важные замечания

- **Excel-примеры:** Структуру колонок и листов из `input_example.xlsx` и `expected_report.xlsx` нужно перенести в конфиги в Фазе 0; без этого маппинг и layout будут предположительными.
- **Open Questions (project_rules §18):** Имя входного листа, список обязательных колонок, точный состав колонок по каждому выходному листу, правило расчёта расхода для Сводная, имя итогового файла — на время MVP можно зафиксировать по примерам и позже уточнить.
- **Код не пишем до подтверждения:** Реализация по этому плану и структуре — после вашего подтверждения.

Если нужно, могу сузить план под «минимальный первый срез» (например, только один лист и валидация) или расширить описания конкретных файлов.
