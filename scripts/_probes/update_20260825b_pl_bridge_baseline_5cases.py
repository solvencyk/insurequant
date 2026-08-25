# -*- coding: utf-8 -*-
"""잔존 5건(교보라플 2024.4Q · BNP카디프 2024.4Q/2025.4Q · DB손해 2023.2Q · 흥국화재
2025.1Q) 재조사 결과를 pl_bridge_baseline.json 의 investigated_20260825 에 덧붙인다.
값은 손대지 않는다(등재만 갱신) -- 3건은 "룰 갭"(데이터 아님, validate_master_tables.py
쪽 수정 필요)으로 확정, 2건은 새 가설도 반증됐음을 기록."""
import json
from pathlib import Path

p = Path("data/_gold/pl_bridge_baseline.json")
d = json.loads(p.read_text(encoding="utf-8"))
entries = d["entries"]


def append_note(key, addendum):
    e = entries[key]
    old = e.get("investigated_20260825", "")
    e["investigated_20260825"] = (old + " | 2026-08-25 재조사(2회차, parser-ifrs17): " + addendum)


RULE_GAP_NOTE = (
    "item2(생명장기손익)=item3(원수손익)+item8(재보험손익)-item16(기타사업비용) 로 정확히 "
    "닫힌다({calc}) -- 데이터가 아니라 검증룰(validate_master_tables.py PL_EQS "
    "'생명장기손익 = 원수손익+재보험손익')이 item16 항을 안 쓰는 게 원인이다. "
    "'보험손익(dual)' 식(bare=item2+13+14 / adj=bare+15-16)엔 이미 이 adj-form이 있는데 "
    "이 sub_leg_gap 식에는 없다. item3/item8/item16 셀 값 자체는 전부 정확하다(수정 불요) "
    "-- 룰 쪽에 adj 후보(item3+item8-item16)를 추가해 달라고 validation 에 넘긴다."
)

append_note(
    "교보라이프플래닛생명보험|2024.4Q|생명장기손익 = 원수손익+재보험손익",
    RULE_GAP_NOTE.format(
        calc="item3(-17,846.322598)+item8(-1,907.799346)-item16(6,261.42124)="
             "-26,015.543184=item2, 잔차 0.000000")
    + " (이전 라운드가 'PAA 표 파싱 실패로 raw 못 읽음' 이라 적었던 건 다른 표를 쫓은 것 "
      "-- item16 은 이미 그 표 없이도 정확히 채워져 있었다.)",
)
append_note(
    "비엔피파리바카디프생명보험|2024.4Q|생명장기손익 = 원수손익+재보험손익",
    RULE_GAP_NOTE.format(
        calc="item3(-1,833.578628)+item8(-1,636.546378)-item16(10,169.128183)="
             "-13,639.253189=item2, 잔차 0.000000"),
)
append_note(
    "비엔피파리바카디프생명보험|2025.4Q|생명장기손익 = 원수손익+재보험손익",
    RULE_GAP_NOTE.format(
        calc="item3(-12,261.467528)+item8(-1,813.896)-item16(10,147.580446)="
             "-24,222.943974 vs item2(-24,222.942939), 잔차 0.001(반올림 이내)"),
)
append_note(
    "DB손해보험|2023.2Q|보험손익(dual)",
    "item1(971,297.908122백만원)을 raw 로 독립 재확인(data/dart/FY2023_Q2/raw/"
    "KR0011_DB손해보험/20230814003012.xml @60277, 연결 '보험서비스결과' 행 당기누적 "
    "971,297,908,122원=item1 과 정확 일치) -- item1 자체가 아니라 그 행이 이미 "
    "'보험서비스수익-보험서비스비용(재보험비용+기타사업비용 포함)' 의 NET 결과라서 "
    "item16(70,375.725865, 라벨 '3.기타사업비용' 도 정확 일치)이 이미 item1 안에 흡수돼 "
    "있다 -- 이걸 다시 빼는 adj 공식(bare-item16)이 틀렸다는 이전 결론을 재확인. 새로 "
    "시도: 같은 문서 @198296 에서 별도(standalone) 기준 '보험서비스결과' "
    "911,297,598,639원=911,297.598639백만원 을 찾아 basis-mismatch(연결 vs 별도) 가설도 "
    "테스트했으나 bare(978,167)와의 갭이 오히려 더 벌어져(66,869) 반증. item1/16 자체는 "
    "연결·별도 두 소스 모두로 확증됐고, 남은 6,869 는 LOB(item2/13/14) 쪽의 조정/미배부 "
    "성분으로 추정되나 원문에서 그 행을 특정하지 못했다 -- 미해결 유지.",
)
append_note(
    "흥국화재|2025.1Q|보험손익(dual)",
    "item16(6,266)이 이미 adj 식(bare-item16=58,418)에 적용된 상태에서 잔차 -714 "
    "재확인 -- 전 항목(item2~19) 재검토했으나 714 를 설명할 추가 후보를 못 찾았다. "
    "item13/14(자동차/일반손익, -4,205/2,199)와 item1~24 전부 정수(반올림된 백만원) "
    "단위로만 공시돼 있어 표별 반올림 누적이 유력하나(허용오차 200 대비 3.5배지만 "
    "item1 대비로는 1.2%) 확증할 원문 성분을 못 찾았다 -- 미해결 유지, 새 가설 없음.",
)

p.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
print("updated 5 entries")
for k in entries:
    if k in (
        "교보라이프플래닛생명보험|2024.4Q|생명장기손익 = 원수손익+재보험손익",
        "비엔피파리바카디프생명보험|2024.4Q|생명장기손익 = 원수손익+재보험손익",
        "비엔피파리바카디프생명보험|2025.4Q|생명장기손익 = 원수손익+재보험손익",
        "DB손해보험|2023.2Q|보험손익(dual)",
        "흥국화재|2025.1Q|보험손익(dual)",
    ):
        print(" ", k, "-> note len", len(entries[k]["investigated_20260825"]))
