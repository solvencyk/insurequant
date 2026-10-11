#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""2026-10-12 (orchestrator decision 3): put the 49 re-sweep BS cells into the overlay data/dart/viz/bs_manual_overrides.json that scripts/build_ifrs17_bs.py re-applies LAST,
so a future builder run reproduces them.  Cell-level UPSERT of exactly the cells of data/_derived/bs_from_disclosure_parts/KR11*_agent_resweep.json (the durable part files) --
this is what scripts/merge_bs_disclosure_parts.py would do for these cells, without rewriting the other ~3,200 sidecar/overlay cells (that script rewrites the whole sidecar
and every overlay entry with LF/ordering of its own).  Guard: a key may be absent or already identical.  Backup first.

  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/reinsurer_resweep_bs_overlay.py [--apply]
"""
from __future__ import annotations

import json
import shutil
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.stdout.reconfigure(encoding="utf-8")
from bspl_granularity_load_bs import dumps, load_json_exact, safe_write  # noqa: E402

OVERRIDES = ROOT / "data/dart/viz/bs_manual_overrides.json"
PARTS = sorted((ROOT / "data/_derived/bs_from_disclosure_parts").glob("KR11*_agent_resweep.json"))
BACKUP = ROOT / "data/_derived/reinsurer_resweep_backup_20261012/overlay"


def main():
    ov, raw = load_json_exact(OVERRIDES, 2, "\n")
    cells = {}
    for p in PARTS:
        cells.update(json.loads(p.read_text(encoding="utf-8"))["cells"])
    new = {k: {"값": v["값"], "근거": v["근거"]} for k, v in cells.items()}
    conflict = [k for k, v in new.items() if k in ov["cells"] and ov["cells"][k] != v]
    if conflict:
        raise SystemExit(f"ABORT: overlay already holds different entries for {conflict[:3]}")
    todo = [k for k in new if k not in ov["cells"]]
    print(f"part files {[p.name for p in PARTS]}: {len(new)} cells; to add {len(todo)}; already identical {len(new) - len(todo)}; overlay cells {len(ov['cells'])} -> {len(ov['cells']) + len(todo)}")
    if not apply_flag():
        print("dry-run")
        return
    BACKUP.mkdir(parents=True, exist_ok=True)
    if (BACKUP / OVERRIDES.name).exists():
        raise SystemExit("ABORT: overlay backup exists")
    shutil.copy2(OVERRIDES, BACKUP / OVERRIDES.name)
    before = {k: json.dumps(v, ensure_ascii=False, sort_keys=True) for k, v in ov["cells"].items()}
    for k in todo:
        ov["cells"][k] = new[k]
    ov["_readme"].append(f"[{time.strftime('%Y-%m-%d')}] 재보사 PL/BS 공란 재스윕(inbox/parser/20261012T0110Z) -- {len(todo)}칸 신규(KR1101 24 · KR1103 11·12·20·24 · KR1104 11·24 · KR1107 20·24), "
                         "scripts/reinsurer_resweep_bs_overlay.py 로 파트 파일(KR11*_agent_resweep.json)에서 셀단위 UPSERT. 계보: data/_derived/bs_from_disclosure.json.")
    if OVERRIDES.read_bytes() != raw:
        raise SystemExit("ABORT: overlay changed since read")
    safe_write(OVERRIDES, dumps(ov, 2, "\n"))
    chk = json.loads(OVERRIDES.read_bytes().decode("utf-8"))["cells"]
    bad = [k for k, s in before.items() if json.dumps(chk.get(k), ensure_ascii=False, sort_keys=True) != s]
    if bad or len(chk) != len(before) + len(todo):
        raise SystemExit(f"VERIFY FAILED {bad[:3]}")
    print(f"APPLIED: overlay +{len(todo)} cells; the other {len(before)} identical")


def apply_flag():
    return "--apply" in sys.argv


if __name__ == "__main__":
    main()
