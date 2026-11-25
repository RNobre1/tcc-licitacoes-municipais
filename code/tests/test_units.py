import ast
from pathlib import Path

from ingestion.models import PublicItem
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


def test_public_item_has_a_persisted_normalized_unit_column():
    field = PublicItem._meta.get_field("unit_normalized")

    assert field.max_length == 50
    assert field.default == ""


_CASE_OR_SPACE_METHODS = {
    "strip",
    "lstrip",
    "rstrip",
    "lower",
    "upper",
    "casefold",
    "capitalize",
    "title",
    "swapcase",
}


def _has_measurement_name(expression):
    for node in ast.walk(expression):
        names = []
        if isinstance(node, ast.Name):
            names.append(node.id)
        elif isinstance(node, ast.Attribute):
            names.append(node.attr)
        if any("unit" in name.casefold() or "unidade" in name.casefold() for name in names):
            return True
    return False


def _is_canonical_measurement(expression):
    if isinstance(expression, ast.Attribute) and expression.attr.casefold() == "unit_normalized":
        return True
    if isinstance(expression, ast.Name) and expression.id.casefold().endswith("unit_normalized"):
        return True
    if isinstance(expression, ast.Call):
        function = expression.func
        if isinstance(function, ast.Name) and function.id == "normalize_unit":
            return True
        if isinstance(function, ast.Attribute) and function.attr == "normalize_unit":
            return True
    return False


def _source_violations(source, filename):
    tree = ast.parse(source, filename=filename)
    violations = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            function = node.func
            method_name = None
            expressions = list(node.args) + [keyword.value for keyword in node.keywords]
            if isinstance(function, ast.Attribute):
                method_name = function.attr
                expressions.append(function.value)
            elif isinstance(function, ast.Name):
                method_name = function.id

            if method_name in _CASE_OR_SPACE_METHODS and any(
                _has_measurement_name(expression) for expression in expressions
            ):
                violations.append(
                    f"{filename}:{node.lineno}: inline {method_name} on unit expression"
                )

        if isinstance(node, ast.Compare):
            compared = [node.left, *node.comparators]
            for operator, left, right in zip(node.ops, compared[:-1], compared[1:], strict=True):
                if not isinstance(operator, (ast.Eq, ast.NotEq)):
                    continue
                if not (_has_measurement_name(left) and _has_measurement_name(right)):
                    continue
                if _is_canonical_measurement(left) and _is_canonical_measurement(right):
                    continue
                violations.append(f"{filename}:{node.lineno}: raw unit equality comparison")

    return violations


def test_ast_guard_detects_inline_normalization_and_raw_comparisons():
    source = """
def compare_items(item, candidate, unit_name):
    key = item.unit.strip().casefold()
    return candidate_unit != item_unit and key
"""

    violations = _source_violations(source, "example.py")

    assert len(violations) == 3
    assert any("strip" in violation for violation in violations)
    assert any("casefold" in violation for violation in violations)
    assert any("equality comparison" in violation for violation in violations)


def test_ast_guard_allows_collection_names_headers_and_environment():
    source = """
def normalize_configuration(collection_name, headers, environment):
    name = collection_name.strip("_").lower()
    header = headers["X-Unit"].strip().lower()
    return name, header, environment.strip()
"""

    assert _source_violations(source, "example.py") == []


def test_ast_guard_allows_canonical_measurement_comparisons():
    source = """
def same_measurement(item, candidate):
    return (
        item.unit_normalized == candidate.unit_normalized
        and normalize_unit(item.unit) == normalize_unit(candidate.unit)
    )
"""

    assert _source_violations(source, "example.py") == []


def test_ast_guard_rejects_noncanonical_comparisons():
    source = """
def same_measurement(item, candidate):
    return item.unit == candidate.unit_normalized
"""

    violations = _source_violations(source, "example.py")

    assert len(violations) == 1
    assert "equality comparison" in violations[0]


def test_ast_guard_rejects_duplicate_normalization_in_codebase():
    code_dir = Path(__file__).resolve().parent.parent
    violations = []

    for py_file in code_dir.rglob("*.py"):
        rel_path = py_file.relative_to(code_dir).as_posix()
        if rel_path == "ingestion/units.py":
            continue
        if ".venv" in rel_path:
            continue

        violations.extend(_source_violations(py_file.read_text(encoding="utf-8"), rel_path))

    assert not violations, (
        "Found noncanonical unit normalization or comparisons outside ingestion/units.py:\n"
        + "\n".join(violations)
    )
