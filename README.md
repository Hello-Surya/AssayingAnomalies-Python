<!--
README for the Assaying Anomalies Python library.

This document serves as both the GitHub landing page and the long
description for the PyPI package. It provides an overview of the
project, installation instructions, feature highlights, and links
to additional documentation.
-->

# Assaying Anomalies – Python Library

![CI](https://github.com/Hello-Surya/AssayingAnomalies-Python/actions/workflows/tests.yml/badge.svg)
![Python](https://img.shields.io/badge/python-3.9%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

The **Assaying Anomalies** project provides a rigorous, open-source protocol for evaluating cross-sectional stock return predictors.

This repository contains a Python translation of the MATLAB toolkit originally developed by **Robert Novy-Marx** and **Mihail Velikov**. The goal is strict functional fidelity: the library supports anomaly signal construction, portfolio sorts, Fama–MacBeth regressions, evaluation metrics, tables, figures, and an end-to-end replication workflow.

---

# Installation

The package requires **Python 3.9+** and relies on standard scientific libraries such as:

- pandas
- numpy
- statsmodels
- matplotlib

To install the development version locally:

```bash
git clone https://github.com/Hello-Surya/AssayingAnomalies-Python.git
cd AssayingAnomalies-Python
pip install -e .[dev]
