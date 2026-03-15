#!/usr/bin/env python3
"""
repository_health_check
=======================

This script performs a basic health check of the Assaying Anomalies
Python repository. It verifies that all modules under the `aa`
package import successfully, confirms that documentation files required
for translation parity exist, and runs the unit tests.
"""

from __future__ import annotations

import argparse
import importlib
import pkgutil
import sys
from pathlib import Path


def check_imports(package: str) -> list[tuple[str, str]]:
    """Attempt to import all submodules of a package."""
    errors: list[tuple[str, str]] = []
    try:
        pkg = importlib.import_module(package)
    except Exception as exc:
        return [(package, str(exc))]

    search_path = pkg.__path__
    for _, modname, _ in pkgutil.walk_packages(path=search_path, prefix=f"{package}."):
        try:
            importlib.import_module(modname)
        except Exception as exc:
            errors.append((modname, str(exc)))
    return errors


def run_tests() -> int:
    """Run the test suite using pytest."""
    try:
        import pytest
    except ImportError:
        print("pytest is not installed; cannot run tests.")
        return 1

    return pytest.main(["-q", "aa/tests"])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Perform repository health checks for the Assaying Anomalies Python port."
    )
    parser.add_argument(
        "--package",
        default="aa",
        help="Top-level package to import (default: aa)",
    )
    parser.add_argument(
        "--docs",
        nargs="*",
        default=["docs/matlab_python_mapping.md", "docs/validation_process.md"],
        help="Documentation files that must exist",
    )
    args = parser.parse_args(argv)

    missing_docs = [doc for doc in args.docs if not Path(doc).exists()]
    if missing_docs:
        print("Missing documentation files:")
        for doc in missing_docs:
            print(f"  - {doc}")
    else:
        print("All required documentation files are present.")

    import_errors = check_imports(args.package)
    if import_errors:
        print("\nImport errors detected:")
        for mod, err in import_errors:
            print(f"  - {mod}: {err}")
    else:
        print("\nAll modules imported successfully.")

    print("\nRunning unit tests...")
    test_result = run_tests()
    if test_result == 0:
        print("All tests passed.")
    else:
        print("Some tests failed. See above for details.")

    return 1 if (missing_docs or import_errors or test_result != 0) else 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
