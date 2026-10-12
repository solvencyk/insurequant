"""b1: DIRECT PDF look-up for the 17 candidate blocks that survive ticket criterion 4 (READ-ONLY).

For each changed cell (field 값) print, for the quarter's OWN filing and the two later filings (F+1 prev col, F+2 prev2 col),
the printed table rows that contain the old / new number.  The text is the PDF text layer (PyMuPDF words clustered by y).
Output -> b1_pdf_rows.txt (read it; the evidence pages are recorded from it).
"""
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/kics_latest_prior_apply_20261012")
from pdfcheck import fmt_tokens, find_rows, utf8_stdout  # noqa: E402
import fitz  # noqa: E402

utf8_stdout()
REPO = Path("C:/Users/sangwook.cho/Desktop/insurequant")
D = REPO / "data" / "_derived" / "kics_latest_prior_precedence_dryrun_20261012"
core = json.loads((D / "core_extract_all.json").read_text(encoding="utf-8"))
verd = list(csv.DictReader(open(D / "block_verdicts.csv", encoding="utf-8-sig")))
QS = [f"{y}.{q}Q" for y in (2023, 2024, 2025, 2026) for q in (1, 2, 3, 4)][:14]
SURVIVORS = ["KR0003_2023.4Q", "KR0003_2025.1Q", "KR0004_2023.1Q", "KR0004_2024.1Q", "KR0009_2023.1Q", "KR0009_2023.2Q",
             "KR0032_2024.3Q", "KR0049_2025.1Q", "KR0049_2026.1Q", "KR0050_2025.3Q", "KR0069_2024.2Q", "KR0070_2024.3Q",
             "KR0071_2024.4Q", "KR0072_2025.2Q", "KR0080_2026.1Q", "KR0095_2024.4Q", "KR0099_2024.3Q"]
only = sys.argv[1].split(",") if len(sys.argv) > 1 else SURVIVORS


def qadd(q, n):
    i = QS.index(q) + n
    return QS[i] if 0 <= i < len(QS) else None


def per(q):
    return f"FY{q[:4]}_Q{q[5]}"


def rec_of(code, filing_q):
    return core.get(f"{per(filing_q)}|{code}") if filing_q else None


for bid in only:
    code, q = bid.split("_")
    plan = json.loads((D / "plans" / f"{bid}.json").read_text(encoding="utf-8"))
    edits = [e for e in plan["edits"] if e["field"] == "값"]
    print("=" * 120)
    print(bid, [(e["item"], e["old"], e["new"]) for e in edits])
    for label, fq, col in (("OWN", q, "cur"), ("F+1", qadd(q, 1), "prev"), ("F+2", qadd(q, 2), "prev2")):
        rec = rec_of(code, fq)
        if rec is None:
            print(f"  [{label}] filing {fq}: no record")
            continue
        pdf = REPO / rec["pdf"]
        print(f"  [{label}] filing {fq} ({col} col) {rec['pdf'].split('/')[-1]}  status={rec['status']} pages={rec.get('pages')}")
        if rec["status"] not in ("OK", "VISION_ONLY") and not rec.get("pages"):
            pages = None
        else:
            pages = rec.get("pages")
        doc = fitz.open(str(pdf))
        try:
            for e in edits:
                old, new = e["old"], e["new"]
                try:
                    to = fmt_tokens(old)
                    tn = fmt_tokens(new)
                except Exception:
                    to = tn = []
                if e["item"] == 22 and float(old) == 0:
                    print(f"      item{e['item']}: old=0 new={new} (small number; checked by eye)")
                    continue
                toks = list(dict.fromkeys(to + tn))
                hits = find_rows(str(pdf), pages, toks, doc)
                print(f"      item{e['item']:>2} old={old} new={new} tokens={toks}: {len(hits)} row(s)")
                for p, y, t in hits[:8]:
                    print(f"          p{p} y{y}: {t[:200]}")
        finally:
            doc.close()
