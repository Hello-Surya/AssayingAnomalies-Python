<!--
    README for the Assaying Anomalies Python library.

    This document is intended to be both the landing page on GitHub and
    the long description displayed on PyPI.  It provides an overview
    of the project, installation instructions, feature highlights and
    links to further documentation.  The badges at the top reflect
    build status, latest PyPI release and licence.
-->

# Assaying Anomalies – Python Library

[![Build Status](https://github.com/Hello-Surya/AssayingAnomalies-Python/actions/workflows/tests.yml/badge.svg?branch=main)](https://github.com/Hello-Surya/AssayingAnomalies-Python/actions/workflows/tests.yml)
[![PyPI Version](https://img.shields.io/pypi/v/assaying-anomalies.svg?color=blue)](https://pypi.org/project/assaying-anomalies/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

The **Assaying Anomalies** project provides a rigorous, open‑source
protocol for evaluating cross‑sectional stock return predictors.  This
repository contains a complete Python translation of the MATLAB toolkit
originally developed by Robert Novy‑Marx and Mihail Velikov.  The aim is
strict functional fidelity: all major features of the MATLAB library
have been ported to Python, including anomaly signal construction,
portfolio sorts, Fama–MacBeth regressions, evaluation metrics,
publication‑quality tables and figures, and an end‑to‑end replication
pipeline.

## Installation

The package requires Python ≥ 3.9 and relies on standard scientific
libraries such as `pandas`, `numpy`, `statsmodels` and `matplotlib`.

To install the latest stable release from [PyPI](https://pypi.org/project/assaying-anomalies/), run:

```bash
pip install assaying-anomalies
```

If you wish to modify the code locally or work on the development version,
clone the repository and install it in editable mode along with
development dependencies:

```bash
git clone https://github.com/Hello-Surya/AssayingAnomalies-Python.git
cd AssayingAnomalies-Python
pip install -e .[dev]
```

This will install the package itself plus testing and linting tools
such as `pytest`, `ruff` and `mypy`.

## Feature highlights

* **Pure functions for anomaly signals** – Compute standard predictors
  (size, book‑to‑market, momentum, investment and profitability) using
  concise, well‑tested functions.  Signals operate on `pandas`
  DataFrames and return a uniform interface suitable for merging and
  analysis.

* **Univariate and double sorts** – Form equal‑ and value‑weighted
  portfolios on one or two characteristics using flexible sorting
  configurations.  Compute high‑minus‑low spreads and examine time‑series
  of portfolio returns.

* **Two‑pass regressions** – Run Fama–MacBeth regressions with
  automatic Newey–West standard errors to estimate risk prices for
  one or multiple signals simultaneously.

* **Multi‑signal evaluation pipeline** – Evaluate arbitrary sets of
  signals in a single call, producing dictionaries of performance
  metrics (mean return, t‑statistic, Sharpe ratio, drawdown, turnover,
  etc.).

* **Tables and figures** – Generate publication‑quality tables and
  figures that mirror those in the original MATLAB documentation.

* **Command‑line scripts** – Orchestrate the full anomaly pipeline
  without writing any custom code via scripts in the `scripts/`
  directory.

* **Extensible and reproducible** – The codebase is modular and
  documented, with deterministic behaviours and validation utilities to
  ensure parity with the MATLAB results.  Researchers can easily add
  new signals while preserving the core protocol.

## Quick start

If you prefer to learn by example, open the Jupyter notebook
`notebooks/assaying_anomalies_quickstart.ipynb` after installing the
package.  The notebook demonstrates how to:

1. Generate synthetic CRSP‑ and Compustat‑style data.
2. Compute standard anomaly signals.
3. Perform a univariate portfolio sort and compute high‑minus‑low spreads.
4. Estimate a Fama–MacBeth regression with Newey–West adjustments.
5. Visualise and interpret the resulting tables and plots.

You can also run the self‑contained example scripts in the `examples/`
folder.  For instance:

```bash
python examples/usage_walkthrough.py
```

will execute a narrated walkthrough of the basic workflow on synthetic
data.

## Documentation

Additional documentation lives in the `docs/` directory.  Notable
resources include:

* **`docs/architecture.md`** – High‑level overview of the system design
  and key modules.
* **`docs/usage_guide.md`** – A comprehensive usage guide with code
  samples and explanations.
* **`docs/translation_completion_report.md`** – Details the mapping
  between MATLAB functions and their Python counterparts, alongside
  translation coverage statistics.
* **`PORTING.md`** – Notes on the porting process and final status of
  translation.

## Contributing

Contributions are welcome!  Please read
[`CONTRIBUTING.md`](CONTRIBUTING.md) for guidelines on how to report
bugs, propose improvements, run tests and adhere to the project’s
coding standards.  In brief, we use `black` for formatting, `ruff` for
linting and `mypy` for type checking.  Unit tests live in the
`tests/` directory and can be run with `pytest`.

## Licence

This project is released under the terms of the MIT licence.  See
[`LICENSE`](LICENSE) for the full text.