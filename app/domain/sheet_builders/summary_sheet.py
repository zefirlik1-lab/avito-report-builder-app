"""Данные для листа «Сводная»: строки метрик по периодам, период в формате ДД.ММ - ДД.ММ."""

import pandas as pd

from app.domain.models.report_dataset import ReportDataset
from app.domain.summary.calculator import build_summary_rows, compute_summary_metrics, period_label_from_dataframe


def build_summary_sheet(dataset: ReportDataset, period_label: str = "") -> pd.DataFrame:
    """
    Сводная для MVP: один период на весь датасет (min first_publish — max unpublish).
    Одна строка с метриками по всем данным. Не разбиваем по неделям.
    """
    df = dataset.df
    label = period_label or period_label_from_dataframe(df)
    metrics = compute_summary_metrics(df)
    rows = build_summary_rows(metrics, label)
    return pd.DataFrame(rows)
