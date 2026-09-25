#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""按 manifest.json 核对验证集视频是否齐全、文件名是否正确。

为什么需要它：
    组委会工程包的 zip 条目名是「UTF-8 字节但没打 UTF-8 标记位」。用 Windows
    资源管理器 / Expand-Archive / 任何 .NET ZipFile 解压时，含非法字符的条目
    会被**静默丢弃**。实测后果：
      · pingpang/public_data/videos/ 里的 0度 / 45度 / 90度 三个子目录连同
        15 个验证集视频全部消失（目录还在，里面是空的）
      · basketball 的 2 个视频文件在，但文件名变成乱码
        `2025-26NBA_甯歌璧沖榄旀湳vs鍑皵鐗逛汉_...` —— manifest 里找不到它，
        自测会直接报「视频不存在」

    **框架自带的 integrity.py 管不到这里**：它只校验 core/*.py、scripts/*.py、
    run.py / run.sh / validate.py / integrity.py / README.md 的 SHA256，
    public_data/ 属于数据、不在校验范围内。所以这种缺失不会被自动发现，
    必须单独核对（本脚本就是这个作用）。

用法：
    python tools/check_dataset.py participant
    python tools/check_dataset.py D:\\mCloudDownload\\...\\participant\\participant

返回码：0 = 两个任务的视频都齐全且文件名与 manifest 一致；1 = 有问题。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # pragma: no cover
    pass

TASKS = ("pingpang", "basketball")


def check_task(task_root: Path) -> bool:
    public = task_root / "public_data"
    manifest = public / "manifest.json"

    print(f"\n── {task_root.name} ─────────────────────────────")
    if not manifest.is_file():
        print(f"  [FAIL] 找不到 {manifest}")
        return False

    data = json.loads(manifest.read_text(encoding="utf-8"))
    videos = data.get("videos", [])
    print(f"  manifest 声明 {len(videos)} 条视频")

    declared = set()
    missing = []
    for v in videos:
        rel = v["path"].replace("\\", "/")
        declared.add(rel)
        target = public / rel
        if target.is_file():
            size_mb = target.stat().st_size / 1024 / 1024
            print(f"  [ OK ] {size_mb:8.2f} MB  {rel}")
        else:
            missing.append(rel)
            print(f"  [MISS]             {rel}")

    # 反向检查：videos/ 下有没有 manifest 不认识的文件（乱码名会在这里暴露）
    videos_dir = public / "videos"
    actual = set()
    if videos_dir.is_dir():
        for p in sorted(videos_dir.rglob("*")):
            if p.is_file():
                actual.add(p.relative_to(public).as_posix())

    extra = actual - declared
    for rel in sorted(extra):
        print(f"  [NAME] 文件名不在 manifest 里: {rel}")

    ok = not missing and not extra
    if ok:
        print(f"  ✅ {task_root.name} 验证集齐全，文件名与 manifest 一致")
    else:
        if missing:
            print(f"  ❌ 缺 {len(missing)} 条视频")
        if extra:
            print(f"  ❌ {len(extra)} 个文件不在 manifest 中（多半是乱码名）")
    print(f"  manifest 名称: {data.get('name', '(未声明)')}")
    return ok


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__)
        return 2

    root = Path(argv[1]).expanduser().resolve()
    if not root.is_dir():
        print(f"找不到目录: {root}", file=sys.stderr)
        return 1

    # 支持两种传法：工程包根目录，或外层（含 participant/ 的那层）
    if not (root / "pingpang").is_dir() and (root / "participant" / "pingpang").is_dir():
        root = root / "participant"

    print(f"工程包根目录: {root}")
    results = [check_task(root / t) for t in TASKS if (root / t).is_dir()]
    if not results:
        print("没有找到 pingpang / basketball 任务目录", file=sys.stderr)
        return 1

    print()
    if all(results):
        print("全部通过 ✅  —— 若之前用资源管理器解压过，这一份是好的。")
        return 0
    print("有问题 ❌")
    print("修法：用 tools/unpack_participant.py 重新解压原始 participant.zip：")
    print("      python tools/unpack_participant.py <participant.zip> <目标目录>")
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
