# -*- coding: utf-8 -*-
"""원장(kics_exemption_provenance.json) 구조 동기화 — 2026-08-24 validation.

바꾸는 것 (전부 **근거 기록**이고, 면제를 새로 추가하거나 억제하지 않는다):
  ① 부재형 면제 2건에 `absent_cells` 신설 — "어느 셀이 원천에 없는가" 를 명제로 적는다.
     종전엔 (회사,분기) 통째 면제라 이 명제가 원장 어디에도 없었고, 그래서 하나생명
     2024.4Q 의 적용후 4셀이 stale/결측인 채로 살아남았다(게이트 출력 바이트 동일).
  ② KR0075 3분기의 `expected_residual` 축 목록을 코드 박제와 맞춘다(감사 H3).
     숫자는 원래 맞았고 **어떤 축을 박제했는가** 가 어긋나 있었다.
게이트 `_pin_ledger_agreement_findings` 가 이 동기화를 매 실행 강제한다."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LED = ROOT / "data" / "_gold" / "kics_exemption_provenance.json"
led = json.loads(LED.read_text(encoding="utf-8"))


def find(reg, company, quarter, status=None):
    hits = [e for e in led["entries"]
            if e.get("registry") == reg and e.get("company") == company
            and e.get("quarter") == quarter
            and (status is None or e.get("status") == status)]
    assert len(hits) == 1, (reg, company, quarter, len(hits))
    return hits[0]


changed = []

# --- ① 부재형 면제: 셀 단위 부재 박제 --------------------------------------
e = find("_AFTER_SUBRISK_NOT_DISCLOSED", "KR0097", "2024.4Q")
e["absent_cells"] = list(range(29, 36)) + list(range(36, 41))
e["absent_cells_note"] = (
    "원천에 적용후 컬럼이 없는 항목. 29~35(생명장기 7 하위위험) = 기존 claim 그대로. "
    "36~40(시장 5 하위위험) = 2026-08-24 재감사가 추가 확인 — raw p301~309 B.2 시장리스크 절에 "
    "'경과조치' 0회. 종전엔 이 사실이 원장 어디에도 없이 축 19가 면제되고 있었다. "
    "**축 15후(기본요구자본)는 박제하지 않는다** — p281 이 여섯 값(17·18·19·20·21후)을 전부 "
    "인쇄하고 산수도 닫힌다(실측 diff +0.0043, tol 2.0). 종전 (회사,분기) 통째 면제는 그 축까지 "
    "근거 없이 사각으로 넣고 있었다(감사 H8).")
e["note"] += (
    " **2026-08-24 재설계**: 이 면제는 더 이상 축을 순회에서 빼지 않는다. `absent_cells` 의 셀이 "
    "결측이면 그 셀을 입력으로 쓰는 축만 `SOURCE_ABSENT_PINNED` 로 미판정 처리되고 셀 번호가 "
    "게이트에 인쇄된다. 값이 나타나면 면제는 그 셀에 대해 즉시 무효이고 축이 되살아나 검산한다. "
    "**사고 기록**: 이 면제가 축을 통째로 눈감기던 동안 마스터의 item33후·item34후가 직전분기 값 "
    "복사(942.86·896.15)였고 item30후·item35후는 결측이었다. 정정 전/후 마스터로 게이트를 각각 "
    "돌려도 출력이 바이트 동일했다 = false-green. parser 가 2026-08-24 에 item33후 1377.71 · "
    "item34후 714.73 · item30후 0 · item35후 0 으로 정정했고, 지금은 R7 집계가 공시 item17후 "
    "2,001.90 을 잔차 −0.004 로 재현한다.")
changed.append("KR0097 2024.4Q absent_cells")

e = find("_POST_PARENT_NOT_DISCLOSED", "KR0049", "2024.3Q")
e["absent_cells"] = list(range(15, 24))
e["absent_cells_note"] = (
    "적용후 컬럼이 원천에 없는 항목 = 요구자본 부모 15~23 **만**. item1/2/3/14/27/28후는 "
    "FY2024_Q4 p36 [지급여력비율 총괄] 에서 확정 가능하고 실제로 마스터에 실려 있다 — "
    "종전 (회사,분기) 통째 면제는 그 여섯까지 continuity census 밖으로 뺐다(claim 보다 넓은 면제).")
e["citation"]["also"] = {
    "file": "data/disclosure/FY2024_Q4/raw/KR0049_악사손해보험.pdf",
    "pages": [36, 42, 43],
    "why": ("claim 두 번째 문장(=데이터가 실제로 온 곳)의 근거. 2026-08-24 재감사가 직접 판독: "
            "p36 [지급여력비율 총괄]이 과거분기 적용후로 싣는 것은 비율·지급여력금액·"
            "지급여력기준금액 3줄뿐(당분기-1분기 = 지급여력기준금액후 1,939 · 비율후 286.5), "
            "p42 경과조치 세부표는 당분기(2024.4Q) 1열 전용이라 과거분기 컬럼이 없고, "
            "p43 (3)최근 3개 사업연도 주요 변동요인은 당기/직전년도 결산만이라 분기 컬럼이 없다. "
            "→ 2024.3Q 의 15~23후는 어느 원천에도 없다. 종전 verify 블록은 FY2024_Q3 파일만 "
            "가리켜 이 두 번째 근거가 매 실행 재확인되지 않는 산문이었다(감사 지적).")}
changed.append("KR0049 2024.3Q absent_cells + FY2024_Q4 인용")

# --- ② KR0075 3분기: 박제 축 목록을 코드와 일치 -----------------------------
e = find("_TIER2_ISSUER_INCONSISTENT", "KR0075", "2024.3Q")
er = e["expected_residual"]
assert "47_tier2_census|적용후" in er
er.pop("47_tier2_census|적용후")
er["47_tier2_census_post|적용후"] = None
changed.append("KR0075 2024.3Q 축 키 오탈 정정(47_tier2_census|적용후 → _post)")

for q in ("2024.4Q", "2025.1Q"):
    e = find("_TIER2_ISSUER_INCONSISTENT", "KR0075", q)
    er = e["expected_residual"]
    er.setdefault("47_tier2_census|적용전", None)
    er.setdefault("47_tier2_census_post|적용후", None)
    changed.append(f"KR0075 {q} census 축 2개 결손 보충")

led["_residual_pin_contract"] = (
    (led.get("_residual_pin_contract", "") or "")
    + " **2026-08-24 — 이 숫자는 이제 기계가 읽는다.** 게이트 "
      "`validate_kics_disclosure._pin_ledger_agreement_findings` 가 매 실행 코드 박제"
      "(`_TIER2_ISSUER_INCONSISTENT` / `_LIFE8_ISSUER_INCONSISTENT` / "
      "`IRR_DERIVE_ISSUER_INCONSISTENT` 의 residual, `_AFTER_SOURCE_ABSENT_CELLS` / "
      "`_POST_PARENT_SOURCE_ABSENT_CELLS` 의 absent_cells)와 이 원장을 대조한다. "
      "축 목록·잔차값·부재셀집합 중 하나라도 어긋나면 `EXEMPTION_PIN_LEDGER_DISAGREE` RED 다. "
      "정본은 코드(게이트를 실제로 움직이는 쪽)이고 원장은 반드시 일치해야 하는 사본이다. "
      "그 전까지 `expected_residual` 을 읽는 코드가 **하나도 없어서** 원장 숫자는 장식이었고, "
      "실제로 KR0075 3분기의 축 목록이 어긋난 채 아무도 못 보고 있었다. "
      "`expected_residual_alt_reading` 은 종전 읽기의 보존 기록이라 대조 대상이 아니다.")

LED.write_text(json.dumps(led, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print("ledger updated:")
for c in changed:
    print("  -", c)
