#!/usr/bin/env python3
"""
verify_full_project.py
======================

This script performs an end-to-end verification of the Assaying Anomalies
Python translation. It is intended to be run from the repository root.

The verifier checks that:
- the package imports cleanly
- the synthetic data generator runs
- an example anomaly pipeline executes
- a replication experiment can run
- the test suite passes

A machine-readable JSON report summarizing the outcome of each step is
written to disk.
"""

from __future__ import annotations

import argparse
import datetime
import json
import pathlib
import subprocess
import sys
import tempfile
from typing import Any


def run_subprocess(cmd: list[str], cwd: pathlib.Path | None = None) -> dict[str, Any]:
    """Run a subprocess and capture stdout and stderr."""
    proc = subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
    )
    return {
        "returncode": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
        "command": cmd,
    }


def verify_environment(report: dict[str, Any]) -> None:
    """Verify that the package can be imported and reports its version."""
    try:
        import aa

        version = getattr(aa, "__version__", "unknown")
        report["environment"] = {
            "status": "success",
            "aa_version": version,
        }
    except Exception as exc:
        report["environment"] = {
            "status": "failure",
            "error": str(exc),
        }


def verify_synthetic_generator(report: dict[str, Any]) -> None:
    """Verify that the synthetic data generator executes."""
    try:
        from aa.data import synthetic_generator

        panel = synthetic_generator.generate_synthetic_panel()
        report["synthetic_generator"] = {
            "status": "success",
            "rows": len(panel),
            "columns": list(panel.columns),
        }
    except Exception as exc:
        report["synthetic_generator"] = {
            "status": "failure",
            "error": str(exc),
        }


def verify_example_pipeline(report: dict[str, Any]) -> None:
    """Execute the example usage script if it exists."""
    script_path = pathlib.Path("examples/usage_walkthrough.py")
    if not script_path.exists():
        report["example_pipeline"] = {
            "status": "skipped",
            "reason": "examples/usage_walkthrough.py not found",
        }
        return

    result = run_subprocess([sys.executable, str(script_path)], cwd=pathlib.Path("."))
    if result["returncode"] == 0:
        report["example_pipeline"] = {"status": "success"}
    else:
        report["example_pipeline"] = {
            "status": "failure",
            "returncode": result["returncode"],
            "stderr": result["stderr"],
        }


def verify_replication_experiment(
    report: dict[str, Any], tmp_dir: pathlib.Path
) -> None:
    """Run a small replication experiment."""
    runner = pathlib.Path("scripts/run_replication_experiment.py")
    config = pathlib.Path("replication/configs/size_anomaly.yaml")
    outputs_dir = tmp_dir / "replication_outputs"
    outputs_dir.mkdir(parents=True, exist_ok=True)

    if not runner.exists() or not config.exists():
        report["replication_experiment"] = {
            "status": "skipped",
            "reason": "Replication runner or config not found",
        }
        return

    cmd = [
        sys.executable,
        str(runner),
        "--config",
        str(config),
        "--outputs_dir",
        str(outputs_dir),
    ]
    result = run_subprocess(cmd)

    if result["returncode"] == 0:
        tables = (
            list((outputs_dir / "tables").glob("**/*"))
            if (outputs_dir / "tables").exists()
            else []
        )
        figures = (
            list((outputs_dir / "figures").glob("**/*"))
            if (outputs_dir / "figures").exists()
            else []
        )
        report["replication_experiment"] = {
            "status": "success",
            "tables_produced": len(tables),
            "figures_produced": len(figures),
        }
    else:
        report["replication_experiment"] = {
            "status": "failure",
            "returncode": result["returncode"],
            "stderr": result["stderr"],
        }


def verify_tests(report: dict[str, Any]) -> None:
    """Run the test suite using pytest."""
    cmd = [sys.executable, "-m", "pytest", "-q"]
    result = run_subprocess(cmd)
    if result["returncode"] == 0:
        report["tests"] = {"status": "success"}
    else:
        report["tests"] = {
            "status": "failure",
            "returncode": result["returncode"],
            "stdout": result["stdout"],
            "stderr": result["stderr"],
        }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Verify the Assaying Anomalies project"
    )
    parser.add_argument(
        "--report",
        type=str,
        default="verification_report.json",
        help="Path where the JSON report should be saved",
    )
    parser.add_argument(
        "--tmp-dir",
        type=str,
        default=None,
        help="Temporary working directory for intermediate outputs",
    )
    parser.add_argument(
        "--skip-tests",
        action="store_true",
        help="Skip running pytest (useful when called from tests or artifact builders)",
    )
    args = parser.parse_args()

    if args.tmp_dir:
        tmp_dir = pathlib.Path(args.tmp_dir)
        tmp_dir.mkdir(parents=True, exist_ok=True)
    else:
        tmp_dir_obj = tempfile.TemporaryDirectory()
        tmp_dir = pathlib.Path(tmp_dir_obj.name)

    report: dict[str, Any] = {
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }

    verify_environment(report)
    verify_synthetic_generator(report)
    verify_example_pipeline(report)
    verify_replication_experiment(report, tmp_dir)

    if args.skip_tests:
        report["tests"] = {
            "status": "skipped",
            "reason": "skip-tests flag used",
        }
    else:
        verify_tests(report)

    report_path = pathlib.Path(args.report)
    with report_path.open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    successes = [
        k
        for k, v in report.items()
        if isinstance(v, dict) and v.get("status") == "success"
    ]
    failures = [
        k
        for k, v in report.items()
        if isinstance(v, dict) and v.get("status") == "failure"
    ]

    print(f"Verification complete. Successes: {successes}. Failures: {failures}.")

    core_checks = ["environment", "synthetic_generator"]
    if not args.skip_tests:
        core_checks.append("tests")

    core_failures = [
        name for name in core_checks if report.get(name, {}).get("status") == "failure"
    ]

    if core_failures:
        sys.exit(1)


if __name__ == "__main__":
    main()
