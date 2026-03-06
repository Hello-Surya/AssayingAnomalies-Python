"""
Replication package exporter
============================

This module provides a utility function to generate a replication
package from a completed experiment. A replication package bundles
together the experiment metadata and the datasets produced by the
pipeline so that other researchers can reproduce every table and
figure exactly. The exported files are plain text (JSON and CSV)
and Parquet to maximize interoperability.

The function is deliberately conservative: it does not assume any
external context beyond the provided ``ExperimentTracker`` and
``DataStore``-like object. All paths are resolved relative to the
caller and no global variables are touched. Users should call
``experiment.save()`` before exporting to ensure that the
``experiment.json`` reflects the final state of the run.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Protocol

import pandas as pd

from aa.util.experiment import ExperimentTracker


__all__ = ["export_replication_package"]


class DataStoreLike(Protocol):
    """Minimal protocol required by the replication exporter."""

    def list_datasets(self) -> list[str]:
        """Return dataset names."""
        ...

    def load_dataset(self, name: str) -> Any:
        """Load a dataset by name."""
        ...


def export_replication_package(
    experiment: ExperimentTracker,
    datastore: DataStoreLike,
    *,
    output_dir: str | Path,
) -> None:
    """Export a replication package for a completed experiment.

    Parameters
    ----------
    experiment : ExperimentTracker
        The tracker containing metadata about the experiment.
    datastore : DataStoreLike
        A datastore-like object used by the pipeline. All datasets
        present in the datastore will be exported.
    output_dir : str or Path
        Destination directory for the replication package. If the
        directory exists it will be overwritten; if not it will be
        created.

    Notes
    -----
    The exported datasets are written both as CSV (for human
    readability) and Parquet (for efficient loading). Metadata is
    stored in JSON to facilitate programmatic inspection.
    """
    out_path = Path(output_dir).expanduser().resolve()

    if out_path.exists():
        for child in out_path.rglob("*"):
            if child.is_file():
                child.unlink()

        for child in sorted(out_path.rglob("*"), reverse=True):
            if child.is_dir():
                try:
                    child.rmdir()
                except OSError:
                    pass

    out_path.mkdir(parents=True, exist_ok=True)

    exp_meta = experiment.to_dict()
    with open(out_path / "experiment.json", "w", encoding="utf-8") as file:
        json.dump(exp_meta, file, indent=2, default=str)

    data_dir = out_path / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    meta_file = data_dir / "metadata.json"
    try:
        meta: dict[str, Any] = getattr(datastore, "_metadata", {})
        if not isinstance(meta, dict):
            meta = {}
    except Exception:
        meta = {}

    with open(meta_file, "w", encoding="utf-8") as file:
        json.dump(meta, file, indent=2, default=str)

    for name in datastore.list_datasets():
        try:
            loaded = datastore.load_dataset(name)
        except FileNotFoundError:
            continue

        if isinstance(loaded, pd.DataFrame):
            df = loaded
        elif hasattr(loaded, "to_table"):
            df = loaded.to_table().to_pandas()
        else:
            raise TypeError(
                f"Unsupported dataset type for '{name}': {type(loaded).__name__}"
            )

        df.to_csv(data_dir / f"{name}.csv", index=False)
        df.to_parquet(data_dir / f"{name}.parquet", index=False)

    readme_path = out_path / "README.md"
    with open(readme_path, "w", encoding="utf-8") as file:
        file.write(f"# Replication package for experiment {experiment.id}\n\n")
        file.write(
            "This folder contains all artefacts needed to reproduce the results "
            "of a single experiment executed with the Assaying Anomalies "
            "research platform.\n\n"
        )
        file.write("## Contents\n\n")
        file.write(
            "* `experiment.json`: Machine-readable metadata about the "
            "experiment.\n"
        )
        file.write(
            "* `data/metadata.json`: Metadata for each dataset saved by the "
            "pipeline.\n"
        )
        file.write(
            "* `data/*.csv` and `data/*.parquet`: Datasets produced by the "
            "pipeline.\n"
        )
        file.write("\n## How to reproduce\n\n")
        file.write(
            "1. Install the same software versions recorded in "
            "`experiment.json`.\n"
        )
        file.write("2. Download and extract this replication package.\n")
        file.write("3. Load the exported data files in your analysis code.\n")
        file.write(
            "4. Recreate tables and figures using the recorded configuration.\n"
        )
        file.write("\n## Contact\n\n")
        file.write(
            "If you encounter issues reproducing the results, consult the "
            "original repository or contact the maintainers.\n"
        )