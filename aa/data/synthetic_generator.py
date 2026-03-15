"""
Synthetic data generator for Assaying Anomalies.

This module provides helper functions to create synthetic panel data
resembling CRSP/Compustat observations.  The generated data can be used
for tests, demonstrations and examples without requiring access to
proprietary WRDS data.  Each dataset contains monthly observations
across a universe of securities with returns, market equity, exchange
codes and a predictive signal.  A fixed random seed ensures that the
output is reproducible.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from typing import Optional

__all__ = ["generate_synthetic_panel"]


def generate_synthetic_panel(
    *,
    n_periods: int = 120,
    n_stocks: int = 300,
    start_date: str = "2000-01-31",
    freq: str = "ME",
    seed: Optional[int] = None,
) -> pd.DataFrame:
    """Create a synthetic panel of stock returns and characteristics.

    The generator simulates a panel of monthly observations for a set of
    securities.  Returns are generated with a small relation to a
    synthetic signal to allow for meaningful portfolio sorts and
    regressions.  Market equity and exchange codes are drawn from
    realistic distributions.  A seed may be supplied to obtain
    deterministic output.

    Parameters
    ----------
    n_periods : int, default 120
        Number of monthly periods to simulate.
    n_stocks : int, default 300
        Number of unique securities (permnos) in the panel.
    start_date : str, default "2000-01-31"
        ISO‑formatted starting date for the first observation.  Dates
        will be spaced according to ``freq``.
    freq : str, default "M"
        Frequency string understood by :func:`pandas.date_range` for
        generating the date index.  ``"M"`` yields month‑end dates.
    seed : int, optional
        Seed passed to NumPy’s default random generator for
        reproducibility.  If None, the generator will be unseeded.

    Returns
    -------
    DataFrame
        A pandas DataFrame with columns:

        - ``date`` – month‑end date (naive timestamp)
        - ``permno`` – integer identifier for each stock
        - ``me`` – simulated market equity (size)
        - ``exchcd`` – exchange code (1 = NYSE, 2 = AMEX, 3 = NASDAQ)
        - ``signal`` – predictive signal used for sorting and regressions
        - ``ret`` – one‑month ahead return in decimal form

    Notes
    -----
    The generated signal is correlated with the log of market equity
    plus independent noise.  Returns are drawn from a normal
    distribution around a small positive drift with an additional
    relation to the signal.  This structure ensures that univariate
    sorts and Fama–MacBeth regressions will produce non‑trivial
    results while remaining entirely synthetic.
    """
    # Initialise random generator
    rng = np.random.default_rng(seed)
    # Generate an array of dates
    dates = pd.date_range(start=start_date, periods=n_periods, freq=freq)
    # Create a Cartesian product of dates and permnos
    permnos = np.arange(1, n_stocks + 1, dtype=int)
    # Use list comprehension for speed and clarity
    panel_index = [(d, p) for d in dates for p in permnos]
    df = pd.DataFrame(panel_index, columns=["date", "permno"])
    # Draw market equity from a log‑normal distribution to mimic firm size
    df["me"] = rng.lognormal(mean=8.0, sigma=0.5, size=len(df))
    # Assign exchange codes randomly with realistic proportions
    df["exchcd"] = rng.choice([1, 2, 3], size=len(df), p=[0.6, 0.1, 0.3])
    # Construct a synthetic signal correlated with market equity
    log_me = np.log(df["me"])
    # Demean per period to remove time trends
    demeaned_log_me = log_me - df.groupby("date")["me"].transform(
        lambda x: np.log(x).mean()
    )
    df["signal"] = demeaned_log_me + rng.normal(scale=0.5, size=len(df))
    # Generate returns: base noise plus small linear relation to the signal
    base_ret = rng.normal(loc=0.001, scale=0.05, size=len(df))
    df["ret"] = base_ret + 0.02 * df["signal"]
    # Convert date to naive timestamp (no timezone)
    df["date"] = pd.to_datetime(df["date"]).dt.tz_localize(None)
    return df
