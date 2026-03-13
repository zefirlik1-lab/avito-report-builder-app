"""Данные для листа «Недельный»: Категория, Адрес, Номер объявления, Тип, метрики."""

import pandas as pd

from app.domain.models.report_dataset import ReportDataset


def build_weekly_sheet(dataset: ReportDataset) -> pd.DataFrame:
    """Собирает таблицу для листа Недельный (output_structure.md)."""
    df = dataset.df
    if df.empty:
        return pd.DataFrame(columns=[
            "Категория", "Адрес", "Номер объявления", "Тип", "Просмотры",
            "Контакты", "Конверсия из просмотров в контакты", "Написали в чат",
            "Посмотрели телефон", "Средняя цена контакта", "Расходы на объявления",
        ])
    out = pd.DataFrame()
    out["Категория"] = df["category"] if "category" in df.columns else ""
    out["Адрес"] = df["address"] if "address" in df.columns else ""
    out["Номер объявления"] = df["ad_id"] if "ad_id" in df.columns else ""
    out["Номер объявления_url"] = df["ad_id_url"].astype(str).replace("nan", "").replace("None", "") if "ad_id_url" in df.columns else ""
    out["Тип"] = df["type"] if "type" in df.columns else ""
    out["Просмотры"] = df["views"] if "views" in df.columns else 0
    out["Контакты"] = df["contacts"] if "contacts" in df.columns else 0
    out["Конверсия из просмотров в контакты"] = df["views_to_contacts_conversion"] if "views_to_contacts_conversion" in df.columns else 0.0
    out["Написали в чат"] = df["chat_contacts"] if "chat_contacts" in df.columns else 0
    out["Посмотрели телефон"] = df["phone_views"] if "phone_views" in df.columns else 0
    out["Средняя цена контакта"] = df["avg_contact_cost"] if "avg_contact_cost" in df.columns else 0.0
    out["Расходы на объявления"] = df["ad_spend"] if "ad_spend" in df.columns else 0.0
    return out
