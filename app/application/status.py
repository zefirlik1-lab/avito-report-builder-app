"""Статусы этапов pipeline генерации отчёта."""

from enum import StrEnum


class PipelineStatus(StrEnum):
    """Жизненный цикл генерации отчёта."""

    UPLOADED = "uploaded"
    VALIDATING = "validating"
    VALIDATION_FAILED = "validation_failed"
    READING = "reading"
    NORMALIZING = "normalizing"
    ENRICHING = "enriching"
    BUILDING_SHEETS = "building_sheets"
    WRITING_WORKBOOK = "writing_workbook"
    FORMATTING_WORKBOOK = "formatting_workbook"
    COMPLETED = "completed"
    FAILED = "failed"
