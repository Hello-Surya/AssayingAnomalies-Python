# Contributing to Assaying Anomalies (Python)

The goal of this repository is to provide a faithful, open‑source Python
translation of the **Assaying Anomalies** MATLAB library.  We welcome
contributions that improve usability, documentation, performance and
maintainability.  Please keep in mind that the core algorithms are
deliberately kept identical to the original code – we do **not** accept
changes that alter the methodology, introduce new models or stray from
the published protocol unless explicitly coordinated with the
maintainers.

## How to contribute

1. **Open an issue** – If you find a bug, have a question or want to
   propose an enhancement, please open an issue on GitHub.  Include as
   much detail as possible (error messages, versions, steps to
   reproduce, links to relevant lines in the code, etc.).  For
   questions about economic research or extensions of the methodology,
   consider creating a discussion topic instead of an issue.

2. **Fork the repository** – Create your own fork and branch off
   `main`.  Use a descriptive branch name (e.g. `fix-sort-bug` or
   `update-docs-installation`).

3. **Install development dependencies** – From the project root run:
   ```bash
   pip install -e .[dev]
   ```
   This installs the tools required for linting, type checking and
   testing.

4. **Make your changes** – Follow the existing code style.  The
   repository uses [Black](https://github.com/psf/black) for
   formatting, [Ruff](https://github.com/astral-sh/ruff) for linting
   and [Mypy](https://github.com/python/mypy) for optional static
   type checking.  Run the following commands before committing:
   ```bash
   # Format code automatically
   python -m black .

   # Lint and catch stylistic issues
   python -m ruff check .

   # Check type annotations
   python -m mypy aa examples

   # Run the test suite and measure coverage
   python -m pytest -q --cov=aa
   ```

   Ensure that no tests fail and that linting/type checking passes.
   Please add or update tests when fixing bugs or adding features.

5. **Submit a pull request (PR)** – Push your branch to your fork and
   open a PR against the `main` branch of this repository.  Briefly
   describe what the change does and reference any relevant issues.
   The maintainers will review your PR and may request changes before
   merging.

## Coding guidelines

* **Preserve functional parity** – The aim of this port is to mirror
  the MATLAB implementation.  Avoid changing default parameters,
  algorithmic steps or statistical definitions.  If you propose an
  enhancement that deviates from the original methodology, explain why
  it is necessary and provide empirical justification.

* **Write tests** – When fixing a bug or adding non‑trivial logic,
  please accompany your change with a unit test in the `tests/`
  directory.  Tests should be deterministic and rely on synthetic
  inputs where possible.

* **Use descriptive names** – Variable and function names should be
  self‑explanatory.  Favour clarity over brevity.

* **Document your code** – Public functions and classes should have
  docstrings explaining their purpose, parameters, return values and
  any caveats.  Use [PEP 257](https://www.python.org/dev/peps/pep-0257/)
  conventions.

* **Respect the licence** – By contributing to this project you agree
  that your code will be released under the terms of the MIT
  licence.  Do not incorporate code whose licence is incompatible with
  MIT.

## Code of conduct

All contributors are expected to adhere to the
[Contributor Covenant](https://www.contributor-covenant.org/version/2/1/code_of_conduct/).
Be respectful in your communications, and strive to make the project a
welcoming place for researchers from all backgrounds.