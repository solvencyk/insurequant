# -*- coding: utf-8 -*-
"""verify-stage own reader: separate-basis comprehensive income statement of a DART filing.
usage as module: stmt(code, fy) -> dict(title_line, unit, rows=[(label, line, [(ctx, text, val)])])"""
import re
from pathlib import Path
ROOT = Path('C:/Users/sangwook.cho/Desktop/insurequant')
RE_TE = re.compile(r'<T[EDH]([^>]*)>(.*?)</T[EDH]>', re.S | re.I)
RE_CTX = re.compile(r'ACONTEXT="([^"]*)"')
RE_DEC = re.compile(r'ADECIMAL="([^"]*)"')
RE_TAG = re.compile(r'<[^>]+>')

def main_xml(code, fy):
    base = ROOT/'data'/'dart'/fy/'raw'
    c = []
    for d in sorted(base.glob(code+'_*')):
        for p in list(d.glob('*.xml'))+list(d.glob('xml/*.xml')):
            if '_007' in p.name: continue
            c.append(p)
    c.sort(key=lambda p: p.stat().st_size, reverse=True)
    return c[0] if c else None

def num(t):
    t = t.replace(',', '').replace('\u3000', '').strip()
    if t in ('', '-'): return None
    neg = (t.startswith('(') and t.endswith(')')) or t.startswith('-') or t.startswith('\u25b3')
    t = t.strip('()-\u25b3 ')
    try: v = float(t)
    except ValueError: return None
    return -v if neg else v

def stmt(code, fy, title_pat=r'포괄손익계산서'):
    p = main_xml(code, fy)
    text = p.read_text(encoding='utf-8', errors='replace')
    lines = text.split('\n')
    # char offset -> line
    offs = []; o = 0
    for l in lines:
        offs.append(o); o += len(l)+1
    import bisect
    def ln(pos): return bisect.bisect_right(offs, pos)
    titles = [(m.start(), m.group(0)) for m in re.finditer(r'<TITLE[^>]*>[^<]*</TITLE>', text)]
    res = []
    cm = [(m.start(), m.group(0)) for m in re.finditer(r'<!-- =====[^>]*===== -->', text)]
    if not titles or not any(re.search(title_pat, RE_TAG.sub('', t)) for _, t in titles):
        titles = cm
    for i,(pos, t) in enumerate(titles):
        tt = t if t.startswith('<!--') else RE_TAG.sub('', t)
        if re.search(title_pat, tt) and '연결' not in tt and '기타포괄' not in tt:
            end = titles[i+1][0] if i+1 < len(titles) else len(text)
            seg = text[pos:end]
            unit = re.search(r'단위\s*:\s*([^)<]*)', seg)
            rows = []
            for trm in re.finditer(r'<TR[^>]*>(.*?)</TR>', seg, re.S | re.I):
                cells = RE_TE.findall(trm.group(1))
                if not cells: continue
                lab = re.sub(r'\s+', ' ', RE_TAG.sub('', cells[0][1]).replace('　', ' ')).strip()
                vals = []
                for attrs, inner in cells[1:]:
                    cmx = RE_CTX.search(attrs)
                    vals.append((cmx.group(1) if cmx else None, RE_TAG.sub('', inner).strip()))
                rows.append((lab, ln(pos+trm.start()), vals))
            res.append(dict(title=tt, title_line=ln(pos), unit=unit.group(1).strip() if unit else None, rows=rows, path=str(p)))
    return res

if __name__ == '__main__':
    import sys
    code, fy = sys.argv[1], sys.argv[2]
    for s in stmt(code, fy):
        print('###', s['title'], 'line', s['title_line'], 'unit', s['unit'], s['path'])
        for lab, l, vals in s['rows']:
            print(l, '|', lab, '|', ' ; '.join(f"{(c or '-').split('_')[0]}={v}" for c, v in vals))
