#!/usr/bin/env python3
"""
Точка входа: чтение input_example.xlsx → валидация → нормализация по column_mapping →
генерация итогового Excel через generate_report.
Запуск: из корня проекта
  python scripts/run_report.py
  или
  uv run python scripts/run_report.py
"""
import os
import re
from datetime import datetime
from pathlib import Path
import sys

# Корень проекта — родитель каталога scripts
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.application.services.report_generation import generate_report
from app.application.exceptions import ReportBuilderError
from app.infrastructure.config.loader import load_input_schema


DATA_DIR = PROJECT_ROOT / "data"
DEFAULT_INPUT_FILE = DATA_DIR / "input_example.xlsx"
OUTPUT_FILE = DATA_DIR / "output_report.xlsx"


def _find_input_file_and_period() -> tuple[Path, str | None]:
    """
    Ищет входной файл в каталоге data:
    - сначала по шаблону 'Статистика_с_*.xlsx' — берёт самый новый по дате изменения;
    - если не найдено — падает обратно на input_example.xlsx без периода.

    Поддерживаем два формата имени файла:
    1) 'Статистика_с_01.03.2026_по_13.03.2026.xlsx'  (ДД.ММ.ГГГГ)
    2) 'Статистика_с_2026-03-01_по_2026-03-13.xlsx'  (YYYY-MM-DD)

    В обоих случаях период для листа «Сводная» формируется в виде 'ДД.MM - ДД.MM'
    (без года, как в старой логике).
    """
    pattern = "Статистика_с_*.xlsx"
    candidates = sorted(
        DATA_DIR.glob(pattern),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    if candidates:
        input_path = candidates[0]
        name = input_path.name
        period_label: str | None = None
        # Формат 1: ДД.ММ.ГГГГ
        m1 = re.search(r"Статистика_с_(\d{2}\.\d{2}\.\d{4})_по_(\d{2}\.\d{2}\.\d{4})\.xlsx", name)
        if m1:
            start_raw, end_raw = m1.group(1), m1.group(2)
            try:
                s = datetime.strptime(start_raw, "%d.%m.%Y")
                e = datetime.strptime(end_raw, "%d.%m.%Y")
                period_label = f"{s.strftime('%d.%m')} - {e.strftime('%d.%m')}"
            except ValueError:
                period_label = None
        else:
            # Формат 2: YYYY-MM-DD
            m2 = re.search(r"Статистика_с_(\d{4}-\d{2}-\d{2})_по_(\d{4}-\d{2}-\d{2})\.xlsx", name)
            if m2:
                start_raw, end_raw = m2.group(1), m2.group(2)
                try:
                    s = datetime.strptime(start_raw, "%Y-%m-%d")
                    e = datetime.strptime(end_raw, "%Y-%m-%d")
                    period_label = f"{s.strftime('%d.%m')} - {e.strftime('%d.%m')}"
                except ValueError:
                    period_label = None
        return input_path, period_label
    # Фоллбек: старое поведение с input_example.xlsx
    return DEFAULT_INPUT_FILE, None


def main() -> None:
    input_path, period_label = _find_input_file_and_period()
    if not input_path.exists():
        print(f"Входной файл не найден: {input_path}", file=sys.stderr)
        print("Положите input_example.xlsx или файл Статистика_с_*.xlsx в каталог data/ и запустите снова.", file=sys.stderr)
        sys.exit(1)

    content = input_path.read_bytes()
    filename = input_path.name

    # Кабинет Авито: из env DEFAULT_CABINET_NAME или из конфига input_schema.default_cabinet_name
    schema = load_input_schema()
    cabinet_name = os.environ.get("DEFAULT_CABINET_NAME") or schema.get("default_cabinet_name") or ""

    try:
        result = generate_report(
            content,
            filename,
            cabinet_name=cabinet_name,
            period_label=period_label,
        )
        OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT_FILE.write_bytes(result.content_bytes)
        print(f"Отчёт сформирован: {result.file_name}")
        print(f"Сохранён: {OUTPUT_FILE}")
        print(f"Листы: {', '.join(result.sheets)}")
    except ReportBuilderError as e:
        print(f"Ошибка: [{e.code}] {e}", file=sys.stderr)
        if e.details:
            print(f"Детали: {e.details}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
