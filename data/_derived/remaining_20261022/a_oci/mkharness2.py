from pathlib import Path
p = Path("apply_kr0073_oci.py")
s = p.read_text(encoding="utf-8")
def sub(old, new):
    global s
    assert s.count(old) == 1, (old[:70], s.count(old))
    s = s.replace(old, new)

sub('''        g["set"].append({"원보험사코드": CODE, "항목번호": c["item"], "공시분기": c["quarter"], "값": c["new"], "was": c["old"], "note": note})
    return g
''', '''        g["set"].append({"원보험사코드": CODE, "항목번호": c["item"], "공시분기": c["quarter"], "값": c["new"], "was": c["old"], "note": note})
    nd = g.setdefault("null_dangi", {"cells": []})
    have = {tuple(x) for x in nd["cells"]}
    for q, i in NULL_DANGI:
        if (CODE, q, i) in have:
            raise SystemExit(f"ABORT: null_dangi already has {(CODE, q, i)}")
        nd["cells"].append([CODE, q, i])
    nd["_doc_oci_20261022"] = NULL_DANGI_DOC
    return g
''')
sub('def rkey(r):', '''# single-quarter (값_당분기) cells that would subtract a restated cumulative from a cumulative of ANOTHER filing basis after this refresh:
#   2024.4Q = FY2024 restated (annual filed 2026) - 9M 2024 as originally filed; 2025.3Q = 9M 2025 as originally filed - H1 2025 restated.
#   No printed 3-month restated column exists for either (annual report has none; the FY2026 Q3 report is not filed yet) -> blank, not a mixed-basis difference.
NULL_DANGI = [(q, i) for q in ("2024.4Q", "2025.3Q") for i in (25, 26, 31, 32)]
NULL_DANGI_DOC = ("KR0073 OCI refresh 2026-10-22 (ticket 20261021T1556Z): 값_당분기 of items 25/26/31/32 for 2024.4Q and 2025.3Q is blanked. After the cumulative refresh of 2024.4Q (FY2025 annual restated column) "
                  "and 2025.1Q/2025.2Q (FY2026 Q1/Q2 restated comparatives) the builder difference of those cells would subtract a restated cumulative from a cumulative of another filing basis "
                  "(2024.3Q and 2025.3Q are still as originally filed; the restated 3-month columns are not published: annual report has none, the FY2026 Q3 report is not filed yet). "
                  "Owner rule 2026-10-22: a blank beats a wrong value. Re-derive once the FY2026 Q3 report restates 2025.3Q. Items 27/28/29/30/24 are unaffected (same basis in both filings).")


def rkey(r):''')
# post-build assertions for the null cells
sub('''    if len(val_changed) != EXPECT["val_changed"]:''', '''    by0 = {rkey(r): r for r in new_rows}
    for q, i in NULL_DANGI:
        r = by0.get((CODE, i, q))
        if r is None or r["값_당분기"] is not None or r["값"] is None:
            errs.append(f"null_dangi cell {(q, i)} not blank/with cumulative: {None if r is None else (r['값'], r['값_당분기'])}")
    if len(val_changed) != EXPECT["val_changed"]:''')
p.write_text(s, encoding="utf-8", newline="\n")
print("ok")
