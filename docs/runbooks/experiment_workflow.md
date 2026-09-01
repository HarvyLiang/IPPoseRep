# Experiment workflow

## 1. Prepare the NTU120 manifest

Keep extracted NTU data outside version control. Build a deterministic manifest
from the skeleton root:

```powershell
python scripts/prepare_data.py D:\datasets\nturgbd120_skeleton --protocol xsub
```

The command only reads `*.skeleton` names. It writes
`data/derived/manifests/ntu120_xsub.json`, assigns the official train/test split,
uses zero-based action indices for classifiers, and records a fingerprint over
sorted relative paths and partitions.

Use `--protocol xset` for the official even-setup/odd-setup protocol. Use
`--output` only for a path inside this repository's `data/derived/` directory.

## 2. Configure an experiment

Definitions live in `configs/experiments/*.toml`. Before real execution, replace
the empty `command` with an argv list, for example:

```toml
command = ["python", "scripts/train_model.py", "--config", "configs/model.toml"]
```

Commands run from the project root without a shell. The harness provides these
environment variables to the child process:

- `IPPOSEREP_PROJECT_ROOT`
- `IPPOSEREP_RUN_DIR`
- `IPPOSEREP_RUN_ID`
- `IPPOSEREP_EXPERIMENT_ID`
- `IPPOSEREP_SEED`

The training/evaluation entry point must write all configured artifacts inside
`IPPOSEREP_RUN_DIR`. `metrics.json` must be a JSON object whose required values
are finite numbers.

## 3. Preflight without side effects

```powershell
python scripts/run_experiment.py m0_skeletonx_baseline --dry-run
```

Dry-run validates the experiment registry, dataset manifest, and accepted
dependency runs. It reports missing inputs, returns a nonzero exit code when the
experiment is not ready, and never creates a run directory.

The current graph is:

```text
m0_skeletonx_baseline
└── m1_dgcn_identity
    └── m2_pom_refinement
```

## 4. Run or resume

```powershell
python scripts/run_experiment.py m0_skeletonx_baseline --run-id m0-seed-20260831
python scripts/run_experiment.py m0_skeletonx_baseline --run-id m0-seed-20260831 --resume
```

Outputs are isolated under
`data/derived/experiment_runs/<run-id>/`. A resume is rejected if the config,
dataset fingerprint, seed, command, or experiment identity changed. Concurrent
writes to the same run are rejected by `.run.lock`.

## 5. Verify persisted evidence

```powershell
python scripts/verify_experiment.py data/derived/experiment_runs/m0-seed-20260831
```

Verification checks the frozen configuration, Git/config/data provenance,
successful execute stage, required files, and required finite numeric metrics.
It returns exit code 0 only when all checks pass.

## Run files

- `run.json`: atomic journal and acceptance result.
- `experiment.toml`: immutable config snapshot used by verification.
- `stdout.log` and `stderr.log`: captured child-process output.
- Model-defined artifacts such as `metrics.json`, `environment.json`, and
  `confusion_matrix.png`.

Generated data and run directories are intentionally ignored by Git. Promote
human-readable conclusions to `reports/experiments/` and record the run id and
fingerprints used to produce them.
