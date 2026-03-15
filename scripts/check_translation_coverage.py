#!/usr/bin/env python3
"""
check_translation_coverage
==========================

This script audits the translation coverage between the original MATLAB
**Assaying Anomalies** library and its Python port.  It scans a MATLAB
source directory for `.m` files and a Python source directory for `.py`
modules, attempts to infer which Python module corresponds to each
MATLAB function, and writes a Markdown report summarising the coverage.

The heuristic used to find a Python equivalent is straightforward: the
`.m` file name (without extension) is converted to lowercase and any
spaces or hyphens are replaced with underscores.  If one or more
Python files share this stem they are considered translations of the
MATLAB function.  All other `.m` files are reported as missing.

The resulting report includes counts of total, translated and missing
MATLAB files along with a list of unmapped names.  This tool is
intended to be run periodically to monitor progress towards full
translation parity.

Example usage::

    python scripts/check_translation_coverage.py \
        --matlab-dir /path/to/AssayingAnomalies/Functions \
        --python-dir /path/to/AssayingAnomalies-Python/aa \
        --output translation_coverage_report.md

The report will be written to the file specified by `--output`.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Dict, Iterable, List, Tuple, Union, DefaultDict
from collections import defaultdict


def list_matlab_files(root: Union[str, Path]) -> List[Path]:
    """Recursively collect all `.m` files under ``root``.

    Parameters
    ----------
    root : str or Path
        Directory to search for MATLAB files.

    Returns
    -------
    List[Path]
        A list of paths to `.m` files.
    """
    root_path = Path(root)
    return [p for p in root_path.rglob("*.m") if p.is_file()]


def list_python_files(root: Union[str, Path]) -> List[Path]:
    """Recursively collect all Python module files under ``root``.

    Test files under an ``aa/tests`` folder are ignored, since they do not
    correspond to MATLAB functions.

    Parameters
    ----------
    root : str or Path
        Directory to search for Python files.

    Returns
    -------
    List[Path]
        A list of paths to `.py` files.
    """
    root_path = Path(root)
    python_files: List[Path] = []
    for p in root_path.rglob("*.py"):
        if p.is_file() and "aa/tests" not in str(p):
            python_files.append(p)
    return python_files


def infer_python_stem(matlab_file: Path) -> str:
    """Derive the expected Python stem name from a MATLAB file name.

    The MATLAB stem is converted to lowercase and spaces and hyphens are
    replaced with underscores.  For example, ``makeDoubleSortInd.m``
    becomes ``makedoublesortind`` which can match a Python module
    ``aa/asset_pricing/makedoublesortind.py`` or the more idiomatic
    ``double_sorts.py`` if present.

    Parameters
    ----------
    matlab_file : Path
        A path to a `.m` file.

    Returns
    -------
    str
        The transformed stem used to search for Python modules.
    """
    stem = matlab_file.stem
    return stem.lower().replace(" ", "_").replace("-", "_")


def build_translation_mapping(
    matlab_files: Iterable[Path], python_files: Iterable[Path]
) -> Tuple[Dict[Path, List[Path]], List[Path]]:
    """Match MATLAB files to Python files based on their stems.

    Parameters
    ----------
    matlab_files : Iterable[Path]
        The MATLAB files to match.
    python_files : Iterable[Path]
        The Python files to search.

    Returns
    -------
    Tuple[Dict[Path, List[Path]], List[Path]]
        A tuple containing:
        - mapping: a dict from MATLAB file Path to a list of matching
          Python Paths
        - missing: a list of MATLAB file Paths with no matches
    """
    py_index: DefaultDict[str, List[Path]] = defaultdict(list)
    for pf in python_files:
        stem = pf.stem.lower()
        py_index[stem].append(pf)

    mapping: Dict[Path, List[Path]] = {}
    missing: List[Path] = []
    for mf in matlab_files:
        target_stem = infer_python_stem(mf)
        matches = []
        # exact stem match
        if target_stem in py_index:
            matches.extend(py_index[target_stem])
        # also search for truncated or partial matches (e.g. makeDoubleSortInd -> double_sorts)
        else:
            for py_stem, pfiles in py_index.items():
                if py_stem.endswith(target_stem) or target_stem.endswith(py_stem):
                    matches.extend(pfiles)
        if matches:
            mapping[mf] = matches
        else:
            missing.append(mf)
    return mapping, missing


def write_report(
    mapping: Dict[Path, List[Path]], missing: List[Path], output_path: Union[str, Path]
) -> None:
    """Write a Markdown report summarising translation coverage.

    Parameters
    ----------
    mapping : Dict[Path, List[Path]]
        Mapping from MATLAB files to corresponding Python files.
    missing : List[Path]
        List of MATLAB files without a Python translation.
    output_path : str or Path
        Destination file path for the report.
    """
    matlab_count = len(mapping) + len(missing)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("# Translation Coverage Report\n\n")
        f.write(f"Total MATLAB files scanned: {matlab_count}\n\n")
        f.write(f"Translated files: {len(mapping)}\n\n")
        f.write(f"Missing translations: {len(missing)}\n\n")
        if missing:
            f.write("## Missing MATLAB files\n\n")
            for mf in sorted(missing, key=lambda p: str(p)):
                f.write(f"- {mf}\n")
            f.write("\n")
        if mapping:
            f.write("## MATLAB to Python mapping\n\n")
            for mf, pfs in sorted(mapping.items(), key=lambda item: str(item[0])):
                py_list = ", ".join(
                    str(p.relative_to(Path.cwd())) if p.is_absolute() else str(p)
                    for p in pfs
                )
                f.write(f"- {mf} -> {py_list}\n")
        f.write("\n")


def main(argv: List[str] | None = None) -> int:
    """Entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description="Generate a translation coverage report between MATLAB and Python repositories."
    )
    parser.add_argument(
        "--matlab-dir",
        required=True,
        help="Path to the root of the MATLAB source (e.g. Functions directory)",
    )
    parser.add_argument(
        "--python-dir",
        required=True,
        help="Path to the root of the Python source (e.g. aa package)",
    )
    parser.add_argument(
        "--output",
        default="translation_coverage_report.md",
        help="Destination for the Markdown report",
    )
    args = parser.parse_args(argv)

    matlab_files = list_matlab_files(args.matlab_dir)
    python_files = list_python_files(args.python_dir)
    mapping, missing = build_translation_mapping(matlab_files, python_files)
    write_report(mapping, missing, args.output)
    print(f"Translation coverage report written to {args.output}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
