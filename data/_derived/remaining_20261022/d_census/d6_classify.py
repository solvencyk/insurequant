# -*- coding: utf-8 -*-
"""d6: classification + closure + materiality per bucket (read-only).  Input d5_buckets.json, masters.  Output d6_rows.json."""
import json, sys
from pathlib import Path
from collections import defaultdict, Counter
sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant"); OUT = ROOT / "data/_derived/remaining_20261022/d_census"
rows = json.loads((OUT / "d5_buckets.json").read_text(encoding="utf-8"))
pl = json.loads((ROOT / "PL_breakdown.json").read_text(encoding="utf-8"))
PLM = defaultdict(dict)
for r in pl: PLM[(r["원보험사코드"], r["공시분기"])][str(r["항목번호"])] = r.get("값")
bb = json.loads((ROOT / "data/_gold/pl_bridge_baseline.json").read_text(encoding="utf-8"))["entries"]
BRIDGE_BASE = {tuple(k.split("|")[:2]) for k in bb}
has_csm_rows = {c for (c, q) in {(r["원보험사코드"], r["공시분기"]) for r in json.loads((ROOT / "CSM_waterfall.json").read_text(encoding="utf-8"))}}

DEFAULT_FLOOR = 200.0
def bridge_diff(bo, m, oi_override=None, oe_override=None):
    """validate_master_tables dual-form: min over (bare, bare+15-16) of (cand - bo)."""
    if bo is None: return None
    legs = [m.get("2"), m.get("13"), m.get("14")]
    bare = sum(0.0 if v is None else v for v in legs)
    cands = [bare]
    oi = oi_override if oi_override is not None else m.get("15")
    oe = oe_override if oe_override is not None else m.get("16")
    if oi is not None and oe is not None: cands.append(bare + oi - oe)
    return min((c - bo for c in cands), key=abs)
def bridge_ok(bo, diff): return diff is None or abs(diff) <= max(0.001 * abs(bo), DEFAULT_FLOOR)

PANEL_ITEMS = {"1", "17", "24", "16", "21", "23", "26", "27", "28", "29", "30", "31", "32"}   # drawn on a page (see d5 PL_PANELS)
out = []
for r in rows:
    code, q = r["code"], r["q"]; k = (code, q); m = PLM[k]
    its = {int(i): v for i, v in r["its"].items()}
    cls = {int(i): c for i, c in r["cls"].items()}
    real = r["real"]
    kind, detail = None, ""
    d24, d25, d31 = r["d24_eok"], r["d25_eok"], r["d31_eok"]
    nonsign_diff = [i for i, c in cls.items() if c in ("REAL",)]
    sign_items = [i for i, c in cls.items() if c in ("SIGN", "SIGN_DERIVED")]
    if not real and not sign_items and r["scope"] == "ADDL_CSM_ONLY":
        kind, detail = "CSM_ONLY_RESTATEMENT", "PL Tier-1 vintages agree; only the CSM waterfall of the later filing differs from the master"
    elif not real:
        if all(r["rel_master"].get(str(i)) in ("LATEST", "NONE") for i in (1, 17, 22, 24) if str(i) in r["rel_master"]) and r["rel_master"].get("1") == "LATEST":
            kind, detail = "ALREADY_LATEST", "master cells equal the later filing's prior column (adopted in an earlier round / gold)"
        else:
            kind, detail = "API_SIGN_ONLY", "no restatement: items 1/17/20/22/24 equal; only sign presentation of expense lines (items %s) differs between the two filings" % ",".join(map(str, sign_items))
    else:
        parts = []
        if 1 in real or 16 in real or 15 in real: parts.append("insurance result restated (item 1/15/16)")
        else: parts.append("insurance result unchanged")
        if d24 is not None and d25 is not None and max(abs(d24), abs(d25)) < 1.0:
            parts.append("net income and OCI unchanged: reclass among operating lines (items %s)" % ",".join(map(str, real)))
        elif d24 is not None and d25 is not None and abs(d24 + d25) <= 0.05 * max(abs(d24), abs(d25), 1) and abs(d31 or 0) <= 0.05 * max(abs(d24), abs(d25), 1):
            parts.append("pure after-tax PL<->OCI reclass (items 24 and 25 move by equal and opposite amounts, 31 unchanged)")
        elif d25 is not None and abs(d25) > 0 and 17 in real:
            parts.append("investment/finance lines and OCI restated (31 changes by %s eok)" % d31)
        elif 25 in real and 17 not in real:
            parts.append("OCI-only restatement (25/26/31/32; PL unchanged)")
        elif 24 in real and 25 not in real:
            parts.append("net income restated without OCI change")
        if r["tag_move_eok"] is not None and r["tag_move_eok"] >= 5:
            parts.append("account-tag movement among OCI leaves ~%s eok" % r["tag_move_eok"])
        kind = "RESTATEMENT"; detail = "; ".join(parts)
        if sign_items: detail += "; sign-presentation noise on items %s ignored" % ",".join(map(str, sign_items))
    # ---- PL closure on the later Tier-1 vector
    idl = r["id_latest"]; tier1_ok = all(v is not False for v in idl.values())
    # bridge: current vs latest (legs from master are the only Tier-2 data we have)
    bo_now = m.get("1"); bo_lat = its.get(1, {}).get("prior") if 1 in its else None
    if bo_lat is None: bo_lat = bo_now
    d_now = bridge_diff(bo_now, m)
    oi_lat = m.get("15"); oe_lat = its.get(16, {}).get("prior") if (16 in its and its[16].get("prior") is not None and cls.get(16) == "REAL") else m.get("16")
    d_lat = bridge_diff(bo_lat, m, oi_lat, oe_lat) if kind == "RESTATEMENT" else d_now
    br_now_ok, br_lat_ok = bridge_ok(bo_now, d_now), bridge_ok(bo_lat, d_lat)
    bridge_note = "n/a" if d_now is None else ("closes unchanged" if (br_now_ok and br_lat_ok and bo_now == bo_lat) else ("closes with legs unchanged" if br_lat_ok and not br_now_ok is False else ("BREAKS: item 1 moves, legs (Tier-2) would need the prior-column reading" if br_now_ok and not br_lat_ok else ("baseline-FAIL now, still FAIL" if not br_now_ok and not br_lat_ok else "baseline-FAIL now, closes on latest"))))
    # ---- CSM state
    c = r["csm"]; has_csm = code in has_csm_rows
    if not has_csm: cstate = "n/a"
    elif c["status"] is None: cstate = "NOSCAN"
    elif c["status"] == "SAME": cstate = "SAME"
    elif c["status"] == "NO_PRIOR": cstate = "NO_PRIOR"
    elif c["status"] == "DIFF": cstate = "DIFF_ALREADY_LATEST" if c["rel_now"] == "LATEST" else "DIFF"
    else: cstate = c["status"]
    csm_delta = {}
    if cstate in ("DIFF",) and c["latest"]:
        for i, (a, b) in enumerate(zip(c["now"], c["latest"]), start=1):
            if a is not None and b is not None and abs(a - b) > 0.051: csm_delta[i] = round(b - a, 2)
    pair = None
    if cstate == "DIFF" and c["latest"] and c["pl4_eok"] is not None:
        a5 = abs(c["now"][4]); l5 = abs(c["latest"][4]); p4 = abs(c["pl4_eok"])
        tol = lambda x: max(0.1, 0.0005 * abs(x))
        pair = {"resid_now": round(p4 - a5, 2), "resid_csm_only_latest": round(p4 - l5, 2), "ok_now": abs(p4 - a5) <= tol(a5), "ok_csm_only": abs(p4 - l5) <= tol(l5)}
    # ---- displayed magnitude
    disp_pl = [d for d in r["disp"] if str(d["item"]) in PANEL_ITEMS]
    best = None
    for d in disp_pl:
        rel = abs(d["rel"]) if d["rel"] is not None else 0
        key = abs(d["delta_eok"] or 0)
        if best is None or key > best["abs"]: best = {"item": d["item"], "name": d["name"], "abs": key, "rel": rel, "master": d["master_eok"], "latest": d["latest_eok"]}
    csm_best = None
    for i, dv in csm_delta.items():
        base = abs(c["now"][i - 1] or 0)
        if csm_best is None or abs(dv) > csm_best["abs"]: csm_best = {"item": i, "abs": abs(dv), "rel": (abs(dv) / base if base else 0), "master": c["now"][i - 1], "latest": c["latest"][i - 1]}
    gold_pl_block = r["gold_in_block"]
    out.append({**{k2: r[k2] for k2 in ("code", "name", "q", "scope", "real", "gold_overlap", "gold_in_block", "gold_val", "fy_status", "pl_verdict_1012", "d24_eok", "d25_eok", "d31_eok", "tag_move_eok", "id_latest", "id_master")},
                "kind": kind, "detail": detail, "sign_items": sign_items, "tier1_ok": tier1_ok,
                "bridge_now": None if d_now is None else round(d_now, 1), "bridge_latest": None if d_lat is None else round(d_lat, 1), "bridge_note": bridge_note,
                "bridge_baseline_now": (code and (r["name"], q) in BRIDGE_BASE) or (code, q) in BRIDGE_BASE,
                "csm_state": cstate, "csm_status": c["status"], "csm_verdict_1012": c["verdict_1012"], "csm_fid": c["fid"], "csm_tier": c["tier"], "csm_now": c["now"], "csm_latest": c["latest"],
                "csm_delta": csm_delta, "csm_gold": c["gold"], "pair": pair, "best_pl": best, "best_csm": csm_best,
                "disp": r["disp"], "rel_master": r["rel_master"], "its": r["its"], "cls": r["cls"]})
json.dump(out, open(OUT / "d6_rows.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(Counter((x["scope"], x["kind"]) for x in out))
print(Counter((x["scope"], x["csm_state"]) for x in out))
print(Counter(x["bridge_note"] for x in out))
print("bridge baseline now:", [(x["name"], x["q"]) for x in out if x["bridge_baseline_now"]])
