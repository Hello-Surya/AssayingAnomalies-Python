# Porting Notes: MATLAB to Python

This document captures considerations when porting the original
Assaying Anomalies codebase (implemented in MATLAB) to the
modern Python platform.  Earlier milestones have already re‑created
the statistical logic; Milestone 5 focuses on engineering maturity.

## High‑level differences

### Data representation

- **MATLAB:** Traditionally uses dense matrices and `.mat` files.
  Working with large CRSP/Compustat datasets can be memory‑intensive
  and is often bound by MATLAB’s data structures.
- **Python:** Utilises `pandas` DataFrames and Apache Parquet for
  storage.  Parquet supports columnar compression and lazy scanning.
  This enables the platform to handle WRDS‑scale data on commodity
  hardware.  Lazy scanning via Arrow is particularly beneficial when
  only a subset of columns is needed.

### Caching and reproducibility

- **MATLAB:** Caching is ad hoc; intermediate results are often saved
  as `.mat` files without associated metadata.
- **Python:** The `DataStore` provides deterministic caching with
  versioning and rich metadata (row counts, column names, hashes,
  timestamps).  Metadata follows recommendations from reproducibility
  literature【196710000405780†L378-L404】.  Cache invalidation is explicit.
  There is no silent reuse of stale files.

### Parallel execution

- **MATLAB:** Parallel computing is available but requires the
  Parallel Computing Toolbox.  Random number streams must be
  carefully managed to avoid duplication.
- **Python:** Parallelism is provided via `joblib.Parallel`.  The
  pipeline assigns unique seeds to each task to avoid global state
  duplication【59230597817682†L90-L127】.  Serial and parallel runs are
  guaranteed to be equivalent by joblib’s ordering semantics【704718591959143†L14-L24】.

### Experiment tracking

- **MATLAB:** Limited built‑in facilities for experiment logging.
  Users typically rely on manual record keeping.
- **Python:** The `ExperimentTracker` records configuration
  fingerprints, environment versions, pipeline fingerprints and task
  logs.  Each experiment receives a unique ID which can be exported
  alongside the datasets for replication.

### Code organisation

- **MATLAB:** Scripts and functions in a flat hierarchy.  Global
  variables are common and functions can implicitly depend on
  workspace state.
- **Python:** A structured package with clear separation between
  modules (`aa.data`, `aa.engine`, `aa.util`, `aa.export`).  Global
  state is avoided; all functions accept explicit parameters.  This
  improves testability and reproducibility.

## Guidance for porting additional functionality

When extending the Python platform with new econometric methods or
anomalies, keep the following principles in mind:

1. **Avoid global state.**  Do not rely on module‑level variables
   for configuration or random seeds.  Pass them explicitly through
   function arguments or the `ExperimentTracker`.
2. **Use vectorisation and efficient data structures.**  Where
   possible, exploit `pandas` vectorised operations instead of
   loops.  For compute‑heavy operations, consider `NumPy` and
   optional Numba acceleration, but isolate JIT code to avoid
   determinism issues.
3. **Respect the pipeline API.**  Encapsulate each logical step as
   a `Task` and declare its dependencies.  Use the `checkpoint`
   option to persist intermediate results when beneficial.
4. **Document your work.**  Update `ARCHITECTURE.md` and
   `REPRODUCIBILITY.md` as the system evolves.  Provide clear
   instructions for replicating your results.

By adhering to these guidelines, the Python implementation will
maintain the analytical fidelity of the original MATLAB code while
achieving greater scalability, transparency and reproducibility.
