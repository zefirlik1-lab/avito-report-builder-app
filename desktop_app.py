import sys
import re
from datetime import datetime
from pathlib import Path
from typing import Optional

import tkinter as tk
from tkinter import filedialog, messagebox

from app.application.exceptions import ReportBuilderError
from app.application.services.report_generation import generate_report


# Обеспечиваем импорт пакета app при запуске из корня проекта или напрямую этого файла
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def _extract_period_label_from_filename(filename: str) -> Optional[str]:
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


class AvitoReportDesktopApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Avito Report Builder")
        self.root.resizable(False, False)

        self.selected_file_path: Optional[Path] = None

        # Заголовок
        title_label = tk.Label(root, text="Avito Report Builder", font=("Arial", 14, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, padx=10, pady=(10, 5))

        # Кнопка выбора файла
        choose_button = tk.Button(root, text="Выбрать Excel файл", command=self.choose_file)
        choose_button.grid(row=1, column=0, padx=10, pady=5, sticky="w")

        self.file_label_var = tk.StringVar(value="Файл не выбран")
        file_label = tk.Label(root, textvariable=self.file_label_var, anchor="w")
        file_label.grid(row=1, column=1, columnspan=2, padx=10, pady=5, sticky="w")

        # Поле ввода названия кабинета
        cabinet_label = tk.Label(root, text="Название кабинета:")
        cabinet_label.grid(row=2, column=0, padx=10, pady=5, sticky="w")

        self.cabinet_entry = tk.Entry(root, width=40)
        self.cabinet_entry.grid(row=2, column=1, columnspan=2, padx=10, pady=5, sticky="w")

        # Кнопка формирования отчёта
        generate_button = tk.Button(root, text="Сформировать отчет", command=self.generate_report_clicked)
        generate_button.grid(row=3, column=0, padx=10, pady=(10, 10), sticky="w")

    def choose_file(self) -> None:
        filetypes = [("Excel файлы", "*.xlsx"), ("Все файлы", "*.*")]
        path_str = filedialog.askopenfilename(title="Выберите Excel файл статистики Авито", filetypes=filetypes)
        if not path_str:
            return
        self.selected_file_path = Path(path_str)
        self.file_label_var.set(self.selected_file_path.name)

    def generate_report_clicked(self) -> None:
        if not self.selected_file_path:
            messagebox.showerror("Ошибка", "Пожалуйста, сначала выберите Excel файл.")
            return

        try:
            input_bytes = self.selected_file_path.read_bytes()
        except Exception as e:  # noqa: BLE001
            messagebox.showerror("Ошибка чтения файла", f"Не удалось прочитать файл:\n{e}")
            return

        filename = self.selected_file_path.name
        cabinet_name = self.cabinet_entry.get().strip() or None
        period_label = _extract_period_label_from_filename(filename)

        try:
            result = generate_report(
                input_bytes=input_bytes,
                filename=filename,
                cabinet_name=cabinet_name,
                period_label=period_label,
            )
        except ReportBuilderError as e:
            msg = f"Ошибка при формировании отчёта: [{e.code}] {e}"
            if getattr(e, "details", None):
                msg += f"\n\nДетали: {e.details}"
            messagebox.showerror("Ошибка", msg)
            return
        except Exception as e:  # noqa: BLE001
            messagebox.showerror("Ошибка", f"Непредвиденная ошибка:\n{e}")
            return

        # Диалог выбора места сохранения
        save_path_str = filedialog.asksaveasfilename(
            title="Сохранить отчёт как",
            defaultextension=".xlsx",
            filetypes=[("Excel файлы", "*.xlsx")],
            initialfile=result.file_name,
        )
        if not save_path_str:
            # Пользователь отменил сохранение
            return

        try:
            save_path = Path(save_path_str)
            save_path.write_bytes(result.content_bytes)
        except Exception as e:  # noqa: BLE001
            messagebox.showerror("Ошибка сохранения файла", f"Не удалось сохранить файл:\n{e}")
            return

        messagebox.showinfo("Готово", f"Отчёт успешно сохранён:\n{save_path}")


def main() -> None:
    root = tk.Tk()
    app = AvitoReportDesktopApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()

