# -*- coding: utf-8 -*-
"""
ILP leftovers (ticket 20261011T1000Z, task 3): the 2-4 / 4-6-2 합계 row of 메트라이프생명(KR0095) prints the 보험료배분접근법 column with one decimal (0.4 / 0.5 억원) and the stage-1 extractor
(`extract_insurance_liability_portfolio.py`, before the 2026-10-11 repair of its number token) cut the decimals off, so the master holds item 7 = 0.0 for 6 quarters
(2024.4Q = 0.3 and the 2024.1Q-3Q prior-year tables = 0.2 were read with the decimal-aware readers and are right).  Item 8 is the sum of items 1-7 and carries the same error.

Every cell is changed only when (a) it still holds the value found on 2026-10-11 (OLD-VALUE GUARD) and (b) the printed 합계 row is read again from the PDF right now and equals the expected
7 numbers (decimals included).  Nothing else is touched.  Backup first, byte-exact round trip required (CRLF, indent 2), only the listed rows change, and the same run records every
correction in the provenance file (new top-level list `value_corrections`: file, page, printed row, old -> new).

The FIX table below is the COMPLETE list found by the whole-master scan of the same ticket (data/disclosure/_meta/ilp_leftovers_20261011/u63_decimal_compare.py over every 2025.1Q-2026.2Q
cell that has a text layer; result in ilp_leftovers_runlog_20261011.md section 3).

Usage:  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/fix_20261011_ilp_decimal_truncation.py [--write]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

import pdfplumber

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
from _disclosure_pdf_paths import disclosure_pdfs  # noqa: E402

ILP = REPO / "insurance_liability_portfolio.json"
PROV = REPO / "insurance_liability_portfolio_provenance.json"
TICKET = "inbox/parser/20261011T1000Z__orchestrator__MULTI_2023.1Q-2026.2Q__ilp_leftovers_hana_attachments.md"
STAMP = datetime.now(timezone.utc).strftime("%Y%m%d")

# (code, quarter) -> expected printed 합계 row (7 numbers, 억원), the item-7 and item-8 values to write, the master's current values, and where it is printed (FY period, page)
FIX = {
    ("KR0095", "2025.1Q"): {"fy": "FY2025_Q1", "page": 7, "row": [108113, 3141, 22583, 75760, 368, 2030, 0.4], "old": {7: 0.0, 8: 211995.0}, "new": {7: 0.4, 8: 211995.4}},
    ("KR0095", "2025.2Q"): {"fy": "FY2025_Q2", "page": 8, "row": [108464, 3200, 21633, 82399, 391, 2409, 0.4], "old": {7: 0.0, 8: 218496.0}, "new": {7: 0.4, 8: 218496.4}},
    ("KR0095", "2025.3Q"): {"fy": "FY2025_Q3", "page": 7, "row": [113421, 3290, 21911, 89591, 411, 2833, 0.4], "old": {7: 0.0, 8: 231457.0}, "new": {7: 0.4, 8: 231457.4}},
    ("KR0095", "2025.4Q"): {"fy": "FY2025_Q4", "page": 24, "row": [109815, 3555, 22810, 98500, 472, 3271, 0.4], "old": {7: 0.0, 8: 238423.0}, "new": {7: 0.4, 8: 238423.4}},
    ("KR0095", "2026.1Q"): {"fy": "FY2026_Q1", "page": 7, "row": [105338, 3621, 25451, 104975, 493, 3542, 0.5], "old": {7: 0.0, 8: 243420.0}, "new": {7: 0.5, 8: 243420.5}},
    ("KR0095", "2026.2Q"): {"fy": "FY2026_Q2", "page": 8, "row": [115032, 3774, 23832, 143844, 597, 5366, 0.5], "old": {7: 0.0, 8: 292445.0}, "new": {7: 0.5, 8: 292445.5}},
}


def printed_row(code: str, fy: str, page: int) -> tuple[list | None, str, str]:
    """re-read the 합계 row of the given page: -> (numbers, line, file name)"""
    pdfs = disclosure_pdfs(fy, code)
    if not pdfs:
        return None, "", ""
    p = pdfs[0]
    with pdfplumber.open(str(p)) as pdf:
        txt = pdf.pages[page - 1].extract_text() or ""
    for ln in txt.split("\n"):
        if re.match(r"^\s*합\s*계\s", ln):
            toks = re.findall(r"-?\d[\d,]*(?:\.\d+)?", ln)
            if len(toks) == 7:
                return [float(t.replace(",", "")) for t in toks], ln.strip(), p.name
    return None, "", p.name


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()
    raw0 = ILP.read_bytes()
    txt = raw0.decode("utf-8")
    crlf = "\r\n" in txt
    rows = json.loads(txt)
    dump = lambda r: (json.dumps(r, indent=2, ensure_ascii=False).replace("\n", "\r\n") if crlf else json.dumps(r, indent=2, ensure_ascii=False))
    if dump(rows) != txt:
        raise SystemExit("abort: file does not round-trip byte-for-byte")
    idx = {(r["원보험사코드"], r["공시분기"], r["항목번호"]): i for i, r in enumerate(rows)}
    plan, evid = [], []
    for (code, q), f in sorted(FIX.items()):
        nums, line, fname = printed_row(code, f["fy"], f["page"])
        if nums is None or any(abs(a - b) > 1e-9 for a, b in zip(nums, f["row"])):
            raise SystemExit(f"abort: the printed 합계 row of {code} {q} ({f['fy']} p{f['page']}) is {nums}, expected {f['row']}")
        sums = [rows[idx[(code, q, n)]]["값"] for n in range(1, 7)]
        if any(abs(a - b) > 1e-9 for a, b in zip(sums, f["row"][:6])):
            raise SystemExit(f"abort: items 1-6 of {code} {q} differ from the printed row: {sums} vs {f['row'][:6]}")
        if abs(sum(f["row"]) - f["new"][8]) > 1e-6:
            raise SystemExit(f"abort: new item 8 {f['new'][8]} is not the sum of the printed row {sum(f['row'])}")
        for n in (7, 8):
            cur = rows[idx[(code, q, n)]]["값"]
            if cur == f["new"][n] and cur != f["old"][n]:
                print(f"already fixed: {code} {q} item {n} = {cur}")
                continue
            if float(cur) != f["old"][n]:
                raise SystemExit(f"abort (old-value guard): {code} {q} item {n} holds {cur}, expected {f['old'][n]}")
            plan.append(((code, q, n), f["old"][n], f["new"][n]))
        evid.append({"company_code": code, "quarter": q, "items": {"7": {"old": f["old"][7], "new": f["new"][7]}, "8": {"old": f["old"][8], "new": f["new"][8]}},
                     "source_file": f"data/disclosure/{f['fy']}/raw/{fname}", "page": f["page"], "printed_row": line, "printed_numbers": f["row"],
                     "reason": "stage-1 extractor cut the decimal of the 보험료배분접근법 column (0.4/0.5억); item 8 = sum of items 1-7", "ticket": TICKET})
    print(f"{len(plan)} cell(s) to change:")
    for (code, q, n), old, new in plan:
        print(f"  {code} {q} item {n}: {old} -> {new}")
    if not args.write or not plan:
        print("dry run" if not args.write else "nothing to do")
        return 0
    backup = REPO / "data" / "_derived" / f"ilp_backup_{STAMP}_pre_decimal_truncation.json"
    k = 2
    while backup.exists():
        backup = REPO / "data" / "_derived" / f"ilp_backup_{STAMP}_pre_decimal_truncation_{k}.json"
        k += 1
    shutil.copyfile(ILP, backup)
    if hashlib.sha256(backup.read_bytes()).hexdigest() != hashlib.sha256(raw0).hexdigest():
        raise SystemExit("abort: backup mismatch")
    new_rows = json.loads(txt)
    for (code, q, n), old, new in plan:
        new_rows[idx[(code, q, n)]]["값"] = new
    if ILP.read_bytes() != raw0:
        raise SystemExit("abort: file changed while preparing the fix")
    tmp = ILP.with_name(ILP.name + ".tmp")
    tmp.write_bytes(dump(new_rows).encode("utf-8"))
    os.replace(tmp, ILP)
    after = json.loads(ILP.read_text(encoding="utf-8"))
    changed = [i for i, (a, b) in enumerate(zip(rows, after)) if a != b]
    assert len(after) == len(rows) and len(changed) == len(plan), (len(changed), len(plan))
    # ---- provenance: new top-level list `value_corrections` (guarded, backed up) ----
    praw = PROV.read_bytes().decode("utf-8")
    prov = json.loads(praw)
    if json.dumps(prov, ensure_ascii=False, indent=1) + "\n" != praw:
        raise SystemExit(f"values are written; the provenance does not round-trip -- record the corrections by hand (backup of the master: {backup.name})")
    pback = REPO / "data" / "_derived" / f"ilp_provenance_backup_{STAMP}_pre_decimal_truncation.json"
    j = 2
    while pback.exists():
        pback = REPO / "data" / "_derived" / f"ilp_provenance_backup_{STAMP}_pre_decimal_truncation_{j}.json"
        j += 1
    shutil.copyfile(PROV, pback)
    prov.setdefault("value_corrections", [])
    prov["value_corrections"] = prov["value_corrections"] + [dict(e, at=datetime.now(timezone.utc).strftime("%Y%m%dT%H%MZ"), emitted_by="scripts/fix_20261011_ilp_decimal_truncation.py") for e in evid]
    tmp = PROV.with_name(PROV.name + ".tmp")
    tmp.write_bytes((json.dumps(prov, ensure_ascii=False, indent=1) + "\n").encode("utf-8"))
    os.replace(tmp, PROV)
    print(f"wrote {ILP.name}; backup {backup.name}; {len(changed)} rows changed, all others identical; provenance +{len(evid)} value_corrections (backup {pback.name})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
