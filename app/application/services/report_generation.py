"""Единая точка входа: генерация отчёта — валидация, чтение, нормализация, листы, экспорт."""

from pathlib import Path

import pandas as pd

from app.application.dto import ReportWorkbook
from app.application.exceptions import ReportBuilderError
from app.domain.enrichment.enricher import enrich_dataset
from app.domain.sheet_builders.admin_sheet import build_admin_sheet
from app.domain.sheet_builders.chart_sheet import build_chart_sheet
from app.domain.sheet_builders.summary_sheet import build_summary_sheet
from app.domain.sheet_builders.weekly_sheet import build_weekly_sheet
from app.domain.transformations.normalizer import read_and_normalize
from app.domain.validation.input_validator import validate_input_file
from app.infrastructure.config.loader import load_workbook_layout
from app.infrastructure.excel.formatter import format_workbook
from app.infrastructure.excel.writer import build_workbook_bytes


def generate_report(
    input_bytes: bytes,
    filename: str,
    cabinet_name: str | None = None,
    configs_dir: Path | None = None,
    period_label: str | None = None,
) -> ReportWorkbook:
    """
    Полный pipeline: валидация → чтение → нормализация → обогащение →
    сборка листов → запись книги → форматирование.
    Возвращает ReportWorkbook с content_bytes для скачивания.
    """
    validate_input_file(input_bytes, filename, configs_dir)
    dataset = read_and_normalize(input_bytes, configs_dir)
    dataset = enrich_dataset(dataset, cabinet_name=cabinet_name, configs_dir=configs_dir)
    layout = load_workbook_layout(configs_dir)
    sheet_order = layout.get("sheet_order") or [
        "Админ панель",
        "Диаграмма",
        "Недельный",
        "Сводная",
    ]
    admin_df = build_admin_sheet(dataset)
    chart_df = build_chart_sheet(dataset)
    weekly_df = build_weekly_sheet(dataset)
    # Если период передан извне (из имени файла), он имеет приоритет над вычисленным по датам.
    summary_df = build_summary_sheet(dataset, period_label=period_label or "")
    sheets_data: dict[str, pd.DataFrame] = {
        "Админ панель": admin_df,
        "Диаграмма": chart_df,
        "Недельный": weekly_df,
        "Сводная": summary_df,
    }
    raw_bytes = build_workbook_bytes(sheets_data, sheet_order=sheet_order, layout=layout)
    content_bytes = format_workbook(raw_bytes, configs_dir=configs_dir)
    # Имя выходного файла фиксировано для MVP
    out_name = "output_report.xlsx"
    return ReportWorkbook(
        file_name=out_name,
        sheets=sheet_order,
        content_bytes=content_bytes,
    )
