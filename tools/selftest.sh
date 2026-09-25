#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════════
# 宿主机侧自测驱动。
#
# 运行环境要求：有 docker + nvidia-container-toolkit 的 Linux 机器
# （Windows 本机没装 docker，跑不了；见 README「环境准备」）。
#
# 用法（在仓库根目录）：
#   ./tools/selftest.sh env      # 只跑环境契约 check_env.py（8 项）
#   ./tools/selftest.sh quick    # 两任务各跑 1 条视频端到端（check_solution.py）
#   ./tools/selftest.sh all      # 双任务联合全量自测（= 评测形态，最慢）
#   ./tools/selftest.sh validate # 校验 all 产出的 predictions.jsonl
#   ./tools/selftest.sh full     # env → quick → all → validate 全走一遍
#
# 可覆盖的变量：
#   IMG=sport-vision-submit:v1 ./tools/selftest.sh all   # 测自己构建的镜像
# ═══════════════════════════════════════════════════════════════════════
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
IMG="${IMG:-sport-base:v1}"
PY=/opt/conda/envs/conda_env/bin/python3
OUT="$REPO/work/out/joint"

# 容器内环境固化，与 participant/*/run.sh 里的写法一致：
# cuDNN8 / cu11 由 torch wheel 自带，喂活 TRT / ORT 的 CUDA EP
ENVLIB='export LD_LIBRARY_PATH="/opt/conda/envs/conda_env/lib/python3.10/site-packages/torch/lib${LD_LIBRARY_PATH:+:${LD_LIBRARY_PATH}}"'

run_in() {  # $1 = 容器内 bash 命令；其余 = docker run 附加参数
    local cmd="$1"; shift
    docker run --rm --gpus all "$@" --entrypoint /bin/bash "$IMG" -lc "set -e; ${ENVLIB}; ${cmd}"
}

cmd_env() {
    echo "═══ 1/4 环境契约 check_env.py ═══"
    run_in "$PY /participant/pingpang/scripts/check_env.py" -v "$REPO/participant:/participant:ro"
}

cmd_quick() {
    echo "═══ 2/4 单条视频端到端 check_solution.py ═══"
    for t in pingpang basketball; do
        echo "── $t ──"
        # 需要可写：check_solution.py 会把产物写到 <task>/scripts/out_check_solution/
        run_in "cd /participant/$t && export PYTHONPATH=/participant/$t && \
                $PY scripts/check_solution.py \
                    --input /participant/$t/public_data \
                    --solution participant.solution:Solution --decoder gpu" \
               -v "$REPO/participant:/participant"
    done
}

cmd_all() {
    echo "═══ 3/4 双任务联合全量自测（等价评测形态）═══"
    mkdir -p "$OUT"
    # 与组委会 README「本地自测」一节给的命令一致
    docker run --rm --gpus all \
        -v "$REPO/participant":/participant:ro \
        -v "$REPO/participant/pingpang/public_data":/participant/input/pingpang:ro \
        -v "$REPO/participant/basketball/public_data":/participant/input/basketball:ro \
        -v "$OUT":/participant/output \
        "$IMG"
}

cmd_validate() {
    echo "═══ 4/4 校验输出 predictions.jsonl ═══"
    for t in pingpang basketball; do
        f="$OUT/$t/predictions.jsonl"
        if [ ! -f "$f" ]; then
            echo "$t: 还没跑 all（缺 $f），跳过"
            continue
        fi
        echo "── $t ──"
        run_in "cd /participant/$t && $PY validate.py \
                    --predictions /out/$t/predictions.jsonl \
                    --manifest /participant/$t/public_data/manifest.json" \
               -v "$REPO/participant:/participant:ro" -v "$OUT:/out:ro"
    done
    echo
    echo "产物目录: $OUT"
}

case "${1:-full}" in
    env)      cmd_env ;;
    quick)    cmd_quick ;;
    all)      cmd_all ;;
    validate) cmd_validate ;;
    full)     cmd_env; cmd_quick; cmd_all; cmd_validate ;;
    *)        sed -n '2,20p' "${BASH_SOURCE[0]}"; exit 2 ;;
esac
