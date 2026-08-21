# -*- coding: utf-8 -*-
"""inbox/parser/20260821T1105Z__orchestrator__KR0071__item24_fabricated_dash_row.md

흥국생명(KR0071) 2023.3Q item24(1. 업권별 자본규제를 활용한 종속회사의 요구자본 환산치) 값(적용전)
= 8313 은 원문 raw p11 이 "-" (해당없음) 인데 8313 (item23/26 을 잘못 복사한 값) 으로 저장돼 있던
오염 셀. 같은 표의 item25(2. 비례성원칙...)는 이미 "-" -> 0 으로 정확히 저장돼 있어, 그 처리와
일관되게 item24 도 0 으로 쓴다(이 표의 "-" 는 "해당없음" = 0, F3 의 시장위험 leaf "전후동일" 의미와는
다른 표/문맥이라 그 규칙은 적용 안 함). item24_적용후는 원래도 None(형제 item25/26_적용후와 동일하게
결측) 이라 손대지 않는다 — 근거 없이 새 값을 만들지 않는다("틀린 값을 싣느니 빈 칸").

검증: item23 = item24+item25+item26 (양쪽 컬럼) 전사 스윕으로 이 1건 외 위반이 없는지 확인한다.

Usage:
  ...python scripts/fix_20260821_kr0071_item24_fabricated_dash.py --dry-run
  ...python scripts/fix_20260821_kr0071_item24_fabricated_dash.py
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

REPO = Path(__file__).resolve().parents[1]
TARGET = REPO / "kics_disclosure.json"


def _num(v):
    if v is None:
        return None
    s = str(v).strip()
    if s == "":
        return None
    try:
        return float(s)
    except ValueError:
        return None


def main() -> int:
    dry = "--dry-run" in sys.argv
    data = json.loads(TARGET.read_text(encoding="utf-8"))

    by_cq: dict[tuple, dict] = {}
    name: dict[str, str] = {}
    for r in data:
        c, q = r.get("원보험사코드"), r.get("공시분기")
        name[c] = r.get("원수사명", c)
        by_cq.setdefault((c, q), {})[int(r["항목번호"])] = r

    # --- sweep: item23 vs item24+item25+item26, both columns, whole master ---
    print("=== sweep BEFORE fix: item23 != item24+item25+item26 ===")
    viol_before = []
    for (c, q), items in sorted(by_cq.items()):
        for col in ("값", "값_적용후"):
            p = _num((items.get(23) or {}).get(col))
            a = _num((items.get(24) or {}).get(col))
            b = _num((items.get(25) or {}).get(col))
            d = _num((items.get(26) or {}).get(col))
            if p is None or a is None or b is None or d is None:
                continue  # missing children -> not comparable, not a "wrong sum" case
            if abs(p - (a + b + d)) > 1.5:
                # tol 1.5: 3 independently-rounded 억원 integers summed vs an independently
                # rounded parent legitimately drifts by +-1 (DB손해/한화생명/삼성생명/교보생명
                # all show exactly diff=1 below - that's rounding noise, not a data bug).
                viol_before.append((c, name.get(c, c), q, col, p, a, b, d))
    for c, nm, q, col, p, a, b, d in viol_before:
        print(f"  {c} {nm:<12} {q} [{col}] item23={p} vs 24+25+26={a}+{b}+{d}={a+b+d}")
    print(f"위반 {len(viol_before)}건")

    # --- targeted fix: KR0071 2023.3Q item24 값(적용전) 8313 -> 0 ---
    row = by_cq.get(("KR0071", "2023.3Q"), {}).get(24)
    if row is None:
        print("KR0071 2023.3Q item24 행을 찾을 수 없음 - 중단")
        return 1
    old = row.get("값")
    print(f"\nKR0071 2023.3Q item24 값(적용전): {old!r} -> '0'  (raw p11: '-' = 해당없음, item25와 동일 처리)")
    print(f"KR0071 2023.3Q item24 값_적용후: {row.get('값_적용후')!r} (변경 없음 - 형제 item25/26_적용후와 동일하게 결측 유지)")

    if not dry:
        row["값"] = "0"
        TARGET.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\nwrote {TARGET.name}")

    # --- re-sweep after fix (in-memory) ---
    print("\n=== sweep AFTER fix (in-memory) ===")
    viol_after = []
    for (c, q), items in sorted(by_cq.items()):
        for col in ("값", "값_적용후"):
            p = _num((items.get(23) or {}).get(col))
            a = _num((items.get(24) or {}).get(col))
            b = _num((items.get(25) or {}).get(col))
            d = _num((items.get(26) or {}).get(col))
            if p is None or a is None or b is None or d is None:
                continue
            if abs(p - (a + b + d)) > 1.5:
                viol_after.append((c, name.get(c, c), q, col, p, a, b, d))
    for c, nm, q, col, p, a, b, d in viol_after:
        print(f"  {c} {nm:<12} {q} [{col}] item23={p} vs 24+25+26={a}+{b}+{d}={a+b+d}")
    print(f"위반 {len(viol_after)}건")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
