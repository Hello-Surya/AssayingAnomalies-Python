#!/usr/bin/env python3
"""
Repository diagnostics script for Assaying Anomalies.

This utility checks that the codebase is healthy by running the test
suite, verifying imports and ensuring that critical documentation and
environment files are present.  Run this script before submitting a
pull request to catch common issues early.
"""

from __future__ import annotations


import pathlib
import subprocess
import sys
from typing import List


def run_tests() -> bool:
    """Execute the test suite with pytest.  Returns True on success."""
    print("Running pytest…")
    try:
        subprocess.run([sys.executable, "-m", "pytest", "-q"], check=True)
        print("✅ Tests passed")
        return True
    except subprocess.CalledProcessError as exc:
        print(f"❌ Tests failed with exit code {exc.returncode}")
        return False


def check_imports() -> bool:
    """Attempt to import the top‑level package.  Returns True if successful."""
    print("Checking that the package can be imported…")
    try:
        __import__("aa")
        print("✅ Import succeeded")
        return True
    except Exception as e:
        print(f"❌ Failed to import 'aa': {e}")
        return False


def check_files(paths: List[str]) -> bool:
    """Ensure that all paths exist.  Returns True if none are missing."""
    missing: List[str] = []
    for p in paths:
        if not pathlib.Path(p).exists():
            missing.append(p)
    if missing:
        print("❌ Missing required files:")
        for m in missing:
            print(f"   • {m}")
        return False
    print("✅ All required files are present")
    return True


def main(argv: List[str] | None = None) -> int:
    # Define critical files to check
    docs = [
        "docs/data_interface.md",
        "docs/developer_guide.md",
    ]
    env_files = [
        "environment.yml",
        "requirements-dev.txt",
    ]
    ok = True
    if not run_tests():
        ok = False
    if not check_imports():
        ok = False
    if not check_files(docs + env_files):
        ok = False
    if ok:
        print("\n🎉 Repository diagnostics passed.  The project appears to be healthy.")
        return 0
    else:
        print("\n⚠️  Diagnostics found issues.  Please address them before proceeding.")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
