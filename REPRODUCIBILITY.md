# Reproducibility Guide

Reproducible research is at the heart of empirical finance.  This
guide explains how the Assaying Anomalies Python platform ensures
that every result can be regenerated and how you, as a researcher or
practitioner, can take advantage of these features.

## Principles of Reproducibility

1. **Determinism:** Given the same inputs and seeds, the pipeline
   produces identical outputs.  Random number generators are seeded
   explicitly for each task to avoid cross‑process state leakage【59230597817682†L90-L127】.
2. **Data provenance:** All datasets are stored in versioned caches
   along with metadata (rows, columns, hashes).  Caching literature
   emphasises the importance of storing metadata such as software
   versions and creation times to make cached data findable and
   reproducible【196710000405780†L378-L404】.
3. **Configuration hashing:** Experiment configurations are hashed and
   logged.  Changing a parameter produces a different experiment ID,
   ensuring that results are not silently overwritten.
4. **Environment capture:** Versions of Python, NumPy, pandas and
   other key libraries are recorded so that the software stack can be
   reconstructed.

## How to reproduce an experiment

Follow these steps to replicate the results of an Assaying Anomalies
experiment:

1. **Obtain the replication package.**  The original author should
   provide a replication folder produced by
   `export_replication_package`.  This folder contains `experiment.json`,
   `data/metadata.json` and one file per dataset in both CSV and
   Parquet formats.
2. **Create a consistent environment.**  Read the `environment`
   section of `experiment.json` and install the same versions of
   Python and the listed packages.  Using Conda or a virtual
   environment can help isolate dependencies.  Matching library
   versions is critical because different versions may change
   algorithms (e.g., random number generators) and lead to
   different outputs【59230597817682†L90-L127】.
3. **Load the datasets.**  Use `pandas.read_csv` or `pandas.read_parquet`
   to read the datasets from the `data` directory.  For large
   datasets, you can use `pyarrow.dataset` to scan columns lazily.
4. **Inspect the configuration.**  The `config` field in
   `experiment.json` describes the signals, filters and other
   parameters used in the run.  Reimplement or reuse the analysis
   code with these exact settings.
5. **Regenerate the analysis.**  Apply the same transformations,
   regressions or portfolio constructions.  Because the data and
   configuration are identical, your tables and figures should match
   the original.  You can also validate the DataFrame hashes in
   `data/metadata.json` to ensure the datasets have not been tampered with.

## Recommendations for authors

* **Call `experiment.save()`** at the end of your pipeline runs to
  persist the metadata.  Without saving, the in‑memory tracker will
  not be serialised.
* **Use descriptive dataset and experiment names.**  This makes it
  easier for others to understand what each file represents.
* **Avoid side effects.**  Never write to global variables or rely on
  global random state; pass parameters and seeds explicitly.

## Using version control for data

While the DataStore manages local caching, consider using a
data‑versioning tool (e.g., [DVC](https://dvc.org/)) for long‑term
storage.  DVC associates data files with Git commits so that
experiments can be reproduced by checking out the exact code and
data versions【828862989152764†L54-L63】.  Combined with the experiment
tracking described here, this creates a robust reproducible
workflow.

By following these guidelines and using the built‑in tracking
mechanisms, you can ensure that your empirical finance research is
transparent, credible and easy for others to replicate.
