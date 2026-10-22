"""vintage_table: exact CSM vintages printed by each filing (original quarter filing vs the next-year same-quarter filing's comparative) per company x FY x quarter,
with rcept numbers, the within-FY opening spread (WFY) and cross-FY continuity of three combinations (ORIGINAL = status quo, LATEST per quarter, and the FY-consistent alternatives).
READ-ONLY -> vintage_table.csv / vintage_table.md"""
import csv
import sys

sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e20_held_and_remaining/measure")
import csmvec as CV  # noqa: E402
import mlib as M  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
CO = {"KR0099": "KB라이프", "KR0003": "롯데손보", "KR0070": "ABL", "KR0072": "KDB생명", "KR0009": "현대해상", "KR0001": "메리츠화재", "KR0068": "한화생명", "KR0079": "미래에셋", "KR0083": "푸본현대"}
VERIFIED = {  # (code, q) -> evidence of the later vector read by an e20 reader (else dry-run scan with open/chain check)
    ("KR0099", "2023.4Q"): "own-read FY2024_Q4 L50518", ("KR0003", "2023.4Q"): "own-read FY2024_Q4 _00760 L10874", ("KR0003", "2024.4Q"): "own-read FY2025_Q4 _00760 L10490/L11056 (== master)",
    ("KR0003", "2024.1Q"): "own-read FY2025_Q1 L15356", ("KR0070", "2023.4Q"): "own-read FY2024_Q4 _00760 L14100", ("KR0070", "2024.4Q"): "own-read FY2025_Q4 _00760 L17230.. (== master)",
    ("KR0009", "2023.4Q"): "own-read FY2024_Q4 L76716", ("KR0083", "2024.4Q"): "own-read FY2025_Q4 L49640.. (== master)", ("KR0079", "2023.4Q"): "own-read FY2024_Q4 L63671..",
    ("KR0079", "2024.1Q"): "own-read FY2025_Q1 L42459..",
}


def rcept(code, fy):
    xs = [p for p in M.main_xmls(code, fy) if not p.name.endswith(("_00760.xml", "_00761.xml"))]
    return xs[0].stem if xs else "-"


csm = M.load_csm()
gold_csm = {(c['원보험사코드'], c['공시분기'], c['항목번호']): c for c in M.jload(M.SNAP / 'user_csm_cells.json')['set']}
rows = []
for code, nm in CO.items():
    for fy in (2023, 2024):
        for qn in (1, 2, 3, 4):
            q = f"{fy}.{qn}Q"
            m = csm.get((code, q), {})
            p = CV.prior(code, q)
            st = CV.status(code, q)
            lf = M.later_fy(q)
            rows.append({"code": code, "company": nm, "quarter": q, "orig_filing": rcept(code, M.fy_of(q)), "master_open": m.get(1), "master_close": m.get(6),
                         "later_filing": rcept(code, lf), "later_open": (p[0] if p else None), "later_close": (p[5] if p else None), "later_status": st,
                         "master_open_gold_note": (f"owner gold {gold_csm[(code, q, 1)]['값']} (filing prints {gold_csm[(code, q, 1)].get('was')})" if (code, q, 1) in gold_csm else ""), "later_verified": VERIFIED.get((code, q), "dry-run scan (opening anchored)" if p else ("same as master" if st in ("SAME", "OVERRIDE_SAME") else "not readable"))})
with open(M.MEASURE / "vintage_table.csv", "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)


def eff(code, fy, mode):
    out = {}
    for qn in (1, 2, 3, 4):
        q = f"{fy}.{qn}Q"
        m = csm.get((code, q), {})
        p = CV.prior(code, q)
        if mode == "latest" and p:
            out[q] = (p[0], p[5])
        else:
            out[q] = (m.get(1), m.get(6))
    return out


md = ["| 회사 | FY | 분기 | 원 공시(rcept) 기초→기말 | 후속 공시 비교열(rcept) 기초→기말 | 판정 |", "|---|---|---|---|---|---|"]
for r in rows:
    later = "-" if r["later_open"] is None else f"{r['later_open']:,.1f}→{r['later_close']:,.1f}"
    md.append(f"| {r['company']} | {r['quarter'][:4]} | {r['quarter']} | {r['orig_filing']} {r['master_open']:,.1f}→{r['master_close']:,.1f} | {r['later_filing']} {later} | {r['later_status']} ({r['later_verified']}) {r['master_open_gold_note']} |")
md.append("")
md.append("| 회사 | FY | 조합 | 분기별 기초 | 연내 기초 편차(WFY) | FY말 기말→다음 FY 기초 연속성 |")
md.append("|---|---|---|---|---|---|")
for code, nm in CO.items():
    for fy in (2023, 2024):
        for mode in ("original", "latest"):
            e = eff(code, fy, mode)
            opens = [v[0] for v in e.values() if v[0] is not None]
            spread = (max(opens) - min(opens)) if opens else 0
            rel = spread / max(opens) if opens else 0
            nxt = eff(code, fy + 1, mode) if fy + 1 <= 2024 else None
            cont = ""
            if nxt:
                c4 = e[f"{fy}.4Q"][1]
                o1 = nxt[f"{fy + 1}.1Q"][0]
                if c4 is not None and o1 is not None:
                    cont = f"{c4:,.1f}→{o1:,.1f} (Δ{o1 - c4:+,.1f}, {abs(o1 - c4) / abs(c4) * 100:.2f}%)"
            md.append(f"| {nm} | {fy} | {mode} | " + " / ".join(f"{v[0]:,.1f}" if v[0] is not None else "-" for v in e.values()) + f" | {spread:,.1f} ({rel * 100:.2f}%) | {cont} |")
M.MEASURE.joinpath("vintage_table.md").write_text("\n".join(md), encoding="utf-8")
print(len(rows), "rows")
