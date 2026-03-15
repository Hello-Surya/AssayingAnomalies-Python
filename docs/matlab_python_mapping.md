# MATLAB‑to‑Python Module Mapping

This document lists how the major functions and scripts in the original MATLAB
**Assaying Anomalies** library correspond to modules in the Python port.  The
goal of the Python project is strict functional parity: every high‑level MATLAB
routine has a direct analogue written in Python.  The mapping below is not
exhaustive – the MATLAB repository contains a large number of helper
functions – but it covers the primary entry points, data‑processing
components and reporting routines.  When functions are not listed here you
should assume that a Python module exists with a similar name in the
appropriate subpackage (e.g. asset pricing functions live in
`aa/asset_pricing/` and utilities in `aa/util/`).

| MATLAB file | Python module | Purpose |
|-------------|---------------|---------|
| `use_library.m` | `scripts/run_full_library_replication.py`, `scripts/reproduce_assaying_anomalies.py` | Entry point for running the entire anomaly evaluation pipeline on a prepared panel dataset.  The `reproduce_assaying_anomalies.py` script is a thin wrapper for convenience and mirrors the MATLAB function name. |
| `setup_library.m` | `scripts/setup_library.py` | Sets up required data files and environment; downloads and caches CRSP data when run with the appropriate credentials. |
| `makeDoubleSortInd.m` | `aa/asset_pricing/double_sorts.py` | Constructs indicator variables for double‑sorted portfolios.  See `make_double_sort_indices` in the Python module. |
| `runFamaMacBeth.m` | `aa/asset_pricing/fama_macbeth.py` | Implements Fama–MacBeth cross‑sectional regressions with Newey–West standard errors. |
| `paper_tables.m` | `aa/reporting/paper_tables.py` | Produces the publication‑quality tables summarising mean returns, t‑statistics and Sharpe ratios for each anomaly. |
| `paper_figures.m` | `aa/vis/paper_figures.py` | Generates figures comparable to those in the MATLAB code, including cumulative return plots, performance comparisons and return distribution histograms. |
| `export_*` functions | `aa/reporting/export_utils.py` | Centralises all file export operations for tables and figures (CSV, Markdown, LaTeX and PNG). |
| `assignToPtf.m` | `aa/asset_pricing/assign_to_portfolio.py` | Assigns observations to portfolios based on their ranked characteristics.  The Python version returns a `pandas.Series` of portfolio identifiers. |
| `FillMonths.m` | `aa/util/fill_months.py` | Fills missing months in panel data to ensure complete time series. |
| `GRStest_p.m` | `aa/analysis/grs_test.py` | Provides functions to perform the Gibbons–Ross–Shanken test on factor models. |

The general pattern used in the Python translation is to convert MATLAB file
names into snake‑case module names (spaces and capital letters become
underscores and lowercase).  For example `calcGenAlpha.m` becomes
`aa/asset_pricing/calc_gen_alpha.py`.  Helper functions that were defined in
MATLAB as nested or local functions are factored out into separate functions
or methods within the corresponding Python module.

If you are unsure how a particular MATLAB function has been translated,
search for the snake‑case equivalent of the MATLAB file name under the
`aa/` package or consult the unit tests in `aa/tests/`.  If no such file
exists, it may not have been ported yet; use the translation coverage
script (`scripts/check_translation_coverage.py`) to identify any missing
components.