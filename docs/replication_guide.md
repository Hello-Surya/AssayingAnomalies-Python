# Replication Guide

This guide explains how to use the replication infrastructure provided by the
Assaying Anomalies Python library to reproduce experiments and generate
publishable tables and figures.  The replication package is designed to
mirror the structure commonly required by academic journals for replication
submissions.

## Directory Structure

All replication‑related files live under the top‑level `replication/` directory.
It contains several subdirectories:

- **configs/**: YAML configuration files defining individual experiments.
* **scripts/**: Placeholder for journal conventions.  The actual command‑line wrappers
  used to run experiments and generate summaries live in the top‑level
  `scripts/` directory.  This subdirectory exists so that replication packages
  extracted from this repository comply with common journal submission
  conventions.  See the README in `replication/scripts/` for details.
- **outputs/**: Experiment‑specific folders containing raw results such as CSV
  tables, regression outputs and per‑experiment manifests.
- **tables/**: Consolidated, publication‑ready tables.
- **figures/**: Generated plots and charts.
- **logs/**: JSON files capturing reproducibility metadata for each run.

You should not modify files under `outputs/`, `tables/`, `figures/` or `logs/`
directly; they are managed by the runner.

## Writing a Configuration

An experiment is defined by a YAML file placed in `replication/configs/`.  At
a minimum the file must specify an `experiment_name` and a `data` section.
The `data` section can either reference an existing dataset on disk (`path`)
or instruct the system to generate a synthetic dataset.  Additional sections
configure the portfolio sort and Fama–MacBeth regression.

Example (`replication/configs/size_anomaly.yaml`):

```yaml
experiment_name: size_anomaly
data:
  source: synthetic
  n_periods: 120
  n_stocks: 300
  start_date: "2000-01-31"
  freq: "M"
  seed: 42
signals:
  - name: size
    column: me
    transform: log
portfolio:
  n_bins: 5
  nyse_breaks: false
  min_obs: 20
regression:
  y: ret
  xcols: [signal]
  time_col: yyyymm
  nw_lags: null
output:
  directory: replication/outputs/size_anomaly
  tables_dir: replication/tables
  figures_dir: replication/figures
  logs_dir: replication/logs
seed: 42
```

The top‑level `seed` key overrides any seed specified in the `data` section
and ensures that multiple runs of the same configuration produce identical
results.

## Running an Experiment

Use the runner script to execute a replication experiment:

```bash
python scripts/run_replication_experiment.py --config replication/configs/size_anomaly.yaml
```

The runner will:

1. Read the configuration file.
2. Seed global random number generators.
3. Load or generate the dataset.
4. Apply any signal transformations.
5. Run a univariate portfolio sort.
6. Estimate a Fama–MacBeth regression.
7. Write result tables to `replication/outputs/<experiment_name>/`.
8. Generate a simple bar chart of equal‑weighted returns by portfolio bin.
9. Log reproducibility metadata to `replication/logs/`.
10. Create a manifest describing the experiment and output file locations.

You can inspect the `manifest.json` file in the experiment's output
directory for a machine‑readable record of the run.

## Generating a Summary Report

After running one or more experiments, you can compile a human‑readable
summary using:

```bash
python scripts/generate_replication_summary.py --outputs_dir replication/outputs --output replication/replication_summary.md
```

This script searches for all `manifest.json` files under the specified
`outputs_dir`, aggregates their contents and writes a Markdown report.  The
report lists the experiment names, timestamps, package version, output files
and configuration parameters.

## Reproducibility Controls

Deterministic behaviour is critical for academic replication.  Randomness
is controlled by the `aa.util.reproducibility.set_random_seed` function, which
seeds Python’s `random`, NumPy and optional PyTorch generators.  The runner
automatically seeds these libraries using the `seed` field from your
configuration.

The reproducibility helpers also record metadata such as the Python
version, NumPy and pandas versions and a hash of the configuration.  This
information is saved in the `logs/` directory and included in the manifest
to aid verification.

## Verifying Results

To verify that two runs produced identical results, compare the manifest
files and result tables.  The test suite (`tests/test_replication_runner.py`)
provides examples of how to programmatically assert determinism.  If you
modify the code or configuration, bump the experiment name or update the
seed to distinguish new runs.

For further details on the anomaly pipeline itself, consult the main
documentation in `docs/usage_guide.md` and `docs/architecture.md`.