# -*- coding: utf-8 -*-
"""순자산 상위 생·손보 5사씩의 금리 듀레이션 지표 산출 (owner 2026-08-30 요청).

## 쓸 수 있는 입력이 둘이고 성격이 다르다

(A) `kics_rate_sensitivity.json` — **평행이동 ±50/±100bp** 아래의 지급여력금액(가용자본)·
    지급여력기준금액(요구자본)·지급여력비율. Δy 가 명시돼 있으므로 **유효듀레이션(년)** 으로
    환산할 수 있다. 분기: 2024.4Q · 2025.2Q · 2025.4Q.
(B) `kics_disclosure.json` 항목41~46 — K-ICS **기간구조 충격**(상승/하락/평탄/경사/평균회귀)
    아래의 금리위험 순자산가치. 충격이 만기별로 달라 **단일 Δy 가 정의되지 않으므로 연수로
    환산하지 않는다.** 여기서는 방향과 변동률만 참고로 붙인다.

그래서 연수는 (A)로만 낸다. (B)를 연수로 바꾸려면 감독규정의 만기별 충격곡선이 필요한데
그건 이 저장소에 없다 — 없는 것을 가정해서 만들지 않는다.

## 산식

가용자본(AC)의 유효듀레이션:
    D_AC = -(AC(+100bp) - AC(-100bp)) / (2 · AC(base) · 0.01)        [년]

듀레이션 갭 근사(자산 규모로 환산):
    D_gap ≈ D_AC · (AC(base) / 자산총계)
  ΔE = -(D_A - D_L·L/A)·A·Δy 에서 (ΔE/E)/Δy = -D_gap·(A/E) 이므로 D_gap = D_AC·(E/A).
  **근사인 이유**: AC 는 K-ICS 가용자본(경제적)이고 자산총계는 IFRS17 장부값이라 분모·분자의
  기준이 다르다. 부호와 크기 순서는 유효하지만 소수점 둘째자리를 믿지 말 것.

부호 규약: **양수 = 금리 상승 시 자본 감소**(자산 듀레이션이 더 김) · 음수 = 그 반대.
"""
import json
import sys
from collections import defaultdict

sys.stdout.reconfigure(encoding="utf-8")

Q = "2025.4Q"          # 시나리오표는 짝수분기만 공시 — 현재 마스터 최신 짝수분기
BASIS = "적용전"        # 전 회사 공통 비교 가능한 기준

rs = json.load(open("kics_rate_sensitivity.json", encoding="utf-8"))
kd = json.load(open("kics_disclosure.json", encoding="utf-8"))
bs = json.load(open("IFRS17_BS.json", encoding="utf-8"))

# 가용자본 ±bp (억원)
ac = {}
for r in rs:
    if r["공시분기"] == Q and r["경과조치여부"] == BASIS and r["measure구분"] == "지급여력금액":
        ac[r["원수사명"]] = r

# BS 자산총계·자본총계 (백만원 -> 억원)
bsv = defaultdict(dict)
for r in bs:
    if r["공시분기"] == Q and r["항목번호"] in (1, 3) and r["값"] is not None:
        bsv[r["원수사명"]][r["항목번호"]] = r["값"] / 100.0   # 백만원 -> 억원

# K-ICS 순자산 시나리오 (억원)
irr = defaultdict(dict)
life = {}
for r in kd:
    if r["공시분기"] == Q and r["항목번호"] in range(41, 47):
        _v = r.get("값")
        try:
            _v = float(str(_v).replace(",", "")) if _v is not None else None
        except ValueError:
            _v = None
        irr[r["원수사명"]][r["항목번호"]] = _v
    life[r["원수사명"]] = r["생손보여부"]


def rows_for(kind: str):
    cand = [(n, bsv[n].get(3)) for n in bsv if life.get(n) == kind and bsv[n].get(3)]
    cand.sort(key=lambda x: -x[1])
    return cand[:5]


for kind in ("생명보험", "손해보험"):
    print(f"\n{'=' * 108}")
    print(f"{kind} — 순자산(자본총계) 상위 5사 · {Q} · 경과조치 {BASIS}")
    print("=" * 108)
    print(f"{'회사':<18}{'자본총계':>10}{'자산총계':>11}{'가용자본':>10}"
          f"{'AC(-100bp)':>11}{'AC(+100bp)':>11}{'D_AC(년)':>9}{'D_gap≈':>8}")
    for name, eq in rows_for(kind):
        a = ac.get(name)
        assets = bsv[name].get(1)
        if not a or a.get("base") in (None, 0):
            print(f"{name:<18}{eq:>10,.0f}{(assets or 0):>11,.0f}   금리민감도 미수록")
            continue
        base, up, dn = a["base"], a.get("+100bp"), a.get("-100bp")
        if up is None or dn is None:
            print(f"{name:<18}{eq:>10,.0f}{(assets or 0):>11,.0f}{base:>10,.0f}   ±100bp 결측")
            continue
        d_ac = -(up - dn) / (2 * base * 0.01)
        d_gap = d_ac * (base / assets) if assets else float("nan")
        print(f"{name:<18}{eq:>10,.0f}{(assets or 0):>11,.0f}{base:>10,.0f}"
              f"{dn:>11,.0f}{up:>11,.0f}{d_ac:>9.2f}{d_gap:>8.2f}")

    print(f"\n  [참고] K-ICS 기간구조 충격 아래 금리위험 순자산가치 변동률 (연수 환산 불가)")
    print(f"  {'회사':<18}{'충격전':>12}{'상승':>9}{'하락':>9}{'평탄':>9}{'경사':>9}{'평균회귀':>10}")
    for name, _eq in rows_for(kind):
        m = irr.get(name, {})
        b = m.get(41)
        if not b:
            print(f"  {name:<18}  (41~46 결측)")
            continue
        def pct(i):
            v = m.get(i)
            return f"{(v - b) / b * 100:+.2f}%" if v is not None else "  -"
        print(f"  {name:<18}{b:>12,.0f}{pct(43):>9}{pct(44):>9}{pct(45):>9}"
              f"{pct(46):>9}{pct(42):>10}")

print("\n단위: 억원 · D_AC = 가용자본 유효듀레이션(년) · 양수 = 금리 상승 시 자본 감소")
