# 基础镜像 sport-base:v1

两个任务共用同一个纯环境镜像（只有运行环境，不含比赛工程）。平台方式（方式一）的基础环境由平台提供；**只有本地开发提交（方式二）才需要本地加载它**。

---

## 1. D 盘那份是什么

```
D:\mCloudDownload\乒乓球多视角落点检测\sport-base_v1\
```

实测结论：**它不是 `sport-base_v1.tar`，而是 `docker save` 的输出被解开后的目录。**

| 项 | 实测值 |
| --- | --- |
| 形式 | 目录（OCI / docker-save 布局），62 个文件 |
| 体积 | 22,705.6 MB（≈ 22.7 GB / 22.2 GiB），未压缩 |
| 体系 | `linux/amd64` |
| 镜像标签 | `sport-base:v1`（见 `manifest.json` 的 `RepoTags`、`index.json` 的 `org.opencontainers.image.ref.name`） |

目录内容：

```
sport-base_v1\
├── manifest.json      # {"Config":..., "RepoTags":["sport-base:v1"], "Layers":[...]}
├── index.json         # OCI index，platform amd64/linux
├── oci-layout         # {"imageLayoutVersion":"1.0.0"}
├── repositories       # {"sport-base":{"v1":"e8f4395f..."}}
└── blobs\sha256\      # 真正的层数据（最大的几个 blob：7.3GB / 6.5GB / 4.3GB / 1.3GB ...）
```

所以：**`docker load -i 这个目录` 是不行的**，`docker load` 只吃 tar 流。

---

## 2. 加载方法

### 方法 A：免落盘（推荐，Linux / macOS）

不需要额外 22.7 GB 磁盘空间，边打包边喂给 docker：

```bash
cd "sport-base_v1所在目录"
tar -c . | docker load
```

原理：`docker save` 产出的 tar 根目录就是 `manifest.json` + `blobs/`，`tar -c .` 重新构造出的正是这个结构。

### 方法 B：先打成 tar 再加载

需要额外 22.7 GB 空闲空间（tar 本身接近未压缩大小）：

```bash
cd "sport-base_v1所在目录"
tar -cf ../sport-base_v1.tar .
docker load -i ../sport-base_v1.tar
```

### 方法 C：根本不加载

如果你走**方式一（咪咕仝学平台创建 2×4090 开发资源）**，平台已按 `pytorch 2.1.2-ubuntu22.04-p3.10-cuda11.8` 配好环境，**不需要**这个镜像，也不需要本地 docker。

---

## 3. 加载后校验

```bash
docker images sport-base
# 期望看到类似：sport-base   v1   <id>   ...   ~22.7GB

# 环境契约 8 项（torch / numpy / TRT / ORT CUDA EP / av+opencv / ffmpeg cuda / GPU / 磁盘）
docker run --rm --gpus all \
    -v "$PWD/participant":/participant:ro \
    --entrypoint /bin/bash sport-base:v1 \
    -lc 'export LD_LIBRARY_PATH=/opt/conda/envs/conda_env/lib/python3.10/site-packages/torch/lib; \
         /opt/conda/envs/conda_env/bin/python3 /participant/pingpang/scripts/check_env.py'
```

---

## 4. 磁盘与权限注意

- 加载后镜像本身约 22.7 GB。若用方法 B 还要再留 22.7 GB 给 tar。加上训练集 5.3 GB，Linux 机器建议预留 **≥ 60 GB**。
- 本机（Windows）**没有装 docker**，上述命令都要在 Linux 机器 / 平台的开发资源里执行。
- `--gpus all` 需要宿主机装好 NVIDIA 驱动 + `nvidia-container-toolkit`；缺了就只跑得动 `DECODER=cpu`（速度远达不到性能分要求）。
- 基础镜像的 `ENTRYPOINT` 已经是 `/participant/run_all.sh`，这也解释了组委会 README 里那句「本地自测可直接挂载到 /participant」——自测时把仓库的 `participant/` 挂进去，无需先构建自己的镜像。
