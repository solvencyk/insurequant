# -*- coding: utf-8 -*-
"""Validation: NH농협손보 KR0032 2023.1Q-2023.3Q items 20-32 from later filings' prior-year columns (won)."""
import json, sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e25_followups/pass3/verify_independent/val")
from vtab import load_tables, num

ROOT = "C:/Users/sangwook.cho/Desktop/insurequant"
FIL = {
    "2023.1Q": ("data/dart/FY2024_Q1/raw/KR0032_NH농협손해보험/20240514001436.xml", "prior"),
    "2023.2Q": ("data/dart/FY2024_Q2/raw/KR0032_NH농협손해보험/20240814001448.xml", "prior"),
    "2023.3Q": ("data/dart/FY2024_Q3/raw/KR0032_NH농협손해보험/20241114001354.xml", "prior"),
    # own original filings (cross-check, may differ by rounding)
    "2023.2Q@own": ("data/dart/FY2023_Q2/raw/KR0032_NH농협손해보험/20230814001056.xml", "cur"),
}
pl = json.load(open(ROOT + "/PL_breakdown.json", encoding="utf-8"))
M = {}
for r in pl:
    if r["원보험사코드"] == "KR0032":
        M[(r["공시분기"], str(r["항목번호"]))] = (r.get("값"), r.get("값_당분기"))

LAB = {
    "20": ["III.영업이익"], "ni": ["IV.영업외수익"], "ne": ["V.영업외비용"],
    "22": ["VI.법인세차감전순이익"], "23": ["VII.법인세비용"], "24": ["VIII.반기순이익", "VIII.분기순이익", "VIII.당기순이익"],
    "25": ["IX.기타포괄손익"],
    "26": ["기타포괄손익-공정가치측정금융자산관련손익"],
    "27": ["보험금융순손익"],
    "28": ["현금흐름위험회피파생상품평가손익"],
    "29": ["기타포괄손익-공정가치측정유가증권평가손익"],
    "30": ["재보험금융순손익"],
    "32": ["확정급여제도의 재측정요소"],
    "31": ["X.총포괄손익"],
}
out = []
P = out.append
fail = 0
for q, (fp, which) in FIL.items():
    tabs, _ = load_tables(ROOT + "/" + fp)
    got = {}
    found_tab = None
    for s, e, rows in tabs:
        labs = [r[0].replace(" ", "") for r in rows if r]
        if any(l.startswith("III.영업이익") for l in labs) and any(l.startswith("X.총포괄손익") for l in labs):
            found_tab = s
            for r in rows:
                if not r:
                    continue
                lab = r[0].replace(" ", "")
                nums = [num(c) for c in r[1:]]
                for k, ls in LAB.items():
                    for l in ls:
                        if lab == l.replace(" ", "") and k not in got and all(n is not None for n in nums) and nums:
                            got[k] = nums
            break
    if "20" not in got:
        P(f"##### {q}: statement table not found/parsed (found_tab={found_tab}, got={sorted(got)})")
        continue
    ncols = len(got["20"])
    P(f"##### {q} {fp} table L{found_tab} numeric cols {ncols}")
    # columns: 4 -> [3M cur, cum cur, 3M prior, cum prior]; 2 -> [cur, prior]
    if ncols == 4:
        idx = {"cur": (1, 0), "prior": (3, 2)}[which]
    else:
        idx = {"cur": (0, 0), "prior": (1, 1)}[which]
    cum_i, m3_i = idx
    cumv = {k: v[cum_i] / 1e6 for k, v in got.items()}
    m3v = {k: v[m3_i] / 1e6 for k, v in got.items()}
    cumv["21"] = cumv["ni"] - cumv["ne"]
    m3v["21"] = m3v["ni"] - m3v["ne"]
    # identities in won
    r1 = cumv["22"] - cumv["23"] - cumv["24"]
    r2 = cumv["20"] + cumv["21"] - cumv["22"]
    r3 = cumv["24"] + cumv["25"] - cumv["31"]
    r4 = cumv["25"] - sum(cumv[k] for k in ("26", "27", "28", "29", "30", "32"))
    P(f"   printed identities (cum, 백만원 resid): 22-23-24={r1:.6f}; 20+21-22={r2:.6f}; 24+25-31={r3:.6f}; 25-leaves={r4:.6f}")
    if q.endswith("@own"):
        # compare own cur vs master
        pass
    qq = q.split("@")[0]
    for k in ("20", "21", "22", "23", "24", "25", "26", "27", "28", "29", "30", "31", "32"):
        mv, ms = M.get((qq, k), (None, None))
        okc = mv is not None and abs(mv - cumv[k]) < 0.0006
        oks = ms is not None and abs(ms - m3v[k]) < 0.0006 if qq != "2023.1Q" else (ms is not None and abs(ms - cumv[k]) < 0.0006)
        tag = "OK" if okc else "DIFF"
        tags = "OK" if oks else ("NULL" if ms is None else "DIFF")
        if q.endswith("@own"):
            P(f"   item{k:>2} cum printed(own) {cumv[k]:>14.6f} master {mv}  {tag}")
            continue
        P(f"   item{k:>2} cum printed {cumv[k]:>14.6f} master {mv}  {tag} | 3M printed {m3v[k]:>14.6f} master_single {ms}  {tags}")
        if not q.endswith("@own"):
            fail += (not okc) + (not oks)
    # master identities
    mm = {k: M.get((qq, k), (None, None))[0] for k in map(str, range(20, 33))}
    if None not in mm.values():
        P(f"   MASTER identities: 22-23-24={mm['22']-mm['23']-mm['24']:.6f}; 20+21-22={mm['20']+mm['21']-mm['22']:.6f}; 24+25-31={mm['24']+mm['25']-mm['31']:.6f}; 25-leaves={mm['25']-sum(mm[k] for k in ('26','27','28','29','30','32')):.6f}")
    else:
        P("   MASTER has blanks: " + str([k for k, v in mm.items() if v is None]))
    P("")
P(f"FAIL count (non-own): {fail}")
open(ROOT + "/data/_derived/remaining_20261022/e25_followups/pass3/verify_independent/val/b03_nh.txt", "w", encoding="utf-8").write("\n".join(out))
print("\n".join(out))
