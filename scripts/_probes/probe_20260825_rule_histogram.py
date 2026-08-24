# -*- coding: utf-8 -*-
"""게이트 2종의 **룰별 finding 히스토그램**을 찍는다 (read-only).

휴리스틱 룰 쳐내기(2026-08-25) 의 before/after 실측용. `validate_data_contract` 는
in-process 로 돌려 severity x rule 를 세고, `validate_kics_disclosure` 는 리포트를
직접 만들어(main() 을 우회해 artifacts/ 공유폴더를 안 건드린다) status x rule 을 센다.
"""
from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))
sys.stdout.reconfigure(encoding="utf-8")

import validate_data_contract as dc          # noqa: E402
import validate_kics_disclosure as kg        # noqa: E402


def main() -> int:
    print("=" * 74)
    print("A. validate_data_contract — severity x rule")
    print("=" * 74)
    res = dc.run_gate(dc.Env())
    hist: Counter = Counter()
    for sev, bucket in (("RED", res.red), ("YELLOW", res.yellow)):
        for f in bucket:
            hist[(sev, getattr(f, "rule", None))] += 1
    for (sev, rule), n in sorted(hist.items(), key=lambda kv: (-kv[1], kv[0])):
        print(f"  {n:5d}  {sev:6s} {rule}")
    print(f"  TOTAL RED={len(res.red)} YELLOW={len(res.yellow)}")

    print()
    print("=" * 74)
    print("B. validate_kics_disclosure — status x rule (findings matrix)")
    print("=" * 74)
    records = kg._load_records(ROOT / "kics_disclosure.json")
    report = kg.run_validation(records,
                               source_has_breakdown=kg._scan_breakdown_presence(records),
                               tfi_applicability=kg._load_tfi_applicability())
    findings = report.get("findings", [])
    fh: Counter = Counter()
    for f in findings:
        fh[(f.get("status"), f.get("rule"))] += 1
    for (st, rule), n in sorted(fh.items(), key=lambda kv: (kv[0][1], kv[0][0])):
        print(f"  {n:5d}  {st:6s} {rule}")
    print(f"  FINDINGS TOTAL = {len(findings)}")

    print()
    print("=" * 74)
    print("C. 메타룰 census (main() 이 인쇄하는 층)")
    print("=" * 74)
    ac = kg._axis_evaluation_census(records)
    ared, arev = kg._axis_eval_findings(ac)
    print(f"  AXIS_NOT_EVALUATED (RED)   = {len(ared)}   {[(r['axis'], r['column']) for r in ared]}")
    print(f"  AXIS_EVAL_RATE_LOW (REVIEW)= {len(arev)}   {[(r['axis'], r['column']) for r in arev]}")
    print(f"  AXIS_SELF_MIRRORED_APPLIER = {len(kg._axis_mirror_findings(ac))}")
    tc, _skip = kg._identity_tautology_census(records)
    tred, texempt, trev = kg._identity_tautology_findings(tc)
    print(f"  IDENTITY_TAUTOLOGY   RED={len(tred)} EXEMPT={len(texempt)} REVIEW={len(trev)}")
    for r in trev:
        print(f"      REVIEW {r.get('rule')}  {r.get('axis')} [{r.get('column')}]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
