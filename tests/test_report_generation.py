"""Интеграционный тест полного pipeline generate_report."""

import io

import pytest
from openpyxl import Workbook

from app.application.exceptions import EmptyFileError, InvalidFileTypeError
from app.application.services.report_generation import generate_report


def _minimal_xlsx_bytes() -> bytes:
    """Минимальный валидный xlsx с листом Sheet1 и обязательными колонками."""
    wb = Workbook()
    ws = wb.active
    ws.title = "Sheet1"
    headers = [
        "Номер объявления", "Город", "Адрес", "Категория", "Название объявления",
        "Сотрудник", "Просмотры", "Контакты", "Написали в чат", "Посмотрели телефон",
        "Средняя цена контакта", "Расходы на объявления",
    ]
    ws.append(headers)
    ws.append(["1", "Москва", "ул. Тест", "Услуги", "Тест", "Иванов", 100, 5, 2, 3, 10.5, 500.0])
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def test_generate_report_returns_workbook():
    content = _minimal_xlsx_bytes()
    result = generate_report(content, "test.xlsx", cabinet_name="Кабинет 1")
    assert result.file_name == "output_report.xlsx"
    assert result.sheets == ["Админ панель", "Диаграмма", "Недельный", "Сводная"]
    assert len(result.content_bytes) > 0


def test_generate_report_rejects_non_xlsx():
    with pytest.raises(InvalidFileTypeError):
        generate_report(b"not excel", "file.csv")


def test_generate_report_rejects_empty_file():
    with pytest.raises(EmptyFileError):
        generate_report(b"", "file.xlsx")
