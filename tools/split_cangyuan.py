#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""《沧元图》索引生成 + 按章分割脚本（集+章模式，第一集无集前缀）。

修复说明（2026-07-22）：
1. 原文集号有笔误，改用"章号==1"作为新集判定信号（每集重启编号）。
2. cn() 支持 1-99 中文数字（原仅支持到三十几，致"第四十章"等解析为0）。
3. CHAP1 正则收紧为 第[一二三四五六七八九十]{1,4}章，排除"第二更，补欠章节"等误匹配。
4. 集号与章号间空格可选 \s*，识别"第28集第31章"无空格章头。
5. 第一集末章"第二十三章...本集终"不再被 JI_RE 误排除。
6. 集号统一规范为中文数字。真实集数 29。
"""
import re, os, shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'resources', '沧元图.txt')
OUTDIR = os.path.join(ROOT, 'resources', '沧元图_分章')
INDEX = os.path.join(ROOT, '沧元图大纲', '00_原文索引.md')

# 集标记：第X集 集名
JI_RE = re.compile(r'^第[一二三四五六七八九十0-9]{1,4}集')
# 带集前缀的章节：第X集 [集名] 第Y章 章名（集号与章号间空格可选）
CHAP2_RE = re.compile(r'^(第[一二三四五六七八九十0-9]{1,4}集)\s*(?:([^第]*?)\s+)?(第[一二三四五六七八九十0-9]{1,4}章)\s*(.*)$')
# 不带集前缀的章节（第一集）：第X章 章名（仅中文数字，排除"第二更"等）
CHAP1_RE = re.compile(r'^(第[一二三四五六七八九十]{1,4}章)\s*(.*)$')
ILLEGAL = re.compile(r'[/\\:*?"<>|]')

def _cn_to_num(cn):
    """中文/阿拉伯数字转int（支持1-99）"""
    cn = cn.strip()
    if cn.isdigit():
        return int(cn)
    d = {'一':1,'二':2,'三':3,'四':4,'五':5,'六':6,'七':7,'八':8,'九':9}
    if cn == '十': return 10
    if cn.startswith('十'): return 10 + d.get(cn[1], 0)
    if cn.startswith('二十'): return 20 + d.get(cn[2], 0) if len(cn) > 2 else 20
    if cn.startswith('三十'): return 30 + d.get(cn[2], 0) if len(cn) > 2 else 30
    if cn.startswith('四十'): return 40 + d.get(cn[2], 0) if len(cn) > 2 else 40
    if cn.startswith('五十'): return 50 + d.get(cn[2], 0) if len(cn) > 2 else 50
    if cn.startswith('六十'): return 60 + d.get(cn[2], 0) if len(cn) > 2 else 60
    if cn.startswith('七十'): return 70 + d.get(cn[2], 0) if len(cn) > 2 else 70
    if cn.startswith('八十'): return 80 + d.get(cn[2], 0) if len(cn) > 2 else 80
    if cn.startswith('九十'): return 90 + d.get(cn[2], 0) if len(cn) > 2 else 90
    return d.get(cn, 0)

def _num_to_cn(n):
    """int 转中文数字（1-99）"""
    d = {1:'一',2:'二',3:'三',4:'四',5:'五',6:'六',7:'七',8:'八',9:'九'}
    if n <= 9: return d[n]
    if n == 10: return '十'
    if n < 20: return '十' + d[n - 10]
    if n % 10 == 0:
        tens = n // 10
        td = {2:'二十',3:'三十',4:'四十',5:'五十',6:'六十',7:'七十',8:'八十',9:'九十'}
        return td[tens]
    tens = n // 10
    ones = n % 10
    td = {2:'二十',3:'三十',4:'四十',5:'五十',6:'六十',7:'七十',8:'八十',9:'九十'}
    return td[tens] + d[ones]

def main():
    with open(SRC, encoding='utf-8') as f:
        lines = f.readlines()

    # 找所有带集前缀的章节标题行
    parts2 = []
    for i, ln in enumerate(lines):
        s = ln.rstrip('\r\n').strip()
        m = CHAP2_RE.match(s)
        if m:
            parts2.append((i, m.group(1), m.group(2) or '', m.group(3), m.group(4)))

    # 第一集范围：0到第一个带集前缀的章节前
    first_end = parts2[0][0] if parts2 else len(lines)
    chaps1 = []
    for i in range(0, first_end):
        s = lines[i].rstrip('\r\n').strip()
        m = CHAP1_RE.match(s)
        if m and not CHAP2_RE.match(s):
            chaps1.append((i, m.group(1), m.group(2)))
    vols = [{'jh': '第一集', 'jn': '秘技三秋叶', 'start': 0, 'end': first_end,
             'chaps': chaps1, 'chap_type': 1}]

    # 第二集起：以"章号==1"作为新集判定信号（每集重启编号，规避原文集号笔误）
    # 去重：同一集内若新章头(章号,章名)与上一章头完全相同，视为重复抓取，跳过
    cur = None
    for (i, jh_raw, jn_raw, ch_raw, cn_raw) in parts2:
        ch_num = _cn_to_num(ch_raw.replace('第', '').replace('章', ''))
        if cur is None:
            num = _cn_to_num(jh_raw.replace('第', '').replace('集', ''))
            cur = {'jh': '第' + _num_to_cn(num) + '集', 'jn': jn_raw or '未知',
                   'start': i, 'end': None,
                   'chaps': [(i, ch_raw, cn_raw)], 'chap_type': 2, 'last_key': (ch_raw, cn_raw)}
        elif ch_num == 1:
            num = _cn_to_num(jh_raw.replace('第', '').replace('集', ''))
            vols.append(cur)
            cur = {'jh': '第' + _num_to_cn(num) + '集', 'jn': jn_raw or '未知',
                   'start': i, 'end': None,
                   'chaps': [(i, ch_raw, cn_raw)], 'chap_type': 2, 'last_key': (ch_raw, cn_raw)}
        else:
            key = (ch_raw, cn_raw)
            if cur['chaps'] and cur.get('last_key') == key:
                # 重复抓取，跳过
                continue
            cur['chaps'].append((i, ch_raw, cn_raw))
            cur['last_key'] = key
    if cur is not None:
        vols.append(cur)

    for k, v in enumerate(vols):
        v['end'] = vols[k + 1]['start'] if k + 1 < len(vols) else len(lines)
        seg = lines[v['start']:v['end']]
        v['chars'] = len(re.sub(r'\s', '', ''.join(seg)))
        v['nchaps'] = len(v['chaps'])

    # 清理旧分章目录后重建
    if os.path.isdir(OUTDIR):
        shutil.rmtree(OUTDIR)

    # 输出索引
    os.makedirs(os.path.dirname(INDEX), exist_ok=True)
    total_ch = sum(v['nchaps'] for v in vols)
    total_chars = sum(v['chars'] for v in vols)
    with open(INDEX, 'w', encoding='utf-8') as f:
        f.write('# 《沧元图》原文索引\n\n> 本索引由脚本自动生成。\n')
        f.write(f'> 原文路径：resources/沧元图.txt\n> 文件总行数：{len(lines)}\n')
        f.write(f'> 修复说明：原文集号有笔误，脚本改用"章号==1"判定新集；cn()支持1-99；正则排除误匹配。真实集数29集。\n\n---\n\n')
        f.write('## 一、全书基本信息\n\n| 项目 | 数据 |\n|---|---|\n')
        f.write(f'| 书名 | 《沧元图》 |\n| 总集数 | {len(vols)} |\n')
        f.write(f'| 总章节数 | {total_ch} |\n| 总字数（非空白字符） | {total_chars:,} |\n\n---\n\n')
        f.write('## 二、集级索引表\n\n| 序号 | 集号 | 集名 | 起始行 | 终止行 | 章节数 | 非空白字符数 |\n')
        f.write('|---:|---|---|---:|---:|---:|---:|\n')
        for k, v in enumerate(vols):
            f.write(f"| {k+1} | {v['jh']} | {v['jn']} | {v['start']+1} | {v['end']} | {v['nchaps']} | {v['chars']:,} |\n")
    print(f'共识别 {len(vols)} 集，{total_ch} 章，{total_chars:,} 字\n')
    for k, v in enumerate(vols):
        print(f"[{v['jh']} {v['jn']}] {v['nchaps']} 章  行{v['start']+1}-{v['end']}")

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
