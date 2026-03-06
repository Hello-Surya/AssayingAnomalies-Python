# System Architecture for Assaying Anomalies Python Platform

This document describes the high‑level architecture of the Python
implementation of **Assaying Anomalies** (AA).  Milestone 5 focuses
on transforming a research prototype into a scalable, reproducible,
high‑performance platform suitable for academic and industry use.  To
achieve this, the system is organised into modular layers with clear
boundaries between data handling, computation, orchestration and
reporting.  The following sections outline each layer, highlight
important design decisions, and provide an ASCII architecture diagram.

## Architectural Layers

### Data layer (`aa.data`)

The data layer is responsible for loading, caching and versioning all
datasets used in the pipeline.  It is implemented by the
`DataStore` class (see `aa/data/datastore.py`) and offers the
following features:

- **Memory‑efficient loading** using Apache Parquet and Arrow.  Large
  files can be loaded lazily; only selected columns are materialised
  into memory.  This enables analysis on CRSP/Compustat‑scale data
  without exhausting RAM.
- **Deterministic caching with versioning.**  Cached datasets live
  under `cache_dir/version`.  Each dataset has an associated
  metadata entry recording row counts, column names, creation time
  and a content hash.  Adding metadata to caches is recommended to
  make data discoverable and reproducible【196710000405780†L378-L404】.
- **Automatic cache invalidation**: users can explicitly remove
  stale data.  There is no implicit global state; all directories
  and version strings are passed explicitly.

### Pipeline engine (`aa.engine`)

The `Pipeline` class (see `aa/engine/pipeline.py`) orchestrates the
execution of a directed acyclic graph (DAG) of tasks.  It provides:

- **Deterministic execution**: tasks receive explicit random seeds and
  the pipeline records a fingerprint of its structure.  Identical
  inputs, configuration and seeds yield identical outputs.
- **Parallel and serial equivalence**: independent tasks can run
  concurrently via `joblib.Parallel`.  Joblib guarantees that the
  order of results matches the order of submission【704718591959143†L14-L24】,
  so multi‑core and single‑core executions produce the same sequence
  of outputs.
- **Checkpointing and resume**: tasks can persist their output to
  the datastore.  On subsequent runs, if the fingerprint matches
  the cached metadata then the result is loaded instead of
  recomputed.  This enables resume‑on‑failure and incremental
  development.

### Experiment tracking (`aa.util`)

The `ExperimentTracker` (see `aa/util/experiment.py`) records
configuration parameters, software versions, pipeline fingerprints
and task logs.  It assigns unique experiment IDs based on a
timestamp and a hash of the configuration.  Logging software
versions and random seeds is essential to reproducible research【196710000405780†L378-L404】.

### Export & replication (`aa.export`)

The `export_replication_package` function (see
`aa/export/replication.py`) packages experiment metadata and
datasets into a self‑contained directory.  Datasets are exported
both as CSV and Parquet.  A `README.md` guides users through
reproducing the results.  This export layer ensures that tables and
figures can be regenerated bit‑for‑bit on a different machine.

### Testing & benchmarking (to be implemented)

Milestone 5 introduces a suite of tests and benchmarks (not yet
implemented in this repository) to verify determinism and measure
performance.  Tests will stress the pipeline on synthetic large
datasets, check that parallel and serial executions match exactly,
validate cache correctness and ensure that random seeds produce
reproducible outputs.  Benchmarks will compare execution time on
small vs large samples and guard against performance regressions.

## ASCII Architecture Diagram

The following diagram visualises how the components interact.  Each
box represents a module; arrows denote data flow or function calls.

```
           +-----------------+
           | User Scripts    |
           +-----------------+
                    |
                    v
           +-----------------+      +----------------------+
           | Experiment      |------> JSON config & logs   |
           | Tracker         |      +----------------------+
           +-----------------+
                    |
                    v
           +-----------------+      +----------------------+
           | Pipeline Engine |------> Joblib workers       |
           +-----------------+      +----------------------+
                    |
        +-----------+-----------+
        |                       |
        v                       v
  +-------------+         +-------------+
  | Task funcs  |         | Task funcs  |  (independent branches)
  +-------------+         +-------------+
        |                       |
        v                       v
  +-------------+         +-------------+
  | DataStore   |         | DataStore   |
  +-------------+         +-------------+
        |                       |
        v                       v
  +-------------+         +-------------+
  | Parquet/CSV |         | Parquet/CSV |
  +-------------+         +-------------+
```

The user defines a set of tasks and an experiment configuration.  The
`ExperimentTracker` generates an ID and records metadata.  The
`Pipeline` executes tasks in dependency order, optionally in
parallel, passing results between tasks and seeding random number
generators to ensure determinism【59230597817682†L90-L127】.  When tasks
checkpoint outputs, they call `DataStore.save_dataset`, which writes
Parquet files and metadata.  The export layer can then package the
experiment and datasets for replication.

## Design Philosophy

* **Separation of concerns:**  Data loading, computation, and
  experiment tracking live in separate modules.  This makes the
  system easier to maintain and extend.
* **Explicit parameters:**  Cache directories, versions and random
  seeds are all explicit arguments.  There is no implicit global
  state; this aids reproducibility.
* **Use of open formats:**  Parquet and CSV are widely supported and
  efficient.  Arrow provides lazy scanning for memory efficiency.
* **Minimal dependencies:**  The core system depends only on
  `pandas`, `numpy`, `joblib` and `pyarrow`.  Optional acceleration
  via Numba or Dask can be added in the future but should be
  isolated to avoid interfering with determinism.

This architecture positions Assaying Anomalies as a modern research
platform that scales from laptops to clusters while preserving the
scientific principles of reproducibility and transparency.
