"""Данные для листа «Диаграмма»: Кабинет Авито, Тип, Название, Адрес, ID объявления."""

import pandas as pd

from app.domain.models.report_dataset import ReportDataset


def build_chart_sheet(dataset: ReportDataset) -> pd.DataFrame:
    """Собирает таблицу для листа Диаграмма (output_structure.md)."""
    df = dataset.df
    if df.empty:
        return pd.DataFrame(columns=[
            "Кабинет Авито", "Тип", "Название", "Адрес", "ID объявления",
        ])
    out = pd.DataFrame()
    out["Кабинет Авито"] = df["cabinet_name"] if "cabinet_name" in df.columns else ""
    out["Тип"] = df["type"] if "type" in df.columns else ""
    out["Название"] = df["title"] if "title" in df.columns else ""
    out["Адрес"] = df["address"] if "address" in df.columns else ""
    out["ID объявления"] = df["ad_id"] if "ad_id" in df.columns else ""
    out["Название_url"] = df["title_url"].astype(str).replace("nan", "").replace("None", "") if "title_url" in df.columns else ""
    out["ID объявления_url"] = df["ad_id_url"].astype(str).replace("nan", "").replace("None", "") if "ad_id_url" in df.columns else ""
    # Для второго блока (расходы по типам) — не выводится в основную таблицу
    out["ad_spend"] = df["ad_spend"] if "ad_spend" in df.columns else 0
    return out
