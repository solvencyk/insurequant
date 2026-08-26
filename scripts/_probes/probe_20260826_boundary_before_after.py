#!/usr/bin/env python3
"""경계 규칙 전/후 전수 대조 (ENG 경로 포함, 실제 함수 대 옛 함수)."""
import sys, re
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "scripts"))
sys.stdout.reconfigure(encoding="utf-8")
from collections import Counter
from scripts.pl_breakdown.common import (_ofs_line_boundary, _plain, _CFS_HEAD_RE,
                                         _OFS_HEAD_RE, _OFS_TITLE_RE, _SOURCELINE_CAP)

def old_boundary(path):
    """표-존재 조건이 없던 판(28f883b)."""
    cfs = kr_cfs = False
    kr_hit = None
    with open(path, encoding="utf-8", errors="replace") as f:
        for i, line in enumerate(f, 1):
            if 'ATOC="Y"' in line and "financial statements" in line.lower():
                m = _OFS_TITLE_RE.search(line)
                if m:
                    eng = m.group(1).lower()
                    if "notes" not in eng:
                        if "consolidated" in eng:
                            cfs = True
                        elif ("separate" in eng or "non-consolidated" in eng) and cfs:
                            return i
            if kr_hit is None and "재무" in line:
                t = _plain(line)
                if _CFS_HEAD_RE.match(t):
                    kr_cfs = True
                elif kr_cfs and _OFS_HEAD_RE.match(t):
                    kr_hit = i
    return kr_hit

rows, n = [], 0
for d in sorted((ROOT / "data" / "dart").glob("FY*_Q*")):
    for rd in sorted(d.glob("raw/KR*")):
        for x in sorted(rd.glob("*.xml")):
            if "_007" in x.name:
                continue
            n += 1
            o, c = old_boundary(x), _ofs_line_boundary(x)
            if o != c:
                rows.append((d.name, rd.name.split("_")[0], o, c))
print(f"본문 XML {n}개 · 경계 변경 {len(rows)}개")
print("회사별:", dict(sorted(Counter(r[1] for r in rows).items())))
lost = [r for r in rows if r[3] is None]
tiny = [r for r in rows if r[2] is not None and r[2] < 1000]
print(f"  목차(<1000줄)를 물던 것: {len(tiny)}   새로 None 이 된 것: {len(lost)}")
for r in lost[:12]:
    print("   LOST", r)
print()
print("샘플 20:")
for r in rows[:20]:
    print(f"   {r[0]:10s} {r[1]} {str(r[2]):>7s} -> {str(r[3]):>7s}")
