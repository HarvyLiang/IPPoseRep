# SkateFormer Baseline Experimental Results

**NTU RGB+D 120 Interaction-26 | Cross-subject Train/Val/Test protocol**  
**EE6008 project baseline report | 22 September 2026**

## 1. Executive Summary

This report evaluates two independently trained SkateFormer streams and their fixed, equal-weight score fusion on the held-out Interaction-26 Test split. The Joint stream processes 3D joint coordinates; the Bone stream derives directed bone vectors from the same skeleton input. Each stream selects its checkpoint using validation Top-1 accuracy. The stored Test logits are fused after inference.

**Primary result.** Equal-weight Joint + Bone fusion achieves **92.20% Test Top-1** and **98.88% Test Top-5** over 11,660 samples. This is **+0.96 percentage points Top-1** and **+0.51 percentage points Top-5** relative to Joint, using the displayed two-decimal results. The fusion weight was fixed at 0.5/0.5; no Test-set weight search was conducted.

Joint alone reaches 91.24% Top-1 and 98.37% Top-5; Bone alone reaches 89.90% and 97.80%. The fusion result is the final SkateFormer baseline for this protocol. The observed gains describe this dataset and split; no statistical-significance or broader state-of-the-art claim is made.

**Experiment path:** Train each stream -> validate every epoch -> save `best_model.pt` at the best validation epoch -> load the best checkpoint -> evaluate Test -> combine aligned raw Test logits at fixed 0.5/0.5 weights.

**Shared input path:** One NPZ -> Joint (`data_type=j`) and Bone (`data_type=b`) -> independent models -> score-level fusion. Bone features are generated dynamically, with no separate Bone NPZ.

![Figure P1. Experimental protocol: validation selects each stream's checkpoint before a single final Test evaluation and fixed score fusion.](figures/experimental_pipeline.png)

<!-- PAGE BREAK -->

## 2. Experimental Setup

The source is the final NTU RGB+D 120 Interaction-26 NPZ. The 26 two-person actions are A050-A060 and A106-A120, remapped to class IDs 0-25. Train, validation, and Test are distinct splits. Both streams use the same samples and class order.

**Table 1. Dataset and input summary**

| Item | Value |
| --- | --- |
| Dataset | NTU RGB+D 120 Interaction-26, cross-subject |
| Classes | 26 interaction actions: A050-A060 and A106-A120 |
| Train / Val / Test | 11,764 / 1,308 / 11,660 samples |
| Stored skeleton layout | `[N, 300, 150]`: 300 frames, 2 persons x 25 joints x 3 coordinates |
| Model input per sample | `[3, 64, 24, 2]`: channels, frames, model joints, persons |
| Modalities | Joint coordinates; dynamically generated Bone vectors |
| Model parameters | 3,609,521 per stream |

**Table 2. Active training configuration, shared by both runs**

| Setting | Value |
| --- | --- |
| Training / evaluation | 500 epochs; validate every epoch; best validation Top-1 selects checkpoint |
| Batch sizes | Global train 128; validation and Test 128 |
| Hardware | 2 x NVIDIA GeForce RTX 3090; logical devices `[0,1]`; PyTorch `nn.DataParallel` |
| Optimizer | AdamW; base LR 0.001; minimum LR 0.00001; weight decay 0.1 |
| Schedule | Cosine; 25-epoch warmup from LR 0.0000001 |
| Loss | LSCE, label smoothing 0.1 |
| Stability | Gradient clipping enabled, maximum norm 1.0 |
| Stream setting | Joint `data_type=j`; Bone `data_type=b` |

The active YAMLs and saved run configs agree on these settings. Each stream has its own independently optimized parameters and its own best checkpoint. The final Test evaluation uses those checkpoints; the fusion itself has no learned parameters.

**Runtime note.** An earlier single-RTX-3090 attempt with global batch 128 ran out of GPU memory during forward (21.83 GiB allocated, 21.88 GiB reserved, about 138 MiB free, and a failed 144 MiB allocation). The completed experiment therefore used two RTX 3090 devices while retaining global batch 128. This observation is recorded in the earlier run's console log.

<!-- PAGE BREAK -->

## 3. Training Behaviour

The TensorBoard records contain 500 validation points per stream and 45,500 training batch points per stream. Figures 1 and 2 show the mean of each epoch's 91 training batches against that epoch's validation value. No synthetic curve points were added. Dashed markers identify the validation-selected checkpoints.

![Figure 1. Joint training and validation Top-1 accuracy. Training values are epoch means of 91 batch records; validation values are per-epoch measurements.](figures/joint_accuracy.png)

![Figure 2. Bone training and validation Top-1 accuracy, using the same aggregation.](figures/bone_accuracy.png)

<!-- PAGE BREAK -->

### Validation comparison and loss

Figure 3 compares the two observed validation trajectories directly. Figure 4 shows LSCE loss; training loss is aggregated per epoch, whereas validation loss is the logged epoch value. Curves show that both runs continued through the configured 500 epochs and that their selected epochs are late in training. The Test split did not enter checkpoint selection.

![Figure 3. Joint and Bone validation Top-1 accuracy. Dashed lines mark epochs 439 and 497, respectively.](figures/validation_comparison.png)

![Figure 4. Training and validation LSCE loss for both streams. Training values are epoch means.](figures/loss_curves.png)

<!-- PAGE BREAK -->

## 4. Single-Stream Results

**Table 3. Validation-selected checkpoints and held-out Test results**

| Stream | Best Val Top-1 | Best epoch | Test loss | Test Top-1 | Test Top-5 |
| --- | ---: | ---: | ---: | ---: | ---: |
| Joint | 97.40% | 439 | 0.89744 | 91.24% | 98.37% |
| Bone | 95.34% | 497 | 0.94391 | 89.90% | 97.80% |

The training logs record best validation accuracies of 0.9740061162079511 and 0.9533639143730887 at epochs 439 and 497. The Test accuracies were reproduced directly from the stored score dictionaries and `y_test`. The reported Test losses were checked by recomputing the repository's 0.1-smoothed LSCE on stored logits and averaging the 128-sample batch means, matching 0.89744 and 0.94391 to five decimal places. These losses are not independent training-log entries.

On this Test split, Joint exceeds Bone by 1.34 percentage points in Top-1 and 0.57 in Top-5 when comparing the displayed two-decimal percentages. Bone nevertheless contributes useful information to the fixed fusion, as the combined result is higher than either individual result. This observation does not identify a causal mechanism.

## 5. Joint + Bone Fusion

For each explicitly matched Test sample key, the two raw-logit vectors are combined as **S_fused = 0.5 S_joint + 0.5 S_bone**. No softmax is applied before fusion. Both score files contain 11,660 matching `test_i` keys, each associated with 26 finite scores. The feeder's `test_i` name maps to row `i` of `y_test`; evaluation does not rely on dictionary iteration order. Each stream's reported Test Top-1 and Top-5 was reproduced before evaluating fusion.

**Table 4. Final held-out Test comparison**

| Method | Test Top-1 | Test Top-5 | Top-1 correct / 11,660 |
| --- | ---: | ---: | ---: |
| Joint | 91.24% | 98.37% | 10,639 |
| Bone | 89.90% | 97.80% | 10,482 |
| **Joint + Bone (0.5/0.5)** | **92.20%** | **98.88%** | **10,751** |

![Figure 5. Held-out Test Top-1 and Top-5 accuracy. The y-axis begins at zero.](figures/test_comparison.png)

<!-- PAGE BREAK -->

## 6. Per-Class Analysis

Fusion performance varies across the 26 action IDs (Figure 6). A059, walking towards each other, has 100.00% Top-1 over 273 samples; A113, cheers and drink, has 99.83% over 575. At the lower end, A107, wield knife towards other person, has 63.19% over 576, and A106, hit other person with something, has 64.35% over 575. These are descriptive class-level results, not explanations for the errors.

![Figure 6. Fused Test Top-1 accuracy for all 26 action IDs. The full action-name mapping is listed in the appendix.](figures/per_class_accuracy.png)

The largest off-diagonal cells are A107 -> A106 (88 samples) and A106 -> A107 (77). A106 -> A050 accounts for 58 samples. The directed counts matter: the row is the true action and the column is the predicted action. Raw counts come from the saved fusion confusion matrix.

<!-- PAGE BREAK -->

### Normalized confusion matrix

Figure 7 normalizes each true-class row to 100%, allowing classes with different Test support to be compared visually. Action IDs are used on both axes to keep the 26 x 26 chart readable; the complete action names are in Appendix A. The raw-count matrix remains available as `fusion_confusion_matrix.csv`.

![Figure 7. Row-normalized fused Test confusion matrix. Rows show true action IDs and columns predicted action IDs; color is percent within each true class.](figures/normalized_confusion_matrix.png)

<!-- PAGE BREAK -->

## 7. Fusion Gain Analysis

Against Joint, the 0.5/0.5 fusion improves displayed Test Top-1 by **0.96 percentage points** (92.20 - 91.24) and Top-5 by **0.51 points** (98.88 - 98.37). Against Bone, the corresponding gains are **2.30** and **1.08 points**. These differences use the displayed two-decimal percentages; differences calculated from unrounded sample counts can differ by 0.01 point after rounding. The fusion adds 112 correct Top-1 predictions over Joint and 269 over Bone.

The gain over both streams indicates complementary predictive information in the two score vectors on this Test set. The experiment does not establish that the same gain holds on other splits or datasets. It also does not measure statistical significance.

## 8. Validation vs Test Behaviour

Joint's best validation Top-1 is 97.40%, versus 91.24% on Test: a displayed gap of **6.16 percentage points**. Bone's best validation Top-1 is 95.34%, versus 89.90% on Test: **5.44 points**. The validation split is smaller than Test (1,308 versus 11,660), and the observed validation accuracy is higher under this split. The report does not assign a definitive cause to the difference.

## 9. Reproducibility and Experimental Integrity

The final NPZ holds distinct Train, Val, and Test members. Both streams share its Test samples and 26-class order. Each checkpoint was chosen by validation Top-1; the protocol uses one final Test evaluation after model selection, and the available artifacts contain one Test score file per stream. The two saved Test score dictionaries were checked for equal key sets, finite 26-element vectors, and agreement with the individual reported metrics. Fusion aligned samples by explicit `test_i` keys.

The fusion weights were fixed at 0.5/0.5 before this Test evaluation. Test performance was not used to scan or select weights, avoiding Test-set hyperparameter tuning. A future optimized weight would require Joint and Bone validation scores, selection on Val alone, and a frozen weight before Test evaluation. The streams were independently trained; the ensemble was not trained end-to-end.

## 10. Conclusions

Joint reaches **91.24%** Test Top-1; Bone reaches **89.90%**. Equal-weight Joint + Bone reaches **92.20%** Test Top-1 and **98.88%** Test Top-5. The fixed fusion is the final SkateFormer baseline for this Interaction-26 cross-subject Train/Val/Test protocol. Its measured improvement applies to the evaluated split.

### Appendix A. Interaction-26 action order

| ID | Action | ID | Action |
| --- | --- | --- | --- |
| A050 | punching/slapping other person | A106 | hit other person with something |
| A051 | kicking other person | A107 | wield knife towards other person |
| A052 | pushing other person | A108 | knock over other person (hit with body) |
| A053 | pat on back of other person | A109 | grab other person's stuff |
| A054 | point finger at the other person | A110 | shoot at other person with a gun |
| A055 | hugging other person | A111 | step on foot |
| A056 | giving something to other person | A112 | high-five |
| A057 | touch other person's pocket | A113 | cheers and drink |
| A058 | handshaking | A114 | carry something with other person |
| A059 | walking towards each other | A115 | take a photo of other person |
| A060 | walking apart from each other | A116 | follow other person |
|  |  | A117 | whisper in other person's ear |
|  |  | A118 | exchange things with other person |
|  |  | A119 | support somebody with hand |
|  |  | A120 | finger-guessing game (playing rock-paper-scissors) |

### Artifact basis

The Joint and Bone run directories provide `log.txt`, `config.yaml`, `best_model.pt`, Test score dictionaries, and TensorBoard `runs/train` and `runs/val` events. The fusion directory provides `fusion_metrics.json`, `fusion_per_class_accuracy.csv`, and `fusion_confusion_matrix.csv`. The exact class labels come from `skateformer/labels.py` and the saved per-class CSV. The earlier single-GPU console log documents the OOM note. No model inference or training was rerun for this report.
