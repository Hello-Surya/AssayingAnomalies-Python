# Reproducing the Assaying Anomalies Outputs

This guide explains how to run the Python translation of the
**Assaying Anomalies** library to generate the tables and figures
found in the accompanying paper.  The replication scripts are
designed to mirror the MATLAB workflow exactly, providing a
single‑command entry point that loads your data, computes anomaly
signals, sorts portfolios, evaluates performance and exports all
outputs.

## Prerequisites

1. **Python environment.** The code targets Python 3.8 or later and
   relies on `pandas`, `numpy`, `matplotlib` and other
   dependencies.  It is recommended to install the required packages
   using `pip` or `conda` before running the scripts.
2. **Dataset.** You need a panel dataset (CSV or Parquet) containing
   monthly or quarterly returns and the accounting variables used to
   compute anomaly signals (size, value, momentum, profitability,
   investment, etc.).  The dataset should include at least the
   following columns:

   - `permno` or another firm identifier
   - A date column convertible to a pandas `Period` or `Timestamp`
   - Return series (e.g. `ret` for equal‑weighted returns)
   - Market equity (`me`) for size weighting
   - Exchange code (`exchcd`) if using Compustat/CRSP merges
   - Accounting variables for signals (e.g. `book_to_market`,
     `momentum`, `profitability`)

## Running the replication script

The main entry point is `scripts/run_full_library_replication.py`.
It provides a flexible interface for selecting signals, choosing the
number of portfolios, specifying the return and size columns, and
setting the ranking metric.  A minimal invocation requires only the
input dataset and an output directory:

```bash
python scripts/run_full_library_replication.py --input path/to/panel.parquet --output outputs/
```

This command will evaluate **all** anomaly signals available in the
dataset, rank them according to the equal‑weighted mean return
(`mean_ew`) and export the following items to the `outputs/` directory:

* `performance_summary.csv`: mean returns, t‑statistics, Sharpe
  ratios and maximum drawdowns for each anomaly signal.
* `long_short_stats.csv`: statistics on the high‑minus‑low spreads
  (equal‑ or value‑weighted depending on the `--value_weighted`
  flag).
* `ranking_table.csv`: anomalies sorted by the ranking metric with
  dense ranks.
* `t_statistics.csv`: t‑statistics for equal‑ and value‑weighted
  spreads.
* `sharpe_ratios.csv`: Sharpe ratios for equal‑ and value‑weighted
  spreads.
* Four PNG images visualising cumulative returns, performance
  comparisons, return distributions and portfolio spreads.

### Advanced usage

Several optional flags allow you to customise the evaluation:

* `--signals size value momentum`: evaluate only the specified
  signals (space‑separated list).  By default all signals are
  evaluated.
* `--returns ret`: specify the column name for returns.
* `--size me`: specify the column used for size weighting.
* `--exch exchcd`: specify the exchange code column.
* `--bins 5`: choose the number of portfolios for the sorts.
* `--metric mean_ew`: choose the ranking metric (any scalar metric
  present in the pipeline outputs).
* `--ascending`: rank anomalies in ascending order rather than
  descending (useful if lower values indicate better performance).
* `--format markdown`: export tables in Markdown format instead of
  CSV (options are `csv`, `markdown`, `latex`).
* `--value_weighted`: compute and plot value‑weighted high–minus‑low
  spreads instead of equal‑weighted spreads.

See `python scripts/run_full_library_replication.py --help` for a full
list of options.

## One‑command reproduction

A convenience script, `scripts/reproduce_assaying_anomalies.py`, is
provided to mimic the MATLAB `use_library.m` file.  It simply
forwards its arguments to `run_full_library_replication.py` using the
current Python interpreter.  To reproduce the default outputs:

```bash
python scripts/reproduce_assaying_anomalies.py --input path/to/panel.parquet --output outputs/
```

This will run the entire evaluation pipeline with default settings
(equal‑weighted mean return ranking, five bins) and store the
results in the specified output directory.

## Interpreting the outputs

The exported CSV files can be opened in a spreadsheet program or
read back into Python for further analysis.  The figures are saved
in PNG format and can be included directly in papers or
presentations.  The `export_utils` module also supports writing
tables to Markdown or LaTeX, which is convenient for integration
into academic manuscripts.

If you encounter any issues or discrepancies between the Python and
MATLAB outputs, please refer to `PORTING.md` for mapping details and
open an issue in the repository.  The porting process aims for
one‑to‑one reproducibility, so any deviations should be investigated.