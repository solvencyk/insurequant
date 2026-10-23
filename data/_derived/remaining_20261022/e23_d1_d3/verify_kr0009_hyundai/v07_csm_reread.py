import sys, json
sys.path.insert(0, ".")
import vlib9, vmaster
H, W = vmaster.load_all("CSM_waterfall")
lines = vlib9.load  # alias
LABELS = {1: "기초순보험계약부채", 2: "신계약효과", 3: "보험금융손익", 4: "보험계약마진을 조정하는 변동", 5: "보험계약마진상각", 6: "기말보험계약순부채"}
TBL = {  # fy -> (current table idx, prior table idx) of the 28-row separate-notes CSM reconciliation, 장기원수 및 수재
    "FY2024_Q1": (508, 510), "FY2024_Q2": (554, 556), "FY2024_Q3": (537, 539), "FY2024_Q4": (992, 994)}
QMAP = {"FY2024_Q1": ("2024.1Q", "2023.1Q"), "FY2024_Q2": ("2024.2Q", "2023.2Q"), "FY2024_Q3": ("2024.3Q", "2023.3Q"), "FY2024_Q4": ("2024.4Q", "2023.4Q")}
out = []
def P(s=""):
    print(s); out.append(s)
cum = {}
for fy in TBL:
    T = vlib9.tables(fy)
    for which, ti in zip(("cur", "prior"), TBL[fy]):
        t = T[ti]
        hdr = [c[1] for c in t["rows"][0]["cells"]]
        assert hdr[0] == "구분" and hdr[3] == "보험계약마진" and hdr[4] == "합계", hdr
        d = {}
        for r in t["rows"]:
            cs = r["cells"]
            if cs and cs[0][1] not in d:
                d[cs[0][1]] = (vlib9.num(cs[3][1]), r["line"] + 4, cs[3][1])
        # identity: 기초 + 신계약 + 이자 + 조정 + 상각 = 기말 (천원)
        lab6 = [l for l in d if l.endswith("말보험계약순부채")]; assert len(lab6) == 1, lab6; LABELS[6] = lab6[0]; v = {k: d[LABELS[k]][0] for k in LABELS}
        ident = v[1] + v[2] + v[3] + v[4] + v[5] - v[6]
        q = QMAP[fy][0 if which == "cur" else 1]
        P("%s %s table@%d lines %d-%d identity residual(천원) %s" % (fy, which, ti, t["start"], t["end"], ident))
        for k in LABELS:
            val = v[k] / 1e5
            cum[(q, k)] = (val, d[LABELS[k]][1], d[LABELS[k]][2], fy, which)
P("\n=== compare reader (EOK, unrounded) vs master WORK/HEAD 값")
bad = 0; n = 0; nchg = 0; nchg_ok = 0
for q in ["2023.1Q", "2023.2Q", "2023.3Q", "2023.4Q", "2024.1Q", "2024.2Q", "2024.3Q", "2024.4Q"]:
    for k in LABELS:
        rv, ln, pr, fy, which = cum[(q, k)]
        hrow = H.get((q, k)); wrow = W.get((q, k))
        hv = hrow["값"] if hrow else None; wv = wrow["값"] if wrow else None
        chg = hv != wv
        ok = wv is not None and abs(wv - rv) <= 0.0501
        n += 1
        if chg:
            nchg += 1; nchg_ok += ok
        if not ok: bad += 1
        P("%s %d %-10s | HEAD %s | WORK %s | reader %.5f | diff %s | %s | %s %s L%d %s" % (q, k, (wrow or hrow)["항목명"][:8], hv, wv, rv, ("%.5f" % (wv - rv)) if wv is not None else "NA", "CHG" if chg else "same", fy, which, ln, pr))
P("\ncells %d bad %d ; changed %d reader-confirmed %d" % (n, bad, nchg, nchg_ok))
json.dump({"%s|%d" % k: list(v) for k, v in cum.items()}, open("v07_csm_cum.json", "w", encoding="utf-8"), ensure_ascii=False)
open("v07_csm_reread.txt", "w", encoding="utf-8").write("\n".join(out))
