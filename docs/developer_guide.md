# Developer Guide

This document provides practical guidance for developers working on the
Python port of **Assaying Anomalies**.  It summarises the project
architecture, describes how to set up a development environment, run
tests and adhere to the coding standards, and explains how to extend
the library by adding new translations or functionality.

## Project architecture

The core code lives under the `aa` package.  Each subpackage has a
well‑defined responsibility, closely mirroring the MATLAB original.
The high‑level architecture is summarised here, adapted from the
architecture overview【437123982565559†L15-L33】:

| Module               | Responsibilities |
|---------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `aa.signals`        | Compute anomaly signals from raw data.  Each function accepts a DataFrame and returns a DataFrame with columns `date`, `permno` and `signal`【437123982565559†L15-L33】.  Standard signals include size, book‑to‑market, momentum, investment and profitability. |
| `aa.asset_pricing`  | Portfolio sorting and asset pricing utilities.  Provides univariate sorts (`univariate_sort`), two‑pass Fama–MacBeth regressions (`fama_macbeth` and `fama_macbeth_full`) and configuration classes【437123982565559†L21-L24】. |
| `aa.analysis`       | Evaluation of anomaly performance.  Contains functions to compute mean returns, t‑statistics, Sharpe ratios, drawdowns and turnover【437123982565559†L25-L27】.  Also hosts high‑level pipelines that evaluate multiple signals together. |
| `aa.prep`           | Data preparation routines.  Functions like `crsp.py` and `compustat.py` load raw data, apply filters and construct a consistent panel; `build_panel.py` merges returns and fundamentals【437123982565559†L29-L33】. |
| `aa.pipeline`       | Orchestrates full workflows.  Scripts in this subpackage read prepared data, compute signals, run portfolio sorts or regressions, and generate output tables and figures【437123982565559†L34-L37】. |
| `aa.reporting`      | Generation of publication‑quality tables.  Modules such as `paper_tables.py` and `anomaly_tables.py` produce LaTeX/CSV/Markdown summaries【437123982565559†L38-L40】. |
| `aa.vis`            | Plotting functions used to reproduce figures from the paper【437123982565559†L42-L43】. |
| `aa.validation`     | Reproducibility and parity checks.  Tools in this module compare Python results against MATLAB outputs to ensure the port is correct【437123982565559†L44-L46】. |
| `aa.util`           | Helper functions for dates, reproducibility (seeding) and logging【437123982565559†L47-L48】. |

Additional directories include `examples/` (worked examples on
synthetic data), `scripts/` (command‑line entry points), `tests/`
(unit and integration tests) and `docs/` (documentation).

## Setting up the development environment

To reproduce the development environment exactly, use the provided
conda environment file:

```bash
conda env create -f environment.yml
conda activate assaying-anomalies-env
```

Alternatively, you can install the same dependencies with pip:

```bash
pip install -r requirements-dev.txt
```

These files pin the versions of Python and all runtime and development
packages.  They mirror the dependencies specified in `pyproject.toml`【753162988832289†L16-L26】 and include additional tools such as
`pytest`, `black`, `ruff` and `mypy` for testing, formatting and type
checking【753162988832289†L49-L59】.

## Running tests and diagnostics

Unit tests live in the `tests/` directory and can be executed with
`pytest`:

```bash
pytest -q
```

An integration test in `tests/test_full_pipeline.py` generates a
synthetic dataset and runs the full anomaly pipeline.  This test
ensures that the library functions work together as expected without
relying on external data.

Prior to submitting a pull request, run the repository diagnostics
script:

```bash
python scripts/run_repo_diagnostics.py
```

This script runs the test suite, checks that documentation and
environment files exist and attempts to import the package.  It helps
catch common issues early.

## Coding standards

The project follows a strict coding style to ensure readability and
consistency.  Please adhere to the following guidelines:

* **Formatting** – All Python files should be formatted with
  [`black`](https://black.readthedocs.io/en/stable/).  You can run
  `black .` from the repository root to auto‑format code.
* **Linting** – Use [`ruff`](https://ruff.rs/) to check for
  stylistic issues and common errors.  Run `ruff .` before
  committing.
* **Type checking** – Where possible, add type hints and run
  [`mypy`](https://mypy-lang.org/) to ensure that type constraints
  hold.  The repository is gradually being annotated.
* **Testing** – Write unit tests for new features and ensure that
  existing tests continue to pass.  Use the synthetic generator for
  constructing minimal reproducible examples.

These tools are included in the development dependencies and are run
automatically in continuous integration.

## Adding new translations or functionality

When porting additional MATLAB functions or adding new features,
follow these steps:

1. **Identify the destination module.**  Choose a subpackage in
   `aa` that matches the function’s purpose (e.g. `aa.signals` for a
   new signal, `aa.asset_pricing` for sorting/regression utilities or
   `aa.analysis` for evaluation metrics).
2. **Adopt the design philosophy.**  Ensure that the function accepts
   explicit inputs and returns outputs without side effects.  Operate
   on `pandas` DataFrames rather than relying on global state.
3. **Mirror naming conventions.**  Name the function and its
   arguments consistently with existing Python counterparts.  If the
   MATLAB function is `makeUnivSortInd`, the Python port becomes
   `univariate_sort` and returns a dictionary instead of modifying
   variables in place.
4. **Write documentation and tests.**  Add a docstring explaining
   parameters, behaviour and return values.  Create unit tests that
   compare the Python output against known MATLAB results (if
   available) or at least ensure sensible behaviour on synthetic data.
5. **Update the translation report.**  If the new function is part of
   the MATLAB toolkit, update `docs/translation_completion_report.md`
   to reflect its completion.

By adhering to these guidelines, contributors can extend the library
while maintaining compatibility and reproducibility.