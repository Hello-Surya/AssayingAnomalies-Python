# Assaying Anomalies – Python Library

![CI](https://github.com/Hello-Surya/AssayingAnomalies-Python/actions/workflows/tests.yml/badge.svg)
![Python](https://img.shields.io/badge/python-3.9%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

Python translation of the **Novy-Marx & Velikov (2023) “Assaying Anomalies” toolkit** for empirical asset-pricing research.

---

# CONTENTS

1. Introduction  
2. Requirements  
3. Inputs  
4. Installation  
5. Setup  
6. Usage  
7. Feature Highlights  
8. Synthetic Data Testing  
9. Reproducible Environments  
10. Repository Maintenance Tools  
11. Documentation  
12. Contributing  
13. Acknowledgements  
14. References  

---

# INTRODUCTION

**Note:** Please cite *Novy-Marx and Velikov (2023)* when using this repository.

Original MATLAB Toolkit Authors  
- Mihail Velikov – velikov@psu.edu  
- Robert Novy-Marx – robert.novy-marx@simon.rochester.edu  

Python Translation  
- Surya Pratap Singh Suryavanshi - suryavanshi@psu.edu

---

The **Assaying Anomalies** project provides a rigorous protocol for evaluating cross-sectional stock return predictors (anomalies) in empirical asset-pricing research.

This repository contains a **Python implementation of the MATLAB toolkit** developed by Novy-Marx and Velikov.

The goal of the translation is **strict functional fidelity** while improving:

- reproducibility  
- usability  
- testing  
- extensibility  

The library enables researchers to conduct the most common empirical asset-pricing workflows in only a few lines of Python.

These include:

- anomaly signal construction  
- univariate portfolio sorts  
- double portfolio sorts  
- Fama-MacBeth cross-sectional regressions  
- performance evaluation metrics  
- generation of tables and figures  
- complete anomaly testing pipelines  

The Python version adds several improvements over the MATLAB toolkit:

- modular package architecture  
- extensive unit testing  
- synthetic datasets for reproducible demonstrations  
- environment reproducibility  
- continuous integration  
- developer documentation  

The library is designed to be used both for **academic research** and for **educational purposes in empirical asset pricing**.

---

# REQUIREMENTS

Full usage of the anomaly testing protocol requires financial datasets commonly used in empirical asset-pricing research.

Recommended data sources include:

WRDS subscription with access to

- Monthly CRSP  
- Daily CRSP  
- Annual COMPUSTAT  
- Quarterly COMPUSTAT  
- CRSP-COMPUSTAT merged dataset (CCM)

However, the repository includes **synthetic dataset generators** so that the entire pipeline can be run without proprietary datasets.

---

# SOFTWARE REQUIREMENTS

The library requires:

- Python **3.9 or newer**

Core dependencies:

- pandas  
- numpy  
- statsmodels  
- scipy  
- matplotlib  

Development dependencies:

- pytest  
- ruff  
- black  
- mypy  

---

# INPUTS

The anomaly pipeline operates on panel data stored in a pandas DataFrame.

Typical columns include:

| Column | Description |
|------|-------------|
| permno | CRSP permanent security identifier |
| date | observation date |
| ret | stock return |
| me | market equity |
| signal | anomaly predictor |

Additional firm characteristics can be included depending on the anomaly being tested.

Dates should typically be stored as pandas `datetime64` objects and are expected to follow **monthly frequency**.

A detailed description of the expected dataset structure is provided in:

`docs/data_interface.md`

---

# INSTALLATION

Clone the repository

```bash
git clone https://github.com/Hello-Surya/AssayingAnomalies-Python.git
cd AssayingAnomalies-Python
