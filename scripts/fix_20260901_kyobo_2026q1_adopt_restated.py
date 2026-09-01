# -*- coding: utf-8 -*-
"""교보생명(KR0073) 2026.1Q — 적용전 컬럼을 발행사 재작성값으로 채택한다 (owner 결정 2026-09-01).

## 무슨 일인가
발행사가 2026.2Q 공시본의 `직전분기(26.1Q)` 칸에 1분기 값을 **다르게 인쇄**했다(소급 재작성).
2026.2Q 공시본이 사유도 직접 적었다 — *"지급여력기준금액 : 종속회사 인수에 따른 기타요구자본
증가, 감독원 계리적가정 가이드라인 반영으로 인한 보험위험액 증가"*
(`data/disclosure/FY2026_Q2/parsed/KR0073_교보생명보험.md` L455).

39사 전수 스캔 결과 2026.1Q→2Q 구간에서 재작성한 회사는 **교보 한 곳뿐**이다
(`scripts/detect_kics_restatement.py`, 830칸 비교, 미비교 0칸).

## owner 결정
"매번 덮어쓰라는 건 아니지만 이번처럼 딱 명확히 발견된 거면 안 고칠 이유가 없다" (2026-09-01).
→ 이 버킷은 **as_restated 를 채택**한다. `data/_gold/kics_restatement_ledger.json` 의
기본 정책(as_filed)에 대한 **건별 예외**로 등재하고, 게이트가 그 기준으로 검사하게 한다.

## 범위 — 적용전만이다
2026.2Q 공시본의 경과조치 표(공통TFI·②·③)에는 **직전분기 칸이 없다** — 당분기의 전/후만
인쇄한다(같은 MD L463-540 실측). 즉 발행사는 **재작성된 적용후 수치를 공시하지 않았다.**
그래서 `값_적용후` 는 원공시본(as_filed) 그대로 둔다. 없는 숫자를 유도해 채우지 않는다.

## 출처
- as_filed  : data/disclosure/FY2026_Q1/raw/KR0073_교보생명보험.pdf p14
- restated  : data/disclosure/FY2026_Q2/pdf/KR0073_교보생명보험.pdf p15
              (= parsed MD L425-445 `해당분기(26.2Q) | 직전분기(26.1Q) | 전전분기(25.4Q)` 표의 2열)

실행:
    C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/fix_20260901_kyobo_2026q1_adopt_restated.py [--apply]
"""
from __future__ import annotations
import json, sys, shutil
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]
sys.stdout.reconfigure(encoding="utf-8")
MASTER = ROOT / "kics_disclosure.json"
CODE, Q = "KR0073", "2026.1Q"

# item -> (as_filed 기대값, restated 새값)   ※ 전부 적용전(`값`) 컬럼
RESTATED = {
    1:  (149556.0, 149557.0),   # 가.지급여력금액
    2:  ( 67581.0,  67582.0),   # 기본자본
    4:  (146041.0, 146042.0),   # Ⅰ.순자산
    11: ( 51169.0,  51170.0),   # 7.조정준비금
    14: ( 92362.0,  93233.0),   # 나.지급여력기준금액
    15: (105171.0, 106059.0),   # Ⅰ.기본요구자본
    16: ( 38077.0,  38522.0),   # 분산효과
    19: ( 54674.0,  55453.0),   # 3.시장위험액
    20: ( 25686.0,  26239.0),   # 4.신용위험액
    22: ( 14697.0,  14713.0),   # Ⅱ.법인세조정액
}
# 파생값(마스터 규칙: item27=item1/item14x100, item28=item2/item14x100)
DERIVED = {27: (1, 14), 28: (2, 14)}


def census(rows):
    combos = {(r["원보험사코드"], r["공시분기"], str(r["항목번호"])) for r in rows}
    filled = sum(1 for r in rows for f in ("값", "값_적용후") if r.get(f) is not None)
    return len(rows), len(combos), filled


def find(rows, item):
    return [r for r in rows if r["원보험사코드"] == CODE and r["공시분기"] == Q
            and str(r["항목번호"]) == str(item)]


def main() -> int:
    apply = "--apply" in sys.argv
    rows = json.loads(MASTER.read_text(encoding="utf-8"))
    before = census(rows)
    print(f"before: rows={before[0]} combos={before[1]} filled={before[2]}")

    targets = []
    for item, (expect, new) in RESTATED.items():
        m = find(rows, item)
        if len(m) != 1:
            print(f"  ABORT item{item}: 행이 {len(m)}개"); return 2
        cur = m[0].get("값")
        curf = None if cur is None else float(str(cur).replace(",", ""))
        if curf is None or abs(curf - expect) > 0.01:
            print(f"  ABORT item{item}: 현재값={cur!r} 기대(as_filed)={expect} — 누가 먼저 고쳤거나 전제가 틀렸다")
            return 2
        targets.append((m[0], item, curf, new))
        print(f"  item{item:<3} {str(m[0]['항목명'])[:34]:<36} {curf:>12,.2f} -> {new:>12,.2f}  Δ{new-curf:>+9,.2f}")

    if not apply:
        print("\n(dry-run) 반영하려면 --apply"); return 0

    for r, item, cur, new in targets:
        r["값"] = new

    # 파생값 재계산
    for item, (num, den) in DERIVED.items():
        m = find(rows, item)
        if len(m) != 1:
            print(f"  ABORT 파생 item{item}: 행이 {len(m)}개"); return 2
        n = float(find(rows, num)[0]["값"]); d = float(find(rows, den)[0]["값"])
        old = m[0].get("값"); m[0]["값"] = n / d * 100.0
        print(f"  item{item:<3} (파생 item{num}/item{den}x100) {float(old):>12,.6f} -> {m[0]['값']:>12,.6f}")

    after = census(rows)
    print(f"after : rows={after[0]} combos={after[1]} filled={after[2]}")
    if after != before:
        print("  ABORT: census 가 변했다 — 값 교체만 해야 한다. 저장하지 않는다."); return 2

    # 항등식 재검산 (적용전)
    g = lambda i: float(find(rows, i)[0]["값"])
    checks = [
        ("item1 = item2 + item3",            g(1),  g(2) + g(3)),
        ("item14 = item15 - item22 + item23", g(14), g(15) - g(22) + g(23)),
        ("item15 = (17+18+19+20+21) - 16",   g(15), sum(g(i) for i in (17, 18, 19, 20, 21)) - g(16)),
        ("item27 = item1/item14x100",        g(27), g(1) / g(14) * 100),
    ]
    for lab, a, b in checks:
        print(f"  검산 {lab:<36} {a:>13,.4f} vs {b:>13,.4f}  Δ{a-b:>+8,.4f}")

    bak = MASTER.with_suffix(f".json.bak_{datetime.now():%Y%m%d_%H%M%S}_kyobo_restated")
    shutil.copy2(MASTER, bak)
    MASTER.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n저장 완료. 백업: {bak.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
