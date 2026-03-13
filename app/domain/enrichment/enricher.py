"""Обогащение датасета: cabinet_name, redirect_target, avito_number_display."""

import re
from pathlib import Path
from typing import Any

import pandas as pd

from app.domain.classification.type_classifier import apply_type_column
from app.domain.models.report_dataset import ReportDataset


def _normalize_employee_for_display(s: Any) -> str:
    """
    Нормализация значения сотрудника для колонки «Куда переадресация»:
    \\xa0→пробел, strip, схлопнуть пробелы, служебные значения NaN/None → пусто.
    """
    if s is None or (isinstance(s, float) and pd.isna(s)):
        return ""
    employee = str(s)
    # Технические значения от pandas/Excel, которые должны интерпретироваться как пустые
    if employee.strip().lower() in {"nan", "none"}:
        return ""
    employee = employee.replace("\xa0", " ")
    employee = employee.strip()
    employee = re.sub(r"\s+", " ", employee)
    employee = employee.strip()
    return employee


def enrich_dataset(
    dataset: ReportDataset,
    cabinet_name: str | None = None,
    configs_dir: Path | None = None,
) -> ReportDataset:
    """
    Добавляет type (по title), cabinet_name, redirect_target, avito_number_display.
    redirect_target = нормализованное значение из колонки «Сотрудник» (без подстановки из mapping).
    """
    df = dataset.df.copy()
    if df.empty:
        df["type"] = []
        df["cabinet_name"] = []
        df["redirect_target"] = []
        df["avito_number_display"] = []
        return ReportDataset(df, dataset.source_sheet_name, dataset.warnings)
    df = apply_type_column(df, configs_dir)
    df["cabinet_name"] = cabinet_name or ""
    if "employee" in df.columns:
        df["redirect_target"] = df["employee"].apply(_normalize_employee_for_display)
    else:
        df["redirect_target"] = ""
    # Номер на Авито: во входном файле нет поля телефона — оставляем пусто (не подставляем ID)
    df["avito_number_display"] = ""
    return ReportDataset(df, dataset.source_sheet_name, dataset.warnings)
