"""
Tests for the replication experiment runner and manifest system.

This module exercises the configuration parser, experiment execution,
manifest recording and deterministic behaviour.  The tests rely on
synthetic data to avoid external dependencies and write all outputs to
temporary directories provided by pytest's ``tmp_path`` fixture.
"""

from __future__ import annotations

from pathlib import Path

import yaml
import pandas as pd

# Ensure the repository root is on the Python path so that the ``aa``
# package can be imported when this test runs in isolation.  Without
# modifying sys.path pytest will not find the local ``aa`` package.
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from aa.replication.runner import run_experiment


def _write_config(config: dict, path: Path) -> None:
    """Helper to write a YAML configuration to disk."""
    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump(config, f)


def test_run_experiment_determinism(tmp_path: Path) -> None:
    """Running the same configuration twice should yield identical outputs."""
    # Construct a minimal configuration using synthetic data and custom output dirs
    output_dir = tmp_path / "outputs" / "exp"
    tables_dir = tmp_path / "tables"
    figures_dir = tmp_path / "figures"
    logs_dir = tmp_path / "logs"
    config_dict = {
        "experiment_name": "test_size",
        "data": {
            "source": "synthetic",
            "n_periods": 6,
            "n_stocks": 20,
            "start_date": "2000-01-31",
            "freq": "M",
            "seed": 123,
        },
        "signals": [
            {
                "name": "size",
                "column": "me",
                "transform": "log",
            }
        ],
        "portfolio": {
            "n_bins": 3,
            "nyse_breaks": False,
            "min_obs": 5,
        },
        "regression": {
            "y": "ret",
            "xcols": ["signal"],
            "time_col": "yyyymm",
            "nw_lags": None,
        },
        "output": {
            "directory": str(output_dir),
            "tables_dir": str(tables_dir),
            "figures_dir": str(figures_dir),
            "logs_dir": str(logs_dir),
        },
        "seed": 123,
    }
    config_file = tmp_path / "config.yaml"
    _write_config(config_dict, config_file)
    # First run
    result1 = run_experiment(config_file)
    # Verify manifest and outputs exist
    manifest1 = result1["manifest"]
    assert manifest1["experiment_name"] == "test_size"
    for path_str in manifest1["outputs"].values():
        assert Path(path_str).exists(), f"Output file {path_str} does not exist"
    # Second run with the same config
    result2 = run_experiment(config_file)
    manifest2 = result2["manifest"]
    # The top-level outputs should be identical in content for deterministic runs
    pd.testing.assert_frame_equal(
        result1["sort_result"]["time_series"], result2["sort_result"]["time_series"]
    )
    pd.testing.assert_frame_equal(
        result1["sort_result"]["summary"], result2["sort_result"]["summary"]
    )
    # Lambdas and other regression outputs should also be equal
    pd.testing.assert_series_equal(
        result1["fm_result"]["lambdas"], result2["fm_result"]["lambdas"]
    )
    pd.testing.assert_series_equal(
        result1["fm_result"]["se"], result2["fm_result"]["se"]
    )
    pd.testing.assert_series_equal(
        result1["fm_result"]["tstat"], result2["fm_result"]["tstat"]
    )
    # Ensure the manifests record the same outputs (paths may differ in timestamp but keys should match)
    assert set(manifest1["outputs"].keys()) == set(manifest2["outputs"].keys())
