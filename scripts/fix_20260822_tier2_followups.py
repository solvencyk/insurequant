# -*- coding: utf-8 -*-
"""inbox 20260821T1425Z (validation, iter-2) 후속 — tier2 잔여 blocking RED 34건 중
데이터 쪽 3건(A·B·C)을 닫는다. 전부 raw PDF 직접 재확인(fitz 텍스트 + get_pixmap 렌더링
시각 대조) 후 확정된 값만 UPSERT 한다. dry-run 기본 지원.

## A. AIA(KR0080) 2023.2Q — items 1,2,3,12,13,14,15,16,19,20,22,27,28 정정

raw(`data/disclosure/FY2023_Q2/raw/KR0080_에이아이에이생명보험.pdf` p8-9, md_inbox 동일)와
master 를 대조한 결과 이 (회사,분기) 만 items 1/2/3/5/6/7/8/9/11/12/13/14/15/16/19/20/22
전부가 raw 의 **어느 페이지·어느 컬럼에도 없는** 값으로 채워져 있었다(예: item2=29645,
raw 에는 "29,645" 문자열 자체가 PDF 35페이지 전체·Docling MD 전체에 0회 등장). 소스 불명
오염 — 이 세션의 tier2 스코프가 아니라 **items 1-14/15-22/27-28 중 tier2 룰(2_tier1_bridge·
3_tier2_composition)이 입력으로 쓰는 항목만** 정정한다(items 5,6,7,8,9,10,11 은 raw 와도
다르지만 우연히 합계가 item4 와 정확히 일치해 어떤 룰도 안 걸림 — 건드리지 않고 별도
후속 발주, 아래 "안 건드린 것" 참조).

수정 범위를 1-4/12-14 로 좁히면 rule 5(item14==item15-item22+item23) · rule 4(item15==
R4sqrt(17,18,19,20)+item21) · rule 6(item16==(17+18+19+20+21)-15) 가 **새로 깨진다**
(현재는 items 14/15/16/19/20/22 가 서로 잘못 정합돼 있어 우연히 green). 그래서 저 6개
항목도 같이 raw 로 맞춘다 — R4 공식으로 직접 재현해 diff -0.54(허용오차 이내) 확인.
items 17/18/21 은 이미 raw 와 일치해 안 건드림. items 27/28 은 item1/2/14 파생값
([[reference-kics-item28-computed]]) 이라 재계산.

AIA 는 "경과조치 미적용" 회사 quirk([[reference-kics-company-quirks]]) 로 전 분기
적용전=적용후 확인됨(p8 표: 경과조치전/후 블록이 전부 동일) — 값_적용후도 같은 값으로 채운다.

## B. 코리안리(KR1000) 6분기+1 — item50/51 신설(TFI표 자신의 기본자본/보완자본)

`[지급여력비율의 경과조치 적용에 관한 사항] (1) 공통적용 경과조치 관련` 표(백만원) 자신의
기본자본·보완자본 행. validation 요청(inbox 20260821T1425Z iter-2 §3-D) — 코리안리는
헤드라인표(item2/3)가 TFI-POST 스코프를 쓰는데(선택경과조치 전부 미신청, "경과조치
적용전"=TFI 만영 상태) 마스터엔 TFI 표 자신의 기본자본/보완자본이 없어 그 스코프차를
검산할 축이 없었다. 7분기(2023.2Q~2024.4Q) 전부 raw 재추출 + 자체검산(기본자본+보완자본
=지급여력금액, 표 자신의 값) 전부 diff<=1(반올림) 확인. 2024.4Q 는 이 페이지 텍스트스트림이
"(2)선택적용" 섹션보다 "(1)공통적용" 표가 텍스트상 나중에 나오는 특이 순서라(라벨 자체는
"(1)"이 인쇄상 위에 있지만 fitz 추출 순서가 뒤바뀜) 값 크기(백만원대, 헤드라인 억원표와
자릿수로 구분)로 식별.

항목번호: 47/48/49 다음으로 이어 50/51 로 정한다(1-46 은 기존 스키마, 47-49 는 2026-08-21
tier2 한도, 50/51 은 이번 신설 — 마스터 전체에서 최초 미사용 번호).
  50 = 기본자본(TFI표, 공통적용경과조치)
  51 = 보완자본(TFI표, 공통적용경과조치)
라벨에 "(TFI표, 공통적용경과조치)" 접미사를 붙여 item2/3(헤드라인 기본자본/보완자본)과
혼동되지 않게 한다.

## C. 동양생명(KR0087) 2026.1Q — item47/48/49 vision 판독 신규 적재

완전 스캔본(fitz 전페이지 텍스트 0~16자, Docling MD 도 0건 — 기존 판정 그대로).
`get_pixmap(dpi=110~200)` 로 32페이지 중 p13(총괄)·p16(헤드라인 세부)·p17(TFI표) 육안
판독. items 1-46 은 이미 이전 라운드에서 vision 으로 적재돼 있었고(headline p16 의
기본자본 15,920/보완자본 27,537/순자산 31,994/불인정항목 943/재분류항목 16,074/
지급여력기준금액 22,926 전부 마스터 기존값과 정확히 일치, 재확인만), 이번에 빠져있던
47/48/49(2026-08-21 신설 항목이라 vision 라운드 이후에 생긴 공백)만 p17 "1) 공통적용
경과조치 관련" 표에서 신규 판독:
  47(한도적용전)=1,240,578백만 · 48(한도)=1,146,316백만 · 49(초과분)=1,607,404백만
(세 값 모두 경과조치 적용전=적용후 컬럼이 시각적으로 동일 — 이 필링은 표 전체가
전=후 동일하게 인쇄돼 있다, p13 총괄표·p16 헤드라인표도 전=후 동일 확인). 자체검산:
min(47,48)+49 = 11,463.16+16,074.04 = 27,537.20 == item3(27,537) 거의 정확 · 한도초과
= 47-48 = 942.62 ≈ item12(943, diff 0.38) → bridge 잔차 943(INPUT_MISSING 폴백으로 발생)
도 47/48/49 적재만으로 자동 해소.

Usage:
  ...python scripts/fix_20260822_tier2_followups.py --dry-run
  ...python scripts/fix_20260822_tier2_followups.py
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

TARGET = REPO / "kics_disclosure.json"

# --- A. AIA(KR0080) 2023.2Q raw-confirmed values (억원; from 백만원/억원 mixed source,
# see raw p8-9 both fitz-extracted text and get_pixmap(dpi=240) visual render, and
# independently cross-verified: md_inbox/FY2023_Q2/KR0080_....md line 181-192 agrees) ---
AIA_FIX = {
    1: 33793, 2: 28620, 3: 5173,
    12: 0, 13: 5173, 14: 13824,
    15: 17930, 16: 2931, 19: 3022, 20: 1351, 22: 4106,
    # item37(주식위험액) -- fixing item19 above exposed a SECOND, independent corruption:
    # rule 19_market went RED (item19=3022 vs sqrt(MARKET_M of 36-40)=2858.70 using the
    # OLD item37=1745.46). raw p16 "③ 주식위험액 현황" 기본법/합계=195,714백만=1,957.14억
    # (NOT 1745.46, no source match for 1745.46 anywhere in the PDF either). With item37
    # corrected, sqrt(MARKET_M)=3022.17 == item19(3022) diff 0.17 -- reconciles. items
    # 36/38/39/40 independently confirmed to already match raw (112,524/103,250/47,990/
    # blank=0 -- see probe_20260822_aia_market_dump.py / _fx.py), left unchanged.
    37: 1957.14,
}
# items 27/28 = item1/item14*100, item2/item14*100 (computed, per established convention)
AIA_27 = AIA_FIX[1] / AIA_FIX[14] * 100.0
AIA_28 = AIA_FIX[2] / AIA_FIX[14] * 100.0

# --- B. Korean Re(KR1000) TFI table's own 기본자본/보완자본 (백만원 raw -> /100 억원) ---
# (pre, post) in 백만원, from raw p8-9 (or p23-24 for 2024.4Q) fitz text, each self-checked
# against the SAME table's own 지급여력금액 row (기본자본+보완자본 == 지급여력금액, both
# columns, diff<=1 rounding in every quarter below).
KR1000_TFI = {
    "2023.2Q": {"기본자본": (3122114.0, 3220438.0), "보완자본": (619243.0, 520920.0)},
    "2023.3Q": {"기본자본": (3095786.0, 3194695.0), "보완자본": (610272.0, 511364.0)},
    "2023.4Q": {"기본자본": (3015824.0, 3115779.0), "보완자본": (646944.0, 546989.0)},
    "2024.1Q": {"기본자본": (3066973.0, 3169609.0), "보완자본": (651623.0, 548988.0)},
    "2024.2Q": {"기본자본": (3293085.0, 3399087.0), "보완자본": (650396.0, 544394.0)},
    "2024.3Q": {"기본자본": (3341972.0, 3450062.0), "보완자본": (707693.0, 599602.0)},
    "2024.4Q": {"기본자본": (3285953.0, 3395012.0), "보완자본": (895327.0, 786267.0)},
}
ITEM50_LABEL = "기본자본(TFI표, 공통적용경과조치)"
ITEM51_LABEL = "보완자본(TFI표, 공통적용경과조치)"

# --- C. 동양생명(KR0087) 2026.1Q vision 판독 (백만원 raw -> /100 억원, 전=후 동일 인쇄) ---
DONGYANG_2026Q1_TIER2 = {47: 1240578.0, 48: 1146316.0, 49: 1607404.0}
DONGYANG_LABELS = {
    47: "보완자본 한도 적용 전",
    48: "보완자본 한도",
    49: "해약환급금 부족분 상당액 중 해약환급금 상당액 초과분",
}


def _fmt(x: float) -> str:
    return str(int(round(x))) if abs(x - round(x)) < 1e-6 else f"{x:.2f}".rstrip("0").rstrip(".")


def main() -> int:
    dry = "--dry-run" in sys.argv
    data = json.loads(TARGET.read_text(encoding="utf-8"))
    print(f"로드 전 row_count = {len(data):,}")

    edits = 0
    inserts = 0

    # --- A. AIA 2023.2Q edit-in-place ---
    aia_rows = {int(r["항목번호"]): r for r in data
                if r["원보험사코드"] == "KR0080" and r["공시분기"] == "2023.2Q"}
    for item, val in AIA_FIX.items():
        r = aia_rows.get(item)
        if r is None:
            print(f"  [WARN] KR0080 2023.2Q item{item} 행 자체가 없음 -- 건드리지 않음")
            continue
        before_v, before_p = r.get("값"), r.get("값_적용후")
        new_v = _fmt(val)
        if str(before_v) != new_v or str(before_p) != new_v:
            print(f"  KR0080 2023.2Q item{item} 값={before_v}->{new_v} "
                  f"값_적용후={before_p}->{new_v}")
            r["값"] = new_v
            r["값_적용후"] = new_v
            edits += 1
    for item, val in ((27, AIA_27), (28, AIA_28)):
        r = aia_rows.get(item)
        if r is None:
            print(f"  [WARN] KR0080 2023.2Q item{item} 행 자체가 없음 -- 건드리지 않음")
            continue
        before_v, before_p = r.get("값"), r.get("값_적용후")
        new_v = f"{val:.8f}"
        print(f"  KR0080 2023.2Q item{item}(파생) 값={before_v}->{new_v} "
              f"값_적용후={before_p}->{new_v}")
        r["값"] = new_v
        r["값_적용후"] = new_v
        edits += 1

    # --- B. Korean Re item50/51 insert (only if not already present) ---
    existing = {(r["원보험사코드"], r["공시분기"], int(r["항목번호"])) for r in data}
    kr1000_meta = next(
        (r for r in data if r["원보험사코드"] == "KR1000"), None
    )
    if kr1000_meta is None:
        print("  [WARN] KR1000 행 자체가 마스터에 없음 -- 중단")
        return 1
    name, ticker, kind = (kr1000_meta.get("원수사명"), kr1000_meta.get("티커"),
                           kr1000_meta.get("생손보여부"))

    new_rows = []
    for q, vals in KR1000_TFI.items():
        for item, label, key in ((50, ITEM50_LABEL, "기본자본"), (51, ITEM51_LABEL, "보완자본")):
            if ("KR1000", q, item) in existing:
                print(f"  [SKIP] KR1000 {q} item{item} 이미 존재 -- 덮어쓰지 않음")
                continue
            pre_raw, post_raw = vals[key]
            pre = round(pre_raw / 100.0, 2)
            post = round(post_raw / 100.0, 2)
            row = {
                "원보험사코드": "KR1000",
                "원수사명": name,
                "티커": ticker,
                "생손보여부": kind,
                "항목번호": item,
                "항목명": label,
                "공시분기": q,
                "값": _fmt(pre),
                "값_적용후": _fmt(post),
            }
            new_rows.append(row)
            inserts += 1
            print(f"  INSERT KR1000 {q} item{item}({label}) 값={row['값']} "
                  f"값_적용후={row['값_적용후']}")

    # --- C. 동양생명 2026.1Q item47/48/49 insert (vision, only if absent) ---
    dy_meta = next(
        (r for r in data if r["원보험사코드"] == "KR0087" and r["공시분기"] == "2026.1Q"),
        None,
    )
    if dy_meta is None:
        print("  [WARN] KR0087 2026.1Q 행 자체가 마스터에 없음 -- 건너뜀")
    else:
        dy_name, dy_ticker, dy_kind = (dy_meta.get("원수사명"), dy_meta.get("티커"),
                                        dy_meta.get("생손보여부"))
        for item, raw in DONGYANG_2026Q1_TIER2.items():
            if ("KR0087", "2026.1Q", item) in existing:
                print(f"  [SKIP] KR0087 2026.1Q item{item} 이미 존재 -- 덮어쓰지 않음")
                continue
            val = round(raw / 100.0, 2)
            row = {
                "원보험사코드": "KR0087",
                "원수사명": dy_name,
                "티커": dy_ticker,
                "생손보여부": dy_kind,
                "항목번호": item,
                "항목명": DONGYANG_LABELS[item],
                "공시분기": "2026.1Q",
                "값": _fmt(val),
                "값_적용후": _fmt(val),  # 전=후 동일 인쇄 (p13/p16/p17 전부 확인)
            }
            new_rows.append(row)
            inserts += 1
            print(f"  INSERT KR0087 2026.1Q item{item}({DONGYANG_LABELS[item]}) "
                  f"값={row['값']} 값_적용후={row['값_적용후']}")

    print(f"\n합계: EDIT {edits}건 · INSERT {inserts}건")
    if dry:
        print("(dry-run; 파일 안 씀)")
        return 0
    if edits == 0 and inserts == 0:
        print("쓸 변경 없음")
        return 0

    data.extend(new_rows)
    TARGET.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nwrote {TARGET.name}  (row_count {len(data) - inserts:,} -> {len(data):,})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
