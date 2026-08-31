"""Full validate_data_contract.py gate, before (pre-session backup) vs after (current
kics_disclosure.json), restricted to the 16 target companies (any quarter) -- checks for
side effects beyond the 2 target rules."""
import io
import json
import sys
from collections import Counter
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from validate_data_contract import Env, run_gate  # noqa: E402

MY_NAMES = {"한화생명", "삼성생명보험", "에이비엘생명보험", "흥국생명보험", "케이디비생명보험",
            "에이아이에이생명보험", "DB생명보험", "푸본현대생명보험", "동양생명", "신한라이프생명보험",
            "하나생명보험", "KB라이프생명", "처브라이프생명보험", "농협생명보험",
            "교보라이프플래닛생명보험", "IBK연금보험"}

BEFORE = ROOT / "kics_disclosure.json.bak_20260901_010358_posttrans_life16"

env = Env()

# AFTER: env already loaded current kics_disclosure.json
res_after = run_gate(env)
after_mine = [f for f in res_after.findings if f.company in MY_NAMES]

# BEFORE: swap in the pre-session snapshot's records, rerun
before_records = json.loads(BEFORE.read_text(encoding="utf-8"))
env.kics_records = before_records
res_before = run_gate(env)
before_mine = [f for f in res_before.findings if f.company in MY_NAMES]


def by_rule(findings):
    return Counter((f.rule, f.severity) for f in findings)


cb, ca = by_rule(before_mine), by_rule(after_mine)
all_keys = sorted(set(cb) | set(ca))
print(f"{'rule/severity':<45} {'before':>8} {'after':>8} {'delta':>8}")
for k in all_keys:
    b, a = cb.get(k, 0), ca.get(k, 0)
    marker = "" if b == a else ("  <-- CHANGED" if k[0] not in ("POST_TRANSITION_PARENT_MISSING", "POST_TRANSITION_CHILD_MISSING") else "  (target rule)")
    print(f"{str(k):<45} {b:>8} {a:>8} {a-b:>+8}{marker}")

print(f"\nTOTAL before: {len(before_mine)}  after: {len(after_mine)}")

# any finding present in AFTER but not attributable to a target-rule fix, for a rule
# OTHER than the 2 target rules, that wasn't in BEFORE -> flag explicitly
target_rules = {"POST_TRANSITION_PARENT_MISSING", "POST_TRANSITION_CHILD_MISSING"}


def sig(f):
    return (f.rule, f.company, f.quarter, f.message)


before_sigs = {sig(f) for f in before_mine if f.rule not in target_rules}
after_sigs = {sig(f) for f in after_mine if f.rule not in target_rules}
new_non_target = after_sigs - before_sigs
gone_non_target = before_sigs - after_sigs
print(f"\nNEW non-target findings introduced: {len(new_non_target)}")
for s in list(new_non_target)[:20]:
    print("  NEW:", s)
print(f"non-target findings that disappeared (unexpected side-heal): {len(gone_non_target)}")
for s in list(gone_non_target)[:20]:
    print("  GONE:", s)
