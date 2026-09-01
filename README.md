# IPPoseRep

Identity-Preserving Pose Representation research workspace for NTU RGB+D 120
skeleton experiments. The repository includes a small, standard-library
experiment harness that makes dataset splits, experiment dependencies,
provenance, resume state, and acceptance evidence explicit.

## Quick start

```powershell
python scripts/prepare_data.py D:\path\to\ntu120\skeleton --protocol xsub
python scripts/run_experiment.py m0_skeletonx_baseline --dry-run
```

The versioned M0/M1/M2 definitions intentionally contain no training command
until their actual model entry points and environments are confirmed. See
[`docs/runbooks/experiment_workflow.md`](docs/runbooks/experiment_workflow.md)
for the complete workflow and output contract.

Project documentation is indexed in [`docs/README.md`](docs/README.md).
