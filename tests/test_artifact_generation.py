"""
Tests for research artifact generation and verification scripts.
"""

from __future__ import annotations

import json
import pathlib
import subprocess
import sys

import pytest


@pytest.fixture
def tmp_artifact_dir(tmp_path: pathlib.Path) -> pathlib.Path:
    """Provide a temporary directory for artifact generation."""
    return tmp_path / "artifact"


def run_script(
    script: str, *args: str, cwd: pathlib.Path | None = None
) -> subprocess.CompletedProcess[str]:
    """Run a Python script as a subprocess."""
    return subprocess.run(
        [sys.executable, script, *args],
        cwd=cwd,
        capture_output=True,
        text=True,
    )


def test_verification_script(tmp_path: pathlib.Path) -> None:
    report_path = tmp_path / "report.json"
    proc = run_script(
        "scripts/verify_full_project.py",
        "--report",
        str(report_path),
        "--tmp-dir",
        str(tmp_path / "tmp"),
        "--skip-tests",
    )
    assert proc.returncode == 0, f"Verification script failed: {proc.stderr}"
    assert report_path.exists(), "Report file was not created"
    data = json.loads(report_path.read_text(encoding="utf-8"))
    assert "timestamp" in data, "Report missing timestamp"


def test_build_research_artifact(tmp_artifact_dir: pathlib.Path) -> None:
    proc = run_script(
        "scripts/build_research_artifact.py",
        "--artifact-dir",
        str(tmp_artifact_dir),
    )
    assert proc.returncode == 0, f"Artifact build failed: {proc.stderr}"

    metadata_path = tmp_artifact_dir / "metadata.json"
    manifest_path = tmp_artifact_dir / "manifest.json"

    assert metadata_path.exists(), "Metadata file missing from artifact"
    assert manifest_path.exists(), "Manifest file missing from artifact"

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert (
        "metadata" in manifest and manifest["metadata"]
    ), "Manifest missing metadata entry"
    assert (
        "reports" in manifest and manifest["reports"]
    ), "Manifest missing reports entry"


def test_manifest_and_metadata_contents(tmp_artifact_dir: pathlib.Path) -> None:
    proc = run_script(
        "scripts/build_research_artifact.py",
        "--artifact-dir",
        str(tmp_artifact_dir),
    )
    assert proc.returncode == 0, f"Artifact build failed: {proc.stderr}"

    metadata = json.loads(
        (tmp_artifact_dir / "metadata.json").read_text(encoding="utf-8")
    )
    manifest = json.loads(
        (tmp_artifact_dir / "manifest.json").read_text(encoding="utf-8")
    )

    assert "python_version" in metadata, "Metadata missing python_version"
    assert "timestamp" in metadata, "Metadata missing timestamp"
    assert "tables" in manifest, "Manifest missing tables key"
    assert "figures" in manifest, "Manifest missing figures key"
