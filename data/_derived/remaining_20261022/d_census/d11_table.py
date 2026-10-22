# -*- coding: utf-8 -*-
"""d11: render the census table (one row per bucket).  Inputs d6_rows.json, d9_disposition.json, d10_effects.json, d12_sign19_scan.txt, d13 notes.
Output d_census_table.csv (utf-8-sig) and d_census_table.tsv-free summary d11_summary.txt"""
import csv, json, re, sys
from pathlib import Path
from collections import Counter, defaultdict
sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant"); OUT = ROOT / "data/_derived/remaining_20261022/d_census"
rows = json.loads((OUT / "d6_rows.json").read_text(encoding="utf-8"))
disp = json.loads((OUT / "d9_disposition.json").read_text(encoding="utf-8"))
eff = json.loads((OUT / "d10_effects.json").read_text(encoding="utf-8")) if (OUT / "d10_effects.json").exists() else {}
sign_defect = set()
for l in (OUT / "d12_sign19_scan.txt").read_text(encoding="utf-8").splitlines()[1:]:
    m = re.match(r"(\S+) (\d{4}\.\dQ) master=", l)
    if m: sign_defect.add((m.group(1), m.group(2)))

NOTE = {
    "KR0003": "accounting-policy change (systematic allocation of insurance finance income/expense, FSS Q&A); prior-year statements retro-restated (notes in FY2025 H1/Q3 filings)",
    "KR0010": "accounting-policy change (systematic allocation of insurance finance income/expense); 2023 retro-restated (FY2024 annual note, FY2025 annual 'comparative restated')",
    "KR0032": "FY2024 annual note 35 'financial statement restatement': Q&A-driven change of the systematic allocation of insurance finance P&L for interest-sensitive contracts, part of it moved from net income to OCI",
    "KR0087": "FY2024 annual: policy change per FSS Q&A conference / accounting committee for insurance finance income (expense) recognition; comparatives restated",
    "KR0083": "FY2025 Q1-Q3 note 49: change of the systematic allocation of insurance finance income (expense), prior-year statements retro-restated",
    "KR0070": "FY2024 annual note (7) / FY2025 Q1-Q3: policy change per FSS Q&A for insurance finance income (expense) recognition; comparatives restated",
    "KR0079": "FY2024 annual / FY2025 Q1-Q3: cash-flow projection logic error of some participating fixed-annuity products (liability overstated) plus systematic-allocation policy change; retro-restated",
    "KR0099": "systematic-allocation policy change in the prior year; the year before retro-restated (FY2025 annual: 'comparatives of 35th period restated')",
    "KR0005": "error correction: expected-maturity measurement of FVOCI foreign-currency debt instruments (FY2025 Q1/Q2 comparatives restated); 2023 quarters follow the same OCI-debt pattern",
    "KR0104": "error correction: some financial-instrument classification errors at first application of K-IFRS 1109 (FY2024 Q1-Q3 comparatives restated)",
    "KR0009": "restated comparative visible in the FS-API prior column; the note text was not located by the text scan",
    "KR0072": "restated comparative visible in the FS-API prior column; the note text was not located by the text scan",
    "KR0082": "restated comparative visible in the FS-API prior column (1/16/17 move by the same 18.85 eok); the note text was not located by the text scan",
    "KR0001": "restated comparative visible in the prior column; the note text was not located",
    "KR0068": "restated comparative (OCI) visible in the prior column; note text not located",
    "KR0069": "FY2026 H1 note: statement restated per FSS Q&A accounting-policy change (OCI)",
    "KR0071": "restated comparative (OCI) visible in the prior column; note text not located",
    "KR0094": "restated comparative (OCI) visible in the prior column; note text not located",
    "KR1000": "restated comparative visible in the prior column; note text not located",
}
SIGN_NOTE = {
    ("KR0002", "2023.3Q"): "master correct; the later filing prints expense lines with the opposite sign, so _parse mis-signs the later vector (artifact of the prior column)",
    ("KR0150", "2025.1Q"): "master correct; the later filing prints expense lines negative, _parse mis-signs the later vector (artifact of the prior column)",
    ("KR0150", "2025.2Q"): "master correct; the later filing prints expense lines negative, _parse mis-signs the later vector (artifact of the prior column)",
}
SHEET_PANEL_CSM = {1: "IFRS17.html CSM waterfall", 2: "IFRS17.html CSM waterfall; csm_combo NB CSM; index.html bubble X; NB_CSM_multiple", 3: "IFRS17.html CSM waterfall",
                   4: "IFRS17.html CSM waterfall", 5: "IFRS17.html CSM waterfall; PL4 pair gate", 6: "IFRS17.html CSM waterfall; compare.html 기말 CSM; csm_combo; index.html bubble"}

def f1(x): return "" if x is None else f"{x:,.1f}"
def fs(x): return "" if x is None else f"{x:+,.1f}"

out = []
for r in rows:
    key = f"{r['code']}|{r['q']}"; d = disp[key]; nameq = f"{r['name']}|{r['q']}"
    e = eff.get(nameq, {})
    sheets = []
    kind_pre = r["kind"]
    pl_touch = bool(r["real"]) or bool(r["sign_items"])
    if kind_pre == "ALREADY_LATEST": sheets.append("PL_breakdown + CSM_waterfall (both already at the later vector)")
    elif pl_touch: sheets.append("PL_breakdown")
    if kind_pre != "ALREADY_LATEST" and r["csm_state"] in ("DIFF", "NO_PRIOR", "DIFF_ALREADY_LATEST"): sheets.append("CSM_waterfall" + ("(unverified)" if r["csm_state"] == "NO_PRIOR" else ""))
    # --- PL differences
    pl_items = ",".join(map(str, r["real"])) if r["real"] else "none"
    pl_delta = "; ".join(f"{x['item']} {x['name']} {f1(x['master_eok'])}->{f1(x['latest_eok'])} ({fs(x['delta_eok'])}{'' if x['rel'] is None else ', %+.1f%%' % (x['rel'] * 100)})" for x in sorted(r["disp"], key=lambda z: -abs(z["delta_eok"] or 0))[:6])
    if r["sign_items"]:
        pl_items += (" | sign-only items " + ",".join(map(str, r["sign_items"])))
    # --- CSM differences
    cs = r["csm_state"]
    if cs == "DIFF": csm_items = ",".join(map(str, sorted(map(int, r["csm_delta"])))) or "none (<0.05 eok)"
    elif cs == "SAME": csm_items = "none (later-filing prior column equals master)"
    elif cs == "NO_PRIOR": csm_items = "unknown (prior column not extractable from the later filing)"
    elif cs == "n/a": csm_items = "n/a (no CSM waterfall for this company)"
    elif cs == "DIFF_ALREADY_LATEST": csm_items = "none now (master already at the later vector)"
    else: csm_items = cs
    nm = ["opening", "new", "interest", "assump.", "amort.", "closing"]
    csm_delta = "; ".join(f"{i} {nm[int(i) - 1]} {f1(r['csm_now'][int(i) - 1])}->{f1(r['csm_latest'][int(i) - 1])} ({fs(dv)})" for i, dv in sorted(r["csm_delta"].items(), key=lambda kv: -abs(kv[1]))[:4]) if r["csm_delta"] else ""
    # --- cause
    kind = r["kind"]
    if kind == "ALREADY_LATEST":
        cause_class = "already_adopted"; cause = "master equals the later filing's prior column (adopted in an earlier round, gold-backed); the FS-API original column differs"
    elif kind == "API_SIGN_ONLY":
        if (r["name"], r["q"]) in sign_defect:
            cause_class = "master_extraction_error"
            cause = "no restatement (items 1/17/20/22/24 equal). Master items 18/19 carry the wrong sign: the original filing prints 보험금융비용 negative, _parse assumes positive (download-only items, no screen impact). Separate sign-normalisation fix; not a vintage question"
        else:
            cause_class = "api_sign_presentation"
            cause = "no restatement (items 1/17/20/22/24 equal); " + SIGN_NOTE.get((r["code"], r["q"]), "sign presentation differs between the two filings")
    elif kind == "CSM_ONLY_RESTATEMENT":
        cause_class = "restatement"; cause = "CSM waterfall restated in the later filing (PL Tier-1 agrees). " + NOTE.get(r["code"], "")
    else:
        cause_class = "restatement"
        parts = [r["detail"]]
        parts.append(NOTE.get(r["code"], "restated comparative; note text not located"))
        parts.append("basis: FS-API OFS in both filings (no consolidated/separate mix); unit: no scale difference")
        cause = " | ".join(p for p in parts if p)
    # master vintage
    rm = r["rel_master"]; vals = [rm.get(str(i)) for i in (1, 17, 22, 24) if str(i) in rm]
    if kind == "ALREADY_LATEST": mv = "latest (already adopted)"
    elif kind == "CSM_ONLY_RESTATEMENT": mv = "original filing (CSM)"
    elif kind == "API_SIGN_ONLY": mv = "original filing (correct)" if (r["name"], r["q"]) not in sign_defect else "original filing; items 18/19 sign-wrong"
    elif vals and all(v in ("ORIGINAL", "ORIGINAL_NOAPI") for v in vals): mv = "original filing"
    elif vals and all(v == "LATEST" for v in vals): mv = "latest"
    else: mv = "mixed (" + ",".join(f"{i}:{rm.get(str(i))}" for i in (1, 17, 22, 24) if str(i) in rm) + ")"
    # closure
    cl = d.get("closing")
    why = d.get("why_not_closing") or []
    if cl is None: closes = "N/A (nothing to adopt)"
    elif cl: closes = "YES"
    else:
        only_noprior = len(why) == 1 and "could not be extracted" in why[0]
        closes = "UNVERIFIED" if only_noprior else "NO"
    if cl:
        item1_moves = bool({1, 15, 16} & set(r["real"]))
        bridge_txt = ("items 1 and 16 move by offsetting amounts and the LOB bridge 1 = sum of legs + 15 - 16 still closes with the current legs (residual %s mn)" % r["bridge_latest"]) if item1_moves else "items 1/15/16 equal, so the LOB bridge (1 = sum of legs) is unchanged"
        basis = "Tier-1 I1 20=1+17, I2 |22-24|=|23|, I3 31=24+25 pass on the later vector; " + bridge_txt + ("; CSM latest = master" if r["csm_state"] != "n/a" else "; no CSM waterfall")
        if r["gold_overlap"]: basis += "; owner gold on " + ",".join(r["gold_overlap"]) if False else ""
    elif cl is None:
        basis = "-"
    else:
        basis = " ; ".join(why)
    fy = " ".join(f"{k[5:]}:{(v or '--')}" for k, v in r["fy_status"].items())
    seam = ",".join(d.get("seam_stale") or []) or "none"
    # gold
    if r["gold_overlap"]: gold = "OVERLAP items " + ",".join(map(str, r["gold_overlap"])) + " (gold " + ",".join(f"{k}{v}" for k, v in r["gold_val"].items() if int(k) in r["gold_overlap"]) + ")"
    elif r["gold_in_block"]: gold = "in block, no overlap: items " + ",".join(r["gold_in_block"])
    else: gold = "none"
    if d.get("csm_gold_conflict"): gold += " | CSM gold cells " + ",".join(map(str, r["csm_gold"])) + " differ from the later vector"
    # adoption effects
    ident, cont = [], []
    if "pl_bridgebreak" in e and r["kind"] == "RESTATEMENT" and r["bridge_note"].startswith("BREAKS"):
        ident.append("PL Tier-1 adopted alone: " + "; ".join(e["pl_bridgebreak"][:2]))
    if cl and d.get("pl_adoptable"):
        ident.append("gate simulation, all 37 closing buckets adopted together (234 cells): master_tables pl_bridge 3697P/23F/0NEW, tax22_src 282P/0F, csm_amort_identity 387P/0F unchanged; data_contract RED 1 (=baseline); only PL_OCI_VS_BS_AOCI YELLOW 23->26 (IFRS17_BS AOCI still original vintage)")
        if "pl_closing" in e:
            ident.append("; ".join(e["pl_closing"][:2]))
    if r["pair"] is not None:
        ident.append("CSM-only adoption: PL4 vs CSM5 residual %s eok (now %s) -> CSM_AMORT_IDENTITY %s unless PL4 is read from the later filing too" % (r["pair"]["resid_csm_only_latest"], r["pair"]["resid_now"], "FAIL" if not r["pair"]["ok_csm_only"] else "still passes"))
    for tag in ("csm_a51", "csm_chain", "csm_full"):
        if tag in e:
            ident.append(f"[{tag}] " + "; ".join(e[tag][:2]))
    nameany = f"{r['name']}|*"
    ec = eff.get(nameany, {})
    for tag in ("csm_a51_cont", "csm_chain_cont", "csm_full_cont"):
        if tag in ec: cont.append(f"[{tag.replace('_cont', '')}] " + "; ".join(sorted(set(ec[tag]))[:3]))
    if d.get("seam_stale"): cont.append("single-quarter (값_당분기) seam: same-FY neighbour(s) %s stay at the other vintage -> those derived cells must be blanked" % seam)
    if not ident: ident.append("none")
    if not cont: cont.append("none found")
    # panels
    panels = sorted({str(x["panel"]) for x in r["disp"]} - {"download-only"})
    if r["disp"] and any(str(x["panel"]) == "download-only" for x in r["disp"]): panels.append("xlsx 손익분해PL / public_exports")
    for i in r["csm_delta"]: panels.extend(SHEET_PANEL_CSM[int(i)].split("; "))
    panels = sorted(set(panels))
    out.append({
        "scope": r["scope"], "code": r["code"], "company": r["name"], "quarter": r["q"], "sheets": " + ".join(sheets) or "-",
        "pl_items_differ": pl_items, "pl_delta_eok_top6": pl_delta, "csm_items_differ": csm_items, "csm_delta_eok": csm_delta,
        "cause_class": cause_class, "cause_detail": cause, "master_vintage": mv,
        "latest_vector_closes_block": closes, "closure_basis": basis, "fy_block_quarters(E=equal D=differs)": fy, "seam_neighbours_stale": seam,
        "gold_cells": gold, "adoption_effect_identity": " | ".join(ident), "adoption_effect_continuity": " | ".join(cont),
        "panels_showing_it": "; ".join(panels) if panels else "none (no displayed number changes)",
        "screen_change_class": d["screen"], "screen_change_top3": d["screen_text"],
        "disposition": {"SAFE": "SAFE_NOW", "OWNER": "OWNER_DECISION", "STAY": "STAY"}[d["disposition"]], "disposition_reason": d["why"],
        "pl_restatement_note": "", "evidence": "d1_scan.json (FS-API original vs later prior, per item); d5_buckets.json; d6_rows.json; d9_disposition.json; gates g_*"})
cols = [k for k in out[0].keys() if k != "pl_restatement_note"]
order = {"A51": 0, "ADDL_SIBLING": 1, "ADDL_CSM_ONLY": 2, "ADDL_OCI_ONLY": 3}
out.sort(key=lambda o: (order[o["scope"]], o["company"], o["quarter"]))
with open(OUT / "d_census_table.csv", "w", encoding="utf-8-sig", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore"); w.writeheader(); w.writerows([o for o in out if o["scope"] == "A51"])
with open(OUT / "d_census_addl.csv", "w", encoding="utf-8-sig", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore"); w.writeheader(); w.writerows([o for o in out if o["scope"] != "A51"])
a = [o for o in out if o["scope"] == "A51"]
c = Counter
txt = []
txt.append(f"rows {len(out)}; A51 {len(a)}")
txt.append("A51 disposition: " + str(c(o["disposition"] for o in a)))
txt.append("A51 closes: " + str(c(o["latest_vector_closes_block"] for o in a)))
txt.append("A51 cause: " + str(c(o["cause_class"] for o in a)))
txt.append("A51 (disposition, screen): " + str(c((o["disposition"], o["screen_change_class"]) for o in a)))
txt.append("ADDL: " + str(c((o["scope"], o["disposition"]) for o in out if o["scope"] != "A51")))
(OUT / "d11_summary.txt").write_text("\n".join(txt) + "\n", encoding="utf-8")
print("\n".join(txt))
