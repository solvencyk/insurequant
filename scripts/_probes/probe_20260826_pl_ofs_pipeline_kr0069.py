#!/usr/bin/env python3
"""② 실작업: 개선된 basis 판정으로 PL 파이프라인을 그대로 돌려 별도값을 뽑는다.

바꾼 것 두 가지 (probe 안에서 monkeypatch, 트리 코드 미변경):
  (A) 별도 섹션 경계 탐지를 ENG 속성 대신 '텍스트'로 — <TITLE> 태그가 없는 HTML 템플릿
      (2026.2Q)도 "4-1. 재무상태표" 로 잡힌다.
  (B) 경계가 65,535 를 넘으면(lxml HTMLParser sourceline 포화) 파일을 물리적으로 잘라
      연결/별도 각각 추출한다 — line_no 비교가 성립하지 않는 구간.
"""
import sys, re, os, tempfile, json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "scripts"))
sys.stdout.reconfigure(encoding="utf-8")
import build_pl_breakdown as BP
from scripts.pl_breakdown.common import _ofs_line_boundary

SAT = 65535
STRIP = lambda s: re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", s)).strip()
CFS_HEAD = re.compile(r"^\d+(-\d+)?\.\s*연결\s*재무(제표|상태표)")
OFS_HEAD = re.compile(r"^\d+(-\d+)?\.\s*재무(제표|상태표)\s*$")
_BCACHE = {}

def boundary(path):
    path = str(path)
    if path in _BCACHE:
        return _BCACHE[path]
    b = _ofs_line_boundary(path)
    if b is None:
        cfs = False
        try:
            with open(path, encoding="utf-8", errors="replace") as f:
                for i, line in enumerate(f, 1):
                    if "재무" not in line:
                        continue
                    t = STRIP(line)
                    if CFS_HEAD.match(t):
                        cfs = True
                    elif cfs and OFS_HEAD.match(t):
                        b = i
                        break
        except OSError:
            b = None
    _BCACHE[path] = b
    return b

_orig_iter = BP._iter_tables_with_context

def _iter2(path):
    b = boundary(path)
    if b is None or b <= SAT:
        for t in _orig_iter(Path(path)):
            t._pre = None
            yield t
        return
    lines = Path(path).read_text(encoding="utf-8", errors="replace").splitlines(keepends=True)
    for part, basis in ((lines[:b - 1], "CFS"), (lines[b - 1:], "OFS")):
        fh = tempfile.NamedTemporaryFile("w", suffix=".xml", delete=False, encoding="utf-8")
        fh.write("".join(part)); fh.close()
        try:
            for t in _orig_iter(Path(fh.name)):
                t._pre = basis
                yield t
        finally:
            os.unlink(fh.name)

def _tag2(tables, path):
    name = os.path.basename(str(path))
    if name.endswith("_00760.xml"):
        for t in tables: t._basis = "OFS"
        return tables
    if name.endswith("_00761.xml"):
        for t in tables: t._basis = "CFS"
        return tables
    b = boundary(path)
    for t in tables:
        pre = getattr(t, "_pre", None)
        t._basis = pre if pre else (None if b is None else ("OFS" if t.line_no >= b else "CFS"))
    return tables

BP._iter_tables_with_context = _iter2
BP._tag_basis = _tag2

code, name = "KR0069", "삼성생명"
pl = {(r["공시분기"], r["항목번호"]): r["값"]
      for r in json.loads((ROOT / "PL_breakdown.json").read_text(encoding="utf-8"))
      if r["원보험사코드"] == code}
wf = {r["공시분기"]: r["값"] for r in json.loads((ROOT / "CSM_waterfall.json").read_text(encoding="utf-8"))
      if r["원보험사코드"] == code and r["항목번호"] == 5}
OPEN = {"2024.1Q", "2024.2Q", "2024.3Q", "2025.2Q", "2026.2Q"}

filings = BP.discover_filings()
print(f"{'분기':9s} {'잔차':5s} {'경계':>8s} {'현재PL':>10s} {'재추출':>10s} {'워터폴':>10s} {'재추출-워터폴':>12s}")
for q in sorted(filings[code], key=BP._quarter_sort_key):
    dirs = filings[code][q]
    bs = [boundary(x) for d in dirs for x in BP._xmls_in(d) if "_007" not in os.path.basename(x)]
    t1, t2 = BP.parse_filing(dirs, True, code=code, name=name, quarter=q)
    new4 = (t2 or {}).get(4)
    cur, w = pl.get((q, 4)), wf.get(q)
    f = lambda v: "-" if v is None else f"{v/100:,.2f}"
    d = "-" if (new4 is None or w is None) else f"{new4/100 - abs(w):+,.2f}"
    print(f"{q:9s} {'OPEN' if q in OPEN else '  ·':5s} {str(bs[0] if bs else None):>8s} "
          f"{f(cur):>10s} {f(new4):>10s} {'-' if w is None else f'{abs(w):,.2f}':>10s} {d:>12s}")
