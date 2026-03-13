"""Данные для листа «Админ панель»: Кабинет, Название, Область, Город, Адрес, Номер на Авито, Куда переадресация, ID объявления.

Номер на Авито: телефон во входном файле отсутствует — заполняем пустым.
Область: если «Все регионы» — пусто.
Название и ID объявления: гиперссылки задаются через _url колонки при записи в Excel.
"""

import pandas as pd

from app.domain.models.report_dataset import ReportDataset


def build_admin_sheet(dataset: ReportDataset) -> pd.DataFrame:
    """Собирает таблицу для листа Админ панель (output_structure.md)."""
    df = dataset.df
    if df.empty:
        return pd.DataFrame(columns=[
            "Кабинет Авито", "Название", "Область", "Город", "Адрес",
            "Номер на Авито", "Куда переадресация", "ID объявления",
        ])
    out = pd.DataFrame()
    out["Кабинет Авито"] = df["cabinet_name"] if "cabinet_name" in df.columns else ""
    out["Название"] = df["title"] if "title" in df.columns else ""
    # Область: если "Все регионы" — пустое значение
    region = df["region"] if "region" in df.columns else pd.Series([""] * len(df))
    out["Область"] = region.astype(str).str.strip().replace("Все регионы", "", regex=False)
    out["Город"] = df["city"] if "city" in df.columns else ""
    out["Адрес"] = df["address"] if "address" in df.columns else ""
    out["Номер на Авито"] = df["avito_number_display"] if "avito_number_display" in df.columns else ""
    out["Куда переадресация"] = df["redirect_target"] if "redirect_target" in df.columns else ""
    out["ID объявления"] = df["ad_id"] if "ad_id" in df.columns else ""
    # Гиперссылки: колонки _url использует writer при записи в Excel
    if "title_url" in df.columns:
        out["Название_url"] = df["title_url"].astype(str).replace("nan", "").replace("None", "")
    else:
        out["Название_url"] = ""
    if "ad_id_url" in df.columns:
        out["ID объявления_url"] = df["ad_id_url"].astype(str).replace("nan", "").replace("None", "")
    else:
        out["ID объявления_url"] = ""
    return out
