# Porting Notes for Assaying Anomalies

This document records the mapping between the original MATLAB
**Assaying Anomalies** library and its Python translation as part of
the porting effort.  It complements the code comments and provides
guidance for developers wishing to understand how the MATLAB
components correspond to their Python counterparts.

## Overview

The goal of this project is a **strict functional replication** of
the MATLAB code in Python.  No new algorithms, models or research
ideas have been introduced.  The Python code follows the same
high‑level workflow: load data, compute anomaly signals, sort into
portfolios, evaluate performance, and produce tables and figures for
publication.  Throughout the porting process the emphasis has been on
maintaining the structure and logic of the MATLAB outputs while
adopting idiomatic Python data structures (primarily `pandas`
`DataFrame`s).

## Mapping between MATLAB and Python

| MATLAB component | Python module/script | Notes |
|------------------|----------------------|-------|
| `use_library.m`  | `scripts/run_full_library_replication.py` and \
`scripts/reproduce_assaying_anomalies.py` | These scripts encapsulate the end‑to‑end workflow of evaluating anomaly signals, ranking anomalies and generating all summary tables and figures.  The `reproduce_assaying_anomalies.py` script simply forwards its arguments to `run_full_library_replication.py` using a subprocess call, so that the entire pipeline can be invoked with a single command. |
| Table generation in MATLAB (`paper_tables.m` and related functions) | `aa/reporting/paper_tables.py` | Provides high‑level functions for assembling performance summaries, long–short statistics, ranking tables, t‑statistics tables and Sharpe ratio tables.  These functions wrap lower‑level utilities in `aa.reporting.library_tables` and operate on dictionaries returned by the evaluation pipeline. |
| Plotting scripts in MATLAB (`paper_figures.m`, etc.) | `aa/vis/paper_figures.py` | Contains functions to create cumulative return plots, performance comparisons, histograms of return distributions and portfolio spread bar charts using `matplotlib`.  The figures mirror those produced by the MATLAB toolkit. |
| Output export routines | `aa/reporting/export_utils.py` | Centralises all file writing for tables and figures.  Tables can be exported to CSV, Markdown or LaTeX via `export_table` and `export_tables`, while figures are saved via `export_figure`. |
| Robustness and large‑scale evaluation scripts | Already implemented in previous milestones | These components were completed in earlier milestones and are reused by the final replication pipeline. |

## Completed translations

All core components of the MATLAB library have been translated to
Python.  This includes:

* The anomaly evaluation pipeline, which handles univariate and
  double sorts, Fama–MacBeth regressions with Newey–West
  adjustments, ranking utilities and a scalable execution
  infrastructure.
* Reporting utilities (`aa/reporting/library_tables.py`), which
  assemble basic performance metrics from the pipeline outputs.
* Paper‑style tables (`aa/reporting/paper_tables.py`) that
  replicate the tables found in the MATLAB documentation.
* Paper‑style figures (`aa/vis/paper_figures.py`) that reproduce
  the plotting functionality of the MATLAB code.
* Export helpers (`aa/reporting/export_utils.py`) that write
  tables and figures to disk in common formats.
* End‑to‑end scripts (`scripts/run_full_library_replication.py` and
  `scripts/reproduce_assaying_anomalies.py`) that drive the entire
  workflow.

## How to run the replication pipeline

To reproduce the MATLAB outputs using the Python implementation,
prepare a panel dataset (CSV or Parquet) containing returns and
fundamental variables.  Then execute the replication script:

```bash
python scripts/run_full_library_replication.py --input my_panel.parquet \
    --signals size value momentum profitability investment \
    --returns ret --size me --exch exchcd --bins 5 \
    --metric mean_ew --output outputs/
```

This command will:

1. Load the panel data and compute the specified anomaly signals.
2. Sort stocks into portfolios and compute high–minus–low spreads.
3. Evaluate each anomaly and rank them according to the chosen
   metric (`mean_ew` by default).
4. Generate the following tables:
   - **Performance summary** (`performance_summary.csv`): mean
     returns, t‑statistics, Sharpe ratios and maximum drawdowns.
   - **Long–short statistics** (`long_short_stats.csv`): mean,
     t‑stat, Sharpe ratio and drawdown for each anomaly's spread.
   - **Ranking table** (`ranking_table.csv`): anomalies sorted by the
     ranking metric with dense ranks.
   - **T‑statistics table** (`t_statistics.csv`): t‑stats for
     equal‑ and value‑weighted spreads.
   - **Sharpe ratios table** (`sharpe_ratios.csv`): Sharpe ratios
     for equal‑ and value‑weighted spreads.
5. Produce four figures in PNG format:
   - `cumulative_returns.png`
   - `performance_comparison.png`
   - `return_distribution.png`
   - `portfolio_spreads.png`

The `scripts/reproduce_assaying_anomalies.py` script is a thin
wrapper around `run_full_library_replication.py` that simply
forwards its arguments.  It exists to mirror the MATLAB
`use_library.m` file and to provide a single‑command reproduction
entry point.  For example:

```bash
python scripts/reproduce_assaying_anomalies.py --input my_panel.parquet \
    --output outputs/
```

will perform the same operations with default settings.

## Contributing

Developers working on further enhancements should consult the
existing module docstrings and unit tests in `aa/tests/` for
additional guidance.  Please ensure that any new code preserves
backwards compatibility with the existing API and does not
introduce new modelling assumptions unless explicitly required by a
future milestone.

## Translation coverage

To monitor progress on the MATLAB‑to‑Python port, a coverage audit
script (`scripts/check_translation_coverage.py`) has been added.  It
recursively scans the MATLAB source tree for `.m` files and the
Python source tree for `.py` modules, attempts to match them using a
simple name transformation (lowercase, underscores replacing spaces
and hyphens) and writes a report summarising the results.  The
generated report lists how many MATLAB files have direct Python
equivalents, and which remain to be translated.  Running this tool
periodically helps ensure no part of the original library is
overlooked.  See `docs/validation_process.md` for details.

## Validation procedures

Deterministic behaviour and reproducibility are crucial for
confidence in the replication.  This milestone introduces two
utility modules – `aa.util.reproducibility` and
`aa.validation.output_consistency` – to support those goals.  The
former centralises random seed initialisation and metadata capture,
while the latter provides functions to compare outputs from separate
runs or against the MATLAB results.  Developers are encouraged to
set a fixed random seed at the start of every experiment and to
record the resulting metadata alongside their outputs.  When
comparing results, the consistency functions will report boolean
success/failure for portfolio returns, anomaly rankings,
Fama–MacBeth regression estimates and summary tables.

## Verifying parity with MATLAB

After running the Python pipeline on a particular dataset, the
resulting tables and figures can be compared against those produced
by the MATLAB scripts.  Export the MATLAB outputs to CSV or another
machine‑readable format, load them into pandas, and apply the
consistency checks provided in `aa.validation.output_consistency`.  If
differences are discovered, they may indicate an error in the
translation or a discrepancy in data preprocessing.  Use the
reporting functions and reproducibility metadata to trace and
diagnose such issues.