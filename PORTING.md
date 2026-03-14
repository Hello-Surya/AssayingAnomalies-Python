# Porting of Assaying Anomalies from MATLAB to Python

This document tracks the translation of functions and scripts from the
original MATLAB repository (`velikov‑mihail/AssayingAnomalies`) to the
Python port (`Hello‑Surya/AssayingAnomalies‑Python`).  Each Python
module implements functionality analogous to one or more MATLAB
scripts.  Where exact parity is not feasible due to language
differences, the behaviour has been replicated as closely as possible.

## Existing Translations

Previous milestones implemented the core components of the library:

| MATLAB Function               | Python Module                                 | Notes |
| ----------------------------- | --------------------------------------------- | ----- |
| `runUnivSort.m`               | `aa.asset_pricing.univariate_sort`             | Implements univariate sorts. |
| `runBivSort.m` and related    | `aa.asset_pricing.double_sort` (stub)          | Placeholder; multiple sorting not ported yet. |
| `famaMacBeth.m`               | `aa.asset_pricing.fama_macbeth`                | Implements Fama–MacBeth regressions with Newey–West. |
| `makeSortSummaryTables.m`     | `aa.reporting.tables`                          | Formats univariate results into tables. |
| `makeAnomTables.m`            | `aa.reporting.anomaly_tables`                  | Builds tables from dictionaries of metrics. |
| `makePortDiagnostics.m`       | `aa.analysis.anomaly_metrics`                  | Provides performance metrics such as mean, t‑statistic and Sharpe ratio. |

## Milestone 7 Additions

Milestone 7 completes the translation by reproducing the full anomaly
evaluation pipeline used in the MATLAB library.

| MATLAB Function/Script              | Python Module                                     | Description |
| ----------------------------------- | -------------------------------------------------- | ----------- |
| `makeAnomStratResults.m`            | `aa.analysis.anomaly_pipeline`                    | Evaluates many anomaly signals at once, performing univariate sorts, constructing high‑minus‑low series and computing metrics. |
| `makeAnomTop.m` and ranking scripts | `aa.analysis.anomaly_ranking`                     | Ranks anomalies by chosen metrics, constructs top‑decile lists and computes average ranks across multiple metrics. |
| `runAnomLibrary.m`                  | `aa.pipeline.run_anomaly_library`                 | High‑level driver that runs the entire library on a dataset, produces summary tables and ranks anomalies. Includes a CLI entry point. |
| `makeAnomBenchmarkResults.m`        | `aa.reporting.library_tables`                    | Assembles performance and ranking tables from evaluation outputs and exports to DataFrame, Markdown or LaTeX. |
| `checkFillAnomalies.m`              | `aa.validation.matlab_parity`                    | Provides functions to compare Python outputs against MATLAB references and verify parity within a tolerance. |

## Translation Notes

* **Data structures**: MATLAB cell arrays and structs have been
  replaced with Python dictionaries and `pandas` DataFrames.  All
  functions accept and return `pandas` objects where appropriate.
* **Sorting**: Portfolio sorts use non‑breaking hyphens (`L‑S`) to
  label the long‑short row, matching the MATLAB output.  The
  `SortConfig` class centralises sort parameters.
* **Performance metrics**: The Python implementation computes
  mean return, t‑statistic, Sharpe ratio and maximum drawdown using
  standard formulas.  Small numerical differences may arise due to
  floating‑point precision and differences in default degrees of
  freedom.
* **Ranking**: Rankings are computed using `pandas` rank functions.
  Ties receive the minimum rank (i.e. dense ranking).  Users can
  choose whether larger or smaller metric values are better via the
  `ascending` parameter.
* **CLI support**: The `run_anomaly_library` module defines a
  `main()` function that can be invoked via `python -m
  aa.pipeline.run_anomaly_library` to run the pipeline on a CSV or
  Parquet dataset.
* **Testing**: Synthetic data tests in `aa/tests` verify that the
  evaluation pipeline, ranking utilities, table generation and
  parity checks behave as expected.

Please update this file whenever new modules are added or when
translation details change.