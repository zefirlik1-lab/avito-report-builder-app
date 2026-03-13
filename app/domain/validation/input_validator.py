"""Валидация входного Excel-файла перед обработкой."""

from pathlib import Path

from app.application.exceptions import (
    EmptyFileError,
    InvalidFileTypeError,
    RequiredColumnsMissingError,
    RequiredSheetMissingError,
)
from app.domain.transformations.normalizer import normalize_headers
from app.infrastructure.config.loader import load_input_schema
from app.infrastructure.excel.reader import get_sheet_names


def validate_input_file(
    content: bytes,
    filename: str,
    configs_dir: Path | None = None,
) -> None:
    """
    Проверяет файл: расширение .xlsx, не пустой, читаемость,
    наличие обязательного листа и обязательных колонок.
    При ошибке выбрасывает доменное исключение.
    """
    if not filename.lower().endswith(".xlsx"):
        raise InvalidFileTypeError(message=f"Ожидается .xlsx, получено: {filename}")
    if not content or len(content) == 0:
        raise EmptyFileError()
    schema = load_input_schema(configs_dir)
    sheet_name = schema.get("source_sheet_name") or "Sheet1"
    try:
        names = get_sheet_names(content)
    except EmptyFileError:
        raise
    except Exception as e:
        from app.application.exceptions import BrokenExcelError
        raise BrokenExcelError(
            message="Файл не удаётся прочитать как Excel",
            details={"error": str(e)},
        ) from e
    if sheet_name not in names:
        raise RequiredSheetMissingError(
            message=f"Лист «{sheet_name}» не найден",
            details={"available_sheets": names},
        )
    required = schema.get("required_columns") or []
    if not required:
        return
    from app.infrastructure.excel.reader import read_sheet_from_bytes
    header_row = schema.get("header_row", 1)
    df = read_sheet_from_bytes(content, sheet_name, header_row=header_row)
    # Сравниваем по нормализованным заголовкам (как в normalizer)
    actual_normalized = {normalize_headers(str(c)) for c in df.columns}
    missing = [c for c in required if normalize_headers(str(c)) not in actual_normalized]
    if missing:
        raise RequiredColumnsMissingError(
            message=f"Отсутствуют обязательные колонки: {', '.join(missing)}",
            details={"missing": missing, "actual_columns": list(df.columns)},
        )
