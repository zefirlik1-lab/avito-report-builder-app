"""Расчёт сводных метрик: суммы, конверсия, средняя стоимость заявки."""

from datetime import datetime
from typing import Any

import pandas as pd


def _parse_dates(df: pd.DataFrame, date_col: str) -> pd.Series:
    """Парсит колонку дат в datetime; невалидные → NaT."""
    if date_col not in df.columns:
        return pd.Series(dtype="datetime64[ns]")
    return pd.to_datetime(df[date_col], errors="coerce")


def _format_period_ddmm(start: datetime | pd.Timestamp, end: datetime | pd.Timestamp) -> str:
    """Форматирует период в виде «ДД.ММ - ДД.ММ»."""
    if pd.isna(start) or pd.isna(end):
        return ""
    s = start if isinstance(start, datetime) else start.to_pydatetime()
    e = end if isinstance(end, datetime) else end.to_pydatetime()
    return f"{s.strftime('%d.%m')} - {e.strftime('%d.%m')}"


def period_label_from_dataframe(df: pd.DataFrame) -> str:
    """
    Один период по всему датасету: min(first_publish_date) — max(unpublish_date).
    Формат «ДД.ММ - ДД.ММ». Если дат нет — пустая строка.
    """
    start_dates = _parse_dates(df, "first_publish_date").dropna()
    end_dates = _parse_dates(df, "unpublish_date").dropna()
    if start_dates.empty and end_dates.empty:
        return ""
    starts = start_dates.min() if not start_dates.empty else end_dates.min()
    ends = end_dates.max() if not end_dates.empty else start_dates.max()
    return _format_period_ddmm(starts, ends)


def summary_metrics_by_week(df: pd.DataFrame) -> list[tuple[str, dict[str, Any]]]:
    """
    Разбивает датасет по неделям (по first_publish_date), для каждой недели считает метрики.
    Возвращает список (period_label, metrics), period_label в формате «ДД.ММ - ДД.ММ».
    Если дат нет — одна запись с пустым периодом и метриками по всему df.
    """
    date_ser = _parse_dates(df, "first_publish_date")
    if date_ser.notna().sum() == 0:
        return [("", compute_summary_metrics(df))]
    df_copy = df.copy()
    df_copy["_week"] = date_ser.dt.to_period("W")
    result = []
    for period in sorted(df_copy["_week"].dropna().unique()):
        week_df = df_copy.loc[df_copy["_week"] == period].drop(columns=["_week"], errors="ignore")
        start = period.start_time
        end = period.end_time
        label = _format_period_ddmm(start, end)
        result.append((label, compute_summary_metrics(week_df)))
    return result if result else [("", compute_summary_metrics(df))]


def safe_divide(num: float, denom: float) -> float:
    """Деление с защитой от нуля → 0."""
    if denom is None or denom == 0 or (isinstance(denom, float) and pd.isna(denom)):
        return 0.0
    return float(num) / float(denom)


def compute_summary_metrics(df: pd.DataFrame) -> dict[str, Any]:
    """
    Считает по датасету: суммы views, contacts, ad_spend;
    конверсия = contacts * 100 / views;
    средняя стоимость заявки = ad_spend / contacts.
    """
    total_views = float(df["views"].sum()) if "views" in df.columns else 0.0
    total_contacts = float(df["contacts"].sum()) if "contacts" in df.columns else 0.0
    total_ad_spend = float(df["ad_spend"].sum()) if "ad_spend" in df.columns else 0.0
    total_chat = float(df["chat_contacts"].sum()) if "chat_contacts" in df.columns else 0.0
    total_phone = float(df["phone_views"].sum()) if "phone_views" in df.columns else 0.0
    avg_contact_cost = float(df["avg_contact_cost"].mean()) if "avg_contact_cost" in df.columns else 0.0
    conversion = safe_divide(total_contacts * 100, total_views)
    avg_cost_per_contact = safe_divide(total_ad_spend, total_contacts)
    return {
        "views": total_views,
        "contacts": total_contacts,
        "ad_spend": total_ad_spend,
        "chat_contacts": total_chat,
        "phone_views": total_phone,
        "avg_contact_cost": avg_contact_cost,
        "conversion": conversion,
        "avg_cost_per_contact": avg_cost_per_contact,
    }


def build_summary_rows(metrics: dict[str, Any], period_label: str = "") -> list[dict[str, Any]]:
    """
    Формирует строки для листа Сводная.
    Одна строка данных: Неделя (пусто), Период, Просмотры, Конверсия (0..1 для формата %), Контакты, ...
    Имена колонок совпадают с workbook_layout для записи.
    """
    # conversion в метриках уже в процентах (contacts*100/views); для формата % в Excel — доля 0..1
    conversion_pct = metrics.get("conversion", 0) / 100.0
    # Средняя цена контакта: агрегированная стоимость = общие расходы / общие контакты
    # (метрика avg_cost_per_contact), а не среднее по столбцу avg_contact_cost.
    # Расходы на объявления — целые числа (рубли без копеек).
    avg_cost = round(float(metrics.get("avg_cost_per_contact", 0)))
    ad_spend = round(float(metrics.get("ad_spend", 0)))
    row = {
        "Неделя": "",
        "Период": period_label,
        "Просмотры": metrics.get("views", 0),
        "Конверсия из просмотров в контакты": conversion_pct,
        "Контакты": metrics.get("contacts", 0),
        "Средняя цена контакта": avg_cost,
        "Звонки": metrics.get("phone_views", 0),
        "Написали в чат": metrics.get("chat_contacts", 0),
        "Расходы на объявления": ad_spend,
        "Комментарий": "",
    }
    return [row]
