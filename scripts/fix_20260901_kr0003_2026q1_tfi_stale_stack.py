# -*- coding: utf-8 -*-
"""롯데손해보험(KR0003) 2026.1Q — TFI 표의 **스테일 자본스택** 6칸 정정.

## 발단 (owner 발주: inbox/parser/20260901T0418Z)
owner 가 보험 기사(fins.co.kr #109853)의 롯데손보 26.1Q 기본자본 -3,509억이 우리 마스터
(item2=-3,962억)와 달라 기사가 틀렸다고 봤다가, raw PDF 를 fitz 로 다시 읽고 **원문 자체에
분기가 뒤섞인 자기모순**이 있는 것을 확인했다. docling 파싱 오류가 아니다.

## 증거
`data/disclosure/FY2026_Q1/raw/KR0003_롯데손해보험.pdf` p21
`[지급여력비율의 경과조치 적용에 관한 사항] (1) 공통적용 경과조치 관련` 표:

    지급여력비율(%)     131.93        <- 26.1Q 헤드라인이 맞다 (26,955/20,432 = 131.93 ✓)
    지급여력금액     2,605,850(백만원) <- **25.4Q 값** (26.1Q 는 26,955)
    기본자본         (387,514)        <- **25.4Q 값** (26.1Q item2 는 -3,962)
    지급여력기준금액  2,067,069        <- **25.4Q 값** (26.1Q 는 20,432)

표 자체로 계산하면 26,058.50/20,670.69 = 126.06% 로 **25.4Q 비율**이 나온다. 즉 26.1Q 비율
라벨에 25.4Q 자본스택이 붙어 있다.

마스터에서 재확인(2026-09-01) — 25.4Q 와 26.1Q 가 **소수점까지 동일**:
    item50 -3,875.14 / -3,875.14 · item51 29,933.63 / 29,933.63 · item52 26,058.50 / 26,058.50
그런데 **item54(후순위채무)만 2,136.72 -> 2,111.36 으로 움직였다** — 표 전체 복붙이 아니라
**일부 행만 갱신된 부분 오염**이라 더 안 잡힌다.

## 왜 기존 룰이 못 잡았나
`50_tfi_tier_split`(item50+item51==item52)은 **스테일한 셋끼리 내적으로 닫혀 있다**
(-3,875.14 + 29,933.63 = 26,058.49 ≈ 26,058.50). 표가 **어느 분기 것인지**를 보는 룰이 없다.

## item53(기발행 신종자본증권 45,370백만원)이 26.1Q 값인지 — 확인함
`data/bonds/capital_securities_fy2026h1.json` 의 롯데 항목은 `bs_hybrid_mn: 45370` 이지만
`as_of: 2025-12-31` 이라 **bonds 로는 26.1Q 시점을 독립 확인할 수 없다**(DART 미공시 —
게이트가 CAPSEC_NUMERATOR_ASOF_MISMATCH 로 이미 YELLOW). 다만 바뀌지 않았다고 볼 근거 셋:
  ① 롯데 신종자본증권 2건의 **콜 날짜가 2026-12-17·2026-12-29** — 1분기에 상환될 게 없다
  ② 그 사이 신규 발행 기록 없음
  ③ **item53 이 2026.2Q 에도 453.70** — 별개 공시본에서 따로 파싱된 값이다
→ TFI 델타 +453.70억은 26.1Q 에도 유효하다고 본다.

## 정정 (owner 승인 2026-09-01: "여섯칸 다 옮기기 좋습니다")
헤드라인(item1/2/3, 내적정합 확인됨)으로 갈아끼우고 표의 TFI 델타 +453.70 을 적용한다.
item50 만 고치면 `item50+item51==item52` 가 깨진다 — 스테일한 셋을 통째로 옮겨야 한다.

    item50 전 -3,875.14 -> -3,962.00 (=item2)      후 -3,421.44 -> -3,508.30 (=item2+453.70)
    item51 전 29,933.63 -> 30,918.00 (=item3)      후 29,479.93 -> 30,464.30 (=item3-453.70)
    item52 전 26,058.50 -> 26,955.00 (=item1)      후 26,058.50 -> 26,955.00

-3,508.30 은 기사의 -3,509억과 반올림 오차 내로 일치한다.
item50+item51 = 26,956.00 vs item52 26,955 는 Δ1 (마스터 헤드라인 자체의 반올림).

실행:
    C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/fix_20260901_kr0003_2026q1_tfi_stale_stack.py [--apply]
"""
from __future__ import annotations
import json, sys, shutil
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]
sys.stdout.reconfigure(encoding="utf-8")
MASTER = ROOT / "kics_disclosure.json"
CODE, Q = "KR0003", "2026.1Q"
TFI_DELTA = 453.70          # item53 기발행 신종자본증권 45,370백만원

# item -> (필드, 기대현재값, 새값)
EDITS = [
    (50, "값",       -3875.14, None),   # None = 아래에서 헤드라인으로 채운다
    (50, "값_적용후", -3421.44, None),
    (51, "값",       29933.63, None),
    (51, "값_적용후", 29479.93, None),
    (52, "값",       26058.50, None),
    (52, "값_적용후", 26058.50, None),
]


def census(rows):
    combos = {(r["원보험사코드"], r["공시분기"], str(r["항목번호"])) for r in rows}
    filled = sum(1 for r in rows for f in ("값", "값_적용후") if r.get(f) is not None)
    return len(rows), len(combos), filled


def main() -> int:
    apply = "--apply" in sys.argv
    rows = json.loads(MASTER.read_text(encoding="utf-8"))
    b = census(rows)
    print(f"before: rows={b[0]} combos={b[1]} filled={b[2]}")
    idx = {(r["원보험사코드"], r["공시분기"], str(r["항목번호"])): r for r in rows}

    def head(i):
        r = idx.get((CODE, Q, str(i)))
        return None if r is None or r.get("값") is None else float(r["값"])

    h1, h2, h3 = head(1), head(2), head(3)
    if None in (h1, h2, h3):
        print(f"  ABORT: 헤드라인 결측 item1={h1} item2={h2} item3={h3}"); return 2
    print(f"  헤드라인 26.1Q: item1={h1:,.2f} item2={h2:,.2f} item3={h3:,.2f} "
          f"(item2+item3={h2+h3:,.2f}, Δ{h2+h3-h1:+.2f})")

    NEW = {(50, "값"): h2,             (50, "값_적용후"): h2 + TFI_DELTA,
           (51, "값"): h3,             (51, "값_적용후"): h3 - TFI_DELTA,
           (52, "값"): h1,             (52, "값_적용후"): h1}

    plan = []
    for it, fld, expect, _ in EDITS:
        r = idx.get((CODE, Q, str(it)))
        if r is None:
            print(f"  ABORT item{it}: 행이 없다"); return 2
        cur = r.get(fld)
        curf = None if cur is None else float(cur)
        if curf is None or abs(curf - expect) > 0.01:
            print(f"  ABORT item{it}.{fld}: 현재 {cur!r} != 기대 {expect} — 누가 먼저 고쳤다"); return 2
        new = NEW[(it, fld)]
        plan.append((r, it, fld, curf, new))
        print(f"  item{it}.{fld:<8} {curf:>12,.2f} -> {new:>12,.2f}  Δ{new-curf:>+10,.2f}")

    if not apply:
        print("\n(dry-run) 반영하려면 --apply"); return 0

    for r, it, fld, cur, new in plan:
        r[fld] = new

    a = census(rows)
    print(f"after : rows={a[0]} combos={a[1]} filled={a[2]}")
    if a != b:
        print("  ABORT: census 가 변했다 — 값 교체만 해야 한다"); return 2

    g = lambda i, f="값": float(idx[(CODE, Q, str(i))][f])
    for fld, lab in (("값", "전"), ("값_적용후", "후")):
        s = g(50, fld) + g(51, fld)
        print(f"  검산 [{lab}] item50+item51 = {s:,.2f} vs item52 {g(52, fld):,.2f}  "
              f"Δ{s-g(52,fld):+.2f}")
    print(f"  검산 TFI 델타 [후-전] item50 {g(50,'값_적용후')-g(50,'값'):+,.2f} · "
          f"item51 {g(51,'값_적용후')-g(51,'값'):+,.2f} (기대 ±{TFI_DELTA})")

    bak = MASTER.with_suffix(f".json.bak_{datetime.now():%Y%m%d_%H%M%S}_kr0003tfi")
    shutil.copy2(MASTER, bak)
    MASTER.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n저장 완료. 백업: {bak.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
