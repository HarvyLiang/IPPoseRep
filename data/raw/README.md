# Raw data

This directory is reserved for local, immutable source data. Raw NTU RGB+D
archives and extracted skeleton files are ignored by Git. Prefer an external
dataset location and pass its path to `scripts/prepare_data.py`.

Do not modify raw inputs during preprocessing. Derived manifests, caches, and
experiment outputs belong in `data/derived/`.
