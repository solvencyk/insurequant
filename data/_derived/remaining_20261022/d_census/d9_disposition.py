# -*- coding: utf-8 -*-
"""d9: closure + disposition per bucket (read-only).  Input d6_rows.json (+ optional d10_gate_findings.json from the gate simulation).
Output d9_disposition.json {code|q: {...}}."""
import json, sys
from pathlib import Path
from collections import defaultdict, Counter
sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant"); OUT = ROOT / "data/_derived/remaining_20261022/d_census"
rows = json.loads((OUT / "d6_rows.json").read_text(encoding="utf-8"))
gcs = json.loads((ROOT / "data/_gold/user_csm_cells.json").read_text(encoding="utf-8"))
GOLD_CSM = defaultdict(dict)
for c in gcs["set"]: GOLD_CSM[(c["원보험사코드"], c["공시분기"])][int(c["항목번호"])] = c["값"]
gate_bad = {}
if (OUT / "d10_gate_findings.json").exists():
    gate_bad = json.loads((OUT / "d10_gate_findings.json").read_text(encoding="utf-8"))

HEADLINE = {1, 17, 24}
ABS_SMALL, REL_SMALL = 20.0, 0.05          # eok, fraction.  'small' = every displayed item < 20 eok AND every headline item (보험손익/투자손익/당기순이익) < 5 %
def screen_class(r):
    items = []
    for d in r["disp"]:
        if str(d["panel"]) == "download-only": continue
        items.append((d["item"], d["name"], d["master_eok"], d["latest_eok"], d["delta_eok"], d["rel"]))
    for i, dv in r["csm_delta"].items():
        items.append((f"CSM{i}", f"CSM item {i}", r["csm_now"][int(i) - 1], r["csm_latest"][int(i) - 1], dv, (dv / abs(r["csm_now"][int(i) - 1]) if r["csm_now"][int(i) - 1] else None)))
    if not items: return "none", ""
    big = False
    for it, nm, a, b, dl, rel in items:
        if abs(dl or 0) >= ABS_SMALL: big = True
        if it in HEADLINE and rel is not None and abs(rel) >= REL_SMALL: big = True
    items.sort(key=lambda x: -abs(x[4] or 0))
    txt = "; ".join(f"{nm} {a:,.1f}->{b:,.1f} ({dl:+,.1f}{'' if rel is None else ', %+.1f%%' % (rel * 100)})" for it, nm, a, b, dl, rel in items[:3])
    return ("material" if big else "small"), txt

x_rows = {(r["code"], r["q"]): r for r in rows}
csm_chain = defaultdict(list)
for r in rows:
    if r["csm_state"] == "DIFF": csm_chain[(r["code"], r["q"][:4])].append(r["q"])
def csm_ok(r):
    if r["csm_state"] != "DIFF": return True
    gv = GOLD_CSM.get((r["code"], r["q"]), {})
    gold_conf = bool(gv) and r["csm_latest"] and any(abs(v - r["csm_latest"][i - 1]) > 0.051 for i, v in gv.items())
    pr = r["pair"]
    return (not gold_conf) and r["csm_fid"] != "DIFF" and pr is not None and pr["ok_csm_only"]
disp = {}
for r in rows:
    key = f"{r['code']}|{r['q']}"
    d = {"scope": r["scope"], "kind": r["kind"]}
    reasons = []
    # CSM gold conflict
    gold_conflict = False
    gv = GOLD_CSM.get((r["code"], r["q"]), {})
    if gv and r["csm_latest"]:
        for i, v in gv.items():
            if abs(v - r["csm_latest"][i - 1]) > 0.051 and r["csm_state"] == "DIFF": gold_conflict = True
    d["csm_gold_conflict"] = gold_conflict
    sc, txt = screen_class(r)
    d["screen"] = sc; d["screen_text"] = txt
    if r["kind"] in ("ALREADY_LATEST", "API_SIGN_ONLY"):
        d.update(closing=None, pl_adoptable=False, disposition="STAY", why="no real difference: " + r["detail"])
        disp[key] = d; continue
    # ---- closing tests
    why = []
    tier1 = r["tier1_ok"]
    if r["kind"] == "RESTATEMENT" and not tier1: why.append("Tier-1 identity on the later vector fails")
    bn = r["bridge_note"]
    item1_moves = 1 in r["real"] or 15 in r["real"] or 16 in r["real"]
    br_lat_ok = r["bridge_latest"] is not None and abs(r["bridge_latest"]) <= max(0.001 * abs(r["its"].get("1", {}).get("prior") or 0), 200.0) if r["bridge_latest"] is not None else None
    br_now_ok = r["bridge_now"] is not None and abs(r["bridge_now"]) <= max(0.001 * abs(r["its"].get("1", {}).get("master") or r["its"].get("1", {}).get("prior") or 0), 200.0) if r["bridge_now"] is not None else None
    if r["kind"] == "RESTATEMENT" and br_lat_ok is False: why.append("Tier-2 legs (items 2/13/14) do not sum to the later item 1 (residual %s mn): prior-column reader for the LOB note is missing" % r["bridge_latest"] if br_now_ok else "bridge already FAIL on the current master (%s mn) and stays FAIL" % r["bridge_latest"])
    if r["kind"] == "RESTATEMENT" and br_lat_ok is None and item1_moves: why.append("bridge not testable (legs missing)")
    cs = r["csm_state"]
    if cs == "DIFF":
        items = ",".join(map(str, sorted(map(int, r["csm_delta"]))))
        pr = r["pair"]
        if d["csm_gold_conflict"]:
            why.append("CSM waterfall restated (items %s) and owner CSM gold cells %s differ from the later vector" % (items, r["csm_gold"]))
        if r["csm_fid"] == "DIFF":
            why.append("CSM waterfall restated (items %s) but the dry-run reader did not reproduce the master on the same filing (fidelity DIFF): vector unverified" % items)
        if pr is None:
            why.append("CSM waterfall restated (items %s); PL4 pair not testable" % items)
        elif not pr["ok_csm_only"]:
            why.append("CSM waterfall restated (items %s); PL4 (Tier-2 CSM amortization of the later filing) is not read, so CSM-only adoption breaks CSM_AMORT_IDENTITY (residual %s eok)" % (items, pr["resid_csm_only_latest"]))
        # FY chain: every CSM-restated quarter of the same FY must be adoptable, otherwise opening drift / FY-boundary breaks appear
        bad = [x for x in csm_chain.get((r["code"], r["q"][:4]), []) if x != r["q"] and not csm_ok(x_rows[(r["code"], x)])]
        if bad:
            why.append("same-FY CSM chain cannot be adopted as a unit (not adoptable: %s)" % ",".join(bad))
    elif cs == "NO_PRIOR":
        why.append("CSM prior column could not be extracted from the later filing: CSM side unverified")
    elif cs == "NOSCAN":
        why.append("CSM not scanned")
    closing = (len(why) == 0)
    d["closing"] = closing; d["why_not_closing"] = why
    d["pl_adoptable"] = False
    if not closing:
        d.update(disposition="STAY", why="; ".join(why))
    elif r["gold_overlap"]:
        d["closing"] = True
        d.update(disposition="STAY", why="closes, but owner gold cells %s sit on items the adoption would change" % r["gold_overlap"])
    else:
        d["pl_adoptable"] = True
        d.update(disposition="OWNER" if sc == "material" else "SAFE", why="closes (Tier-1 identities, bridge unchanged, CSM unchanged); on-screen change %s" % sc)
    disp[key] = d
# FY seam: for adoptable buckets, which same-FY neighbours stay at the other vintage
for r in rows:
    key = f"{r['code']}|{r['q']}"; d = disp[key]
    stale = []
    if d.get("pl_adoptable"):
        for sq, st in r["fy_status"].items():
            if sq == r["q"]: continue
            if st == "DIFF" and not (disp.get(f"{r['code']}|{sq}") or {}).get("pl_adoptable"): stale.append(sq)
            if st is None: stale.append(sq + "(no later filing)")
    d["seam_stale"] = stale
    if d.get("disposition") == "SAFE" and any("(no later" not in s for s in stale):
        d["disposition"] = "OWNER"; d["why"] += "; same-FY neighbour(s) %s stay at the original vintage -> single-quarter seam cells must be blanked" % ",".join(s for s in stale if "(no later" not in s)
    if key in gate_bad and d.get("pl_adoptable"):
        d["gate_findings"] = gate_bad[key]
json.dump(disp, open(OUT / "d9_disposition.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
a51 = [(k, v) for k, v in disp.items() if v["scope"] == "A51"]
print("A51:", Counter(v["disposition"] for k, v in a51), " closing:", Counter(v["closing"] for k, v in a51), " screen:", Counter((v["disposition"], v["screen"]) for k, v in a51))
print("ADDL:", Counter((v["scope"], v["disposition"]) for k, v in disp.items() if v["scope"] != "A51"))
print("pl_adoptable:", sum(1 for v in disp.values() if v.get("pl_adoptable")), "of which A51:", sum(1 for k, v in a51 if v.get("pl_adoptable")))
