#!/usr/bin/env python3
"""개선된 basis 판정의 전수 영향범위 — 전 회사 × 전 분기, 항목별 diff.

트리 코드 미변경(monkeypatch). 산출: scratch 의 JSON + 표준출력 요약.
  (A) 별도 경계 탐지를 ENG 속성 -> 텍스트 기반으로 확장
  (B) 경계 > 65,535 (lxml HTMLParser sourceline 포화) 면 파일을 잘라 각각 추출
"""
import sys, re, os, json, tempfile, time
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "scripts"))
sys.stdout.reconfigure(encoding="utf-8")
import build_pl_breakdown as BP
from scripts.pl_breakdown.common import _ofs_line_boundary

OUT = Path(sys.argv[1])
SAT = 65535
STRIP = lambda s: re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", s)).strip()
CFS_HEAD = re.compile(r"^\d+(-\d+)?\.\s*연결\s*재무(제표|상태표)")
OFS_HEAD = re.compile(r"^\d+(-\d+)?\.\s*재무(제표|상태표)\s*$")
_BC = {}

def boundary(path):
    p = str(path)
    if p in _BC:
        return _BC[p]
    b = _ofs_line_boundary(p)
    if b is None:
        cfs = False
        try:
            with open(p, encoding="utf-8", errors="replace") as f:
                for i, line in enumerate(f, 1):
                    if "재무" not in line:
                        continue
                    t = STRIP(line)
                    if CFS_HEAD.match(t):
                        cfs = True
                    elif cfs and OFS_HEAD.match(t):
                        b = i; break
        except OSError:
            b = None
    _BC[p] = b
    return b

_orig_iter = BP._iter_tables_with_context
_orig_tag = BP._tag_basis

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

MODE = sys.argv[2] if len(sys.argv) > 2 else "new"
if MODE == "new":
    BP._iter_tables_with_context = _iter2
    BP._tag_basis = _tag2

uni = BP.load_universe()
filings = BP.discover_filings()
res, t0, n = {}, time.time(), 0
for code in sorted(filings):
    name, life_flag = uni.get(code, (code, None))
    is_life = (life_flag == "생명보험")
    for q in sorted(filings[code], key=BP._quarter_sort_key):
        try:
            t1h, t2 = BP.parse_filing(filings[code][q], is_life, code=code, name=name, quarter=q)
            t1a = BP._fs_tier1(name, q, code)
            t1 = t1a if t1a else t1h
            if t1 is None and t2 is None:
                continue
            v = BP.assemble(t1, t2, is_life)
            res[f"{code}|{q}"] = {str(i): v.get(i) for i in range(1, 25)}
        except Exception as e:
            res[f"{code}|{q}"] = {"_error": f"{type(e).__name__}: {e}"}
        n += 1
        if n % 60 == 0:
            print(f"  ... {n} buckets, {time.time()-t0:.0f}s", flush=True)
OUT.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
print(f"{MODE}: {len(res)} buckets -> {OUT}  ({time.time()-t0:.0f}s)")
