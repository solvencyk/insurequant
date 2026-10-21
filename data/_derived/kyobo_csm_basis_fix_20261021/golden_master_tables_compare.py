import json, re, sys
from pathlib import Path
ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
sys.stdout.reconfigure(encoding="utf-8")
gold = json.loads((ROOT / "tests/fixtures/master_tables_golden.json").read_text(encoding="utf-8"))
def summ(p):
    for ln in Path(p).read_text(encoding="utf-8").splitlines():
        if ln.startswith("SUMMARY"):
            return re.sub(r"\s+", " ", ln.strip())
EV = ROOT / "data/_derived/kyobo_csm_basis_fix_20261021"
base, after = summ(EV / "gates_before/master_tables.txt"), summ(EV / "gates_after_E5/master_tables.txt")
print("fixture == baseline summary:", gold["summary"] == base, "| fixture exit", gold["exit_code"])
print("fixture == post-apply summary:", gold["summary"] == after)
a, b = gold["summary"].split(" | "), after.split(" | ")
for x, y in zip(a, b):
    if x != y:
        print("  moved:", x, "->", y)
