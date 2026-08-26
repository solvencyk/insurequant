#!/usr/bin/env python3
"""② 후속 실작업: 삼성생명 잔차 5분기를 별도(OFS)로 재추출한다.

경계 탐지를 텍스트 기반으로 바꾸고(TITLE 태그 유무 무관), 경계가 65,535 를 넘어
lxml HTMLParser sourceline 이 포화되는 필링은 파일을 물리적으로 잘라 tail 만 추출한다.
read-only: 마스터/빌더 미변경, 임시파일은 scratch 에만 쓴다.
"""
import sys, re, tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "scripts"))
sys.stdout.reconfigure(encoding="utf-8")
from src.ifrs17.csm_extractor import _iter_tables_with_context
from scripts.pl_breakdown.common import _tag_basis
from scripts.pl_breakdown.companies import extract_tier2_samsung_life
import json

SAT = 65535                      # lxml HTMLParser sourceline 포화점
STRIP = lambda s: re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", s)).strip()
CFS_HEAD = re.compile(r"^\d+(-\d+)?\.\s*연결\s*재무(제표|상태표)")
OFS_HEAD = re.compile(r"^\d+(-\d+)?\.\s*재무(제표|상태표)\s*$")

def boundary(path):
    cfs = False
    with open(path, encoding="utf-8", errors="replace") as f:
        for i, line in enumerate(f, 1):
            t = STRIP(line)
            if not t or "재무" not in t:
                continue
            if CFS_HEAD.match(t):
                cfs = True
            elif cfs and OFS_HEAD.match(t):
                return i
    return None

def ofs_tables(path):
    """별도 섹션 테이블만 반환. 경계가 포화점을 넘으면 파일을 잘라서 추출."""
    b = boundary(path)
    if b is None:
        return None, None, "no-boundary"
    if b <= SAT:
        ts = _tag_basis(list(_iter_tables_with_context(Path(path))), path)
        return [t for t in ts if getattr(t, "_basis", None) == "OFS"], b, "line_no"
    lines = Path(path).read_text(encoding="utf-8", errors="replace").splitlines(keepends=True)
    with tempfile.NamedTemporaryFile("w", suffix=".xml", delete=False, encoding="utf-8") as fh:
        fh.write("".join(lines[b - 1:]))
        tmp = fh.name
    ts = list(_iter_tables_with_context(Path(tmp)))
    for t in ts:
        t._basis = "OFS"
    Path(tmp).unlink(missing_ok=True)
    return ts, b, "split"

QS = {"2024.1Q": "FY2024_Q1", "2024.2Q": "FY2024_Q2", "2024.3Q": "FY2024_Q3",
      "2025.2Q": "FY2025_Q2", "2026.2Q": "FY2026_Q2",
      "2024.4Q": "FY2024_Q4", "2025.1Q": "FY2025_Q1", "2025.3Q": "FY2025_Q3",
      "2025.4Q": "FY2025_Q4", "2026.1Q": "FY2026_Q1",
      "2023.1Q": "FY2023_Q1", "2023.2Q": "FY2023_Q2", "2023.3Q": "FY2023_Q3", "2023.4Q": "FY2023_Q4"}
OPEN = {"2024.1Q", "2024.2Q", "2024.3Q", "2025.2Q", "2026.2Q"}

pl = {(r["공시분기"], r["항목번호"]): r["값"]
      for r in json.loads((ROOT / "PL_breakdown.json").read_text(encoding="utf-8"))
      if r["원보험사코드"] == "KR0069"}
wf = {r["공시분기"]: r["값"] for r in json.loads((ROOT / "CSM_waterfall.json").read_text(encoding="utf-8"))
      if r["원보험사코드"] == "KR0069" and r["항목번호"] == 5}

print(f"{'분기':9s} {'잔차':5s} {'경계':>8s} {'경로':>8s} {'현재PL(억)':>11s} {'별도재추출(억)':>13s} "
      f"{'워터폴(억)':>11s} {'재추출-워터폴':>12s}")
for q in sorted(QS, key=lambda x: (x[:4], x[5])):
    dirs = sorted((ROOT / "data" / "dart" / QS[q] / "raw").glob("KR0069_*"))
    if not dirs:
        print(f"{q:9s} raw 없음"); continue
    xs = [x for x in sorted(dirs[0].glob("*.xml")) if "_00761" not in x.name]
    main = [x for x in xs if "_007" not in x.name]
    pool, b, how = ([], None, "-")
    for x in (main or xs):
        t, bb, hh = ofs_tables(x)
        if t:
            pool += t; b, how = bb, hh
    for x in xs:                                     # 별도 첨부(_00760)가 있으면 합친다
        if x.name.endswith("_00760.xml"):
            t = _tag_basis(list(_iter_tables_with_context(x)), x)
            pool += t; how += "+00760"
    out = extract_tier2_samsung_life(pool) if pool else {}
    new4 = out.get(4)
    cur = pl.get((q, 4))
    w = wf.get(q)
    f = lambda v: "-" if v is None else f"{v/100:,.2f}"
    d = "-" if (new4 is None or w is None) else f"{new4/100 - abs(w):+,.2f}"
    print(f"{q:9s} {'OPEN' if q in OPEN else '  ·':5s} {str(b):>8s} {how:>8s} {f(cur):>11s} "
          f"{f(new4):>13s} {'-' if w is None else f'{abs(w):,.2f}':>11s} {d:>12s}")
