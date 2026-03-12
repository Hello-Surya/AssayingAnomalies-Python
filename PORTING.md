# Porting Notes: MATLAB to Python

This document captures considerations when porting the original
Assaying Anomalies codebase (implemented in MATLAB) to the
modern Python platform.  Earlier milestones have already
re‑created the statistical logic; Milestone 6 focuses on
translating the remaining core modules.

## High‑level differences

The original MATLAB code relies on dense matrices, implicit
workspaces and ad hoc scripts.  In contrast, the Python
implementation embraces ``pandas`` DataFrames, explicit function
interfaces and reproducible pipelines.  Breakpoint universes are
determined via boolean filters rather than logical indexing, and
vectorised operations replace explicit loops wherever feasible.

## Milestone 6 – Translated modules

This milestone completes the translation of the remaining core
functions from the MATLAB Assaying Anomalies library into Python.
The following table summarises the MATLAB functions and their
corresponding Python modules:

| MATLAB function/script | Python module/function |
|------------------------|------------------------|
| `makeBivSortInd.m`     | :func:`aa.asset_pricing.double_sorts.make_double_sort_ind` |
| `runBivSort.m`         | :func:`aa.asset_pricing.double_sorts.run_double_sort` |
| `calcPtfRets.m`        | Built into ``run_double_sort`` (EW and VW returns) |
| `computeLongShortSeries` (implied) | :func:`aa.asset_pricing.double_sorts.compute_long_short_series` |
| Performance metrics (mean return, Sharpe ratio, drawdowns, turnover) | Functions in :mod:`aa.analysis.anomaly_metrics` |
| Factor regressions (formerly within `runBivSort.m`) | :mod:`aa.asset_pricing.factor_tests` (``regress_against_factors``, ``regress_portfolios``) |
| Anomaly summary tables | :mod:`aa.reporting.anomaly_tables` |
| Helper utilities (`winsorize`, `lag`) | :mod:`aa.util.statistics` |

The Python implementations follow the same algorithms as their
MATLAB counterparts but operate on ``pandas`` DataFrames and Series.
Where MATLAB relied on implicit matrices and workspace state, Python
functions accept and return explicit objects.  High–low series are
returned as separate tables rather than being appended to the summary.