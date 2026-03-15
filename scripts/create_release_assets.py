#!/usr/bin/env python3
"""
create_release_assets.py
=======================

This utility script automates the creation of release artefacts for the
Assaying Anomalies Python package.  It performs the following tasks:

1. Builds a source distribution and wheel via `python -m build`.
2. Copies the resulting archives into a user‑specified output
   directory.
3. Creates a ZIP archive containing the source tree and ancillary
   files (examples, notebooks, docs, licence, changelog, etc.).
4. Generates a skeleton release notes file summarising the release.

Run this script from the root of the repository.  It requires the
`build` package (`pip install build`).  Example usage:

    python scripts/create_release_assets.py --version 1.0.0 --output release

This will produce distribution packages in `release/dist/`, a zip
`release/assaying-anomalies-1.0.0.zip` and release notes
`release/release_notes_1.0.0.md`.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path


def build_distributions() -> Path:
    """Invoke the build module to create a wheel and sdist in the `dist/` directory.

    Returns
    -------
    Path
        The path to the `dist/` directory containing the built artefacts.
    """
    # Clean any existing distribution artefacts
    dist_dir = Path("dist")
    if dist_dir.exists():
        shutil.rmtree(dist_dir)
    dist_dir.mkdir(parents=True, exist_ok=True)

    # Build source and wheel distributions.  Use sys.executable to
    # ensure the same interpreter is used regardless of virtualenv.
    subprocess.run([sys.executable, "-m", "build", "--sdist", "--wheel"], check=True)
    return dist_dir


def make_release_zip(version: str, output_dir: Path) -> Path:
    """Create a ZIP archive of the source tree and ancillary files.

    The archive will include top‑level packages (`aa`), documentation,
    examples, notebooks and key text files.  The resulting file is
    named `assaying-anomalies-{version}.zip` in the output directory.

    Parameters
    ----------
    version : str
        The release version number.
    output_dir : Path
        The directory to place the archive in.

    Returns
    -------
    Path
        The path to the created ZIP file.
    """
    zip_name = f"assaying-anomalies-{version}.zip"
    zip_path = output_dir / zip_name
    # Define which paths to include in the archive
    include_paths = [
        Path("aa"),
        Path("scripts"),
        Path("docs"),
        Path("examples"),
        Path("notebooks"),
        Path("LICENSE"),
        Path("CHANGELOG.md"),
        Path("CONTRIBUTING.md"),
        Path("PORTING.md"),
        Path("README.md"),
        Path("pyproject.toml"),
    ]

    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in include_paths:
            if path.is_dir():
                for file in path.rglob("*"):
                    # Skip hidden files and directories (e.g. .pytest_cache)
                    if any(part.startswith(".") for part in file.parts):
                        continue
                    zf.write(file, file)
            elif path.exists():
                zf.write(path, path)
    return zip_path


def write_release_notes(version: str, output_dir: Path) -> Path:
    """Generate a basic release notes file based on the changelog.

    This function extracts the top section of CHANGELOG.md corresponding
    to the specified version and writes it to a separate file.  If
    parsing fails, it writes a templated message instead.

    Parameters
    ----------
    version : str
        The release version number.
    output_dir : Path
        Directory to write the release notes to.

    Returns
    -------
    Path
        Path to the release notes file.
    """
    changelog_path = Path("CHANGELOG.md")
    notes_path = output_dir / f"release_notes_{version}.md"
    try:
        content = changelog_path.read_text(encoding="utf-8")
        # Find the section header for the version
        lines = content.splitlines()
        start_idx = None
        for i, line in enumerate(lines):
            if line.strip().startswith(f"## [{version}]"):
                start_idx = i
                break
        if start_idx is not None:
            # Collect until the next version header or end of file
            end_idx = len(lines)
            for j in range(start_idx + 1, len(lines)):
                if lines[j].startswith("## ["):
                    end_idx = j
                    break
            section = "\n".join(lines[start_idx:end_idx]).strip()
        else:
            section = f"## [{version}]\n\nRelease notes not found in CHANGELOG.md."
    except Exception:
        section = f"## [{version}]\n\nRelease notes could not be extracted."

    header = f"# Release {version}\n\nReleased on {_dt.date.today():%Y-%m-%d}\n\n"
    notes_path.write_text(header + section, encoding="utf-8")
    return notes_path


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build distribution packages and assemble release assets."
    )
    parser.add_argument(
        "--version", required=True, help="Version number of the release (e.g. 1.0.0)"
    )
    parser.add_argument(
        "--output", default="release", help="Output directory for release assets"
    )
    args = parser.parse_args()

    version = args.version
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Building distributions for version {version}...")
    dist_dir = build_distributions()
    # Copy built artefacts to output directory
    out_dist = output_dir / "dist"
    out_dist.mkdir(parents=True, exist_ok=True)
    for artefact in dist_dir.glob("*"):
        shutil.copy(artefact, out_dist)
    print(f"Copied {len(list(dist_dir.iterdir()))} artefact(s) to {out_dist}")

    print("Creating release ZIP archive...")
    zip_path = make_release_zip(version, output_dir)
    print(f"Created archive at {zip_path}")

    print("Generating release notes...")
    notes_path = write_release_notes(version, output_dir)
    print(f"Wrote release notes to {notes_path}")
    print("Release assets prepared successfully.")


if __name__ == "__main__":
    main()
