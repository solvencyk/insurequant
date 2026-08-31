# -*- coding: utf-8 -*-
import sys, io, json, copy
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = r"C:\Users\sangwook.cho\Desktop\insurequant"
MASTER = ROOT + r"\kics_disclosure.json"

with open(MASTER, "r", encoding="utf-8") as f:
    rows = json.load(f)

def get_label(code, quarter, item):
    for r in rows:
        if r.get("원보험사코드") == code and r.get("공시분기") == quarter and int(r.get("항목번호", -1)) == item:
            return r.get("항목명")
    return None

def get_value(code, quarter, item):
    for r in rows:
        if r.get("원보험사코드") == code and r.get("공시분기") == quarter and int(r.get("항목번호", -1)) == item:
            return r.get("값")
    return None

# byte-exact labels pulled straight from the master (not retyped)
labels_from_2026q2 = {i: get_label("KR1000", "2026.2Q", i) for i in [16,17,18,19,20,21,22,23,29,30,31,32,33,34,35]}
labels_from_2025q4 = {i: get_label("KR1000", "2025.4Q", i) for i in [36,37,38,39,40,41,42,43,44,45,46]}
values_2026q2_2935 = {i: get_value("KR1000", "2026.2Q", i) for i in [29,30,31,32,33,34,35]}

print("=== labels sourced from KR1000 2026.2Q (existing 값 rows) ===")
for i, lbl in labels_from_2026q2.items():
    print(f"item{i}: {lbl!r}")
print("=== labels sourced from KR1000 2025.4Q (36-46 template) ===")
for i, lbl in labels_from_2025q4.items():
    print(f"item{i}: {lbl!r}")

assert all(v is not None for v in labels_from_2026q2.values()), "missing label in 2026.2Q!"
assert all(v is not None for v in labels_from_2025q4.values()), "missing label in 2025.4Q!"
assert all(v is not None for v in values_2026q2_2935.values()), "missing 값 for 29-35 in 2026.2Q!"

# --- values (억원), derived above and self-check-verified against the real rule engine ---
mirror_values = {   # items 16-23: 전 already loaded in master; 후 = mirror (TFI doesn't touch SCR)
    16: 15525, 17: 12903, 18: 15578, 19: 10627, 20: 4247, 21: 2555, 22: 7216, 23: 184,
}
market_irr_mn = {   # 백만원, raw extraction (fitz p.20-21 + MD ④⑤⑥ tables)
    36: 478_074, 37: 716_903, 38: 153_965, 39: 337_815, 40: 1_279,
    41: 5_571_520, 42: 5_598_973, 43: 5_068_868, 44: 6_150_170, 45: 5_517_678, 46: 5_637_558,
}
market_irr_eok = {k: round(v / 100.0, 4) for k, v in market_irr_mn.items()}

evidence = {
    16: "raw PDF p.19 4-2-2)[경과조치 적용 전 지급여력비율 세부] '- 분산효과' 전=15525(마스터 기존값). "
        "코리안리 경과조치 신고내역(공통TFI만 O, 선택 TAC/TIR/TER/TIRR/PCA_DEFER 전부 X, MD 4-2-2 표) "
        "→ 요구자본(15-23)측은 경과조치 미적용이므로 값_적용후=값 미러링. "
        "재검산(자체 스크립트, R4/R6): item16후=Σ(17~21후)-15후=45910-30385=15525, 일치.",
    17: "raw PDF p.19 표 전=12903. TIR(신규보험위험 점진인식) 미적용(X)이므로 값_적용후=값.",
    18: "raw PDF p.19 표 전=15578. 요구자본측 경과조치 미적용이므로 값_적용후=값.",
    19: "raw PDF p.19 표 전=10627. TER(주식위험 점진인식)·TIRR(금리위험 점진인식) 둘 다 미적용 "
        "(MD 4-2-2 (2)③ '당사는 주식위험 경과조치 또는 금리위험 경과조치를 적용하지 않아 경과조치 "
        "전∙후의 금액 및 비율이 동일함') → 값_적용후=값. 재검산: item19후=√(V'·MARKET_M·V), "
        "V=[36~40후] → 10627.11 (diff 0.11, tol 이내).",
    20: "raw PDF p.19 표 전=4247. 요구자본측 경과조치 미적용이므로 값_적용후=값.",
    21: "raw PDF p.19 표 전=2555. 요구자본측 경과조치 미적용이므로 값_적용후=값.",
    22: "raw PDF p.19 표 전=7216(법인세조정액, +magnitude 저장 컨벤션). 요구자본측 경과조치 미적용 "
        "이므로 값_적용후=값. 재검산: item14후=15후-22후+23후=30385-7216+184=23353=마스터 기존 "
        "item14_적용후(23353)와 정확 일치.",
    23: "raw PDF p.19 표 전=184(기타요구자본 1+2+3). 요구자본측 경과조치 미적용이므로 값_적용후=값.",
    29: "raw PDF p.14 6-2-1)② 생명·장기손해보험위험액 현황 표, [-대재해위험 이외] '2026년2분기' "
        "Ⅲ.총계 사망위험=4,343.11(마스터 기존값). item17 축의 경과조치(TAC/TIR/TER/TIRR) 전부 "
        "미적용이므로 값_적용후=값. item17_적용후를 채우면 게이트의 17→29-35 완전성census가 "
        "동시에 열려 값_적용후 필요(부분충전 방지) — 29-35를 통째로 같이 채우는 이유.",
    30: "동일 표 장수위험 Ⅲ.총계=208.09(마스터 기존값). 값_적용후=값.",
    31: "동일 표 장해·질병위험 Ⅲ.총계=6,917.23(마스터 기존값). 값_적용후=값.",
    32: "동일 표 장기재물·기타위험 Ⅲ.총계=287.23(마스터 기존값). 값_적용후=값.",
    33: "동일 표 해지위험 Ⅲ.총계=4,566.36(마스터 기존값). 값_적용후=값.",
    34: "동일 표 사업비위험 Ⅲ.총계=1,200.93(마스터 기존값). 값_적용후=값.",
    35: "[생명·장기손해보험위험액-대재해위험] 표 'Ⅲ.총계' 대재해위험액=3,682.58(마스터 기존값). "
        "값_적용후=값. 재검산(R7): item17후=√(S'R7S)=12902.97 vs disclosed 12903 (diff 0.03, "
        "사실상 일치).",
    36: "docling MD가 6-4.시장위험 관리 절의 ①개념/②금리위험액현황/③주식위험액현황을 통째로 "
        "누락(keyword-window가 raw PDF p.20-21을 skip; p.22 ④부동산위험액현황부터 MD 재개 — "
        "fitz 키워드스캔으로 확인). raw PDF p.20 fitz 직접추출: 6-4-1)②금리위험액현황 표 "
        "'2026년2분기' 블록 'Ⅳ.금리위험액' 행 첫 값=478,074백만원=4,780.74억원. "
        "재검산: irr_derive_expected(41~46)=4780.7444 (diff -0.0044, 사실상 일치). "
        "값_적용후=값(TIRR 미적용, MD 4-2-2(2)③ 확인, 6-2-2 표 '지급여력기준금액 2,335,338=2,335,338' "
        "전=후 로 SCR측 무변 재확인).",
    37: "raw PDF p.21 fitz 직접추출(MD 누락분): ③주식위험액현황 표 '2026년2분기' 블록 "
        "Ⅲ.합계주2)=716,903백만원=7,169.03억원. 값_적용후=값(TER 미적용).",
    38: "docling MD ④부동산위험액현황 표 첫 블록 Ⅲ.합계=153,965백만원=1,539.65억원 "
        "(두번째 블록 147,477백만원이 마스터 KR1000 2025.4Q item38=1474.77과 정확 일치 → "
        "첫 블록=2026.2Q·둘째=2025.4Q 비교 확인됨). 값_적용후=값(시장위험 하위 경과조치 미적용).",
    39: "docling MD ⑤외환위험액현황 표 첫 '계/계' 행=337,815백만원=3,378.15억원 "
        "(둘째 블록 359,314백만원은 비교분기; 부동산과 동일 순서 컨벤션). 값_적용후=값.",
    40: "docling MD ⑥자산집중위험액현황 표 첫 '계/계' 행=1,279백만원=12.79억원. 값_적용후=값.",
    41: "raw PDF p.20 fitz 직접추출: 6-4-1)②금리위험액현황 '2026년2분기' 표 Ⅲ.순자산가치 "
        "'충격전' 컬럼=5,571,520백만원=55,715.20억원. 값_적용후=값.",
    42: "동일 표 Ⅲ.순자산가치 '평균회귀' 컬럼=5,598,973백만원=55,989.73억원. 값_적용후=값.",
    43: "동일 표 Ⅲ.순자산가치 '금리상승' 컬럼=5,068,868백만원=50,688.68억원. 값_적용후=값.",
    44: "동일 표 Ⅲ.순자산가치 '금리하락' 컬럼=6,150,170백만원=61,501.70억원. 값_적용후=값.",
    45: "동일 표 Ⅲ.순자산가치 '금리평탄' 컬럼=5,517,678백만원=55,176.78억원. 값_적용후=값.",
    46: "동일 표 Ⅲ.순자산가치 '금리경사' 컬럼=5,637,558백만원=56,375.58억원. 값_적용후=값.",
}

cells = []
for i in [16,17,18,19,20,21,22,23]:
    v = mirror_values[i]
    cells.append({"항목번호": i, "항목명": labels_from_2026q2[i], "값": v, "값_적용후": v, "근거": evidence[i]})
for i in [29,30,31,32,33,34,35]:
    v = values_2026q2_2935[i]
    cells.append({"항목번호": i, "항목명": labels_from_2026q2[i], "값": v, "값_적용후": v, "근거": evidence[i]})
for i in [36,37,38,39,40,41,42,43,44,45,46]:
    v = market_irr_eok[i]
    cells.append({"항목번호": i, "항목명": labels_from_2025q4[i], "값": v, "값_적용후": v, "근거": evidence[i]})

patch = {
    "company_code": "KR1000",
    "quarter": "2026.2Q",
    "cells": cells,
    "notes": (
        "코리안리재보험 2026.2Q. 경과조치 신고: 공통적용 TFI=O(가용자본 재분류만, item2/3에 영향, "
        "item1/14 불변), 선택적용 TAC/TIR/TER/TIRR/적기시정조치유예=전부 X (raw PDF p.19 4-2-2 표, "
        "data/_derived/kics_transition_applicability.json 의 2026.1Q 동일사 프로필과 일치). "
        "따라서 요구자본측(item15-23)·생명장기 세부(29-35)·시장위험 세부(36-40)·금리위험IRR(41-46) 은 "
        "경과조치 영향이 없어 값_적용후=값 미러링이 근거를 갖는다(4-2-2 표 '지급여력기준금액 "
        "2,335,338=2,335,338' 명시적 전=후 disclosure로 확인). 29-35는 item17후를 채우면서 게이트의 "
        "17→29-35 적용후 완전성census(_PARENT_CHILD_AFTER)가 함께 열려 부분충전 RED로 새로 잡히는 것을 "
        "1차 scratch 검증 라운드에서 실측 확인 후 추가함(항목이 서로 census로 얽혀 있어 15/17/19 세 "
        "parent 축을 한 번에 닫아야 함). 36-46은 docling MD가 raw PDF p.20-21(6-4절 개념/금리위험/"
        "주식위험) 을 keyword-window 파싱범위에서 skip해 통째로 누락한 것을 fitz 직접추출로 복구 "
        "(부동산/외환/자산집중은 p.22+ 라 MD에 남아있었음). 전 항목 kics_json_rules.py의 실제 "
        "MARKET_M/R4/irr_derive_expected 로 재검산 완료 — 잔차: 36_irr diff=-0.0044, 19_market "
        "diff=-0.1115(rel 0.0010%), rule4/15(후) diff=-0.0424, rule5/14(후) diff=0, rule6/16 정확 "
        "일치. 전부 tolerance 이내(대부분 사실상 0)."
    ),
    "unfixable": [],
}

out_path = ROOT + r"\data\_derived\_patch_2026q2_KR1000.json"
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(patch, f, ensure_ascii=False, indent=2)
print(f"\nWrote patch: {out_path} ({len(cells)} cells)")
