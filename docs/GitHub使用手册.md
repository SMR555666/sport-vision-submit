# GitHub 项目使用手册

> 仓库：`https://github.com/SMR555666/sport-vision-submit`
> 配套文档：根 [`README.md`](../README.md)（赛题全流程 · 主指南）· [`docs/提交记录.md`](提交记录.md)（5 次提交机会留痕）· [`docs/本地资源清单.md`](本地资源清单.md)（D 盘资源与缺文件事故）
>
> 本手册只讲 **GitHub 这一侧怎么用**：网页上能做什么、Actions 在跑什么、怎么和队友协作、哪些事 GitHub 天生帮不了你。赛题本身的开发流程看 README。

---

## 目录

- [0. 先分清四件"运行"](#0-先分清四件运行)
- [1. 在 GitHub 上运行：Actions 完全指南](#1-在-github-上运行actions-完全指南)
- [2. 为什么这里跑不了赛题代码](#2-为什么这里跑不了赛题代码)
- [3. 队友上手五步](#3-队友上手五步)
- [4. 日常协作流程](#4-日常协作流程)
- [5. 网页上能做哪些日常操作](#5-网页上能做哪些日常操作)
- [6. 权限与安全设置清单](#6-权限与安全设置清单)
- [7. 出错对照表](#7-出错对照表)
- [8. GitHub 帮不了你的事](#8-github-帮不了你的事)

---

## 0. 先分清四件"运行"

"在 GitHub 上跑代码"这句话有歧义。这个项目里，"运行"分成四件完全不同的事，运行环境和能做的事都不同：

| # | 在哪运行 | 能跑什么 | 跑不了什么 |
| --- | --- | --- | --- |
| ① | **GitHub Actions**（网页上） | 两道框架守卫：逐文件 SHA256 校验 + 与基线标签比对 | 任何推理、训练、Docker 构建 |
| ② | **本机 Windows** | 纯标准库工具（完整性校验、验证集核对）、git 操作、编辑代码 | `run.py`（缺 torch/cv2/av）、`selftest.sh`（缺 docker） |
| ③ | **Linux + docker + NVIDIA 容器运行时** | `selftest.sh` 全档自测、`docker build` 打提交包 | 官方计时评测 |
| ④ | **平台 2×4090 开发资源** | 与评测同形态的完整跑通、正式提交 | — |

> **只有 ① 是你"在 GitHub 上"能运行的**，而它跑的是仓库守卫，不是赛题。②③④ 都在 GitHub 之外，但都通过 git 与这个仓库同步。

---

## 1. 在 GitHub 上运行：Actions 完全指南

### 1.1 它在跑什么

仓库里有一个 workflow：`.github/workflows/framework-guard.yml`，由一个叫 `framework-guard` 的工作流承载，含两个 job。它们防的是**同一件事**：把组委会的评测框架改坏了却没人发现——后果不是"测试失败"，而是评测时 `exit 4`，一次提交机会直接作废。

| job | 做什么 | 具体拦什么 |
| --- | --- | --- |
| `integrity` | 逐任务跑 `integrity.py --verify`（逐文件 SHA256）；再跑 `tools/check_dataset.py` 核对验证集 | ① 框架受保护文件被改；② 验证集缺文件 |
| `baseline-diff` | 逐文件比 **blob 内容哈希**（不是 `git diff`），与 `baseline-package` 标签比对，覆盖 **32 个受保护文件** | ③「改了 `core/` 之后顺手重跑 `--generate` 刷哈希」这条能骗过第一道防线的路；④ 新增 `participant/*/core/xxx.py` |

两个 job 都跑在 `runs-on: ubuntu-latest` 上，用的是仓库自带的 `ubuntu-latest` 环境里预置的 `python3`，**不装任何依赖**——因为这两个脚本都只用 Python 标准库。

> 第 ④ 条容易漏：`baseline-diff` 会把基线和当前两侧的文件清单都取出来求并集，所以"新增一个文件"也会被发现。它比对的是内容哈希而非文件差异，所以**只改权限位、内容没变不会被误判**。

### 1.2 怎么看结果

网页路径：

```
仓库首页 → 顶部 Actions → 左侧选中 framework-guard → 点某一次 run → 点 job 名 → 展开 step
```

判读方式：

| 你看到的 | 含义 | 要做什么 |
| --- | --- | --- |
| 两个 job 都是绿勾 | 仓库健康，框架与验证集都没问题 | 无事 |
| `integrity` 红，报 `::error title=xxx 完整性校验失败` | 该任务的受保护文件与 `.integrity.json` 不一致 | 按下面的还原法处理 |
| `baseline-diff` 红，报 `受保护文件被改动` + 列出文件名 | 有文件相对基线变了 | 见 1.4 |
| `baseline-diff` 出现**黄色警告** `缺少基线标签` | 远端没有 `baseline-package` 标签，比对被跳过 | `git push origin baseline-package` |
| 整个 run 没跑起来 | 看 run 页面顶部的提示（权限、workflow 语法） | 见第 7 节 |

### 1.3 手动触发（不用改代码也能跑一次）

workflow 已配置 `workflow_dispatch`，所以网页上可以直接手动跑一遍：

```
Actions → 左侧 framework-guard → 右上角 "Run workflow" → 选分支 main → Run workflow
```

**什么时候用**：改了本地环境、拉了别人的分支、或者只是想确认"仓库现在还是健康的"，但又不想造一个空提交。

> `workflow_dispatch` 只是多了一个触发入口，它不会改变两个 job 的判定逻辑，也不会放宽任何一道防线。

### 1.4 被拦住了怎么还原

CI 报错信息里会直接给出还原命令，照抄即可：

```bash
# 把单个文件还原到基线版本
git checkout baseline-package -- participant/pingpang/core/types.py

# 如果一次改了好几个，先把受保护文件整体还原
git checkout baseline-package -- participant/pingpang/core participant/pingpang/scripts \
    participant/pingpang/run.py participant/pingpang/run.sh participant/pingpang/validate.py \
    participant/pingpang/integrity.py participant/pingpang/.integrity.json \
    participant/basketball/core participant/basketball/scripts \
    participant/basketball/run.py participant/basketball/run.sh participant/basketball/validate.py \
    participant/basketball/integrity.py participant/basketball/.integrity.json \
    participant/run_all.sh participant/README.md
```

> `integrity` 与 `baseline-diff` 要是**同时**红了，说明是"改了 `core/` 又重刷了哈希"这一类操作——两种手段一起上才拦得住，还原时把 `.integrity.json` 也一起还原。

### 1.5 受保护范围到底有哪 32 个（背诵版）

每个任务 15 个：

| 类别 | 文件 |
| --- | --- |
| `core/**` | 8 个 `.py` |
| `scripts/**` | 2 个 `.py` |
| 任务级入口 | `run.py`、`run.sh`、`validate.py`、`integrity.py` |
| 哈希清单 | `.integrity.json` |

全局 2 个：`participant/run_all.sh`、`participant/README.md`。

合计 `15 × 2 + 2 = 32`。

**你能改的只有**：`participant/<task>/participant/` 下面的东西（`solution.py`、`weights/`、`configs/`、`base_solution.py`、`ball_detector.py`、`player_detector.py`、`tracker.py`）。

---

## 2. 为什么这里跑不了赛题代码

这不是配置问题，是三条硬原因叠加，改配置也解决不了：

1. **GitHub 托管的 runner 没有 GPU。** `runs-on: ubuntu-latest` 是一台托管的纯 CPU 虚拟机。赛题硬约束是 Intel CPU + 2×4090、单卡显存 < 24 GB，官方基线本身就依赖 GPU 解码（`DECODER=gpu`）。
2. **那 22.7 GB 的基础镜像不在任何镜像仓库里。** `sport-base:v1` 是平台下发的**本地 OCI 布局目录**（`D:\mCloudDownload\乒乓球多视角落点检测\sport-base_v1\`），runner 没有渠道拿到它；把它推上容器仓库也不现实。
3. **形态不同。** 赛题是"评测机 + 单任务 7200 秒全程计时 + 每队 5 次机会"的形态，CI 是"每次 push 几十秒做完静态检查"的形态。把评测塞进 CI 既跑不动，也跑不出有意义的数字。

所以正确的分工是：

```
GitHub（这个仓库）          负责「不许改坏」——版本管理、协作、框架守卫
Linux + GPU 机器            负责「跑得起来」——selftest.sh 三档自测
平台 2×4090                 负责「跑得好不好」——正式评测
```

> **进阶（通常不适用）**：GitHub 支持"自托管 runner"，理论上可以让平台那台 2×4090 机器注册成 runner，从而在 Actions 里调度 GPU 任务。但平台开发环境一般不允许对外注册、也不保证网络与持久化，**不建议**在这上面花时间。真要在 GPU 上验证，直接 SSH 上去跑 `tools/selftest.sh` 更直接。

---

## 3. 队友上手五步

### 第 1 步：克隆

```bash
git clone https://github.com/SMR555666/sport-vision-submit.git
cd sport-vision-submit
```

> 仓库地址请从仓库页绿色 **Code** 按钮 → **HTTPS** 复制，不要凭记忆打字。历史上踩过一次仓库名少一个连字符导致 `repository '...' not found` 的坑。
>
> 仓库约 **234.7 MB**（含组委会工程包里的验证集视频与权重），首克隆需要点时间。

### 第 2 步：立刻证明"我这份是好的"

克隆完第一件事就跑这两个校验——它们**只用 Python 标准库**，不需要 torch、不需要 GPU，Windows 上也能跑：

```bash
# 验证集是否齐全（15 + 2 个视频）
python tools/check_dataset.py participant

# 两个任务的框架完整性（逐文件 SHA256）
PYTHONPATH=participant/pingpang    python participant/pingpang/integrity.py    --verify
PYTHONPATH=participant/basketball  python participant/basketball/integrity.py  --verify
```

Windows PowerShell 写法：

```powershell
python tools\check_dataset.py participant

$env:PYTHONPATH="$PWD\participant\pingpang"
python participant\pingpang\integrity.py --verify
$env:PYTHONPATH="$PWD\participant\basketball"
python participant\basketball\integrity.py --verify
```

期望结果：`check_dataset.py` 返回 0 并报"全部通过"；两个 `integrity.py` 都报"完整性校验通过"。

> **为什么必须做这一步**：这份仓库的完整性强依赖逐字节一致。虽然 `.gitattributes` 里的 `* -text` 已经全局关闭了行尾转换（它会覆盖 `core.autocrlf`），但"我这份克隆是好的"应该是**验证过的事实**，而不是假设。跑一次几十秒，比在平台上浪费一次提交机会便宜太多。
>
> 万一这一步失败：先看第 7 节对应项，别急着改文件——很可能只是本地 git 配置在克隆前就设错了。

### 第 3 步：准备运行环境

- **只在 Windows 上改代码**：Python 3 足够（第 2 步那些工具都是纯标准库）。跑不了 `run.py`。
- **要真正跑推理**：需要 Linux + docker + NVIDIA 容器运行时。按根 `README.md` 第 4 节操作，基础镜像加载看 [`docker/README.md`](../docker/README.md)。
- **平台开发资源**：按平台指引挂载，直接在 2×4090 上跑。

### 第 4 步：训练数据与基础镜像

这两样**不在仓库里**（`.gitignore` 挡住了，合计 28 GB 上下），需要用本地链接：

```powershell
# Windows：在 D 盘资源原地建 Junction，不复制、不占额外空间
powershell -ExecutionPolicy Bypass -File tools\link_data.ps1
```

Linux 上直接把数据目录挂进容器即可，命令见根 README 第 5、6 节。

### 第 5 步：开自己的分支

```bash
git switch -c feat/pingpang-track
```

命名建议 `area/what`，`area` 取 `pingpang` / `basketball` / `ci` / `docs`。

---

## 4. 日常协作流程

### 4.1 一个完整循环

```bash
git switch main && git pull                      # 先同步
git switch -c feat/pingpang-track                # 开分支
# …改代码…
git add -A
git commit -m "feat(pingpang): 多头热图替换单热图，45° F1 +0.03"
git push -u origin feat/pingpang-track           # 推到远端
```

然后在网页上开 PR：`Compare & pull request` → 按 PR 模板填 → 等 CI → 请人 review → 合并。

### 4.2 PR 模板会强制你填三件事

仓库里配了 `.github/pull_request_template.md`，开 PR 时自动带出来：

1. **改动范围**（含"我没有改受保护文件"的确认项）
2. **自测证据**（跑了哪一档、结果如何）
3. **性能影响**（对 FPS 与分数的影响）

这三项不是形式主义：赛题只有 5 次成功提交机会、以最后一次计分，任何一次盲目提交都可能把成绩覆盖掉。

### 4.3 上线前必须通过的门禁

合并到 `main` 之前，`framework-guard` 的两个 job 都必须是绿的。建议把它设成**硬门禁**（见第 6 节），这样受保护路径被改动时 PR 根本合不进去——把"靠自觉"变成"靠机制"。

### 4.4 谁能改什么

| 范围 | 规则 |
| --- | --- |
| `participant/<task>/participant/**` | 随便改，这是你的战场 |
| `participant/run_all.sh`、`participant/README.md` | 禁止改，CI 会拦 |
| `participant/<task>/core/**`、`scripts/**`、`run.py`、`run.sh`、`validate.py`、`integrity.py`、`.integrity.json` | 禁止改，CI 会拦 |
| `.github/**`、`tools/**`、`docs/**`、根 `README.md` | 可以改（不受守卫保护），但要过 review |

> **想改框架怎么办**：不要在本仓库改。要么在 PR 里说明为什么非改不可并请全队确认，要么把改动放到 `participant/<task>/participant/` 里用继承/组合的方式绕开——后者才是赛题允许的路径。

---

## 5. 网页上能做哪些日常操作

不用克隆也能干不少事。常用路径（`<owner>` = `SMR555666`，`<repo>` = `sport-vision-submit`）：

| 想做的事 | 网页路径 |
| --- | --- |
| 看某个文件的历史与逐行改动 | 文件页 → 右上 `History`，或某行左侧的 blame |
| 比两条分支的差异 | `github.com/<owner>/<repo>/compare/main...feat/xxx` |
| 比任意两个提交 | `github.com/<owner>/<repo>/compare/<sha1>..<sha2>` |
| 看某个文件在基线版本长什么样 | 切到标签：`github.com/<owner>/<repo>/tree/baseline-package/participant/...` |
| 看所有标签 | `github.com/<owner>/<repo>/tags` |
| 下载单个文件 | 文件页 → 右上 `Raw`（右键另存为） |
| 看 CI 历史与日志 | 顶部 `Actions` |
| 手动跑一次 CI | `Actions` → `framework-guard` → `Run workflow` |
| 提任务 / 记 bug | 顶部 `Issues` |
| 看谁在改什么 | 顶部 `Insights` → `Contributors` / `Network` |
| 改仓库名、可见性、协作者 | `Settings` |

> **`Code → Download ZIP` 不要用来替代 clone**：ZIP 里不含 `.git` 目录，拿到的是一堆文件而不是一个仓库——没法 commit、没法 push、也没法比对基线。只在"临时看几眼代码"时用它。

### 5.1 三个容易被忽略但很有用的功能

- **Issues 当任务板**：把"补 pingpang 的 tracker"、"调 basketball 的每帧上限"这类活拆成 issue，指派人，进度就自动可见了。
- **PR 里逐行评论**：review 时在具体某一行留言，比在群里说"那段有问题"精确得多。
- **`Insights → Network / Commits`**：能看到哪些提交还没并进 `main`，避免以为推上去了就是合进去了。

---

## 6. 权限与安全设置清单

跑一次这个清单，后面省很多事：

| 项 | 建议值 | 为什么 |
| --- | --- | --- |
| 可见性（`Settings → General`） | **Private** | 仓库里有完整验证集与组委会材料，不适合公开 |
| 协作者（`Settings → Collaborators`） | 只加队员，角色给 **Write**，不要给 Admin | 给 Admin 意味着对方能改可见性、删仓库 |
| `main` 保护（`Settings → Rules → Rulesets`） | 勾 **Require a pull request before merging**；勾 **Require status checks to pass**，选 `integrity` 与 `baseline-diff` | 受保护路径被改时 PR 合不进去 |
| 允许强推（force push） | **禁止** 对 `main` | 强推会重写历史，而 `baseline-package` 是契约基准，不能被抹掉 |
| Secrets（`Settings → Secrets and variables`） | **不要放任何东西** | 本项目不需要密钥；放进来的任何 token 都会对所有协作者可见 |

> **不要往仓库里放的东西**（`.gitignore` 已挡住大部分）：训练集（5.3 GB）、基础镜像（22.7 GB）、`work/`、TRT 缓存、日志、`*.pt/.pth/.ckpt`、任何压缩包。检查方式见根 README 第 9.4 节。

---

## 7. 出错对照表

以下都是本项目**实际踩过的**，不是设想：

| 症状 | 真正原因 | 修法 |
| --- | --- | --- |
| `repository '...' not found`（你确信自己已登录） | URL 里的用户名或仓库名不对。**这个报错说明认证已经过了**，只是那个路径下没有你有权访问的仓库 | 从仓库页 `Code` 按钮复制地址；名字不确定时用 `git ls-remote --heads <URL>` 试探，`exit 0` 才是"存在且有权限" |
| `error: remote origin already exists` | `origin` 已存在。`git remote add` 只能新增，不能覆盖同名远端 | `git remote set-url origin <URL>`（报错本身没有任何副作用） |
| `error: RPC failed; HTTP 504` | 大包上传的网关超时（本仓库一次要传 231 MB） | 分两步：先 `git push -u origin main`，再 `git push origin baseline-package`；直接重试通常也会过 |
| `remote: warning: File ... larger than GitHub's recommended maximum file size of 50.00 MB` | 只是**提示**，不是失败 | 忽略。硬上限是 100 MB，本仓库最大两个文件 88.69 MB / 77.06 MB 均可正常入库 |
| CI 红：`受保护文件被改动` | 改了 `core/` 等受保护内容 | `git checkout baseline-package -- <按报错里列出的文件>` |
| CI 黄：`缺少基线标签` | 远端没有 `baseline-package` 标签，`baseline-diff` 被跳过 | `git push origin baseline-package`。**别忽略这条**——防线会从两道变一道 |
| 队友克隆后 `integrity.py --verify` 失败 | 本地 git 在克隆前就设了行尾转换，文件被改过 | 确认 `.gitattributes` 在位；`git config --global core.autocrlf false` 后**重新克隆**（`.gitattributes` 的 `* -text` 会覆盖 `autocrlf`，但已被污染的工作区不会自动修复） |
| PowerShell 里命令报 `<` 相关错误 | 把 `<用户名>` 这类占位符原样粘进去了，`<` 被当成重定向 | 占位符要替换成真值 |
| `fatal: not a git repository` | 当前目录不是仓库根 | `cd` 到仓库根；本仓库根是 `D:\mCloudDownload\sport-vision-submit` |
| 追踪文件数不是 83 | 有东西漏进去或漏出来 | `git ls-files \| wc -l` 应为 83（Windows：`(git ls-files).Count`） |

---

## 8. GitHub 帮不了你的事

写清楚边界，避免把时间花错地方：

| 做不到 | 替代路径 |
| --- | --- |
| 跑推理 / 训练 | Linux + GPU 机器，或平台 2×4090 |
| 跑 `tools/selftest.sh` | 需要 docker + nvidia-container-toolkit，只能在 Linux 上 |
| 构建提交用 Docker 镜像 | 同上；`docker build` 依赖 22.7 GB 的本地基础镜像 |
| 保管训练集（5.3 GB）与基础镜像（22.7 GB） | 不入库，用 `tools/link_data.ps1` 或直接挂载 |
| 替你完成官方评测 | 评测在平台上，每队 5 次成功提交机会、以最后一次计分 |
| 替你判断"代码写对了吗" | `baseline-diff` 只能证明**框架没被改坏**，证明不了你的 `Solution` 正确。端到端正确性要靠 `selftest.sh` 那三档 |

---

## 附：与根 README 的分工

| 想知道 | 看哪里 |
| --- | --- |
| 赛题怎么解、`Solution` 怎么写、评分口径 | 根 `README.md` |
| 三条命令跑起来、环境准备、数据准备、三段自测 | 根 `README.md` |
| 提交作品、Docker 打包、5 次机会怎么用 | 根 `README.md` 第 8 节 + `docs/提交记录.md` |
| **GitHub 网页怎么用、CI 在跑什么、怎么协作、出错怎么修** | **本手册** |
| D 盘资源清单、工程包缺文件事故的根因 | `docs/本地资源清单.md` |
| 基础镜像（22.7 GB OCI 目录）怎么加载 | `docker/README.md` |
