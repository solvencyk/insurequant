import io
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, "scripts")
import extract_asset_quality as aq

code = sys.argv[1] if len(sys.argv) > 1 else "KR0080"
period = sys.argv[2] if len(sys.argv) > 2 else "FY2026_Q2"

pdf_path = aq.find_pdf(period, code)
print("pdf_path:", pdf_path)
lines, p_start, p_end, total_chars = aq._pdf_window_text(pdf_path)
print(f"window p{p_start}-{p_end}, {len(lines)} lines")

# replicate the candidate-scan loop from _parse_32_lines with prints
n = len(lines)
i = 0
candidates = []
while i < n:
    compact = aq._compact(lines[i])
    is_leaf = compact in aq.LEAF_KEYWORDS
    is_subtotal = compact.startswith("소계")
    is_total = compact.startswith("합계")
    if is_leaf or is_subtotal or is_total:
        vals = []
        j = i + 1
        scanned = 0
        while j < n and len(vals) < 2 and scanned < 6:
            tokc = aq._compact(lines[j])
            if aq._looks_like_value_token(tokc):
                vals.append(aq._parse_amount(tokc))
            elif tokc in aq.LEAF_KEYWORDS or tokc.startswith("소계") or tokc.startswith("합계"):
                break
            j += 1
            scanned += 1
        kind = "subtotal" if is_subtotal else ("total" if is_total else compact)
        candidates.append((i, kind, vals))
        print(f"  cand @ line{i}: {lines[i]!r} kind={kind} vals={vals}")
        i = j if vals else i + 1
    else:
        i += 1

print(f"\ntotal candidates: {len(candidates)}")
leaves = [c for c in candidates if c[1] not in ("subtotal", "total")]
subtotals = [c for c in candidates if c[1] == "subtotal"]
totals = [c for c in candidates if c[1] == "total"]
print(f"leaves={len(leaves)} subtotals={len(subtotals)} totals={len(totals)}")

# also dump raw lines around where things might be going wrong
print("\n--- all lines (compact) for manual review ---")
for idx, l in enumerate(lines):
    print(f"{idx:3d}: {l!r}")
