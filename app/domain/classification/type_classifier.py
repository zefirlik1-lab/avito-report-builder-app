"""Классификация поля type по заголовку объявления (title)."""

import re
from pathlib import Path
from typing import Any

import pandas as pd

from app.infrastructure.config.loader import load_type_rules

DEFAULT_TYPE = "Не определено"


def _normalize_title(s: Any) -> str:
    """Название для проверки: strip и lower (ТЗ: проверка case-insensitive по подстроке)."""
    if s is None or (isinstance(s, float) and pd.isna(s)):
        return ""
    return str(s).strip().lower()


def classify_type(title: str, rules: list[dict[str, Any]] | None = None) -> str:
    """
    Возвращает тип по правилам: contains, regex, exact.
    При конфликте — правило с большим priority.
    """
    text = _normalize_title(title)
    if rules is None:
        rules = load_type_rules()
    # Сортируем по priority по убыванию (сначала высокий приоритет)
    sorted_rules = sorted(rules, key=lambda r: r.get("priority", 0), reverse=True)
    for rule in sorted_rules:
        if not rule.get("enabled", True):
            continue
        pattern = rule.get("pattern", "")
        match_type = rule.get("match_type", "contains")
        case_sensitive = rule.get("case_sensitive", False)
        if not case_sensitive:
            text_lower = text.lower()
            pattern_check = pattern.lower() if isinstance(pattern, str) else pattern
        else:
            text_lower = text
            pattern_check = pattern
        if match_type == "exact":
            if pattern == "" or text_lower == pattern_check:
                return rule.get("result_type", DEFAULT_TYPE)
        elif match_type == "contains":
            if pattern_check in text_lower:
                return rule.get("result_type", DEFAULT_TYPE)
        elif match_type == "regex":
            try:
                if re.search(pattern, text, re.IGNORECASE if not case_sensitive else 0):
                    return rule.get("result_type", DEFAULT_TYPE)
            except re.error:
                continue
    return DEFAULT_TYPE


def apply_type_column(df: pd.DataFrame, configs_dir: Path | None = None) -> pd.DataFrame:
    """Добавляет колонку type по колонке title. Модифицирует копию DataFrame."""
    df = df.copy()
    rules = load_type_rules(configs_dir)
    if "title" not in df.columns:
        df["type"] = DEFAULT_TYPE
        return df
    df["type"] = df["title"].apply(lambda t: classify_type(t, rules))
    return df
