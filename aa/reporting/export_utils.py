"""
Export utilities for Assaying Anomalies results.

This module provides helper functions to persist tables and figures
produced by the anomaly evaluation pipeline.  Tables can be written
to CSV, Markdown or LaTeX files, and figures can be saved as PNG
(or any format supported by ``matplotlib``).  These helpers are
lightweight wrappers around ``pandas`` and ``matplotlib``
functionality and are intended to standardise output formats across
the library.

Example
-------
>>> import pandas as pd
>>> from aa.reporting.export_utils import export_table, export_figure
>>> df = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
>>> export_table(df, "my_table.csv", format="csv")
>>> # Later
>>> import matplotlib.pyplot as plt
>>> fig, ax = plt.subplots()
>>> ax.plot([0, 1], [0, 1])
>>> export_figure(fig, "my_plot.png")
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict

import pandas as pd

from aa.reporting import anomaly_tables

import matplotlib.pyplot as plt

__all__ = ["export_table", "export_tables", "export_figure"]


def export_table(
    df: pd.DataFrame,
    path: str,
    *,
    format: str = "csv",
    index: bool = True,
    encoding: str = "utf-8",
) -> None:
    """Write a single DataFrame to disk in the specified format.

    Parameters
    ----------
    df : DataFrame
        The table to export.
    path : str
        Destination path.  The file suffix does not determine the
        format – use the ``format`` argument.
    format : {'csv', 'markdown', 'latex'}, default 'csv'
        Which output format to use.  Markdown and LaTeX formats will
        write a text file containing the table representation.
    index : bool, default True
        Whether to include the DataFrame index in the output.
    encoding : str, default 'utf-8'
        Text encoding for Markdown and LaTeX files.

    Raises
    ------
    ValueError
        If an unsupported format is requested.
    """
    fmt = format.lower()
    dest = Path(path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    if fmt == "csv":
        df.to_csv(dest, index=index)
    elif fmt == "markdown":
        md = anomaly_tables.to_markdown(df, index=index)
        dest.write_text(md, encoding=encoding)
    elif fmt == "latex":
        latex = anomaly_tables.to_latex(df, index=index)
        dest.write_text(latex, encoding=encoding)
    else:
        raise ValueError(
            f"Unsupported format '{format}'. Use 'csv', 'markdown' or 'latex'."
        )


def export_tables(
    tables: Dict[str, pd.DataFrame],
    directory: str,
    *,
    format: str = "csv",
    index: bool = True,
    encoding: str = "utf-8",
) -> None:
    """Write multiple tables to a directory.

    Each entry in ``tables`` is written to ``directory/<name>.<ext>`` where
    ``name`` is the dictionary key and ``ext`` is determined by the
    ``format`` argument.  The directory is created if it does not
    already exist.

    Parameters
    ----------
    tables : dict
        Mapping from table names to DataFrames.
    directory : str
        Directory into which the files should be written.
    format : {'csv', 'markdown', 'latex'}, default 'csv'
        Output format for all tables.
    index : bool, default True
        Whether to include the index in each output file.
    encoding : str, default 'utf-8'
        Text encoding for Markdown and LaTeX files.
    """
    dir_path = Path(directory)
    dir_path.mkdir(parents=True, exist_ok=True)
    for name, df in tables.items():
        suffix = {
            "csv": ".csv",
            "markdown": ".md",
            "latex": ".tex",
        }.get(format.lower())
        if suffix is None:
            raise ValueError(
                f"Unsupported format '{format}'. Use 'csv', 'markdown' or 'latex'."
            )
        file_path = dir_path / f"{name}{suffix}"
        export_table(df, str(file_path), format=format, index=index, encoding=encoding)


def export_figure(
    fig: plt.Figure,
    path: str,
    *,
    dpi: int = 300,
    bbox_inches: str | None = "tight",
) -> None:
    """Save a Matplotlib figure to disk.

    Parameters
    ----------
    fig : Figure
        The figure to save.
    path : str
        Output file path.  The file extension determines the image
        format (e.g. ``.png``, ``.pdf``).
    dpi : int, default 300
        Dots per inch for raster formats.
    bbox_inches : str or None, default 'tight'
        Bounding box option passed to ``Figure.savefig``.
    """
    dest = Path(path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(dest, dpi=dpi, bbox_inches=bbox_inches)
