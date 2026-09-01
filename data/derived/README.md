# Derived data

Reproducible generated state is written here and ignored by Git:

- `manifests/`: deterministic dataset inventories and split assignments.
- `experiment_runs/<run-id>/`: run journals, logs, config snapshots, metrics,
  and artifacts.

Regenerate these files from versioned code/configuration plus documented raw
inputs. Publish stable conclusions under `reports/`, not from this directory.
