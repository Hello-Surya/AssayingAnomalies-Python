#!/usr/bin/env python
"""
Script for running replication experiments defined by YAML configuration files.

This entry point wraps the :func:`aa.replication.runner.run_experiment` function
to allow users to execute experiments from the command line.  Pass the path
to a YAML configuration file via the ``--config`` flag.  See the sample
configuration in ``replication/configs/`` for guidance on the available fields.
"""

from __future__ import annotations

import argparse

from aa.replication.runner import run_experiment


def main() -> None:
    """Parse arguments and run the configured experiment."""
    parser = argparse.ArgumentParser(description="Run a replication experiment.")
    parser.add_argument(
        "--config",
        type=str,
        required=True,
        help="Path to the YAML configuration file describing the experiment.",
    )
    args = parser.parse_args()
    run_experiment(args.config)


if __name__ == "__main__":
    main()
