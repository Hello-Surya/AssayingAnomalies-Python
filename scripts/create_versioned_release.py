#!/usr/bin/env python3
"""
Utility for creating a versioned release of the Assaying Anomalies library.

This script bumps the version number in `pyproject.toml`, builds the source
and wheel distributions, packages them into a zip archive and writes a
release notes template.  It provides a reproducible way to prepare new
releases for PyPI and GitHub.

Usage:

```bash
python scripts/create_versioned_release.py --part patch
```

The `--part` argument selects which component of the semantic version to
increment: ``patch`` (default), ``minor`` or ``major``.  A `--dry-run`
option skips writing changes and building artefacts so you can preview
the next version.
"""

from __future__ import annotations

import argparse
import pathlib
import re
import shutil
import subprocess
import sys


def parse_version(pyproject: pathlib.Path) -> str:
    """Extract the current version string from a pyproject.toml file."""
    text = pyproject.read_text(encoding="utf-8")
    match = re.search(
        r"^version\s*=\s*[\"'](\d+\.\d+\.\d+)[\"']", text, flags=re.MULTILINE
    )
    if not match:
        raise ValueError("Could not find version in pyproject.toml")
    return match.group(1)


def bump_version(version: str, part: str) -> str:
    """Increment a semantic version string."""
    major, minor, patch = (int(x) for x in version.split("."))
    if part == "major":
        major += 1
        minor = 0
        patch = 0
    elif part == "minor":
        minor += 1
        patch = 0
    else:
        patch += 1
    return f"{major}.{minor}.{patch}"


def update_pyproject_version(pyproject: pathlib.Path, new_version: str) -> None:
    """Rewrite the version field in pyproject.toml."""
    text = pyproject.read_text(encoding="utf-8")
    new_text = re.sub(
        r"(^version\s*=\s*[\"'])(\d+\.\d+\.\d+)([\"'])",
        rf"\1{new_version}\3",
        text,
        flags=re.MULTILINE,
    )
    pyproject.write_text(new_text, encoding="utf-8")


def build_distributions() -> None:
    """Build source and wheel distributions using `python -m build`."""
    subprocess.run([sys.executable, "-m", "build", "--sdist", "--wheel"], check=True)


def create_archive(version: str) -> pathlib.Path:
    """Archive the contents of the dist/ directory into a zip file."""
    release_dir = pathlib.Path("release")
    release_dir.mkdir(exist_ok=True)
    archive_base = release_dir / f"assaying-anomalies-{version}"
    archive_path = shutil.make_archive(str(archive_base), "zip", root_dir="dist")
    return pathlib.Path(archive_path)


def write_release_notes(version: str, archive_path: pathlib.Path) -> pathlib.Path:
    """Generate a template for release notes with checksum placeholders."""
    notes_dir = pathlib.Path("release")
    notes_dir.mkdir(exist_ok=True)
    notes_file = notes_dir / f"RELEASE_NOTES_{version}.md"
    content = (
        f"# Release {version}\n\n"
        "## Highlights\n\n"
        "- Describe new features, enhancements and bug fixes here.\n\n"
        "## Distribution files\n\n"
        f"Archive: `{archive_path.name}`\n\n"
        "## Checksums\n\n"
        "Compute SHA256 checksums of the files in `dist/` and paste them below.\n"
        "\n``\nTODO: sha256sum dist/*\n``\n"
    )
    notes_file.write_text(content, encoding="utf-8")
    return notes_file


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Create a versioned release")
    parser.add_argument(
        "--part",
        choices=["major", "minor", "patch"],
        default="patch",
        help="Which part of the version number to increment",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Perform a dry run without changing files or building",
    )
    args = parser.parse_args(argv)

    repo_root = pathlib.Path(__file__).resolve().parents[1]
    pyproject = repo_root / "pyproject.toml"
    if not pyproject.exists():
        print("ERROR: pyproject.toml not found in repository root", file=sys.stderr)
        return 1
    current_version = parse_version(pyproject)
    new_version = bump_version(current_version, args.part)
    print(f"Current version: {current_version}\nNew version: {new_version}")
    if args.dry_run:
        return 0
    # Update version
    update_pyproject_version(pyproject, new_version)
    # Build the distributions
    build_distributions()
    # Archive the dist directory
    archive_path = create_archive(new_version)
    # Generate release notes
    notes_file = write_release_notes(new_version, archive_path)
    print(f"Built distributions and archived to {archive_path}")
    print(f"Release notes template written to {notes_file}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
