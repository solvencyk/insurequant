# -*- coding: utf-8 -*-
"""Build the per-company patch JSON files for the 2026.2Q RED-23 round.

Writes/merges data/_derived/_patch_2026q2_<code>.json for KR0009, KR0150,
KR0087, KR0083, KR1011, KR0051 (KR0079 excluded per explicit "hands off").

Merge policy: if a patch file already exists, keep its existing cells
(different item numbers) and only append/update the cells this round needs.
Never remove an existing cell that isn't part of this round's list.
"""
import json
import io
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = Path(r"C:\Users\sangwook.cho\Desktop\insurequant")
DERIVED = ROOT / "data" / "_derived"

# item label lookup (canonical, from docs/agents/kics-json-validation-rules.md)
LABELS = {
    1: "가. 지급여력금액", 2: "기본자본", 3: "보완자본",
    4: "Ⅰ. 건전성감독기준 재무상태표 상의 순자산",
    5: "1. 보통주", 6: "2. 자본항목 중 보통주 이외의 자본증권", 7: "3. 이익잉여금",
    8: "4. 자본조정", 9: "5. 기타포괄손익누계액", 10: "6. 비지배지분", 11: "7. 조정준비금",
    12: "Ⅱ. 지급여력금액으로 불인정하는 항목 (지급이 예정된 주주배당액 등)",
    13: "Ⅲ. 보완자본으로 재분류하는 항목 (기본자본 자본증권의 인정한도를 초과한 금액 등)",
    14: "나. 지급여력기준금액 (Ⅰ-Ⅱ+Ⅲ)", 15: "Ⅰ. 기본요구자본",
    16: "- 분산효과 : (1+2+3+4+5) - Ⅰ",
    17: "1. 생명장기손해보험위험액", 18: "2. 일반손해보험위험액", 19: "3. 시장위험액",
    20: "4. 신용위험액", 21: "5. 운영위험액", 22: "Ⅱ. 법인세조정액",
    23: "Ⅲ. 기타 요구자본(1+2+3)",
    24: "1. 업권별 자본규제를 활용한 종속회사의 요구자본 환산치",
    25: "2. 비례성원칙을 적용한 종속회사의 요구자본 대응치",
    26: "3. 업권별 자본규제를 활용한 관계회사의 요구자본 환산치",
    47: "보완자본 한도 적용 전", 48: "보완자본 한도",
    49: "해약환급금 부족분 상당액 중 해약환급금 상당액 초과분",
}

# ---------------------------------------------------------------------------
# KR0009 현대해상 -- items 1-26 were 100% absent (wrong-doc reparse gap).
# Reparsed today (243s, conf=1.00). MD table "[경과조치 적용 전 지급여력비율 세부]"
# (md_inbox/FY2026_Q2/KR0009_현대해상.md L410-444), 당분기(26.2Q) column.
# Pre==post confirmed explicitly: L404 "당사는 자본감소분 경과조치를 적용하지 않아
# 경과조치 전·후 금액 및 비율이 동일함" (and same wording for the other two
# selective measures) -- only TFI(공통, O) applies and headline pre==post
# exactly (L329-334: 209.0/153,285/73,335 both columns).
KR0009 = {
    1: 153285, 2: 61458, 3: 91826, 4: 128853, 5: 1048, 6: 0, 7: 88591, 8: -366,
    9: -23792, 10: 0, 11: 63372, 12: 0, 13: 67395, 14: 73335, 15: 99205,
    16: 35999, 17: 73580, 18: 12306, 19: 29618, 20: 13763, 21: 5938,
    22: 26101, 23: 231, 24: 231, 25: 0, 26: 0,
}
KR0009_SRC = ("md_inbox/FY2026_Q2/KR0009_현대해상.md L410-444 [경과조치 적용 전 지급여력비율 "
              "세부] 당분기(26.2Q) 열, 재파싱 후(run_id 20260831T144734Z, "
              "--fallback-scan-pages 60 --max-hit-pages 60 --keyword-window 2). "
              "L404/406/408 명시: 선택적용 경과조치(자본감소분/장수·사업비·해지·대재해/주식·"
              "금리) 전부 미적용 -> 값_적용후=값.")

# ---------------------------------------------------------------------------
# KR0150 서울보증보험 -- item1/14/27/36/41-46/52 already correct (loaded from
# the correctly-refetched raw earlier today). items 2,3,4-13,15-26 were absent
# because the keyword-window drop skipped the "[경과조치 적용 전 지급여력비율
# 세부]" page. Reparsed today (220s, conf=1.00).
KR0150 = {
    2: 56245, 3: 43, 4: 56588, 5: 1746, 6: 0, 7: 49511, 8: 0, 9: -1306, 10: 0,
    11: 6638, 12: 300, 13: 43, 15: 19085, 16: 6197, 17: 0, 18: 12894,
    19: 8616, 20: 3098, 21: 674, 22: 4740, 23: 0, 24: 0, 25: 0, 26: 0,
}
# also mirror pre==post onto the already-present headline cells (1,14,27) --
# update only 값_적용후, leave 값 untouched (already correct).
KR0150_MIRROR_ONLY = {1: 56288, 14: 14345, 27: None}  # 27 filled from existing 값
KR0150_SRC = ("md_inbox/FY2026_Q2/KR0150_서울보증보험.md L471-505 [경과조치 적용 전 "
              "지급여력비율 세부] 당분기(26.2Q) 열, 재파싱 후(run_id 20260831T122038Z, "
              "--fallback-scan-pages 60 --max-hit-pages 60 --keyword-window 2). "
              "L531/533/535 명시: 선택적용 경과조치 전부 미적용 -> 값_적용후=값.")

# ---------------------------------------------------------------------------
# KR0087 동양생명 -- OCR (EasyOCR, 59p scan). item1 missing, item3/item48
# mismapped (both held item1's 48808 due to an OCR label collision on
# "보완자본)" -- the truncated tail of "가.지급여력금액(기본자본+보완자본)").
# Confirmed by (a) internal identity item1=item2+item3 closing exactly with
# 28794 but not with the old 48808, (b) direct 240dpi render of PDF p16-17
# (scripts/_probes/probe_20260901_kr0087_render.py -> kr0087_pages/p16.png,
# p17.png) -- both visually read and cross-checked against the printed table.
KR0087_FIX = {3: 28794, 48: 11883.77}  # overwrite wrong existing values
KR0087_NEW = {
    1: 48808, 6: 0, 7: 16550, 9: -5255, 10: 0, 16: 7664, 18: 0,
    23: 0, 24: 0, 25: 0, 26: 0, 47: 12478.17, 49: 16910.13,
}
KR0087_SRC = ("PDF p16 [경과조치 적용 전 지급여력비율 세부] + p17 TFI 표(백만원), 240dpi "
              "fitz 렌더 직독(scripts/_probes/probe_20260901_kr0087_render.py). "
              "item3 기존값 48808은 item1(가.지급여력금액) 값이 '보완자본)' 라벨편(가.지급여력"
              "금액(기본자본+보완자본) OCR 절단)에 오매핑된 것 -- item1=item2+item3 항등식이 "
              "28794로만 닫힘(48808으로는 20014+48808=68822<>48808). item48 기존값 48808도 "
              "동일 오염(진짜 보완자본한도=1,188,377백만원=11,883.77억). p17 명시: 선택적용 "
              "경과조치 전부 미적용 -> 값_적용후=값(모든 신규/수정 셀 동일)."
              )

# ---------------------------------------------------------------------------
# KR0083 푸본현대생명보험 -- item49 was the only missing TFI leg; raw shows an
# explicit dash (both columns) for "해약환급금 부족분 상당액 중 해약환급금 상당액
# 초과분", i.e. genuinely 0, not an extraction gap.
KR0083_NEW = {49: 0.0}
KR0083_NEW_POST = {49: 0.0}
KR0083_SRC = ("md_inbox/FY2026_Q2/KR0083_푸본현대생명보험.md L414: '해약환급금 부족분 상당액 "
              "중 해약환급금 상당액 초과분 | - | -' -- 적용전/적용후 둘 다 명시적 대시=0. "
              "item49=0을 넣으면 _tier2_branch 4-input(3,47,48,49)이 전부 채워져 CAPPED로 "
              "분류되고(min(10034.79,7712.91)+0=7712.91≈item3=7713), 한도초과=10034.79-"
              "7712.91=2321.88≈2322로 2_tier1_bridge 항등식이 정확히 닫힘.")

# ---------------------------------------------------------------------------
# KR1011 IBK연금보험 -- item47/48/49 (TFI detail table) were entirely absent
# from the pre-reparse MD (page dropped by keyword-window); item48's stale
# 7168 in the live master coincidentally equalled item3 (보완자본), not the
# true limit. Reparsed today (169s, conf=1.00); table now present with real
# pre/post values.
KR1011_FIX = {48: 3610.46}
KR1011_FIX_POST = {48: 3610.46}
KR1011_NEW = {47: 4346.77, 49: 3557.89}
KR1011_NEW_POST = {47: 2744.69, 49: 3557.89}
KR1011_SRC = ("md_inbox/FY2026_Q2/KR1011_IBK연금보험.md L353-361 (1)공통적용 경과조치 관련 "
              "(백만원), 재파싱 후(run_id 20260831T1..., --fallback-scan-pages 60 "
              "--max-hit-pages 60 --keyword-window 2): 보완자본한도적용전 434,677/274,469, "
              "보완자본한도 361,046/361,046(전후 동일), 해약환급금... 355,789/355,789(전후 "
              "동일). 기존 item48=7168은 item3(보완자본)의 오사본(TFI 표 부재 시기의 대체값 "
              "추정). CAPPED로 재분류: min(4346.77,3610.46)+3557.89=7168.35≈item3=7168, "
              "한도초과=4346.77-3610.46=736.31≈736 -- 2_tier1_bridge 잔차 736과 정확히 일치.")

# ---------------------------------------------------------------------------
# KR0051 신한이지손해보험 -- items 1-26 (core table) were silently loaded with
# the WRONG QUARTER's numbers: every value that currently differs quarter to
# quarter in the master exactly equals the 2026.1Q disclosed figure (e.g.
# 값 item1=1131 == MD의 "당분기-1분기(26.1Q)" 열, 값 item27=210.91 == 2026.1Q
# 공시비율). items 47-54 (TFI) were correctly re-extracted to 2026.2Q figures
# earlier today by the parallel item47-54 pass (item50=1176/item52=1197 match
# the true 26.2Q column) -- that correction is what exposed the pre-existing
# quarter-slip in items 1-26 via 3_tier2_composition (item3 stale=17 vs
# item47/48/49's honest 2026.2Q basis).
KR0051_FIX = {
    1: 1197, 2: 1176, 3: 22, 4: 1197, 7: -874, 9: -62, 11: -344, 13: 22,
    14: 524, 15: 524, 16: 92, 17: 23, 18: 370, 19: 75, 21: 116,
}
KR0051_NEW = {24: 0, 25: 0}
KR0051_SRC = ("md_inbox/FY2026_Q2/KR0051_신한이지손해보험.md L332-360 [지급여력비율의 경과조치 "
              "적용 전 세부] 및 L377-388 TFI 표, 당분기(26.2Q) 열. 기존 마스터 값은 전부 "
              "'당분기-1분기(26.1Q)' 열과 바이트 일치(1131/1114/17/536/90/21/396/71/105/"
              "210.91 등) -- 분기밀림. item50(기본자본,TFI)=1176·item52(지급여력금액,TFI)="
              "1197이 이미 정답 26.2Q 값으로 로드돼 있어(오늘 다른 세션이 item47-54 축을 "
              "고정) 교차검증됨. L367/369/371 명시: 선택적용 경과조치 전부 미적용 -> "
              "값_적용후=값(정정 셀 전체).")


def cell(item_no, value, value_post, note):
    return {
        "항목번호": item_no,
        "항목명": LABELS[item_no],
        "값": value,
        "값_적용후": value_post,
        "근거": note,
    }


def merge_patch(code, quarter, new_cells):
    """Merge new_cells (list of cell dicts) into data/_derived/_patch_2026q2_<code>.json,
    keeping any existing cells whose 항목번호 is not in new_cells."""
    path = DERIVED / f"_patch_2026q2_{code}.json"
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            doc = json.load(f)
    else:
        doc = {"company_code": code, "quarter": quarter, "cells": []}
    existing = doc.get("cells", [])
    new_item_nos = {c["항목번호"] for c in new_cells}
    kept = [c for c in existing if c["항목번호"] not in new_item_nos]
    doc["cells"] = kept + new_cells
    doc["cells"].sort(key=lambda c: c["항목번호"])
    with open(path, "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=2)
    print(f"wrote {path} : kept {len(kept)} existing + {len(new_cells)} new/updated = {len(doc['cells'])} total")


def main():
    # KR0009
    cells = [cell(i, v, v, KR0009_SRC) for i, v in KR0009.items()]
    merge_patch("KR0009", "2026.2Q", cells)

    # KR0150
    cells = [cell(i, v, v, KR0150_SRC) for i, v in KR0150.items()]
    # mirror headline (1,14) 값_적용후 only -- these already exist with correct 값
    cells.append({"항목번호": 1, "항목명": LABELS[1], "값": 56288, "값_적용후": 56288,
                   "근거": KR0150_SRC + " (기존 값=56288 유지, 값_적용후만 미러링)"})
    cells.append({"항목번호": 14, "항목명": LABELS[14], "값": 14345, "값_적용후": 14345,
                   "근거": KR0150_SRC + " (기존 값=14345 유지, 값_적용후만 미러링)"})
    merge_patch("KR0150", "2026.2Q", cells)

    # KR0087
    cells = [cell(i, v, v, KR0087_SRC) for i, v in {**KR0087_FIX, **KR0087_NEW}.items()]
    merge_patch("KR0087", "2026.2Q", cells)

    # KR0083
    cells = [cell(49, 0.0, 0.0, KR0083_SRC)]
    merge_patch("KR0083", "2026.2Q", cells)

    # KR1011
    cells = [
        cell(47, KR1011_NEW[47], KR1011_NEW_POST[47], KR1011_SRC),
        cell(48, KR1011_FIX[48], KR1011_FIX_POST[48], KR1011_SRC),
        cell(49, KR1011_NEW[49], KR1011_NEW_POST[49], KR1011_SRC),
    ]
    merge_patch("KR1011", "2026.2Q", cells)

    # KR0051
    cells = [cell(i, v, v, KR0051_SRC) for i, v in {**KR0051_FIX, **KR0051_NEW}.items()]
    merge_patch("KR0051", "2026.2Q", cells)


if __name__ == "__main__":
    main()
