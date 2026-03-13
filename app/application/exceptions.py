"""Доменные исключения с кодами ошибок для pipeline."""

from typing import Any


class ReportBuilderError(Exception):
    """Базовое исключение приложения."""

    code: str = "REPORT_BUILD_ERROR"
    message: str = "Ошибка формирования отчёта"

    def __init__(
        self,
        message: str | None = None,
        code: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        self._message = message or self.message
        # Use __dict__ to get class default without triggering property
        default_code = self.__class__.__dict__.get("code", "REPORT_BUILD_ERROR")
        self._code = code if code is not None else (
            default_code if isinstance(default_code, str) else "REPORT_BUILD_ERROR"
        )
        self._details = details or {}
        super().__init__(self._message)

    @property
    def code(self) -> str:
        return self._code

    @property
    def details(self) -> dict[str, Any]:
        return self._details

    def __str__(self) -> str:
        return f"[{self._code}] {self._message}"


class InvalidFileTypeError(ReportBuilderError):
    """Недопустимый тип файла (не .xlsx)."""

    code = "INVALID_FILE_TYPE"
    message = "Разрешён только формат .xlsx"


class EmptyFileError(ReportBuilderError):
    """Файл пустой."""

    code = "EMPTY_FILE"
    message = "Файл пустой"


class BrokenExcelError(ReportBuilderError):
    """Файл повреждён или не читается как Excel."""

    code = "BROKEN_EXCEL"
    message = "Файл не удаётся прочитать как Excel"


class RequiredSheetMissingError(ReportBuilderError):
    """Отсутствует обязательный лист с данными."""

    code = "REQUIRED_SHEET_MISSING"
    message = "Отсутствует обязательный лист с данными"


class RequiredColumnsMissingError(ReportBuilderError):
    """Отсутствуют обязательные колонки."""

    code = "REQUIRED_COLUMNS_MISSING"
    message = "Отсутствуют обязательные колонки"


class DataNormalizationError(ReportBuilderError):
    """Ошибка нормализации или преобразования данных."""

    code = "DATA_NORMALIZATION_ERROR"
    message = "Ошибка нормализации данных"
