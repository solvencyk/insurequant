"""one-off: derive e21_read.py from e20_read.py (own copy with the label variants the READY buckets need); safe to delete"""
p = "e21_read.py"
s = open(p, encoding="utf-8").read()
rep = [
    ('"""e20 statement reader + PL Tier-1 item mapper (own code; no scripts/ or src/ imports).', '"""e21 statement reader + PL Tier-1 item mapper (copy of STEP 1 e20_read.py with extra label variants; own code; no scripts/ or src/ imports).\nExtra vs e20: 투자서비스손익 (17), 반기/분기/당기 총포괄이익 (31), 대손충당금 -> OCI residual bucket (32) (KB손보), life income-statement insurance lines (read_is_lines).'),
    ('    17: ["투자손익", "투자서비스결과"],', '    17: ["투자손익", "투자서비스결과", "투자서비스손익"],'),
    ('    31: ["총포괄손익", "분기총포괄손익", "반기총포괄손익", "당기총포괄손익"],', '    31: ["총포괄손익", "분기총포괄손익", "반기총포괄손익", "당기총포괄손익", "총포괄이익", "분기총포괄이익", "반기총포괄이익", "당기총포괄이익"],'),
    ('    if "신용손실" in n or "손상충당금" in n:', '    if "신용손실" in n or "손상충당금" in n or "대손충당금" in n:'),
]
for a, b in rep:
    assert s.count(a) == 1, a
    s = s.replace(a, b)
s = s.replace('if lab.endswith("총포괄손익"):', 'if lab.endswith(("총포괄손익", "총포괄이익")):')
s = s.replace('and not r.lab.endswith("총포괄손익")', 'and not r.lab.endswith(("총포괄손익", "총포괄이익"))')
s += '''

# --------------------------------------------------------------------------------------------- life income-statement insurance lines (items 3 / 8 inputs)
LIFE_IS = {
    # company group -> (rev labels, cost labels, rerev labels, recost labels); the first label present wins
    "default": (["보험수익", "보험서비스수익"], ["보험서비스비용", "보험비용"], ["재보험수익", "출재보험서비스수익"], ["재보험비용", "출재보험서비스비용", "재보험서비스비용"]),
}


def read_is_lines(st, role="prior", kind="cum", labels=None):
    """-> dict name -> Part for the four statement lines the life branch of assemble() uses (_is_rev, _is_cost, _is_rerev, _is_recost); raises when a label set matches 0 or >1 rows"""
    revs, costs, rerevs, recosts = labels or LIFE_IS["default"]
    out = {}
    for key, names in (("rev", revs), ("cost", costs), ("rerev", rerevs), ("recost", recosts)):
        row = None
        for nm in names:
            row = st.find([nm], optional=True, oci_only=False)
            if row is not None:
                break
        if row is None:
            raise KeyError(f"{st.rel}: none of {names}")
        c = st.pick_cell(row, role, kind)
        v = cellnum(c)
        out[key] = Part(row.raw.replace("　", " ").strip(), c["line"], c["text"], 1, v / st.scale)
    return out
'''
open(p, "w", encoding="utf-8", newline="\n").write(s)
print("e21_read.py written", len(s))
