"""Загрузка YAML-конфигов из app/configs с поддержкой запуска через PyInstaller."""

import re
import sys
from pathlib import Path
from typing import Any

import yaml


def _detect_configs_dir() -> Path:
    """
    Определяет каталог конфигов как при запуске из исходников, так и из PyInstaller bundle.

    Приоритет:
    1. app/configs рядом с модулем (исходники / editable install)
    2. <_MEIPASS>/app/configs  (если структура пакета сохранена внутри bundle)
    3. <_MEIPASS>/configs
    """
    here = Path(__file__).resolve()
    candidates: list[Path] = []

    # Исходники / обычная установка: app/configs рядом с модулем
    candidates.append(here.parent.parent.parent / "configs")

    # Запуск из PyInstaller: файлы могут быть распакованы в sys._MEIPASS
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        base = Path(getattr(sys, "_MEIPASS"))
        candidates.append(base / "app" / "configs")
        candidates.append(base / "configs")

    for c in candidates:
        if c.exists():
            return c

    # Если ничего не нашли, возвращаем первый кандидат (для ошибок с понятным путём)
    return candidates[0]


_CONFIGS_DIR = _detect_configs_dir()


def get_configs_dir() -> Path:
    """Возвращает путь к каталогу конфигов."""
    return _CONFIGS_DIR


def load_yaml(name: str, configs_dir: Path | None = None) -> Any:
    """
    Загружает YAML-файл по имени (без расширения или с .yaml).
    Возвращает структуру: dict, list и т.д.
    """
    directory = configs_dir or _CONFIGS_DIR
    path = directory / name if name.endswith(".yaml") else directory / f"{name}.yaml"
    if not path.exists():
        raise FileNotFoundError(f"Config not found: {path}")
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def load_column_mapping(configs_dir: Path | None = None) -> dict[str, str]:
    """Загружает маппинг входных колонок → канонические имена."""
    data = load_yaml("column_mapping", configs_dir)
    return {str(k).strip(): str(v).strip() for k, v in data.items()}


def load_input_schema(configs_dir: Path | None = None) -> dict[str, Any]:
    """Загружает схему входного файла: source_sheet_name, header_row, required_columns."""
    return load_yaml("input_schema", configs_dir)


def load_type_rules(configs_dir: Path | None = None) -> list[dict[str, Any]]:
    """Загружает правила классификации type."""
    data = load_yaml("type_rules", configs_dir)
    rules = data.get("rules") or []
    return [r for r in rules if r.get("enabled", True)]


def _normalize_employee_key(key: str) -> str:
    """Нормализация ключа для поиска: \\xa0→пробел, strip, схлопнуть пробелы, lower."""
    s = str(key).replace("\xa0", " ")
    s = s.strip()
    s = re.sub(r"\s+", " ", s)
    s = s.strip()
    s = s.lower()
    return s


def load_redirect_mapping(configs_dir: Path | None = None) -> dict[str, str]:
    """Загружает маппинг employee → redirect_target. Ключи нормализованы для поиска (lower, без \xa0)."""
    data = load_yaml("redirect_mapping", configs_dir)
    if not isinstance(data, dict):
        return {}
    return {_normalize_employee_key(k): str(v).strip() for k, v in data.items()}


def load_workbook_layout(configs_dir: Path | None = None) -> dict[str, Any]:
    """Загружает layout итоговой книги: sheet_order, sheets, formatting."""
    return load_yaml("workbook_layout", configs_dir)
