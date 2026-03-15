#!/usr/bin/env python3
"""
Reproduce the Assaying Anomalies library outputs in a single command.

This convenience script runs the full anomaly evaluation pipeline and
produces all paper‑style tables and figures, mirroring the workflow
of the MATLAB ``use_library.m`` example.  It wraps the
``run_full_library_replication.py`` script in this directory and
forwards any command‑line arguments to it.  The only difference is
that default values for a few key arguments are provided here so
that the entire replication can be executed without specifying
anything more than the input dataset.

Typical usage
-------------

```
python scripts/reproduce_assaying_anomalies.py --input data/panel.parquet --output outputs/
```

If ``--signals`` is omitted, all available signals in the dataset
will be evaluated.  The results will be written into the directory
specified by ``--output`` in CSV format by default, and figures will
be saved as PNG files.  See ``scripts/run_full_library_replication.py``
for detailed argument descriptions.

This script is intended for reproducibility and does not introduce
any new functionality beyond what is already provided by
``run_full_library_replication.py``.
"""

from __future__ import annotations

import sys
import subprocess
from pathlib import Path
from typing import List, Optional


def main(argv: Optional[List[str]] = None) -> None:
    """Dispatch to ``run_full_library_replication.py`` with the provided arguments.

    Parameters
    ----------
    argv : list of str, optional
        Command‑line arguments (excluding the program name).  If
        ``None``, ``sys.argv[1:]`` is used.

    Notes
    -----
    This function constructs a subprocess call to invoke the
    ``run_full_library_replication.py`` script residing in the same
    directory as this file.  It uses the current Python interpreter
    (``sys.executable``) to run the child script.  Any arguments
    passed to this wrapper are forwarded unchanged to the downstream
    script, which performs the heavy lifting of loading data,
    evaluating anomalies and exporting the outputs.
    """
    if argv is None:
        argv = sys.argv[1:]
    # Determine the path to run_full_library_replication.py relative to this file
    current_dir = Path(__file__).resolve().parent
    script_path = current_dir / "run_full_library_replication.py"
    # Build the command using the current Python executable
    cmd: List[str] = [sys.executable, str(script_path)] + list(argv)
    # Execute the script as a subprocess and propagate the exit code
    try:
        subprocess.check_call(cmd)
    except subprocess.CalledProcessError as exc:
        # Bubble up errors so that they are visible to the caller
        sys.exit(exc.returncode)


if __name__ == "__main__":
    main()
