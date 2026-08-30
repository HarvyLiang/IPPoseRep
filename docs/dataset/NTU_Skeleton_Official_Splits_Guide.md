# NTU Skeleton 官方划分与 CTR-GCN / SkeletonX 数据使用指南

本文档面向 NTU RGB+D 60（NTU60）和 NTU RGB+D 120（NTU120）的 skeleton-based action recognition 实验，说明官方训练/测试划分、文件名解析、validation 的正确处理方式，以及 CTR-GCN、SkeletonX 的完整数据准备与使用流程。

> 核心原则：官方协议只定义 **training set** 和 **testing set**，没有额外定义 validation set。开发阶段的 validation 必须从官方 training set 内部划分，不能使用官方 testing set 调参、早停或选择 checkpoint。

## 1. 快速对照

| 数据集 | 官方协议 | 训练规则 | 测试规则 |
| --- | --- | --- | --- |
| NTU60 | XSub / CS | 指定的 20 个主体 | 其余 20 个主体 |
| NTU60 | XView / CV | Camera 2、3 | Camera 1 |
| NTU120 | XSub / CSub | 指定的 53 个主体 | 其余 53 个主体 |
| NTU120 | XSet / CSet | 偶数 setup：S002、S004、…、S032 | 奇数 setup：S001、S003、…、S031 |

数据包关系：

- NTU60 使用 `nturgbd_skeletons_s001_to_s017.zip`。
- 完整 NTU120 必须同时使用：
  - `nturgbd_skeletons_s001_to_s017.zip`
  - `nturgbd_skeletons_s018_to_s032.zip`
- `S018–S032` 只是 NTU120 相对 NTU60 的扩展部分，不能单独作为完整 NTU120 使用。

## 2. Skeleton 文件名解析

标准文件名格式：

```text
SsssCcccPpppRrrrAaaa.skeleton
```

可使用以下正则表达式解析：

```regex
^S(\d{3})C(\d{3})P(\d{3})R(\d{3})A(\d{3})\.skeleton$
```

字段含义：

| 字段 | 含义 | 示例 |
| --- | --- | --- |
| `Ssss` | collection setup ID | `S001` |
| `Cccc` | camera ID | `C002` |
| `Pppp` | performer / subject ID | `P003` |
| `Rrrr` | repetition ID | `R002` |
| `Aaaa` | action class ID | `A060` |

示例：

```text
S001C002P003R002A060.skeleton
```

表示：setup 1、camera 2、subject 3、第 2 次重复、动作类别 60。

注意：

- 文件名中的 action ID 从 1 开始；PyTorch 分类标签通常从 0 开始，因此常见转换为 `label = action_id - 1`。
- `S`、`C`、`P`、`R`、`A` 都是实验元数据，不应通过目录顺序或文件排序间接推断。
- 多相机可能记录同一次动作表演。自行制作 validation 时，随机按单文件切分可能让同一次表演的不同相机视角落入不同集合，造成数据泄漏。

## 3. NTU60 官方划分

NTU60 包含 60 个动作类别、40 个主体和 3 个同步相机。官方定义 XSub 和 XView 两种评估协议。

### 3.1 XSub：Cross-Subject

训练主体 ID：

```text
1, 2, 4, 5, 8, 9, 13, 14, 15, 16,
17, 18, 19, 25, 27, 28, 31, 34, 35, 38
```

测试主体 ID：

```text
3, 6, 7, 10, 11, 12, 20, 21, 22, 23,
24, 26, 29, 30, 32, 33, 36, 37, 39, 40
```

划分逻辑：

```text
if P in TRAIN_SUBJECTS_NTU60:
    split = train
else:
    split = test
```

官方论文给出的名义样本数为：

- training：40,320
- testing：16,560

公开 skeleton 文件经过缺失/异常样本排除后，实际生成数量可能略低。应以预处理日志和所用 missing-skeleton 列表为准，并在实验报告中说明。

### 3.2 XView：Cross-View

划分规则：

- training：`C002`、`C003`
- testing：`C001`

```text
if C in {2, 3}:
    split = train
elif C == 1:
    split = test
```

官方论文给出的名义样本数为：

- training：37,920
- testing：18,960

不要误写为 Camera 1、2 训练和 Camera 3 测试。NTU60 官方 XView 明确使用 Camera 2、3 训练，Camera 1 测试。

## 4. NTU120 官方划分

NTU120 是 NTU60 的扩展版本，共 120 个动作类别、106 个主体和 32 个 collection setups。官方定义 XSub 和 XSet 两种评估协议。

### 4.1 XSub：Cross-Subject

训练主体 ID（53 个）：

```text
1, 2, 4, 5, 8, 9, 13, 14, 15, 16, 17, 18, 19,
25, 27, 28, 31, 34, 35, 38, 45, 46, 47, 49, 50, 52,
53, 54, 55, 56, 57, 58, 59, 70, 74, 78, 80, 81, 82,
83, 84, 85, 86, 89, 91, 92, 93, 94, 95, 97, 98, 100, 103
```

测试主体 ID（其余 53 个）：

```text
3, 6, 7, 10, 11, 12, 20, 21, 22, 23, 24, 26, 29,
30, 32, 33, 36, 37, 39, 40, 41, 42, 43, 44, 48, 51,
60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 71, 72, 73,
75, 76, 77, 79, 87, 88, 90, 96, 99, 101, 102, 104, 105, 106
```

NTU120 XSub 不是简单地按奇偶 subject ID 划分，也不能只沿用 NTU60 的 20 个训练主体列表。

### 4.2 XSet：Cross-Setup

训练 setup ID（偶数，共 16 个）：

```text
2, 4, 6, 8, 10, 12, 14, 16,
18, 20, 22, 24, 26, 28, 30, 32
```

测试 setup ID（奇数，共 16 个）：

```text
1, 3, 5, 7, 9, 11, 13, 15,
17, 19, 21, 23, 25, 27, 29, 31
```

划分逻辑：

```text
if setup_id % 2 == 0:
    split = train
else:
    split = test
```

XSet 按文件名中的 `S` 字段划分，不是按 camera ID 划分。不要将 NTU60 的 XView 规则套用到 NTU120 XSet。

## 5. Validation 的正确处理方式

### 5.1 官方没有独立 validation set

NTU60 和 NTU120 的标准协议只定义 official train 与 official test。部分 ST-GCN 系代码把官方测试文件命名为 `val_data.npy`、`val_label.pkl`，或在训练日志中将 test loader 显示为 `val`。这只是代码命名习惯，不代表它是可反复用于调参的官方 validation set。

以下操作会造成测试集信息泄漏：

- 根据 official test accuracy 选择 epoch；
- 使用 official test 调 learning rate、augmentation、模型宽度或 ensemble 权重；
- 多次查看 official test 后只报告最高结果；
- 将仓库中名为 `val`、但实际对应 official test 的数据用于 early stopping。

### 5.2 推荐的开发流程

1. 先严格生成官方 train/test。
2. 仅从 official train 中创建内部 `train-dev` 和 `validation`。
3. 使用 validation 选择超参数、epoch 和 checkpoint。
4. 确定配置后，可使用完整 official train 重新训练。
5. 最后只在 official test 上进行最终评估并报告结果。

### 5.3 内部 validation 的建议划分单位

| 官方协议 | 推荐 validation 分组单位 | 原因 |
| --- | --- | --- |
| NTU60 XSub | subject ID `P` | 保持 train/validation 主体不重叠 |
| NTU60 XView | capture group `(S, P, R, A)`；或明确保留一个训练相机 | 防止同一次表演的不同相机视角跨集合泄漏 |
| NTU120 XSub | subject ID `P` | 保持 train/validation 主体不重叠 |
| NTU120 XSet | setup ID `S`，且只能从偶数 official-train setups 中选 | 保持 train/validation setup 不重叠 |

推荐采用固定 seed，并把实际选中的 validation subject/setup/group 列表保存为文本或 CSV。validation 比例可按实验规模取 official train 的约 5%–15%，但这属于用户自定义协议，不能称为“官方 validation”。

对于 NTU60 XView：

- 若将 `C002` 或 `C003` 整体作为 validation，能够保持 camera-disjoint，但训练数据会明显减少，且只剩一个训练 camera。
- 更实用的方法是按 `(S, P, R, A)` 分组后，从 official train 中按类别分层抽取 validation，并让同组的 `C002`、`C003` 一起进入 train 或 validation。
- 无论采用哪种方法，都应在实验记录中公开说明。

### 5.4 数据变换与统计量

- 逐样本中心化、逐样本裁剪等不依赖其他样本的操作可以在划分前执行。
- 全局 mean/std、类别重采样权重等统计量必须仅由当前训练子集计算。
- augmentation 只应用于训练 loader，validation 和 official test 不启用随机增强。
- 如果为 validation 生成新的 `.npz`，建议保留原始 sample name/manifest，以便审计划分是否正确。

## 6. CTR-GCN 完整数据流程

### 6.1 推荐目录

CTR-GCN 官方仓库预期的核心目录结构为：

```text
CTR-GCN/
├── data/
│   ├── ntu/
│   ├── ntu120/
│   └── nturgbd_raw/
│       ├── nturgb+d_skeletons/       # S001–S017 压缩包解压内容
│       └── nturgb+d_skeletons120/    # S018–S032 压缩包解压内容
├── config/
├── feeders/
├── graph/
├── model/
└── main.py
```

注意：构建 NTU120 时，`nturgb+d_skeletons120/` 不是完整数据；NTU120 预处理应同时读取 S001–S017 和 S018–S032。

### 6.2 预处理

分别进入 `data/ntu` 和 `data/ntu120` 执行：

```bash
# NTU60
cd data/ntu
python get_raw_skes_data.py
python get_raw_denoised_data.py
python seq_transformation.py

# NTU120
cd ../ntu120
python get_raw_skes_data.py
python get_raw_denoised_data.py
python seq_transformation.py
```

三个阶段通常完成：

1. 读取逐帧 `.skeleton` 文件并提取每个 performer；
2. 清理错误跟踪、异常 body 和官方列出的缺失样本；
3. 将序列中心化并生成模型可读取的 NumPy 数据。

标准输出通常包括：

```text
data/ntu/NTU60_CS.npz
data/ntu/NTU60_CV.npz
data/ntu120/NTU120_CSub.npz
data/ntu120/NTU120_CSet.npz
```

不同 fork 可能只默认生成部分协议，或使用 `XSub/XView/XSet` 等不同大小写命名。应查看当前版本的 `seq_transformation.py` 和 YAML 中的 `data_path`，不要只靠重命名文件来切换协议。

常见 `.npz` 字段为：

```text
x_train, y_train, x_test, y_test
```

其中标签常以 one-hot 形式存储，feeder 再转换为 0-based class index；skeleton 输入通常整理为：

```text
N, C, T, V, M
```

- `N`：样本数
- `C`：坐标通道，通常为 3（x、y、z）
- `T`：时间帧
- `V`：关节数，NTU 为 25
- `M`：最大人数，常设为 2

### 6.3 训练与测试

先选择与数据协议一致的配置，例如：

```bash
# 示例：NTU120 XSub，joint stream
python main.py \
  --config config/nturgbd120-cross-subject/default.yaml \
  --work-dir work_dir/ntu120/xsub/ctrgcn_joint \
  --device 0
```

bone 或 motion stream 可通过 feeder 参数启用：

```bash
# bone stream 示例
python main.py \
  --config config/nturgbd120-cross-subject/default.yaml \
  --train_feeder_args bone=True \
  --test_feeder_args bone=True \
  --work-dir work_dir/ntu120/xsub/ctrgcn_bone \
  --device 0
```

最终测试：

```bash
python main.py \
  --config <work_dir>/config.yaml \
  --work-dir <work_dir> \
  --phase test \
  --save-score True \
  --weights <work_dir>/<checkpoint>.pt \
  --device 0
```

如果训练 joint、bone、joint-motion、bone-motion 四个 stream，可在各 stream 独立完成 validation/checkpoint 选择后再进行 score-level ensemble。ensemble 权重也必须在内部 validation 上确定，不能在 official test 上搜索。

## 7. SkeletonX 完整数据流程

SkeletonX 的代码结构和 NTU 预处理流程主要继承 CTR-GCN 风格，可使用相同的原始目录：

```text
SkeletonX/
├── data/
│   ├── ntu/
│   ├── ntu120/
│   └── nturgbd_raw/
│       ├── nturgb+d_skeletons/
│       └── nturgb+d_skeletons120/
├── config/
├── feeders/
├── model/
├── main_baseline.py
├── main_xmix.py
└── run_one-shot_training.py
```

### 7.1 基础预处理

```bash
cd data/ntu       # 或 data/ntu120
python get_raw_skes_data.py
python get_raw_denoised_data.py
python seq_transformation.py
```

SkeletonX 官方 README 主要列出的标准基础文件是：

```text
data/ntu/NTU60_CS.npz
data/ntu120/NTU120_CSub.npz
```

这反映其公开训练配置主要围绕 cross-subject 数据和 data-efficient 场景。若要在 SkeletonX 中运行 NTU60 XView 或 NTU120 XSet，必须先确认当前仓库中存在对应 config、生成逻辑和 feeder 路径；若复用 CTR-GCN 生成的 `NTU60_CV.npz` 或 `NTU120_CSet.npz`，还应核对字段名、shape、标签编码和预处理版本完全兼容。

### 7.2 One-shot 与 limited-scale 数据

完成基础预处理后，在相应数据目录运行：

```bash
# 生成 one-shot 数据及样本信息
python seq_transformation_1Shot.py

# 生成 limited-scale 数据及样本信息
python seq_transformation_LimBudget.py
```

典型输出包括：

```text
NTU60_1Shot.npz
NTU60_LimBudget_*.npz
NTU120_1Shot.npz
NTU120_LimBudget_*.npz
train_indices_info_*.csv
one-shot_anchor_info.csv
one-shot_aux_info.csv
one-shot_eval_info.csv
```

SkeletonX 的 one-shot / limited-scale 是额外的 data-efficient 实验设定，不等同于 NTU 官方 XSub、XView 或 XSet。报告结果时必须同时注明：

- 数据集：NTU60 或 NTU120；
- 基础官方协议；
- one-shot 或每类样本预算；
- 使用的样本清单/CSV；
- seed 和 checkpoint 选择规则。

官方仓库中的示例入口包括：

```bash
# one-shot
python run_one-shot_training.py --device 0,1 --dataset ntu

# limited-scale baseline 示例
python main_baseline.py \
  --config config/ntu/limited_scale/base_10_LB.yaml \
  --work-dir results/ntu/limited_scale/ctrgcn_baseline \
  --model model.ctrgcn.Model \
  --device 0 1 \
  --eval-interval 5
```

应以当前 checkout 中的配置文件名和参数为准，因为仓库更新或 fork 可能改变路径。

## 8. 推荐的可复现实验顺序

```text
两个原始压缩包
        ↓
解压到各自 raw 目录
        ↓
校验文件名、重复文件和缺失样本列表
        ↓
解析 S / C / P / R / A，保存 sample manifest
        ↓
按目标官方协议生成 official train / official test
        ↓
从 official train 内部生成 train-dev / validation
        ↓
预处理并确认 N,C,T,V,M、标签范围和样本数量
        ↓
训练 joint/bone/motion streams
        ↓
仅用内部 validation 选择超参数、checkpoint 和 ensemble 权重
        ↓
使用完整 official train 重训最终模型（可选但推荐）
        ↓
在 official test 上进行一次最终评估
```

建议为每次实验保存：

- 使用的原始压缩包名称与校验值；
- 缺失/异常样本列表版本；
- 完整 sample manifest；
- official split 和 internal validation 的 ID 清单；
- 预处理脚本的 commit；
- 配置文件、随机种子和环境版本；
- 最终 checkpoint 选择依据；
- Top-1，必要时同时报告 Top-5 和各类别结果。

## 9. 常见错误检查表

- [ ] NTU120 是否同时读取了 S001–S017 和 S018–S032？
- [ ] 文件名中的 `A001` 是否正确转换为类别索引 0？
- [ ] NTU60 XView 是否为 Camera 2、3 训练，Camera 1 测试？
- [ ] NTU120 XSet 是否按 setup 奇偶划分，而不是按 camera 划分？
- [ ] NTU120 XSub 是否使用完整 53-subject 训练列表？
- [ ] 是否把代码中的 official-test `val` 误用于调参或 early stopping？
- [ ] validation 是否只来自 official train？
- [ ] 同一 capture group 的多相机文件是否被拆到 train 和 validation 两侧？
- [ ] 全局归一化统计量是否只由训练子集计算？
- [ ] train/test 是否使用同一关节顺序、最大人数和时间处理规则？
- [ ] 是否记录了缺失样本列表和预处理代码版本？
- [ ] 数据文件、YAML 中的协议、类别数和输出目录名称是否一致？

## 10. 主要参考资料

- [NTU RGB+D 官方论文：NTU RGB+D: A Large Scale Dataset for 3D Human Activity Analysis](https://arxiv.org/pdf/1604.02808)
- [NTU RGB+D 120 官方论文：NTU RGB+D 120: A Large-Scale Benchmark for 3D Human Activity Understanding](https://www.ntu.edu.sg/media/docs/librariesprovider106/publications/video-analytics/ntu-rgb-d-120-a-large-scale-benchmark-for-3d-human-activity-understanding.pdf)
- [CTR-GCN 官方代码仓库](https://github.com/Uason-Chen/CTR-GCN)
- [SkeletonX 官方代码仓库](https://github.com/zzysteve/SkeletonX)

