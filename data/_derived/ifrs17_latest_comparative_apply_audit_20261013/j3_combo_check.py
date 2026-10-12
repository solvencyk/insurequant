import json, os, re
from collections import defaultdict
REPO = "C:/Users/sangwook.cho/Desktop/insurequant"
here = os.path.dirname(os.path.abspath(__file__))
src = open(REPO + "/scripts/viz_build_csm_combo_panel.py", encoding="utf-8").read()
EST_TOL = float(re.search(r"EST_TOL\s*=\s*([0-9.]+)", src).group(1))
panel = json.load(open(REPO + "/data/csm_combo/panel_csm_combo.json", encoding="utf-8"))
wf = json.load(open(REPO + "/CSM_waterfall.json", encoding="utf-8"))
bs = json.load(open(REPO + "/IFRS17_BS.json", encoding="utf-8"))
port = json.load(open(REPO + "/insurance_liability_portfolio.json", encoding="utf-8"))
nb = {(r["원보험사코드"], r["공시분기"]): r.get("값_당분기") for r in wf if r["항목번호"] == 2}
bs20 = {(r["원보험사코드"], r["공시분기"]): float(r["값"]) for r in bs if r["항목번호"] == 20}
restated = {}
rpath = re.search(r'RESTATED\s*=\s*.*?["\']([^"\']+\.json)["\']', src)
out = open(here + "/j3_combo_check.txt", "w", encoding="utf-8")
out.write(f"EST_TOL={EST_TOL} restated file={rpath and rpath.group(1)}\n")
if rpath:
    p = rpath.group(1)
    p = p if os.path.isabs(p) else os.path.join(REPO, p)
    for cell in json.load(open(p, encoding="utf-8"))["cells"]:
        restated[(cell["company_code"], cell["quarter"])] = round(cell["restated_bs_insurance_contract_liability_eok"], 2)
bad = 0; n = 0
for c, co in panel["companies"].items():
    for q, row in co["q"].items():
        n += 1
        exp_nb = nb.get((c, q)); exp_nb = None if exp_nb in (None, "") else float(exp_nb)
        if (row[8] is None) != (exp_nb is None) or (exp_nb is not None and abs(row[8] - exp_nb) > 1e-6):
            bad += 1; out.write(f"NB leaf differs {c} {q}: panel {row[8]} vs CSM master item2 값_당분기 {exp_nb}\n")
        b = bs20.get((c, q)); b = None if b is None else round(b / 100.0, 1)
        if (c, q) in restated: b = restated[(c, q)]
        if (row[10] is None) != (b is None) or (b is not None and abs(row[10] - b) > 1e-6):
            bad += 1; out.write(f"bs20 leaf differs {c} {q}: panel {row[10]} vs BS master/100 {b}\n")
out.write(f"checked {n} (company,quarter) rows: nb_csm and bs20 leaves; mismatches {bad}\n")
# est_unreliable recompute
pf = defaultdict(dict)
for r in port:
    pf[(r["원보험사코드"], r["공시분기"])][r["항목번호"]] = None if r["값"] in (None, "") else float(r["값"])
side = json.load(open(REPO + "/data/_derived/ilp_includes_lic_sidecar.json", encoding="utf-8"))["companies"] if os.path.exists(REPO + "/data/_derived/ilp_includes_lic_sidecar.json") else None
out.write(f"sidecar file found: {side is not None}\n")
