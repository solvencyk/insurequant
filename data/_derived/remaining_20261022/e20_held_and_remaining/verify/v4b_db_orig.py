# -*- coding: utf-8 -*-
"""Original-vintage print of DB생명 (KR0082) 2023.1Q / 2023.2Q separate income statement (flat 2023 layout) and
FY2024 Q1/Q2 prior column, to prove old gold == original print."""
import re, sys
from pathlib import Path
ROOT = Path('C:/Users/sangwook.cho/Desktop/insurequant')
def seg(fy, startpat):
    d = list((ROOT/'data'/'dart'/fy/'raw').glob('KR0082_*'))[0]
    p = [x for x in d.glob('*.xml')][0]
    lines = p.read_text(encoding='utf-8', errors='replace').split('\n')
    # last occurrence of startpat in the "4. 재무제표" half (after the separate-section title)
    t = [i for i, l in enumerate(lines) if '<TITLE' in l and '4. 재무제표' in l and '주석' not in l][0]
    s = [i for i in range(t, len(lines)) if re.search(startpat, lines[i])][0]
    return p, lines, s
V = Path(__file__).parent
out = []
for fy, pat in (('FY2023_Q1', r'분 기 포 괄 손 익 계 산 서'), ('FY2023_Q2', r'(반|분) *기 *포 *괄 *손 *익 *계 *산 *서')):
    p, lines, s = seg(fy, pat)
    txt = '\n'.join(lines[s:s+700])
    rows = re.findall(r'<TR[^>]*>(.*?)</TR>', txt, re.S)
    for r in rows:
        cells = [re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', c)).strip() for c in re.findall(r'<T[DH][^>]*>(.*?)</T[DH]>', r, re.S)]
        if cells and re.match(r'^(I\.|1\.|II\.|III\.|\(3\)) *(보험서비스손익|보험손익|투자손익|보험금융손익|기타사업비)', cells[0]) :
            out.append(f'{fy} L{s+1} {cells}')
        if cells and re.match(r'^(\(3\)) 기타사업비', cells[0]):
            out.append(f'{fy} {cells}')
        if cells and re.match(r'^(Ⅳ|IV)\.', cells[0]):
            break
(V/'v4b_db_orig.txt').write_text('\n'.join(out), encoding='utf-8')
print('\n'.join(out))
