"""
Library‑wide summary and ranking tables for anomaly evaluation.

This module contains helper functions to convert the results of the
large‑scale anomaly evaluation pipeline into tables that mirror the
outputs of the original MATLAB library.  Two primary kinds of
tables are supported:

* **Performance tables** summarising the mean return, t‑statistic,
  Sharpe ratio and drawdown of each anomaly.  These tables are
  derived from the metrics returned by
  :func:`aa.analysis.anomaly_pipeline.evaluate_signals`.
* **Ranking tables** listing anomalies in order of a chosen metric
  (e.g. mean return or t‑statistic) along with their rank.  These
  tables can be produced by the functions in
  :mod:`aa.analysis.anomaly_ranking` and formatted here.

The functions defined here wrap the lower‑level formatting utilities
in :mod:`aa.reporting.anomaly_tables` and :mod:`aa.reporting.tables`
to provide a convenient one‑stop interface for exporting results
directly to Markdown or LaTeX.
"""

from __future__ import annotations

from typing import Dict, Any, Union

import pandas as pd

from . import anomaly_tables

__all__ = [
    "performance_table",
    "performance_tables",
    "ranking_table",
    "ranking_tables",
]


def performance_table(metrics: Dict[str, Dict[str, Any]]) -> pd.DataFrame:
    """Assemble a DataFrame summarising anomaly performance metrics.

    Parameters
    ----------
    metrics : dict
        Mapping from anomaly identifiers to dictionaries of scalar
        metrics (e.g. ``mean``, ``t_stat``, ``sharpe``, ``max_dd``).

    Returns
    -------
    DataFrame
        Rows correspond to anomalies and columns correspond to
        metrics.  The column ordering is taken from the first entry
        in the metrics dictionary.
    """
    return anomaly_tables.make_summary_table(metrics)


def performance_tables(
    metrics: Dict[str, Dict[str, Any]],
    *,
    to: str = "dataframe",
) -> Union[pd.DataFrame, Dict[str, str]]:
    """Create performance tables in DataFrame, Markdown or LaTeX format.

    Parameters
    ----------
    metrics : dict
        Performance metrics keyed by anomaly name.
    to : {"dataframe", "markdown", "latex"}, default "dataframe"
        Desired output format.  ``"dataframe"`` returns a pandas
        DataFrame; ``"markdown"`` returns a dict with a key
        ``"markdown"`` containing a Markdown table; ``"latex"`` returns
        a dict with a key ``"latex"`` containing LaTeX code.

    Returns
    -------
    DataFrame or dict
        Depending on ``to``, returns either the raw DataFrame or a
        dictionary containing the formatted table.  If ``metrics`` is
        empty, an empty DataFrame or empty strings are returned.
    """
    df = performance_table(metrics)
    if to == "dataframe":
        return df
    elif to == "markdown":
        return {"markdown": anomaly_tables.to_markdown(df)}
    elif to == "latex":
        return {"latex": anomaly_tables.to_latex(df)}
    else:
        raise ValueError(
            f"Unsupported format '{to}'. Choose from 'dataframe', 'markdown', 'latex'."
        )


def ranking_table(ranks: pd.DataFrame) -> pd.DataFrame:
    """Return a DataFrame representing anomaly ranks.

    Parameters
    ----------
    ranks : DataFrame
        DataFrame with index corresponding to anomaly identifiers and a
        column ``rank`` (and possibly other columns, e.g. the
        underlying metric).  Produced by
        :func:`aa.analysis.anomaly_ranking.rank_anomalies`.

    Returns
    -------
    DataFrame
        The input DataFrame, unmodified, but provided for symmetry
        with :func:`performance_table`.
    """
    return ranks.copy()


def ranking_tables(
    ranks: pd.DataFrame,
    *,
    to: str = "dataframe",
) -> Union[pd.DataFrame, Dict[str, str]]:
    """Create ranking tables in DataFrame, Markdown or LaTeX format.

    Parameters
    ----------
    ranks : DataFrame
        DataFrame produced by :func:`aa.analysis.anomaly_ranking.rank_anomalies`.
    to : {"dataframe", "markdown", "latex"}, default "dataframe"
        Desired output format.

    Returns
    -------
    DataFrame or dict
        The formatted ranking table.
    """
    df = ranking_table(ranks)
    if to == "dataframe":
        return df
    elif to == "markdown":
        return {"markdown": anomaly_tables.to_markdown(df)}
    elif to == "latex":
        return {"latex": anomaly_tables.to_latex(df)}
    else:
        raise ValueError(
            f"Unsupported format '{to}'. Choose from 'dataframe', 'markdown', 'latex'."
        )
