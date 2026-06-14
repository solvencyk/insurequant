#!/usr/bin/env python3
"""Validate root kics_disclosure.json against K-ICS JSON rules."""
from __future__ import annotations

import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from solvency.validation.kics_json_rules import KEY_CODE, KEY_QUARTER, run_validation

SPOT_CODE = "KR0005"
SPOT_QUARTER = "2025.4Q"
SPOT_NAME_HINT = "\ud5d5\uad6d\ud654\uc7ac"


def _load_records(path: Path) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise SystemExit(f"Expected list JSON at {path}")
    return data


def _coverage_census(records: list[dict]) -> dict:
    """Expected (filer x quarter) grid census. A quarter present in the data that
    is missing 'regular filers' (codes seen in >=half of established quarters) goes
    RED — guards against a whole quarter being silently under-parsed (e.g. 2026.1Q
    held only 1 of ~35 filers yet rules emitted no finding → RED=0). Missing-cell is
    a first-class failure, not a SKIP. See memory: coverage-census-mandatory."""
    by_q: dict[str, set] = {}
    code_name: dict[str, str] = {}
    for r in records:
        q = r.get("공시분기")
        c = r.get("원보험사코드")
        if not q or not c:
            continue
        by_q.setdefault(q, set()).add(c)
        code_name[c] = r.get("원수사명", c)
    quarters = sorted(by_q)
    # 'established' history = all but trailing under-filled latest, used to learn the
    # regular-filer set; a code is a regular filer if it appears in >=50% of quarters.
    n_q = len(quarters)
    appears: dict[str, int] = {}
    for q in quarters:
        for c in by_q[q]:
            appears[c] = appears.get(c, 0) + 1
    regular = {c for c, n in appears.items() if n >= max(2, n_q // 2)}
    median_n = sorted(len(by_q[q]) for q in quarters)[len(quarters) // 2] if quarters else 0
    missing_rows = []  # (quarter, code, name)
    for q in quarters:
        present = by_q[q]
        for c in sorted(regular - present):
            missing_rows.append((q, c, code_name.get(c, c)))
    # also flag quarters whose filer count collapsed vs median (gross under-parse)
    collapsed = [
        (q, len(by_q[q])) for q in quarters if len(by_q[q]) < max(3, median_n // 2)
    ]
    return {
        "regular_filers": len(regular),
        "median_filers_per_q": median_n,
        "missing_rows": missing_rows,
        "collapsed_quarters": collapsed,
    }


def _top_offenders(findings: list[dict], status: str, limit: int = 10) -> list[dict]:
    rows = [f for f in findings if f.get("status") == status]
    rows.sort(key=lambda f: abs(float(f.get("diff") or 0.0)), reverse=True)
    return [
        {
            "rule": f.get("rule"),
            "code": f.get(KEY_CODE),
            "quarter": f.get(KEY_QUARTER),
            "diff": f.get("diff"),
        }
        for f in rows[:limit]
    ]


# 19_market source-grounded cadence: 시장위험 세부표(36-40) 5종 라벨. >=3 distinct = 표 존재.
# (경과조치 문맥의 '금리위험액'/'주식위험액' 단발 언급과 구분 위해 distinct>=3; 자산집중/부동산/외환은
#  세부표에만 등장. 검증: 삼성화재 홀수분기 <=2 / 짝수분기 5-10 / 삼성생명 홀수 표있는분기 >=3.)
_SUBRISK_KW = ["금리위험액", "주식위험액", "부동산위험액", "외환위험액", "자산집중위험"]


def _scan_breakdown_presence(records: list[dict]) -> frozenset:
    """(원보험사코드, 공시분기) 중 disclosure MD에 36-40 세부표가 실재하는 셀의 집합.
    item19 공시인데 36-40 결측인 후보 셀만 MD 확인 → 표 있으면 파서갭(RED), 없으면 cadence(SKIP).
    See: 19_market source-grounded cadence fix (2026-06-13)."""
    by_cq: dict[tuple, set] = {}
    for r in records:
        c, q, it = r.get("원보험사코드"), r.get("공시분기"), r.get("항목번호")
        if c and q and it is not None and r.get("값") is not None:
            by_cq.setdefault((c, q), set()).add(it)
    candidates = [
        (c, q) for (c, q), items in by_cq.items()
        if 19 in items and not (set(range(36, 41)) & items)
    ]
    present, cache = set(), {}
    for c, q in candidates:
        fyq = f"FY{q[:4]}_Q{q[5]}"  # 2025.1Q -> FY2025_Q1
        cands = list((ROOT / "data" / "disclosure" / fyq / "parsed").glob(f"*{c}*.md"))
        if not cands:
            continue  # MD 없으면 후속 else 분기에서 RED(보수적) 처리
        p = cands[0]
        if p not in cache:
            try:
                cache[p] = p.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                cache[p] = ""
        if sum(1 for k in _SUBRISK_KW if k in cache[p]) >= 3:
            present.add((c, q))
    return frozenset(present)


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # Windows console defaults to cp949
    except Exception:
        pass
    src = ROOT / "kics_disclosure.json"
    records = _load_records(src)
    report = run_validation(records, source_has_breakdown=_scan_breakdown_presence(records))
    findings = report.get("findings", [])

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_dir = ROOT / "artifacts" / "kics_validation"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"report_{ts}.json"
    report["source"] = str(src)
    report["generated_at"] = ts
    report["spot_check"] = {
        "code": SPOT_CODE,
        "quarter": SPOT_QUARTER,
        "name_hint": "헕국화재",
        "findings": [
            f
            for f in findings
            if f.get(KEY_CODE) == SPOT_CODE and f.get(KEY_QUARTER) == SPOT_QUARTER
        ],
    }
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    census = _coverage_census(records)
    report["coverage_census"] = {
        "regular_filers": census["regular_filers"],
        "median_filers_per_q": census["median_filers_per_q"],
        "missing_count": len(census["missing_rows"]),
        "missing_rows": [
            {"quarter": q, "code": c, "name": n} for q, c, n in census["missing_rows"]
        ],
        "collapsed_quarters": census["collapsed_quarters"],
    }
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    # stable-name 최신 포인터: glob 정렬 함정(stale report_latest.json) 방지 — 매 실행 fresh 덮어쓰기.
    (out_dir / "report_latest.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    summary = report.get("summary", {})
    by_status = summary.get("by_status", {})
    red = int(by_status.get("RED", 0))
    yellow = int(by_status.get("YELLOW", 0))
    err = int(by_status.get("ERROR", 0))
    census_red = len(census["missing_rows"])

    fail_by_rule = Counter(f.get("rule") for f in findings if f.get("status") == "RED")
    print(f"K-ICS validation report: {out_path}")
    print(
        f"Status counts: RED={red} YELLOW={yellow} GREEN={by_status.get('GREEN', 0)} "
        f"SKIP={by_status.get('SKIP', 0)} ERROR={err}"
    )
    print(
        f"Coverage census: regular_filers={census['regular_filers']} "
        f"median/q={census['median_filers_per_q']} "
        f"MISSING_CELLS(RED)={census_red} "
        f"collapsed_quarters={census['collapsed_quarters']}"
    )
    if census["missing_rows"]:
        by_q_missing = Counter(q for q, _, _ in census["missing_rows"])
        print("  missing filers by quarter:")
        for q, cnt in sorted(by_q_missing.items()):
            sample = ", ".join(
                n for qq, _, n in census["missing_rows"] if qq == q
            )
            print(f"    {q}: {cnt} missing — {sample[:160]}")
    print("RED failures by rule:")
    for rule_id, cnt in sorted(fail_by_rule.items(), key=lambda x: (-x[1], x[0])):
        print(f"  rule {rule_id}: {cnt}")
    print("Top RED offenders:")
    for row in _top_offenders(findings, "RED", limit=10):
        print(f"  rule {row['rule']} {row['code']} {row['quarter']} diff={row['diff']}")

    spot = report["spot_check"]["findings"]
    spot_red = [f for f in spot if f.get("status") == "RED"]
    print(
        f"Spot-check {SPOT_CODE} {SPOT_QUARTER} ({SPOT_NAME_HINT}): "
        f"{len(spot)} results, RED={len(spot_red)}"
    )
    for f in spot:
        if f.get("status") == "RED":
            print(
                f"  RED rule {f.get('rule')}: expected={f.get('expected')} "
                f"actual={f.get('actual')} diff={f.get('diff')}"
            )

    return 2 if (red > 0 or census_red > 0) else 0


if __name__ == "__main__":
    raise SystemExit(main())
