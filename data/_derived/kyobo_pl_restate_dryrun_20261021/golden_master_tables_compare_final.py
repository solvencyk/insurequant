"""Read-only: which fields of the pinned tests/fixtures/master_tables_golden.json SUMMARY moved between the baseline (before this ticket), post-E5 and the final state."""
import json
import re
import sys
from pathlib import Path

ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
sys.stdout.reconfigure(encoding="utf-8")
gold = json.loads((ROOT / "tests/fixtures/master_tables_golden.json").read_text(encoding="utf-8"))


def summ(p):
    for ln in Path(p).read_text(encoding="utf-8").splitlines():
        if ln.startswith("SUMMARY"):
            return re.sub(r"\s+", " ", ln.strip())


D = ROOT / "data/_derived"
states = {"baseline(before ticket)": D / "kyobo_csm_basis_fix_20261021/gates_before/master_tables.txt",
          "post-E5": D / "kyobo_pl_restate_dryrun_20261021/gates_pre_PL/master_tables.txt",
          "final": D / "kyobo_pl_restate_dryrun_20261021/gates_after_apply/master_tables.txt"}
print("fixture exit_code:", gold["exit_code"])
for name, p in states.items():
    s = summ(p)
    print(f"fixture == {name} summary: {gold['summary'] == s}")
final = summ(states["final"])
a, b = gold["summary"].split(" | "), final.split(" | ")
print("fields moved (fixture -> final):")
for x, y in zip(a, b):
    if x != y:
        print("   ", x, "->", y)
