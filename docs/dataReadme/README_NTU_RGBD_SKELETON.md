# NTU RGB+D Skeleton 数据说明

本文档说明 NTU RGB+D 数据集中两个 skeleton 压缩包的内容、用途及推荐的目录组织方式，适用于 CTR-GCN、SkeletonX 等基于骨架的动作识别模型。

## 数据包说明

| 压缩包 | 对应内容 | 使用说明 |
| --- | --- | --- |
| `nturgbd_skeletons_s001_to_s017.zip` | NTU RGB+D 60（NTU60）的完整 skeleton 数据，采集设置编号为 S001–S017 | 训练或评估 NTU60 时只需使用此包 |
| `nturgbd_skeletons_s018_to_s032.zip` | NTU RGB+D 120（NTU120）相较于 NTU60 新增的 skeleton 部分，采集设置编号为 S018–S032 | 此包不能单独构成完整的 NTU120；训练或评估 NTU120 时必须与 S001–S017 包一起使用 |

简而言之：

- **NTU60**：使用 `S001–S017`。
- **完整 NTU120**：同时使用 `S001–S017` 和 `S018–S032`。

## Skeleton 数据内容

每个 `.skeleton` 文件对应一个动作样本，记录该样本视频中逐帧检测到的人体骨架信息，主要包括：

- 每个骨架包含 **25 个关节（25 joints）**；
- 按时间顺序保存每一帧的 skeleton 数据；
- 提供关节的 **3D 坐标**，通常表示为相机坐标系中的 `(x, y, z)`；
- 同一帧可包含一个或多个人体，支持双人交互等多人动作样本；
- 文件中还可能包含人体跟踪标识、关节跟踪状态、骨架方向及映射到 RGB/Depth 图像平面的坐标等元数据；
- 样本文件名编码了采集设置、相机、被试者、重复次数和动作类别等信息。

该数据不包含 RGB 视频本身。对于仅使用骨架序列进行训练的模型，一般不需要额外下载 RGB、Depth 或 IR 数据。

## 适用训练任务

这两个压缩包适合用于 skeleton-based action recognition，例如：

- CTR-GCN；
- SkeletonX；
- ST-GCN 及其他基于图卷积或时空建模的骨架动作识别模型。

通常需要先运行目标项目提供的数据预处理脚本，将原始 `.skeleton` 文件转换为模型需要的张量、标签和数据划分格式，再开始训练。

常用评估协议包括：

- NTU60：Cross-Subject（XSub）和 Cross-View（XView）；
- NTU120：Cross-Subject（XSub）和 Cross-Setup（XSet）。

具体协议名称、预处理命令及输出格式应以所使用代码仓库的说明为准。

## 推荐目录结构

建议保留原始压缩包，并将解压后的 `.skeleton` 文件统一放入原始数据目录：

```text
data/
└── ntu_rgbd/
    ├── archives/
    │   ├── nturgbd_skeletons_s001_to_s017.zip
    │   └── nturgbd_skeletons_s018_to_s032.zip
    ├── raw/
    │   └── nturgbd_raw/
    │       ├── S001C...A001.skeleton
    │       ├── S001C...A002.skeleton
    │       └── ...
    └── processed/
        ├── ntu60/
        └── ntu120/
```

如果项目文档明确要求类似 `./data/nturgbd_raw` 的路径，应优先遵循项目要求。例如：

```text
project_root/
└── data/
    └── nturgbd_raw/
        ├── S001C...skeleton
        ├── S018C...skeleton
        └── ...
```

NTU60 目录中只需要 S001–S017 的样本；构建 NTU120 时，应确保预处理程序能够同时读取 S001–S017 和 S018–S032 的全部样本。

## 注意事项

1. `nturgbd_skeletons_s018_to_s032.zip` 是扩展部分，不是可独立使用的完整 NTU120 skeleton 数据集。
2. 解压后注意避免出现重复嵌套目录，例如 `nturgbd_raw/nturgbd_raw/*.skeleton`，否则预处理脚本可能找不到文件。
3. 不要混用 NTU60 与 NTU120 的类别数、标签映射和评估协议。
4. 原始数据可能包含缺失骨架、跟踪不稳定或需要排除的样本；应使用目标代码仓库提供的缺失样本列表和预处理规则。
5. 多人样本通常需要统一最大人数、帧数和关节顺序。不要在不了解模型输入约定的情况下自行删除第二个人体。
6. 建议保留原始压缩包和原始 `.skeleton` 文件，只将生成的中间数据写入 `processed/`，以便重新预处理和复现实验。
7. 数据集的使用与分发应遵守 NTU RGB+D 官方许可及申请要求。

