import sys
from datetime import datetime
from io import BytesIO
from pathlib import Path
import re

import streamlit as st

from app.application.exceptions import ReportBuilderError
from app.application.services.report_generation import generate_report


# Обеспечиваем импорт пакета app при запуске из корня проекта
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def _extract_period_label_from_filename(filename: str) -> str | None:
    """
    Извлекает период из имени файла в одном из форматов:
    1) Статистика_с_01.03.2026_по_13.03.2026.xlsx  (ДД.ММ.ГГГГ)
    2) Статистика_с_2026-03-01_по_2026-03-13.xlsx  (YYYY-MM-DD)

    Возвращает строку в формате 'ДД.ММ - ДД.ММ' или None, если парсинг не удался.
    """
    name = filename or ""

    # Формат 1: ДД.ММ.ГГГГ
    m1 = re.search(r"Статистика_с_(\d{2}\.\d{2}\.\d{4})_по_(\d{2}\.\d{2}\.\d{4})\.xlsx", name)
    if m1:
        start_raw, end_raw = m1.group(1), m1.group(2)
        try:
            s = datetime.strptime(start_raw, "%d.%m.%Y")
            e = datetime.strptime(end_raw, "%d.%m.%Y")
            return f"{s.strftime('%d.%m')} - {e.strftime('%d.%m')}"
        except ValueError:
            return None

    # Формат 2: YYYY-MM-DD
    m2 = re.search(r"Статистика_с_(\d{4}-\d{2}-\d{2})_по_(\d{4}-\d{2}-\d{2})\.xlsx", name)
    if m2:
        start_raw, end_raw = m2.group(1), m2.group(2)
        try:
            s = datetime.strptime(start_raw, "%Y-%m-%d")
            e = datetime.strptime(end_raw, "%Y-%m-%d")
            return f"{s.strftime('%d.%m')} - {e.strftime('%d.%m')}"
        except ValueError:
            return None

    return None


def main() -> None:
    st.title("Avito Report Builder")

    st.markdown("Загрузите Excel-файл статистики Авито (.xlsx), чтобы сформировать отчёт.")

    uploaded_file = st.file_uploader("Файл статистики Авито (.xlsx)", type=["xlsx"])

    cabinet_name = st.text_input(
        "Название кабинета (необязательно)",
        help="Если указано, будет передано в отчёт как название кабинета Авито.",
    )

    generate_clicked = st.button("Сформировать отчёт")

    if generate_clicked:
        if uploaded_file is None:
            st.error("Пожалуйста, выберите файл Excel перед формированием отчёта.")
            return

        input_bytes = uploaded_file.read()
        filename = uploaded_file.name or "input.xlsx"
        period_label = _extract_period_label_from_filename(filename)

        with st.spinner("Формируем отчёт..."):
            try:
                result = generate_report(
                    input_bytes=input_bytes,
                    filename=filename,
                    cabinet_name=cabinet_name or None,
                    period_label=period_label,
                )
            except ReportBuilderError as e:
                msg = f"Ошибка построения отчёта: [{e.code}] {e}"
                st.error(msg)
                if getattr(e, "details", None):
                    st.error(f"Детали: {e.details}")
                return
            except Exception as e:  # noqa: BLE001
                st.error(f"Непредвиденная ошибка: {e}")
                return

        st.success("Отчёт успешно сформирован.")

        st.download_button(
            label="Скачать отчёт Excel",
            data=BytesIO(result.content_bytes),
            file_name=result.file_name,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )


if __name__ == "__main__":
    main()

