"""READ-ONLY. KR1000 재감사용 — 룰엔진이 이 회사에 대해 내는 finding 전문 덤프.

게이트가 실제로 쓰는 입력(`_load_tfi_applicability`)을 그대로 써서 run_validation 을 돌리고,
KR1000 의 tier2/bridge 축 finding 을 detail 까지 인쇄한다. 회사별 item47 스코프 투표 결과도
같이 찍는다(룰이 어떤 읽기로 검사하는지 확인용). 아무 파일도 안 고친다.

사용: probe_20260824_reaudit_kr1000_findings.py --out <utf8 파일>
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

CODE = "KR1000"
AXES = ("2_tier1_bridge", "3_tier2_composition", "51_tfi_tier2_composition",
        "47_tier2_census", "48_tier2_limit", "50_tfi_tier1", "52_tfi_total")


def main() -> None:
    out_path = sys.argv[sys.argv.index("--out") + 1]
    from src.solvency.validation.kics_json_rules import (
        run_validation, _tier2_cross_bucket_context, _group_records,
    )
    from validate_kics_disclosure import _load_tfi_applicability

    rows = json.loads((ROOT / "kics_disclosure.json").read_text(encoding="utf-8"))
    res = run_validation(rows, tfi_applicability=_load_tfi_applicability())
    findings = res["findings"] if isinstance(res, dict) else res

    buf: list[str] = []
    # scope vote
    try:
        buckets = _group_records(rows)
        ctx = _tier2_cross_bucket_context(buckets)
        scope_map = ctx[3] if isinstance(ctx, tuple) and len(ctx) >= 4 else {}
        buf.append("item47 scope vote for %s = %r" % (CODE, scope_map.get(CODE)))
        from collections import Counter
        buf.append("scope vote distribution: %r" % dict(Counter(scope_map.values())))
    except Exception as e:  # pragma: no cover - diagnostic only
        buf.append("scope map unavailable: %r" % (e,))

    buf.append("=" * 90)
    for f in findings:
        if f.get("원보험사코드") != CODE:
            continue
        rule = f.get("rule", "")
        if not any(rule.startswith(a) for a in AXES):
            continue
        buf.append("%-9s %-28s %-7s exp=%-14s act=%-14s diff=%s" % (
            f.get("공시분기"), rule, f.get("status"),
            f.get("expected"), f.get("actual"), f.get("diff")))
        buf.append("    %s" % f.get("detail", ""))
    io.open(out_path, "w", encoding="utf-8").write("\n".join(buf))
    print("written", out_path)


if __name__ == "__main__":
    main()
