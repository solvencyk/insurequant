# -*- coding: utf-8 -*-
"""Manual patches: 생명·장기손해보험위험액 하위위험(item29-35) cells where docling's MD
lost the source table (or the table has no header row a scanner can key off), verified
directly against the raw disclosure PDF via fitz text extraction.

## Why manual, not the fill script

`scripts/fill_subitems_to_disclosure.py` drives off `md_inbox/<period>/<code>_*.md`. For
each (code, quarter) below, the MD's rendition of the "② 장수위험·사업비위험·해지위험 및
대재해위험 경과조치" (or equivalent) sub-risk table is missing rows entirely or lost its
header row, so the automated scanner returns nothing for those items even though the raw
PDF has clean text. Confirmed per-cell via
`scripts/_probes/probe_20260903_life2935_triage.py` (LABELS_PRESENT_NO_PARSE /
LABELS_ABSENT-with-raw-text-present) before adding an entry here — this script is NOT a
first resort, it's the documented fallback once the MD is confirmed to have lost the data.

## Provenance (per company, cited inline below and in TODO_parser_kics.md)

Values are 백만원 in the source table; divided by 100 to match the 억원 convention used by
the rest of kics_disclosure.json.

## Overwrite policy

Additive only, like `fill_subitems_to_disclosure.py` — this script REFUSES to touch a
(code, quarter, item_no) that already has a row (asserts absence, doesn't assert+overwrite
like the TFI-resubmission fix scripts). Idempotent: safe to re-run, already-applied targets
are skipped with a note. Reloads the JSON immediately before writing to minimize the window
for a lost update from a concurrent session.

Usage: python scripts/fix_20260903_life2935_manual_patches.py [--apply]
(dry-run by default; prints every row this would insert).
"""
from __future__ import annotations

import argparse
import io
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
JSON_PATH = REPO / "kics_disclosure.json"

ITEM_NAMES = {
    29: "1-1. 사망위험액",
    30: "1-2. 장수위험액",
    31: "1-3. 장해·질병위험액",
    32: "1-4. 장기재물·기타위험액",
    33: "1-5. 해지위험액",
    34: "1-6. 사업비위험액",
    35: "1-7. 대재해위험액",
}

# (code, quarter) -> {item_no: (값, 값_적용후 or None)}
#
# KR0050 하나손해보험 2026.1Q: raw p20 (`data/disclosure/FY2026_Q1/raw/
# KR0050_하나손해보험.pdf`), section "[지급여력비율의 경과조치 적용에 관한 사항]
# (2) 선택적용 경과조치 관련 ② 장수위험·사업비위험·해지위험 및 대재해위험 경과조치"
# (단위: 백만원). md_inbox/FY2026_Q1/KR0050_하나손해보험.md L138-146 shows this table
# with an `<!-- image -->` marker right before it and only 2 of 7 labels/values surviving
# conversion (사업비위험/대재해위험, no header row) -- the other 5 rows (사망/장수/장해질병/
# 장기재물기타/해지) never made it into the MD as text at all. Raw PDF text (fitz) is
# unambiguous:
#   사망위험 6,409 / 장수위험 10 / 장해·질병위험 122,355 / 장기재물·기타위험 7,264 /
#   해지위험 130,187 / 사업비위험 43,509 / 대재해위험 5,051  (all 백만원)
# Footnote on the same page: "당사는 장수위험·사업비위험·해지위험 및 대재해위험 경과조치를
# 적용하지 않아 경과조치 전·후 금액 및 비율이 동일함" -- explicit pre=post statement, so
# 값_적용후 is set equal to 값 (not a guess; matches the convention already used for every
# other KR0050 item29-35 row in this dataset, all of which have 값==값_적용후, e.g.
# 2026.2Q item29 62.58/62.58). Sanity: sum(29-35)/item17 = 3147.85/2157.56 = 1.46, within
# the 1.2-1.6 diversified-sum range documented in the kics-parser skill.
# KR0087 동양생명 2023.2Q: raw p15-16 (`FY2023_Q2/raw/KR0087_동양생명.pdf`), "(2) 생명·
# 장기손해보험위험액 현황" 당기(2023.2Q) block (백만원): 사망137,543 장수38,923 장해질병
# 859,861 장기재물기타0 해지1,743,777 사업비315,172; item35 from the adjoining
# [생명장기손해보험위험액-대재해위험] Ⅲ.총계=94,348. p13 confirms "(나) 장수위험·사업비
# 위험·해지위험 및 대재해위험 경과조치 ... 미적용으로 경과조치 전·후 금액 및 비율이 동일"
# -> 값_적용후=값. Sanity: sum/item17 = 31896.24/22342 = 1.43.
#
# KR0104 농협생명보험 2023.2Q: raw p13 (`FY2023_Q2/raw/KR0104_농협생명보험_amended.pdf`),
# "② 장수위험·사업비위험·해지위험 및 대재해위험 경과조치" table -- THIS company shows an
# explicit, DIFFERING 경과조치 적용전/적용후 pair (applier, unlike the others in this batch):
# 사망245,330/245,330 장수34,192/- 장해질병780,809/780,809 장기재물기타-/- 해지2,238,984/
# 209,385 사업비245,424/- 대재해70,726/- (백만원; dash in the leaf 후 column = 0, matches
# `_parse_leaf_subrisk_value` convention). Cross-checked against p18-19's non-transition
# detail table, which independently reprints the SAME 전 values. Sanity: sum(전)/item17 =
# 36154.65/26036 = 1.39.
#
# KR0074 라이나생명보험 2023.2Q (2 cells only -- 29/30/31/33/34 already in master): raw p15
# (`FY2023_Q2/raw/KR0074_라이나생명보험_amended.pdf`) "생명·장기손해보험위험액-대재해위험
# 이외" 당기(2023.2Q) row shows 장기재물·기타위험 = "ㅡ" (dash) -> 0; item35 from p16
# [...-대재해위험] Ⅲ.총계 당기(2023.2Q) = 36,901백만원. p13 "② 장수위험·사업비위험·해지
# 위험 및 대재해위험 경과조치 ... 적용하지 않아 경과조치 전·후 금액 및 비율이 동일함" ->
# 값_적용후=값 for both.
#
# KR0087 동양생명 2023.4Q (item35 only -- 29-34 already in master): raw p47 (`FY2023_Q4/raw/
# KR0087_동양생명.pdf`) [생명장기손해보험위험액ㆍ대재해위험] table, 4-column layout
# (당기 exposure/위험액, 직전반기 exposure/위험액); Ⅲ.총계 row = 479,720,796/91,608/
# 488,381,409/94,348 -- the SECOND pair (488,381,409/94,348) independently matches the
# already-verified 2023.2Q item35 (94,348, see KR0087 2023.2Q entry above), confirming the
# FIRST pair (91,608) is 당기(2023.4Q). p29 "② ... 미적용으로 경과조치 전·후 금액 및 비율이
# 동일하며 기재 생략" -> 값_적용후=값.
#
# KR0087 동양생명 2025.2Q (item32 only -- rest already in master): raw p19 (`FY2025_Q2/raw/
# KR0087_동양생명.pdf`) 당기(2025.2Q) row: 장기재물·기타위험 = 0 explicitly. p17 "②...
# 미적용...동일하며 기재 생략" -> 값_적용후=값.
#
# KR0029 AIG손해보험 2025.2Q: raw p20 (`FY2025_Q2/raw/KR0029_AIG손해보험.pdf`) 당기
# (2025.2Q) row (백만원): 사망16,163 장수0 장해질병205,465 장기재물기타433 해지109,276
# 사업비70,182; item35 from p21 [...-대재해위험] Ⅲ.총계 당기(2025.2Q)=2,457. p16 "②...
# 적용하지 않아 경과조치 전·후 금액 및 비율이 동일함" -> 값_적용후=값. Sanity: sum/item17 =
# 4039.76/2902 = 1.39.
#
# KR1098 카카오페이손해보험 2025.2Q: raw p21 (`FY2025_Q2/raw/KR1098_카카오페이손해보험.pdf`,
# reading order is column-scrambled by fitz -- verified the 당기/직전 block assignment via
# the trailer header text "구분|2025년2/4분기|2024년4/4분기|익스포져 대재해위험액 익스포져
# 대재해위험액" and matching row-position). 당기(2025.2Q), 백만원: 사망- (0) 장수2 장해질병
# 1,252 장기재물기타6 해지557 사업비425; item35 Ⅲ.총계 당기=17. p17 "...적용하지 않아
# 경과조치 전후 금액 및 비율이 동일함" -> 값_적용후=값. Sanity: sum/item17 = 22.59/17 = 1.33
# (item17 tiny -- KR1098 is a micro digital insurer, rounding-sensitive but in-range).
#
# KR0094 신한라이프생명보험 2024.2Q (5 cells -- 32/35 already in master): raw p19
# (`FY2024_Q2/raw/KR0094_신한라이프생명보험.pdf`), docling/fitz emits this company's table
# labels character-split (e.g. "사\n망\n위\n험") -- confirmed the block-order (당기 first,
# 직전반기 second) by matching the SECOND block byte-for-byte against the already-loaded
# KR0094 2023.4Q master row (사망500,137=5001.37억 등, all 6 core items match exactly).
# 당기(2024.2Q), 백만원: 사망539,175 장수108,178 장해질병2,177,442 해지2,481,348
# 사업비1,002,042 (장기재물기타=0, 대재해=245,150 already present in master, not touched).
# **값_적용후 NOT set** -- unlike the other cells in this batch, this page's text does not
# include a "②...미적용...동일함" statement in the extracted range, and the company's
# common-TFI table (p15) shows PRE!=POST for other items (기본자본/보완자본), so pre=post
# cannot be assumed here without direct confirmation. Left for a future post-transition pass.
#
# KR0094 신한라이프생명보험 2026.2Q: raw p25-26 (`FY2026_Q2/raw/KR0094_신한라이프생명보험.pdf`,
# same character-split table + block-order verified against the already-loaded KR0094
# 2025.4Q master row, all 6 core items match exactly). 당기(2026.2Q), 백만원: 사망395,666
# 장수95,317 장해질병1,771,412 장기재물기타- (0) 해지4,087,510 사업비860,969; item35 from
# separate [...-대재해위험] table Ⅲ.총계 당기=235,277 (직전 236,842 matches master 2025.4Q
# exactly). p21 "...장수위험·사업비위험·해지위험 및 대재해위험 경과조치를 적용하지 않아
# 경과조치 전·후 금액 및 비율이 동일함" -> 값_적용후=값. Sanity: sum/item17 = 74461.51/52371
# = 1.42.
#
# KR0099 KB라이프생명 2026.2Q: raw p25 (`FY2026_Q2/raw/KR0099_케이비라이프생명보험.pdf`)
# 당기(2026.2Q), 백만원: 사망336,659 장수43,987 장해질병386,077 장기재물기타- (0)
# 해지2,356,799 사업비448,008; item35 from Ⅲ.총계 당기=107,412. p21 "②...적용하지 않아
# 경과조치 전∙후 금액 및 비율이 동일함" -> 값_적용후=값. Sanity: sum/item17 = 36789.42/27648
# = 1.33.
#
# KR0104 농협생명보험 2026.1Q: raw p20 (`FY2026_Q1/raw/KR0104_농협생명보험.pdf`) "②
# 장수위험·사업비위험·해지위험 및 대재해위험 경과조치" table, explicit differing 경과조치
# 적용전/적용후 pair (this company is a consistent TIR/TER/TIRR/TAC applier -- same pattern
# as its already-loaded 2023.2Q row). 백만원: 사망270,509/270,509 장수19,872/- 장해질병
# 907,944/907,944 장기재물기타-/- 해지1,917,597/496,878 사업비255,296/76,905
# 대재해83,554/33,792 (dash = 0, leaf sub-risk convention). Surfaced by the new
# `8_life_census` completeness rule (owner-confirmed gap: "농협생명보험 2026.1Q: 선택
# 경과조치 적용사인데 없다" -- `kics_transition_applicability.json` TIR/TER/TIRR/TAC lookup
# independently confirms 'O'). Sanity: sum(전)/item17 = 34547.72/23843 = 1.45.
#
# KR0051 신한이지손해보험 2026.2Q (item30 only -- rest already in master): raw p17
# (`FY2026_Q2/raw/KR0051_신한이지손해보험.pdf`) -- linear text reading order is scrambled
# (row labels emitted out of visual sequence), resolved via word-bbox row-clustering
# (`scripts/_probes/probe_20260903_wordbbox_table.py KR0051 2026.2Q 17`): row y=489 reads
# "당기 | 장수위험 | - | -" (both Ⅱ.장기손해보험 and Ⅲ.총계 columns are dash) while the
# 직전반기(25.4Q) row at y=618 reads "장수위험 | - | 3 | 3", which matches the already-loaded
# master value for 2025.4Q item30 (0.03억=3백만원) exactly -- cross-validates the row
# clustering. So 당기(2026.2Q) 장수위험 = 0 (genuinely disclosed as "-", not a parse gap).
# p15 confirms "...장수위험·사업비위험·해지위험 및 대재위험 경과조치 ... 동일함" ->
# 값_적용후=값=0.
PATCHES: dict[tuple[str, str], dict[int, tuple[str, str | None]]] = {
    ("KR0050", "2026.1Q"): {
        29: ("64.09", "64.09"),
        30: ("0.1", "0.1"),
        31: ("1223.55", "1223.55"),
        32: ("72.64", "72.64"),
        33: ("1301.87", "1301.87"),
        34: ("435.09", "435.09"),
        35: ("50.51", "50.51"),
    },
    ("KR0087", "2023.2Q"): {
        29: ("1375.43", "1375.43"),
        30: ("389.23", "389.23"),
        31: ("8598.61", "8598.61"),
        32: ("0", "0"),
        33: ("17437.77", "17437.77"),
        34: ("3151.72", "3151.72"),
        35: ("943.48", "943.48"),
    },
    ("KR0104", "2023.2Q"): {
        29: ("2453.3", "2453.3"),
        30: ("341.92", "0"),
        31: ("7808.09", "7808.09"),
        32: ("0", "0"),
        33: ("22389.84", "2093.85"),
        34: ("2454.24", "0"),
        35: ("707.26", "0"),
    },
    ("KR0074", "2023.2Q"): {
        32: ("0", "0"),
        35: ("369.01", "369.01"),
    },
    ("KR0087", "2023.4Q"): {
        35: ("916.08", "916.08"),
    },
    ("KR0087", "2025.2Q"): {
        32: ("0", "0"),
    },
    ("KR0029", "2025.2Q"): {
        29: ("161.63", "161.63"),
        30: ("0", "0"),
        31: ("2054.65", "2054.65"),
        32: ("4.33", "4.33"),
        33: ("1092.76", "1092.76"),
        34: ("701.82", "701.82"),
        35: ("24.57", "24.57"),
    },
    ("KR1098", "2025.2Q"): {
        29: ("0", "0"),
        30: ("0.02", "0.02"),
        31: ("12.52", "12.52"),
        32: ("0.06", "0.06"),
        33: ("5.57", "5.57"),
        34: ("4.25", "4.25"),
        35: ("0.17", "0.17"),
    },
    ("KR0094", "2024.2Q"): {
        29: ("5391.75", None),
        30: ("1081.78", None),
        31: ("21774.42", None),
        33: ("24813.48", None),
        34: ("10020.42", None),
    },
    ("KR0094", "2026.2Q"): {
        29: ("3956.66", "3956.66"),
        30: ("953.17", "953.17"),
        31: ("17714.12", "17714.12"),
        32: ("0", "0"),
        33: ("40875.1", "40875.1"),
        34: ("8609.69", "8609.69"),
        35: ("2352.77", "2352.77"),
    },
    ("KR0099", "2026.2Q"): {
        29: ("3366.59", "3366.59"),
        30: ("439.87", "439.87"),
        31: ("3860.77", "3860.77"),
        32: ("0", "0"),
        33: ("23567.99", "23567.99"),
        34: ("4480.08", "4480.08"),
        35: ("1074.12", "1074.12"),
    },
    ("KR0051", "2026.2Q"): {
        30: ("0", "0"),
    },
    ("KR0104", "2026.1Q"): {
        29: ("2705.09", "2705.09"),
        30: ("198.72", "0"),
        31: ("9079.44", "9079.44"),
        32: ("0", "0"),
        33: ("19175.97", "4968.78"),
        34: ("2552.96", "769.05"),
        35: ("835.54", "337.92"),
    },
}


def _baseline_meta(rows: list[dict], code: str) -> dict[str, str] | None:
    for r in rows:
        if r["원보험사코드"] == code:
            return {"원수사명": r["원수사명"], "티커": r["티커"], "생손보여부": r["생손보여부"]}
    return None


def main(argv: list[str]) -> int:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="write changes (default: dry-run)")
    args = ap.parse_args(argv)

    rows = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    print(f"loaded {len(rows)} rows from {JSON_PATH}")

    existing = {(r["원보험사코드"], r["공시분기"], r["항목번호"]) for r in rows}

    to_insert: list[dict] = []
    skipped: list[str] = []
    for (code, quarter), items in PATCHES.items():
        meta = _baseline_meta(rows, code)
        if not meta:
            print(f"ABORT: no baseline metadata for {code}")
            return 1
        for item_no, (val, val_post) in sorted(items.items()):
            key = (code, quarter, item_no)
            if key in existing:
                skipped.append(f"{code} {quarter} item{item_no}: already present, skipping")
                continue
            new_row = {
                "원보험사코드": code,
                "원수사명": meta["원수사명"],
                "티커": meta["티커"],
                "생손보여부": meta["생손보여부"],
                "항목번호": item_no,
                "항목명": ITEM_NAMES[item_no],
                "공시분기": quarter,
                "값": val,
            }
            if val_post is not None:
                new_row["값_적용후"] = val_post
            to_insert.append(new_row)

    if skipped:
        print("\nalready-applied (skipped):")
        for s in skipped:
            print(f"  {s}")

    print(f"\n{len(to_insert)} row(s) to insert:")
    for r in to_insert:
        print(f"  {r['원보험사코드']} {r['공시분기']} item{r['항목번호']} ({r['항목명']}) "
              f"값={r['값']} 값_적용후={r.get('값_적용후')}")

    if not to_insert:
        print("\nnothing to write")
        return 0

    if not args.apply:
        print("\n(dry-run; pass --apply to write)")
        return 0

    # Reload immediately before writing to minimize the lost-update window.
    fresh_rows = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    fresh_existing = {(r["원보험사코드"], r["공시분기"], r["항목번호"]) for r in fresh_rows}
    reconfirmed = [r for r in to_insert if (r["원보험사코드"], r["공시분기"], r["항목번호"]) not in fresh_existing]
    if len(reconfirmed) != len(to_insert):
        print("ABORT: some target rows appeared since the initial read (concurrent write) -- rerun to recompute")
        return 1

    backup_path = JSON_PATH.with_suffix(JSON_PATH.suffix + ".bak_pre_life2935_manual_patches")
    if not backup_path.exists():
        backup_path.write_text(json.dumps(fresh_rows, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"backup written: {backup_path}")

    fresh_rows.extend(to_insert)
    JSON_PATH.write_text(json.dumps(fresh_rows, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {len(fresh_rows)} rows to {JSON_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
