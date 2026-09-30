#!/usr/bin/env python3
"""创建小说转漫画工程目录骨架。

用法:
    python init_project.py <小说名> [--path 输出根目录]

默认在当前目录创建 `<小说名>-漫画工程/`。
"""
import argparse
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="创建小说转漫画工程目录")
    parser.add_argument("novel", help="小说名（工程目录前缀）")
    parser.add_argument("--path", default=".", help="输出根目录，默认当前目录")
    args = parser.parse_args()

    root = Path(args.path) / f"{args.novel}-漫画工程"
    if root.exists():
        raise SystemExit(f"已存在: {root}")

    dirs = [
        root / "原著",
        root / "01-设定" / "设定图" / "人物",
        root / "01-设定" / "设定图" / "场景",
        root / "02-分镜",
        root / "03-漫画页",
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=False)

    (root / "01-设定" / "设定总表.md").write_text(
        "# 设定总表\n\n"
        "## 画风基准\n\n> 待与创作者确认后填写（大类/线条/上色/色彩/分镜气质/群演描述）\n\n"
        "## 人物\n\n## 场景\n\n## 世界观\n",
        encoding="utf-8",
    )
    (root / "生成日志.md").write_text(
        "# 生成日志\n\n"
        "| 时间 | 阶段 | ID | 提示词摘要 | 参考图 | 状态 | 备注 |\n"
        "|---|---|---|---|---|---|---|\n",
        encoding="utf-8",
    )
    (root / "原著" / "README.txt").write_text(
        "把小说原文放入本目录（如 原文.txt）。本目录只读，分析产物不要写回这里。\n",
        encoding="utf-8",
    )
    print(f"OK: {root}")


if __name__ == "__main__":
    main()
