"""Модель набора данных после нормализации и обогащения."""

from typing import Any

import pandas as pd


class ReportDataset:
    """Единый нормализованный датасет для построения листов."""

    def __init__(
        self,
        df: pd.DataFrame,
        source_sheet_name: str,
        warnings: list[str] | None = None,
    ) -> None:
        self.df = df
        self.source_sheet_name = source_sheet_name
        self.warnings = list(warnings) if warnings else []

    @property
    def row_count(self) -> int:
        return len(self.df)
