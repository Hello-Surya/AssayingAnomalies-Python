"""
Panel construction utilities.

This module defines functions to merge raw CRSP returns, Compustat
fundamental data and CCM link history into a unified monthly panel.  The
resulting panel can then be used to construct anomaly signals and run
asset‑pricing tests.  For the size anomaly considered in
``run_size_pipeline``, the Compustat and link data are optional, but
fully supported when provided.

In contrast to the simplified implementation in the initial Python port
of Assaying Anomalies (which ignored fundamentals entirely), this
version cleans the Compustat FUNDA table, maps GVKEYs to PERMNOs using
the CCM link history, and merges the resulting fundamentals onto the
monthly CRSP panel using an as‑of merge.  Fundamentals are assigned to
months on or after their June Y+1 ``assign_month`` and persist until
the next annual report.  Periods prior to the first assignment month
retain ``NaN`` values for fundamental variables.
"""

from __future__ import annotations

from typing import Optional
import warnings
import pandas as pd

from .compustat import prepare_compustat_annual
from .linktables import map_gvkey_to_permno

__all__ = ["build_monthly_panel"]


def build_monthly_panel(
    *,
    crsp: pd.DataFrame,
    funda: Optional[pd.DataFrame] = None,
    lnkhist: Optional[pd.DataFrame] = None,
) -> pd.DataFrame:
    """Assemble a monthly asset panel from CRSP, Compustat and CCM link data.

    Parameters
    ----------
    crsp : DataFrame
        Monthly CRSP data with at minimum ``date``, ``permno`` and ``ret``.
        Additional columns (e.g. ``me``, ``exchcd``) are preserved.
    funda : DataFrame, optional
        Raw Compustat FUNDA table; if provided, it will be cleaned
        via :func:`prepare_compustat_annual` and linked to PERMNOs via
        :func:`map_gvkey_to_permno`.  Rows where a valid link exists
        are merged on assignment month.
    lnkhist : DataFrame, optional
        CCM link history table used to map GVKEYs to PERMNOs.  Required
        when ``funda`` is provided.

    Returns
    -------
    DataFrame
        A panel with CRSP returns and, if available, matched Compustat
        fundamentals.  For periods with no match, Compustat columns are
        ``NaN``.  The returned DataFrame is sorted by ``permno`` and
        ``date``.
    """
    # Start with CRSP copy to avoid mutating caller data
    panel = crsp.copy()
    # Normalise date column
    if "date" not in panel.columns:
        raise KeyError("crsp must contain a 'date' column")
    panel["date"] = (
        pd.to_datetime(panel["date"], errors="coerce")
        .dt.tz_localize(None)
        .astype("datetime64[ns]")
    )
    # Ensure permno is numeric so that merge_asof works properly
    if "permno" not in panel.columns:
        raise KeyError("crsp must contain a 'permno' column")
    panel["permno"] = pd.to_numeric(panel["permno"], errors="coerce").astype("Int64")

    # If Compustat + link data provided, clean and merge
    if funda is not None:
        if lnkhist is None:
            raise ValueError("lnkhist must be provided when funda is not None")
        # Clean fundamentals and assign to June Y+1
        clean_funda = prepare_compustat_annual(funda)
        # Map GVKEYs to PERMNOs
        mapped_funda = map_gvkey_to_permno(
            clean_funda, lnkhist, date_col="assign_month"
        )
        # Drop rows with no permno match
        mapped_funda = mapped_funda.dropna(subset=["permno"]).copy()
        # Cast permno to Int64
        mapped_funda["permno"] = mapped_funda["permno"].astype("Int64")
        # Determine fundamental columns to merge (exclude keys and dates)
        excluded = {"gvkey", "datadate", "fyear", "fyr", "assign_month", "permno"}
        fund_cols = [c for c in mapped_funda.columns if c not in excluded]
        # If no numeric fundamental columns, warn but continue
        if not fund_cols:
            warnings.warn(
                "No fundamental numeric columns found after cleaning; only CRSP variables will be returned.",
                RuntimeWarning,
            )
        # Prepare fundamentals for asof merge: sort by permno and assign_month
        mapped_funda["assign_month"] = pd.to_datetime(
            mapped_funda["assign_month"], errors="coerce"
        ).astype("datetime64[ns]")
        mapped_funda = mapped_funda.sort_values(
            ["assign_month", "permno"], kind="mergesort"
        ).reset_index(drop=True)

        panel["date"] = pd.to_datetime(panel["date"], errors="coerce").astype(
            "datetime64[ns]"
        )
        panel = panel.sort_values(["date", "permno"], kind="mergesort").reset_index(
            drop=True
        )
        # Perform asof merge: for each (permno, date) pick the latest assign_month <= date
        merged = pd.merge_asof(
            panel,
            mapped_funda[["permno", "assign_month"] + fund_cols],
            by="permno",
            left_on="date",
            right_on="assign_month",
            direction="backward",
            allow_exact_matches=True,
        )
        # Drop the assign_month column from the merged result
        merged = merged.drop(columns=["assign_month"], errors="ignore")
        panel = merged
    else:
        # If fundamentals were not provided but link data was, warn user
        if lnkhist is not None:
            warnings.warn(
                "funda is None but lnkhist provided; ignoring lnkhist since there are no fundamentals to link.",
                RuntimeWarning,
            )
        panel = panel.copy()

    # Final ordering
    panel = panel.sort_values(["permno", "date"]).reset_index(drop=True)

    # enforce strict monotonic ordering within permno
    panel = panel.sort_values(["permno", "date"], kind="mergesort").reset_index(
        drop=True
    )
    return panel
