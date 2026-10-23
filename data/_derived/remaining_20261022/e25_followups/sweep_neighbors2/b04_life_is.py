# -*- coding: utf-8 -*-
"""Items 3 / 8 / 2 for life companies without an e21_life SPEC (KR0082, KR0087, KR0069, KR0071, KR0094): income-statement lines of the LATER filing (default fallback of production assemble()):
3 = 보험수익 - |보험(서비스)비용| ; 8 = 재보험수익 - |재보험(서비스)비용| ; 2 = 3 + 8.  Calibration: the CURRENT column must reproduce the master of quarter+4 (items 2, 3, 8)."""
import json, sys, re, collections
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e23_d1_d3")
sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e21_ready25")
import s2lib
import e21_read as R
ROOT = "C:/Users/sangwook.cho/Desktop/insurequant"
S2 = ROOT + "/data/_derived/remaining_20261022/e25_followups/sweep_neighbors2/"
pl = {(r["원보험사코드"], str(r["항목번호"]), r["공시분기"]): r.get("값") for r in json.load(open(f"{ROOT}/PL_breakdown.json", encoding="utf-8"))}
unc = {tuple(x) for x in json.load(open(S2 + "uncovered.json", encoding="utf-8"))}
_orig = R.Stmt.pick_cell
def pick_cell(self, row, role, kind):
    r = _orig(self, row, role, kind)
    if r is None and (not row.cells or any(R.RE_CTX.match(c["ctx"] or "") for c in row.cells)):
        return dict(text="(blank cell)", val=0.0, line=row.line, ctx="BLANK")
    return r
R.Stmt.pick_cell = pick_cell
COMP = ("KR0082", "KR0087", "KR0069", "KR0071", "KR0094")
tg = sorted({(c, q) for c, q, i in unc if c in COMP and i in ("2", "3", "8") and q != "2025.3Q"})
out = []
LAB = dict(rev=["보험수익", "보험서비스수익", "보험영업수익"], cost=["보험서비스비용", "보험비용", "보험영업비용"], rerev=["재보험수익", "출재보험서비스수익", "재보험영업수익"],
           recost=["재보험비용", "출재보험서비스비용", "재보험서비스비용", "재보험영업비용"])


def lines_for(st, role):
    got = {}
    for key, names in LAB.items():
        row = None
        for nm in names:
            hit = [r for r in st.rows if not r.oci and r.lab == nm]
            if hit:
                row = hit[0]
                break
        if row is None:
            return None
        c = st.pick_cell(row, role, "cum")
        if c is None:
            return None
        got[key] = (c["val"] / st.scale if c["val"] is not None else 0.0, c["line"], c["text"])
    return got


def items(got):
    i3 = got["rev"][0] - abs(got["cost"][0])
    i8 = got["rerev"][0] - abs(got["recost"][0])
    return {"3": i3, "8": i8, "2": i3 + i8}


for c, q in tg:
    fy = f"FY{int(q[:4]) + 1}_Q{q[5]}"
    mq = f"{int(q[:4]) + 1}.{q[5:]}"
    try:
        st = R.Stmt(c, fy)
    except Exception as e:
        print(c, q, "ERR", str(e)[:100])
        continue
    gp, gc = lines_for(st, "prior"), lines_for(st, "cur")
    if gp is None or gc is None:
        print(c, q, "labels not found")
        continue
    cur, pri = items(gc), items(gp)
    cal = all(abs(cur[k] - (pl.get((c, k, mq)) if pl.get((c, k, mq)) is not None else 1e18)) <= 1.5 for k in ("3", "8", "2"))
    print(c, q, "cal", cal, {k: (round(cur[k], 1), pl.get((c, k, mq))) for k in cur}, "prior", {k: round(v, 1) for k, v in pri.items()})
    for k, v in pri.items():
        if pl.get((c, k, mq)) is not None and abs(cur[k] - pl.get((c, k, mq))) <= 1.5:
            lines_ = [gp[x][1] for x in (("rev", "cost") if k == "3" else (("rerev", "recost") if k == "8" else ("rev", "cost", "rerev", "recost")))]
            out.append(dict(company=c, quarter=q, item=k, master=pl.get((c, k, q)), latest=v, filing=st.rel, line=",".join(str(x) for x in lines_), source="stmt_life_is", confidence="high",
                            note=f"income-statement insurance lines prior/cum; cur column reproduces master {mq}"))
json.dump(dict(cells=out), open(S2 + "b04_life_is.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("cells", len(out))
