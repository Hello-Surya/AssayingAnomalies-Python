# Usage Guide

This document provides a practical walkthrough of how to use the
**Assaying Anomalies** Python library to compute anomaly signals,
construct portfolios and run cross‑sectional regressions.  The focus is on
demonstrating the high‑level API on synthetic data; for a
production‑scale analysis you would replace the toy inputs with
CRSP/Compustat data.

## Prerequisites

The library depends on Python ≥ 3.9 and standard scientific
packages.  After cloning the repository, install it in editable mode:

```bash
git clone https://github.com/Hello‑Surya/AssayingAnomalies‑Python.git
cd AssayingAnomalies‑Python
pip install -e .
```

Editable installation allows you to run the examples and inspect the
source.  To install development dependencies (e.g. for testing and
linting) run `pip install -r requirements.txt`.

## Preparing data

Portfolio sorts and regressions require a panel of monthly returns
indexed by a firm identifier (`permno`) and a period‐end date (`date`).
For some signals you also need additional fundamentals:

- `me`: market equity (for size).
- `be`: book equity (for book‑to‑market).
- `at`: total assets (for investment).
- `op`: operating profitability (for profitability).

These variables can be loaded from CRSP and Compustat via the
functions in `aa.prep`, but for this guide we will create synthetic
data.

## Computing anomaly signals

Signal functions live in `aa.signals` and operate on
DataFrames with columns `date`, `permno` and the relevant input
variable.  They return a DataFrame with columns `date`, `permno` and
`signal`.  The main functions are:

- `compute_size_signal` – lagged log market equity.
- `compute_book_to_market_signal` – six‑month lagged log book‑to‑market.
- `compute_momentum_signal` – 12‑minus‑2 momentum using an 11‑month lookback window.
- `compute_investment_signal` – negative asset growth (investment).
- `compute_profitability_signal` – operating profitability relative to book equity.

Example:

```python
import pandas as pd
from aa.signals import compute_size_signal, compute_book_to_market_signal

# Suppose crsp_df has columns date, permno, me; funda_df has be, op, at
size = compute_size_signal(crsp_df[["date", "permno", "me"]])
bm   = compute_book_to_market_signal(funda_df[["date", "permno", "be"]],
                                     crsp_df[["date", "permno", "me"]])
```

The `book_to_market` helper merges Compustat and CRSP inputs internally.

## Univariate portfolio sorts

To form portfolios and compute high‑minus‑low spreads for a single
signal, use `aa.asset_pricing.univariate_sort`.  This function
takes returns, a signal, optional market equity for value weighting
and a `SortConfig` specifying the number of portfolios and
breakpoint options.  It returns both a time‑series of portfolio
returns and a summary table.

```python
from aa.asset_pricing import univariate

# Synthetic example
returns = pd.DataFrame({"date": dates, "permno": firms, "ret": returns_array})
signal  = size  # computed above
res = univariate.univariate_sort(
    returns=returns,
    signal=signal,
    size=crsp_df[["date", "permno", "me"]],
    exch=None,
    config=univariate.SortConfig(n_bins=5, nyse_breaks=False, min_obs=20),
)
ts      = res["time_series"]   # one row per date/bin
summary = res["summary"]      # average EW and VW returns per bin
hl      = res["hl"]            # high‑minus‑low time series
```

For conditional sorts on two characteristics, use
`aa.asset_pricing.double_sort` or the higher‑level
`aa.asset_pricing.double_sorts.run_double_sort`.

## Fama–MacBeth regressions

The module `aa.asset_pricing.fama_macbeth` implements two‑pass
Fama–MacBeth regressions.  Use `fama_macbeth` for a simple call or
`fama_macbeth_full` to obtain the full time‑series of cross‑sectional
coefficients in addition to the average betas and t‑statistics.

```python
from aa.asset_pricing.fama_macbeth import fama_macbeth_full

# Suppose panel has columns date, permno, ret and one or more signals
panel = returns.merge(size, on=["date", "permno"])
panel = panel.merge(bm, on=["date", "permno"], suffixes=("", "_bm"))

reg_res = fama_macbeth_full(
    panel=panel,
    y="ret",
    xcols=["signal", "signal_bm"],
    time_col="date",
    nw_lags=3,
)
avg_beta  = reg_res["average_beta"]
beta_ts   = reg_res["beta_ts"]
stderr    = reg_res["se_beta"]
```

`nw_lags` controls the Newey–West correction for autocorrelation.  The
function automatically handles missing data and maps directly to the
MATLAB implementation【795186362666985†L0-L23】.

## Evaluating multiple signals

To evaluate a set of anomaly signals simultaneously, call
`aa.analysis.anomaly_pipeline.evaluate_signals`.  It accepts a
dictionary of signals and returns a dictionary keyed by signal name
with performance metrics (mean return, t‑statistic, Sharpe ratio,
drawdown, turnover, etc.).

```python
from aa.analysis.anomaly_pipeline import evaluate_signals

signals = {
    "size": size,
    "value": bm,
    "momentum": compute_momentum_signal(...),
}

perf = evaluate_signals(
    signals=signals,
    returns=returns,
    size=crsp_df[["date", "permno", "me"]],
    exch=None,
    sort_config=univariate.SortConfig(n_bins=5, nyse_breaks=False),
)
print(perf["size"]["mean_return"], perf["size"]["t_statistic"])
```

Under the hood the pipeline computes portfolio returns and high‑minus‑low
series for each signal and applies functions from
`aa.analysis.anomaly_metrics`【201875463115225†L10-L49】.

## Running the full pipeline

For a complete replication of the published results, use the
scripts in the `scripts/` directory.  The most comprehensive entry
point is `scripts/run_full_library_replication.py`, which reads
pre‑processed data, computes all signals, forms portfolios and
generates tables and figures.  See the script’s `--help` flag for
options.

```bash
python scripts/run_full_library_replication.py \
  --crsp-path data/crsp_msf.parquet \
  --comp-path data/comp_funda.parquet \
  --linktables-path data/ccm_lnkhist.parquet \
  --output-dir results/
```

Alternatively, `scripts/run_size_pipeline.py` demonstrates a
lightweight pipeline focusing on the size anomaly.

## Further reading

For details on the underlying algorithms and translation coverage, see
`docs/architecture.md` and `docs/translation_completion_report.md`.  The
docstrings in the source code also provide extensive explanations and
citation links back to the original MATLAB routines.