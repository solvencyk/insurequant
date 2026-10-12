# -*- coding: utf-8 -*-
"""마이브라운 TIER2_STALE_FALSE_POSITIVE 근거 원장 기록 추가 (owner 승인 2026-10-12). 마커는 게이트 함수로 먼저 재현한다."""
import json, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, "scripts")
import validate_kics_disclosure as K
P = "data/_gold/kics_exemption_provenance.json"
F = "data/disclosure/FY2025_Q3/raw/KR1108_마이브라운반려동물전문보험.pdf"
markers = [
    "보완자본--보완자본한도적용전--보완자본한도--해약환급금부족분상당액중해약환급금상당액초과분--(기발행신종자본증권)-(기발행후순위채무)-지급여력기준금액619619",
    "당사는기발행신종자본증권및후순위채무가없어공통적용경과조치전,후지급여력비율이동일함",
]
v = {"file": F, "pages": [16], "present_markers": markers}
bad, why = K._verify_absent_markers(v)
assert K._verify_markers_ran(v) and not bad, why
e = {
    "registry": "TIER2_STALE_FALSE_POSITIVE",
    "company": "KR1108",
    "quarter": "2025.3Q",
    "claim": "마이브라운 2025.3Q 의 보완자본 한도 3줄(47/48/49)과 TFI 메모행(53/54)이 0 인 것은 직전분기 한도가 잔존한 것(TIER2_LIMIT_STALE)이 아니라 그 분기 원문 표가 대시를 인쇄한 것이다. 소액(지급여력기준금액 1.25억 -> 6.19억)이라 직전분기 기대치 0.63억이 허용오차 안이어서 0 이 전기 한도 지문에 걸리는 소액 오탐이다.",
    "claim_kind": "PRINTED_DASH_MICRO_SCALE_FALSE_POSITIVE",
    "status": "VERIFIED",
    "citation": {"file": F, "pages": [16]},
    "verify": v,
    "note": "validation 2026-10-12: FY2025_Q3 KR1108 p16 (1) 공통적용 경과조치 표(백만원)가 보완자본·보완자본 한도 적용 전·보완자본 한도·해약환급금 상당액 초과분·기발행 신종자본증권·기발행 후순위채무를 전부 `-` 로 인쇄하고 지급여력기준금액 619 / 619(=6.19억), 「기발행 신종자본증권 및 후순위채무가 없어 공통적용 경과조치 전, 후 지급여력비율이 동일함」 주석이 붙는다(마커 2개를 게이트가 매 실행 재확인). 직전분기 2025.2Q 의 47/48/49 도 0 이고 지급여력기준금액은 1.25억이라 값만으로는 재탕과 구분이 안 된다 -- 구분 근거는 원문 이 분기 표가 대시를 직접 인쇄한다는 사실이다. 인메모리 시뮬레이션(data/_derived/validation_registrations_20261012/sim_mybrown_munich.txt): 47/48/49/53/54 = 0 을 (값·값_적용후)에 적재하면 새 RED 는 `47_tier2_census` TIER2_LIMIT_STALE 2건(전·후)뿐이고 나머지는 GREEN/비차단 YELLOW. 이 셀들은 아직 마스터에 없다(parser-kics 가 적재; 적재 전에는 DORMANT 로 인쇄).",
    "registered_by": "owner 승인 2026-10-12 (inbox/validation/20261012T1010Z 「나머지는 다 승인」, TODO.md 결정 ④) -- validation 이 `kics_json_rules.TIER2_STALE_FALSE_POSITIVE` 로 등재. 읽는 쪽 = `_tier2_cross_bucket_context` 의 stale 판정(박제 셀 일치 시에만 지문에서 제외), 보고 = `tier2_stale_false_positive_view`.",
    "not_a_blanket_skip": "(회사,분기) 한 칸. 그 컬럼의 47/48/49 가 적재돼 있고 박제값(0.0)과 정확히 같을 때만 지문에서 뺀다. 다른 값·결측이면 면제가 없어 TIER2_LIMIT_STALE 이 그대로 RED 이고, 원문 마커가 반증되면 EXEMPTION_CITATION_CONTRADICTED RED 다. 다른 분기·회사에는 적용되지 않는다.",
    "scope": "KR1108 2025.3Q `47_tier2_census`(·_post)의 TIER2_LIMIT_STALE 1종. 다른 룰·분기·회사로 넓히지 않는다.",
}
raw = open(P, "rb").read().decode("utf-8")
d = json.loads(raw)
assert not [x for x in d["entries"] if x.get("registry") == e["registry"]]
body = json.dumps(e, ensure_ascii=False, indent=2)
body = "\r\n".join("    " + ln for ln in body.split("\n"))
anchor = "\r\n  ],\r\n  \"_residual_pin_contract\""
assert raw.count(anchor) == 1
new = raw.replace(anchor, ",\r\n" + body + anchor)
json.loads(new)
open(P, "wb").write(new.encode("utf-8"))
print("ok")
