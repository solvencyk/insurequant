# -*- coding: utf-8 -*-
"""Read-only census: for every 2026.2Q company, does extract_mkt_subs() on the
CURRENT md_inbox MD reproduce the 36-40 values already loaded in master
kics_disclosure.json? Flags: MISSING (master has it, current MD extraction
doesn't produce it) and VALUE_MISMATCH (both present, values differ beyond
rounding). Does NOT write kics_disclosure.json.
"""
import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))
from fill_market_subitems_to_disclosure import extract_mkt_subs, mkt_est, _to_eok, MKT_SUBS  # noqa: E402

QUARTER = "2026.2Q"
MD_DIR = REPO / "md_inbox" / "FY2026_Q2"

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

codes = sorted(by_code_item.keys())
print(f"2026.2Q companies in master: {len(codes)}")

n_have_1936 = 0
n_gap = 0
n_value_mismatch = 0
n_clean = 0
n_no_item19 = 0
n_no_md = 0
report_rows = []

for code in codes:
    items = by_code_item[code]
    name = names.get(code, code)
    item19 = items.get(19)
    master_v5 = {i: items.get(i) for i in (36, 37, 38, 39, 40)}
    master_present = {i: v for i, v in master_v5.items() if v is not None and str(v.get("값", "")).strip() not in ("", "-")}
    if not master_present and item19 is None:
        continue  # nothing to check for this company (parent-zero / no market items expected)
    n_have_1936 += 1

    md_path = MD_DIR / f"{code}_*.md"
    matches = list(MD_DIR.glob(f"{code}_*.md"))
    if not matches:
        n_no_md += 1
        report_rows.append((code, name, "NO_MD", "-", "-"))
        continue
    md_path = matches[0]
    text = md_path.read_text(encoding="utf-8")
    subs = extract_mkt_subs(text)

    gaps = []
    mismatches = []
    for i in (36, 37, 38, 39, 40):
        m = master_present.get(i)
        if m is None:
            continue  # master doesn't have this item either -> not a gap to flag
        m_val = float(str(m["값"]).replace(",", ""))
        if i not in subs:
            gaps.append((i, m_val))
            continue
        raw, unit = subs[i]
        md_val = float(_to_eok(raw, unit))
        if abs(md_val - m_val) > max(0.5, 0.01 * abs(m_val)):
            mismatches.append((i, m_val, md_val))

    if gaps:
        n_gap += 1
        gap_str = ",".join(f"item{i}(master={v:.2f})" for i, v in gaps)
        report_rows.append((code, name, "MD_GAP", gap_str, ""))
    if mismatches:
        n_value_mismatch += 1
        mm_str = ",".join(f"item{i}(master={mv:.2f} vs md={dv:.2f})" for i, mv, dv in mismatches)
        report_rows.append((code, name, "VALUE_MISMATCH", mm_str, ""))
    if not gaps and not mismatches:
        n_clean += 1

print(f"\ncompanies with 36-40 and/or item19 present in master: {n_have_1936}")
print(f"  clean (current MD reproduces master exactly, tol 1%): {n_clean}")
print(f"  MD_GAP (master has item, current MD extraction can't find it): {n_gap}")
print(f"  VALUE_MISMATCH (both present, differ >1%): {n_value_mismatch}")
print(f"  NO_MD (no md_inbox file at all): {n_no_md}")

print("\n--- detail ---")
for code, name, kind, detail, _ in report_rows:
    print(f"{code} {name:<14} {kind:<15} {detail}")
