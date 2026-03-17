#!/usr/bin/env python3
"""
prepare_final_release.py
=======================

This script prepares the repository for its final archived release.  It
performs a verification pass, builds source and wheel distributions,
packages a snapshot of the repository and generates a set of release
notes based on the provided documentation.  The resulting archives
facilitate long‑term preservation of the code and accompanying
materials.

Usage::

    python scripts/prepare_final_release.py --output-dir release

The default output directory is ``release``.  The script assumes it
is being run from the repository root.
"""

from __future__ import annotations

import argparse
import pathlib
import shutil
import subprocess
import sys
import datetime
import textwrap


def run_cmd(cmd: list[str], cwd: pathlib.Path | None = None) -> None:
    """Run a command and raise if it fails."""
    proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(
            f"Command {' '.join(cmd)} failed with exit code {proc.returncode}:\n{proc.stderr}"
        )


def prepare_release(output_dir: pathlib.Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. Run full verification
    verify_script = pathlib.Path("scripts/verify_full_project.py")
    if verify_script.exists():
        print("Running full project verification before release...")
        run_cmd(
            [
                sys.executable,
                str(verify_script),
                "--report",
                str(output_dir / "pre_release_verification.json"),
            ]
        )
    else:
        raise FileNotFoundError(
            "verify_full_project.py not found – aborting release preparation"
        )

    # 2. Build distributions using python -m build, if available
    print("Building source and wheel distributions...")
    try:
        run_cmd(
            [
                sys.executable,
                "-m",
                "build",
                "--sdist",
                "--wheel",
                "--outdir",
                str(output_dir / "dist"),
            ]
        )
    except Exception as exc:
        # If build is not available, skip building and issue a warning
        print(f"WARNING: Failed to build distributions: {exc}")

    # 3. Package a snapshot of the repository (excluding the output directory)
    snapshot_name = (
        f"repository_snapshot_{datetime.datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}"
    )
    snapshot_path = output_dir / f"{snapshot_name}.zip"
    print(f"Creating repository snapshot archive at {snapshot_path}...")
    # Use shutil.make_archive to create a ZIP archive of the current working directory
    # Exclude the output directory itself to avoid recursion
    root_dir = pathlib.Path(".").resolve()

    def _filter(path: pathlib.Path) -> bool:
        # Exclude output_dir and hidden directories like .git
        try:
            # Skip any files inside the output directory or within .git
            return not (output_dir in path.parents or ".git" in path.parts)
        except Exception:
            return True

    # Collect all file paths to include
    paths: list[str] = []
    for item in root_dir.rglob("*"):
        if item.is_file() and _filter(item):
            rel = item.relative_to(root_dir)
            paths.append(str(rel))
    # Create archive
    archive_base = snapshot_path.with_suffix(
        ""
    )  # remove .zip extension for make_archive
    shutil.make_archive(
        str(archive_base), "zip", root_dir=str(root_dir), base_dir=".", verbose=False
    )
    # Move to desired name if necessary
    if archive_base.with_suffix(".zip") != snapshot_path:
        shutil.move(archive_base.with_suffix(".zip"), snapshot_path)

    # 4. Generate release notes combining documentation
    release_notes_path = output_dir / "RELEASE_NOTES.md"
    docs_dir = pathlib.Path("docs")
    notes_parts: list[str] = []
    for doc_name in ["project_completion_report.md", "archival_documentation.md"]:
        doc_path = docs_dir / doc_name
        if doc_path.exists():
            content = doc_path.read_text(encoding="utf-8")
            notes_parts.append(f"## {doc_name}\n\n{content}\n")
    if notes_parts:
        header = textwrap.dedent(
            f"""
            # Release Notes

            This document summarises the final state of the Assaying Anomalies Python translation.  It collates
            the key sections from the archival documentation and the project completion report to provide a
            concise record of the repository at the point of release.  The date of generation is
            {datetime.datetime.utcnow().isoformat()}Z.

            """
        )
        with release_notes_path.open("w", encoding="utf-8") as f:
            f.write(header)
            for part in notes_parts:
                f.write(part)
    else:
        # If documentation is missing, write a minimal placeholder
        release_notes_path.write_text(
            "# Release Notes\n\nNo documentation was found to include in the release notes."
        )

    print(f"Release preparation complete. Files are located in {output_dir}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare final release archive")
    parser.add_argument(
        "--output-dir",
        type=str,
        default="release",
        help="Directory where release artifacts should be written",
    )
    args = parser.parse_args()
    prepare_release(pathlib.Path(args.output_dir))


if __name__ == "__main__":
    main()
