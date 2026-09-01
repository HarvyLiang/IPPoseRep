# ADR 0001: Minimal reproducible experiment harness

- Status: accepted
- Date: 2026-08-31

## Context

The project needs to compare staged research changes without losing the exact
dataset split, configuration, dependency, command, or completion evidence for a
run. General-purpose agent harness features would add operational surface area
before the training entry points are stable.

## Decision

Use a repository-native Python harness with these boundaries:

- TOML experiment definitions form a validated dependency graph.
- NTU120 manifests are deterministic and contain the official XSub or XSet split.
- Raw data is read-only; generated manifests and runs live under `data/derived/`.
- Each run has an exclusive lock, an atomically replaced `run.json`, a frozen
  `experiment.toml`, stdout/stderr logs, Git/config/data provenance, and explicit
  preflight, execute, and verify stages.
- Completion requires a successful process plus configured artifacts and finite
  numeric metrics. Exit code zero alone is insufficient.
- Commands are argv lists executed without a shell. Empty commands are allowed
  for versioning and dry-run inspection but cannot execute.

The implementation uses the Python standard library only. Reusable behavior is
kept in `src/ippose_rep/`; scripts are thin command-line adapters.

## Consequences

Runs can be inspected and resumed safely, and M1/M2 cannot start until their
declared predecessor has an accepted completed run. Project-specific training
commands and metric writers still need to be connected once their interfaces
are confirmed. Background scheduling, multi-agent orchestration, MCP services,
and a general-purpose permissions engine remain out of scope.
