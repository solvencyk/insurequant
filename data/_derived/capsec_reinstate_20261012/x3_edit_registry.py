# -*- coding: utf-8 -*-
"""x3: registry edit after the per-security issuer-treatment test (x2). Text-level edit (keeps the inline style).

 - 하나생명 제1회 (KR0097, 2023-03-31) and 교보 2024-11-12 (KR0073): type tier2 -> tier1 (follow the issuer's own K-ICS
   treatment, owner 2026-10-12); issuer_type removed (type now equals the issuer treatment); term-based reading
   (step-up) kept only in the new internal field terms_note.
 - every other security the registry types tier2 (10 companies): new field issuer_check = result of the x2 test.
   CONFIRMED -> type unchanged; INCONCLUSIVE (푸본 600 / 농협생명 제5회 / 코리안리 제6회) -> type kept, no guess.
Run once (repo root): C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe data/_derived/capsec_reinstate_20261012/x3_edit_registry.py
"""
import json
import re
import sys
from pathlib import Path

REG = Path("data/bonds/capital_tier_registry.json")
EV = "data/_derived/capsec_reinstate_20261012/x2_per_security_x_test.txt"
STAMP = "발행사 처리 확인 2026-10-12(증빙 " + EV + "): "

CHECK = {
    ("KR0005", "2025-03-21"): "보완자본형 확인. 발행 분기 X(항목13-49) +1,989 = 발행액 1,993(기본자본형이면 +238), 항목 47 +1,998, 발행 전 X 띠 2,591~2,630 이 발행 후에도 이어짐(X-1,993 = 2,620~2,377).",
    ("KR0032", "2024-12-27"): "보완자본형 확인. 발행 분기 X +4,848 = 발행액 4,500 + 잡음(기본자본형이면 +3,102); 이후 7분기 X 4,820~5,125 가 한도(1,344~1,642) 변동에 안 움직임.",
    ("KR0050", "2024-05-14"): "보완자본형 확인. 발행 분기 X +974 = 발행액 1,000(기본자본형이면 +733), 발행 전 X 15~39, 이후 8분기 X 1,000~1,052 가 한도(290~463) 상승에 안 움직임.",
    ("KR0050", "2026.2Q"): "보완자본형 확인. 발행 분기 X +992 = 발행액 999(기본자본형이면 +531; 제1회가 보완자본형이라 이 건만 한도에 걸림).",
    ("KR0068", "2024-07-17"): "보완자본형 확인(2024.3Q 두 건 합산 시험, 한 건씩 기본자본형으로 뒤집어도 불일치). 기발행 4,983 이 X 안에 있다가 빠지는 분기라 X +5,590 = 11,000 - 4,983 - 잔차 427; 신종5 만 기본자본형이면 +1,017, 신종6 만이면 +17 로 허용오차(4,020) 밖. 두 건을 따로 가르는 직접 열은 없다.",
    ("KR0068", "2024-09-24"): "보완자본형 확인(2024.3Q 두 건 합산 시험, 신종5 항목 참조).",
    ("KR0068", "2025-03-26"): "보완자본형 확인. 발행 분기 X +5,972 = 발행액 6,000(기본자본형이면 0).",
    ("KR0068", "2025-06-24"): "보완자본형 확인. 발행 분기 X +13,176 = 발행액 13,819 - 잔차 643(기본자본형이면 0, 한도 13,861 안). 이후 X - 4건 합 = 59~408.",
    ("KR0072", "2023-05-19"): "보완자본형 확인. 기발행 2,160(X 안, 2023.1Q X = 항목 53 = 2,160)을 같은 금액으로 갈아탄 분기에 X 불변(기본자본형이면 -1,596); 이후 13분기 X = 항목 6 (오차 0.5 이내)이 한도(1,288~1,613) 변동에 안 움직임.",
    ("KR0072", "2024-12-26"): "보완자본형 확인. 발행 분기 X +245 = 항목 6 증가분 245(액면 250); 기본자본형이면 0.",
    ("KR0073", "2023-05-12"): "보완자본형 확인. 발행 분기 X +4,985 = 발행액(기본자본형이면 0), 기발행 11,089 불변, 이 분기는 X = 항목 6 = 16,074 로 일치.",
    ("KR0083", "2023-02-28"): "판정 불가(현 분류 유지, 추측 안 함). 공시 첫 분기(2023.1Q)가 발행 분기라 발행 전 열이 없고, 600 을 X 에서 빼거나 말거나 나머지가 2,364~3,735 로 ±400 흔들려 가르지 못한다. 발행사 처리는 확인되지 않았으며 분류는 발행조건(스텝업 문구) 기준이다.",
    ("KR0104", "2023-01-31"): "판정 불가(현 분류 유지, 추측 안 함). 공시 첫 분기(2023.1Q)가 발행 분기라 발행 전 열이 없고, 한도(SCR x 10% 최저 2,749)가 발행액 2,500 보다 항상 커서 한도 초과분 변동으로도 못 가른다. 나머지 항목이 보완자본형 가정이면 529~2,017, 기본자본형 가정이면 3,029~4,517. 발행사 처리는 확인되지 않았으며 분류는 발행조건(스텝업 문구) 기준이다.",
    ("KR1000", "2023-03-16"): "보완자본형 확인(수준 시험, 모델의 한도 분리 적용 기준). 2023.2Q~2024.3Q 6분기 X = 기발행 15% 한도 초과분 + 제5회 2,495 가 0.3 이내로 일치(기본자본형 10% 로 읽으면 나머지가 한도 값 1,979~2,162 로 남음). 단 기발행과 제5회 합계에 15% 한도를 함께 씌우는 읽기에서는 같은 숫자가 나와 가르지 못하는데, 모델은 한도를 따로 적용하므로 보완자본형으로 본다.",
    ("KR1000", "2024-10-11"): "판정 불가(현 분류 유지, 추측 안 함). 발행 분기에 기발행 제3회 2,300 상환과 겹치고(기발행 한도초과분 2,324 감소), 항목 6 변동 없이 X 에 +1,7xx(2024.4Q)·+3,456(2025.1Q) 가 따로 들어와 나머지가 0 -> 1,728 -> 5,203 으로 커졌다. 보완자본형 가정 잔차 1,728, 기본자본형 가정 3,909 로 어느 쪽도 0 이 안 된다. 발행사 처리는 확인되지 않았으며 분류는 발행조건(스텝업 문구) 기준이다.",
}

FLIP = {
    ("KR0097", "2023-03-31"): dict(
        evidence="발행사 처리 기준(owner 2026-10-12 「회사에서 그렇게 분류했으면 회사 분류를 따르는 게 맞다」): 하나생명 제1회는 발행사 K-ICS 표가 기본자본 자본증권으로 처리했다. X(항목13-49)가 13분기 중 12분기 발행액 1,799 보다 작아(1,251~1,884) 전액 보완자본형이면 산술상 불가능하고, 기본자본형으로 두면 한도(SCR x 10% = 417~755) 초과분만 재분류돼 나머지 항목이 29~502 로 안정(필요조건 시험, x2 level_hanalife). 발행 직후 항목 47(1,885) < 액면.",
        terms_note="내부 메모(화면 문구 아님): owner 발췌(아시아경제 2023-04-05)는 5년 후 콜 미행사 시 금리가 단계적으로 오르는 스텝업 구조라 발행조건만 보면 보완자본형이나, DART 주석에는 스텝업 문구가 없고 발행사 처리가 우선한다.",
    ),
    ("KR0073", "2024-11-12"): dict(
        evidence="발행사 처리 기준(owner 2026-10-12): 교보 2024-11-12 6,000억은 발행사 K-ICS 표가 기본자본 자본증권으로 처리했다. 발행 분기(2024.4Q) 항목 6 +5,983 인데 X +89(직전 3분기 변동 2~730, 보완자본형이면 +5,983), 항목 47 +202. 기발행이 결속하는 쪽이라 소진율 70.1% 는 type 과 무관하게 같다(기본자본형 신규 5,983 / SCR x 10% = 56.8%).",
        terms_note="내부 메모(화면 문구 아님): 사업보고서 L46354 에 2034-11-12 +1%p 스텝업이 있어 발행조건만 보면 보완자본형이나 발행사 처리가 우선한다.",
    ),
}

NOTES = [
    ('"note": "소진율 = max(기발행 11,089 / SCR x 15% = 70.1%, 기본자본형 신규 0) = 70.1%(2024-11 건을 발행사처럼 기본자본형으로 보면 5,983 / SCR x 10% = 56.8% 로 여전히 기발행이 결속 - 숫자 불변)."',
     '"note": "소진율 = max(기발행 11,089 / SCR x 15% = 70.1%, 기본자본형 신규 5,983 / SCR x 10% = 56.8%) = 70.1%(2024-11 건을 발행사 처리대로 기본자본형으로 분류 2026-10-12 - 기발행이 결속해 숫자 불변)."'),
    ('"note": "소진율 = 기본자본형 신규 0 / SCR x 10% = 0%(재분류 2026-10-12: 종전 238.2%). 발행사는 일부를 기본자본으로 인정(issuer_type=tier1)."',
     '"note": "소진율 = 기본자본형 신규 1,799 / SCR x 10% = 238.2%. 발행사 처리대로 기본자본형으로 분류(2026-10-12; 발행사는 한도 초과분 약 1,044억만 보완자본으로 재분류)."'),
    ('600억은 보완자본형 확정, 항목 6 - 항목 53 - 600 = 50억(2024.4Q~, 채권원장에 없음)만 미확정이라 type_unconfirmed 를 남긴다(결속하지 않아 숫자에는 영향 없음)."',
     '600억은 발행조건 기준 보완자본형으로 두되 발행사 처리는 판정 불가(issuer_check), 항목 6 - 항목 53 - 600 = 50억(2024.4Q~, 채권원장에 없음)만 미확정이라 type_unconfirmed 를 남긴다(결속하지 않아 숫자에는 영향 없음)."'),
    ('(제5회 2,500억은 보완자본형 확정이라 기본자본 자본증권에서 제외; 종전 상한 72.7%)."',
     '(제5회 2,500억은 발행조건 기준 보완자본형으로 제외, 발행사 처리는 판정 불가(issuer_check); 종전 상한 72.7%)."'),
    ('(신규 4,800억 두 건은 보완자본형 확정이라 제외; 종전 상한 205.1%)."',
     '(신규 4,800억 두 건은 보완자본형으로 제외: 제5회는 발행사 처리 확인, 제6회는 판정 불가(issuer_check); 종전 상한 205.1%)."'),
]

TOP = [
    ('"updated": "2026-10-12 (재공개 라운드: 하나생명·푸본·농협생명·코리안리 확정, issuer_type 신설)"',
     '"updated": "2026-10-12 (발행사 처리 기준 재확인: 하나생명 제1회·교보 2024-11 을 기본자본형으로, 나머지 보완자본형은 증권별 X 검정 결과를 issuer_check 에 기록)"'),
    ('"tier2": "보완자본형 - 기본자본요건을 못 맞춘(스텝업 등) 자본증권. [별표22] Ⅲ.2.다.(2) 로 기본자본에서 빼 보완자본으로 분류하므로 기본자본 소진율 분자에서 제외한다. 산식은 이 형의 amount_eok 합계를 뺀다."',
     '"tier2": "보완자본형 - 발행사 K-ICS 표가 보완자본([별표22] Ⅲ.2.다.(2))으로 처리한 자본증권. 기본자본에서 빼 보완자본으로 분류하므로 기본자본 소진율 분자에서 제외한다. 산식은 이 형의 amount_eok 합계를 뺀다. 분류 기준은 발행사 처리다(owner 2026-10-12): 발행조건·기사 해석은 terms_note 에만 적고 type 에는 반영하지 않는다."'),
    ('"issuer_type_policy": "증권별 선택 필드 issuer_type = ',
     '"type_basis_policy": "type 은 발행사가 K-ICS 공시에서 실제로 처리한 형을 따른다(owner 2026-10-12 「회사에서 그렇게 분류했으면 회사 분류를 따르는 게 맞다」). 판정은 증권별 X 검정(x2_per_security_x_test): 발행 분기 X(항목13-49)가 발행액만큼 오르면 보완자본형, 한도 초과분만 오르거나 안 오르면 기본자본형. 증권별 결과는 issuer_check, 판정 불가는 현 분류 유지 + 그렇게 표시. 2026-10-12 현재 type 과 발행사 처리가 다른 증권은 없다(issuer_type 을 쓰는 증권 0건).",\n  "issuer_type_policy": "(현재 사용 0건) 증권별 선택 필드 issuer_type = '),
]


def main():
    t = REG.read_bytes().decode("utf-8")
    assert "\r\n" not in t
    for old, new in TOP + NOTES:
        assert t.count(old) == 1, old[:60]
        t = t.replace(old, new)
    t = t.replace('"data/_derived/capital_utilization_apply_20261012/a1_bond_ledger_hybrids.txt"\n  ]',
                  '"data/_derived/capital_utilization_apply_20261012/a1_bond_ledger_hybrids.txt",\n    "' + EV + '"\n  ]')
    out, code, seen = [], None, set()
    for line in t.split("\n"):
        m = re.match(r'^    "(KR\d{4})": \{$', line)
        if m:
            code = m.group(1)
        if code and line.startswith('        {"name"'):
            tail = "," if line.endswith("},") else ""
            d = json.loads(line.strip().rstrip(","))
            key = (code, d["issue_date"])
            if key in FLIP:
                f = FLIP[key]
                assert d["type"] == "tier2" and d.get("issuer_type") == "tier1"
                d["type"] = "tier1"
                del d["issuer_type"]
                d["evidence"] = f["evidence"]
                d["terms_note"] = f["terms_note"]
                d["issuer_check"] = STAMP + ("기본자본형 확인(위 evidence 참조). 이전 분류 보완자본형 -> 기본자본형으로 변경.")
                seen.add(key)
                line = "        " + json.dumps(d, ensure_ascii=False) + tail
            elif d["type"] == "tier2":
                assert key in CHECK, key
                d["issuer_check"] = STAMP + CHECK[key]
                seen.add(key)
                line = "        " + json.dumps(d, ensure_ascii=False) + tail
        out.append(line)
    t2 = "\n".join(out)
    assert seen == set(CHECK) | set(FLIP), (set(CHECK) | set(FLIP)) - seen
    json.loads(t2)
    REG.write_bytes(t2.encode("utf-8"))
    print("edited", REG, "securities touched", len(seen))


if __name__ == "__main__":
    sys.exit(main())
