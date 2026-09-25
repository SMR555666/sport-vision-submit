# 乒乓球多视角落点检测 · 参赛仓库

咪咕仝学「体育视频理解」赛题参赛工程。**主赛题**：乒乓球多视角落点检测（按 0° / 45° / 90° 三视角评分）；**附加题**：篮球球员跟踪（自愿选做，不影响主赛题成绩）。

本仓库 = 组委会工程包 + 版本管理 + 团队协作 + 提交流水线。

> **仓库位置**：`D:\mCloudDownload\sport-vision-submit`
> 组委会资源位置：`D:\mCloudDownload\乒乓球多视角落点检测\`
> 资源实测清单、工程包缺文件事故的修复记录 → **[`docs/本地资源清单.md`](docs/本地资源清单.md)**
> 赛题原文（评分、提交、限定条件）→ **[`docs/赛题详情.md`](docs/赛题详情.md)**

---

## 目录

1. [三条命令跑起来](#1-三条命令跑起来)
2. [仓库结构与三条路径对齐](#2-仓库结构与三条路径对齐)
3. [红线：动这些直接没成绩](#3-红线动这些直接没成绩)
4. [环境准备](#4-环境准备)
5. [数据准备](#5-数据准备)
6. [三段自测](#6-三段自测)
7. [开发：写你的 Solution](#7-开发写你的-solution)
8. [提交](#8-提交)
9. [上传到 GitHub 与协作](#9-上传到-github-与-协作)
10. [常见坑](#10-常见坑)

---

## 1. 三条命令跑起来

在**有 docker + GPU 的 Linux 机器**上（Windows 本机跑不了，原因见 §4）：

```bash
python tools/check_dataset.py participant   # 验证集齐全吗（integrity.py 查不到这里）
./tools/selftest.sh quick                   # 两任务各跑 1 条视频，最快暴露接入错误
./tools/selftest.sh all                     # 双任务联合全量自测 = 评测形态
```

拿到退出码 `0` 且 `n_errors = 0`，就可以走到 §8 提交了。

---

## 2. 仓库结构与三条路径对齐

```
sport-vision-submit/                    ← git 仓库根
├── participant/                        组委会工程包（原样，未改动）
│   ├── run_all.sh                        联合入口：先完整性校验，再依次跑两任务
│   ├── pingpang/                         乒乓球任务
│   │   ├── core/                           评测框架（禁改）
│   │   ├── run.py  validate.py  integrity.py
│   │   ├── scripts/check_env.py  check_solution.py
│   │   ├── public_data/                    验证集 15 条视频 + manifest + GT
│   │   └── participant/                ← ★ 你的代码区（solution.py / weights/ / configs/）
│   └── basketball/                     篮球任务（结构同上，验证集 2 条视频）
├── docker/
│   ├── Dockerfile                        提交镜像：FROM sport-base:v1 + COPY participant/
│   └── README.md                         ★ 22.7GB 基础镜像（OCI 目录）怎么加载
├── tools/
│   ├── unpack_participant.py             正确解压 participant.zip（修中文名）
│   ├── check_dataset.py                  按 manifest 核对验证集
│   ├── link_data.ps1                     把 D 盘训练集链接进 work/data
│   └── selftest.sh                       宿主机侧自测驱动
├── docs/
│   ├── 赛题详情.md                        赛题原文
│   ├── 本地资源清单.md                    ★ D 盘资源实测 + 缺文件事故修复记录
│   └── 提交记录.md                        ★ 5 次提交机会的留痕表
├── work/                                本地工作区（gitignore；训练集链接 + 自测产物）
├── .github/workflows/framework-guard.yml  CI：两道防线守住框架完整性
├── .gitattributes                        ★ 全局关闭行尾转换（删了会 exit 4）
├── .gitignore  .dockerignore
└── README.md                            本文件
```

### 本地磁盘 → 仓库 → 容器，路径对照

| 资源 | 本地磁盘 | 仓库内 | 容器内 |
| --- | --- | --- | --- |
| 工程包 | `D:\mCloudDownload\乒乓球多视角落点检测\participant\participant\` | `participant/`（已入库） | `/participant` |
| 乒乓球验证集 | 同上 | `participant/pingpang/public_data/` | `/participant/input/pingpang` |
| 篮球验证集 | 同上 | `participant/basketball/public_data/` | `/participant/input/basketball` |
| 乒乓球训练集 | `…\pp_train_data\pp_train_data\`（646 MB，不入库） | `work/data/pp_train_data`（Junction） | 不需要（训练在容器外做） |
| 篮球训练集 | `…\bb_train_data\bb_train_data\`（4.67 GB，不入库） | `work/data/bb_train_data`（Junction） | 同上 |
| 基础镜像 | `…\sport-base_v1\`（22.7 GB，OCI 目录，不入库） | 不纳入 | `sport-base:v1` |
| 输出产物 | — | `work/out/joint/`（gitignore） | `/participant/output` |

---

## 3. 红线：动这些直接没成绩

组委会的 `participant/<task>/integrity.py` 会给**每个任务 14 个文件**记录 SHA256，写在 `participant/<task>/.integrity.json` 里；`run_all.sh` / `run.sh` **启动时最先校验**，任何一处字节不一致就 `exit 4`，这次提交作废：

```
participant/<task>/core/**            8 个 .py
participant/<task>/scripts/**         2 个 .py
participant/<task>/run.py
participant/<task>/run.sh
participant/<task>/validate.py
participant/<task>/integrity.py
participant/<task>/.integrity.json    记录清单本身也纳入仓库 CI 比对
```

另外两处虽然不在 SHA256 清单里（顶层没有 `.integrity.json`，且 `integrity.py` 的 `ROOT` 是任务目录，所以它们校验不到自己那一层），但同样是组委会框架的一部分——本仓库的 CI 会额外盯着：

- `participant/run_all.sh`（联合入口）
- `participant/README.md`（组委会说明文档）

**只能改** `participant/<task>/participant/` 里的东西：

| 可以改 | 说明 |
| --- | --- |
| `solution.py` | 实现 `Solution` 类；官方参考实现可直接整体替换 |
| `weights/` | 模型权重（只带 ONNX，见 §7.3） |
| `configs/` | 配置文件 |
| `base_solution.py` / `ball_detector.py` / `player_detector.py` / `tracker.py` | 参考实现拆出来的模块，也归你 |

三个容易踩的变形：

1. **行尾**。`LF → CRLF` 的自动转换同样算「字节不一致」。本仓库已用 `.gitattributes` 的 `* -text` 全局关掉转换——**不要删这一行**，也不要用会擅自改行尾的编辑器保存这些文件。已实测：用 `core.autocrlf=true` 克隆一份，两个任务的完整性校验照样通过。
2. **顺手刷哈希**。改完 `core/` 再跑一遍 `integrity.py --generate` 把哈希刷成新的，本地能过、评测也能过——但这是「恶意改动」，规则明确取消成绩。CI 的第二道防线专门拦这个：`.integrity.json` 自身也在比对范围内，实测会同时报出 `.integrity.json` 和 `core/types.py` 两处。
3. **`public_data/` 缺文件**。完整性校验**管不到**数据。Windows 下解压组委会 zip 会静默丢掉 15 个乒乓球验证集视频，而校验照样「通过」。所以每次同步后跑一次 `python tools/check_dataset.py participant`。
4. **顺手格式化**。「格式化整个目录」这类操作会把 `core/` 一起改掉；IDE 的 format-on-save 也可能动到。`git status --short` 一眼能看出来——只应出现 `participant/<task>/participant/` 下的改动。

---

## 4. 环境准备

### 4.1 本机（Windows）能做和不能做

| 能做 | 不能做 |
| --- | --- |
| 编辑代码、写 `solution.py`、整理配置 | 跑推理（没有 CUDA / 没有 torch+cu118） |
| `git` 全部操作、推 GitHub | `docker build` / `docker load`（**没装 docker**） |
| 跑纯标准库脚本：`integrity.py`、`check_dataset.py` | 跑 `run.py`（缺 torch / cv2 / av / onnxruntime） |
| 链接训练集、看视频、标数据 | 训练模型（要 2×4090） |

**结论：算法开发与训练放到 Linux 机器或平台开发资源上做，本机只做代码编辑 + 版本管理。**

### 4.2 依赖契约（固化在基础镜像里，禁止动）

| 组件 | 版本 | 备注 |
| --- | --- | --- |
| torch | `2.1.2+cu118` | |
| numpy | `1.26.4` | |
| TensorRT | `8.6.x` | |
| onnxruntime-gpu | `1.18.1` | 必须 `CUDAExecutionProvider` 可用 |
| onnx | `1.16.2` | |
| 容器内 python | `/opt/conda/envs/conda_env/bin/python3` | base 环境没有依赖 |
| `LD_LIBRARY_PATH` | `/opt/conda/envs/conda_env/lib/python3.10/site-packages/torch/lib` | cuDNN8 / cu11 由 torch wheel 自带，喂活 TRT / ORT 的 CUDA EP。`run.sh` 已固化，自己写入口时别漏 |

赛道规则明确：**不得升级或替换 torch / numpy / onnxruntime / TensorRT**，评测环境没有网络安装环节。

### 4.3 基础镜像

`D:\mCloudDownload\乒乓球多视角落点检测\sport-base_v1\` **不是 tar，是 `docker save` 输出被解开后的目录**（62 个文件 / 22.7 GB，`RepoTags: ["sport-base:v1"]`）。`docker load -i <目录>` 无效。

```bash
# 推荐：免落盘（不需要额外 22.7GB）
cd sport-base_v1 && tar -c . | docker load
```

完整说明（含校验、磁盘预估、以及「走平台方式根本不用加载」）→ **[`docker/README.md`](docker/README.md)**

### 4.4 方式一的环境安装（平台开发资源里）

平台选镜像必须是 **`pytorch 2.1.2-ubuntu22.04-p3.10-cuda11.8`**（与评测一致，勿选其他）。然后在平台里：

```bash
apt-get update && apt-get install ffmpeg -y
pip install av numpy==1.26.4 opencv-python-headless scipy \
    onnx==1.16.2 onnxruntime-gpu==1.18.1 \
    tensorrt-libs==8.6.1 tensorrt-bindings==8.6.1 \
    --extra-index-url https://pypi.nvidia.com
pip install tensorrt==8.6.1 --no-build-isolation
```

---

## 5. 数据准备

### 5.1 验证集（已在仓库里，开箱即用）

| 任务 | 视频数 | 分辨率 | 组织 |
| --- | ---: | --- | --- |
| pingpang | 15 | 1920×1080 / 25 fps | `videos/{0度,45度,90度}/`，每机位 5 条，合计 92 个标注落点 |
| basketball | 2 | 1920×1080 / 25 fps | 同场比赛 main + switch，各 750 帧 |

同步或换机器后先核对一遍（**这一步必不可少**）：

```bash
python tools/check_dataset.py participant
```

### 5.2 训练集（5.3 GB，不入库，用链接）

```powershell
# Windows 本机执行一次即可，在 D 盘资源原地建 Junction，不复制
PowerShell -ExecutionPolicy Bypass -File tools\link_data.ps1
```

链接后在 `work/data/` 下得到：

```
work/data/pp_train_data/     ← annotations\00..24\  + rallies_videos\00..24\
work/data/bb_train_data/     ← manifest.json + gt_train.jsonl + videos\（68 条）
work/data/sport-base_v1/     ← 基础镜像目录（可选）
```

> ⚠️ D 盘资源是**双层嵌套**（`pp_train_data\pp_train_data\`），脚本已按实际结构写好。
> ⚠️ 训练集以 **720p** 为主，验证集/评测集全是 **1920×1080** —— 注意模型输入尺度与坐标口径。

---

## 6. 三段自测

三档从快到慢，**别跳级**：80% 的接入错误（`frame_id` 语义、RGB/BGR、x/y 越界、float 序列化）第一档就会暴露。

### 第 1 档：环境契约（8 项）

```bash
./tools/selftest.sh env
# 等价于容器内：
#   /opt/conda/envs/conda_env/bin/python3 /participant/pingpang/scripts/check_env.py
```

检查 torch 2.1.2+cu118 / numpy 1.26.4 / TensorRT 8.6.x / ORT CUDA EP / av+opencv / ffmpeg cuda hwaccel / GPU 卡数与显存 / 输出盘剩余。
**任何一项 FAIL 先修环境，不要靠升级上述组件来「修」。**

### 第 2 档：单条视频端到端（几十秒）

```bash
./tools/selftest.sh quick
# 等价于容器内：
#   cd /participant/pingpang && PYTHONPATH=/participant/pingpang \
#   python3 scripts/check_solution.py --input /participant/pingpang/public_data \
#           --solution participant.solution:Solution --decoder gpu
```

只跑 manifest 里的第一条视频，产物落在 `participant/<task>/scripts/out_check_solution/`（已 gitignore）。
通过标志：`SOLUTION CHECK PASSED ✅`。

### 第 3 档：双任务联合全量（= 评测形态）

```bash
./tools/selftest.sh all
./tools/selftest.sh validate
```

`all` 用的就是组委会 README 给的那条命令：

```bash
docker run --rm --gpus all \
    -v $PWD/participant:/participant:ro \
    -v $PWD/participant/pingpang/public_data:/participant/input/pingpang:ro \
    -v $PWD/participant/basketball/public_data:/participant/input/basketball:ro \
    -v $PWD/out/joint_demo:/participant/output \
    sport-base:v1
```

**退出码**（`run_all.sh` 返回的是第一个非零任务的码，两任务都会跑完）：

| 码 | 含义 | 先看哪 |
| ---: | --- | --- |
| 0 | 成功 | — |
| 1 | 预测结果校验不通过 | `validate.py` 的 errors |
| 2 | 任务运行失败 | `run.log` 的 traceback |
| 3 | 输出超 1 GB | 有没有把 engine / 中间帧写进输出目录 |
| 4 | **完整性校验不通过** | 受保护文件被改了（见 §3） |
| 124 | 外层超时强杀 | 单任务 `TIMEOUT_SEC=7200`，平台外层硬超时要 ≥ 2×7200 |

> `TIMEOUT_SEC` 对两个任务**各自**生效，所以平台外层硬超时必须 ≥ 14400 秒。

---

## 7. 开发：写你的 Solution

### 7.1 生命周期（`core/types.py`）

```python
class Solution(ABC):
    def prepare(self, context: RunContext) -> None: ...            # 一次：加载模型 / TRT 转换 / warmup
    def reset(self, video_meta: VideoMeta) -> None: ...            # 每个视频一次：清状态
    def process_frame(self, frame_rgb, frame_meta) -> list[...]:   # 每帧：返回「本帧已确认」的结果
    def finish_video(self, video_meta) -> list[...]: ...           # 可选：flush 尾部延迟结果
```

- 顺序：`prepare(一次) → [reset → process_frame* → finish_video]*`
- `frame_rgb`：**RGB** uint8 `HxWx3`
- `frame_meta`：含 `video_id` / `frame_id` / `pts` / `width` / `height`
- `RunContext`：`input_dir` / `output_dir` / `decoder` / `info`（回填 `backend` 等，进 `run_status`）/ `extra`
- **允许延迟输出**：`process_frame` 可以攒几帧再确认落点，**但 `frame_id` 必须是落点真正所属的那一帧**，不是当前处理帧。尾部积压的用 `finish_video` flush。
- 继承官方 `BaseSolution` 可以少写三个方法，最薄子类只需实现 `process_frame`。

乒乓球返回 `Landing(frame_id, x, y)`，篮球返回 `Track(frame_id, track_id, bbox)`。
官方参考实现就在代码区里，**直接改写或整体替换**。

### 7.2 两个任务的关键参数（参考实现里可调）

**乒乓球**（`pingpang/participant/`）

| 参数 | 默认 | 作用 |
| --- | ---: | --- |
| `IN_H, IN_W` | 288, 512 | 网络输入尺寸；坐标按 `sx = W/512`、`sy = H/288` 回原分辨率 |
| 滑动栈 | 3 帧 | 拼成 `(1, 9, 288, 512)`；解码取中间帧通道 `ch1`，**固有 1 帧滞后** |
| `SCORE_TH` | 0.7 | 热图阈值，blob 加权质心 |
| `CONF_TH` | 0.75 | 轨迹点置信门槛（抑制弱检测） |
| `MIN_GAP` | 10 | 两次落点最小帧间隔（数据集节奏约 10–12 帧/落点） |
| `FALL_AMP` / `RISE_AMP` | 2.0 / 1.0 | 下落 / 反弹最小幅度门控（px） |

落点判定 = 球心 y 的**局部极大值** + 下落/反弹门控。因为 `ch1` 滞后 1 帧，上报帧号取 `fid - 1`——**改这里要特别小心，这是最容易悄悄掉分的地方**。

**篮球**（`basketball/participant/`）：`PlayerDetector` + `IoUTracker`，`CLASSES=[0]`（COCO person），`layout="e2e"`。

### 7.3 权重契约

**只带 ONNX**（跨机器可移植的唯一交付格式）；TRT engine 现场构建，首跑约 5 分钟，之后从 `<output_dir>/trt_cache` 秒级加载。

| | pingpang | basketball |
| --- | --- | --- |
| 文件名 | `weights/ball.onnx`（5.19 MB） | `weights/player.onnx`（9.91 MB） |
| 输入 | `(1, 9, 288, 512)` float32 | `(1, 3, H, W)` float32，**RGB**，值域 [0,1] |
| 输入尺寸 | 固定 288×512 | 建议 **960×960** 或 1280×1280（640 下远端球员易漏） |
| 输出 | 3 通道热图（sigmoid 已含） | 端到端 `[1, K, 6]`（x1,y1,x2,y2,score,class_id，图内已 NMS） |
| opset | — | 建议 12–17（TRT 8.6 兼容区间） |

篮球权重来源与导出（在容器外的 Ultralytics 环境里做）：

```bash
yolo export model=yolo26n.pt format=onnx imgsz=960 opset=13
```

导出后先自检：

```bash
python3 -c "import onnx; m=onnx.load('player.onnx'); onnx.checker.check_model(m); print(m.graph.input[0])"
```

> TRT 对**静态 shape** 最友好。`player_detector` 会读 ONNX 图里的输入名与 shape，动态维度回落到 letterbox 目标尺寸。

### 7.4 输出格式与校验规则

每个任务的输出目录：

```
predictions.jsonl   预测结果，每行一个 JSON
run_status.json     运行状态 / 逐视频结果 / 耗时统计   ← 看耗时和 backend 就靠它
run.log             运行日志，失败先看 traceback
```

```json
{"video_id":"v000001","frame_id":123,"x":960.0,"y":540.0}
{"video_id":"魔术vs凯尔特人_seg1_main","frame_id":123,"track_id":1,"bbox":[100.0,200.0,180.0,360.0]}
```

规则（**框架不自动修正，不合规直接判非法**）：

- `video_id` 必须在输入 manifest 中
- `frame_id` 为 `[0, n_frames)` 内的整数（0 基，Python `int`，不能是 bool）
- 乒乓球 `x ∈ [0, width)`、`y ∈ [0, height)`，float 有限值 —— **越界直接非法，框架不 clip**
- 同一视频内近邻重复（`|Δframe| ≤ 1` 且距离 ≤ 50 px）只**警告**、不修改（评分时一对一枚举，重复没有额外收益）
- 篮球 `track_id` 为每视频内正整数；`bbox` 满足 `x1 < x2`、`y1 < y2`、不越界；同一 `(video_id, frame_id, track_id)` 至多一行
- 篮球**每帧预测数上限 15**，超出部分在评分时直接计 FP

### 7.5 训练数据怎么用

```bash
python tools/check_dataset.py participant       # 先确认验证集
powershell -File tools\link_data.ps1            # 再链接训练集到 work/data
```

| | 乒乓球 | 篮球 |
| --- | --- | --- |
| 规模 | 154 段回合视频（140 段 720p + 14 段 1080p），逐帧球/球员/球桌 bbox | 68 条视频 / 34 场比赛 / 40.5 万框 / 815 条轨迹 |
| 组织 | `annotations\{00..24}\*.json` + `rallies_videos\{00..24}\*.mp4` | `gt_train.jsonl` + `videos\*.mp4` + `manifest.json` |

训练在**容器外或平台开发资源**里做，产物是 ONNX，最后放回 `participant/<task>/participant/weights/`。训练代码建议放 `work/` 下（已 gitignore）或单独建分支，别把数据集和 checkpoint 提进主分支。

### 7.6 评分口径（决定优化方向）

| | 主赛题 | 附加题 |
| --- | --- | --- |
| 精度分（75） | `F1_0°×25 + F1_45°×25 + F1_90°×25` | `(0.6×IDF1 + 0.4×MOTA)×75` |
| TP 判定 | 帧号 ±1 且位置 ≤ 50 px，一对一匹配 | IoU ≥ 0.5 + 帧内 Hungarian；回放等 GT 无框时段预测计 FP |
| 性能分（25） | 平均推理 FPS 线性：1 fps = 1 分，≥50 fps 封顶 | 同左 |
| 官方基线 | public F1 **0.604**（0° 0.408 / 45° 0.644 / 90° 0.697） | IDF1 ≈ **0.34** / MOTA ≈ **0.53** |

- 三视角**分开算再相加**：0° 只占 1/3 权重，别把全部精力压在单一视角；0° 是最弱的一环（0.408），提升空间最大。
- 精度与速度要一起算账：F1 涨 0.02 约值 1.5 分，若因此把 FPS 从 30 拖到 20 就少约 5 分，净亏。
- 测试集中**二次弹跳、桌边反弹、环境遮挡**等干扰点误检/遗漏不影响评分——不用为它们专门做抑制。

### 7.7 官方参考实现里有、但需要你自己补的

篮球 `weights/README.md` 写明 **`player.onnx` 由赛事方提供、不随代码仓分发**。如果 `weights/` 里没有它，自测会在 `prepare` 阶段报错——按 §7.3 的命令自己导出，或从平台补齐。

另外，组委会 `participant/README.md` 引用了《作品形式&提交流程.md》和《赛题解析.md》，这两份**不在工程包里**，需要从平台另行下载。

---

## 8. 提交

**每队只有 5 次成功提交机会，以最后一次成功提交计分。** 每次提交前后都填 [`docs/提交记录.md`](docs/提交记录.md)。

### 方式一：平台开发 + 提交（推荐先走这条）

1. 平台创建 **2 卡 4090** 资源，镜像选 `pytorch 2.1.2-ubuntu22.04-p3.10-cuda11.8`
2. 上传 `participant.zip`（**用 `tools/unpack_participant.py` 解，或解完跑 `check_dataset.py` 核对**）
3. 按 §4.4 装环境
4. 用软链接把验证集组织成评测形态，不用复制数据：

```bash
cd /participant
mkdir -p input
ln -s ../pingpang/public_data input/pingpang
ln -s ../basketball/public_data input/basketball
./run_all.sh input output          # 双任务联合自测，与评测形态一致
```

5. 按平台要求提交算法模型、推理程序与配置文件

### 方式二：本地开发 + 提交 Docker 镜像

```bash
docker build -f docker/Dockerfile -t sport-vision-submit:v1 .
docker run --rm --gpus all ...                                    # 先按 §6 跑通
docker save sport-vision-submit:v1 -o sport-vision-submit.tar     # 上传这个 tar
```

入口固定为 `/participant/run_all.sh`，`COPY participant/ /participant/`。**镜像里不要塞训练集或日志**（新增空间限 < 50 GB）。

### 提交前逐项过一遍

见 [`docs/提交记录.md`](docs/提交记录.md) 的检查清单。最关键的三条：

- `git diff --stat` 确认只动了 `participant/<task>/participant/`
- 输出目录合计 < 1 GB
- 单任务耗时 < 7200 秒

---

## 9. 上传到 GitHub 与协作

### 9.1 绑远端并首次推送

**第 1 步：把仓库真名抄准。** 打开仓库页面 → 绿色 `Code` → `HTTPS` → 复制那一行，形如 `https://github.com/<用户名>/<仓库名>.git`。这一步不要凭记忆打字。

> 本仓库的实际名字是 **`-sport-vision-submit`**——开头**有一个连字符**。少写这个连字符，推送就会得到 `repository '...' not found`。
> 注意这个报错**不等于没登录成功**：它说明认证已经过了，只是那个路径下没有该账号有权访问的仓库。
> 认证有没有过，看 Windows 凭据管理器里有没有 `GitHub - https://api.github.com/<用户名>` 这一条（`cmdkey /list`）。
> 名字不确定时可以试探——本机授权过账号后，`git ls-remote` 能区分「存在」与「不存在」：
>
> ```bash
> git ls-remote --heads https://github.com/<用户名>/<候选仓库名>.git
> # exit 0  = 仓库存在，且这个账号有权限
> # exit 128 + remote: Repository not found. = 仓库不存在（或该账号无权访问，两种情况报错一字不差，无法区分）
> ```

**第 2 步：绑远端。**

```bash
cd D:\mCloudDownload\sport-vision-submit
git remote add origin https://github.com/<用户名>/<仓库名>.git
```

若报 `error: remote origin already exists`，说明之前已经绑过（`add` 只能新增、不能覆盖同名远端；报错本身没有任何副作用）。改用：

```bash
git remote set-url origin https://github.com/<用户名>/<仓库名>.git
git remote -v      # 必须看到 fetch / push 两行都是真名
```

**第 3 步：推送——分两条，先分支后标签。**

```bash
git push -u origin main            # 231 MB，最慢的一步
git push origin baseline-package   # 对象已在远端，几乎瞬间完成
```

> **为什么不一条 `--tags` 推完**：`baseline-package` 指向最初那个提交，单独推它等于把 231 MB 整个传一遍。实测先推标签会撞 `error: RPC failed; HTTP 504 curl 22`（大包上传的网关超时，重试通常就过）。而 `main` 上去之后，标签指向的提交已是远端已有内容的祖先，补推标签只传一个标签对象。
> 标签**不能漏**：它是 CI 第二道防线 `baseline-diff` 的比对基准，没推上去那一步会打 warning 跳过。
> 超 50 MB 的文件会给 `remote: warning: ... larger than GitHub's recommended maximum file size`——只是提示。本仓库两名大件 88.69 MB / 77.06 MB 均已正常入库（硬上限是 100 MB）。

推送时会弹浏览器让你登录授权（本机 git 已装好 Credential Manager），不用手工造 PAT。

**第 4 步：加协作与护栏。**

1. 仓库 → Settings → Collaborators → 添加队友的 GitHub 账号。
2. 仓库 → Settings → Rules → Rulesets（旧界面在 Branches）→ 给 `main` 加规则：勾 **Require a pull request before merging**，再勾 **Require status checks to pass**，把 `integrity` 与 `baseline-diff` 选进去。这样受保护路径被改动时 CI 会红着、PR 合不进去——把「靠自觉」变成「靠机制」。
3. 仓库 → Settings → General 确认可见性。仓库内含完整验证集与组委会材料，建议保持 **Private**。

### 9.2 日常协作流程

队友第一次拿到仓库：

```bash
git clone https://github.com/<用户名>/-sport-vision-submit.git
cd ./-sport-vision-submit                   # 注意：仓库名以 - 开头，必须加 ./，否则 cd 会把它当选项报错
python tools/check_dataset.py participant   # 期望 15 + 2 个视频齐全
```

> 克隆下来的仓库**不含**训练集与基础镜像（被 `.gitignore` 挡住，靠 `tools/link_data.ps1` 本地 Junction 引用），所以 `check_dataset.py` 校验的是 `participant/` 里的验证集。

之后每人一个分支：

```bash
git switch -c feat/pingpang-trk          # 每人一个分支，命名 area/what
# …改代码…
git add -A && git commit -m "feat(pingpang): 用多头热图替换单热图，45° F1 +0.03"
git push -u origin feat/pingpang-trk
```

然后在网页上开 PR。PR 模板会强制填改动范围与自测证据；`framework-guard` 两个 job 必须绿。

> **拉下来跑过再合**。`selftest.sh quick` 几十秒，比在评测机上浪费一次提交机会便宜太多。

### 9.3 让 CI 真正拦得住

仓库已配 `.github/workflows/framework-guard.yml`，push / PR 时跑两个 job：

| job | 做什么 | 拦什么 |
| --- | --- | --- |
| `integrity` | 逐任务跑 `integrity.py --verify`；再跑 `check_dataset.py` | 框架被改；验证集缺文件（后者 `integrity.py` 查不到） |
| `baseline-diff` | 逐文件比对受保护内容与 `baseline-package` 标签（**32 个文件**） | 「改完 `core/` 顺手刷哈希」这种能骗过第一道防线的操作；新增 `core/xxx.py` 也会被发现 |

这道防线已经在本机用真实提交实测过 7 种情形，全部符合预期：

| 情形 | 预期 | 实际 |
| --- | --- | --- |
| 干净状态 | PASS | PASS（32 个受保护文件） |
| 改 `pingpang/core/types.py` | FAIL | FAIL |
| 改 `basketball/run.sh` | FAIL | FAIL |
| 改顶层 `run_all.sh` | FAIL | FAIL |
| 只改文件权限位、内容不变 | PASS | PASS（不误伤） |
| 新增 `pingpang/core/extra.py` | FAIL | FAIL（文件数变 33） |
| 改 `core/` 后重刷 `.integrity.json` | FAIL | FAIL（同时报出两处） |

> 实现上有个坑值得记一笔：`baseline-diff` 用 `git ls-tree` 取文件清单，路径**必须写字面目录名**。`participant/*/core` 这种 glob 在 git 里是对完整文件路径做 `fnmatch`，匹配不到 `participant/pingpang/core/types.py`，实测只会匹配到 1 个文件——防线静默失效却照样显示 PASS。

想自己验证防线真的有效：往 `participant/pingpang/run.py` 追加一行 → push → 应该看到红色 `integrity`；然后 `git checkout baseline-package -- participant/pingpang/run.py` 还原。

### 9.4 不要提交的东西

`.gitignore` 已挡住训练集、基础镜像、`work/`、TRT 缓存、日志、`*.pt`。检查一次：

```bash
git status --short
du -sh .git                    # 应该只有几百 MB（主要是工程包里的视频和权重）
git ls-files | wc -l           # 期望 83 个跟踪文件
```

如果 .git 涨到 GB 级，说明有东西漏进去了，用 `git rm --cached <路径>` 撤出跟踪再补进 `.gitignore`。

---

## 10. 常见坑

| # | 现象 | 根因 | 处理 |
| ---: | --- | --- | --- |
| 1 | Windows 解压工程包后 `pingpang/public_data/videos/` 是空的，但完整性校验通过 | zip 中文条目名是 UTF-8 字节却无 UTF-8 标记位，Windows 按 GBK 解码后**静默跳过**非法名条目 | 用 `tools/unpack_participant.py` 重新解压；解完跑 `check_dataset.py`。`integrity.py` 管不到 `public_data/` |
| 2 | 本地一切正常，评测 `exit 4` | 行尾被转成 CRLF，或动了受保护文件 | 确认 `.gitattributes` 的 `* -text` 还在；`git diff baseline-package -- participant/*/core` 应为空 |
| 3 | 评价 F1 明显低于自测 | 上报 `frame_id` 差 1 帧（乒乓球的 `ch1` 固有 1 帧滞后） | 参考实现取 `fid - 1`，改解码路径时同步改帧对齐；容错只有 ±1 帧 |
| 4 | `x/y 越界` 报错 | 框架**不自动 clip**，越界即非法 | 坐标回原分辨率后自己 clamp 到 `[0, width)` / `[0, height)` |
| 5 | 成绩比预期低很多，日志看着正常 | 篮球在回放/镜头切换段检测出「人」，全部计 FP | 非比赛画面**正确行为是输出空**；每帧预测上限 15 |
| 6 | 单任务跑不完、`exit 124` | 首跑 TRT engine 现场构建约 5 分钟，全算在 7200 秒里 | engine 缓存放 `<output_dir>/trt_cache`；`prepare` 里做 warmup；确认缓存能被复用 |
| 7 | 平台报「环境不对」/ 依赖 import 失败 | 升级或替换了 torch / numpy / onnxruntime / TensorRT | 一律不升级；TRT 靠 `LD_LIBRARY_PATH` 指针到 torch 自带的 cuDNN8/cu11 |
| 8 | `exit 3`，输出超 1 GB | 把 engine / 中间帧 / 调试图写进了输出目录 | 输出目录只放 `predictions.jsonl` + `run_status.json` + `run.log` + `trt_cache` |
| 9 | `docker load -i sport-base_v1` 报错 | D 盘那份是解开的 OCI 目录，不是 tar | `tar -c . | docker load`，见 `docker/README.md` |
| 10 | Linux 上 `./run_all.sh: Permission denied` | Windows 侧 commit 时丢了可执行位 | `chmod +x participant/*.sh participant/*/run.sh`；`docker/Dockerfile` 里已自动补 |
| 11 | 训练集取到空目录 | D 盘资源是双层嵌套 | 取内层：`pp_train_data\pp_train_data\`、`bb_train_data\bb_train_data\` |

---

## 附：命令速查

```bash
# 验证集核对（每次同步后）
python tools/check_dataset.py participant

# 框架完整性
PYTHONPATH=participant/pingpang   python3 participant/pingpang/integrity.py   --verify
PYTHONPATH=participant/basketball python3 participant/basketball/integrity.py --verify

# 自测（Linux + docker）
./tools/selftest.sh env | quick | all | validate | full

# 容器内单任务手跑
docker run --rm --gpus all -v $PWD/participant:/participant -v $PWD/work/out:/participant/output \
    --entrypoint python3 sport-base:v1 /participant/pingpang/run.py \
    --input /participant/pingpang/public_data --output /participant/output/pingpang_demo \
    --solution participant.solution:Solution --decoder gpu

# 打提交包
docker build -f docker/Dockerfile -t sport-vision-submit:v1 .
docker save sport-vision-submit:v1 -o sport-vision-submit.tar

# 训练集链接（Windows）
powershell -ExecutionPolicy Bypass -File tools\link_data.ps1

# GitHub
git remote -v                                   # 确认 fetch / push 两行都是真名
git status --short && git ls-files | wc -l      # 期望 83 个跟踪文件
git push -u origin main                         # 231 MB，最慢的一步
git push origin baseline-package                # 先分支后标签，这条几乎瞬间完成
```

---

## 相关文档

| 文件 | 内容 |
| --- | --- |
| [`docs/赛题详情.md`](docs/赛题详情.md) | 赛题原文：任务描述、评分规则、提交形式、赛道限定条件 |
| [`docs/本地资源清单.md`](docs/本地资源清单.md) | D 盘资源实测清单、工程包缺文件事故的根因与修复记录 |
| [`docs/提交记录.md`](docs/提交记录.md) | 5 次提交机会的留痕表 + 提交前检查清单 |
| [`docker/README.md`](docker/README.md) | 22.7 GB 基础镜像（OCI 目录）的加载方法 |
