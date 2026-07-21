#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""《沧元图》索引生成 + 按章分割脚本（集+章模式，第一集无集前缀，类似飞剑问道路）"""
import re, os

ROOT = '/Users/dengzeyu/workspace/fanqie'
SRC = os.path.join(ROOT, 'resources', '沧元图.txt')
OUTDIR = os.path.join(ROOT, 'resources', '沧元图_分章')
INDEX = os.path.join(ROOT, '沧元图大纲', '00_原文索引.md')

# 集标记：第X集 集名 或 第X集集名
JI_RE = re.compile(r'^(第.+?集)\s*(.*)$')
# 带集前缀的章节：第X集 [集名] 第Y章 章名
CHAP2_RE = re.compile(r'^(第.+?集)\s+(?:([^第]*?)\s+)?(第[^章]{1,4}章)\s*(.*)$')
# 不带集前缀的章节（第一集）：第X章 章名
CHAP1_RE = re.compile(r'^(第[^集]{1,5}章)\s*(.*)$')
ILLEGAL = re.compile(r'[/\\:*?"<>|]')

def _cn_to_num(cn):
    """中文/阿拉伯数字转int（支持一..二十九及1..29）"""
    cn = cn.strip()
    if cn.isdigit():
        return int(cn)
    d = {'一':1,'二':2,'三':3,'四':4,'五':5,'六':6,'七':7,'八':8,'九':9}
    if cn == '十': return 10
    if cn.startswith('十'): return 10 + d.get(cn[1], 0)
    if cn.startswith('二十'): return 20 + d.get(cn[2], 0) if len(cn) > 2 else 20
    if cn.startswith('三十'): return 30 + d.get(cn[2], 0) if len(cn) > 2 else 30
    return d.get(cn, 0)

def main():
    with open(SRC, encoding='utf-8') as f:
        lines = f.readlines()

    # 找所有带集前缀的章节标题行
    parts2 = []
    for i, ln in enumerate(lines):
        s = ln.rstrip('\r\n').strip()
        m = CHAP2_RE.match(s)
        if m:
            parts2.append((i, m.group(1), m.group(2), m.group(3), m.group(4)))

    # 第一集范围：0到第一个带集前缀的章节前
    first_end = parts2[0][0] if parts2 else len(lines)
    chaps1 = []
    for i in range(0, first_end):
        s = lines[i].rstrip('\r\n').strip()
        m = CHAP1_RE.match(s)
        if m and not CHAP2_RE.match(s) and not JI_RE.match(s):
            chaps1.append((i, m.group(1), m.group(2)))
    vols = [{'jh': '第一集', 'jn': '秘技三秋叶', 'start': 0, 'end': first_end,
             'chaps': chaps1, 'chap_type': 1}]

    # 第二集起：按集号分组（集号递增才新建集）
    cur = None
    cur_jn = '未知'
    cur_num = 0
    for (i, jh, jn, ch, cn) in parts2:
        num = _cn_to_num(jh.replace('第','').replace('集',''))
        if jn: cur_jn = jn
        if num > cur_num:
            if cur is not None:
                vols.append(cur)
            cur = {'jh': jh, 'jn': cur_jn, 'start': i, 'end': None,
                   'chaps': [(i, ch, cn)], 'chap_type': 2}
            cur_num = num
        else:
            cur['chaps'].append((i, ch, cn))
    if cur is not None:
        vols.append(cur)

    for k, v in enumerate(vols):
        v['end'] = vols[k + 1]['start'] if k + 1 < len(vols) else len(lines)
        seg = lines[v['start']:v['end']]
        v['chars'] = len(re.sub(r'\s', '', ''.join(seg)))
        v['nchaps'] = len(v['chaps'])

    # 输出索引
    os.makedirs(os.path.dirname(INDEX), exist_ok=True)
    total_ch = sum(v['nchaps'] for v in vols)
    total_chars = sum(v['chars'] for v in vols)
    with open(INDEX, 'w', encoding='utf-8') as f:
        f.write('# 《沧元图》原文索引\n\n> 本索引由脚本自动生成。\n')
        f.write(f'> 原文路径：resources/沧元图.txt\n> 文件总行数：{len(lines)}\n\n---\n\n')
        f.write('## 一、全书基本信息\n\n| 项目 | 数据 |\n|---|---|\n')
        f.write(f'| 书名 | 《沧元图》 |\n| 总集数 | {len(vols)} |\n')
        f.write(f'| 总章节数 | {total_ch} |\n| 总字数（非空白字符） | {total_chars:,} |\n\n---\n\n')
        f.write('## 二、集级索引表\n\n| 序号 | 集号 | 集名 | 起始行 | 终止行 | 章节数 | 非空白字符数 |\n')
        f.write('|---:|---|---|---:|---:|---:|---:|\n')
        for k, v in enumerate(vols):
            f.write(f"| {k+1} | {v['jh']} | {v['jn']} | {v['start']+1} | {v['end']} | {v['nchaps']} | {v['chars']:,} |\n")
    print(f'共识别 {len(vols)} 集，{total_ch} 章，{total_chars:,} 字\n')
    for v in vols:
        print(f"[{v['jh']} {v['jn']}] {v['nchaps']} 章")

    # 按章分割
    total_files = 0
    for v in vols:
        dirname = f"{v['jh']}_{v['jn']}"
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
