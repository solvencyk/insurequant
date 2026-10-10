# -*- coding: utf-8 -*-
"""
Ticket 20261011T0320Z stage 5: KR0003 롯데손해보험 item 9 (무·저해지상품 해지율 예외모형 사용여부).

Finding (2026-10-11, the seven 경영공시 PDFs 2024.4Q .. 2026.2Q read page by page): in EVERY filing the section 「무·저해지상품 해지율 예외모형 사용에 관한 사항」
(2-5 in the quarterly template, 4-6-6 in the year-end template) says that the company chose the exception model
(「예외모형을 선택하였으며, 원칙모형을 선택한 경우와 (재무정보) 비교내역은 다음과 같습니다」 / 「예외모형 선택에 대한 합리성 및 타당성을 입증하고 문서화하였습니다」) and prints the
예외모형 vs 원칙모형 comparison of the current period (the prior-year columns say 「해당사항 없음」).  The master precedent (item 9 = 1 at 2026.2Q) means exactly that, but the
extractor had left item 9 BLANK for the other quarters (its pattern only matched the 2026.2Q wording).  This script ADDS the missing rows (value 1) for
2024.4Q, 2025.1Q, 2025.2Q, 2025.3Q, 2025.4Q, 2026.1Q.  Existing rows are not touched (2026.2Q = 1 stays).

Guards: a key that already exists aborts (no overwrite); before writing every quarter is re-read from its PDF and the phrase must be found in the section's window, else abort;
backup first, byte-exact round trip, file rewritten in its own format (CRLF, indent 2).  Provenance: new list key item9_cells (additive).

Usage:  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/fix_20261011_ilp_kr0003_item9.py [--write]
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
import extract_insurance_liability_lic as lic  # noqa: E402
import load_ilp_backfill_pre2025 as L  # noqa: E402

CODE = "KR0003"
QUARTERS = {"2024.4Q": "FY2024_Q4", "2025.1Q": "FY2025_Q1", "2025.2Q": "FY2025_Q2", "2025.3Q": "FY2025_Q3", "2025.4Q": "FY2025_Q4", "2026.1Q": "FY2026_Q1"}
PHRASES = ("예외모형을선택하였", "예외모형선택에대한합리성및타당성을입증")
TICKET = "inbox/parser/20261011T0320Z__orchestrator__MULTI_2023.1Q-2026.2Q__ilp_remaining_backfill_lic23_reinsurers.md"


def evidence_from_pdf(fy: str):
    import fitz
    g = sorted(glob.glob(str(REPO / "data" / "disclosure" / fy / "raw" / f"{CODE}_*.pdf")))
    if not g:
        raise SystemExit(f"abort: no PDF for {CODE} {fy}")
    doc = fitz.open(g[0])
    try:
        for i in range(min(doc.page_count, 80)):
            tn = re.sub(r"\s+", "", doc[i].get_text("text") or "")
            m = re.search(r"무[·∙ㆍ.,]?저해지상품해지율예외모형사용에관한사항", tn)
            if not m or i + 1 <= 3:
                continue
            # the statement sits right behind the heading, on the same page or (heading at the page foot) the next one; the year-end template puts it BEFORE the heading
            window = tn[max(0, m.start() - 700): m.end() + 900]
            if i + 1 < doc.page_count:
                window += re.sub(r"\s+", "", doc[i + 1].get_text("text") or "")[:900]
            hit = next((p for p in PHRASES if p in window), None)
            if hit:
                k = window.find(hit)
                return {"file": str(Path(g[0]).relative_to(REPO)).replace("\\", "/"), "page": i + 1, "phrase": hit, "quote": window[max(0, k - 30): k + 90]}
        raise SystemExit(f"abort: the exception-model statement was not found in {fy}")
    finally:
        doc.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    ilp = json.loads(lic.ILP.read_text(encoding="utf-8"))
    reg = lic.ilp_registry(ilp)
    have = {(r["원보험사코드"], r["공시분기"], r["항목번호"]): r["값"] for r in ilp}
    if have.get((CODE, "2026.2Q", 9)) != 1:
        raise SystemExit(f"abort: precedent cell {CODE} 2026.2Q item 9 is {have.get((CODE, '2026.2Q', 9))}, expected 1")
    new_rows, prov = [], []
    for q, fy in QUARTERS.items():
        if (CODE, q, 9) in have:
            raise SystemExit(f"abort: {CODE} {q} item 9 already exists ({have[(CODE, q, 9)]})")
        if (CODE, q, 8) not in have:
            raise SystemExit(f"abort: {CODE} {q} has no items 1-8 (item 9 is only added next to a loaded cell)")
        ev = evidence_from_pdf(fy)
        print(f"{CODE} {q}: statement found {fy} p{ev['page']} | …{ev['quote']}…")
        new_rows.append(L.row(reg, CODE, q, 9, L.ITEM9_NAME, L.SEC_LAPSE, 1, 1))
        prov.append({"company_code": CODE, "quarter": q, "item": 9, "value": 1, "basis": "pdf_text_exception_model_selected", "source_file": ev["file"], "page": ev["page"],
                     "evidence": ev["quote"], "note": ("the section states that the exception model was chosen and prints the 예외모형 vs 원칙모형 comparison of the current period; "
                                                      "same meaning as the master's 2026.2Q = 1")})
    if not args.write:
        print(f"dry run: {len(new_rows)} rows would be added")
        return
    backup = lic.merge_into_ilp(new_rows, tag="pre_kr0003_item9")
    raw0 = L.PROV.read_bytes()
    txt = raw0.decode("utf-8")
    pv = json.loads(txt)
    if json.dumps(pv, ensure_ascii=False, indent=1) + "\n" != txt:
        raise SystemExit("abort: provenance file does not round-trip byte for byte (the master rows ARE written; add the provenance by hand)")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d")
    pb = lic.BACKUP_DIR / f"ilp_provenance_backup_{stamp}_pre_kr0003_item9.json"
    shutil.copyfile(L.PROV, pb)
    pv["item9_cells"] = pv.get("item9_cells", []) + prov
    pv["backfills"] = pv.get("backfills", []) + [{"stage": "kr0003_item9", "at": datetime.now(timezone.utc).strftime("%Y%m%dT%H%MZ"), "emitted_by": "scripts/fix_20261011_ilp_kr0003_item9.py",
                                                  "ticket": TICKET, "note": "item 9 = 1 added for KR0003 롯데손해보험 2024.4Q, 2025.1Q-4Q, 2026.1Q (PDF statement: exception model chosen)"}]
    out = json.dumps(pv, ensure_ascii=False, indent=1) + "\n"
    tmp = L.PROV.with_name(L.PROV.name + ".tmp")
    tmp.write_bytes(out.encode("utf-8"))
    os.replace(tmp, L.PROV)
    print(f"written: {len(new_rows)} rows; backups {backup.name}, {pb.name}")


if __name__ == "__main__":
    main()
