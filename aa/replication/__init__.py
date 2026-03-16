"""Top-level package for replication utilities.

This subpackage exposes functions for executing replication
experiments based on configuration files.  Use
``aa.replication.runner.run_experiment`` to programmatically run
experiments from within Python.
"""

from .runner import run_experiment  # noqa: F401

__all__ = ["run_experiment"]
