#!/usr/bin/env python3
"""
Диагностика колонки «Куда переадресация» (лист Админ панель).
Показывает: что реально читается из Excel, как выглядит после нормализации,
какие ключи в redirect_mapping, почему часть сотрудников не находится.
"""
from pathlib import Path
import sys

# Корень проекта
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.domain.transformations.normalizer import read_and_normalize
from app.infrastructure.config.loader import load_redirect_mapping, load_yaml


def repr_chars(s: str, max_len: int = 80) -> str:
    """Показать строку и коды символов (для поиска \\xa0 и скрытых символов)."""
    if not s:
        return "(пусто)"
    preview = repr(s)
    if len(preview) > max_len:
        preview = preview[: max_len - 3] + "..."
    codes = " ".join(f"{ord(c):04x}" for c in s[:50])
    if len(s) > 50:
        codes += " ..."
    return f"{preview}  |  codes: {codes}"


def main() -> None:
    configs_dir = Path(__file__).resolve().parent.parent / "app" / "configs"
    input_path = Path(__file__).resolve().parent.parent / "data" / "input_example.xlsx"

    print("=" * 70)
    print("1. Ключи в redirect_mapping.yaml (как в файле и после нормализации)")
    print("=" * 70)
    raw_data = load_yaml("redirect_mapping", configs_dir)
    if isinstance(raw_data, dict):
        for k, v in raw_data.items():
            print(f"  В файле: key = {repr(k)}, value = {repr(v)}")
            print(f"           key codes: {' '.join(f'{ord(c):04x}' for c in str(k))}")
    from app.infrastructure.config.loader import _normalize_employee_key
    redirect_map = load_redirect_mapping(configs_dir)
    print("\n  После нормализации (ключи, по которым идёт поиск):")
    for norm_key, val in redirect_map.items():
        print(f"    {repr(norm_key)} -> {repr(val)}")

    print("\n" + "=" * 70)
    print("2. Чтение данных из Excel (read_and_normalize)")
    print("=" * 70)
    content = input_path.read_bytes()
    dataset = read_and_normalize(content, configs_dir=configs_dir)
    df = dataset.df
    if "employee" not in df.columns:
        print("  Колонка 'employee' отсутствует в DataFrame!")
        print("  Доступные колонки:", list(df.columns))
        return
    employees = df["employee"].dropna().astype(str)
    # Уникальные непустые (как есть в DataFrame после нормализатора)
    unique_raw = employees[employees.str.strip() != ""].unique()
    print(f"  Уникальных непустых значений 'employee': {len(unique_raw)}")

    print("\n" + "=" * 70)
    print("3. Значения сотрудника: как приходят из Excel (после normalizer)")
    print("=" * 70)
    for i, raw in enumerate(unique_raw, 1):
        print(f"\n  [{i}] Сырое значение (repr + коды символов):")
        print(f"      {repr_chars(raw)}")

    print("\n" + "=" * 70)
    print("4. Нормализация (как в enricher: \\xa0 -> пробел, strip, lower)")
    print("=" * 70)
    from app.domain.enrichment.enricher import _normalize_employee
    for i, raw in enumerate(unique_raw, 1):
        norm = _normalize_employee(raw)
        in_map = norm in redirect_map
        print(f"\n  [{i}] raw = {repr(raw)[:60]}")
        print(f"      normalized = {repr(norm)}")
        print(f"      в redirect_mapping? {in_map}  ->  redirect = {repr(redirect_map.get(norm, ''))}")

    print("\n" + "=" * 70)
    print("5. Итог: какие ключи маппинга и какие нормализованные значения")
    print("=" * 70)
    print("  Ключи в redirect_map (нормализованные):", sorted(redirect_map.keys()))
    normalized_from_excel = [_normalize_employee(e) for e in unique_raw]
    print("  Нормализованные значения из Excel:", normalized_from_excel)
    print("  Совпадения:", [n for n in normalized_from_excel if n in redirect_map])
    print("  Не найдены:", [n for n in normalized_from_excel if n not in redirect_map])

    print("\n" + "=" * 70)
    print("6. Проверка гипотезы: лишние пробелы / неразрывный пробел ломают совпадение?")
    print("=" * 70)
    test_values = [
        "Канбаров Эмиль",       # один обычный пробел
        "Канбаров  Эмиль",      # два пробела
        "Канбаров\xa0Эмиль",   # неразрывный пробел
        " Канбаров Эмиль ",     # пробелы по краям
    ]
    for tv in test_values:
        norm = _normalize_employee(tv)
        found = norm in redirect_map
        print(f"  raw = {repr(tv):45} -> normalized = {repr(norm):25} в маппинге? {found}")


if __name__ == "__main__":
    main()
