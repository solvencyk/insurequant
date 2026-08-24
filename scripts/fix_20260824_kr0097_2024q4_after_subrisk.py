# -*- coding: utf-8 -*-
"""orchestrator 발주(2026-08-24, 재감사기 승계) -- KR0097 하나생명보험 2024.4Q
생명장기 하위위험(item29-35) 값_적용후 4셀 정정.

Source: artifacts/validation/reaudit_20260824_KR0097_KR0049_KR0079_plus_ledger_quality.md
파트 1-A. 이 세션에서 raw PDF·마스터를 독립 재현한 근거는 세션 답변 참조
(probe_20260824b_kr0097_raw_verify.py / probe_20260824_kr0097_phasein.py /
probe_20260824e_kr0097_final_check.py).

## 결함
마스터의 item33_적용후="942.86" / item34_적용후="896.15" 는 2024.3Q 의 동일 항목 값과
바이트 단위로 같다(stale carry-forward). raw p281/p326/p296 어디에도 942.86·896.15·
94,286·89,615 는 없다(전수 grep 0 hit). item30_적용후·item35_적용후 는 애초에 결측.

## 정정 근거 -- phase-in 식이 13분기 중 12분기를 정확히 재현
  적용후_i = max(0, 적용전_i - (1-인식비율) x 최초산출액_i)   i in {장수(30),해지(33),사업비(34),대재해(35)}
  최초산출액(raw p326, 2023-03-31 기준, 천원->억원): 장수 143.25093 / 해지 664.03015 /
    사업비 438.77926 / 대재해 78.47532
  인식비율(연도별, raw p326 "2024년 인식비율 10%"): 2023=0% 2024=10% 2025=20% 2026=30%
2023.1Q~2026.1Q 중 2024.4Q 를 제외한 12분기 전부 이 식으로 derived 값이 마스터 값_적용후와
±0.01억 이내로 일치(부동소수 반올림 수준). 2024.4Q 에 같은 식을 적용하면:
  item30_적용후 = max(0, 95.51 - 0.9x143.25093) = 0.00
  item33_적용후 = 1975.34 - 0.9x664.03015       = 1377.712865 -> round2 = 1377.71
  item34_적용후 = 1109.63 - 0.9x438.77926       =  714.728666 -> round2 =  714.73
  item35_적용후 = max(0, 52.08 - 0.9x78.47532)  = 0.00
R7([230.82,0,391.46,0,1377.71,714.73,0]) = 2001.8958 (raw round-trip 정밀재계산,
probe_20260824e) vs 공시 item17_적용후 raw p281 200,189,811천원 = 2001.89811억
  잔차 -0.0023억(=약 230원, 무시 가능) -- tol(max(10,5%)=100.09) 대비 압도적으로 닫힘.
기존 stale/결측 값으로는 R7=1800.8172, 잔차 -201.08 -- tol 을 2배 넘겨 깨짐(감사보고서
원 서술과 부호는 반대지만 절대값 일치 -- 이 스크립트의 재계산이 정본, 위 docstring 값 사용).

## item30/35 를 "0"으로 채우는 이유(결측 유지가 아니라)
파트 1 규율("파생식으로 채울지는 증거 기준을 넘을 때만"): (a) 이 회사 다른 12분기 전부에서
성립 (b) 채운 값의 R7 이 공시 item17_적용후를 재현. 둘 다 충족. 또한 item30(장수)은 13분기
중 2024.4Q 를 제외한 12분기 전부 "0"(최초산출액이 적용전보다 항상 커서 클램프) -- 같은
패턴. item35(대재해)도 2023.1Q~2024.3Q 까지는 전부 "0"이었다가 2025.1Q 부터 양수로 전환
(적용전이 커지면서) -- 2024.4Q(적용전 52.08)는 여전히 2024.3Q(적용전 43.41, 0)측 패턴이라
"0"이 자연스럽다.

## 면제와의 관계 (건드리지 않음)
이 (KR0097,2024.4Q)는 `_AFTER_SUBRISK_NOT_DISCLOSED` 면제가 `_transition_mmult_after`
버킷 첫머리에서 부모 조회 전에 스킵시켜 이 4셀이 어떤 룰의 검사도 받은 적이 없었다(면제
등재 자체는 참 -- 원문에 항목별 적용후 세부표가 없다는 claim 은 맞다. 다만 그 사실이 마스터
셀의 정확성까지 보증하진 않았다). 면제 로직/레지스트리는 이 스크립트가 건드리지 않는다 --
값만 고친다. 스코프 축소·해제 여부는 owner/validation 판단.

Usage:
  ...python scripts/fix_20260824_kr0097_2024q4_after_subrisk.py --dry-run
  ...python scripts/fix_20260824_kr0097_2024q4_after_subrisk.py
"""
from __future__ import annotations

import json
import sys
import os
from pathlib import Path

sys.stdout = os.fdopen(1, "w", encoding="utf-8", closefd=False)

REPO = Path(__file__).resolve().parents[1]
TARGET = REPO / "kics_disclosure.json"

_MISSING = object()  # sentinel: field must NOT currently exist on the row


def find_row(data, code, q, item_no):
    hits = [r for r in data if r.get("원보험사코드") == code and r.get("공시분기") == q
            and int(r.get("항목번호", -1)) == item_no]
    if len(hits) > 1:
        raise SystemExit(f"FATAL: 중복행 {code} {q} item{item_no}: {len(hits)}건")
    return hits[0] if hits else None


def main() -> int:
    dry = "--dry-run" in sys.argv
    data = json.loads(TARGET.read_text(encoding="utf-8"))
    n0 = len(data)
    print(f"로드 전 row_count = {n0:,}")

    log = []  # (op, code, q, item, field, old, new)

    def upd(code, q, item_no, field, new_val, expect_old):
        r = find_row(data, code, q, item_no)
        if r is None:
            raise SystemExit(f"FATAL: 대상 행 없음 {code} {q} item{item_no}")
        has_field = field in r
        old = r.get(field)
        if expect_old is _MISSING:
            if has_field:
                raise SystemExit(
                    f"FATAL: {code} {q} item{item_no}.{field} 이 신설 예정이었는데 이미 "
                    f"존재함(값={old!r}) -- 동시편집 의심, 중단")
        else:
            if not has_field or str(old) != str(expect_old):
                raise SystemExit(
                    f"FATAL: {code} {q} item{item_no}.{field} 현재값({old!r})이 예상값"
                    f"({expect_old!r})과 다름 -- 동시편집 의심, 중단")
        if has_field and old == new_val:
            log.append(("SKIP(이미반영)", code, q, item_no, field, old, new_val))
            return
        r[field] = new_val
        log.append(("INSERT_FIELD" if not has_field else "UPDATE", code, q, item_no, field, old, new_val))

    # ---- item33/34_적용후: 2024.3Q stale copy -> phase-in 파생값으로 정정 ----
    upd("KR0097", "2024.4Q", 33, "값_적용후", "1377.71", expect_old="942.86")
    upd("KR0097", "2024.4Q", 34, "값_적용후", "714.73", expect_old="896.15")

    # ---- item30/35_적용후: 결측 -> phase-in 파생값(둘 다 클램프로 0) 신설 ----
    upd("KR0097", "2024.4Q", 30, "값_적용후", "0", expect_old=_MISSING)
    upd("KR0097", "2024.4Q", 35, "값_적용후", "0", expect_old=_MISSING)

    print(f"\n=== 변경 로그 ({len(log)}건) ===")
    for op, code, q, item_no, field, old, new in log:
        print(f"  {op:14s} {code} {q} item{item_no}.{field}: {old!r} -> {new!r}")

    n_change = sum(1 for r in log if r[0] in ("UPDATE", "INSERT_FIELD"))
    n_skip = sum(1 for r in log if r[0].startswith("SKIP"))
    print(f"\nUPDATE/INSERT_FIELD={n_change} SKIP={n_skip}")

    if dry:
        print("\n(dry-run; 파일 안 씀)")
        return 0

    if n_change == 0:
        print("변경 없음 -- 파일 안 씀")
        return 0

    TARGET.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nwrote {TARGET.name} (row_count {n0:,} -> {len(data):,})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
