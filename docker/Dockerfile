# ═══════════════════════════════════════════════════════════════════════
# 提交镜像（方式二：本地开发 → 提交 Docker 镜像）
#
# 官方约定（《赛题详情.md》方式二第 3 条）：
#   提交物 = 基于 sport-base:v1 的镜像
#   COPY participant/ /participant/
#   入口   = /participant/run_all.sh
#   docker save <image> -o <file>.tar  后上传平台
#
# ── 构建（在仓库根目录执行）────────────────────────────────────────────
#   docker build -f docker/Dockerfile -t sport-vision-submit:v1 .
#
# ── 本地全量自测（与评测形态一致）──────────────────────────────────────
#   见 docker/README.md 与 tools/selftest.sh
#
# ── 导出提交包 ────────────────────────────────────────────────────────
#   docker save sport-vision-submit:v1 -o sport-vision-submit.tar
#
# 说明：这里**不做任何 apt / pip 安装**。依赖契约
# （torch 2.1.2+cu118 / numpy 1.26.4 / onnxruntime-gpu 1.18.1 / TensorRT 8.6.x）
# 已固化在基础镜像中，赛道规则明确禁止升级或替换这些基础组件；
# 而且评测环境没有网络安装环节。
# ═══════════════════════════════════════════════════════════════════════
FROM sport-base:v1

# 工程包 → 容器内固定路径 /participant
# （participant/*/run.sh 里写死了 /participant/<task>/... 这个前缀，路径不能改）
COPY participant/ /participant/

# 从 Windows 侧 clone / 拷贝过来的 .sh 往往丢掉可执行位，
# 这里补回来，保证 ENTRYPOINT 能直接 exec。
# 只改权限位、不改内容，不影响 SHA256 完整性校验。
RUN chmod +x /participant/*.sh /participant/*/run.sh

WORKDIR /participant

# 与 run_all.sh 的默认值保持一致；需要覆盖时用 docker run -e 传入
ENV SOLUTION=participant.solution:Solution \
    DECODER=gpu \
    TIMEOUT_SEC=7200

ENTRYPOINT ["/participant/run_all.sh"]
