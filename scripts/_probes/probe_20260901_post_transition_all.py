"""Enumerate ALL POST_TRANSITION_PARENT_MISSING / POST_TRANSITION_CHILD_MISSING findings,
any company/quarter, to see what's left globally."""
import io
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from validate_data_contract import Env, run_gate  # noqa: E402

TARGET_RULES = {"POST_TRANSITION_PARENT_MISSING", "POST_TRANSITION_CHILD_MISSING"}

env = Env()
res = run_gate(env)

mine = [f for f in res.findings if f.rule in TARGET_RULES]
print(f"Total findings across repo for these 2 rules: {len(mine)}")
for f in mine:
    print(f"  {f.company} {f.quarter} [{f.severity}] {f.rule} | {f.message}")

print()
print("--- rule name census (all rules present in this gate run) ---")
from collections import Counter
c = Counter(f.rule for f in res.findings if f.severity == "RED")
for rule, n in c.most_common(40):
    print(f"  {n:4d}  {rule}")
