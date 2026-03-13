"""Модель итоговой Excel-книги на экспорт."""

from pydantic import BaseModel


class ReportWorkbook(BaseModel):
    """Итоговая книга отчёта."""

    file_name: str
    sheets: list[str]
    content_bytes: bytes
