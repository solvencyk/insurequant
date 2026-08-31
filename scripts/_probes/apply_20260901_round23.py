# -*- coding: utf-8 -*-
"""Cell-level UPSERT of the round-23 (2026.2Q) fixes into a kics_disclosure.json.

Usage:
    python apply_20260901_round23.py <target_json_path>

Applies ONLY the item numbers this round's 10 rules need (never items 53/54,
29-40 etc. that sit in the same per-company patch files for other tickets).
Prints before/after row count and unique (company,quarter,item) combo count
so out-of-scope loss can be caught immediately.
"""
import json
import sys
import io
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = Path(r"C:\Users\sangwook.cho\Desktop\insurequant")
QUARTER = "2026.2Q"

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
    27: "다. 지급여력비율 : 가 ÷ 나 × 100", 28: "기본자본비율",
    47: "보완자본 한도 적용 전", 48: "보완자본 한도",
    49: "해약환급금 부족분 상당액 중 해약환급금 상당액 초과분",
}

META = {
    "KR0009": ("현대해상", "001450", "손해보험"),
    "KR0150": ("서울보증보험", "031210", "손해보험"),
    "KR0087": ("동양생명", "082640", "생명보험"),
    "KR0083": ("푸본현대생명보험", "X", "생명보험"),
    "KR1011": ("IBK연금보험", "X", "생명보험"),
    "KR0051": ("신한이지손해보험", "X", "손해보험"),
}

# (item -> (값, 값_적용후)) per company. None means "leave that field untouched
# if row exists already" -- used only for the KR0150 headline mirror-only rows.
PATCHES = {
    "KR0009": {
        1: (153285, 153285), 2: (61458, 61458), 3: (91826, 91826), 4: (128853, 128853),
        5: (1048, 1048), 6: (0, 0), 7: (88591, 88591), 8: (-366, -366),
        9: (-23792, -23792), 10: (0, 0), 11: (63372, 63372), 12: (0, 0),
        13: (67395, 67395), 14: (73335, 73335), 15: (99205, 99205), 16: (35999, 35999),
        17: (73580, 73580), 18: (12306, 12306), 19: (29618, 29618), 20: (13763, 13763),
        21: (5938, 5938), 22: (26101, 26101), 23: (231, 231), 24: (231, 231),
        25: (0, 0), 26: (0, 0),
    },
    "KR0150": {
        1: (56288, 56288), 14: (14345, 14345),  # mirror 값_적용후 only, 값 unchanged
        2: (56245, 56245), 3: (43, 43), 4: (56588, 56588), 5: (1746, 1746), 6: (0, 0),
        7: (49511, 49511), 8: (0, 0), 9: (-1306, -1306), 10: (0, 0), 11: (6638, 6638),
        12: (300, 300), 13: (43, 43), 15: (19085, 19085), 16: (6197, 6197), 17: (0, 0),
        18: (12894, 12894), 19: (8616, 8616), 20: (3098, 3098), 21: (674, 674),
        22: (4740, 4740), 23: (0, 0), 24: (0, 0), 25: (0, 0), 26: (0, 0),
    },
    "KR0087": {
        1: (48808, 48808), 3: (28794, 28794), 6: (0, 0), 7: (16550, 16550),
        9: (-5255, -5255), 10: (0, 0), 16: (7664, 7664), 18: (0, 0), 23: (0, 0),
        24: (0, 0), 25: (0, 0), 26: (0, 0),
        47: (12478.17, 12478.17), 48: (11883.77, 11883.77), 49: (16910.13, 16910.13),
    },
    "KR0083": {
        49: (0.0, 0.0),
    },
    "KR1011": {
        47: (4346.77, 2744.69), 48: (3610.46, 3610.46), 49: (3557.89, 3557.89),
    },
    "KR0051": {
        1: (1197, 1197), 2: (1176, 1176), 3: (22, 22), 4: (1197, 1197),
        7: (-874, -874), 9: (-62, -62), 11: (-344, -344), 13: (22, 22),
        14: (524, 524), 15: (524, 524), 16: (92, 92), 17: (23, 23), 18: (370, 370),
        19: (75, 75), 21: (116, 116), 24: (0, 0), 25: (0, 0),
        # item27/28 pre-existed with STALE (quarter-slipped) values -> explicit
        # overwrite here (derive_capital_ratios.py's default missing-only mode
        # would skip them since they're "present").
        27: (1197 / 524 * 100, 1197 / 524 * 100),
        28: (1176 / 524 * 100, 1176 / 524 * 100),
    },
}

SOURCE_NOTE = "round-23 2026.2Q identity fix (see TODO_parser_kics.md 2026-09-01 entry)"


def main():
    target_path = Path(sys.argv[1])
    with open(target_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    records = data["records"] if isinstance(data, dict) and "records" in data else data

    before_rows = len(records)
    before_combos = len({(r.get("원보험사코드"), r.get("공시분기"), r.get("항목번호")) for r in records})

    index = {}
    for i, r in enumerate(records):
        key = (r.get("원보험사코드"), r.get("공시분기"), r.get("항목번호"))
        index[key] = i

    n_updated = 0
    n_inserted = 0
    changes = []
    for code, items in PATCHES.items():
        name, ticker, kind = META[code]
        for item_no, (val, val_post) in items.items():
            key = (code, QUARTER, item_no)
            if key in index:
                row = records[index[key]]
                old_val, old_val_post = row.get("값"), row.get("값_적용후")
                row["값"] = val
                row["값_적용후"] = val_post
                n_updated += 1
                changes.append((code, item_no, "UPDATE", old_val, old_val_post, val, val_post))
            else:
                new_row = {
                    "원보험사코드": code, "원수사명": name, "티커": ticker,
                    "생손보여부": kind, "항목번호": item_no,
                    "항목명": LABELS[item_no], "공시분기": QUARTER,
                    "값": val, "값_적용후": val_post,
                }
                records.append(new_row)
                n_inserted += 1
                changes.append((code, item_no, "INSERT", None, None, val, val_post))

    after_rows = len(records)
    after_combos = len({(r.get("원보험사코드"), r.get("공시분기"), r.get("항목번호")) for r in records})

    print(f"rows: {before_rows} -> {after_rows} (delta {after_rows - before_rows})")
    print(f"combos: {before_combos} -> {after_combos} (delta {after_combos - before_combos})")
    print(f"updated={n_updated} inserted={n_inserted}")
    print()
    for c in changes:
        print(c)

    if isinstance(data, dict) and "records" in data:
        data["records"] = records
        out = data
    else:
        out = records
    with open(target_path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print("\nwrote", target_path)


if __name__ == "__main__":
    main()
