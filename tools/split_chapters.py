#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
《吞噬星空》按章分割脚本
- 读取 00_原文索引.md 获取各篇起止行/章节数
- 对第一篇~最终篇（序号1-29，全篇）按章切分原文
- 输出到 resources/吞噬星空_分章/第X篇_篇名/第N章_章名.txt
- 校验每篇切出章数 == 索引章数，不一致则报错
注意：原文为 CRLF(\r\n) 换行，标题行顶格，格式「第X篇 篇名 第Y章 章名」
"""
import re
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'resources', '吞噬星空.txt')
INDEX = os.path.join(ROOT, '吞噬星空大纲', '00_原文索引.md')
OUT = os.path.join(ROOT, 'resources', '吞噬星空_分章')

# 匹配章节标题行：第X篇 篇名 第Y章 [章名]（章名及前置空格均可缺）
TITLE_RE = re.compile(r'^(第.+篇|最终篇)\s+.+?\s+第.+章(?:\s*.+)?$')
# 从标题行提取「第X章 章名」部分
CHAP_RE = re.compile(r'(第.+?章)\s+(.+)$')
# 文件名非法字符
ILLEGAL = re.compile(r'[/\\:*?"<>|]')


def parse_index():
    """解析索引表格，返回篇信息列表"""
    rows = []
    with open(INDEX, encoding='utf-8') as f:
        for line in f:
            m = re.match(
                r'\|\s*(\d+)\s*\|\s*(第[^|]+篇|最终篇)\s*\|\s*([^|]+?)\s*\|'
                r'\s*(\d+)\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*([\d,]+)\s*\|',
                line)
            if m:
                rows.append({
                    'seq': int(m.group(1)),
                    'pianhao': m.group(2).strip(),
                    'pianming': m.group(3).strip(),
                    'start': int(m.group(4)),
                    'end': int(m.group(5)),
                    'chapters': int(m.group(6)),
                })
    return rows


def main():
    rows = parse_index()
    targets = rows  # 第1篇~最终篇（全篇1-29）
    print(f'索引解析：共 {len(rows)} 篇，待分割 {len(targets)} 篇（序号1-29，全篇）\n')

    with open(SRC, encoding='utf-8') as f:
        all_lines = f.readlines()

    total_files = 0
    all_ok = True
    for t in targets:
        start, end = t['start'], t['end']
        seg = all_lines[start - 1:end]  # 1-based -> 0-based 切片
        # 找章节标题行（0-based 偏移）
        title_idx = []
        for i, ln in enumerate(seg):
            s = ln.rstrip('\r\n').strip()
            if TITLE_RE.match(s):
                title_idx.append(i)

        # 合并同章号标题（处理"第三十六章上/下"分章情况）
        chap_list = []
        for ti in title_idx:
            title_raw = seg[ti].rstrip('\r\n').strip()
            m2 = CHAP_RE.search(title_raw)
            if m2:
                chap_label = m2.group(1)  # 第一章 / 第三十六章
                chap_name = m2.group(2)   # 罗峰的选择
            else:
                chap_label = f'第{len(chap_list)+1}章'
                chap_name = 'unknown'
            if chap_list and chap_list[-1]['label'] == chap_label:
                chap_list[-1]['merged'] = True  # 同章号，并入前一章
                continue
            chap_list.append({'label': chap_label, 'name': chap_name,
                              'start': ti, 'merged': False})
        for i, c in enumerate(chap_list):
            c['end'] = chap_list[i + 1]['start'] if i + 1 < len(chap_list) else len(seg)

        ok = len(chap_list) == t['chapters']
        all_ok = all_ok and ok
        flag = 'OK' if ok else f'!!! MISMATCH (期望{t["chapters"]}, 实际{len(chap_list)})'
        note = (f' (合并{len(title_idx)-len(chap_list)}个分章标题)'
                if len(title_idx) != len(chap_list) else '')
        print(f'[{t["seq"]:>2}] {t["pianhao"]} {t["pianming"]}: '
              f'{len(chap_list)} 章  {flag}{note}')

        if not ok:
            # 不一致则不写文件，继续检查下一篇
            continue

        # 写单章文件
        dirname = f'{t["pianhao"]}_{t["pianming"]}'
        outdir = os.path.join(OUT, dirname)
        os.makedirs(outdir, exist_ok=True)
        for c in chap_list:
            name = c['name']
            if c['merged']:
                name = re.sub(r'[上下]$', '', name).strip()  # 去掉分章上/下后缀
            safe_name = ILLEGAL.sub('_', name).strip()
            fname = f'{c["label"]}_{safe_name}.txt'
            content = ''.join(seg[c['start']:c['end']])
            with open(os.path.join(outdir, fname), 'w', encoding='utf-8') as f:
                f.write(content)
            total_files += 1

    print(f'\n分割完成：共写入 {total_files} 个单章文件')
    print('校验结果：' + ('全部通过' if all_ok else '存在不一致，请检查上方 MISMATCH 项'))
    sys.exit(0 if all_ok else 1)


if __name__ == '__main__':
    main()
