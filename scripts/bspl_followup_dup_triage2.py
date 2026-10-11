#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""2026-10-11 BS/PL follow-up (parser/ifrs17), step 3c: second-pass source triage of the PL duplicate records the first pass left as MANUAL.

  (a) disclosure-lineage items (1/16/22/23/24), 값_당분기 runs: the quarterly figure is a YTD difference, so equal consecutive quarterly
      figures are arithmetic when the YTD cells of the quarters involved are source-confirmed (pl_candidates EXISTS_SAME) and the master's
      값_당분기 equals the YTD difference  -> CONFIRMED_ARITHMETIC
  (b) DART FS-API-lineage items (21, 28, 29, 32 ...): the cached FS-API response of every quarter of the run is re-parsed with the
      production parser (fetch_dart_fs._parse, cache only, no network) and compared with the master; equal -> CONFIRMED_BY_FS_CACHE
      (the equality is in the DART data, not a downstream copy); a differing quarter -> MISMATCH (copy candidate)
  (c) Tier-2 note items (5, 10): marked NOTE_ITEM (needs the raw filing; looked at by hand)
Output: consecutive_duplicates_triage2_20261011.json in bspl_followup_20261011/.  Read-only.  Run from the repo root (fetch_dart_fs uses cwd).
"""
from __future__ import annotations

import json
import os
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
sys.path.insert(0, str(ROOT))
sys.stdout.reconfigure(encoding="utf-8")

from scripts import fetch_dart_fs as F  # noqa: E402

W = ROOT / "data" / "_derived" / "bspl_followup_20261011"
G = ROOT / "data" / "_derived" / "bspl_granularity_20261011"
REP = {"1Q": "11013", "2Q": "11012", "3Q": "11014", "4Q": "11011"}
NAME_FIX = {"KR0099": "KB라이프생명"}


def qprev(q):
    y, n = int(q[:4]), int(q[5])
    return f"{y - 1}.4Q" if n == 1 else f"{y}.{n - 1}Q"


def cache_t1(code, name, q):
    cc = F.resolve_corp(NAME_FIX.get(code, name))
    if not cc:
        return None
    reprt = REP[q[5:]]
    for fs in ("OFS", "CFS"):
        p = F.CACHE / f"{cc}_{q[:4]}_{reprt}_{fs}.json"
        if not p.exists():
            continue
        t1 = F._parse(json.loads(p.read_text(encoding="utf-8")), q[5:] == "4Q")
        if t1:
            return t1
    return None


def main():
    pl = json.loads((ROOT / "PL_breakdown.json").read_text(encoding="utf-8"))
    mv = {(r["원보험사코드"], str(r["항목번호"]), r["공시분기"]): (r.get("값"), r.get("값_당분기")) for r in pl}
    tri = json.loads((W / "consecutive_duplicates_triage_20261011.json").read_text(encoding="utf-8"))
    plc = {}

    def pl_cand(code):
        if code not in plc:
            p = G / "pl_candidates" / f"{code}.json"
            d = defaultdict(list)
            if p.exists():
                for c in json.loads(p.read_text(encoding="utf-8"))["candidates"]:
                    d[(int(c["item"]), c["quarter"])].append(c)
            plc[code] = d
        return plc[code]

    out = []
    for r in tri:
        if r["master"] != "PL" or r["verdict"] != "MANUAL":
            continue
        code, item, fld, qs = r["code"], r["item"], r["field"], r["quarters"]
        rec = {k: r[k] for k in ("code", "name", "item", "item_name", "field", "quarters", "value")}
        if isinstance(item, int) and item in (1, 16, 22, 23, 24):
            pc = pl_cand(code)
            qq = sorted(set(qs) | {qprev(q) for q in qs if q[5] != "1"})
            ev = []
            for q in qq:
                cs = [c for c in pc.get((item, q), []) if str(c.get("how", "")).startswith("own")]
                ev.append({"quarter": q, "ytd": mv.get((code, str(item), q), (None, None))[0],
                           "own_status": sorted({c.get("status") for c in cs}) or None})
            arith = True
            for q in qs:
                ytd, qtr = mv[(code, str(item), q)]
                prev = mv.get((code, str(item), qprev(q)), (None, None))[0] if q[5] != "1" else 0.0
                if prev is None or ytd is None or qtr is None or abs((ytd - prev) - qtr) > 1e-6:
                    arith = False
            confirmed = all(e["own_status"] and "EXISTS_SAME" in e["own_status"] for e in ev if e["ytd"] is not None)
            rec.update(evidence=ev, arithmetic_ok=arith,
                       verdict="CONFIRMED_ARITHMETIC" if (fld == "값_당분기" and arith and confirmed) else "CHECK")
        elif isinstance(item, int) and item in (21, 28, 29, 32):
            ev = []
            ok = True
            for q in sorted(set(qs) | ({qprev(q) for q in qs if q[5] != "1"} if fld == "값_당분기" else set())):
                t1 = cache_t1(code, r["name"], q)
                cv = None if t1 is None else t1.get(item)
                mval = mv.get((code, str(item), q), (None, None))[0]
                same = cv is not None and mval is not None and abs(cv - mval) <= 0.0005
                ok = ok and same
                ev.append({"quarter": q, "master_ytd": mval, "fs_cache_ytd": cv, "equal": same})
            rec.update(evidence=ev, verdict="CONFIRMED_BY_FS_CACHE" if ok else "MISMATCH_OR_NOCACHE")
        else:
            rec.update(evidence=[{"note": "Tier-2 note-derived item (raw filing XML only): hand check"}], verdict="NOTE_ITEM")
        out.append(rec)
    (W / "consecutive_duplicates_triage2_20261011.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    cnt = defaultdict(int)
    for o in out:
        cnt[o["verdict"]] += 1
    print(dict(cnt))
    for o in out:
        print(o["verdict"], o["code"], o["name"][:8], o["item"], o["item_name"][:12], o["field"], o["quarters"][0], "..", o["quarters"][-1], o["value"])
        if o["verdict"] in ("MISMATCH_OR_NOCACHE", "CHECK"):
            for e in o["evidence"]:
                print("     ", e)


if __name__ == "__main__":
    main()
