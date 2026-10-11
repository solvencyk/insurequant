#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""2026-10-11 BS/PL follow-up (parser/ifrs17), step 3b: source triage of the consecutive-duplicate records.

Reads consecutive_duplicates_20261011.json (scripts/bspl_followup_consecutive_dups.py) and attaches independent evidence per cell:
  BS item 30 (자본금)      equity_scan.json observations (equity table c0/c1/c2 and the picked 8-1) -> source prints the same capital
  BS other items           Stage-B candidate records (status EXISTS_SAME = the disclosure line of that quarter prints this value, at the
                           disclosure's rounding precision)
  PL items 1/16/22/23/24   pl_candidates (own-filing summary PL, YTD) -> EXISTS_SAME = the disclosure of that quarter prints this YTD
  PL other items           no disclosure lineage (DART FS-API / Tier-2 notes): left for the manual look (evidence field says so)
Verdicts per record: CONFIRMED (every quarter of the run is reproduced by an own-filing observation) | PARTIAL | NO_EVIDENCE | MISMATCH.
Output: consecutive_duplicates_triage_20261011.json in bspl_followup_20261011/ (+ printed summary).  Read-only.
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.stdout.reconfigure(encoding="utf-8")
W = ROOT / "data" / "_derived" / "bspl_followup_20261011"
G = ROOT / "data" / "_derived" / "bspl_granularity_20261011"


def main():
    dups = json.loads((W / "consecutive_duplicates_20261011.json").read_text(encoding="utf-8"))["records"]
    eq = json.loads((W / "equity_scan.json").read_text(encoding="utf-8"))
    eq_idx = defaultdict(list)
    for r in eq:
        if r["item"] == 30:
            eq_idx[(r["code"], r["quarter"])].append(r)
    cand_cache, plc_cache = {}, {}

    def bs_cand(code):
        if code not in cand_cache:
            p = G / "candidates" / f"{code}.json"
            cand_cache[code] = {(c["item"], c["quarter"]): c for c in json.loads(p.read_text(encoding="utf-8"))["candidates"]} if p.exists() else {}
        return cand_cache[code]

    def pl_cand(code):
        if code not in plc_cache:
            p = G / "pl_candidates" / f"{code}.json"
            d = defaultdict(list)
            if p.exists():
                for c in json.loads(p.read_text(encoding="utf-8"))["candidates"]:
                    d[(int(c["item"]), c["quarter"])].append(c)
            plc_cache[code] = d
        return plc_cache[code]

    out = []
    for r in dups:
        ev = []
        if r["master"] == "BS" and r["item"] == 30:
            for q in r["quarters"]:
                obs = eq_idx.get((r["code"], q), [])
                own = [o for o in obs if o["col"] == 0 and o["pdf_quarter"] == q]
                same = [o for o in obs if o.get("within_rounding")]
                ev.append({"quarter": q, "own_filing_obs": len(own), "any_obs": len(obs), "reproduced": bool(same),
                           "own_reproduced": any(o.get("within_rounding") for o in own)})
        elif r["master"] == "BS":
            cs = bs_cand(r["code"])
            for q in r["quarters"]:
                c = cs.get((r["item"], q))
                ev.append({"quarter": q, "status": c["status"] if c else None,
                           "value_mn": c.get("value_mn") if c else None, "reproduced": bool(c and c["status"] == "EXISTS_SAME"),
                           "kind": c.get("kind") if c else None, "unit": c.get("unit") if c else None})
        elif r["item"] in (1, 16, 22, 23, 24) and isinstance(r["item"], int) and r["field"] == "값":
            pc = pl_cand(r["code"])
            for q in r["quarters"]:
                cs = [c for c in pc.get((r["item"], q), []) if c.get("how") == "own_summary" or c.get("how", "").startswith("own")]
                ok = [c for c in cs if c.get("status") == "EXISTS_SAME"]
                ev.append({"quarter": q, "n_own": len(cs), "reproduced": bool(ok), "statuses": sorted({c.get("status") for c in cs})})
        else:
            ev.append({"note": "no disclosure lineage for this item/field (DART FS-API or Tier-2 note, or a derived 당분기): manual source look"})
        if all("reproduced" in e for e in ev):
            n = sum(1 for e in ev if e["reproduced"])
            verdict = "CONFIRMED" if n == len(ev) else ("PARTIAL" if n else "NO_EVIDENCE")
        else:
            verdict = "MANUAL"
        out.append({**{k: r[k] for k in ("master", "code", "name", "item", "item_name", "field", "quarters", "value", "class")},
                    "evidence": ev, "verdict": verdict})
    (W / "consecutive_duplicates_triage_20261011.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    cnt = defaultdict(int)
    for o in out:
        cnt[(o["master"], o["verdict"])] += 1
    print(dict(cnt))
    for o in out:
        if o["verdict"] != "CONFIRMED" and not (o["master"] == "BS" and o["item"] == 30):
            print(o["master"], o["code"], o["name"][:8], o["item"], o["item_name"][:14], o["field"], o["quarters"][0], "..", o["quarters"][-1],
                  o["value"], o["verdict"])
    bad30 = [o for o in out if o["master"] == "BS" and o["item"] == 30 and o["verdict"] != "CONFIRMED"]
    print("자본금 runs not CONFIRMED:", len(bad30))
    for o in bad30:
        print("  ", o["code"], o["name"][:8], o["quarters"][0], "..", o["quarters"][-1], o["value"], o["verdict"],
              [(e["quarter"], e["own_filing_obs"], e["any_obs"], e["reproduced"]) for e in o["evidence"]][:6])


if __name__ == "__main__":
    main()
