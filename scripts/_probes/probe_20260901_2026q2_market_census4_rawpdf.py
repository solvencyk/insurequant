# -*- coding: utf-8 -*-
"""For every Category-A (code,item) pair from census3 (heading regex absent from
current MD), open the RAW PDF directly (fitz) and search every page's text for
the same heading pattern. Distinguishes:
  TEXT_IN_RAW_PDF   - the heading (and presumably the table) exists as real text
                       in the raw PDF -> docling window dropped it (Samsung-class).
  NOT_IN_RAW_PDF    - heading not found anywhere in the raw PDF's text layer ->
                       either scanned/image page (no text layer) or a genuinely
                       different disclosure layout. Reports avg page-text-density
                       so scanned vs. sparse-but-real can be told apart.

Read-only (PDF + MD + master JSON only). No writes anywhere.
"""
import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))
from fill_market_subitems_to_disclosure import extract_mkt_subs, _HEADING_RISK_RE, _HEADING_RISK_MAP  # noqa: E402
import fitz  # noqa: E402

QUARTER = "2026.2Q"
MD_DIR = REPO / "md_inbox" / "FY2026_Q2"
PDF_DIR = REPO / "data" / "disclosure" / "FY2026_Q2" / "pdf"

RISK_NAME = {36: "금리", 37: "주식", 38: "부동산", 39: "외환", 40: "자산집중"}

rows = json.loads((REPO / "kics_disclosure.json").read_text(encoding="utf-8"))
by_code_item = {}
names = {}
for r in rows:
    if r["공시분기"] != QUARTER:
        continue
    code = r["원보험사코드"]
    names[code] = r.get("원수사명", code)
    try:
        it = int(r["항목번호"])
    except (TypeError, ValueError):
        continue
    by_code_item.setdefault(code, {})[it] = r

# rebuild Category-A set (same logic as census3)
cat_a = {}
for code, items in sorted(by_code_item.items()):
    matches = list(MD_DIR.glob(f"{code}_*.md"))
    if not matches:
        continue
    text = matches[0].read_text(encoding="utf-8")
    present_risk_items = {_HEADING_RISK_MAP[m.group(1)] for m in _HEADING_RISK_RE.finditer(text)}
    subs = extract_mkt_subs(text)
    for i in (36, 37, 38, 39, 40):
        rec = items.get(i)
        if rec is None:
            continue
        val_str = str(rec.get("값", "")).strip()
        if val_str in ("", "-") or i in subs or i in present_risk_items:
            continue
        cat_a.setdefault(code, []).append(i)

print(f"Category-A companies to raw-PDF-verify: {len(cat_a)}\n")

for code in sorted(cat_a):
    name = names.get(code, code)
    pdfs = list(PDF_DIR.glob(f"{code}_*.pdf"))
    if not pdfs:
        print(f"{code} {name}: NO RAW PDF FOUND under {PDF_DIR}")
        continue
    doc = fitz.open(pdfs[0])
    total_chars = 0
    page_texts = []
    for pno in range(doc.page_count):
        t = doc[pno].get_text()
        total_chars += len(t)
        page_texts.append(t)
    avg_density = total_chars / max(1, doc.page_count)

    found = {}
    for i in cat_a[code]:
        kw = RISK_NAME[i]
        hit_pages = [p + 1 for p, t in enumerate(page_texts) if kw in t and "위험액" in t]
        found[i] = hit_pages

    verdict_bits = []
    for i in cat_a[code]:
        hp = found[i]
        if hp:
            verdict_bits.append(f"item{i}:TEXT_IN_RAW_PDF(p{hp[:3]})")
        else:
            verdict_bits.append(f"item{i}:NOT_IN_RAW_PDF")
    print(f"{code} {name:<16} avg_chars/page={avg_density:6.0f} pages={doc.page_count:3d}  " + " ".join(verdict_bits))
    doc.close()
