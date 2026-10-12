"""i1_golden_report.py -- what does the K-ICS rules golden (tests/test_kics_rules_golden.py) see before / after THIS change?  (READ-ONLY)

expected = tests/fixtures/kics_rules_golden.json (what is pinned today; it was already stale before this ticket)
before   = the rule engine over the pre-change master (backup/kics_disclosure_before_<sha>.json == git HEAD)
after    = the rule engine over the live master
Prints the manifest keys for the three and the exact (code, quarter, rule, status) tuples that moved between before and after.
Nothing is written; the golden fixture is not touched.
"""
import importlib.util
import json
import sys
from pathlib import Path

sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/kics_latest_prior_apply_20261012")
sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/scripts")
sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/src")
from lib_apply import *  # noqa: F401,F403,E402

utf8_stdout()
spec = importlib.util.spec_from_file_location("kics_golden_mod", REPO / "tests" / "test_kics_rules_golden.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
expected = json.loads(mod.GOLDEN.read_text(encoding="utf-8"))
before_master = BACKUP / "kics_disclosure_before_bede3bcc0bc6.json"


def tuples(master):
    mod.MASTER = master
    rep = mod._run()
    man = mod._manifest(rep)
    rows = {}
    for f in rep["findings"]:
        rows[(f.get("원보험사코드"), f.get("공시분기"), str(f.get("rule")))] = f.get("status")
    return man, rows


mb, rb = tuples(before_master)
ma, ra = tuples(MASTER)
for k in ("sha256", "buckets", "findings", "by_status", "by_rule"):
    e, b, a = expected.get(k), mb[k], ma[k]
    if k == "by_rule":
        print(f"{k}: expected==before {e == b} | before==after {b == a}")
    else:
        print(f"{k}:\n   expected {e}\n   before   {b}\n   after    {a}")
moved = sorted((k, rb.get(k), ra.get(k)) for k in set(rb) | set(ra) if rb.get(k) != ra.get(k))
print(f"\n(code, quarter, rule) findings whose status moved because of this change: {len(moved)}")
from collections import Counter
print("   transitions:", dict(Counter((x[1], x[2]) for x in moved)))
for k, s0, s1 in moved:
    print("   ", k, s0, "->", s1)
bd = {r: (mb["by_rule"].get(r), ma["by_rule"].get(r)) for r in set(mb["by_rule"]) | set(ma["by_rule"]) if mb["by_rule"].get(r) != ma["by_rule"].get(r)}
print("\nby_rule entries that changed:", bd)
print("\nexpected (fixture) vs before: which manifest keys were already off BEFORE this ticket:",
      [k for k in ("sha256", "buckets", "findings", "by_status", "by_rule") if expected.get(k) != mb[k]])
