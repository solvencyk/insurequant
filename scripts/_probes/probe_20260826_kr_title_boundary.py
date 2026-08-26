#!/usr/bin/env python3
"""한글 ATOC 제목 기반 별도(OFS) 경계 후보를 전 분기에서 실측."""
import sys, re
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "scripts"))
sys.stdout.reconfigure(encoding="utf-8")
from scripts.pl_breakdown.common import _ofs_line_boundary

TITLE = re.compile(r'<TITLE\s+ATOC="Y"[^>]*>([^<]{0,80})</TITLE>')

def kr_boundary(path):
    """연결재무제표 제목을 먼저 본 뒤 나오는 '재무제표'(연결 아님) 제목 줄."""
    cfs = False
    with open(path, encoding="utf-8", errors="replace") as f:
        for i, line in enumerate(f, 1):
            for m in TITLE.finditer(line):
                t = re.sub(r"\s+", "", m.group(1))
                if "주석" in t:
                    continue
                if "연결재무제표" in t:
                    cfs = True
                elif cfs and re.search(r"\d\.재무제표$", t):
                    return i, t
    return None, None

def titles(path):
    out = []
    with open(path, encoding="utf-8", errors="replace") as f:
        for i, line in enumerate(f, 1):
            for m in TITLE.finditer(line):
                t = m.group(1).strip()
                if "재무제표" in t or "financial" in t.lower():
                    out.append((i, t))
    return out

code = sys.argv[1] if len(sys.argv) > 1 else "KR0069"
print(f"{'분기':9s} {'파일':30s} {'줄수':>9s} {'ENG경계':>8s} {'한글경계':>9s} {'>65535':>7s}")
for d in sorted((ROOT / "data" / "dart").glob("FY*_Q*")):
    for rd in sorted(d.glob(f"raw/{code}_*")):
        for x in sorted(rd.glob("*.xml")):
            if "_007" in x.name:
                continue
            n = sum(1 for _ in open(x, encoding="utf-8", errors="replace"))
            e = _ofs_line_boundary(x)
            k, lab = kr_boundary(x)
            q = d.name.replace("FY", "").replace("_Q", ".") + "Q"
            print(f"{q:9s} {x.name:30s} {n:>9,} {str(e):>8s} {str(k):>9s} "
                  f"{'YES' if (k or e or 0) > 65535 else '-':>7s}  {lab or ''}")
            if k is None and e is None:
                for i, t in titles(x)[:8]:
                    print(f"          └ L{i:>7,}  {t}")
