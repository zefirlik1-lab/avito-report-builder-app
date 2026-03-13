"""Нормализация заголовков и данных к канонической схеме."""

import re
from pathlib import Path
from typing import Any

import pandas as pd

from app.domain.models.report_dataset import ReportDataset
from app.infrastructure.config.loader import load_column_mapping, load_input_schema


def normalize_headers(s: str) -> str:
    """Заменяет неразрывные пробелы на обычные, схлопывает пробелы, strip."""
    if not isinstance(s, str):
        return ""
    s = s.replace("\u00a0", " ").replace("\u202f", " ")
    s = re.sub(r"\s+", " ", s).strip()
    return s


def normalize_dataset(
    df: pd.DataFrame,
    source_sheet_name: str,
    configs_dir: Path | None = None,
) -> ReportDataset:
    """
    Приводит DataFrame к каноническим именам колонок, очищает строки,
    удаляет полностью пустые строки и строки без ad_id и title.
    """
    if df.empty:
        return ReportDataset(pd.DataFrame(), source_sheet_name)
    mapping = load_column_mapping(configs_dir)
    # Нормализуем заголовки и переименовываем
    df = df.copy()
    df.columns = [normalize_headers(str(c)) for c in df.columns]
    rename = {k: v for k, v in mapping.items() if k in df.columns}
    df = df.rename(columns=rename)
    # Строки: strip для object/string
    str_cols = df.select_dtypes(include=["object", "string"]).columns
    for col in str_cols:
        df[col] = df[col].astype(str).str.strip().replace("", None)
    # Удаляем полностью пустые строки
    df = df.dropna(how="all")
    # Пустые ad_id/title заполняем "", чтобы не терять строки (HYPERLINK без кэша → None)
    for col in ("ad_id", "title"):
        if col in df.columns:
            df[col] = df[col].fillna("").astype(str).str.strip().replace("nan", "")
    # Удаляем строки без ad_id и без title (по ТЗ)
    if "ad_id" in df.columns and "title" in df.columns:
        df = df.dropna(subset=["ad_id", "title"], how="all")
    # Числовые колонки: fillna 0 для типичных метрик (список можно вынести в конфиг)
    numeric_candidates = [
        "views", "contacts", "ad_spend", "impressions", "chat_contacts",
        "phone_views", "avg_contact_cost", "views_to_contacts_conversion",
        "favorites", "bonus_spend", "placement_and_target_spend", "promotion_spend",
        "other_spend", "days_on_avito", "phone_and_chat_contacts", "discount_chat_responses",
        "impressions_to_views_conversion", "avg_view_cost",
    ]
    for col in numeric_candidates:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    return ReportDataset(df, source_sheet_name)


def read_and_normalize(
    content: bytes,
    configs_dir: Path | None = None,
) -> ReportDataset:
    """Читает лист из content и возвращает нормализованный ReportDataset."""
    from app.infrastructure.excel.reader import read_sheet_from_bytes
    schema = load_input_schema(configs_dir)
    sheet_name = schema.get("source_sheet_name") or "Sheet1"
    header_row = schema.get("header_row", 1)
    df = read_sheet_from_bytes(content, sheet_name, header_row=header_row)
    return normalize_dataset(df, sheet_name, configs_dir)
