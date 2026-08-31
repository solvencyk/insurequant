"""validate_kics_disclosure.py run_validation(), before (pre-session backup) vs after
(current), restricted to the 16 target companies (any quarter)."""
import io
import json
import sys
from collections import Counter
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import validate_kics_disclosure as vkd  # noqa: E402

MY_CODES = {"KR0068", "KR0069", "KR0070", "KR0071", "KR0072", "KR0080", "KR0082", "KR0083",
            "KR0087", "KR0094", "KR0097", "KR0099", "KR0100", "KR0104", "KR1010", "KR1011"}

BEFORE = ROOT / "kics_disclosure.json.bak_20260901_010358_posttrans_life16"

after_records = vkd._load_records(Path(ROOT / "kics_disclosure.json"))
before_records = vkd._load_records(Path(BEFORE))


def run(records):
    report = vkd.run_validation(records,
                                 source_has_breakdown=vkd._scan_breakdown_presence(records),
                                 tfi_applicability=vkd._load_tfi_applicability())
    return report.get("findings", [])


after_f = [f for f in run(after_records) if f.get("원보험사코드") in MY_CODES]
before_f = [f for f in run(before_records) if f.get("원보험사코드") in MY_CODES]


def by_status_rule(findings):
    return Counter((f.get("rule"), f.get("status")) for f in findings)


cb, ca = by_status_rule(before_f), by_status_rule(after_f)
keys = sorted(set(cb) | set(ca))
print(f"{'rule/status':<40} {'before':>8} {'after':>8} {'delta':>8}")
changed = False
for k in keys:
    b, a = cb.get(k, 0), ca.get(k, 0)
    if b != a:
        changed = True
    print(f"{str(k):<40} {b:>8} {a:>8} {a-b:>+8}" + ("  <-- CHANGED" if b != a else ""))

print(f"\nTotal (mine) before={len(before_f)} after={len(after_f)}")
if not changed:
    print("NO CHANGE in rule/status distribution for my 16 companies.")

red_before = [f for f in before_f if f.get("status") == "RED"]
red_after = [f for f in after_f if f.get("status") == "RED"]
print(f"\nRED before: {len(red_before)}  RED after: {len(red_after)}")
for f in red_after:
    print("  AFTER RED:", f.get("원보험사코드"), f.get("공시분기"), f.get("rule"), f.get("detail", "")[:100])
