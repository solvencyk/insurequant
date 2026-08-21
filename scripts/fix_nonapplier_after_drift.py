# -*- coding: utf-8 -*-
"""비적용사의 요구자본측 '적용후'가 '적용전'과 다른 셀을 전값으로 되돌린다 (오염 정정).

`_TRANSITION_APPLIERS`(FSS 정본 18사) **밖** 회사는 선택적용 경과조치를 신청하지 않았다. 공통
경과조치(TFI)는 자본 티어만 재배분하고 요구자본(15-26·29-46)은 아예 건드리지 않는다 —
그러므로 이 회사들의 요구자본측 `값_적용후`는 정의상 `값`과 같아야 한다. 다르면 추출 오염이다.

`fix_20260716_nonapplier_requirement_mirror.py`는 **UPSERT 전용**(빈 칸만 채움)이라 이미 값이
들어간 오염 셀은 손대지 못한다. 이 스크립트가 그 반대편 — 이미 채워졌는데 전≠후인 셀 — 을 맡는다.

원문 확인한 대표 사례 (전부 "경과조치를 적용하지 않아 전·후 동일" 명시):
  KR0051 신한이지 2025.1Q item35후=43  ← raw p14 "대재해위험 2 / 2". 부모 item17후=10 인데
      하위가 43 이라 R7 이 47.01 로 튀었다(분산 후 부모가 하위보다 작을 수 없다).
  KR0050 하나손해 2025.2Q item34후=44.43 ← raw p21 "사업비위험 38,153"(=381.53억). 44.43 은
      바로 아래 대재해위험 값 — 한 칸 밀림.
  KR0050 하나손해 2023.3Q item35후=77.35 ← 전 26.90.
  KR0099 KB라이프 2024.2Q·2025.2Q 하위 4개 ← raw p3/p11/p15 "당사는 선택적용 경과조치를
      적용하지 않아 경과조치 전∙후의 금액 및 비율이 동일함". 저장된 후는 생명·장기위험액 현황
      표의 다른 분기 컬럼으로 보인다(해지 10,787.13 → 12,363.9 로 오히려 증가).
  나머지(카카오페이·AIA·신한이지 item15/29/32)는 억원 정수 반올림 수준의 잔차지만 같은 이유로
      전값으로 통일한다.

Usage: ...python scripts/fix_nonapplier_after_drift.py [--dry-run]
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

REPO = Path(__file__).resolve().parent.parent
TARGET = REPO / "kics_disclosure.json"

# Keep in sync with _TRANSITION_APPLIERS in scripts/validate_kics_disclosure.py
APPLIERS = frozenset({
    "KR0070", "KR0071", "KR0072", "KR0073", "KR0076", "KR0082", "KR0083",
    "KR0097", "KR0100", "KR1010", "KR1011", "KR0104", "KR0049", "KR0002",
    "KR0003", "KR0004", "KR0005", "KR0032",
})
ITEMS = list(range(15, 27)) + list(range(29, 47))   # 요구자본측만. 1-13(자본 티어)은 TFI가 건드린다.


def _num(v):
    try:
        return float(str(v).replace(",", ""))
    except (TypeError, ValueError):
        return None


def main() -> int:
    dry = "--dry-run" in sys.argv
    data = json.loads(TARGET.read_text(encoding="utf-8"))
    fixed = []
    for r in data:
        c = r.get("원보험사코드")
        if c in APPLIERS:
            continue
        try:
            it = int(r["항목번호"])
        except (TypeError, ValueError, KeyError):
            continue
        if it not in ITEMS:
            continue
        pre, post = _num(r.get("값")), _num(r.get("값_적용후"))
        if pre is None or post is None:
            continue
        if abs(pre - post) <= max(0.005, 0.0005 * abs(pre)):
            continue
        fixed.append((c, r.get("원수사명", c), r["공시분기"], it, r.get("값_적용후"), r.get("값")))
        if not dry:
            r["값_적용후"] = r["값"]

    print(f"{'DRY-RUN ' if dry else ''}비적용사 적용후 오염 {len(fixed)}셀")
    for c, nm, q, it, old, new in sorted(fixed):
        print(f"  {c} {nm:<12} {q} item{it:>2}: {old} -> {new}")
    if not dry and fixed:
        TARGET.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"wrote {TARGET.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
