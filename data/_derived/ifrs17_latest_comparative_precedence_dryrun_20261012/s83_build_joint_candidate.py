"""Read-only: candidate masters for the JOINT (CSM + PL) blocks - the companies whose CSM latest-comparative block closes only together with the PL companion block
(CSM_AMORT_IDENTITY couples PL item 4 and waterfall item 5).  The repo masters are never touched; candidates are served to the live gates by gate_overlay.py.

  CSM_waterfall.JOINT.json : live master, waterfall items 1..6 of the joint blocks replaced by the LATEST comparative vector (cand/csm_adopt_overlay.json)
  PL_breakdown.JOINT.json  : live master, PL items 1..32 of the joint blocks replaced by the LATEST comparative block (cand/pl_latest_blocks.json,
                              Tier-1 = FS-API comparative column OFS, Tier-2 = production chain on the comparative columns).  Block replaced as a whole:
                              a cell present in the current block but absent in the latest block is reported and (for the candidate) blanked.
  usage: python s83_build_joint_candidate.py KR0008|2023.1Q KR0008|2023.2Q ...   [--tag JOINT] [--pl-only KR0011|2023.1Q ...]
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import build_root_masters as BR  # noqa: E402  (pure helpers only)

args = sys.argv[1:]
tag = "JOINT"
pl_only = []
csm_only = []
mode = "joint"
joint = []
i = 0
while i < len(args):
    a = args[i]
    if a == "--tag":
        tag = args[i + 1]
        i += 2
        continue
    if a in ("--pl-only", "--csm-only", "--joint"):
        mode = a[2:].replace("-", "_")
        i += 1
        continue
    {"joint": joint, "pl_only": pl_only, "csm_only": csm_only}[mode].append(a)
    i += 1

csm_ov = json.loads((HERE / "cand" / "csm_adopt_overlay.json").read_text(encoding="utf-8"))
plb = json.loads((HERE / "cand" / "pl_latest_blocks.json").read_text(encoding="utf-8"))
db = json.loads((HERE / "cand" / "db_pl_block_lat.json").read_text(encoding="utf-8"))          # {quarter: {item: value}} for KR0011

csm_rows = json.loads((ROOT / "CSM_waterfall.json").read_text(encoding="utf-8"))
pl_rows = json.loads((ROOT / "PL_breakdown.json").read_text(encoding="utf-8"))
cidx = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r for r in csm_rows}
pidx = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r for r in pl_rows}
tmpl = {}
for r in pl_rows:
    tmpl.setdefault((r["원보험사코드"], r["항목번호"]), r)
tmpl_any = {}
for r in pl_rows:
    tmpl_any.setdefault(r["항목번호"], r)

report = {"csm_changed": 0, "pl_changed": 0, "pl_added": 0, "pl_blanked": 0, "details": []}


def pl_block_for(key):
    kr, q = key.split("|")
    if kr == "KR0011" and q in db:
        return {int(k): v for k, v in db[q].items()}, "db_pl_block_lat.json"
    for suffix in ("sumcheck", "prod"):
        b = plb.get(f"{kr}|{q}|{suffix}")
        if b:
            return {int(k): v for k, v in b["block"].items()}, f"pl_latest_blocks.json[{suffix}]"
    return None, None


def apply_pl(kr, q, block, src):
    changed = added = blanked = 0
    for it in range(1, 33):
        key = (kr, it, q)
        lat = block.get(it)
        cur_row = pidx.get(key)
        cur = cur_row["값"] if cur_row else None
        if lat is None:
            if cur is not None:
                cur_row["값"] = None
                blanked += 1
                report["details"].append(f"{kr} {q} item {it}: current {cur} absent in latest block -> blanked in candidate")
            continue
        if cur_row is None:
            t = tmpl.get((kr, it)) or tmpl_any.get(it)
            if t is None:
                continue
            nr = {k: t[k] for k in t if k not in ("값", "값_당분기")}
            nr["원보험사코드"] = kr
            nr["공시분기"] = q
            nr["값"] = lat
            nr["값_당분기"] = None
            pl_rows.append(nr)
            pidx[key] = nr
            added += 1
        elif cur != lat:
            cur_row["값"] = lat
            changed += 1
    report["pl_changed"] += changed
    report["pl_added"] += added
    report["pl_blanked"] += blanked
    print(f"  PL {kr} {q}: changed {changed} added {added} blanked {blanked} (source {src})")


touched_pl = set()
csm_cos_extra = set()
for key in joint:
    kr, q = key.split("|")
    v = csm_ov.get(key)
    if v is None:
        print("NO CSM overlay for", key)
    else:
        n = 0
        for k, x in v.items():
            ck = (kr, int(k), q)
            if x is not None and ck in cidx and cidx[ck]["값"] != x:
                cidx[ck]["값"] = x
                n += 1
        report["csm_changed"] += n
        print(f"  CSM {kr} {q}: {n} cells changed")
    blk, src = pl_block_for(key)
    if blk is None:
        print("NO PL block for", key)
    else:
        apply_pl(kr, q, blk, src)
        touched_pl.add((kr, q))
for key in pl_only:
    kr, q = key.split("|")
    blk, src = pl_block_for(key)
    if blk is None:
        print("NO PL block for", key)
        continue
    apply_pl(kr, q, blk, src)
    touched_pl.add((kr, q))
for key in csm_only:
    kr, q = key.split("|")
    v = csm_ov.get(key)
    if v is None:
        print("NO CSM overlay for", key)
        continue
    n = 0
    for k, x in v.items():
        ck = (kr, int(k), q)
        if x is not None and ck in cidx and cidx[ck]["값"] != x:
            cidx[ck]["값"] = x
            n += 1
    report["csm_changed"] += n
    csm_cos_extra.add(kr)
    print(f"  CSM-only {kr} {q}: {n} cells changed")

# 값_당분기 : recompute only the series touched (other series keep the live bytes)
ytd_c = defaultdict(dict)
for r in csm_rows:
    ytd_c[(r["원보험사코드"], r["항목번호"])][r["공시분기"]] = r["값"]
cos_c = {k.split("|")[0] for k in joint} | csm_cos_extra
for r in csm_rows:
    code, item, q, v = r["원보험사코드"], r["항목번호"], r["공시분기"], r["값"]
    if code not in cos_c:
        continue
    if v is None:
        dangi = None
    elif item == BR.CSM_CLOSE:
        dangi = v
    elif item == BR.CSM_OPEN:
        p = BR._prev_q(q)
        dangi = v if p is None else ytd_c[(code, BR.CSM_CLOSE)].get(p)
    else:
        dangi = BR._flow_dangi(ytd_c[(code, item)], q)
    r["값_당분기"] = round(dangi, 6) if isinstance(dangi, (int, float)) else dangi
ytd_p = defaultdict(dict)
for r in pl_rows:
    ytd_p[(r["원보험사코드"], r["항목번호"])][r["공시분기"]] = r["값"]
cos_p = {k for k, _ in touched_pl}
for r in pl_rows:
    if r["원보험사코드"] not in cos_p:
        continue
    v = r.get("값")
    r["값_당분기"] = BR._flow_dangi(ytd_p[(r["원보험사코드"], r["항목번호"])], r["공시분기"]) if v is not None else None

if joint or csm_only:
    (HERE / "cand" / f"CSM_waterfall.{tag}.json").write_text(json.dumps(csm_rows, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
(HERE / "cand" / f"PL_breakdown.{tag}.json").write_text(json.dumps(pl_rows, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
print({k: v for k, v in report.items() if k != "details"})
for d in report["details"][:40]:
    print("   ", d)
