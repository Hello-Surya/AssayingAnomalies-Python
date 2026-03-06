"""
Replication package exporter
===========================
This module provides a utility function to generate a replication
package from a completed experiment.  A replication package bundles
together the experiment metadata and the datasets produced by the
pipeline so that other researchers can reproduce every table and
figure exactly.  The exported files are plain text (JSON and CSV)
and Parquet to maximise interoperability.

The function is deliberately conservative: it does not assume any
external context beyond the provided ``ExperimentTracker`` and
``DataStore`` instances.  All paths are resolved relative to the
caller and no global variables are touched.  Users should call
``experiment.save()`` before exporting to ensure that the
``experiment.json`` reflects the final state of the run.

Example usage::

    from aa.export.replication import export_replication_package
    export_replication_package(experiment, datastore, output_dir="replication/size_v1")

This will create a folder ``replication/size_v1`` containing:

* ``experiment.json`` – metadata describing the experiment (config,
  environment, pipeline structure, task logs).
* ``data/metadata.json`` – metadata about each dataset saved in the
  datastore.
* ``data/<dataset>.csv`` and ``data/<dataset>.parquet`` – the
  materialised datasets associated with the experiment.
* ``README.md`` – human‑readable instructions on how to reproduce
  results.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from aa.data.datastore import DataStore
from aa.util.experiment import ExperimentTracker

__all__ = ["export_replication_package"]


def export_replication_package(
    experiment: ExperimentTracker,
    datastore: DataStore,
    *,
    output_dir: str | Path,
) -> None:
    """Export a replication package for a completed experiment.

    Parameters
    ----------
    experiment : ExperimentTracker
        The tracker containing metadata about the experiment.  The caller
        should have already invoked ``experiment.save()`` to persist
        logs; however the function will still serialise the current
        in‑memory state.
    datastore : DataStore
        The datastore used by the pipeline.  All datasets present in
        the datastore under the current version will be exported.
    output_dir : str or Path
        Destination directory for the replication package.  If the
        directory exists it will be overwritten; if not it will be
        created.

    Notes
    -----
    The exported datasets are written both as CSV (for human
    readability) and Parquet (for efficient loading).  Metadata is
    stored in JSON to facilitate programmatic inspection.
    """
    out_path = Path(output_dir).expanduser().resolve()
    # Reset or create directory
    if out_path.exists():
        # Remove existing contents
        for child in out_path.rglob("*"):
            if child.is_file():
                child.unlink()
            elif child.is_dir():
                # Leave directories for deletion in next pass
                pass
        # Now remove empty dirs
        for child in sorted(out_path.rglob("*"), reverse=True):
            if child.is_dir():
                try:
                    child.rmdir()
                except OSError:
                    pass
    out_path.mkdir(parents=True, exist_ok=True)
    # Write experiment metadata
    exp_meta = experiment.to_dict()
    with open(out_path / "experiment.json", "w", encoding="utf-8") as f:
        json.dump(exp_meta, f, indent=2, default=str)
    # Export datasets
    data_dir = out_path / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    # Write datastore metadata
    meta_file = data_dir / "metadata.json"
    # Copy metadata from datastore
    try:
        # Load the full metadata mapping directly from datastore._metadata
        # Note: We access the protected member to avoid reading the file again.
        meta: Any = getattr(datastore, "_metadata", {})
    except Exception:
        meta = {}
    with open(meta_file, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, default=str)
    # For each dataset, dump CSV and Parquet
    for name in datastore.list_datasets():
        try:
            df_or_ds = datastore.load_dataset(name)
        except FileNotFoundError:
            continue
        # Materialise if lazy (dataset)
        if not isinstance(df_or_ds, pd.DataFrame):
            # It's an Arrow Dataset; convert to DataFrame
            df = df_or_ds.to_table().to_pandas()
        else:
            df = df_or_ds
        # Write CSV and Parquet
        df.to_csv(data_dir / f"{name}.csv", index=False)
        df.to_parquet(data_dir / f"{name}.parquet", index=False)
    # Write README
    readme_path = out_path / "README.md"
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(f"# Replication package for experiment {experiment.id}\n\n")
        f.write("This folder contains all artefacts needed to reproduce the results of a single experiment executed\n")
        f.write("with the Assaying Anomalies research platform.  It was generated automatically by the\n")
        f.write("`export_replication_package` utility.\n\n")
        f.write("## Contents\n\n")
        f.write("* `experiment.json`: Machine‑readable metadata about the experiment (configuration, software versions,\n")
        f.write("  pipeline fingerprint, task logs).\n")
        f.write("* `data/metadata.json`: Metadata for each dataset saved by the pipeline (rows, columns, hashes, etc.).\n")
        f.write("* `data/*.csv` and `data/*.parquet`: The datasets produced by the pipeline.  These files can be loaded\n")
        f.write("  into Python, R or other statistical software to regenerate tables and figures.\n")
        f.write("\n")
        f.write("## How to reproduce\n\n")
        f.write("1. Install the same versions of the software packages recorded in `experiment.json` (see the\n")
        f.write("   `environment` section).  Using conda or virtualenv is recommended.\n")
        f.write("2. Download the replication package and extract it to a convenient location.\n")
        f.write("3. Load the datasets from the `data` directory into your analysis script.  For example, in Python:\n")
        f.write("\n")
        f.write("```python\n")
        f.write("import pandas as pd\n")
        f.write("df = pd.read_csv('data/your_dataset.csv')\n")
        f.write("```\n")
        f.write("\n")
        f.write("4. Recreate the tables or figures by following the analysis code referenced in the original\n")
        f.write("   experiment.  Because all parameters and seeds are recorded, your results should match bit‑for‑bit.\n")
        f.write("\n")
        f.write("## Contact\n\n")
        f.write("If you encounter issues reproducing the results, please consult the original repository or\n")
        f.write("contact the maintainers.\n")
