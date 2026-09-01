# Experiment Harness Implementation Plan

Date: 2026-08-31

## Goal

Build a minimal, reproducible experiment harness for the IPPoseRep research
project. The harness must validate NTU RGB+D 120 split metadata, describe the
M0/M1/M2 experiment dependency graph, persist run provenance and stage state,
and verify completion using machine-checkable evidence.

## Scope

Included:

- NTU sample-name parsing and official XSub/XSet assignment.
- Versioned experiment definitions and dependency validation.
- Atomic run journals, run locking, input fingerprints, and resumable stages.
- Preflight, execution, and acceptance-verification command-line entry points.
- Documentation, example M0/M1/M2 configurations, and automated tests.

Excluded:

- SkeletonX, PoseC3D, or CTR-GCN training implementations.
- Dataset download or redistribution.
- GPU job scheduling, multi-agent orchestration, cron, or MCP integration.
- Fabricated baseline commands or metrics.

## Key Decisions

1. Use TOML rather than YAML so Python 3.11+ can load configurations through
   the standard-library `tomllib` module.
2. Keep reusable logic under `src/ippose_rep/`; scripts are thin CLI adapters.
3. Store generated run state under `data/derived/experiment_runs/` and exclude
   it from Git. Versioned experiment definitions remain under `configs/`.
4. Treat `data/raw/` as read-only. All generated data must stay under
   `data/derived/`.
5. Do not infer a training command. A non-dry run fails preflight when an
   experiment has no configured command.
6. A run is complete only when the process succeeded and every configured
   artifact and metric requirement passes verification.

## Implementation Stages

1. Add package metadata and NTU120 split utilities.
2. Add experiment configuration models, registry validation, and dependency
   cycle detection.
3. Add atomic journal persistence, exclusive run locking, stage tracking, and
   provenance fingerprints.
4. Add acceptance checks and CLI commands for data preparation, execution, and
   verification.
5. Add M0/M1/M2 TOML examples, documentation, and repository hygiene rules.
6. Add tests for normal paths, invalid metadata, dependency cycles, locking,
   resume behavior, path boundaries, and acceptance failures.

## Risks and Controls

- **Incorrect official split constants:** copy the complete 53-subject XSub
  training list from the repository's dataset guide and test representative
  train/test boundaries.
- **Overwriting an existing run:** use exclusive lock creation and reject an
  existing run unless the user explicitly selects resume mode.
- **Unsafe output paths:** resolve all paths and require generated outputs to
  remain under `data/derived/experiment_runs/`.
- **Partial journal writes:** write a temporary file, flush it, then replace the
  destination atomically.
- **False completion:** require explicit exit code, metrics, artifacts,
  configuration snapshot, seed, Git commit, and dataset fingerprint evidence.
- **Premature abstraction:** keep the implementation standard-library-only and
  avoid a generic agent/workflow platform.

## Verification

- Run the complete automated test suite.
- Run Python bytecode compilation without writing cache files.
- Run configured formatting and static checks from `pyproject.toml`.
- Exercise all three CLI help commands.
- Dry-run M0 and confirm it reports the missing command and manifest without
  writing state; confirm a real M0 run fails clearly while its training command
  remains unconfigured.
