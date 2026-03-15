"""
Tests for the translation coverage script.

These tests construct temporary MATLAB and Python project structures and
verify that the coverage functions identify translated and missing files
as expected. Only minimal examples are used so that the tests run
quickly.
"""

from __future__ import annotations

from pathlib import Path

from scripts.check_translation_coverage import (
    build_translation_mapping,
    infer_python_stem,
)


def test_infer_python_stem_simple() -> None:
    tmp = Path("dummy")
    assert infer_python_stem(tmp.with_suffix(".m")) == "dummy"


def test_build_translation_mapping(tmp_path: Path) -> None:
    matlab_dir = tmp_path / "matlab"
    python_dir = tmp_path / "python"
    matlab_dir.mkdir()
    python_dir.mkdir()

    mf = matlab_dir / "MyFunction.m"
    mf.write_text("function y = MyFunction(x)\n  y = x;\nend")

    pf = python_dir / "myfunction.py"
    pf.write_text("def myfunction(x):\n    return x")

    mapping, missing = build_translation_mapping([mf], [pf])

    assert mf in mapping
    assert pf in mapping[mf]
    assert not missing


def test_build_translation_mapping_missing(tmp_path: Path) -> None:
    matlab_dir = tmp_path / "matlab"
    python_dir = tmp_path / "python"
    matlab_dir.mkdir()
    python_dir.mkdir()

    mf = matlab_dir / "Unmapped.m"
    mf.write_text("function y = Unmapped(x)\n  y = x;\nend")

    mapping, missing = build_translation_mapping([mf], [])

    assert mf in missing
    assert not mapping
