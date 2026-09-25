#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""正确解压组委会的 participant.zip。

为什么需要这个脚本：
    participant.zip 里的中文条目名是 **UTF-8 字节，但没有设置 ZIP 的
    UTF-8 语言编码标记位（flag 0x800）**。Windows 资源管理器 / PowerShell
    Expand-Archive / .NET ZipFile 在这种情况下会回退到系统 ANSI（简体中文为
    GBK/CP936）解码，得到形如 "0搴?" 的乱码名；其中含非法字符（'?'）的条目
    会被直接跳过——表现就是 `pingpang/public_data/videos/` 解压后是空的
    （15 个验证集视频全部丢失），而 basketball 的 2 个视频也带乱码名。

本脚本按条目自身的 flag 位判断编码，必要时用 cp437 -> utf-8 还原原始名字，
可得到与 Linux 下 unzip 一致的正确中文路径。

用法：
    python tools/unpack_participant.py <participant.zip> [目标目录]
    目标目录缺省为当前目录，解压后得到 <目标目录>/participant/...

解压后务必跑一次核对：
    python tools/check_dataset.py <目标目录>/participant
"""

from __future__ import annotations

import shutil
import sys
import zipfile
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # pragma: no cover - 极老版本 Python 无该属性
    pass


def decode_entry_name(info: zipfile.ZipInfo) -> str:
    """按 ZIP 条目自带信息还原文件名，避免中文乱码。"""
    name = info.filename
    if info.flag_bits & 0x800:      # 已声明 UTF-8，直接用
        return name
    # zipfile 在未声明 UTF-8 时按 cp437 解码，因此这里逆向还原原始字节，
    # 再按 UTF-8 解码（组委会包实际就是 UTF-8 名字）。
    try:
        return name.encode("cp437").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return name


def safe_target(root: Path, name: str) -> Path:
    """拼出目标路径，并阻止 ../ 逃逸到 root 之外。"""
    parts = [p for p in name.replace("\\", "/").split("/") if p not in ("", ".", "..")]
    target = root.joinpath(*parts)
    if root.resolve() not in list(target.resolve().parents) + [target.resolve()]:
        raise ValueError(f"条目路径越界: {name}")
    return target


def unpack(zip_path: Path, dest: Path) -> int:
    dest.mkdir(parents=True, exist_ok=True)
    n_file = n_dir = n_fixed = 0

    with zipfile.ZipFile(zip_path) as z:
        for info in z.infolist():
            name = decode_entry_name(info)
            if name != info.filename:
                n_fixed += 1
            target = safe_target(dest, name)

            if info.is_dir():
                target.mkdir(parents=True, exist_ok=True)
                n_dir += 1
                continue

            target.parent.mkdir(parents=True, exist_ok=True)
            with z.open(info) as src, open(target, "wb") as dst:
                shutil.copyfileobj(src, dst)
            n_file += 1

    print(f"解压完成：{n_file} 个文件 / {n_dir} 个目录")
    print(f"其中修正了 {n_fixed} 个中文条目名（原为 GBK 误读的乱码）")
    return n_file


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__)
        return 2

    zip_path = Path(argv[1]).expanduser()
    dest = Path(argv[2]).expanduser() if len(argv) > 2 else Path.cwd()

    if not zip_path.is_file():
        print(f"找不到压缩包: {zip_path}", file=sys.stderr)
        return 1

    print(f"源  : {zip_path}")
    print(f"目标: {dest}")
    unpack(zip_path, dest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
