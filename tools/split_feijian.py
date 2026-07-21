#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
《飞剑问道》索引生成 + 按章分割脚本
- 第一篇(1-8700行附近)：章节标题「第X章 章名」不带篇前缀
- 第二篇起：章节标题「第X篇 篇名 第Y章 章名」带篇前缀
- 生成 飞剑问道大纲/00_原文索引.md
- 按章分割到 resources/飞剑问道_分章/第X篇_篇名/第N章_章名.txt
"""
import re
import os

ROOT = '/Users/dengzeyu/workspace/fanqie'
SRC = os.path.join(ROOT, 'resources', '飞剑问道.txt')
OUTDIR = os.path.join(ROOT, 'resources', '飞剑问道_分章')
INDEX = os.path.join(ROOT, '飞剑问道大纲', '00_原文索引.md')

# 第二篇起：第X篇 [篇名] 第Y章 章名（篇名可缺，缺则继承当前篇名）
CHAP2_RE = re.compile(r'^(第.+?篇)\s+(.*?)\s*(第[^章]{1,4}章)\s*(.*)$')
# 第一篇：第X章 章名（不带篇前缀）
CHAP1_RE = re.compile(r'^(第.+?章)\s*(.*)$')
ILLEGAL = re.compile(r'[/\\:*?"<>|]')


def _cn_to_num(cn):
    """中文数字转阿拉伯（支持一..三十）"""
    d = {'一': 1, '二': 2, '三': 3, '四': 4, '五': 5, '六': 6, '七': 7, '八': 8, '九': 9}
    if cn == '十':
        return 10
    if cn.startswith('十'):
        return 10 + d.get(cn[1], 0)
    if cn.startswith('二十'):
        return 20 + d.get(cn[2], 0) if len(cn) > 2 else 20
    if cn.startswith('三十'):
        return 30 + d.get(cn[2], 0) if len(cn) > 2 else 30
    return d.get(cn, 0)


def main():
    with open(SRC, encoding='utf-8') as f:
        lines = f.readlines()

    # 找所有带篇前缀的章节标题行（第二篇起）
    parts2 = []  # (行号0-based, 篇号, 篇名, 章号, 章名)
    for i, ln in enumerate(lines):
        s = ln.rstrip('\r\n').strip()
        m = CHAP2_RE.match(s)
        if m:
            parts2.append((i, m.group(1), m.group(2), m.group(3), m.group(4)))

    # 确定各篇边界
    # 第一篇：0 ~ 第一个parts2行之前
    # 第二篇起：按篇号分组
    vols = []  # {篇号, 篇名, 起始行, 终止行, 章节列表[(行号,章号,章名)]}

    # 第一篇
    first_end = parts2[0][0] if parts2 else len(lines)
    # 第一篇内找章节（不带篇前缀）
    chaps1 = []
    for i in range(0, first_end):
        s = lines[i].rstrip('\r\n').strip()
        m = CHAP1_RE.match(s)
        if m and not CHAP2_RE.match(s):
            chaps1.append((i, m.group(1), m.group(2)))
    vols.append({'ph': '第一篇', 'pn': '炼一口飞剑', 'start': 0, 'end': first_end,
                 'chaps': chaps1, 'chap_type': 1})

    # 第二篇起：按篇号分组（篇号须递增才新建篇，过滤原文篇号倒退/重复噪音）
    cur = None
    cur_pn = '未知'
    cur_num = 0
    for (i, ph, pn, ch, cn) in parts2:
        num = _cn_to_num(ph.replace('第', '').replace('篇', ''))
        if pn:
            cur_pn = pn
        if num > cur_num:
            if cur is not None:
                vols.append(cur)
            cur = {'ph': ph, 'pn': cur_pn, 'start': i, 'end': None,
                   'chaps': [(i, ch, cn)], 'chap_type': 2}
            cur_num = num
        else:
            cur['chaps'].append((i, ch, cn))
    if cur is not None:
        vols.append(cur)

    # 确定每篇终止行
    for k, v in enumerate(vols):
        v['end'] = vols[k + 1]['start'] if k + 1 < len(vols) else len(lines)

    # 字数统计
    for v in vols:
        seg = lines[v['start']:v['end']]
        v['chars'] = len(re.sub(r'\s', '', ''.join(seg)))
        v['nchaps'] = len(v['chaps'])

    # 输出索引
    os.makedirs(os.path.dirname(INDEX), exist_ok=True)
    total_ch = sum(v['nchaps'] for v in vols)
    total_chars = sum(v['chars'] for v in vols)
    with open(INDEX, 'w', encoding='utf-8') as f:
        f.write('# 《飞剑问道》原文索引\n\n')
        f.write('> 本索引由脚本自动生成。\n')
        f.write(f'> 原文路径：resources/飞剑问道.txt\n')
        f.write(f'> 文件总行数：{len(lines)}\n\n---\n\n')
        f.write('## 一、全书基本信息\n\n')
        f.write(f'| 项目 | 数据 |\n|---|---|\n')
        f.write(f'| 书名 | 《飞剑问道》 |\n')
        f.write(f'| 总篇数 | {len(vols)} |\n')
        f.write(f'| 总章节数 | {total_ch} |\n')
        f.write(f'| 总字数（非空白字符） | {total_chars:,} |\n\n---\n\n')
        f.write('## 二、篇级索引表\n\n')
        f.write('| 序号 | 篇号 | 篇名 | 起始行 | 终止行 | 章节数 | 非空白字符数 |\n')
        f.write('|---:|---|---|---:|---:|---:|---:|\n')
        for k, v in enumerate(vols):
            f.write(f"| {k+1} | {v['ph']} | {v['pn']} | {v['start']+1} | {v['end']} | {v['nchaps']} | {v['chars']:,} |\n")

    print(f'共识别 {len(vols)} 篇，{total_ch} 章，{total_chars:,} 字\n')
    for v in vols:
        print(f"[{v['ph']} {v['pn']}] {v['nchaps']} 章")

    # 按章分割
    total_files = 0
    for v in vols:
        dirname = f"{v['ph']}_{v['pn']}"
        outdir = os.path.join(OUTDIR, dirname)
        os.makedirs(outdir, exist_ok=True)
        seg = lines[v['start']:v['end']]
        base = v['start']
        chaps = v['chaps']
        for k, (ci, ch, cn) in enumerate(chaps):
            ch_start = ci - base
            ch_end = (chaps[k + 1][0] - base) if k + 1 < len(chaps) else len(seg)
            safe_cn = ILLEGAL.sub('', cn).strip()
            fname = f'{ch}_{safe_cn}.txt' if safe_cn else f'{ch}.txt'
            content = ''.join(seg[ch_start:ch_end])
            with open(os.path.join(outdir, fname), 'w', encoding='utf-8') as f:
                f.write(content)
            total_files += 1
    print(f'\n分割完成：共写入 {total_files} 个单章文件')


if __name__ == '__main__':
    main()
