# -*- coding: utf-8 -*-
"""KR0087 동양생명 2025.2Q — `2_tier1_bridge` 면제 해제 (2026-08-24 재감사 `OUR_RULE_DEFECT`).

등재 주장("발행사가 자기 각주 주1) 을 어겼다")이 거짓이었다. 각주는 지켜졌고, 틀린 것은
`한도초과 = max(0, item47 − item48)` 이라는 우리 룰의 가정이다 — 발행사가 `한도 적용 전` 행에
한도값을 그대로 인쇄해서 그 식이 구조적으로 0 을 낸다.

`47_tier2_census`(TIER2_DUPLICATE_ROW) 박제는 **유지**한다 — 그건 여전히 발행사쪽 사실이다.
다만 사유를 "우연히 같은 값" 이 아니라 "참 한도적용전 13,295.05 자리에 한도값이 인쇄됨" 으로 바꾼다.

해제된 축은 `contradicted_pins` 에 남겨, 코드에 다시 등재되면 게이트가
`EXEMPTION_PIN_RE_REGISTERED` RED 를 띄운다(한화생명 status=CONTRADICTED tripwire 의 축 단위 판)."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LED = ROOT / "data" / "_gold" / "kics_exemption_provenance.json"
led = json.loads(LED.read_text(encoding="utf-8"))
e = next(x for x in led["entries"]
         if (x.get("registry"), x.get("company"), x.get("quarter"))
         == ("_TIER2_ISSUER_INCONSISTENT", "KR0087", "2025.2Q"))

assert "2_tier1_bridge|적용전" in e["expected_residual"]
e["expected_residual"].pop("2_tier1_bridge|적용전")

e["claim"] = (
    "발행사가 `보완자본 한도 적용 전`(item47) 자리에 **한도값**(item48 = 1,210,705백만)을 "
    "그대로 인쇄했다. 참 한도적용전(채무성 보완자본)은 1,329,509백만이고 그 차이 118,804백만"
    "(=1,188.04억)이 실제 한도초과액이다. 인쇄된 두 줄이 같은 값이라 `47_tier2_census` 가 "
    "`TIER2_DUPLICATE_ROW` 로 잡는다 — 우리 추출은 두 줄 다 원문 그대로다.")
e["claim_kind"] = "ISSUER_ROW_PRINTS_POST_LIMIT_VALUE"
e["note"] = (
    "**2026-08-24 재감사로 사유가 뒤집혔다.** 종전 claim(‘헤드라인표가 자기 각주 주1) 을 어긴다’)은 "
    "거짓이다. 주1) 은 지켜졌고 틀린 것은 우리 룰의 `한도초과 = max(0, item47 − item48)` 가정이었다. "
    "참 한도초과는 같은 TFI 표 적용후 컬럼에서 되짚어진다(헤드라인을 전혀 안 보는 독립 도출): "
    "promo = item2후 − item2전 = 17,563.63 − 14,118 = 3,445.63 (= (기발행 신종자본증권) 3,445.67 과 일치) · "
    "debt_post = item51후 − item49후 = 25,286.65 − 15,437.23 = 9,849.42 · "
    "debt_true = 13,295.05 → 한도초과 = 13,295.05 − 12,107.05 = 1,188.00. "
    "다리에 넣으면 33,001 − (1,188 − 1,188.00) − 18,883 = 14,118.00 = 공시 기본자본(잔차 0.00). "
    "적용후 구성도 같은 참값으로 닫힌다: min(13,295.09 − 3,445.67, 12,107.05) + 15,437.23 = 25,286.65 "
    "= 인쇄 보완자본_후. "
    "**같은 발행사 13분기 전수**에서 2025.4Q·2026.1Q 는 `47 > 48` 을 정상 인쇄하고 현행 룰이 계산한 "
    "한도초과로 다리가 그대로 닫힌다(잔차 0.24 · 0.38) — 즉 이 발행사는 한도초과액을 "
    "`Ⅱ. 불인정 항목` 에 담고 주1) 대로 다시 제외하는 관행이 일관되며, 룰은 47 > 48 인 분기에서는 "
    "이미 그 관행을 올바로 처리하고 있었다. 2025.2Q 만 인쇄 사고로 초과액이 0 이 됐다. "
    "룰 수정 배선: `kics_json_rules._tier2_excess_recovered_from_post` (가드 5개). "
    "전 버킷 시뮬(488): 발동 1 · 해결 1 · **파손 0** "
    "(`scripts/_probes/probe_20260824_v_kr0087_sim.py`). "
    "되짚기 식의 독립 검증: 중복행 가드를 빼면 item47 이 정상 인쇄된 5버킷(KR0076 2023.1Q · "
    "KR0104 2024.4Q~2025.3Q)에서도 발동하는데, 되짚은 초과액이 인쇄값 기반 초과액과 0.41 이내로 일치한다. "
    "남는 `47_tier2_census` 박제의 사유: 발행사가 우연히 같은 값을 두 줄에 인쇄한 것이 아니라 "
    "`한도 적용 전` 자리에 한도값을 인쇄한 것이다.")
e["contradicted_pins"] = {
    "2_tier1_bridge|적용전": (
        "2026-08-24 해제. 잔차 1,188.0 은 발행사 결함이 아니라 **우리 룰 결함**이었다 — "
        "인쇄된 item47 이 이미 한도 적용 후 값이라 `max(0, 47−48) = 0` 이 구조적으로 나왔다. "
        "적용후 컬럼에서 되짚은 참 한도초과 1,188.00 을 쓰면 다리가 잔차 0.00 으로 닫힌다. "
        "이 축을 다시 박제하려는 시도는 `EXEMPTION_PIN_RE_REGISTERED` RED 로 막힌다 — "
        "다시 등재하려면 되짚기(`_tier2_excess_recovered_from_post`)가 왜 틀렸는지를 먼저 보여야 한다.")
}
e["refuted_by"] = ("validation 2026-08-24 면제 재감사 "
                   "(artifacts/validation/reaudit_20260824_KR0075_KR0087_KR0073.md §4)")
e["scope"] = ("KR0087 2025.2Q 의 `47_tier2_census` 축뿐. `2_tier1_bridge` 는 2026-08-24 해제됐다. "
              "다른 (회사,분기)·다른 룰로 넓히지 않는다.")

LED.write_text(json.dumps(led, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print("KR0087 2025.2Q: 2_tier1_bridge 박제 해제 + contradicted_pins tripwire 등재")
