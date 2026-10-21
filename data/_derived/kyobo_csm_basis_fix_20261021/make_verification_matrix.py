"""Read-only: verification matrix for ticket 20261021T1310Z (E1-E5), one row per quarter.

Columns: current master (git HEAD, before this fix) vs original-vintage raw (separate basis) vs latest-comparative (restated) raw,
the PL item-4 pairing test of the restated item 5, and the decision.  Output: verification_matrix.csv (utf-8-sig).
"""
import csv
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
EV = ROOT / "data" / "_derived" / "kyobo_csm_basis_fix_20261021"
sys.stdout.reconfigure(encoding="utf-8")


def head_json(rel):
    out = subprocess.run(["git", "show", f"HEAD:{rel}"], cwd=ROOT, capture_output=True, check=True)
    return json.loads(out.stdout.decode("utf-8"))


vec = json.loads((EV / "csm_vectors_raw.json").read_text(encoding="utf-8"))
master = head_json("CSM_waterfall.json")
pl = head_json("PL_breakdown.json")
cur = {}
for r in master:
    if r["원보험사코드"] == "KR0073":
        cur.setdefault(r["공시분기"], {})[r["항목번호"]] = r["값"]
pl4 = {r["공시분기"]: r["값"] for r in pl if r["원보험사코드"] == "KR0073" and r["항목번호"] == 4}

ROWS = [
    # quarter, original spec, restated spec, ticket ref, decision
    ("2023.1Q", "2023.1Q@FY2023_Q1", "2023.1Q@FY2024_Q1prior", "E3", "HELD"),
    ("2023.2Q", "2023.2Q@FY2023_Q2", "2023.2Q@FY2024_Q2prior", "E3", "HELD"),
    ("2023.3Q", "2023.3Q@FY2023_Q3", "2023.3Q@FY2024_Q3prior", "E1+E3", "HELD"),
    ("2023.4Q", "2023.4Q@FY2023_Q4", "2023.4Q@FY2024_Q4prior", "E1+E2+E3", "HELD"),
    ("2024.1Q", "2024.1Q@FY2024_Q1", "2024.1Q@FY2025_Q1prior", "E4", "HELD"),
    ("2024.2Q", "2024.2Q@FY2024_Q2", "2024.2Q@FY2025_Q2prior", "E4", "HELD"),
    ("2024.3Q", "2024.3Q@FY2024_Q3", "2024.3Q@FY2025_Q3prior", "confirm", "CONFIRMED (no restatement)"),
    ("2024.4Q", "2024.4Q@FY2024_Q4", "2024.4Q@FY2025_Q4prior_3blk", "confirm", "CONFIRMED (no restatement, 3-block separate sum)"),
    ("2026.1Q", "2026.1Q@FY2026_Q1sep_cur_3blk", None, "E5", "APPLIED"),
    ("2026.2Q", "2026.2Q@FY2026_Q2sep_cur_3blk", None, "confirm", "CONFIRMED (matches separate)"),
]


def fmt(v):
    return "[" + ", ".join(f"{x:.2f}" for x in v) + "]"


out = EV / "verification_matrix.csv"
with open(out, "w", encoding="utf-8-sig", newline="") as f:
    w = csv.writer(f)
    w.writerow(["quarter", "ticket", "master_before(I1..I6)", "original_vintage_raw(sep)", "orig_filing_lines", "restated_raw(sep)", "restated_filing_lines",
                "closure_gap_orig_mn", "closure_gap_restated_mn", "PL_item4_pl_eok", "restated_I5_eok", "pair_residual_eok", "pair_tol_eok", "pair_closes", "decision", "note"])
    for q, so, sr, tref, dec in ROWS:
        m = [cur[q][i] for i in range(1, 7)]
        vo = vec[so]
        lines_o = f"{vo['file'].split('/')[-1]} tables {vo['tables']}"
        if sr:
            vr = vec[sr]
            lines_r = f"{vr['file'].split('/')[-1]} tables {vr['tables']}"
            rv = vr["vec_eok"]
            pl_eok = round(abs(pl4[q]) / 100.0, 2)
            i5 = round(abs(rv[4]), 2)
            resid = round(pl_eok - i5, 2)
            tol = max(0.1, 0.0005 * i5)
            closes = abs(resid) <= tol
            note = ""
            if tref in ("E3", "E1+E3", "E1+E2+E3", "E4"):
                note = ("restated block verified from raw and closes by itself; adopting it makes CSM_AMORT_IDENTITY (PL item 4 still original vintage) "
                        + ("pass" if closes else "FAIL (new RED)") + "; see note on PL restatement / owner pins")
            w.writerow([q, tref, fmt(m), fmt(vo["vec_eok"]), lines_o, fmt(rv), lines_r, vo["closure_gap_mn"], vr["closure_gap_mn"],
                        pl_eok, i5, resid, round(tol, 3), closes, dec, note])
        else:
            w.writerow([q, tref, fmt(m), fmt(vo["vec_eok"]), lines_o, "", "", vo["closure_gap_mn"], "", "", "", "", "", "", dec,
                        "separate-basis 3-block sum (유배당+무배당+변액); item1 kept 65109.6 = master 2025.4Q close" if q == "2026.1Q" else "master already equals the separate sum (rounding)"])
print("wrote", out)
for row in csv.reader(open(out, encoding="utf-8-sig")):
    print(" | ".join(row[:1] + row[13:15]) if row[0] != "quarter" else "")
