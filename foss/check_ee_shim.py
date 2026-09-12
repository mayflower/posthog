# ruff: noqa: T201, PLC0415 -- a CLI script that prints its report and boots Django on demand
"""Verify the FOSS ``ee`` shim covers every ``ee`` import that core code makes unconditionally.

Run from the repository root with the shim in place of ``ee/`` (the FOSS image does this at build time):

    python foss/check_ee_shim.py

It parses ``posthog/``, ``products/`` and ``common/`` (tests excluded), classifies each ``ee`` import by
its guard (module level, lazy inside a function, behind ``EE_AVAILABLE``, inside ``try/except ImportError``),
then imports every unconditional and lazy symbol. Missing unconditional symbols fail the check; missing
lazy symbols are reported so a reviewer can decide whether the code path is reachable in the FOSS build.
"""

import ast
import sys
import pathlib
import importlib
from collections import defaultdict

ROOTS = ("posthog", "products", "common")
SKIP = ("/test", "/tests/", "conftest.py", "/eval/", "/evals/", "/benchmarks/", "/dags/")


def guard_of(ancestors: list[ast.AST]) -> str:
    kinds: set[str] = set()
    for node in ancestors:
        if isinstance(node, ast.Try):
            handled = [ast.unparse(h.type) if h.type else "bare" for h in node.handlers]
            if any("ImportError" in h or "ModuleNotFoundError" in h or h in ("Exception", "bare") for h in handled):
                kinds.add("try_import")
        elif isinstance(node, ast.If):
            test = ast.unparse(node.test)
            if "EE_AVAILABLE" in test:
                kinds.add("if_ee")
            elif "TYPE_CHECKING" in test:
                kinds.add("type_checking")
        elif isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            kinds.add("lazy")
    for kind in ("type_checking", "try_import", "if_ee", "lazy"):
        if kind in kinds:
            return kind
    return "unconditional"


def collect() -> dict[str, list[tuple[str, str, str, int]]]:
    found: dict[str, list[tuple[str, str, str, int]]] = defaultdict(list)

    def walk(node: ast.AST, ancestors: list[ast.AST], file: str) -> None:
        for child in ast.iter_child_nodes(node):
            if (
                isinstance(child, ast.ImportFrom)
                and child.module
                and (child.module == "ee" or child.module.startswith("ee."))
            ):
                guard = guard_of([*ancestors, node])
                for alias in child.names:
                    found[guard].append((child.module, alias.name, file, child.lineno))
            walk(child, [*ancestors, node], file)

    for root in ROOTS:
        for path in pathlib.Path(root).rglob("*.py"):
            text = str(path)
            if any(marker in text for marker in SKIP):
                continue
            try:
                walk(ast.parse(path.read_text()), [], text)
            except SyntaxError:
                continue
    return found


# Symbols core imports at module level that the shim leaves out on purpose, with the reason.
INTENTIONALLY_ABSENT = {
    # The management command is Cloud-only; the Temporal workflow that shares this import catches ImportError.
    ("ee.billing.quota_limiting", "update_all_orgs_billing_quotas"),
}


def try_import(module: str, name: str) -> str | None:
    try:
        mod = importlib.import_module(module)
    except ImportError as e:
        return f"module missing ({e})"
    if name == "*" or hasattr(mod, name):
        return None
    try:
        importlib.import_module(f"{module}.{name}")
    except ImportError:
        return "name missing"
    return None


def main() -> int:
    import os

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "posthog.settings")
    import django

    django.setup()
    from django.conf import settings

    found = collect()
    for module in getattr(settings, "CELERY_IMPORTS", []):
        if module.startswith("ee."):
            found["unconditional"].append((module, "*", "posthog/settings/celery.py", 0))
    failures = []
    warnings = []
    for module, name, file, line in sorted(set(found["unconditional"])):
        if module == "ee.settings" or (module, name) in INTENTIONALLY_ABSENT:
            continue  # ee.settings is imported by posthog/settings/__init__.py only when EnterpriseConfig is installed
        problem = try_import(module, name)
        if problem:
            failures.append(f"{module}.{name}: {problem}  <- {file}:{line}")
    for module, name, file, line in sorted(set(found["lazy"])):
        problem = try_import(module, name)
        if problem:
            warnings.append(f"{module}.{name}: {problem}  <- {file}:{line}")
    for module, name, file, line in sorted(set(found["try_import"]) | set(found["if_ee"])):
        if try_import(module, name) is None and module in ("ee.apps", "ee.urls", "ee.settings", "ee.models.license"):
            failures.append(f"{module}.{name} must stay absent so core takes its FOSS branch  <- {file}:{line}")
    print(f"unconditional imports: {len(set(found['unconditional']))}, lazy: {len(set(found['lazy']))}")
    if warnings:
        print("\nLazy imports the shim does not provide (reachable only on enterprise paths):")
        print("\n".join(f"  {w}" for w in warnings))
    if failures:
        print("\nFAIL: the shim is missing symbols that core imports unconditionally:")
        print("\n".join(f"  {f}" for f in failures))
        return 1
    print("\nOK: the FOSS ee shim covers every unconditional import.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
