# -*- coding: utf-8 -*-
"""KR0075(비엔피파리바카디프생명보험) 2023.4Q PL_breakdown item3~7(생명장기 원수손익 분해)을
DART 감사보고서 §14(4) 측정요소별 변동내역(원수, 당기) 표에서 산출해 user_pl_cells.json 에 UPSERT.

CSM_waterfall 갱신(probe_20260911_apply_csm_override_kr0075.py)으로 새로 뜬 RED
PL_CSM_AMORT_VS_WATERFALL(item4=None vs CSM_waterfall 상각 86.8억)을 해소하는 것이 직접
목적 -- 같은 원수 표에서 item3/5/6 도 같이 뽑히므로 함께 채운다. item1/2/8(재보험 부호관례
미검증)은 이번엔 채우지 않는다(아래 note 참조).

단위: 백만원(PL_breakdown 마스터 관례). 원천 표는 천원 -> /1000.
행 매핑(원문 라벨 -> 합계 컬럼, 천원):
  item3 생명장기 원수손익   = '보험서비스결과 합계'               = -10,596,067
  item4 원수 CSM상각        = '보험계약마진상각'                  =  -8,684,565
  item5 원수 위험조정 변동  = '비금융위험에 대한 위험조정의 변동'  =  -2,624,504
  item6 원수 예실차         = '경험조정'                           = -41,152,756
  item7 기타 생명장기 원수손익 = item3-(item4+item5+item6) (플러그, 도메인 SOT 공식)
       = -10,596,067 - (-8,684,565-2,624,504-41,152,756) = 41,865,758
       (교차검산: 신계약인식효과789,729+48,775,552... 아 오타, 재계산은 스크립트 docstring 아래)
       검산: 손실부담계약손익환입(789,729)+신계약인식효과(48,775,552)+보험계약마진조정추정치
       변동(0)+발생사고이행현금흐름변동(-7,699,523) = 41,865,758 (동일 -- 두 경로 일치, 잔차 0)
"""
import json
from pathlib import Path

PATH = Path("data/_gold/user_pl_cells.json")

NOTE = (
    "DART 감사보고서 원수 §14(4) 측정요소별 변동내역표(1)당기, 단위 천원 -- "
    "data/dart/FY2023_Q4/raw/KR0075_비엔피파리바카디프생명보험_20240403001384/"
    "20240403001384_00760.xml. item3=보험서비스결과 합계(-10,596,067천원), "
    "item4=보험계약마진상각(-8,684,565천원, CSM_waterfall item5 CSM상각 -86.84565억원과"
    " 원단위까지 일치 -- PL_CSM_AMORT_VS_WATERFALL RED 해소), "
    "item5=비금융위험에대한위험조정의변동(-2,624,504천원), item6=경험조정(-41,152,756천원),"
    " item7=플러그(item3-(4+5+6)=41,865,758천원, 신계약인식효과+손실부담계약손익환입+"
    "발생사고이행현금흐름변동 합과 교차검산 일치, 잔차 0). item1/2(보험손익/생명장기손익)와"
    " item8(생명장기재보험손익)은 출재(재보험) 측 부호관례를 이번 세션에서 독립검증하지"
    " 못해 미기입(추후 별도 확인 필요) -- item13/14(자동차/일반)는 기존 0으로 이미 확정."
    " (inbox/parser/20260902T1200Z, 2026-09-11 parser/ifrs17)"
)

NEW_SET = [
    {"원보험사코드": "KR0075", "항목번호": 3, "공시분기": "2023.4Q", "값": -10596.067, "was": None, "note": NOTE},
    {"원보험사코드": "KR0075", "항목번호": 4, "공시분기": "2023.4Q", "값": -8684.565, "was": None, "note": NOTE},
    {"원보험사코드": "KR0075", "항목번호": 5, "공시분기": "2023.4Q", "값": -2624.504, "was": None, "note": NOTE},
    {"원보험사코드": "KR0075", "항목번호": 6, "공시분기": "2023.4Q", "값": -41152.756, "was": None, "note": NOTE},
    {"원보험사코드": "KR0075", "항목번호": 7, "공시분기": "2023.4Q", "값": 41865.758, "was": None, "note": NOTE},
]


def main():
    doc = json.loads(PATH.read_text(encoding="utf-8"))
    existing_keys = {(s["원보험사코드"], s["항목번호"], s["공시분기"]) for s in doc["set"]}
    added = 0
    for s in NEW_SET:
        key = (s["원보험사코드"], s["항목번호"], s["공시분기"])
        if key in existing_keys:
            print(f"SKIP (already present) {key}")
            continue
        doc["set"].append(s)
        added += 1
        print(f"ADD {key}: {s['값']}")
    PATH.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nadded={added} total_set={len(doc['set'])}")


if __name__ == "__main__":
    main()
