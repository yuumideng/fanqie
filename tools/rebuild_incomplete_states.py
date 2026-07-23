#!/usr/bin/env python3
"""Rebuild missing or empty state archives from their current outline files.

This is intentionally conservative: existing non-empty state files are left
untouched, and the generated files are a lightweight handoff view rather than
an independent correctness audit of the source text.
"""

from pathlib import Path
import re


ROOT = Path(__file__).resolve().parent.parent


def get_section(text: str, number: str) -> list[str]:
    """Return the body of the numbered ## section, without surrounding blanks."""
    lines = text.splitlines()
    start = None
    for i, line in enumerate(lines):
        if re.match(rf"^##\s*{re.escape(number)}[、.]", line):
            start = i + 1
            break
    if start is None:
        return []
    end = len(lines)
    for i in range(start, len(lines)):
        if re.match(r"^##\s+", lines[i]):
            end = i
            break
    while start < end and not lines[start].strip():
        start += 1
    while end > start and not lines[end - 1].strip():
        end -= 1
    return lines[start:end]


def compact(lines: list[str], limit: int) -> list[str]:
    """Keep useful markdown lines while bounding the generated state size."""
    out = []
    for line in lines:
        if line.strip() or (out and out[-1].strip()):
            out.append(line.rstrip())
        if len(out) >= limit:
            break
    while out and not out[-1].strip():
        out.pop()
    return out


def chapter_blocks(lines: list[str]) -> list[list[str]]:
    starts = []
    for i, line in enumerate(lines):
        if re.match(r"^###\s+.*章", line) or re.match(r"^\*\*第[^*]+章.*\*\*$", line):
            starts.append(i)
    blocks = []
    for pos, start in enumerate(starts):
        end = starts[pos + 1] if pos + 1 < len(starts) else len(lines)
        block = compact(lines[start:end], 6)
        if block:
            blocks.append(block)
    return blocks


def unit_name(outline: Path) -> str:
    parts = outline.stem.split("_")
    return parts[1] if len(parts) > 1 else outline.stem


def title(outline: Path) -> str:
    for line in outline.read_text(encoding="utf-8").splitlines():
        if line.startswith("# "):
            return line[2:].strip().replace(" 大纲", "")
    return outline.stem


def first_info(text: str) -> list[str]:
    info = get_section(text, "一")
    return compact(info, 18)


def make_state(outline: Path) -> str:
    text = outline.read_text(encoding="utf-8")
    name = title(outline)
    section_two = get_section(text, "二")
    section_five = get_section(text, "五")
    section_six = get_section(text, "六")
    section_seven = get_section(text, "七")
    details = get_section(text, "三")
    recent = chapter_blocks(details)[-10:]

    lines = [
        f"# {name} · 滚动状态档案",
        "",
        "> 本档案由对应篇/卷/集现有大纲生成，用于后续 Agent 轻量接手；未对原文进行全库正确性审计。",
        "",
        "## 1. 阶段概况",
    ]
    lines.extend(first_info(text) or ["- 基本信息未在当前大纲中单列，后续按需查询索引。"])
    lines += ["", "## 2. 核心人物与设定"]
    person_source = section_six or section_five
    if person_source:
        lines.extend(compact(person_source, 42))
    else:
        lines.append("- 当前独立大纲未附人物关系/设定汇总；后续按任务需要从章节大纲或原文提取。")
    lines += ["", "## 3. 核心主线进度"]
    if section_two and any(line.strip() for line in section_two):
        lines.extend(compact(section_two, 32))
    else:
        lines.append("- 当前独立大纲未重复收录合并版主线，以下近章摘要作为本阶段交接依据。")
    lines += ["", "## 4. 近章摘要队列"]
    if recent:
        for block in recent:
            lines.extend(block)
            lines.append("")
        if lines[-1] == "":
            lines.pop()
    else:
        lines.append("- 当前大纲未提供可提取的章节摘要。")
    lines += ["", "## 5. 伏笔与待确认项"]
    if section_seven:
        lines.extend(compact(section_seven, 45))
    else:
        lines.append("- 当前大纲未附独立伏笔追踪；遇到不确定事实时按项目规则回查原文，不凭此档案猜测补全。")
    lines += ["", "## 6. 交接边界", "- 本档案只作为当前阶段的轻量状态入口；具体分析、修订或冲突核查时，仍需按需读取对应原文、索引和大纲。"]
    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    rebuilt = []
    for book_dir in sorted(ROOT.glob("*大纲")):
        state_dir = book_dir / "_state"
        state_dir.mkdir(exist_ok=True)
        for outline in sorted(book_dir.glob("*.md")):
            if outline.name.startswith("00_"):
                continue
            state = state_dir / f"{unit_name(outline)}_state.md"
            if state.exists() and state.stat().st_size > 0:
                continue
            state.write_text(make_state(outline), encoding="utf-8")
            rebuilt.append(state.relative_to(ROOT).as_posix())
    print(f"rebuilt={len(rebuilt)}")
    for path in rebuilt:
        print(path)


if __name__ == "__main__":
    main()
