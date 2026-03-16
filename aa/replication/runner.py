"""
aa.replication.runner
=====================

Functions for executing replication experiments based on YAML configuration
files.  The core function, :func:`run_experiment`, loads a configuration,
prepares data, runs the anomaly pipeline and saves results to the
replication package structure.  It returns a dictionary with the manifest
and other intermediate outputs for inspection and testing.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

import yaml
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from aa.data.synthetic_generator import generate_synthetic_panel
from aa.asset_pricing import SortConfig, univariate_sort, fama_macbeth_full
from aa.util.reproducibility import (
    set_random_seed,
    create_reproducibility_log,
    log_reproducibility_metadata,
)
from aa.util.output_manifest import create_manifest


def _load_config(config_path: str | Path) -> Dict[str, Any]:
    """Load a YAML configuration file and return it as a dictionary."""
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def run_experiment(config_path: str | Path) -> Dict[str, Any]:
    """
    Run a replication experiment defined by a YAML configuration.

    The experiment runner performs the following steps:

    * Reads the configuration file.
    * Seeds all random number generators for deterministic output.
    * Loads or generates the dataset.
    * Applies any signal transformations defined in the config.
    * Performs a univariate portfolio sort.
    * Runs a Fama–MacBeth regression.
    * Writes outputs (tables, figures, metadata, manifest) to disk.
    * Returns a dictionary containing the configuration, manifest and other outputs.

    Parameters
    ----------
    config_path : str or Path
        Path to the YAML configuration file.

    Returns
    -------
    dict
        Dictionary with keys ``config``, ``manifest``, ``outputs``,
        ``sort_result`` and ``fm_result``.
    """
    config = _load_config(config_path)
    # Seed control from config
    seed = config.get("seed")
    if seed is not None:
        set_random_seed(int(seed))
    # Prepare data
    data_cfg: Dict[str, Any] = config.get("data", {})
    if data_cfg.get("source", "").lower() == "synthetic":
        gen_kwargs = {k: v for k, v in data_cfg.items() if k not in {"source"}}
        panel = generate_synthetic_panel(**gen_kwargs)
    else:
        dataset_path = data_cfg.get("path")
        if dataset_path is None:
            raise ValueError(
                "A dataset path must be provided when source != 'synthetic'."
            )
        panel = pd.read_csv(dataset_path, parse_dates=["date"])
    # Ensure basic columns exist
    required_cols = {"date", "permno", "ret"}
    missing = required_cols - set(panel.columns)
    if missing:
        raise KeyError(f"Dataset is missing required columns: {missing}")
    # Handle signals
    signals = config.get("signals", [])
    # If no signals defined, assume the dataset already has a 'signal' column
    if not signals:
        if "signal" not in panel.columns:
            raise KeyError("No signals defined and dataset lacks a 'signal' column.")
    else:
        sig = signals[0]
        col = sig.get("column", "signal")
        if col not in panel.columns:
            raise KeyError(f"Signal column '{col}' not found in dataset.")
        # Create 'signal' column on a copy of panel
        if sig.get("transform") == "log":
            # Replace nonpositive values with nan to avoid -inf from log
            panel["signal"] = np.log(panel[col].replace(0, np.nan))
        else:
            panel["signal"] = panel[col]
    # Create separate DataFrames for the sort
    returns_df = panel[["date", "permno", "ret"]].copy()
    signal_df = panel[["date", "permno", "signal"]].copy()
    size_df = panel[["date", "permno", "me"]].copy() if "me" in panel.columns else None
    exch_df = (
        panel[["date", "permno", "exchcd"]].copy()
        if "exchcd" in panel.columns
        else None
    )
    # Sort configuration
    port_cfg = config.get("portfolio", {})
    sort_config = SortConfig(
        n_bins=int(port_cfg.get("n_bins", 5)),
        nyse_breaks=bool(port_cfg.get("nyse_breaks", False)),
        min_obs=int(port_cfg.get("min_obs", 20)),
    )
    sort_result = univariate_sort(
        returns=returns_df,
        signal=signal_df,
        size=size_df,
        exch=exch_df,
        config=sort_config,
    )
    # Add a time identifier for regressions
    panel = panel.copy()
    if "yyyymm" not in panel.columns:
        panel["yyyymm"] = panel["date"].dt.year * 100 + panel["date"].dt.month
    reg_cfg = config.get("regression", {})
    ycol = reg_cfg.get("y", "ret")
    xcols = reg_cfg.get("xcols", ["signal"])
    time_col = reg_cfg.get("time_col", "yyyymm")
    nw_lags = reg_cfg.get("nw_lags")
    fm_result = fama_macbeth_full(
        panel,
        y=ycol,
        xcols=xcols,
        time_col=time_col,
        nw_lags=nw_lags,
    )
    # Output configuration
    out_cfg = config.get("output", {})
    experiment_name = config.get("experiment_name", "experiment")
    out_dir = Path(out_cfg.get("directory", f"replication/outputs/{experiment_name}"))
    tables_dir = Path(out_cfg.get("tables_dir", "replication/tables"))
    figures_dir = Path(out_cfg.get("figures_dir", "replication/figures"))
    logs_dir = Path(out_cfg.get("logs_dir", "replication/logs"))
    for d in (out_dir, tables_dir, figures_dir, logs_dir):
        d.mkdir(parents=True, exist_ok=True)
    # Save tables
    sort_result["time_series"].to_csv(out_dir / "time_series.csv", index=False)
    sort_result["summary"].to_csv(out_dir / "summary.csv", index=False)
    fm_result["lambdas"].to_csv(out_dir / "lambdas.csv")
    fm_result["lambda_ts"].to_csv(out_dir / "lambda_ts.csv")
    fm_result["se"].to_csv(out_dir / "se.csv")
    fm_result["tstat"].to_csv(out_dir / "tstat.csv")
    fm_result["n_obs"].to_csv(out_dir / "n_obs.csv")
    # Plot summary of equal-weighted returns by bin excluding the L-S row if present
    summary = sort_result["summary"]
    plot_data = summary[summary["bin"] != "L‑S"]
    fig = plt.figure()
    plt.bar(plot_data["bin"].astype(str), plot_data["ret_ew"])
    plt.title(f"{experiment_name} Equal-Weighted Returns by Bin")
    plt.xlabel("Portfolio bin")
    plt.ylabel("Return")
    fig_path = figures_dir / f"{experiment_name}_returns.png"
    plt.tight_layout()
    plt.savefig(fig_path)
    plt.close(fig)
    # Reproducibility metadata: include experiment_id and config hash
    repro_metadata = create_reproducibility_log(config, experiment_name)
    repro_path = logs_dir / f"{experiment_name}_reproducibility.json"
    log_reproducibility_metadata(repro_path, repro_metadata)
    # Create manifest
    output_files = {
        "time_series": str(out_dir / "time_series.csv"),
        "summary": str(out_dir / "summary.csv"),
        "lambdas": str(out_dir / "lambdas.csv"),
        "lambda_ts": str(out_dir / "lambda_ts.csv"),
        "se": str(out_dir / "se.csv"),
        "tstat": str(out_dir / "tstat.csv"),
        "n_obs": str(out_dir / "n_obs.csv"),
        "figure": str(fig_path),
        "reproducibility": str(repro_path),
    }
    manifest = create_manifest(experiment_name, config, output_files)
    # Write manifest to JSON in the output directory
    with open(out_dir / "manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    return {
        "config": config,
        "manifest": manifest,
        "outputs": output_files,
        "sort_result": sort_result,
        "fm_result": fm_result,
    }
