# Porting Notes for Assaying Anomalies – Final Release

This document records the goals, principles and results of porting the
original MATLAB **Assaying Anomalies** library into Python.  It
complements the code comments and provides guidance for developers
interested in understanding how the MATLAB components correspond to
their Python counterparts.  For a full mapping of modules and scripts,
see `docs/translation_completion_report.md`.

## Objectives

The objective of this project is a **strict functional replication** of
the MATLAB code.  No new algorithms, models or research ideas have
been introduced.  The Python code follows the same high‑level
workflow: load data, compute anomaly signals, sort into portfolios,
evaluate performance and produce tables and figures for publication.

Throughout the porting process the emphasis has been on maintaining
the structure and logic of the MATLAB outputs while adopting
idiomatic Python data structures (primarily `pandas` `DataFrame`s).

## Summary of mapping

Each MATLAB function or script has a direct analogue in the Python
package.  For example, the MATLAB `use_library.m` entry point is
implemented as `scripts/run_full_library_replication.py` and its thin
wrapper `scripts/reproduce_assaying_anomalies.py`.  Table generation
routines in MATLAB (`paper_tables.m`, etc.) correspond to the
`aa.reporting.papertables` module; plotting scripts map to
`aa.vis.paper_figures`.  Helper functions for exporting outputs are
consolidated into `aa.reporting.export_utils`.  See the translation
report for the full list.

## Final translation status

With the completion of this release (version 1.0.0), **all core
components** of the MATLAB library have been translated to Python.
Researchers can rely on the `aa` package to reproduce the behaviour of
the MATLAB routines up to numerical precision and minor idiomatic
differences.  The translation has been validated on synthetic and
real‑world data and matched against the MATLAB outputs.  In addition,
examples, notebooks and continuous integration tests have been added to
ensure long‑term maintainability.

### Deviations and limitations

* **Floating‑point differences** – Due to differences in numerical
  libraries and floating‑point arithmetic, results may differ from
  MATLAB at the eighth decimal place.  Validation utilities in
  `aa.validation` provide tolerances for parity checks.

* **Missing‑data handling** – `pandas` may drop rows with missing
  signals or returns more aggressively than MATLAB.  Ensure that your
  input data are cleaned consistently across languages.

* **Performance on huge datasets** – While the Python implementation
  supports Arrow/Parquet and lazy loading, running the full pipeline
  on CRSP‑scale data can be memory intensive.  Use the caching and
  chunking utilities in `aa.data` and `aa.util.experiment` to manage
  resources.

* **GRS test and peripheral functions** – Some specialised statistics
  and diagnostic helpers from the MATLAB toolkit are beyond the scope
  of the core protocol and remain unimplemented.  Contributions to
  extend these areas are welcome but should preserve backwards
  compatibility and be accompanied by tests.

### Future work

The completion of the port opens the door for further community
contributions.  Potential avenues include:

* Providing wrappers around common data sources (e.g. WRDS, CRSP via
  open datasets) to simplify data preparation.
* Extending visualisation utilities with interactive plots.
* Implementing additional robustness diagnostics such as the GRS test
  or alternative sorting schemes.
* Porting peripheral MATLAB helpers that were intentionally omitted.

Please consult `CONTRIBUTING.md` if you are interested in contributing.