#!/usr/bin/env python3
"""Validate root kics_disclosure.json against K-ICS JSON rules."""
from __future__ import annotations

import json
import re
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


# 19_market source-grounded cadence: 시장위험 세부표(36-40) 5종 라벨이 **분해표 행으로 실재**하는지.
# 2026-06-14 fix: 종전 substring 카운트는 경과조치표의 '주식위험액증가분점진적인식'·산문의 '자산집중위험등'
#  같은 compound/서술 부분문자열을 라벨로 세어 distinct>=3을 거짓충족 → 삼성생명 odd-Q(2023.3Q 등)
#  false RED (parser D 분쟁, raw 확인 결과 분해표 부재 = SKIP 정당). → 번호접두어를 떼어낸 **셀 전체가
#  라벨과 일치**하거나 라벨 직후 숫자가 오는 행만 카운트.
_SUBRISK_LABELS = ["금리위험액", "주식위험액", "부동산위험액", "외환위험액", "자산집중위험액"]
_NUM_PREFIX = re.compile(r"^[\s0-9.\-()ⅠⅡⅢⅣⅤ]*")


def _count_subrisk_rows(text: str) -> int:
    """Distinct 시장위험 5종 라벨이 분해표 '행'으로 실재하는 수.
    경과조치 compound('주식위험액증가분점진적인식')·산문('자산집중위험등')은 제외:
    번호접두어 제거 후 셀==라벨(또는 어간) 또는 라벨 직후 숫자(plain-text 표)만 인정."""
    found: set[str] = set()
    for line in text.splitlines():
        cells = line.split("|") if "|" in line else [line]
        for cell in cells:
            cleaned = _NUM_PREFIX.sub("", cell.strip()).strip()
            for lab in _SUBRISK_LABELS:
                stem = lab[:-1]  # '금리위험액' -> '금리위험'
                if cleaned == lab or cleaned == stem:
                    found.add(lab)
                    break
                if cleaned.startswith(lab) or cleaned.startswith(stem):
                    rest = cleaned[len(lab) if cleaned.startswith(lab) else len(stem):].lstrip()
                    if rest[:1].isdigit():
                        found.add(lab)
                        break
    return len(found)


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
        if _count_subrisk_rows(cache[p]) >= 3:
            present.add((c, q))
    return frozenset(present)


def _market_tooling_fail(records: list[dict]) -> list[tuple]:
    """시장위험 페이지 localizer 실패(`market_pages_nonok.json`의 ERR/NO_SIGNAL/TIMEOUT/SCAN) (회사,분기) 중
    *현재도* 분해 갭(item19 공시·36-40 결측)인 셀 = re-localize 후보(TOOLING_FAIL).
    이미 백필된 stale-nonok은 제외(데이터 lag 방지). 추출도구가 죽었는데 게이트가 '미공시(SKIP)'로
    오인하는 SKIP-on-missing 위반을 가시화. 2026-06-14 배선(parser fitz-fallback 안착 → nonok 시맨틱
    안정 후). 게이트 차단은 안 함 — 짝수분기 진짜 갭은 19_market이 이미 RED, 이 목록은 원인 귀속·재로컬 워크리스트."""
    p = ROOT / "artifacts" / "kics_validation" / "market_pages_nonok.json"
    if not p.exists():
        return []
    try:
        nonok = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return []
    by_cq: dict[tuple, set] = {}
    name: dict[str, str] = {}
    for r in records:
        c, q, it = r.get("원보험사코드"), r.get("공시분기"), r.get("항목번호")
        name[c] = r.get("원수사명")
        if c and q and it is not None and r.get("값") is not None:
            by_cq.setdefault((c, q), set()).add(it)
    out = []
    for status, cells in (nonok.items() if isinstance(nonok, dict) else []):
        for cell in cells or []:
            if not (isinstance(cell, (list, tuple)) and len(cell) >= 2):
                continue
            c, q = cell[0], cell[1]
            items = by_cq.get((c, q), set())
            if 19 in items and not (set(range(36, 41)) & items):  # 여전히 갭(백필 안 됨)
                out.append((c, q, status, name.get(c, c)))
    return out


# 부모 위험액 항목 → 그 하위 세부항목 번호. 항목번호는 flat index라 계층은 라벨접두어가 아니라
# 명시 매핑으로 잡는다(라벨 '1.'은 자본tiering·종속회사 네임스페이스에도 출현 → 접두어 매칭 불가).
#   item 17 (1. 생명장기손해보험위험액) -> 29-35 (1-1..1-7)
#   item 19 (3. 시장위험액)            -> 36-40 (3-1..3-5)
_PARENT_CHILD_ITEMS = {17: (29, 30, 31, 32, 33, 34, 35), 19: (36, 37, 38, 39, 40)}


def _parent_zero_child_nonzero(records: list[dict]) -> list[tuple]:
    """부모 위험액 항목이 표에 0으로 존재하는데 하위 세부항목이 비0 = 행 오정렬/셀 밀림.
    구조상 불가능(K-ICS 상관행렬 집계상 분산총액 ≥ 최대 단일세부 → 세부 비0이면 부모도 비0).
    서울보증 25.4Q 생명장기(item17=0) 아래 대재해위험액(item35=5212) 파싱오류를 게이트가 못 잡던
    사각(owner 라이브 QA 3차). 부모 '결측'은 census 소관 → 여기선 부모 present&≈0만 RED."""
    def _num(v):
        try:
            return float(v)
        except (TypeError, ValueError):
            return None

    by_cq: dict[tuple, dict] = {}
    name: dict[str, str] = {}
    for r in records:
        c, q, it = r.get("원보험사코드"), r.get("공시분기"), r.get("항목번호")
        name[c] = r.get("원수사명", c)
        try:
            it = int(it)
        except (TypeError, ValueError):
            continue
        if c and q:
            by_cq.setdefault((c, q), {})[it] = _num(r.get("값"))
    out = []
    for (c, q), items in sorted(by_cq.items()):
        for parent, kids in _PARENT_CHILD_ITEMS.items():
            if parent not in items:
                continue  # 부모 결측 = census 소관, 이 룰 아님
            pv = items[parent]
            if pv is None or abs(pv) >= 1.0:
                continue  # 부모가 present & ≈0 인 경우만
            nz = [(k, items[k]) for k in kids
                  if items.get(k) is not None and abs(items[k]) >= 1.0]
            if nz:
                out.append((c, q, parent, name.get(c, c), nz))
    return out


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
    tooling_fail = _market_tooling_fail(records)
    report["market_tooling_fail"] = [
        {"code": c, "quarter": q, "status": s, "name": n} for c, q, s, n in tooling_fail
    ]
    parent_child = _parent_zero_child_nonzero(records)
    report["parent_zero_child_nonzero"] = [
        {
            "code": c, "quarter": q, "parent_item": p, "name": n,
            "nonzero_children": [{"item": k, "value": v} for k, v in nz],
        }
        for c, q, p, n, nz in parent_child
    ]
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
    if tooling_fail:
        print(f"Market localizer TOOLING_FAIL (re-localize, still-gap): {len(tooling_fail)}")
        for c, q, s, n in tooling_fail:
            print(f"    {q} {c} {n} [{s}] — item19 공시·36-40 결측, localizer 실패 → re-localize")
    else:
        print("Market localizer TOOLING_FAIL: 0 (nonok 셀 전부 백필됨 또는 비-갭)")
    if parent_child:
        print(f"Parent-zero / nonzero-child (structural misparse, RED): {len(parent_child)}")
        for c, q, p, n, nz in parent_child:
            kids = ", ".join(f"item{k}={v}" for k, v in nz)
            print(f"    {q} {c} {n}: 부모 item{p}=0 인데 자식 {kids} → 행 오정렬/셀 밀림")
    else:
        print("Parent-zero / nonzero-child: 0")
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

    return 2 if (red > 0 or census_red > 0 or parent_child) else 0


if __name__ == "__main__":
    raise SystemExit(main())
