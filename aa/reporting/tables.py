"""
Table formatting for asset pricing results.

This module provides helper functions to convert the outputs of
portfolio sorts and Fama–MacBeth regressions into Markdown and
LaTeX tables suitable for academic papers.  The emphasis is on
producing clean tables without external styling dependencies.

The functions return a dictionary with two keys: ``markdown`` and
``latex``.  The value associated with ``markdown`` is a string
containing a GitHub‑flavoured Markdown table, while ``latex``
contains LaTeX code compatible with the ``tabular`` environment.

Usage
-----
>>> from aa.reporting.tables import portfolio_returns_table
>>> tables = portfolio_returns_table(res['summary'], value_weighted=False)
>>> print(tables['markdown'])
>>> print(tables['latex'])

Notes
-----
These functions do not attempt to adjust units or formatting beyond
rounding floats to three decimal places.  Users seeking greater
control over table appearance should post‑process the returned strings.
"""

from __future__ import annotations

from typing import Dict, Any

import pandas as pd

__all__ = [
    "portfolio_returns_table",
    "high_low_table",
    "fama_macbeth_table",
]


def _format_table(df: pd.DataFrame) -> Dict[str, str]:
    """Internal helper to format a DataFrame into Markdown and LaTeX.

    Floats are rounded to three decimal places.  The index and column
    names are included in the output.  If pandas' optional dependencies
    needed for ``to_markdown`` or ``to_latex`` are unavailable, the
    function falls back to a simple pipe‑delimited Markdown table and
    returns an empty string for LaTeX.

    Parameters
    ----------
    df : DataFrame
        The table to format.  Index and column names are retained.

    Returns
    -------
    dict
        Dictionary with keys ``markdown`` and ``latex`` containing the
        formatted table in Markdown and LaTeX, respectively.
    """
    # Copy the DataFrame and round floating‑point columns for readability
    fmt_df = df.copy()
    for col in fmt_df.columns:
        if pd.api.types.is_float_dtype(fmt_df[col]):
            numeric_col = fmt_df[col].astype(float)
            fmt_df[col] = numeric_col.map(lambda x: f"{x:.3f}" if pd.notna(x) else "")

    # Construct Markdown using pandas' to_markdown if available
    try:
        md = fmt_df.to_markdown(index=True)
    except Exception:
        # Build a simple pipe‑delimited Markdown table as a fallback
        header_vals = [fmt_df.index.name or ""] + list(fmt_df.columns)
        header = "| " + " | ".join([str(c) for c in header_vals]) + " |"
        separator = "|" + "|".join(["---" for _ in header_vals]) + "|"
        rows = []
        for idx, row in fmt_df.iterrows():
            row_vals = [str(idx)] + [
                str(row[c]) if row[c] != "" else "" for c in fmt_df.columns
            ]
            rows.append("| " + " | ".join(row_vals) + " |")
        md = "\n".join([header, separator] + rows)
    # Construct LaTeX using pandas' to_latex if available
    try:
        latex = fmt_df.to_latex(index=True, escape=False)
    except Exception:
        # If LaTeX support is unavailable, return an empty string
        latex = ""
    return {"markdown": md, "latex": latex}


def portfolio_returns_table(
    summary: pd.DataFrame,
    *,
    value_weighted: bool = False,
) -> Dict[str, str]:
    """Generate a 2D portfolio return table from a double sort summary.

    Parameters
    ----------
    summary : DataFrame
        Output of :func:`aa.asset_pricing.double_sort` keyed by
        ``'summary'``.  Must contain columns ``bin1``, ``bin2`` and
        either ``ret_ew`` or ``ret_vw`` depending on the desired
        weighting.
    value_weighted : bool, default False
        If True, use the value‑weighted returns (``ret_vw``); if
        False, use equal‑weighted returns (``ret_ew``).

    Returns
    -------
    dict
        Dictionary with keys ``markdown`` and ``latex`` containing
        formatted tables.  The index corresponds to ``bin1`` and
        columns correspond to ``bin2``.

    Notes
    -----
    This function pivots the summary DataFrame so that bins along the
    first characteristic form the rows and bins along the second
    characteristic form the columns.  Any missing combinations are
    represented by ``NaN``.
    """
    col = "ret_vw" if value_weighted else "ret_ew"
    if col not in summary.columns:
        raise KeyError(f"summary must contain column '{col}'")
    pivot = summary.pivot(index="bin1", columns="bin2", values=col)
    # Ensure sorted index and columns
    pivot = pivot.sort_index(axis=0).sort_index(axis=1)
    # Assign proper names for nicer output
    pivot.index.name = "bin1"
    pivot.columns.name = "bin2"
    return _format_table(pivot)


def high_low_table(
    hl_ts: pd.DataFrame,
    *,
    value_weighted: bool = False,
    average: bool = True,
) -> Dict[str, str]:
    """Create a summary table for high–low spreads.

    Parameters
    ----------
    hl_ts : DataFrame
        Time‑series of high–low spreads returned by
        :func:`aa.asset_pricing.double_sort` under keys ``'hl_dim1'``
        or ``'hl_dim2'``.  Must contain columns ``hl_ew`` and
        ``hl_vw``.
    value_weighted : bool, default False
        If True, use ``hl_vw``; otherwise use ``hl_ew``.
    average : bool, default True
        If True, compute the sample mean of the high–low series and
        display as a one‑row table.  If False, return the entire
        time‑series as a table.

    Returns
    -------
    dict
        Dictionary with keys ``markdown`` and ``latex``.
    """
    col = "hl_vw" if value_weighted else "hl_ew"
    if col not in hl_ts.columns:
        raise KeyError(f"hl_ts must contain column '{col}'")
    if average:
        avg = hl_ts[col].mean()
        df = pd.DataFrame({col: [avg]}, index=["mean"])
    else:
        df = hl_ts[["date", col]].copy()
        df = df.set_index("date")
    return _format_table(df)


def fama_macbeth_table(
    fm_results: Dict[str, Any],
) -> Dict[str, str]:
    """Format Fama–MacBeth regression results into a table.

    Parameters
    ----------
    fm_results : dict
        Output of :func:`aa.asset_pricing.fama_macbeth_full`.  Must
        contain keys ``'lambda'``, ``'se'``, ``'t'`` and ``'n'``.

    Returns
    -------
    dict
        Dictionary with keys ``markdown`` and ``latex``.  The table
        has rows for the intercept and each regressor and columns for
        the point estimates (``lambda``), Newey–West standard errors
        (``se``), t‑statistics (``t``) and the number of cross‑sectional
        observation periods (``n``).
    """
    required_keys = {"lambda", "se", "t", "n"}
    if not required_keys.issubset(fm_results.keys()):
        missing = required_keys - set(fm_results.keys())
        raise KeyError(f"fm_results missing keys: {missing}")
    # Build DataFrame
    df = pd.DataFrame(
        {
            "lambda": fm_results["lambda"],
            "se": fm_results["se"],
            "t": fm_results["t"],
            "n": fm_results["n"],
        }
    )
    # Ensure order of coefficients (const first)
    idx = [c for c in df.index if c == "const"] + [c for c in df.index if c != "const"]
    df = df.loc[idx]
    return _format_table(df)
