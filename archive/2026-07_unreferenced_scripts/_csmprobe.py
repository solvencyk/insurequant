# -*- coding: utf-8 -*-
"""Scratch probe: a SUM-confirmed-by-grand-total annual rule.
Cluster-picks (별도, one per opening-cluster). SUM them only if some raw candidate block
~= that sum (a disclosed grand total confirms the picks form a complete segment
decomposition); else take MIN (별도/연결 pair). Verify against every annual combined-agn
company so no gold (한화생명·삼성생명·메리츠·농협·교보·푸본) regresses. NOT pipeline."""
from __future__ import annotations
import sys
import json
from pathlib import Path

sys.path.insert(0, ".")
import scripts.build_csm_waterfall_master as C


def _norm(sts):
    allv = [v for s in sts for v in s.values() if v is not None]
    mag = max((abs(v) for v in allv), default=0.0)
    udiv = 1e6 if mag > 1e10 else (1e3 if mag > 1e8 else 1.0)
    return lambda v: (v or 0) / udiv / 100.0


def annual_pick(cur, norm):
    """cur = current-period stage candidates (prior dropped). Returns chosen stages."""
    picks = C._opening_clusters(cur)
    if len(picks) >= 2:
        psum = sum(norm(p.get(1)) for p in picks)
        # confirm: some raw candidate ~= the segment-sum (a disclosed grand total)?
        confirmed = any(
            abs(psum) > 1 and abs(norm(s.get(1)) - psum) / abs(psum) <= 0.01 for s in cur)
        if confirmed:
            return {no: sum((p.get(no) or 0) for p in picks) for no in C.STAGE_KEYS}, "SUM"
    return C._comparable_min(cur), "MIN"


def main():
    m = json.loads(Path("data/dart/viz/csm_waterfall_master_diag.json").read_text(encoding="utf-8"))
    cov = json.loads(Path("data/dart/viz/csm_waterfall_master_cov.json").read_text(encoding="utf-8"))
    nm = {r["원보험사코드"]: r["원수사명"] for r in m}
    curop = {(r["원보험사코드"], r["공시분기"]): r["값"] for r in m if r["항목번호"] == 1}
    for key, src in sorted(cov.items()):
        code, q = key.split("|")
        if not q.endswith("4Q") or src not in ("combined", "combined-agn"):
            continue
        ds = [p for p in Path(".").glob(f"data/dart/FY{q[:4]}_Q4/raw/{code}_*") if p.is_dir()]
        if not ds:
            continue
        cands, seg = C._seg_cands(C.blocks_for_dir(ds[0], nm[code]))
        sts = [t[0] for t in cands]
        norm = _norm(sts)
        cur = C._drop_prior(sts)
        if not cur:
            continue
        out, how = annual_pick(cur, norm)
        newo = round(norm(out.get(1)), 1)
        old = curop.get((code, q))
        flag = "" if (old is not None and abs(newo - old) <= max(1.0, abs(old) * 0.01)) else "  <<< CHANGED"
        print(f"{nm[code][:10]:10} {code} {q} how={how:3} old={old!s:>10} new={newo!s:>10}{flag}")


if __name__ == "__main__":
    main()
