# Architecture Overview

This document describes the structure of the **Assaying Anomalies**
Python library and the design principles followed during the
translation from MATLAB.  The goal of the port has been to
preserve the functionality of the original toolkit while adopting
idiomatic Python patterns, explicit inputs/outputs and modular
organisation.

## Package layout

The core code lives under the `aa` package and is organised into
subpackages corresponding to functional domains.  A high‑level
overview:

| Module | Responsibilities |
|-------|------------------|
| `aa.signals` | Compute anomaly signals from raw data.  Each function accepts a `DataFrame` with the necessary input variable(s) and returns a `DataFrame` with columns `date`, `permno` and `signal`.  Signals include size, book‑to‑market, momentum, investment and profitability. |
| `aa.asset_pricing` | Portfolio sorting and asset pricing utilities.  Contains implementations of univariate sorts (`univariate_sort`), double sorts (`double_sort` and `double_sorts`), two‑pass Fama–MacBeth regressions (`fama_macbeth`), factor tests and characteristic‑managed portfolios. |
| `aa.analysis` | Tools for evaluating anomaly performance.  Provides functions to compute mean returns, t‑statistics, Sharpe ratios, drawdowns and turnover, and higher‑level pipelines that evaluate multiple signals and rank them. |
| `aa.prep` | Data preparation routines.  Functions like `crsp.py` and `compustat.py` load raw CRSP/Compustat data, apply filters and create consistent panels.  `build_panel.py` merges returns and fundamentals into a unified DataFrame.  `linktables.py` handles link mapping between CRSP and Compustat identifiers. |
| `aa.pipeline` | High‑level orchestration scripts.  `run_anomaly_library.py` and `run_size_pipeline.py` drive the end‑to‑end workflow: reading prepared data, computing signals, running portfolio sorts or regressions, and generating output tables and figures. |
| `aa.reporting` | Generation of publication‑quality tables for the library.  Modules like `paper_tables.py`, `anomaly_tables.py` and `library_tables.py` produce LaTeX/CSV/Markdown summaries consistent with the original MATLAB documentation.  `export_utils.py` centralises export logic. |
| `aa.vis` | Plotting functions.  Provides routines to reproduce the figures from the paper (e.g. cumulative return plots) using `matplotlib`/`seaborn`. |
| `aa.validation` | Reproducibility and parity checks.  Modules such as `output_consistency.py` and `matlab_parity.py` compare Python results to published figures or MATLAB outputs, ensuring the port is correct. |
| `aa.util` | Helper functions for dates, experiment reproducibility, ID generation and logging. |
| `aa.export` | Replication helpers.  Contains scripts to re‑generate tables and figures from intermediate results. |

Outside of `aa`, the repository includes:

* `examples/` – illustrative scripts that generate synthetic data, compute signals, perform sorts and regressions, and showcase the API.
* `scripts/` – command‑line entry points that orchestrate the full library replication.  They parse arguments, call into `aa.pipeline` and write results to disk.
* `tests/` – an extensive test suite ported from MATLAB verification scripts.  It ensures that every translated function produces the same outputs as its MATLAB counterpart for a range of synthetic inputs.
* `docs/` – documentation including this architecture overview, a translation completion report and a usage guide.

## Design philosophy

Several guiding principles shaped the translation:

1. **Functional fidelity** – the primary objective is to replicate the behaviour of the MATLAB library.  When in doubt, the Python functions return the same values as their MATLAB equivalents, even if alternative vectorised implementations exist.
2. **Explicit inputs and outputs** – unlike MATLAB scripts that operate on global variables, each function in the Python library accepts all required data as arguments and returns results explicitly.  This improves readability and composability.
3. **DataFrame‑centric operations** – portfolio assignments and regressions are implemented using pandas `DataFrame` operations.  GroupBys and merges replace MATLAB loops and matrix indexing.
4. **Modularity** – functionality is decomposed into small, purpose‑specific modules.  This makes the code easier to test and allows researchers to reuse individual pieces (e.g. univariate sorts or Fama–MacBeth regressions) in isolation.
5. **Reproducibility** – functions avoid non‑deterministic behaviour unless explicitly seeded.  The `aa.util.reproducibility` module sets global seeds for NumPy and pandas, and `aa.validation` provides tools to check equality of outputs across versions.
6. **Extensibility** – although the port aims to mirror the MATLAB toolkit, the Python architecture is open to future extensions.  For example, additional anomaly signals can be added to `aa.signals`, and new evaluation metrics can be registered in `aa.analysis.anomaly_metrics` without breaking existing code.

## Interactions between modules

The typical workflow is:

1. **Data preparation** – use `aa.prep` to read CRSP and Compustat data, merge them via link tables and construct a monthly panel with returns and fundamentals.
2. **Signal computation** – call functions in `aa.signals` to compute anomaly predictors from the prepared panel.
3. **Portfolio sorting** – feed the returns and signals into `aa.asset_pricing.univariate_sort` or `aa.asset_pricing.double_sort` to obtain time‑series of portfolio returns and high‑minus‑low spreads.
4. **Evaluation** – use `aa.analysis.anomaly_metrics` to compute statistics for each portfolio or call `aa.analysis.anomaly_pipeline.evaluate_signals` to evaluate multiple signals at once.
5. **Reporting** – generate tables and figures with `aa.reporting`.  For example, `paper_tables.py` reproduces tables identical to those in the original MATLAB documentation.
6. **Replication** – run the scripts in `scripts/` to reproduce the entire anomaly library on real data.  These scripts orchestrate the previous steps and save outputs to disk.

Throughout these steps the modules interact via simple data structures (primarily pandas `DataFrame`s and Python dicts), avoiding implicit state.  This design ensures that the library can serve both as an out‑of‑the‑box tool for researchers and as a foundation for further methodological work.