# Changelog

All notable changes to this project will be documented in this file.  The
format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] – 2026‑03‑15

### Added

* **Complete port of the MATLAB library** – The Python package now
  encompasses all major functionality from the original Assaying Anomalies
  toolkit: anomaly signal construction, univariate and double sorts, Fama–
  MacBeth regressions with Newey–West adjustments, multi‑signal evaluation,
  summary statistics, paper‑style tables and figures, export utilities and
  end‑to‑end replication scripts.

* **PyPI‑ready packaging** – The `pyproject.toml` has been overhauled
  with rich metadata (keywords, classifiers, optional dependencies) and
  versioned as 1.0.0.  This release can be built into a wheel and
  source distribution and installed via `pip`.

* **Licensing and contributing guidelines** – Added an MIT `LICENSE` file
  and a comprehensive `CONTRIBUTING.md` explaining how to report issues,
  propose changes, run tests and adhere to the project’s coding standards.

* **Change log** – Introduced this `CHANGELOG.md` to document future
  releases.

* **Tutorial notebooks** – Added a `notebooks/` directory containing a
  Jupyter notebook that walks new users through generating synthetic data,
  computing signals, running portfolio sorts, estimating Fama–MacBeth
  regressions and interpreting the resulting tables and plots.

* **Polished examples** – Enhanced the `examples/` folder with a
  `usage_walkthrough.py` script containing narrative comments to guide
  researchers through common use cases without needing external data.

* **Continuous integration improvements** – Updated the GitHub Actions
  workflow to test on multiple Python versions, run linting and type
  checking, execute the full test suite and verify that wheel and source
  distributions build successfully.

* **Release automation** – Added `scripts/create_release_assets.py` to
  streamline building distribution packages, assembling a release zip and
  generating basic release notes for GitHub.

### Changed

* Updated the `README.md`, `PORTING.md` and documentation to reflect
  final release status, including installation instructions via PyPI,
  pointers to the new notebooks and contribution guidelines.

* Bumped the version number from 0.1.0 to 1.0.0.

### Removed

* Removed vestigial development utilities and obsolete CI workflows.

## [0.1.0] – 2025‑??

* Initial pre‑release version capturing milestones 1–10 of the
  MATLAB‑to‑Python translation.  Not published on PyPI.
