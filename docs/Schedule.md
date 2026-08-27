# EE6008 Human Pose Analytics — Group Instructional Schedule

## 1. Project Direction

Our project is **Instance-Preserving Pose Representation for Multi-Person Action Recognition**.

The central hypothesis is that, for multi-person interactions, explicitly preserving **person identity** and **relative inter-person geometry** will improve recognition of **role-asymmetric actions** compared with representations that merge multiple people into shared pose heatmaps.

The project will focus on **representation design and controlled evaluation**, not on building a new large backbone.

---

## 2. Research Objective

We will construct an **instance-preserving pose representation** without materially increasing backbone complexity, and test whether it improves multi-person interaction recognition.

The project will answer three questions:

1. **Which interaction classes are most affected when person identity is fused or lost?**
2. **Does an independent person stream plus relative displacement / distance / velocity improve recognition?**
3. **Does the gain come from identity preservation and interaction modeling rather than simply from additional parameters?**

---

## 3. Technical Baselines

### Main baseline — SkeletonX
SkeletonX will be the main development baseline. Our modification will be inserted at the **input or fusion stage**, while the main backbone remains unchanged as far as possible.

### Required control — PoseC3D
PoseC3D will be used to test the weakness of **multi-person heatmap fusion** and to provide the principal representation-level comparison.

### Structural reference — ISTA-Net
ISTA-Net will be treated as an interaction-oriented structural reference rather than the main development target.

### Fallback
If SkeletonX cannot be stabilized early because of environment or dependency issues, the project will immediately fall back to **PoseC3D / CTR-GCN** rather than spending multiple weeks repairing the environment.

---

## 4. Data and Evaluation

### Main dataset
**NTU RGB+D 120 — two-person / mutual interaction subset**

We will retain the official:
- Cross-Subject split
- Cross-Setup split

The main report will focus on the **interaction subset**, not full NTU120 overall accuracy.

### Optional validation
**PKU-MMDv2** will only be added after the complete main experiment and ablation pipeline is finished.

### Primary metrics
- Top-1 Accuracy
- Macro-F1
- Per-class Recall for role-asymmetric interaction classes
- Parameter Count
- Throughput
- Identity-Swap Sensitivity

Confusion matrices and representative role-error cases will be part of the final analysis.

---

## 5. Proposed Representation

The final model family will remain small and controlled.

### M0 — Original Baseline
Original SkeletonX representation and classifier.

### M1 — Instance-Preserving Representation
Each person is encoded separately:

`Person A → Person Stream A`

`Person B → Person Stream B`

The two streams are fused only after person-specific information has been retained.

### M2 — Instance + Relative Interaction Representation
M2 extends M1 with explicit inter-person features:

- Relative joint displacement
- Inter-person distance
- Relative velocity

The model therefore represents both **individual motion** and **how one person moves relative to the other**.

### Required ablation
The experiment will separate the effects of:

- person-instance preservation;
- relative position;
- distance;
- velocity;
- additional parameter count.

The comparison must remain parameter-conscious so that performance gains cannot be explained only by a larger network.

---

## 6. Identity Handling

Person ordering will be resolved before the innovation model is finalized.

The preprocessing pipeline will maintain stable person identity across a sequence through tracking or a deterministic ordering rule.

Identity-swap experiments will then deliberately exchange person order to measure model sensitivity.

For role-symmetric interactions, swapping people should have limited effect. For role-asymmetric interactions, the analysis will determine whether preserving role/identity information materially changes prediction behavior.

---

## 7. Compute Budget

The project will use a single GPU.

Target resource:

- **1 × RTX 3090 / RTX 4090, 24 GB**
- PoseC3D: reserve approximately **16–24 GB VRAM**
- Skeleton-only branches can run with less memory
- Main experimental budget: approximately **20–60 GPU-hours**
- Multi-GPU training is not required

---

## 8. Main Risks and Controls

### Unstable person identity
**Control:** lock down person ordering / tracking before large-scale training.

### Interaction improvements hidden by full-dataset accuracy
**Control:** interaction-subset metrics and per-class recall are primary results.

### SkeletonX environment instability
**Control:** establish a reproducible environment immediately; fall back to PoseC3D / CTR-GCN if it cannot be stabilized within the first implementation week.

### Apparent gain caused by model size
**Control:** report parameter count and throughput, and include parameter-matched ablations wherever feasible.

---

# 9. Group Schedule

## Completed Context

### Course Week 1 — 12 Aug to 18 Aug
**Completed**
- Read several key papers in human pose estimation, skeleton-based action recognition, motion representation and pose-language modeling.
- Established the basic technical background.
- Produced the initial research-question list.

### Course Week 2 — 19 Aug to 25 Aug
**Completed / closed**
- Consolidated the project charter.
- Discussed candidate research directions.
- Received the mentor's scoped direction and froze the project around **instance-preserving multi-person pose representation**.

---

## Six-Week Research Core

### Course Week 3 / Scoping Week 1 — 26 Aug to 1 Sep
**Objective: environment and data pipeline must run.**

Tasks:
- Assign owners for dataset, baselines, evaluation and innovation.
- Prepare the NTU RGB+D 120 interaction subset.
- Verify official Cross-Subject and Cross-Setup splits.
- Set up SkeletonX and PoseC3D environments.
- Run at least one baseline end-to-end.
- Define stable person ordering / identity handling.

**Exit condition:** dataset loader, split protocol and at least one baseline are reproducibly runnable.

### Course Week 4 / Scoping Week 2 — 2 Sep to 8 Sep
**Objective: baseline table must exist.**

Tasks:
- Run SkeletonX baseline.
- Run PoseC3D control.
- Record Top-1, macro-F1, per-class recall, parameters and throughput.
- Generate confusion matrices.
- Identify role-asymmetric classes with the largest errors.
- Implement the identity-swap evaluation script.

**Exit condition:** complete baseline results plus first evidence of where identity loss matters.

### Course Week 5 / Scoping Week 3 — 9 Sep to 15 Sep
**Objective: validate the problem before proposing the solution.**

Tasks:
- Complete identity-swap experiments.
- Compare symmetric and asymmetric interaction classes.
- Analyze PoseC3D / SkeletonX failure cases.
- Freeze the exact innovation hypothesis.
- Implement M1: independent person streams with late fusion.

**Exit condition:** clear problem evidence and a runnable instance-preserving prototype.

### Course Week 6 / Scoping Week 4 — 16 Sep to 22 Sep
**Objective: complete the core innovation.**

Tasks:
- Complete M1 experiments.
- Implement M2 relative-interaction branch.
- Add relative displacement, distance and velocity features.
- Keep the backbone unchanged where possible.
- Start baseline vs M1 vs M2 comparison.

**Exit condition:** the complete proposed representation is trainable and evaluable.

### Course Week 7 / Scoping Week 5 — 23 Sep to 29 Sep
**Objective: determine why the method works.**

Tasks:
- Run controlled ablations: baseline; identity only; identity + relative position; identity + position + distance; full model with velocity.
- Report parameters and throughput for every variant.
- Run per-class analysis for role-asymmetric interactions.
- Repeat identity-swap sensitivity tests on the proposed model.

**Exit condition:** quantitative evidence separates identity preservation, interaction features and model-size effects.

### Course Week 8 / Scoping Week 6 — 30 Sep to 6 Oct
**Objective: close the six-week research scope with a defensible conclusion.**

Tasks:
- Finish Cross-Subject and Cross-Setup experiments.
- Consolidate confusion matrices and role-error cases.
- Complete fair comparison with PoseC3D and SkeletonX.
- Use ISTA-Net as structural reference where reproducible.
- Freeze the main results, conclusion and failure cases.

**Exit condition:** the core research question is answered with complete baseline, proposed-method and ablation results.

---

# 10. Final Project Phase

### Course Week 9 — 7 Oct to 13 Oct
**Robustness**
- Add controlled pose noise / missing-joint tests if useful to the final argument.
- Repeat key experiments for statistical reliability.
- Fix implementation and evaluation inconsistencies.

### Course Week 10 — 14 Oct to 20 Oct
**Final quantitative evaluation**
- Produce final tables.
- Finalize efficiency comparison.
- Complete per-class and identity-swap analyses.
- Freeze model checkpoints and experiment configurations.

### Course Week 11 — 21 Oct to 27 Oct
**Extended validation**
- Run PKU-MMDv2 only if all main experiments are already complete.
- Otherwise use this week for deeper failure analysis and stronger ablations.
- Prepare visual examples for successful and failed role recognition.

### Course Week 12 — 28 Oct to 3 Nov
**Report and demonstration**
- Finalize code structure and reproducibility instructions.
- Prepare figures, confusion matrices and architecture diagrams.
- Complete the first full technical report.
- Produce the demonstration pipeline.

### Course Week 13 — 4 Nov to 10 Nov
**Delivery**
- Freeze all results.
- Complete the final report.
- Complete presentation slides and demonstration video.
- Rehearse the presentation and prepare answers for methodology, fairness of comparison, ablation and limitations.

---

# 11. Final Deliverable Logic

The final project will tell one coherent research story:

`Multi-person pose fusion loses identity information`

→ `Role-asymmetric interaction classes are affected`

→ `Instance-preserving streams retain person-specific motion`

→ `Relative geometry explicitly represents interaction`

→ `Controlled ablations separate representation gains from parameter-count gains`

→ `Per-class, identity-swap and efficiency results determine whether the hypothesis is supported`

The project is successful if this causal chain is experimentally clear, even if the overall NTU120 accuracy gain is small.
