import json, os
from collections import defaultdict
REPO = "C:/Users/sangwook.cho/Desktop/insurequant"
here = os.path.dirname(os.path.abspath(__file__))
panel = json.load(open(REPO + "/data/csm_combo/panel_csm_combo.json", encoding="utf-8"))
bs = json.load(open(REPO + "/IFRS17_BS.json", encoding="utf-8"))
port = json.load(open(REPO + "/insurance_liability_portfolio.json", encoding="utf-8"))
side = json.load(open(REPO + "/data/_derived/ilp_includes_lic.json", encoding="utf-8"))["companies"]
side_q = {c: set(v["quarters"]) for c, v in side.items()}
bs20 = {(r["원보험사코드"], r["공시분기"]): float(r["값"]) for r in bs if r["항목번호"] == 20}
pf = defaultdict(dict); names = {}
for r in port:
    pf[(r["원보험사코드"], r["공시분기"])][r["항목번호"]] = None if r["값"] in (None, "") else float(r["값"]); names[r["원보험사코드"]] = 1
dev = {}
for (c, q), d in pf.items():
    b, t = bs20.get((c, q)), d.get(8)
    if d.get(10) and b is not None and t is not None and c not in side_q:
        dv = abs((b / 100.0 - t) / d[10] - 1)
        dev[c] = max(dev.get(c, 0.0), dv)
unrel = sorted(c for c in names if dev.get(c, 0.0) > 0.15)
out = open(here + "/j4_est.txt", "w", encoding="utf-8")
out.write(f"recomputed est_unreliable ({len(unrel)}): {unrel}\npanel meta est_unreliable ({len(panel['meta']['est_unreliable'])}): {panel['meta']['est_unreliable']}\nequal: {unrel == panel['meta']['est_unreliable']}\n")
out.write(f"KR0099 max dev = {dev.get('KR0099')}\n")
