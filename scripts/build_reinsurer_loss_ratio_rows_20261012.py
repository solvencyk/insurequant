#!/usr/bin/env python3
"""Stage 2 (ticket 20261012T0100Z): assemble the reinsurer (KR1101~KR1107) table-B long rows + table-A rows.

Sources, per (company, annual filing):
  * generic extractor result (data/_derived/reinsurer_loss_ratio_20261012/ext_B.json) where its own identity checks passed
        KR1103 / KR1104 / KR1105 (all), KR1106 FY2025, KR1107 FY2024
  * ruled-grid reader (extract_loss_ratio_reinsurer_grid_20261012.py) for KR1101 / KR1102 / KR1107 FY2025
  * KR1106 FY2024: extractor page parse with the year forced (the caption row is printed under the heading) + segment by heading order
Writes only to data/_derived/reinsurer_loss_ratio_20261012/ (reinsurer_B_rows.json, reinsurer_A_rows.json, assemble_log.txt).
Run: C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/build_reinsurer_loss_ratio_rows_20261012.py
"""
from __future__ import annotations

import io
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import extract_loss_ratio as X  # noqa: E402
import extract_loss_ratio_reinsurer_grid_20261012 as G  # noqa: E402
import fitz  # noqa: E402

if sys.stdout.encoding is None or "utf" not in sys.stdout.encoding.lower():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

OUT = ROOT / "data" / "_derived" / "reinsurer_loss_ratio_20261012"
EXT_B = OUT / "ext_B.json"
EXT_A = OUT / "ext_A.json"

EXTRACTOR_B = {("KR1103", "2024.4Q"), ("KR1103", "2025.4Q"), ("KR1104", "2024.4Q"), ("KR1104", "2025.4Q"),
               ("KR1105", "2024.4Q"), ("KR1105", "2025.4Q"), ("KR1106", "2025.4Q"), ("KR1107", "2024.4Q")}
GRID_B = {("KR1101", "2024.4Q"), ("KR1101", "2025.4Q"), ("KR1102", "2024.4Q"), ("KR1102", "2025.4Q"), ("KR1107", "2025.4Q")}
LOG: list[str] = []


def log(s: str) -> None:
    LOG.append(s)
    print(s)


def runs_of(pages):
    pages = sorted(set(pages))
    runs, cur = [], []
    for p in pages:
        if cur and p == cur[-1] + 1:
            cur.append(p)
        else:
            if cur:
                runs.append(cur)
            cur = [p]
    if cur:
        runs.append(cur)
    return runs


def grid_rows(code, q, path, meta, idx_all):
    rel = X.rel(path)
    h = idx_all[rel]["hits"]
    cand = sorted(set(h["B_head"]) | set(h["B_lab"]))
    doc = fitz.open(str(path))
    npg = doc.page_count
    rows = []
    for run in runs_of(cand):
        nxt = run[-1] + 1
        if nxt <= npg and G.page_grids(doc[nxt - 1]):
            run.append(nxt)
        st = G.read_pdf(str(path), run)
        if not st["rows"]:
            log(f"   {code} {q} pages {run[0]}-{run[-1]}: no grid rows (nogrid {st.get('nogrid')})")
            continue
        groups = G.resolve_groups(st)
        long_, notes = G.to_long(groups, X.meta_row(code, q, meta), rel, npg, year_default=int(q[:4]))
        for n in notes:
            log(f"   {code} {q} note: {n}")
        for r in long_:
            r.pop("bad", None)
            r["판독"] = "ruled-grid"
        rows += long_
    return rows


def kr1106_fy2024(path, meta):
    """KR1106 FY2024 p15: table 2 (4-6-4) has no year caption row and two heading segments inside the table."""
    rel = X.rel(path)
    doc = fitz.open(str(path))
    secs = X.extract_B_sections(doc, [15])
    rows: list[dict] = []
    for sec in secs:
        for b in sec["blocks"]:
            b["year"] = 2024
            rr, bad = X.block_rows(b, X.meta_row("KR1106", "2024.4Q", meta))
            for r in rr:
                r["기준연도"] = 2024
            rows += rr
            if bad:
                log(f"   KR1106 FY2024 bad cells {bad[:4]}")
    # rows come out in group order: a new group starts when (구분, 포트폴리오) changes; the 2nd 합계 group starts the 장기손해보험 segment
    seg_now, tot_seen, last_key = "생명보험", 0, None
    out = []
    for r in rows:
        # the next segment's heading `장기손해보험` (printed right under the last 생명보험 row) is glued onto that row's label by the word reader
        for lk in ("포트폴리오_원문", "포트폴리오"):
            if r.get(lk) and r[lk].endswith("장기손해보험") and r[lk] != "장기손해보험":
                r[lk] = r[lk][: -len("장기손해보험")]
        k = (r["구분"], r["포트폴리오"])
        if k != last_key:
            if k[0] == "합계":
                tot_seen += 1
                seg_now = "생명보험" if tot_seen == 1 else "장기손해보험"
            last_key = k
        r["사업구분"] = seg_now
        r["출처"] = {"file": rel, "page": 15}
        r["추출방식"] = "text"
        r["원천위치"] = "본문"
        r["판독"] = "coordinate(year forced 2024)"
        r["플래그"] = ["year_forced(캡션 <2024년> 은 p15 에 있으나 일반 추출기가 읽지 못해 연도를 직접 지정)"]
        out.append(r)
    return out


def check_rows(rows, tag):
    keyset = sorted({(r["기준연도"], r.get("사업구분")) for r in rows}, key=str)
    res = {}
    for yr, seg in keyset:
        sub = [dict(r, 부문=seg) for r in rows if r["기준연도"] == yr and r.get("사업구분") == seg]
        st = X.check_B_rows(sub)
        res[(yr, seg)] = st
        log(f"   {tag} year {yr} seg {seg}: rows {len(sub)} ratio {st['ratio_checked']}/fail {st['ratio_fail']} total {st['total_checked']}/fail {st['total_fail']} dup {st['dup_keys']} miss {st['missing_cols']} nonstd {st['nonstd'][:5]}")
        for f in st["fails"][:3]:
            log(f"      {f}")
    return res


def main():
    meta = X.load_company_meta()
    pdfs = X.discover_pdfs(meta)
    idx_all = json.loads((ROOT / "data/_derived/_probe_loss_ratio_pageindex.json").read_text(encoding="utf-8"))
    ext_b = json.loads(EXT_B.read_text(encoding="utf-8"))
    allrows: list[dict] = []
    for code, q in sorted(EXTRACTOR_B):
        sub = [dict(r, 판독="generic-extractor") for r in ext_b if r["원보험사코드"] == code and r["공시분기"] == q]
        for r in sub:      # the saved rows lost the private printed-decimals field; repr decimals are never finer than printed -> checks are no tighter than the extractor's own
            v = r.get("값")
            r["_dec"] = 0 if v is None else (len(repr(float(v)).split(".")[1].rstrip("0")) if "." in repr(float(v)) else 0)
        log(f"== {code} {q} extractor rows {len(sub)}")
        check_rows(sub, "ext")
        allrows += sub
    for code, q in sorted(GRID_B):
        path = pdfs[(q, code)]
        log(f"== {code} {q} grid {X.rel(path)}")
        sub = grid_rows(code, q, path, meta, idx_all)
        check_rows(sub, "grid")
        allrows += sub
    path = pdfs[("2024.4Q", "KR1106")]
    log(f"== KR1106 2024.4Q forced-year {X.rel(path)}")
    sub = kr1106_fy2024(path, meta)
    check_rows(sub, "kr1106")
    allrows += sub
    for r in allrows:
        for k in [k for k in r if k.startswith("_")]:
            r.pop(k)
        r.pop("bad", None)
    (OUT / "reinsurer_B_rows.json").write_text(json.dumps(allrows, ensure_ascii=False, indent=1), encoding="utf-8")
    (OUT / "assemble_log.txt").write_text("\n".join(LOG), encoding="utf-8")
    cnt = defaultdict(int)
    for r in allrows:
        cnt[(r["원보험사코드"], r["공시분기"], r["기준연도"])] += 1
    for k, v in sorted(cnt.items()):
        print(k, v)
    print("total", len(allrows))


if __name__ == "__main__":
    main()
