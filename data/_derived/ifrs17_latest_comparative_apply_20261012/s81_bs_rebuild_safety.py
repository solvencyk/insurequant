"""BS rebuild-safety: run scripts/build_ifrs17_bs.py main() IN-PROCESS with OUT / CARRY_OUT pointed at temp files and OVERRIDES pointed at the candidate overlay
(the repo files are never written).  The builder output must equal the candidate master row for row (the live master equals the builder output at HEAD:
sha256 0d88b860.. = the BS golden).  usage: s81_bs_rebuild_safety.py <simdir>"""
import json, sys, tempfile
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sim = Path(sys.argv[1])
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
import scripts.build_ifrs17_bs as B

tmp = Path(tempfile.mkdtemp(prefix="bs_rb_"))
B.OUT = tmp / "IFRS17_BS.json"
B.CARRY_OUT = tmp / "bs_carry_forward_cells.json"
B.OVERRIDES = sim / "data/dart/viz/bs_manual_overrides.json"
B.main()
out = json.loads(B.OUT.read_text(encoding="utf-8"))
cand = json.loads((sim / "IFRS17_BS.json").read_text(encoding="utf-8"))
live = json.loads((ROOT / "IFRS17_BS.json").read_text(encoding="utf-8"))
key = lambda r: (r["원보험사코드"], r["항목번호"], r["공시분기"])
oi, ci, li = {key(r): r for r in out}, {key(r): r for r in cand}, {key(r): r for r in live}
print("rows builder/candidate/live:", len(out), len(cand), len(live))
d_cand = {k: (ci.get(k, {}).get("값"), oi.get(k, {}).get("값")) for k in set(ci) | set(oi) if ci.get(k) != oi.get(k)}
d_live = {k: (li.get(k, {}).get("값"), oi.get(k, {}).get("값")) for k in set(li) | set(oi) if li.get(k) != oi.get(k)}
print("builder output vs CANDIDATE master: differing rows", len(d_cand), list(d_cand.items())[:6])
print("builder output vs LIVE master (expected = exactly the plan cells):", len(d_live))
plan = json.loads((HERE / "plan_final.json").read_text(encoding="utf-8"))
pk = {(c["code"], c["item"], c["quarter"]) for c in plan["cells"] if c["master"] == "IFRS17_BS"}
print("   differing rows that are plan cells:", len(set(d_live) & pk), "/", len(pk), "; other differing rows:", len(set(d_live) - pk), list(set(d_live) - pk)[:5])
