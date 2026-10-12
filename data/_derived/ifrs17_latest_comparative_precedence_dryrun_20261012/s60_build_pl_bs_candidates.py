"""Read-only: build candidate PL_breakdown.json / IFRS17_BS.json byte-files (under cand/) in which the Tier-1 PL items / year-end BS main items of every
non-gold block with a REAL difference are replaced by the LATEST comparative column.  The repo masters are never touched; the files are served to the
live gates through gate_overlay.py.

PL  : items taken from pl_tier1_scan_refined.csv (kind REAL_SMALL / REAL_LARGE, class RESTATED_STALE) for blocks whose verdict (pl_block_verdicts.csv) is
      '후보 불완전...' ; 값_당분기 recomputed with build_root_masters._flow_dangi over the YTD chain of each (company, item).
BS  : cells of blocks with verdict '최신 채택...' in bs_block_verdicts.csv (stale cells only).
"""
from __future__ import annotations

import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import lib_dryrun as D  # noqa: E402

ROOT = D.ROOT
sys.path.insert(0, str(ROOT / "scripts"))
import build_root_masters as BR  # noqa: E402

(HERE / "cand").mkdir(exist_ok=True)

# ----------------------------------------------------------------------------- PL
pl_rows = json.loads((ROOT / "PL_breakdown.json").read_text(encoding="utf-8"))
verd = {(r["kr"], r["quarter"]): r["verdict"] for r in csv.DictReader(open(HERE / "pl_block_verdicts.csv", encoding="utf-8-sig"))}
refined = [r for r in csv.DictReader(open(HERE / "pl_tier1_scan_refined.csv", encoding="utf-8-sig")) if r["kind"] in ("REAL_SMALL", "REAL_LARGE")]
adopt = {}
for r in refined:
    if verd.get((r["kr"], r["quarter"]), "").startswith("후보 불완전"):
        adopt[(r["kr"], int(r["item"]), r["quarter"])] = float(r["later"])
idx = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r for r in pl_rows}
changed = 0
for key, v in adopt.items():
    if key in idx and idx[key]["값"] is not None and idx[key]["값"] != v:
        idx[key]["값"] = v
        changed += 1
ytd = defaultdict(dict)
for r in pl_rows:
    ytd[(r["원보험사코드"], r["항목번호"])][r["공시분기"]] = r["값"]
touched = {(k[0], k[1]) for k in adopt}
for r in pl_rows:
    if (r["원보험사코드"], r["항목번호"]) not in touched:      # untouched series keep the live 값_당분기 byte for byte
        continue
    v = r.get("값")
    r["값_당분기"] = BR._flow_dangi(ytd[(r["원보험사코드"], r["항목번호"])], r["공시분기"]) if v is not None else None
(HERE / "cand" / "PL_breakdown.TIER1.json").write_text(json.dumps(pl_rows, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
print("PL candidate: blocks", len({(k[0], k[2]) for k in adopt}), "cells changed", changed, "rows", len(pl_rows))

# ----------------------------------------------------------------------------- BS
bs_rows = json.loads((ROOT / "IFRS17_BS.json").read_text(encoding="utf-8"))
bverd = {(r["kr"], r["quarter"]): r["verdict"] for r in csv.DictReader(open(HERE / "bs_block_verdicts.csv", encoding="utf-8-sig"))}
bscan = [r for r in csv.DictReader(open(HERE / "bs_4q_scan.csv", encoding="utf-8-sig")) if r["cls"] == "RESTATED_STALE"]
bidx = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r for r in bs_rows}
bchanged = 0
for r in bscan:
    if bverd.get((r["kr"], r["quarter"]), "").startswith("최신 채택") and r["later"] not in ("", "None"):
        key = (r["kr"], int(r["item"]), r["quarter"])
        if key in bidx:
            nv = float(r["later"])
            if bidx[key]["값"] != nv:
                bidx[key]["값"] = nv
                bchanged += 1
(HERE / "cand" / "IFRS17_BS.YEAREND.json").write_text(json.dumps(bs_rows, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
print("BS candidate: cells changed", bchanged, "rows", len(bs_rows))
