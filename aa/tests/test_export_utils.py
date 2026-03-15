"""
Unit tests for the export utilities in ``aa.reporting.export_utils``.

These tests ensure that tables and figures can be written to disk in
the supported formats.  They operate in a temporary directory under
the pytest scratch path to avoid polluting the repository.  The
generated files are inspected for existence and non‑empty content.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt

from aa.reporting.export_utils import export_table, export_tables, export_figure


class TestExportUtils(unittest.TestCase):
    """Tests for export utilities."""

    def setUp(self) -> None:
        # Create a temporary directory for all file outputs
        self.tmpdir = tempfile.TemporaryDirectory()
        self.base = Path(self.tmpdir.name)
        # Synthetic DataFrame
        self.df = pd.DataFrame(
            {
                "a": [1, 2],
                "b": [3, 4],
            },
            index=["row1", "row2"],
        )
        # Simple figure
        self.fig, self.ax = plt.subplots()
        self.ax.plot([0, 1], [0, 1])

    def tearDown(self) -> None:
        # Clean up temporary directory and close figure
        self.tmpdir.cleanup()
        plt.close(self.fig)

    def test_export_table_csv(self) -> None:
        path = self.base / "table.csv"
        export_table(self.df, str(path), format="csv", index=True)
        # File should exist and not be empty
        self.assertTrue(path.exists())
        self.assertGreater(path.stat().st_size, 0)

    def test_export_table_markdown(self) -> None:
        path = self.base / "table.md"
        export_table(self.df, str(path), format="markdown", index=False)
        self.assertTrue(path.exists())
        content = path.read_text().strip()
        # Markdown should start with a header separator
        self.assertIn("--", content)

    def test_export_tables(self) -> None:
        tables = {"t1": self.df, "t2": self.df.copy()}
        export_tables(tables, str(self.base), format="csv", index=False)
        # Two files should exist
        for name in tables:
            file_path = self.base / f"{name}.csv"
            self.assertTrue(file_path.exists())
            self.assertGreater(file_path.stat().st_size, 0)

    def test_export_figure_png(self) -> None:
        path = self.base / "plot.png"
        export_figure(self.fig, str(path))
        self.assertTrue(path.exists())
        # Check that the file size is greater than zero
        self.assertGreater(path.stat().st_size, 0)


if __name__ == "__main__":
    unittest.main()
