#!/usr/bin/env python3
"""③ 검증: 한글 제목 경계가 목차를 먼저 무는지 — 본문 XML 전수 census.

현행 경계 vs '연결 제목과 별도 제목 사이에 <TABLE> 이 1개 이상' 규칙 경계를 대조한다.
"""
import sys, re
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "scripts"))
sys.stdout.reconfigure(encoding="utf-8")
from scripts.pl_breakdown.common import (_ofs_line_boundary, _plain, _CFS_HEAD_RE,
                                         _OFS_HEAD_RE, _OFS_TITLE_RE, _SOURCELINE_CAP)

def boundary_with_table_rule(path):
    """연결 제목 이후 <TABLE> 을 1개 이상 본 뒤에 나오는 별도 제목만 인정."""
    cfs, tables_since_cfs, hit = False, 0, None
    with open(path, encoding="utf-8", errors="replace") as f:
        for i, line in enumerate(f, 1):
            low = line.lower()
            if "<table" in low:
                tables_since_cfs += line.count("<table") + line.count("<TABLE")
            if "재무" not in line:
                continue
            t = _plain(line)
            if _CFS_HEAD_RE.match(t):
                cfs, tables_since_cfs = True, 0
            elif cfs and tables_since_cfs >= 1 and _OFS_HEAD_RE.match(t):
                hit = i
                break
    return hit

rows, n_body = [], 0
for d in sorted((ROOT / "data" / "dart").glob("FY*_Q*")):
    for rd in sorted(d.glob("raw/KR*")):
        for x in sorted(rd.glob("*.xml")):
            if "_007" in x.name:
                continue
            n_body += 1
            cur = _ofs_line_boundary(x)
            new = boundary_with_table_rule(x)
            if cur != new:
                rows.append((d.name, rd.name.split("_")[0], x.name, cur, new))
print(f"본문 XML {n_body}개 · 경계가 달라지는 것 {len(rows)}개 ({100*len(rows)/max(n_body,1):.0f}%)")
from collections import Counter
print("회사별:", dict(sorted(Counter(r[1] for r in rows).items())))
print("분기별:", dict(sorted(Counter(r[0] for r in rows).items())))
print()
for r in rows[:25]:
    print(f"  {r[0]:10s} {r[1]} {r[2][:22]:22s} 현행={str(r[3]):>7s} -> 표규칙={str(r[4]):>7s}")
