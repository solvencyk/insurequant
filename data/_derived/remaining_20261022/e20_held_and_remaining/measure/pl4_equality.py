"""pl4_equality: PL item 4 (원수 CSM상각) read from the LATER filing's note PRIOR column by the e20 prototypes vs the CSM waterfall prior amortisation (item 5, 억원) of the same filing.
tolerance of the live gate: max(0.1억, 0.05%).  READ-ONLY -> pl4_equality.csv/.txt"""
import csv, json, sys
sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e20_held_and_remaining/measure")
import csmvec as CV, mlib as M
sys.stdout.reconfigure(encoding="utf-8")
def J(n):
    p = M.MEASURE / n
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}
rows = []
def add(code, q, note_mn, src):
    p = CV.prior(code, q)
    csm5 = None if not p else p[4]
    if csm5 is None:
        m = M.load_csm().get((code, q), {})
        csm5 = m.get(5)   # unchanged CSM -> master
    diff = None if csm5 is None else abs(note_mn) / 100 - abs(csm5)
    tol = None if csm5 is None else max(0.1, 0.0005 * abs(csm5))
    rows.append({"code": code, "quarter": q, "note_prior_mn": note_mn, "csm_prior_item5_eok": csm5, "diff_eok": None if diff is None else round(diff, 3), "gate_tol_eok": None if tol is None else round(tol, 3), "within": (None if diff is None else abs(diff) <= tol), "reader_source": src})
for q, v in J("p_lotte.json").items():
    add("KR0003", q, v["prior_run"]["4"], "p_lotte_run (2nd table of the LOB note pair)")
for q, v in J("p_kblife.json").items():
    add("KR0099", q, v["later_prior"].get("4"), "p_kblife (전기/twin table block)")
for q, v in J("p_lifeold_KR0072.json").items():
    add("KR0072", q, v["later_prior_col"].get("4"), "p_lifeold (old-life L2, one period block to the right)")
for q, v in J("p_hanwha.json").items():
    add("KR0068", q, v["later_prior"].get("4"), "p_hanwha (L1, 2nd table)")
for q, v in J("p_meritz.json").items():
    add("KR0001", q, v["later_prior"]["4"], "p_meritz (Format-B 2nd 상세내역 table)")
for q, mn, src in (("2023.2Q", 46789, "FY2024_Q2 note '(1) 당반기와 전반기 중 보험영업수익' 보험계약마진상각 prior-YTD cell L22569"), ("2023.3Q", 69639, "FY2024_Q3 same note cell L22013"), ("2023.4Q", 92971, "FY2024_Q4 [구분|당기|전기] note 전기 col (p_abl)")):
    add("KR0070", q, mn, src)
rows = [r for r in rows if r["note_prior_mn"] is not None]
with open(M.MEASURE / "pl4_equality.csv", "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
print(len(rows), "rows; within tol:", sum(1 for r in rows if r["within"]))
for r in rows:
    print(r["code"], r["quarter"], r["note_prior_mn"], r["csm_prior_item5_eok"], r["diff_eok"], r["gate_tol_eok"], r["within"])
