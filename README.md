<!--
        README for the Assaying Anomalies Python library.

        This document is intended to be both the landing page on GitHub and
        the long description displayed on PyPI.  It provides an overview
        of the project, installation instructions, feature highlights and
        links to further documentation.  The badges at the top reflect
        build status, latest PyPI release and licence.
    -->

# Assaying Anomalies – Python Library

![CI](https://github.com/Hello-Surya/AssayingAnomalies-Python/actions/workflows/tests.yml/badge.svg)
![Python](https://img.shields.io/badge/python-3.9%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

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

To install the latest stable release from
[PyPI](https://pypi.org/project/assaying-anomalies/), run:

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

## Reproducible environments

To ensure that results can be reproduced and that collaborators are
working in identical setups, we provide two environment specification
files: `environment.yml` and `requirements-dev.txt`.  These files pin
the versions of Python and all runtime and development dependencies.

To create the environment using conda, run:

```bash
conda env create -f environment.yml
conda activate assaying-anomalies-env
```

Alternatively, you can install the development dependencies with pip:

```bash
pip install -r requirements-dev.txt
```

These files mirror the dependencies defined in the project's
`pyproject.toml` and include additional tooling such as
`pytest`, `black` and `mypy` for development.

## Synthetic data testing

Users who do not have access to WRDS can still experiment with the
library using synthetic data.  The module `aa/data/synthetic_generator.py`
implements a `generate_synthetic_panel` function that simulates
panel data of stock returns, market equity and a predictive signal.
The integration test in `tests/test_full_pipeline.py` uses this
generator to run a complete anomaly pipeline – univariate sorts,
portfolio return calculation and Fama–MacBeth regressions – without
any external data.  This makes it easy to verify the installation and
understand the API before working with real CRSP/Compustat inputs.

## Repository maintenance and release tools

Several scripts under `scripts/` help maintain the health of the
repository and produce reproducible releases:

* **`scripts/run_repo_diagnostics.py`** – Runs the test suite, checks
  that documentation and environment files exist and attempts to import
  the package.  Use this script to validate the repository before
  submitting a pull request.
* **`scripts/create_versioned_release.py`** – Bumps the version number
  in `pyproject.toml`, builds source and wheel distributions with
  `python -m build`, archives the release and generates a release notes
  template.  This script streamlines the process of preparing a new
  PyPI release.

## Replication package and reproducibility

This repository includes a dedicated replication package designed to
facilitate long‑term archival and reproducibility of research results.
All replication resources live in the top‑level `replication/` directory.
Within this directory you will find configuration files defining
experiments (`replication/configs/`), as well as output subdirectories
for tables, figures and logs.  The command‑line scripts used to run
experiments and generate summary reports live in the top‑level
`scripts/` directory; `replication/scripts/` exists only as a
placeholder for compatibility with journal replication package
conventions.  See
`docs/replication_guide.md` for a detailed overview of the structure
and how to use it.

To run a replication experiment, invoke the runner script with a YAML
configuration file.  For example:

```bash
python scripts/run_replication_experiment.py --config replication/configs/size_anomaly.yaml
```

The runner will seed all random number generators, load or generate the
dataset, compute the specified anomaly signal, form portfolios, run a
Fama–MacBeth regression and save tables and figures to the appropriate
subdirectories.  It also writes a machine‑readable manifest and
reproducibility metadata to help verify and archive the results.  A
summary report aggregating multiple experiments can be generated via

```bash
python scripts/generate_replication_summary.py --outputs_dir replication/outputs --output replication/replication_summary.md
```

These features make it straightforward to share and reproduce
experiments, ensuring that published findings remain transparent and
verifiable.

## Licence

This project is released under the terms of the MIT licence.  See
[`LICENSE`](LICENSE) for the full text.

## Project verification and artifact generation

To provide long‑term reproducibility guarantees, the repository now
includes a comprehensive verification and artifact generation
framework.  The `scripts/verify_full_project.py` script performs an
end‑to‑end health check: it imports the package, generates synthetic
data, runs an example pipeline, executes a replication experiment and
invokes the test suite.  A JSON report summarising the outcome of
each check is written to disk.  Invoke the verifier with:

```bash
python scripts/verify_full_project.py
```

The `scripts/build_research_artifact.py` script wraps the verifier and
replication runner to produce a complete research artifact.  It
collects the outputs (tables, figures and logs), the configuration
files used, the verification report and reproducibility metadata into
a single directory, along with a machine‑readable manifest.  Build an
artifact with:

```bash
python scripts/build_research_artifact.py --artifact-dir artifact
```

The resulting `artifact/` directory can be archived or shared to allow
others to reproduce the experiments without ambiguity.

## Preparing a final release

The `scripts/prepare_final_release.py` script automates the final
release process.  It runs the full verification, builds source and
wheel distributions, packages a snapshot of the repository and
generates release notes by collating the archival documentation and
project completion report.  Use it as follows:

```bash
python scripts/prepare_final_release.py --output-dir release
```

This will create a `release/` directory containing the distributions,
repository snapshot, pre‑release verification report and release
notes.  Together with the research artifact, these files ensure that
the Assaying Anomalies Python library is ready for long‑term
archival and future reproducibility studies.