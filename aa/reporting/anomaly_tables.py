"""
Anomaly reporting and summary tables.

This module provides helper functions to assemble the outputs of
portfolio sorts and performance evaluations into human‑readable
tables.  The aim is to replicate the functionality of MATLAB
scripts that generate comparison tables of anomaly strategies.  By
accepting Python dictionaries of metrics and converting them into
``pandas`` DataFrames, these helpers integrate seamlessly with
existing reporting tools (e.g. conversion to Markdown or LaTeX via
:mod:`pandas`).

Functions
---------
make_summary_table
    Assemble a tidy DataFrame from a dictionary of metric
    dictionaries, one entry per anomaly.

to_markdown
    Convert a DataFrame into Markdown format using
    ``pandas.DataFrame.to_markdown``.

to_latex
    Convert a DataFrame into LaTeX format using
    ``pandas.DataFrame.to_latex``.

Notes
-----
These functions are intentionally lightweight.  They do not apply
styling or formatting beyond what pandas provides.  Users may
choose to post‑process the resulting strings for publication.
"""

from __future__ import annotations

from typing import Dict, Any

import pandas as pd


def make_summary_table(metrics: Dict[str, Dict[str, Any]]) -> pd.DataFrame:
    """Create a summary table from a nested dictionary of metrics.

    Parameters
    ----------
    metrics : dict
        Mapping from anomaly names to dictionaries of metric values.
        Each inner dictionary must map metric names to scalar values.

    Returns
    -------
    DataFrame
        A DataFrame where rows correspond to anomalies and columns
        correspond to metric names.  The row index is the anomaly
        identifier.
    """
    if not metrics:
        return pd.DataFrame()
    # Use the first entry to define the column ordering
    first_key = next(iter(metrics))
    cols = list(metrics[first_key].keys())
    records = []
    index = []
    for name, stats in metrics.items():
        index.append(name)
        # Ensure that stats has the same keys as cols; fill missing with NaN
        row = {c: stats.get(c, float("nan")) for c in cols}
        records.append(row)
    df = pd.DataFrame(records, index=index, columns=cols)
    return df


def to_markdown(df: pd.DataFrame, *, index: bool = True) -> str:
    """Render a DataFrame as a Markdown table.

    Parameters
    ----------
    df : DataFrame
        The table to render.
    index : bool, default True
        Whether to include the index in the output.

    Returns
    -------
    str
        A Markdown representation of the DataFrame.
    """
    if df is None or df.empty:
        return ""
    return df.to_markdown(index=index)


def to_latex(df: pd.DataFrame, *, index: bool = True) -> str:
    """Render a DataFrame as a LaTeX table.

    Parameters
    ----------
    df : DataFrame
        The table to render.
    index : bool, default True
        Whether to include the index in the output.

    Returns
    -------
    str
        A LaTeX representation of the DataFrame.  Column names are
        used as header labels.  The caller is responsible for adding
        any required LaTeX table environments.
    """
    if df is None or df.empty:
        return ""
    return df.to_latex(index=index, escape=False)
