from pathlib import Path

from ingestion.units import normalize_unit


def test_normalize_unit_strips_and_casefolds():
    assert normalize_unit("  UNIDADE  ") == "unidade"
    assert normalize_unit("Caixa com 10") == "caixa com 10"
    assert normalize_unit("MÊS") == "mês"
    assert normalize_unit("KG") == "kg"


def test_normalize_unit_handles_none_and_empty():
    assert normalize_unit(None) == ""
    assert normalize_unit("") == ""
    assert normalize_unit("   ") == ""


def test_guard_no_duplicate_strip_casefold_in_codebase():
    """Guard rule: .strip().casefold() must never be written inline outside ingestion/units.py."""
    code_dir = Path(__file__).resolve().parent.parent
    violations = []
    pattern_1 = ".strip().casefold()"
    pattern_2 = ".casefold().strip()"

    for py_file in code_dir.rglob("*.py"):
        rel_path = py_file.relative_to(code_dir).as_posix()
        # Exempt the units definition module and this test file
        if rel_path in ("ingestion/units.py", "tests/test_units.py"):
            continue
        if ".venv" in rel_path:
            continue

        lines = py_file.read_text(encoding="utf-8").splitlines()
        for lineno, line in enumerate(lines, start=1):
            if pattern_1 in line or pattern_2 in line:
                violations.append(f"{rel_path}:{lineno}: {line.strip()}")

    assert not violations, (
        "Found inline strip/casefold unit normalization outside ingestion/units.py:\n"
        + "\n".join(violations)
    )
