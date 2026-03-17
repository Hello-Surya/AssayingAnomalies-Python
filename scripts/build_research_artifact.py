#!/usr/bin/env python3
"""
build_research_artifact.py
==========================

This script automates the construction of a complete research artifact
bundle for the Assaying Anomalies Python library.
"""

from __future__ import annotations

import argparse
import datetime
import json
import pathlib
import shutil
import subprocess
import sys
import tempfile

from aa.util import artifact_metadata


def run_cmd(cmd: list[str], cwd: pathlib.Path | None = None) -> None:
    """Run a command and raise an exception if it fails."""
    proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(
            f"Command {' '.join(cmd)} failed with code {proc.returncode}:\n{proc.stderr}"
        )


def copy_file(src: pathlib.Path, dest_dir: pathlib.Path) -> pathlib.Path:
    """Copy a file into a directory, preserving the file name."""
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / src.name
    shutil.copy2(src, dest)
    return dest


def build_artifact(artifact_dir: pathlib.Path) -> None:
    artifact_dir.mkdir(parents=True, exist_ok=True)
    tmp_dir_obj = tempfile.TemporaryDirectory()
    tmp_dir = pathlib.Path(tmp_dir_obj.name)

    verification_report_path = tmp_dir / "verification_report.json"
    verify_script = pathlib.Path("scripts/verify_full_project.py")

    if verify_script.exists():
        print("Running verification script...")
        run_cmd(
            [
                sys.executable,
                str(verify_script),
                "--report",
                str(verification_report_path),
                "--tmp-dir",
                str(tmp_dir / "verify_tmp"),
                "--skip-tests",
            ]
        )
    else:
        raise FileNotFoundError(
            "scripts/verify_full_project.py not found – cannot build artifact"
        )

    reports_dir = artifact_dir / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    report_copy = reports_dir / verification_report_path.name
    shutil.copy2(verification_report_path, report_copy)

    replication_runner = pathlib.Path("scripts/run_replication_experiment.py")
    config_path = pathlib.Path("replication/configs/size_anomaly.yaml")
    replication_outputs_dir = pathlib.Path("replication/outputs")

    if replication_runner.exists() and config_path.exists():
        print("Running replication experiment on synthetic data...")
        run_cmd(
            [
                sys.executable,
                str(replication_runner),
                "--config",
                str(config_path),
            ]
        )
    else:
        raise FileNotFoundError(
            "Replication runner or config file missing – cannot run experiment"
        )

    outputs_dest = artifact_dir / "outputs"
    outputs_dest.mkdir(parents=True, exist_ok=True)

    if (replication_outputs_dir / "tables").exists():
        shutil.copytree(
            replication_outputs_dir / "tables",
            outputs_dest / "tables",
            dirs_exist_ok=True,
        )
    if (replication_outputs_dir / "figures").exists():
        shutil.copytree(
            replication_outputs_dir / "figures",
            outputs_dest / "figures",
            dirs_exist_ok=True,
        )
    if (replication_outputs_dir / "logs").exists():
        shutil.copytree(
            replication_outputs_dir / "logs",
            outputs_dest / "logs",
            dirs_exist_ok=True,
        )

    configs_dest = artifact_dir / "configs"
    copy_file(config_path, configs_dest)

    metadata = artifact_metadata.gather_metadata(
        config_file=str(config_path),
        verification_report=report_copy,
    )
    metadata_path = artifact_dir / "metadata.json"
    artifact_metadata.save_metadata(metadata, metadata_path)

    manifest = {
        "tables": (
            sorted(
                [
                    str(p.relative_to(artifact_dir))
                    for p in (outputs_dest / "tables").rglob("*.*")
                ]
            )
            if (outputs_dest / "tables").exists()
            else []
        ),
        "figures": (
            sorted(
                [
                    str(p.relative_to(artifact_dir))
                    for p in (outputs_dest / "figures").rglob("*.*")
                ]
            )
            if (outputs_dest / "figures").exists()
            else []
        ),
        "logs": (
            sorted(
                [
                    str(p.relative_to(artifact_dir))
                    for p in (outputs_dest / "logs").rglob("*.*")
                ]
            )
            if (outputs_dest / "logs").exists()
            else []
        ),
        "configs": [str((configs_dest / config_path.name).relative_to(artifact_dir))],
        "reports": [str(report_copy.relative_to(artifact_dir))],
        "metadata": [str(metadata_path.relative_to(artifact_dir))],
        "generated_at": datetime.datetime.now(datetime.UTC).isoformat(),
    }

    manifest_path = artifact_dir / "manifest.json"
    with manifest_path.open("w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    print(f"Research artifact built successfully at {artifact_dir}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build research artifact bundle")
    parser.add_argument(
        "--artifact-dir",
        type=str,
        default="artifact",
        help="Directory where the artifact should be created",
    )
    args = parser.parse_args()
    artifact_dir = pathlib.Path(args.artifact_dir)
    build_artifact(artifact_dir)


if __name__ == "__main__":
    main()
