import sys
sys.path.insert(0,'C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e23_d1_d3/verify_kr0072_kdb_loaded')
from xlib import *
V=ROOT+'data/_derived/remaining_20261022/e23_d1_d3/verify_kr0072_kdb_loaded/'
out=open(V+'s03_enum.txt','w',encoding='utf-8')
for q,p in FILES.items():
    txt=read(p); T=tables(txt)
    out.write(f'=== {q} {p} tables={len(T)}\n')
    for ln,rows in T:
        labs=[r[0] for r in rows]
        if any(l.startswith('1. 기초 보험계약자산') for l in labs):
            out.write(f' CSMcand L{ln} rows={len(rows)} hdr={rows[:2]}\n')
            for r in rows:
                if r[0].startswith('1. 기초') or r[0].startswith('9.') or '최초 인식한 계약의 효과' in r[0]: out.write(f'      {r}\n')
        if any(l=='보험손익' for l in labs) and any('당기순이익' in l for l in labs):
            out.write(f' STMT L{ln} rows={len(rows)} hdr={rows[:2]}\n')
        if any('제공된 서비스의 보험계약마진' in l for l in labs):
            out.write(f' CSMAMORT L{ln} rows={len(rows)} hdr={rows[:2]}\n')
            for r in rows:
                if '제공된 서비스의 보험계약마진' in r[0]: out.write(f'      {r}\n')
