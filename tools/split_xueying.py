#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""《雪鹰领主》索引生成 + 按章分割脚本（篇标记单独行，章节不带篇前缀，同莽荒纪模式）"""
import re, os

ROOT = '/Users/dengzeyu/workspace/fanqie'
SRC = os.path.join(ROOT, 'resources', '雪鹰领主.txt')
OUTDIR = os.path.join(ROOT, 'resources', '雪鹰领主_分章')
INDEX = os.path.join(ROOT, '雪鹰领主大纲', '00_原文索引.md')

VOL_RE = re.compile(r'^(第.+篇)\s+(.+)$')
CHAP_RE = re.compile(r'^(第.+?章)\s*(.*)$')
ILLEGAL = re.compile(r'[/\\:*?"<>|]')

def main():
    with open(SRC, encoding='utf-8') as f:
        lines = f.readlines()
    # 找篇标记
    vols = []
    for i, ln in enumerate(lines):
        s = ln.rstrip('\r\n').strip()
        m = VOL_RE.match(s)
        if m:
            vols.append((i, m.group(1), m.group(2)))
    vol_ranges = []
    for idx, (i, vh, vn) in enumerate(vols):
        start = i + 1
        end = vols[idx + 1][0] if idx + 1 < len(vols) else len(lines)
        vol_ranges.append((i, vh, vn, start, end))
    print(f'共识别 {len(vols)} 篇\n')
    all_vols = []
    for (vi, vh, vn, start, end) in vol_ranges:
        seg = lines[start:end]
        chap_idx = []
        for j, ln in enumerate(seg):
            s = ln.rstrip('\r\n').strip()
            if CHAP_RE.match(s) and not VOL_RE.match(s):
                chap_idx.append(j)
        text = ''.join(seg)
        chars = len(re.sub(r'\s', '', text))
        all_vols.append({'vh': vh, 'vn': vn, 'start': start, 'end': end,
                         'chapters': len(chap_idx), 'chars': chars,
                         'chap_idx': chap_idx, 'seg': seg})
    # 输出索引
    os.makedirs(os.path.dirname(INDEX), exist_ok=True)
    total_ch = sum(v['chapters'] for v in all_vols)
    total_chars = sum(v['chars'] for v in all_vols)
    with open(INDEX, 'w', encoding='utf-8') as f:
        f.write('# 《雪鹰领主》原文索引\n\n> 本索引由脚本自动生成。\n')
        f.write(f'> 原文路径：resources/雪鹰领主.txt\n> 文件总行数：{len(lines)}\n\n---\n\n')
        f.write('## 一、全书基本信息\n\n| 项目 | 数据 |\n|---|---|\n')
        f.write(f'| 书名 | 《雪鹰领主》 |\n| 总篇数 | {len(all_vols)} |\n')
        f.write(f'| 总章节数 | {total_ch} |\n| 总字数（非空白字符） | {total_chars:,} |\n\n---\n\n')
        f.write('## 二、篇级索引表\n\n| 序号 | 篇号 | 篇名 | 起始行 | 终止行 | 章节数 | 非空白字符数 |\n')
        f.write('|---:|---|---|---:|---:|---:|---:|\n')
        for k, v in enumerate(all_vols):
            f.write(f"| {k+1} | {v['vh']} | {v['vn']} | {v['start']+1} | {v['end']} | {v['chapters']} | {v['chars']:,} |\n")
    print(f'索引已写入：{INDEX}')
    print(f'全书：{len(all_vols)}篇，{total_ch}章，{total_chars:,}字\n')
    # 按章分割
    total_files = 0
    for v in all_vols:
        dirname = f"{v['vh']}_{v['vn']}"
        outdir = os.path.join(OUTDIR, dirname)
        os.makedirs(outdir, exist_ok=True)
        ci = v['chap_idx']
        seg = v['seg']
        for k, ti in enumerate(ci):
            ch_start = ti
            ch_end = ci[k + 1] if k + 1 < len(ci) else len(seg)
            title_raw = seg[ti].rstrip('\r\n').strip()
            m = CHAP_RE.match(title_raw)
            chap_label = m.group(1) if m else f'第{k+1}章'
            chap_name = m.group(2).strip() if m and m.group(2) else ''
            safe_name = ILLEGAL.sub('_', chap_name).strip()
            fname = f'{chap_label}_{safe_name}.txt' if safe_name else f'{chap_label}.txt'
            content = ''.join(seg[ch_start:ch_end])
            with open(os.path.join(outdir, fname), 'w', encoding='utf-8') as f:
                f.write(content)
            total_files += 1
        print(f"[{v['vh']} {v['vn']}] {v['chapters']} 章  OK")
    print(f'\n分割完成：共写入 {total_files} 个单章文件')

if __name__ == '__main__':
    main()
