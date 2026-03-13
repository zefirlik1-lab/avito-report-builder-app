#!/usr/bin/env python3
"""Создаёт минимальный data/input_example.xlsx для проверки pipeline (все колонки из column_mapping)."""
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT = PROJECT_ROOT / "data" / "input_example.xlsx"

try:
    from openpyxl import Workbook
except ImportError:
    print("Требуется openpyxl: pip install openpyxl", file=sys.stderr)
    sys.exit(1)


def main() -> None:
    wb = Workbook()
    ws = wb.active
    ws.title = "Sheet1"
    headers = [
        "Номер объявления", "Регион размещения", "Город", "Адрес", "Категория", "Подкатегория",
        "Параметр", "Название объявления", "Цена", "Дата первой публикации", "Дата снятия с публикации",
        "Дней на Авито", "Сотрудник", "Показы", "Конверсия из показов в просмотры", "Просмотры",
        "Средняя цена просмотра", "Конверсия из просмотров в контакты", "Контакты", "Написали в чат",
        "Посмотрели телефон", "Посмотрели телефон и написали в чат", "Откликнулись на скидку в чате",
        "Средняя цена контакта", "Добавили в избранное", "Расходы на объявления",
        "Списано бонусов на объявления", "Расходы на размещение и целевые действия",
        "Расходы на продвижение", "Остальные расходы",
    ]
    ws.append(headers)
    ws.append([
        "12345", "Москва и область", "Москва", "ул. Примерная, 1", "Услуги", "Приём",
        "", "Приём металлолома", "5 000 ₽", "2025-01-01", "2025-02-01", 30,
        "Иванов И.И.", 1000, 0.1, 100, 0.5, 0.02, 5, 2, 3, 1, 0, 10.5, 10,
        500.0, 0, 0, 0, 0,
    ])
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    wb.save(OUTPUT)
    print(f"Создан: {OUTPUT}")


if __name__ == "__main__":
    main()
