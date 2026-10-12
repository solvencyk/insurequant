"""Dry run of scripts/build_ifrs17_bs.py (adapted from data/_derived/reinsurer_resweep_20261012/dry_build_bs.py): OUT and CARRY_OUT are redirected to a temp dir, so
IFRS17_BS.json is NOT touched.  Compares the built rows with the live master and checks that the 6 Chubb item-20 cells (D2) come out of the builder (overlay applied last)."""
import hashlib, importlib, json, sys, tempfile
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
live_path = ROOT / "IFRS17_BS.json"
h_before = hashlib.sha256(live_path.read_bytes()).hexdigest()
carry = ROOT / "data/_derived/bs_carry_forward_cells.json"
hc_before = hashlib.sha256(carry.read_bytes()).hexdigest() if carry.exists() else None
tmp = Path(tempfile.mkdtemp(prefix="dry_bs_build_"))
mod = importlib.import_module("scripts.build_ifrs17_bs")
mod.OUT = tmp / "IFRS17_BS.json"
mod.CARRY_OUT = tmp / "bs_carry_forward_cells.json"
sys.argv = ["build_ifrs17_bs.py"]
mod.main()
built = json.loads(mod.OUT.read_text(encoding="utf-8"))
live = json.loads(live_path.read_text(encoding="utf-8"))
key = lambda r: (r["원보험사코드"], r["항목번호"], r["공시분기"])
B = {key(r): r for r in built}
Lv = {key(r): r for r in live}
only_b = [k for k in B if k not in Lv]
only_l = [k for k in Lv if k not in B]
diff = [k for k in B if k in Lv and abs((B[k]["값"] or 0) - (Lv[k]["값"] or 0)) > 1e-6]
print(f"built rows {len(built)} live rows {len(live)} | only in built {len(only_b)} | only in live {len(only_l)} | value diffs {len(diff)}")
spec = json.loads((ROOT / "data/_derived/ifrs17_owner_followups_20261012/chubb_d2_spec_bs.json").read_text(encoding="utf-8"))["cells"]
ok = miss = bad = 0
for c in spec:
    code, item, q = c["key"].split("|")
    k = (code, int(item), q)
    if k not in B:
        miss += 1
    elif abs(B[k]["값"] - c["new"]) > 1e-6:
        bad += 1
    else:
        ok += 1
print(f"Chubb {len(spec)} D2 cells in the builder output: present with equal value {ok}, missing {miss}, different value {bad}")
print("sample only_in_live:", only_l[:8])
print("sample only_in_built:", only_b[:8])
print("sample diffs:", [(k, B[k]["값"], Lv[k]["값"]) for k in diff[:8]])
json.dump({"built_rows": len(built), "live_rows": len(live), "only_built": [list(k) for k in only_b], "only_live": [list(k) for k in only_l], "diffs": [[list(k), B[k]["값"], Lv[k]["값"]] for k in diff]},
          open(ROOT / "data/_derived/ifrs17_owner_followups_20261012/dry_build_bs_result.json", "w", encoding="utf-8"), ensure_ascii=False)
print("live IFRS17_BS.json untouched:", hashlib.sha256(live_path.read_bytes()).hexdigest() == h_before,
      "| carry file untouched:", (hashlib.sha256(carry.read_bytes()).hexdigest() == hc_before) if carry.exists() else "n/a")
