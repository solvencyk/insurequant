"""f0_build_candidate.py OUT.json [BLOCK,BLOCK,...]  -- candidate master = live master + the final plans (all 16 by default), written to OUT.json
(canonical master bytes).  The live master is not touched."""
import copy
import sys
from pathlib import Path

sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/kics_latest_prior_apply_20261012")
from lib_apply import *  # noqa: F401,F403,E402

utf8_stdout()
out = Path(sys.argv[1])
names = sys.argv[2].split(",") if len(sys.argv) > 2 else APPLIED
rows = read_rows()
live_sha = sha_file(MASTER)
plans = merge_plans(names)
cand = copy.deepcopy(rows)
n = apply_to_rows(cand, plans["edits"])
out.parent.mkdir(parents=True, exist_ok=True)
out.write_bytes(dump_master_bytes(cand))
print(f"candidate {out.name}: {len(names)} blocks, {n} cells, live sha {live_sha[:12]}, candidate sha {sha_file(out)[:12]}")
