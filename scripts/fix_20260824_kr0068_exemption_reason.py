"""KR0068 2025.2Q 면제 원장의 **사유 텍스트만** 정정한다 (2026-08-24 iter-2 인과 규명).

바꾸지 않는 것: status(VERIFIED_BY_OWNER) · expected_residual(-30,095.0) ·
expected_residual_alt_reading(826.0) · pin_tolerance · verify 마커 · owner_confirmation 의
read_by/date/what_was_read/verdict. 게이트와 변이시험이 그 값들을 기계로 잡고 있고,
룰을 아직 안 고쳤으므로 룰이 내는 잔차는 여전히 -30,095.0 이다.

바꾸는 것: 인과가 "미규명" 이라고 적힌 자유텍스트(claim / claim_kind / note / open_lead /
scope / release_condition). 규명됐는데 미규명이라고 적힌 원장은 다음 세션을 잘못 인도한다.

CRLF·UTF-8(BOM 없음)을 보존한다.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "data" / "_gold" / "kics_exemption_provenance.json"

CAUSE = (
    "item47(보완자본 한도 적용 전)의 **스코프가 발행사마다 다르다.** 한화생명은 item47 에 "
    "item49(해약환급금 부족분 상당액 중 해약환급금 상당액 초과분)를 **포함해서** 인쇄하고, "
    "한도(item48)는 그 나머지(채무성 자본 = item47 - item49)에만 걸린다. "
    "raw 3분기 대조로 확인: 2025.1Q 보완자본 12,225,226 = 한도적용전 12,225,226 "
    "(채무성 5,792,383 < 한도 6,838,221 → 한도 미구속) · 2025.3Q 14,428,486 = 14,428,486 "
    "(채무성 7,023,226 < 한도 7,122,730 → 미구속) · **2025.2Q 만 채무성 7,013,273 > 한도 "
    "6,930,699 → 한도가 82,574백만원(=825.74억) 만큼 구속**하여 보완자본 = 6,930,699 + "
    "6,999,555 = 13,930,254 로 잘렸다. 그 825.74 가 주2) 의 '보완자본 한도를 초과한 금액' "
    "이고, 213,475 - (30,921 - 825.74) - 100,874 = 82,505.74 로 인쇄된 82,506 과 억 반올림 "
    "안에서 닫힌다(잔차 0.26). 대조군(EXCL 관행): IBK연금 2025.3Q 는 한도적용전 403,778 이 "
    "보완자본 695,572 보다 **작고** 해약환급금 343,103 을 따로 더한다 — 같은 행 이름이 두 "
    "관행으로 인쇄된다는 직접 증거."
)

EDITS: list[tuple[str, str]] = [
    # 1) claim — 결론을 뒤집는다. 원문은 모순이 아니라 **자기 안에서 닫힌다**.
    (
        "인과는 규명되지 않았다 — 이 항목은 '발행사 자기모순을 산수로 증명' 한 것이 아니라 "
        "**owner 가 원문을 직접 열어 보고 설명이 없음을 확인한 뒤 원문 그대로 오차를 용인하기로 "
        "결정** 한 것이다.",
        "**2026-08-24 iter-2 에 인과가 규명됐다 — 발행사 자기모순이 아니라 우리 룰의 결함이다.** "
        + CAUSE
        + " 즉 원문(p17·p18)은 자기 안에서 닫히고, -30,095 는 룰이 한도초과를 "
        "max(0, item47-item48)=70,821.29 로 과대계산한 뒤 item12 로 클램프해서 생긴 값이다. "
        "등재는 **룰을 고칠 때까지만** 유지한다(원 등재 근거는 owner 가 원문을 직접 열어 보고 "
        "오차를 용인하기로 한 판단이었다). 재현: "
        "scripts/_probes/probe_20260824_scope_aware_bridge_sim.py "
        "(스코프 인식 한도초과로 이 칸 diff -30,095.00 -> 0.26, 나머지 600칸 무변화·신규 파손 0).",
    ),
    # 2) claim_kind
    (
        '"claim_kind": "ISSUER_UNEXPLAINED_RESIDUAL_OWNER_ACCEPTED"',
        '"claim_kind": "OUR_RULE_MISREADS_item47_SCOPE__owner_accepted_pending_rule_fix '
        '(구 ISSUER_UNEXPLAINED_RESIDUAL_OWNER_ACCEPTED — 2026-08-24 iter-2 규명)"',
    ),
    # 3) note 의 마지막 단정이 **틀렸다** — 825.74 는 원문 세 행에서 나온다.
    (
        "**어느 해석에서도 826/30,095 에 해당하는 항목은 원문에 없다.**",
        "~~어느 해석에서도 826/30,095 에 해당하는 항목은 원문에 없다~~ **← 2026-08-24 iter-2 "
        "에 반증됐다.** 826 에 해당하는 값은 원문 p18 의 세 행에서 그대로 나온다: "
        "(한도적용전 14,012,828 - 해약환급금초과분 6,999,555) - 한도 6,930,699 = 82,574백만원 "
        "= 825.74억. 30,095 쪽은 원문에 없는 것이 맞다 — 그건 룰의 산물이다.",
    ),
    # 4) open_lead — 게이트가 매 실행 인쇄하는 줄이다. 여기서 규명 사실을 말해야 조용해지지 않는다.
    (
        "item51(경과조치표 보완자본) 후 140,128.28 - 전 139,302.53 = 825.75 로 필요 잔차 826.00 "
        "과 반올림 오차 이내다. **설명이 아니다** — 우연일 수 있고 owner 도 원인을 못 찾았다. "
        "이 관계가 규명되면 등재를 재검토한다.",
        "★2026-08-24 iter-2 에 규명됐다(이 review 줄 앞머리의 '인과 미규명' 은 게이트 하드코딩 "
        "문구라 룰 수정 때 같이 고친다). 825.75 는 우연이 아니라 한도 구속액이다 — "
        + CAUSE
        + " 후속: 룰(_validate_tier2_limit 의 한도초과 계산)을 스코프 인식으로 고치면 이 면제는 "
        "불필요해진다. 고치기 전까지 등재 유지.",
    ),
    # 5) scope — "인과 미규명이므로" 가 stale.
    (
        "**인과 미규명이므로 다른 회사·분기에 같은 사유를 적용하지 않는다** — 이 status 는 "
        "선례가 아니다.",
        "**인과는 2026-08-24 iter-2 에 규명됐다(item47 스코프). 그래도 이 등재를 다른 회사·분기로 "
        "넓히지 않는다** — 등재는 룰 수정 전까지의 임시 조치이지 선례가 아니다. 같은 스코프를 "
        "쓰는 회사(전수 투표: KR0004·KR0068·KR0075·KR0079·KR0080)는 **면제가 아니라 룰 수정**으로 "
        "다뤄야 한다. 실측상 그중 한도가 실제로 구속하는 칸은 이 한 칸뿐이다.",
    ),
    # 6) release_condition
    (
        "**인과가 규명되면(티켓 20260824T0410Z) 등재를 재검토한다.**",
        "**인과는 규명됐다(2026-08-24 iter-2, 티켓 20260824T0410Z). 해제 경로는 이제 하나다 — "
        "한도초과 계산을 item47 스코프 인식으로 고치면 RED 가 사라지고 게이트가 "
        "TIER2_EXEMPTION_INERT review 로 '등재를 풀어라' 를 찍는다.** 그 수정은 룰 골든"
        "(tests/test_kics_rules_golden.py, 라이브 마스터에 물려 있음) 재생성과 이 원장의 "
        "박제값 4개(-30,095.0 / 826.0 / branch=CAPPED / gate._TIER2_ISSUER_INCONSISTENT) "
        "동시 갱신을 수반하므로 마스터를 만지는 세션이 없을 때 한 커밋으로 해야 한다.",
    ),
]


def main() -> None:
    txt = LEDGER.read_text(encoding="utf-8", newline="")
    for old, new in EDITS:
        n = txt.count(old)
        if n != 1:
            raise SystemExit(f"replacement target count={n} (expected 1): {old[:70]!r}")
        txt = txt.replace(old, new)
    json.loads(txt)  # 구조 검증
    LEDGER.write_text(txt, encoding="utf-8", newline="")
    raw = LEDGER.read_bytes()
    assert raw[:3] != b"\xef\xbb\xbf", "BOM 이 붙었다"
    d = json.loads(raw.decode("utf-8"))
    e = next(x for x in d["entries"]
             if x.get("company") == "KR0068" and x.get("quarter") == "2025.2Q")
    assert e["status"] == "VERIFIED_BY_OWNER"
    assert e["expected_residual"]["2_tier1_bridge|적용전"] == -30095.0
    assert e["expected_residual_alt_reading"]["2_tier1_bridge|적용전|한도초과=0"] == 826.0
    assert e["pin_tolerance"] == 0.01
    for k in ("read_by", "date", "what_was_read", "verdict"):
        assert e["owner_confirmation"].get(k)
    print("OK: reason text patched at 6 sites; pins/status/markers unchanged")


if __name__ == "__main__":
    main()
