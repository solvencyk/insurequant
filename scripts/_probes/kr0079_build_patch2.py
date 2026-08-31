# -*- coding: utf-8 -*-
"""Build data/_derived/_patch_2026q2_KR0079.json (final)."""
import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(r"C:\Users\sangwook.cho\Desktop\insurequant")

data = json.load(open(ROOT / "kics_disclosure.json", encoding="utf-8"))
by_item = {}
for r in data:
    if r["원보험사코드"] == "KR0079" and r["공시분기"] == "2026.2Q":
        by_item.setdefault(("2026.2Q", r["항목번호"]), r["항목명"])
    if r["원보험사코드"] == "KR0079" and r["공시분기"] == "2025.4Q":
        by_item.setdefault(("2025.4Q", r["항목번호"]), r["항목명"])
TFI_LABELS = {}
for r in data:
    if r["항목번호"] in (47, 48, 49) and r["원보험사코드"] == "KR0079":
        TFI_LABELS[r["항목번호"]] = r["항목명"]
    if r["항목번호"] == 50 and r["원보험사코드"] == "KR1000" and r["공시분기"] == "2023.2Q":
        TFI_LABELS[50] = r["항목명"]
    if r["항목번호"] == 51 and r["원보험사코드"] == "KR1000" and r["공시분기"] == "2023.2Q":
        TFI_LABELS[51] = r["항목명"]
    if r["항목번호"] in (52, 53, 54) and r["원보험사코드"] == "KR0001" and r["공시분기"] == "2023.1Q":
        TFI_LABELS[r["항목번호"]] = r["항목명"]

def label(item):
    if ("2026.2Q", item) in by_item:
        return by_item[("2026.2Q", item)]
    if ("2025.4Q", item) in by_item:
        return by_item[("2025.4Q", item)]
    return TFI_LABELS[item]

item1, item2, item3 = 37207, 23735, 13473
item4, item5 = 34276, 10265
item6 = 0
item7, item8, item9 = 17962, -218, -4828
item10 = 0
item11 = 11096
item12 = 0
item13 = 10542
item14, item15, item16 = 23962, 29924, 8714
item17, item18, item19, item20, item21, item22 = 20349, 0, 12052, 3878, 2359, 5962
item23, item24, item25, item26 = 0, 0, 0, 0
item27 = 37207 / 23962 * 100
item28 = 23735 / 23962 * 100

# life sub-risks (page 24/25, 백만원/100)
item29, item30, item31, item32 = 1842.32, 409.70, 8242.50, 0.0
item33, item34, item35 = 15899.62, 2479.25, 704.81

# market sub-risks (page 28/30/31, 백만원/100)
item36, item37, item38, item39, item40 = 2341.56, 10081.54, 2919.10, 2260.87, 0.0

# IRR net asset value scenarios (page 28, 백만원/100)
item41, item42, item43 = -108292.87, -108136.38, -110728.81
item44, item45, item46 = -106116.93, -107664.13, -108846.48

# TFI table (page 20, 백만원/100)
item47, item48, item49 = 13472.53, 11981.02, 10541.60
item50, item51, item52 = 23734.80, 13472.53, 37207.33
item53, item54 = 0.0, 2930.94

EV_HEADLINE = "p16 [지급여력비율 총괄] / p19 [경과조치 적용 전 지급여력비율 세부] 해당분기(26.2Q) 컬럼, 240dpi 렌더 직독. 26.1Q/25.4Q 비교컬럼이 기존 kics_disclosure.json 값과 바이트 일치(교차검증)."
EV_LIFE = "p24 [생명·장기손해보험위험액-대재해위험 이외] + p25 [...-대재해위험] 당기(2026.2Q) 컬럼, 240dpi 렌더 직독(단위 백만원, /100). 직전반기(25.4Q) 비교컬럼이 마스터와 바이트 일치. item17=sqrt(S'R7S) 검산 20349.23 vs 공시 20349(diff 0.23, GREEN)."
EV_MARKET = "p28 [②금리위험액현황] + p30 [③주식위험액현황 ④부동산위험액현황] + p31 [⑤외환위험액현황 ⑥자산집중위험액] 당기(2026.2Q) 컬럼, 240dpi 렌더 직독(단위 백만원, /100). 직전반기(25.4Q) 비교컬럼이 마스터와 바이트 일치. item19=sqrt(V'MV) 검산 12051.50 vs 공시 12052(diff 0.50, GREEN)."
EV_IRR = "p28 [②금리위험액현황] Ⅲ.순자산가치 행, 6개 시나리오 컬럼(충격전/평균회귀/금리상승/금리하락/금리평탄/금리경사), 240dpi 렌더 직독(단위 백만원, /100). 직전반기(25.4Q) 비교컬럼이 마스터와 바이트 일치(7/7). irr_derive_expected(item36)=2341.57 vs 공시(같은 페이지 Ⅳ.금리위험액)=2341.56 (diff 0.007, GREEN)."
EV_TFI = "p20 [지급여력비율의 경과조치 적용에 관한 사항 1)공통적용 경과조치 관련], 240dpi 렌더 직독(단위 백만원, /100). item50+51=item52(37207.33=37207.33) 항등식 정확히 닫힘. item48=item14(23962)x50%=11981.02 정확 일치. INCL scope 검증: min(item47-item49,item48)+item49=13472.53=item51 정확히 닫힘(item47이 item49를 포함하는 스코프). item47(13472.53)≈headline item3(13473) — uncapped(한도 미구속) 서명."
EV_MIRROR = "p19 표: '2023년 지급여력제도 변경(RBC->K-ICS)... 당사의 경과조치 적용 사항' 표에서 공통적용(TFI)·선택적용(TAC/TIR/TER/TIRR)·K-ICS비율(적기시정조치유예) 전부 '적용여부=X'. p16 각주: '당사는 선택적용 경과조치를 적용하지 않아 경과조치 전·후 금액 및 비율이 동일함' — 명시적 비적용 문구. 값_적용후=값 미러링(2025.4Q/2026.1Q 자사 관례와 동일)."

cells = []

def add(item, val, ev, post=None, has_post=True):
    row = {
        "항목번호": item,
        "항목명": label(item),
        "값": val,
    }
    if has_post:
        row["값_적용후"] = val if post is None else post
    row["근거"] = ev
    cells.append(row)

for it, v in [(1, item1), (2, item2), (3, item3), (4, item4), (5, item5), (6, item6),
              (7, item7), (8, item8), (9, item9), (10, item10), (11, item11), (12, item12),
              (13, item13), (14, item14), (15, item15), (16, item16),
              (17, item17), (18, item18), (19, item19), (20, item20), (21, item21), (22, item22),
              (23, item23), (24, item24), (25, item25), (26, item26)]:
    add(it, v, EV_HEADLINE + " " + EV_MIRROR)

add(27, item27, EV_HEADLINE + " item27=item1/item14x100=37207/23962x100(공시 인쇄값 155.3, 풀정밀도 저장, 기존관례 2025.4Q=176.68225637과 동일방식). " + EV_MIRROR)
add(28, item28, "item28=item2/item14x100 파생값(원문 비인쇄, [KICS item28 computed] 관례). " + EV_MIRROR)

for it, v in [(29, item29), (30, item30), (31, item31), (32, item32), (33, item33), (34, item34), (35, item35)]:
    add(it, v, EV_LIFE)

for it, v in [(36, item36), (37, item37), (38, item38), (39, item39), (40, item40)]:
    add(it, v, EV_MARKET)

for it, v in [(41, item41), (42, item42), (43, item43), (44, item44), (45, item45), (46, item46)]:
    add(it, v, EV_IRR)

for it, v in [(47, item47), (48, item48), (49, item49), (50, item50), (51, item51), (52, item52)]:
    add(it, v, EV_TFI)

# 53/54: this repo's existing convention never populates 값_적용후 for these two memo rows
# (checked: KR0001 2023.1Q-2024.2Q all show 값_적용후 absent for 53/54) -- match it.
add(53, item53, EV_TFI + " (기발행 신종자본증권=0, p20/p17 둘 다 대시)", has_post=False)
add(54, item54, EV_TFI + " (기발행 후순위채무, 적용후 컬럼은 해당 표에서 해치 처리=인쇄 생략, 타사 전례와 동일하게 값_적용후 비움)", has_post=False)

patch = {
    "company_code": "KR0079",
    "quarter": "2026.2Q",
    "cells": cells,
    "notes": (
        "source: data/disclosure/FY2026_Q2/pdf/KR0079_미래에셋생명.pdf (65p, genuinely image-only -- "
        "fitz get_text() yields ~530 words total across all pages, confirmed no text layer). "
        "EasyOCR MD (md_inbox/FY2026_Q2/KR0079_미래에셋생명.md) was NOT used as a value source for this "
        "patch -- it has systematic digit confusion (leading '1'<->'7' swap observed repeatedly, e.g. "
        "OCR '755.3' vs actual '155.3', OCR '73,473' vs actual '13,473', OCR '70,265' vs actual '10,265', "
        "OCR '72,052' vs actual '12,052'). Every value in this patch was instead read directly off "
        "240dpi fitz-rendered PNGs of the specific pages (16,17,19,20,24,25,28,29,30,31) via Claude vision, "
        "then cross-checked two independent ways: (a) against this company's own already-loaded 2026.1Q/"
        "2025.4Q comparative columns printed in the SAME tables (all matched byte-for-byte after /100 unit "
        "conversion), and (b) against kics_json_rules.py identities imported from src/solvency/validation/"
        "kics_json_rules.py (rule1 item1=2+3, rule4 item15=sqrt(V'R4V)+21, rule5 item14=15-22+23, rule6 "
        "item16=sum(17..21)-15, 8_life item17=sqrt(S'R7S) diversif ratio 1.45, 19_market item19=sqrt(V'MV), "
        "36_irr item36 formula, TFI item50+51=52 and item48=item14x50%). All identities close within GREEN "
        "tolerance (worst diff 0.5 on 19_market, most exact to 0.01-0.2). Unit throughout the source tables "
        "is 백만원 (divided by 100 to store 억원, matching repo convention). "
        "Transition (경과조치): p19's own applicability table shows TFI/TAC/TIR/TER/TIRR/적기시정조치유예 all "
        "'X' (not applied) for 2026.2Q, and p16 carries an explicit footnote confirming pre/post-transition "
        "amounts and ratios are identical -- so 값_적용후=값 mirroring is applied throughout (items 47-52 too, "
        "confirmed identical columns on p20's TFI table; items 53/54 follow this repo's universal convention "
        "of leaving 값_적용후 unpopulated for those two memo rows regardless of transition status). "
        "kics_transition_applicability.json has no 2026.2Q entry for KR0079 yet and its 2025.4Q/2026.1Q "
        "entries are UNKNOWN/stale (that registry was built from a different, wrongly-cached 559p DART "
        "사업보고서 bundle under data/disclosure/FY2024_Q4|FY2025_Q4/raw/ that has no 경과조치 keyword at all "
        "-- a separate, pre-existing data issue outside this patch's scope, flagged in the report). "
        "Items 6 (자본항목 중 보통주 이외의 자본증권), 10 (비지배지분), 12 (지급여력금액으로 불인정하는 항목) "
        "are included as 0 -- p19 shows '-' (dash) for all three quarters in all three rows, same disclosed-"
        "zero convention already used elsewhere in this exact filing for item18/23-26/32/40."
    ),
    "unfixable": [],
}

out_path = ROOT / "data" / "_derived" / "_patch_2026q2_KR0079.json"
out_path.write_text(json.dumps(patch, ensure_ascii=False, indent=2), encoding="utf-8")
print("wrote", out_path, "cells=", len(cells))
