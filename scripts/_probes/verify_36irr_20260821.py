# -*- coding: utf-8 -*-
"""Run the GATE's own 36_irr derive function (not a hand rederivation) against the live
kics_disclosure.json and print the finding for the 5 target buckets."""
import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from solvency.validation.kics_json_rules import run_validation  # noqa: E402

TARGETS = {
    ("KR0073", "2025.2Q"),
    ("KR0094", "2024.2Q"),
    ("KR0094", "2024.4Q"),
    ("KR0094", "2025.2Q"),
    ("KR0094", "2025.4Q"),
}

data = json.load(open(ROOT / "kics_disclosure.json", encoding="utf-8"))
report = run_validation(data, source_has_breakdown=None)
findings = report.get("findings", [])
print(f"total findings: {len(findings)}")
hits = [f for f in findings if f.get("rule") == "36_irr"
        and (f.get("원보험사코드"), f.get("공시분기")) in TARGETS]
hits.sort(key=lambda f: (f.get("원보험사코드"), f.get("공시분기")))
for f in hits:
    exp = f.get("expected")
    act = f.get("actual")
    diff = f.get("diff")
    rel = (diff / act * 100) if (diff is not None and act) else None
    print(f"{f.get('원보험사코드')} {f.get('공시분기')}  status={f.get('status'):5s}  "
          f"disclosed(actual)={act}  derived(expected)={exp}  diff={diff}  "
          f"rel%={rel:.2f}" if rel is not None else
          f"{f.get('원보험사코드')} {f.get('공시분기')}  status={f.get('status'):5s}  actual={act} expected={exp} diff={diff}")
    print(f"    detail: {f.get('detail')}")
