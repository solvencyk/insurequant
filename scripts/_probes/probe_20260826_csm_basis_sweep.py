#!/usr/bin/env python3
"""CSM 워터폴 쪽 basis 전수 census — 본문에서 별도(OFS) 섹션만 써서 재추출하고 마스터와 diff.

PL 과 같은 두 수정을 CSM 빌더의 blocks_for_dir 에 적용(monkeypatch, 트리 미변경):
  (A) 별도 경계 = ENG 속성 OR 텍스트 제목
  (B) 경계 > 65,535 면 파일을 잘라서 tail 만 추출 (lxml HTMLParser sourceline 포화 구간)
OFS 블록이 하나도 안 나오면 기존 pool 그대로(커버리지 무손실).
"""
import sys, re, os, json, time, tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "scripts"))
sys.stdout.reconfigure(encoding="utf-8")
import build_csm_waterfall_master as B
from src.ifrs17.measurement_extractor import extract_measurement_tables, to_jsonable
from viz_build_csm_waterfall import normalize_block_header, deduplicate
from scripts.pl_breakdown.common import _ofs_line_boundary

OUT = Path(sys.argv[1])
MODE = sys.argv[2] if len(sys.argv) > 2 else "new"
SAT = 65535
STRIP = lambda s: re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", s)).strip()
CFS_HEAD = re.compile(r"^\d+(-\d+)?\.\s*연결\s*재무(제표|상태표)")
OFS_HEAD = re.compile(r"^\d+(-\d+)?\.\s*재무(제표|상태표)\s*$")
_BC = {}

def boundary(p):
    p = str(p)
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

def _tables_ofs(x, name):
    """(tables, used_ofs) — 별도 섹션 테이블만. 경계 못 찾으면 전체."""
    b = boundary(x)
    if b is None:
        return list(extract_measurement_tables(x, company_name=name)), False
    if b <= SAT:
        ts = [t for t in extract_measurement_tables(x, company_name=name) if t.line_no >= b]
        return (ts, True) if ts else (list(extract_measurement_tables(x, company_name=name)), False)
    lines = Path(x).read_text(encoding="utf-8", errors="replace").splitlines(keepends=True)
    fh = tempfile.NamedTemporaryFile("w", suffix=".xml", delete=False, encoding="utf-8")
    fh.write("".join(lines[b - 1:])); fh.close()
    try:
        ts = list(extract_measurement_tables(Path(fh.name), company_name=name))
    finally:
        os.unlink(fh.name)
    return (ts, True) if ts else (list(extract_measurement_tables(x, company_name=name)), False)

_orig_blocks = B.blocks_for_dir

def blocks2(rd, name):
    xmls = {}
    for x in list(rd.glob("*.xml")) + list(rd.glob("xml/*.xml")) + list(rd.glob("extracted/*.xml")):
        if x.name.endswith("_00761.xml"):
            continue
        xmls.setdefault(x.name, x)
    tables = []
    for x in sorted(xmls.values()):
        try:
            ts, _used = (_tables_ofs(x, name) if "_007" not in x.name
                         else (list(extract_measurement_tables(x, company_name=name)), True))
            for t in ts:
                jt = to_jsonable(t); jt["_src"] = x.name; tables.append(jt)
        except Exception:
            pass
    out = []
    for b in deduplicate(tables):
        nb = normalize_block_header(b)
        nb["_src"] = b.get("_src", "")
        nb["basis"] = B._block_basis(nb["_src"])
        out.append(nb)
    return out

if MODE == "new":
    B.blocks_for_dir = blocks2

res, t0, n = {}, time.time(), 0
for d in sorted((ROOT / "data" / "dart").glob("FY*_Q*")):
    q = d.name.replace("FY", "").replace("_Q", ".") + "Q"
    for rd in sorted(d.glob("raw/KR*")):
        m = re.match(r"(KR\d+)_(.+?)(?:_\d{14})?$", rd.name)
        if not m:
            continue
        code, name = m.group(1), m.group(2)
        try:
            wf, src = B.waterfall_for_dir(rd, name)
            res[f"{code}|{q}"] = {"wf": wf, "src": src}
        except Exception as e:
            res[f"{code}|{q}"] = {"error": f"{type(e).__name__}: {e}"}
        n += 1
        if n % 60 == 0:
            print(f"  ... {n} dirs, {time.time()-t0:.0f}s", flush=True)
OUT.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
print(f"{MODE}: {len(res)} dirs -> {OUT} ({time.time()-t0:.0f}s)")
