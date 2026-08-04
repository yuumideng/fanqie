#!/usr/bin/env python3
"""Extract protagonist skill/soul/realm passages from the first 300 chapters.

The extracted passage text is copied from the user-provided chapter files. Only
the surrounding Markdown headings and topic labels are generated here.
"""

from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = ROOT / "resources"
OUTPUT_ROOT = ROOT / "docs" / "原文专项摘录"


BOOKS = {
    "吞噬星空": {"dir": "吞噬星空_分章", "lead": "罗峰"},
    "莽荒纪": {"dir": "莽荒纪_分章", "lead": "纪宁"},
    "飞剑问道": {"dir": "飞剑问道_分章", "lead": "秦云"},
    "沧元图": {"dir": "沧元图_分章", "lead": "孟川"},
    "雪鹰领主": {"dir": "雪鹰领主_分章", "lead": "东伯雪鹰"},
}


CN_DIGITS = {
    "零": 0,
    "〇": 0,
    "一": 1,
    "二": 2,
    "两": 2,
    "三": 3,
    "四": 4,
    "五": 5,
    "六": 6,
    "七": 7,
    "八": 8,
    "九": 9,
    "十": 10,
    "百": 100,
    "千": 1000,
}


def chinese_number(value: str) -> int:
    if value.isdigit():
        return int(value)
    total = 0
    section = 0
    for char in value:
        number = CN_DIGITS.get(char)
        if number is None:
            continue
        if number >= 10:
            total += (section or 1) * number
            section = 0
        else:
            section = section * 10 + number
    return total + section


VOLUME_RE = re.compile(r"第([零〇一二两三四五六七八九十百千0-9]+)[卷篇集]")
CHAPTER_RE = re.compile(r"第([零〇一二两三四五六七八九十百千0-9]+)章")


TOPICS = {
    "技艺": re.compile(
        r"修炼|练功|练刀|练剑|练枪|练拳|练体|炼体|炼气|功法|法诀|秘法|秘技|剑法|刀法|枪法|拳法|身法|步法|箭术|棍法|棍术|掌法|指法|招式|招法|武学|术法|神通|剑意|刀意|枪意|剑气|刀气|枪术|剑阵|剑域|领域|斗气|真元|法力|仙力|气血|肉身|念力|原力|发力|力量振幅|振幅|战刀|战技|技巧|技艺|拳力|拳力测试|速度测试|神经反应|测试机|考核|宇宙能量|感应|神魔炼体|意境|道境|悟道|参悟|领悟|演练|推演|心境"
    ),
    "灵魂": re.compile(
        r"灵魂|魂魄|神魂|元神|心魂|心力|神念|神识|灵识|魂海|识海|念力|精神念力|心灵之力|意志威压"
    ),
    "境界提升": re.compile(
        r"境界|突破|破境|晋升|提升|进阶|跨入|踏入|圆满|大成|小成|入门|修为|后天|先天|紫府|万象|元神|返虚|天仙|炼体|脱胎|洗髓|无漏|神魔|神魔体|神体|洞天|世界境|道君|合道|主宰|尊者|界主|域主|行星级|恒星级|宇宙级|不朽|真神|虚空神|浑源|神海|神桥|造化|真意|神心|超凡|半神|基因原能|生命基因|道果|天人合一|仙门|金丹|散仙|仙人"
    ),
}


def chapter_files(book_dir: Path) -> list[tuple[int, int, Path, str]]:
    chapters: list[tuple[int, int, Path, str]] = []
    for volume in book_dir.iterdir():
        if not volume.is_dir():
            continue
        volume_match = VOLUME_RE.search(volume.name)
        if not volume_match:
            continue
        volume_no = chinese_number(volume_match.group(1))
        for path in volume.glob("*.txt"):
            chapter_match = CHAPTER_RE.search(path.name)
            if not chapter_match:
                continue
            chapter_no = chinese_number(chapter_match.group(1))
            title = path.stem.split("_", 1)[1] if "_" in path.stem else path.stem
            chapters.append((volume_no, chapter_no, path, title))
    return sorted(chapters, key=lambda item: (item[0], item[1], item[2].name))


def topic_hits(text: str) -> list[str]:
    return [name for name, pattern in TOPICS.items() if pattern.search(text)]


STRONG_ACTION = re.compile(
    r"修炼|练功|练习|参悟|领悟|感悟|悟出|突破|晋升|提升|进步|达到|掌握|施展|催动|运转|凝聚|锻炼|测试|检测|考核|演练|推演|创造|自创|发力|出拳|出刀|出剑|出枪|挥刀|挥剑|刺枪|操控|拳头|拳力|右拳|左拳|冲刺|蹬踏|格挡|闪躲|躲闪|吸收|感应|感受到|感觉到"
)


SELF_ACTION = re.compile(
    r"(?:我|自己|自身).{0,45}(?:修炼|练功|练习|参悟|领悟|感悟|突破|提升|进步|掌握|施展|运转|凝聚|锻炼|测试|检测|考核|发力|出拳|出刀|出剑|出枪|挥刀|挥剑|刺枪)|(?:修炼|练功|练习|参悟|领悟|感悟|突破|提升|进步|掌握|施展|运转|凝聚|锻炼|测试|检测|考核|发力|出拳|出刀|出剑|出枪|挥刀|挥剑|刺枪).{0,45}(?:我|自己|自身)"
)


def paragraph_blocks(text: str) -> list[str]:
    # The source splitter stores one logical paragraph per physical line, with
    # blank lines used only as visual separators. Preserve that paragraph as a
    # whole so dialogue and the protagonist's immediate reaction are not cut
    # into incomplete sentences.
    return [line for line in text.splitlines() if line.strip()]


def extract_chapter(text: str, title: str, lead: str) -> list[tuple[list[str], str]]:
    blocks = paragraph_blocks(text)
    title_hits = topic_hits(title)
    selected: list[tuple[int, list[str]]] = []
    for index, block in enumerate(blocks):
        hits = topic_hits(block)
        if not hits:
            continue
        strong = STRONG_ACTION.search(block)
        direct = SELF_ACTION.search(block)
        if re.search(r"KTV|包厢|唱歌|小姑娘", block):
            continue
        if re.search(r"罗峰师兄", block) and re.search(r"我的目标|大学毕业前", block):
            continue
        if re.search(r"终有一天|梦想", block) and not re.search(r"修炼|提升|突破|达到|测试|领悟", block):
            continue
        if re.search(r"考核", block) and not re.search(r"身体|实力|力量|拳力|速度|进步|提升|修炼|练习|测试|通过", block):
            continue
        lead_near_action = False
        for lead_match in re.finditer(re.escape(lead), block):
            window = block[max(0, lead_match.start() - 100) : lead_match.end() + 100]
            if STRONG_ACTION.search(window):
                lead_near_action = True
                break
        # A passage is kept only when it describes the protagonist's own
        # training/understanding/progress. Mere mention of generic terms such
        # as “实力” or a stranger's cultivation is not enough.
        # First-person training language without the protagonist's name is
        # ambiguous: it often belongs to a side character's dialogue. Keep it
        # only when the same source line also anchors the protagonist.
        if not lead_near_action:
            continue
        if not strong:
            continue
        selected.append((index, ", ".join(hits)))

    if not selected and title_hits:
        # A topical chapter title with unusual formatting still deserves its
        # opening paragraph rather than being silently omitted.
        selected = [(0, ", ".join(title_hits))] if blocks else []

    ranges: list[tuple[int, int, set[str]]] = []
    for index, labels in selected:
        # Do not attach generic neighbouring narration. The user requested
        # passages that actually show the protagonist's own progress; keeping
        # only the hit line makes that boundary auditable.
        start = index
        end = index
        labels_set = set(labels.split(", "))
        short_gap = (
            ranges
            and start > ranges[-1][1] + 1
            and all(len(blocks[i].strip()) <= 10 for i in range(ranges[-1][1] + 1, start))
        )
        if ranges and (start <= ranges[-1][1] + 1 or short_gap):
            old_start, old_end, old_labels = ranges[-1]
            ranges[-1] = (old_start, max(old_end, end), old_labels | labels_set)
        else:
            ranges.append((start, end, labels_set))

    result: list[tuple[list[str], str]] = []
    for start, end, labels in ranges:
        result.append((blocks[start : end + 1], "、".join(sorted(labels))))
    return result


def markdown_for_book(book: str, config: dict[str, str]) -> tuple[str, int, int]:
    files = chapter_files(SOURCE_ROOT / config["dir"])
    first = files[:300]
    output: list[str] = [
        f"# 《{book}》前300章：主角技艺、灵魂与境界提升原文摘录",
        "",
        "> 原文来自仓库 `resources/" + config["dir"] + "`。以下正文均按原分章文件逐段截取，仅增加卷章标题、主题标签和来源路径，不改写原文。",
        "> 选取范围：按卷号、章号排序后的前300章；只保留原文段落中明确涉及主角自身训练、领悟、能力变化或境界推进的内容。",
        "",
    ]
    chapter_count = 0
    fragment_count = 0
    for global_no, (volume_no, chapter_no, path, title) in enumerate(first, 1):
        text = path.read_text(encoding="utf-8")
        fragments = extract_chapter(text, title, config["lead"])
        if not fragments:
            continue
        chapter_count += 1
        volume_label = path.parent.name
        output.extend(
            [
                f"## 原文第{global_no}章｜{volume_label}·第{chapter_no}章 {title}",
                f"来源：`{path.relative_to(ROOT)}`",
                "",
            ]
        )
        for fragment_no, (blocks, labels) in enumerate(fragments, 1):
            fragment_count += 1
            output.extend([f"### 片段{fragment_no}｜主题：{labels}", ""])
            output.append("\n\n".join(blocks))
            output.extend(["", "---", ""])
    return "\n".join(output).rstrip() + "\n", chapter_count, fragment_count


def main() -> None:
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    manifest: list[str] = [
        "# 前300章技艺、灵魂与境界提升原文摘录",
        "",
        "> 本目录只收录当前仓库可读取的五套完整分章原文。第六套《宇宙职业选手》只有大纲索引，原文路径指向仓库外且当前不可读取，因此没有用大纲内容冒充原文摘录。",
        "",
    ]
    for book, config in BOOKS.items():
        content, chapters, fragments = markdown_for_book(book, config)
        filename = f"{book}_前300章技艺灵魂境界原文摘录.md"
        (OUTPUT_ROOT / filename).write_text(content, encoding="utf-8")
        manifest.append(f"- [{book}]({filename})：命中 {chapters} 个章节，{fragments} 个连续片段。")
    manifest.extend(
        [
            "- 《宇宙职业选手》：缺少可读取的原文/分章文件，待用户补充原文后再生成。",
            "",
            "## 主题口径",
            "",
            "- **技艺**：功法、秘法、刀剑枪法、身法、招式、意境、悟道和相关训练过程。",
            "- **灵魂**：灵魂、魂魄、元神、神念、神识、心力、心魂、念力及明确的灵魂/意志修行。",
            "- **境界提升**：境界、修为、突破、进阶、圆满及各作品前期境界名称。",
        ]
    )
    (OUTPUT_ROOT / "README.md").write_text("\n".join(manifest) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
