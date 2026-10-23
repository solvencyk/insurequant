# -*- coding: utf-8 -*-
"""patch kr0072_verify.py D2: compare the FY2025 annual third column (제 36 기 = FY2023) with the FY2024 annual prior column row by row (labels aligned, the two labels that shifted in FY2025 mapped)."""
from pathlib import Path

p = Path(__file__).resolve().parent / "kr0072_verify.py"
s = p.read_text(encoding="utf-8")


def sub(a, b):
    global s
    assert s.count(a) == 1, (s.count(a), a[:80])
    s = s.replace(a, b)


sub('''    S25 = Stmt(F["A25"])
    v25 = items_from(S25.read(2023, "cum"))
    worst25 = max(abs(v25[i] - NEW["2023.4Q"]["items"][i]) for i in v25 if i not in (4, 7, 12))
    say(f"    worst |A25 - N4| over {len([i for i in v25 if i not in (4, 7, 12)])} items = {worst25:.6f} -> {'no later restatement of FY2023' if worst25 <= 2e-6 else 'DIFFERENT'}")
    if worst25 > 2e-6:
        problem("A25", "FY2025 annual third column differs from the FY2024 prior column")''',
    '''    a25 = fy_column_rows(F["A25"], "제 36 기")
    n4c = fy_column_rows(F["N4"], "제 36 기")
    shift = {nspace("보험비용"): nspace("보험서비스비용"), nspace("보험서비스비용"): nspace("보험영업비용"), nspace("영업이익"): nspace("영업이익(손실)"),
             nspace("법인세차감전순이익"): nspace("법인세비용차감전순이익(손실)"), nspace("법인세수익"): nspace("법인세비용(수익)"), nspace("당기순이익"): nspace("당기순이익(손실)")}
    pool = list(a25)
    n_match, unmatched = 0, []
    for lab, val, ln in n4c:
        cands = [lab] + ([shift[lab]] if lab in shift else [])
        hit = next((x for x in pool if x[0] in cands and abs(x[1] - val) <= 1e-9), None)
        if hit is None:
            unmatched.append((lab, val, ln))
        else:
            pool.remove(hit)
            n_match += 1
    say(f"    FY2024 annual prior column rows {len(n4c)} | matched in the FY2025 annual third column (same label or the shifted label, same value to the won) {n_match} | unmatched {len(unmatched)}")
    for u in unmatched[:12]:
        say(f"      unmatched: {u}")
    key_ok = all(any(abs(x[1] - NEW['2023.4Q']['V'][k]['printed_won']) <= 1e-9 for x in a25 if x[0] in (nspace(LABELS[k][0]),)) for k in ("ins_result", "inv", "ni", "oci", "tci"))
    say(f"    key rows (보험손익 투자손익 당기순이익 기타포괄손익 총포괄손익) equal in both: {key_ok} -> {'no later restatement of FY2023' if not unmatched else 'DIFFERENT'}")
    if unmatched:
        problem("A25", f"FY2025 annual third column differs from the FY2024 prior column on {len(unmatched)} rows")''')
sub('''def eok(v_mn):''', '''def fy_column_rows(rel, header_text):
    """[(normalised label, value in 원 as float, 1-based line)] of the separate 4-2 statement for the column whose header cell reads `header_text` (no THEAD needed: header cells are found among the first rows)"""
    L = lines_of(rel)
    a, b = section(L, r"^4-2\.\s*포괄손익계산서")
    tab = None
    for (ta, tb) in all_tables(L):
        if a <= ta <= b:
            rows = table_rows(L, ta, tb)
            if any(nspace(r["cells"][0]["text"]) == "보험손익" for r in rows if r["cells"]):
                tab = (ta, tb, rows)
                break
    ta, tb, rows = tab
    hdr_idx = None
    for r in rows[:8]:
        texts = [c["text"] for c in r["cells"]]
        if header_text in texts and len(texts) >= 3:
            hdr_idx = texts.index(header_text)
            break
    if hdr_idx is None:
        # THEAD paths
        from kdb_raw import header_paths
        paths = header_paths(L, ta, tb)
        hdr_idx = next(j for j, p_ in enumerate(paths) if p_ and p_[0] == header_text)
    out = []
    for r in rows:
        cs = r["cells"]
        if len(cs) > hdr_idx and hdr_idx > 0:
            v = parse_num(cs[hdr_idx]["text"])
            if v is not None and cs[hdr_idx]["text"] != "" and nspace(cs[0]["text"]) != "":
                out.append((nspace(cs[0]["text"]), v, cs[hdr_idx]["line"]))
    return out


def eok(v_mn):''')
p.write_text(s, encoding="utf-8", newline="\n")
print("patched")
