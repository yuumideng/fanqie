#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""定点读取 Markdown、TXT 和 CSV，避免为查一条资料加载整份大文件。"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path


QUICK_HEADINGS = re.compile(r"人物.*状态|人物.*境界|当前状态|核心主线|近章摘要|最近.*章|待确认|存疑")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="按关键词、标题或 CSV 字段定点查询资料")
    parser.add_argument("file", type=Path)
    parser.add_argument("--pattern", help="文本正则；Markdown/TXT 查行，CSV 查整行")
    parser.add_argument("--section", help="Markdown 标题正则，读取该标题下的一个段落")
    parser.add_argument("--quick", action="store_true", help="提取 state 的快速视图")
    parser.add_argument("--head", type=int, help="无查询条件时读取前 N 行")
    parser.add_argument("--tail", type=int, help="无查询条件时读取后 N 行")
    parser.add_argument("--before", type=int, default=0, help="关键词命中前的行数")
    parser.add_argument("--after", type=int, default=0, help="关键词命中后的行数")
    parser.add_argument("--max-matches", type=int, default=20, help="最多输出多少个命中")
    parser.add_argument("--book")
    parser.add_argument("--unit")
    parser.add_argument("--chapter")
    parser.add_argument("--chapter-column", default="global_chapter")
    return parser.parse_args()


def heading_level(line: str) -> int | None:
    match = re.match(r"^(#+)\s+", line)
    return len(match.group(1)) if match else None


def markdown_section(lines: list[str], expression: str) -> list[str]:
    matcher = re.compile(expression)
    start = None
    level = None
    for index, line in enumerate(lines):
        current_level = heading_level(line)
        if current_level and matcher.search(line):
            start = index
            level = current_level
            break
    if start is None:
        return []
    end = len(lines)
    for index in range(start + 1, len(lines)):
        current_level = heading_level(lines[index])
        if current_level is not None and current_level <= level:
            end = index
            break
    return lines[start:end]


def quick_state(lines: list[str]) -> list[str]:
    selected: list[str] = []
    for index, line in enumerate(lines):
        level = heading_level(line)
        if level and QUICK_HEADINGS.search(line):
            end = len(lines)
            for next_index in range(index + 1, len(lines)):
                next_level = heading_level(lines[next_index])
                if next_level is not None and next_level <= level:
                    end = next_index
                    break
            selected.extend(lines[index:end])
    if selected:
        return selected
    fallback = lines[:60]
    if len(lines) > 60:
        fallback.append("\n...（快速视图未识别到标准标题，以下为前60行）\n")
    return fallback


def print_text(path: Path, args: argparse.Namespace) -> None:
    lines = path.read_text(encoding="utf-8-sig").splitlines(keepends=True)
    if args.quick:
        output = quick_state(lines)
    elif args.section:
        output = markdown_section(lines, args.section)
        if not output:
            raise SystemExit(f"未找到 Markdown 标题：{args.section}")
    elif args.pattern:
        matcher = re.compile(args.pattern)
        output = []
        hits = 0
        for index, line in enumerate(lines):
            if matcher.search(line):
                hits += 1
                if hits > args.max_matches:
                    break
                start = max(0, index - args.before)
                end = min(len(lines), index + args.after + 1)
                output.append(f"--- 命中第 {index + 1} 行 ---\n")
                output.extend(lines[start:end])
        if not output:
            raise SystemExit(f"未找到匹配：{args.pattern}")
    elif args.tail:
        output = lines[-args.tail:]
    else:
        output = lines[: args.head or 80]
    sys.stdout.write("".join(output))


def print_csv(path: Path, args: argparse.Namespace) -> None:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    selected = []
    pattern = re.compile(args.pattern) if args.pattern else None
    for row in rows:
        if args.book and row.get("book") != args.book:
            continue
        if args.unit and row.get("unit") != args.unit:
            continue
        if args.chapter and row.get(args.chapter_column) != args.chapter:
            continue
        if pattern and not pattern.search("\t".join(row.values())):
            continue
        selected.append(row)
        if len(selected) >= args.max_matches:
            break
    if not selected:
        raise SystemExit("CSV 未找到符合条件的记录")
    fields = ["book", "unit", "global_chapter", "local_chapter", "title", "type", "tags", "summary", "core"]
    fields = [field for field in fields if field in selected[0]]
    for row in selected:
        print(" | ".join(f"{field}={row.get(field, '')}" for field in fields))


def main() -> None:
    args = parse_args()
    if not args.file.is_file():
        raise SystemExit(f"文件不存在：{args.file}")
    if args.file.suffix.lower() == ".csv":
        print_csv(args.file, args)
    else:
        print_text(args.file, args)


if __name__ == "__main__":
    main()
