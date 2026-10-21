"""Read-only: does the pinned tests/fixtures/master_tables_golden.json SUMMARY equal the gate SUMMARY before / after the 2023.3Q blanking?  (no real validator run, so the tracked warn files are not rewritten)"""
import json
import re
import sys
from pathlib import Path

ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
HERE = Path(__file__).resolve().parent
sys.stdout.reconfigure(encoding="utf-8")
gold = json.loads((ROOT / "tests/fixtures/master_tables_golden.json").read_text(encoding="utf-8"))


def summ(p):
    for ln in Path(p).read_text(encoding="utf-8").splitlines():
        if ln.startswith("SUMMARY"):
            return re.sub(r"\s+", " ", ln.strip())


before, after = summ(HERE / "gates_before/master_tables.txt"), summ(HERE / "gates_after2/master_tables.txt")
print("fixture exit_code:", gold["exit_code"], "(overlay gate exit before/after: see gates_*/master_tables.txt head, both 2)")
print("fixture == gate SUMMARY before the blanking:", gold["summary"] == before)
print("fixture == gate SUMMARY after the blanking :", gold["summary"] == after)
a, b = gold["summary"].split(" | "), after.split(" | ")
for x, y in zip(a, b):
    if x != y:
        print("  moved:", x, "->", y)
