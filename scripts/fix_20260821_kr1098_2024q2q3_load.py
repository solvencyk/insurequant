"""Load 카카오페이손해보험(KR1098) 2024.2Q and 2024.3Q -- whole (company,
quarter) census RED (inbox 20260821T1505Z item 3).

Raw availability check: data/disclosure/FY2024_Q2/raw/
KR1098_카카오페이손해보험_amended2.pdf (45p) and FY2024_Q3/raw/
KR1098_카카오페이손해보험.pdf (19p) BOTH EXIST. But both are scanned
image-only PDFs -- fitz text extraction returns 622 chars over 45 pages
(Q2) and 28 chars over 19 pages (Q3), i.e. no usable text layer at all.
md_inbox docling output for both is a 48/39-line "head_fallback" stub with
keyword_hit_pages="" (docling's own keyword localizer found nothing to
parse in detail either). This IS a parsing gap parser can close -- not a
missing-raw case for downloader -- because Q3's OWN filing carries a
3-quarter trailing comparative table that includes 2024.2Q's figures
alongside 2024.3Q's, so a single rendered page recovers both missing
quarters. (Precedent this same session: KR0097 2024.2Q was recovered the
same way -- get_pixmap(dpi) + vision read of a scanned page.)

Source: data/disclosure/FY2024_Q3/raw/KR1098_카카오페이손해보험.pdf
  - page 11 "[경과조치 적용 전 지급여력비율 세부]" -- 3-column comparative
    table (2024년 3/4분기 | 2024년 2/4분기 | 2024년 1/4분기), read via
    get_pixmap(dpi=100) + vision. The 1/4분기 (2024.1Q) column cross-checks
    exactly against the value ALREADY in master for that quarter (item1=867,
    item2=867, item3=0, item5=2000, item7=-812, item8=-14, item9=-6,
    item11=-301, item14=40, item16=7, item18=29, item19=8, item20=2,
    item21=7 -- all match kics_disclosure.json's existing 2024.1Q row
    exactly), which is why the 2024.2Q/2024.3Q columns of the SAME table are
    trusted without independently cracking the Q2 scan.
  - page 12/13 "[지급여력비율의 경과조치 적용에 관한 사항]" -- confirms
    KR1098 applies NONE of the elective transitions for either quarter
    ("당사는 ... 경과조치를 적용하지 않아 경과조치 전·후 금액 및 비율이
    동일함" for capital-decrease/life-longterm/equity-interest-rate, all
    three blocks, both quarters) -- so 값_적용후 = 값 for every item, same
    convention as the company's other already-loaded quarters.
  - item27 (다. 지급여력비율 : 가÷나×100) is the DIRECTLY DISCLOSED ratio
    cell (1,171.90 / 667.44), not derived from item1/item14 -- those are
    display-rounded to the 억원 integer, so item1/item14*100 undershoots
    (867/40*100=2167.5 vs the disclosed 2024.1Q value; the existing master
    row for 2024.1Q already carries the same rounded-derivation gap, not
    reproduced here). item28 = item27 exactly (보완자본 = 0 in both
    quarters, so 기본자본=지급여력금액 and the two ratios are identical).
  - items 29-46 (하위위험 breakdown): NOT loaded. item17(생명장기위험액)=0
    for 2024.2Q (no life/longterm book that quarter) so 29-35 would be a
    degenerate all-zero table; item19(시장위험액)=8 for both quarters is
    almost entirely 자산집중위험액 (~7-8억원, page 28-29 of the Q2 scan
    confirms 주식/외환 "해당사항 없음"), but a clean 4-decimal breakdown
    wasn't extracted -- leaving 36-40 blank rather than estimate a split.

Cell-by-cell INSERT (new rows only, no existing KR1098 2024.2Q/2024.3Q rows
present -- verified before insert). Prints before/after census.
"""
from __future__ import annotations
import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
REPO = Path(__file__).resolve().parent.parent
JSON_PATH = REPO / "kics_disclosure.json"

CODE = "KR1098"
NAME = "카카오페이손해보험"
TICKER = "X"
KIND = "손해보험"

# (item_no, item_name, 값 2024.2Q, 값 2024.3Q)
ITEMS = [
    (1, "가. 지급여력금액", "774", "666"),
    (2, "기본자본", "774", "666"),
    (3, "보완자본", "0", "0"),
    (4, "Ⅰ. 건전성감독기준 재무상태표 상의 순자산", "774", "666"),
    (5, "1. 보통주", "2000", "2000"),
    (6, "2. 자본항목 중 보통주 이외의 자본증권", "0", "0"),
    (7, "3. 이익잉여금", "-914", "-1045"),
    (8, "4. 자본조정", "-14", "-14"),
    (9, "5. 기타포괄손익누계액", "-6", "-6"),
    # item10 (6. 비지배지분) not disclosed for this company -- matches the
    # existing 2024.1Q/2023.x rows, which also have no item10.
    (11, "7. 조정준비금", "-291", "-268"),
    (12, "Ⅱ. 지급여력금액으로 불인정하는 항목 (지급이 예정된 주주배당액 등)", "0", "0"),
    (13, "Ⅲ. 보완자본으로 재분류하는 항목 (기본자본 자본증권의 인정한도를 초과한 금액 등)", "0", "0"),
    (14, "나. 지급여력기준금액 (Ⅰ-Ⅱ+Ⅲ)", "66", "100"),
    (15, "Ⅰ. 기본요구자본", "66", "100"),
    (16, "- 분산효과 : (1+2+3+4+5) - Ⅰ", "7", "9"),
    (17, "1. 생명장기손해보험위험액", "0", "2"),
    (18, "2. 일반손해보험위험액", "53", "82"),
    (19, "3. 시장위험액", "8", "8"),
    (20, "4. 신용위험액", "3", "2"),
    (21, "5. 운영위험액", "10", "15"),
    (22, "Ⅱ. 법인세조정액", "0", "0"),
    (23, "Ⅲ. 기타 요구자본(1+2+3)", "0", "0"),
    (24, "1. 업권별 자본규제를 활용한 종속회사의 요구자본 환산치", "0", "0"),
    (25, "2. 비례성원칙을 적용한 종속회사의 요구자본 대응치", "0", "0"),
    (26, "3. 업권별 자본규제를 활용한 관계회사의 요구자본 환산치", "0", "0"),
    (27, "다. 지급여력비율 : 가 ÷ 나 × 100", "1171.90", "667.44"),
    (28, "기본자본비율", "1171.90", "667.44"),
]


def main():
    rows = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    print(f"loaded {len(rows)} rows")

    existing = [
        r for r in rows
        if r.get("원보험사코드") == CODE and r.get("공시분기") in ("2024.2Q", "2024.3Q")
    ]
    if existing:
        print(f"ABORT: {len(existing)} rows already exist for KR1098 2024.2Q/2024.3Q")
        for r in existing:
            print("  ", r)
        sys.exit(1)

    new_rows = []
    for item_no, item_name, v2, v3 in ITEMS:
        for quarter, val in (("2024.2Q", v2), ("2024.3Q", v3)):
            new_rows.append({
                "원보험사코드": CODE,
                "원수사명": NAME,
                "티커": TICKER,
                "생손보여부": KIND,
                "항목번호": item_no,
                "항목명": item_name,
                "공시분기": quarter,
                "값": val,
                "값_적용후": val,  # confirmed non-applier, all electives -> mirror
            })

    print(f"inserting {len(new_rows)} rows ({len(ITEMS)} items x 2 quarters)")
    rows.extend(new_rows)

    JSON_PATH.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {len(rows)} rows (was {len(rows) - len(new_rows)}, +{len(new_rows)})")


if __name__ == "__main__":
    main()
