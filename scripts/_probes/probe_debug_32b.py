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
print(f"window p{p_start}-{p_end}, {len(lines)} raw lines")
lines = aq._normalize_aliases(aq._merge_fragments(lines))
print(f"after merge+alias: {len(lines)} lines")

vals32, status32, detail32 = aq._parse_32_lines(lines)
print("status32:", status32, detail32)

# manually replicate candidate scan against the FINAL (merged) lines for inspection
n = len(lines)
i = 0
candidates = []
while i < n:
    compact = aq._compact(lines[i])
    is_leaf = compact in aq.LEAF_KEYWORDS
    is_subtotal = compact.startswith("소계") or "A+B+C+D" in compact.upper()
    is_total = compact.startswith("합계")
    if is_leaf or is_subtotal or is_total:
        vals = []
        j = i + 1
        scanned = 0
        while j < n and len(vals) < 2 and scanned < 6:
            tokc = aq._compact(lines[j])
            if aq._looks_like_value_token(tokc):
                vals.append(aq._parse_amount(tokc))
            elif tokc in aq.LEAF_KEYWORDS or tokc.startswith("소계") or "A+B+C+D" in tokc.upper() or tokc.startswith("합계"):
                break
            j += 1
            scanned += 1
        kind = "subtotal" if is_subtotal else ("total" if is_total else compact)
        candidates.append((i, kind, vals))
        print(f"  cand @ line{i}: {lines[i]!r} kind={kind} vals={vals}")
        i = j if vals else i + 1
    else:
        i += 1
print(f"total candidates: {len(candidates)}")
