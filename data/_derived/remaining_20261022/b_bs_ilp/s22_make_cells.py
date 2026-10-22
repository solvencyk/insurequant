"""Read-only generator: proposed_cells.csv (tier A: closes) and hold_cells.csv (tier B/C/ALT) for KR0073 BS + ILP.
Writes only into this folder.  Never touches a master."""
import csv, json, re, sys
from pathlib import Path

ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
D = ROOT / "data/_derived/remaining_20261022/b_bs_ilp"
sys.path.insert(0, str(D))
from s4_bs_rows import filings, bs_rows  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")


def num(t):
    t = t.replace(",", "").strip()
    neg = t.startswith("(") and t.endswith(")")
    t = t.strip("()")
    v = float(t)
    return -v if neg else v


bs = json.loads((ROOT / "IFRS17_BS.json").read_text(encoding="utf-8"))
ilp = json.loads((ROOT / "insurance_liability_portfolio.json").read_text(encoding="utf-8"))
MB = {(r["공시분기"], r["항목번호"]): r["값"] for r in bs if r["원보험사코드"] == "KR0073"}
MI = {(r["공시분기"], r["항목번호"]): r["값"] for r in ilp if r["원보험사코드"] == "KR0073"}
NAME_BS = {1: "자산총계", 2: "부채총계", 3: "자본총계", 4: "기타포괄손익 누계액", 20: "보험계약부채", 31: "이익잉여금"}
NAME_ILP = {10: "발생사고요소_합계", 13: "발생사고요소_미분리", 14: "잔여보장요소_합계", 15: "보험계약부채_합계"}
LAB = {1: "자산총계", 2: "부채총계", 3: "자본총계", 20: "보험계약부채", 31: "이익잉여금"}
files = filings()


def rel(p):
    return p.relative_to(ROOT).as_posix()


def bs_cell(fy, item, col):
    rows = bs_rows(files[fy])
    for tr, cells, lns in rows:
        if cells[0].replace(" ", "").replace("(결손금)", "") == LAB[item]:
            return num(cells[1 + col]) / 1e6, lns[1 + col] if len(lns) > 1 + col else lns[0], cells[1 + col], lns[0]
    raise KeyError((fy, item))


HDR = ["tier", "master", "company_code", "company", "quarter", "item", "item_name", "unit", "old", "new", "delta",
       "source", "second_source", "verification", "apply_route"]
A, H = [], []
ROUTE_BS = ("data/dart/viz/bs_manual_overrides.json key KR0073|<item>|<quarter> {value, basis}; then build_ifrs17_bs.py "
            "(overrides applied last) + tests/test_ifrs17_bs_golden.py --update")
ROUTE_ILP = ("no overlay for ILP: cell-guarded loader (precedent scripts/unify_ilp_restated_3cells_2023_4q.py: old-value guard, "
             "provenance original_basis_value, backup) -- not run here")

# ---- tier A: BS 2023.4Q (FY2024 annual comparative == FY2025 annual third column), BS 2024.4Q item 1
for item in (1, 2, 3, 20, 31):
    v25, l25, t25, tr25 = bs_cell("FY2025_Q4", item, 2)
    v24, l24, t24, tr24 = bs_cell("FY2024_Q4", item, 1)
    assert abs(v25 - v24) < 1e-6, (item, v25, v24)
    old = MB[("2023.4Q", item)]
    A.append(["A", "IFRS17_BS", "KR0073", "교보생명보험", "2023.4Q", item, NAME_BS[item], "백만원", old, v25, round(v25 - old, 6),
              f"{rel(files['FY2025_Q4'])}#L{l25} {LAB[item]} 제67기 열 {t25} 원 (별도 재무상태표 3번째 열)",
              f"{rel(files['FY2024_Q4'])}#L{l24} 제67기 열 {t24} 원 (FY2024 사업보고서 전기 열); 소급재작성 효과표 "
              "data/dart/FY2024_Q3/raw/KR0073_교보생명보험/20241114003039.xml#L57768-57894 (수정후/수정전/증감)",
              "block closes: 1 = 2 + 3 (115,002,544.050 = 105,026,788.690 + 9,975,755.360, residual 0.000); "
              "d(2) = d(20) = -290,457.894; d(1) = -77,094.505 = d(2) + d(3); RE roll 5,920,420.192 + 632,200.607 - 51,250 - 74,244.917 "
              "= 6,427,125.882 = item 31 (PL FY2023 net income 632,201)",
              ROUTE_BS])
v, l, t, trn = bs_cell("FY2025_Q4", 1, 1)
old = MB[("2024.4Q", 1)]
A.append(["A", "IFRS17_BS", "KR0073", "교보생명보험", "2024.4Q", 1, "자산총계", "백만원", old, v, round(v - old, 6),
          f"{rel(files['FY2025_Q4'])}#L{l} 자산총계 제68기 열 {t} 원 (별도 재무상태표 2번째 열)",
          f"{rel(files['FY2025_Q4'])}#L71111 소급재작성 효과표(44-2 전기말) 자산총계 수정후 122,408,552 / 수정전 122,408,983 / 증감 (431)",
          "completes the 2026-10-12 partial block: items 2,3,4 already on this column; after: 1 = 2 + 3 residual 0.000 "
          "(115,102,330.810 + 7,306,220.723 = 122,408,551.533); today 431.466 off",
          ROUTE_BS])

# ---- tier A: ILP 2023.4Q
r9 = json.loads((D / "s9_ilp_all.json").read_text(encoding="utf-8"))["FY2024_Q4|prior"]
new = {10: r9["lic"], 14: r9["lrc"], 15: r9["total"]}
note = {10: "rounding-level (+0.01); printed LIC closing 2,692,746 mn = 26,927.46; kept in the set so that 10 + 14 = 15",
        14: "LRC restated: printed 83,536,489 + 1,013,643 = 84,550,132 mn",
        15: "= restated BS item 20 / 100 (87,242,878.594 mn -> 872,428.786; printed 87,242,879)"}
for item in (10, 14, 15):
    old = MI[("2023.4Q", item)]
    A.append(["A", "insurance_liability_portfolio", "KR0073", "교보생명보험", "2023.4Q", item, NAME_ILP[item], "억원", old, new[item],
              round(new[item] - old, 2),
              f"{rel(files['FY2024_Q4'])}#L63748/L63764/L63772 기말 보험계약자산 및 부채 (전기 열, 별도 주석 보험계약부채 변동표; "
              "stage-1 engine table 477, cur/prior swapped read)",
              f"{rel(files['FY2024_Q4'])}#L49738 보험계약부채 제67기 87,242,878,594,424 원; {note[item]}",
              "10 + 14 = 15 (0.00); 15 == restated BS20/100 (diff 0.004); BS20 and ILP15 move together (R-LIC1 pair)", ROUTE_ILP])
with open(D / "proposed_cells.csv", "w", encoding="utf-8-sig", newline="") as f:
    w = csv.writer(f)
    w.writerow(HDR)
    w.writerows(A)


# ---- hold file
def soce(fy, date_label):
    p = D / f"soce_rows_{fy}.txt"
    for ln in p.read_text(encoding="utf-8").split("\n"):
        m = re.match(r"\s*L(\d+): (%s) \(\S*말자본\) \| (.*)" % re.escape(date_label), ln)
        if m:
            cols = [num(x) / 1e6 for x in m.group(3).split(" | ")]
            return int(m.group(1)), cols
    raise KeyError((fy, date_label))


S = {"2023.1Q": ("FY2024_Q1", "2023.03.31"), "2023.2Q": ("FY2024_Q2", "2023.06.30"), "2023.3Q": ("FY2024_Q3", "2023.09.30"),
     "2024.1Q": ("FY2025_Q1", "2024.03.31"), "2024.2Q": ("FY2025_Q2", "2024.06.30"), "2024.3Q": ("FY2025_Q3", "2024.09.30"),
     "2025.1Q": ("FY2026_Q1", "2025.03.31")}
SOCE = {}
for q, (fy, dl) in S.items():
    ln, cols = soce(fy, dl)
    SOCE[q] = (fy, ln, cols)
SOCE["2025.2Q"] = ("FY2026_Q2", 32013,
                   [102500.0, 2205726.208213, 365966.306274, -197234.758164, -3129858.437041, 7441652.486049, 6788751.805331])
Q2_2026 = "data/dart/FY2026_Q2/raw/KR0073_교보생명보험/20260814004024.xml"


def srcline(q):
    fy, ln, _ = SOCE[q]
    path = rel(files[fy]) if fy in files else Q2_2026
    return f"{path}#L{ln} 자본변동표 전기(전년 동기) 열 기말자본"


HOLD_WHY = {
    "2023.1Q": "restated equity printed only on the FSS-guideline (policy-change) basis; the Nov-2024 error correction of 2023 H1 was never printed; "
               "assets/liabilities of the quarter not printed -> block cannot close",
    "2023.2Q": "same as 2023.1Q",
    "2023.3Q": "error-corrected basis (FY2024 Q3 bridge 10,459,288 -> 10,398,402 -> 10,573,071 at L58401/L58490) but assets/liabilities of the "
               "quarter not printed -> block cannot close",
    "2024.1Q": "assets/liabilities of the quarter not printed", "2024.2Q": "assets/liabilities of the quarter not printed",
    "2025.1Q": "OCI-only restatement (policy change in the FY2026 filings); assets/liabilities not printed; must move with the OCI lane PL cells "
               "(ticket 20261021T1556Z)",
    "2025.2Q": "same as 2025.1Q"}
for q in ("2023.1Q", "2023.2Q", "2023.3Q", "2024.1Q", "2024.2Q", "2025.1Q", "2025.2Q"):
    cols = SOCE[q][2]
    for item, idx, nm in ((4, 4, "기타포괄손익 누계액"), (3, 6, "자본총계"), (31, 5, "이익잉여금")):
        old = MB[(q, item)]
        nv = cols[idx]
        if abs(nv - old) < 0.51:
            continue
        tier = "B" if item == 4 else "C"
        ver = ("AOCI roll d(AOCI) == PL item 25 single quarter exactly (s20_aoci_tie.txt); leaves items 3/31 of the same quarter on the old basis "
               "-> mixed equity section unless 3/31 move too" if item == 4 else "equity statement column; block 1 = 2 + 3 not closable")
        H.append([tier, "IFRS17_BS", "KR0073", "교보생명보험", q, item, nm, "백만원", old, nv, round(nv - old, 6), srcline(q), "",
                  ver + "; " + HOLD_WHY[q], "hold -- owner decision"])
r9a = json.loads((D / "s9_ilp_all.json").read_text(encoding="utf-8"))
for q, fy in (("2023.1Q", "FY2024_Q1"), ("2023.2Q", "FY2024_Q2"), ("2023.3Q", "FY2024_Q3")):
    rr = r9a[f"{fy}|prior"]
    for item, key in ((14, "lrc"), (15, "total")):
        old = MI[(q, item)]
        H.append(["C", "insurance_liability_portfolio", "KR0073", "교보생명보험", q, item, NAME_ILP[item], "억원", old, rr[key],
                  round(rr[key] - old, 2),
                  f"{fy} xml prior-period roll-forward closing (stage-1 engine, cur/prior swapped, table {rr['tables'][0][0]}); s9_ilp_all.json", "",
                  "derived from the note roll-forward; no balance sheet printed for the quarter (BS20 pair cannot be set from a printed BS line); "
                  "dE/dBS20 = 0.73 (tax effect, cross-check only); " + HOLD_WHY[q], "hold -- owner decision"])
V2 = {1: (115009276, "L71277"), 2: (105052287, "L71333"), 3: (9956989, "L71382"), 4: (1651401, "L71396")}
for item, (val, ln) in V2.items():
    old = MB[("2023.4Q", item)]
    H.append(["ALT", "IFRS17_BS", "KR0073", "교보생명보험", "2023.4Q", item, NAME_BS[item], "백만원", old, float(val), round(val - old, 3),
              f"{rel(files['FY2025_Q4'])}#{ln} 소급재작성 효과표 44-2 전기초 수정후 (백만원, rounded)", "",
              "later basis (유배당 accounting-policy change, FY2025 annual) for the SAME date, printed only as the 2024-01-01 opening in a note; the "
              "third BS column of the same report is NOT restated for it (separate BS L46624-46771 prints the pre-change values; the consolidated "
              "BS footnote at L5352 says the 제67(전전)기 column was not restated for the policy change); block closes "
              "115,009,276 = 105,052,287 + 9,956,989; PL FY2023 not affected; items 20/31 unchanged",
              "alternative to tier A items 1,2,3 (4 would newly change) -- owner decision"])
with open(D / "hold_cells.csv", "w", encoding="utf-8-sig", newline="") as f:
    w = csv.writer(f)
    w.writerow(HDR)
    w.writerows(H)
print("tier A rows", len(A), " hold rows", len(H))
for r in A:
    print(r[0], r[1][:6], r[4], r[5], r[8], "->", r[9], r[10])
for r in H:
    print(r[0], r[1][:6], r[4], r[5], r[8], "->", r[9], r[10])
