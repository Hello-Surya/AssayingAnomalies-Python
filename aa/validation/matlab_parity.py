"""
Validation routines for MATLAB parity.

The functions in this module help verify that the Python
implementation of Assaying Anomalies produces results consistent
with the original MATLAB version.  They compare metrics and
time‑series outputs from both implementations and flag
discrepancies exceeding a user‑specified tolerance.

These utilities are not meant to perform exhaustive checks but
provide a convenient sanity check during development.  Developers
can adjust the tolerance levels depending on the precision of the
MATLAB outputs and the expected numerical differences arising from
floating‑point computations.
"""

from typing import Dict, Any, Tuple
import pandas as pd

__all__ = ["compare_metrics", "parity_ok"]


def compare_metrics(
    reference: Dict[str, Dict[str, Any]],
    candidate: Dict[str, Dict[str, Any]],
    *,
    tolerance: float = 1e-6,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Compare two nested dictionaries of metrics and compute differences.

    Parameters
    ----------
    reference : dict
        Dictionary of reference metrics (e.g. from MATLAB).  Keys are
        anomaly names; values are dictionaries of metric names to
        scalar values.
    candidate : dict
        Dictionary of candidate metrics (e.g. from Python).  Same
        structure as ``reference``.
    tolerance : float, default 1e-6
        Absolute tolerance.  Differences with magnitude less than or
        equal to ``tolerance`` are considered acceptable.

    Returns
    -------
    diff_df : DataFrame
        DataFrame with hierarchical index (anomaly, metric) and a
        column ``'difference'`` equal to ``candidate - reference``.
    flag_df : DataFrame
        DataFrame of the same shape as ``diff_df`` with a boolean
        column ``'within_tolerance'`` indicating whether the
        difference is within the specified tolerance (True) or
        exceeds it (False).
    """
    # Determine common anomalies and metrics
    anomalies = set(reference.keys()) & set(candidate.keys())
    rows = []
    flags = []
    for anom in sorted(anomalies):
        ref_metrics = reference[anom]
        cand_metrics = candidate[anom]
        common_metrics = set(ref_metrics.keys()) & set(cand_metrics.keys())
        for m in sorted(common_metrics):
            ref_val = ref_metrics[m]
            cand_val = cand_metrics[m]
            # Compute difference; treat NaN comparisons as zero difference if both are NaN
            if pd.isna(ref_val) and pd.isna(cand_val):
                diff = 0.0
            else:
                diff = cand_val - ref_val
            rows.append(((anom, m), diff))
            flags.append(((anom, m), abs(diff) <= tolerance))
    if not rows:
        diff_df = pd.DataFrame(columns=["difference"])
        flag_df = pd.DataFrame(columns=["within_tolerance"])
        return diff_df, flag_df
    index_tuples, diffs = zip(*rows)
    diff_df = pd.DataFrame(
        {"difference": diffs},
        index=pd.MultiIndex.from_tuples(index_tuples, names=["anomaly", "metric"]),
    )
    index_tuples_f, flag_vals = zip(*flags)
    flag_df = pd.DataFrame(
        {"within_tolerance": flag_vals},
        index=pd.MultiIndex.from_tuples(index_tuples_f, names=["anomaly", "metric"]),
    )
    return diff_df, flag_df


def parity_ok(
    reference: Dict[str, Dict[str, Any]],
    candidate: Dict[str, Dict[str, Any]],
    *,
    tolerance: float = 1e-6,
) -> bool:
    """Return True if all metrics are within tolerance of the reference.

    Parameters
    ----------
    reference : dict
        Reference metrics (e.g. MATLAB outputs).
    candidate : dict
        Candidate metrics (e.g. Python outputs).
    tolerance : float, default 1e-6
        Tolerance threshold.

    Returns
    -------
    bool
        True if every common anomaly and metric differs by no more
        than ``tolerance``; False otherwise.  If either dictionary
        is empty, returns False.
    """
    if not reference or not candidate:
        return False
    _, flag_df = compare_metrics(reference, candidate, tolerance=tolerance)
    # If flag_df is empty, there were no common metrics; treat as False
    if flag_df.empty:
        return False
    return bool(flag_df["within_tolerance"].all())
