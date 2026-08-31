# -*- coding: utf-8 -*-
"""Reusable post-process for AIG (KR0029) historical backfill, one quarter at
a time. Run AFTER fill_period_to_disclosure.py / fill_subitems_to_disclosure.py
/ fill_market_subitems_to_disclosure.py have already loaded items 1-46 (or as
many as cadence allows) for the target quarter.

Does four things, all scoped to KR0029 + QUARTER only (never touches any
other company/quarter):
  A. item10 (6. 비지배지분) -- AIG's older-template MD tables omit this row
     entirely rather than printing 0. Only fill it when item4 == sum(5,6,7,
     8,9,11) EXACTLY WITHOUT item10 (i.e. the closure already holds, proving
     item10 must be 0) -- never force a value that doesn't close.
  B. item28 = item2/item14*100 (기본자본비율) -- disclosed nowhere as its own
     row; established repo convention is to compute+UPSERT
     ([[reference-kics-item28-computed]]).
  C. items 47-54 (TFI table, "[지급여력비율의 경과조치 적용에 관한 사항]
     (1) 공통적용 경과조치 관련") -- auto-parsed from the MD's own
     "경과조치 적용 전 | 경과조치 적용 후" table (not hand-copied), because
     the label set/format has been stable across the AIG quarters checked
     so far. Self-checks BEFORE writing: item48 ~= item14(적용전 core)*50%,
     and CAPPED formula min(47,48)+49[+item54] == item51 (both columns).
  D. mirror 값_적용후 = 값 for every item present this quarter -- AIG is a
     confirmed non-applier (raw MD states "당사는 경과조치를 적용하지 않음"
     every quarter checked; registry data/_derived/kics_transition_applicability.json
     also shows TFI/RPT/TAC/TIR/TER/TIRR/PCA_DEFER all X for 2025.4Q/2026.1Q).
     Verified per-quarter by re-checking that exact phrase is present in
     THIS quarter's MD before mirroring -- never assumed.

Usage: python _20260831_aig_quarter_postprocess.py FY2023_Q1 [--dry-run]
"""
from __future__ import annotations

import io
import json
import re
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

REPO = Path(r"C:\Users\sangwook.cho\Desktop\insurequant")
TARGET = REPO / "kics_disclosure.json"
MD_INBOX = REPO / "md_inbox"

CODE = "KR0029"
CNAME = "AIG손해보험"

TABLE_ROW_RE = re.compile(r"^\s*\|.*\|\s*$")

# Per-quarter manual overrides for items the general extractors miss because
# AIG's own per-risk-type sub-tables (주식/부동산/외환/자산집중위험액 현황,
# each an ad-hoc company-specific layout -- no general handler exists repo-
# wide for these, per docs/TODO.md's own admission) aren't auto-parsed, or a
# risk type's row is structurally absent from the source (0, matching this
# company's own established convention elsewhere). Populated by hand-reading
# the MD table for each quarter and cross-checking against the adjacent
# already-loaded comparative-period column before writing. Never applied to
# an item that's already present -- gap-fill only, never overwrite.
QUARTER_OVERRIDES: dict[str, dict[int, tuple[float, str]]] = {
    "FY2023_Q4": {
        30: (0.0, "1-2. 장수위험액"),
        37: (18.93, "3-2. 주식위험액"),
        38: (0.0, "3-3. 부동산위험액"),
        39: (31.01, "3-4. 외환위험액"),
        40: (287.49, "3-5. 자산집중위험액"),
    },
    "FY2025_Q1": {
        # docling parsed this PDF in a degraded fallback mode this session
        # (MD frontmatter: parse_profile=docling_partial_v4, parse_confidence
        # =0.55 vs the usual ~0.85-0.90) -- keyword localization correctly
        # identified the right page window (source_page_ranges 4-8;10-17
        # does span raw pages 11-16 where the K-ICS section actually lives),
        # but the resulting MD contains ONLY the preceding IFRS17 손익/BS
        # sections (ends after page ~17's B/S 자기자본 table) and the entire
        # 4-2. 지급여력비율 section (raw pp.11-16) never made it to text.
        # All values below read directly off the raw PDF via fitz
        # (data/disclosure/FY2025_Q1/raw/KR0029_AIG손해보험.pdf p.14-15,
        # 당분기(25.1Q) column). Comparative columns on the same pages
        # (24.4Q: 6101/2536/369/... , 24.3Q: 6247/2639/314/...) independently
        # reproduce already-loaded values exactly, cross-confirming the read.
        1: (6177.0, "가. 지급여력금액"),
        2: (6177.0, "기본자본"),
        3: (0.0, "보완자본"),
        4: (6177.0, "Ⅰ. 건전성감독기준 재무상태표 상의 순자산"),
        5: (1776.0, "1. 보통주"),
        6: (0.0, "2. 자본항목 중 보통주 이외의 자본증권"),
        7: (4845.0, "3. 이익잉여금"),
        8: (0.0, "4. 자본조정"),
        9: (117.0, "5. 기타포괄손익누계액"),
        10: (0.0, "6. 비지배지분"),
        11: (-560.0, "7. 조정준비금"),
        12: (0.0, "Ⅱ. 지급여력금액으로 불인정하는 항목 (지급이 예정된 주주배당액 등)"),
        13: (0.0, "Ⅲ. 보완자본으로 재분류하는 항목 (기본자본 자본증권의 인정한도를 초과한 금액 등)"),
        14: (2559.0, "나. 지급여력기준금액 (Ⅰ-Ⅱ+Ⅲ)"),
        15: (3302.0, "Ⅰ. 기본요구자본"),
        16: (831.0, "- 분산효과 : (1+2+3+4+5) - Ⅰ"),
        17: (2873.0, "1. 생명장기손해보험위험액"),
        18: (596.0, "2. 일반손해보험위험액"),
        19: (363.0, "3. 시장위험액"),
        20: (89.0, "4. 신용위험액"),
        21: (212.0, "5. 운영위험액"),
        22: (743.0, "Ⅱ. 법인세조정액"),
        23: (0.0, "Ⅲ. 기타 요구자본(1+2+3)"),
        24: (0.0, "1. 업권별 자본규제를 활용한 종속회사의 요구자본 환산치"),
        25: (0.0, "2. 비례성원칙을 적용한 종속회사의 요구자본 대응치"),
        26: (0.0, "3. 업권별 자본규제를 활용한 관계회사의 요구자본 환산치"),
        27: (241.34, "다. 지급여력비율 : 가 ÷ 나 × 100"),
        # TFI table (raw p.15, "(1) 공통적용 경과조치 관련" -- both 전/후
        # columns equal, non-applier). item48 self-check: 1279.73 ~=
        # item14*50%=1279.5 (diff 0.23). CAPPED: min(0,1279.73)+0+0=0=item51.
        47: (0.0, "보완자본 한도 적용 전"),
        48: (1279.73, "보완자본 한도"),
        49: (0.0, "해약환급금 부족분 상당액 중 해약환급금 상당액 초과분"),
        50: (6177.05, "기본자본(TFI표, 공통적용경과조치)"),
        51: (0.0, "보완자본(TFI표, 공통적용경과조치)"),
        52: (6177.05, "지급여력금액(TFI표, 공통적용경과조치)"),
        53: (0.0, "(기발행 신종자본증권)"),
        54: (0.0, "(기발행 후순위채무)"),
    },
    "FY2023_Q3": {
        # The core "[경과조치 적용 전 지급여력비율 세부]" breakdown table
        # spans raw PDF pages 9-10; docling's keyword-window capture only
        # kept page 9 (items 1-4) -- page 10 (items 5-27) never made it into
        # md_inbox/FY2023_Q3/KR0029_AIG손해보험.md at all (confirmed: the MD
        # jumps straight from item4's row into an unrelated IFRS17 table).
        # Values below are read directly off the raw PDF via fitz
        # (data/disclosure/FY2023_Q3/raw/KR0029_AIG손해보험.pdf, 당분기
        # (23.3Q) column only -- the 전분기/전전분기 comparative columns on
        # the same page independently reproduce 2023.2Q/2023.1Q's
        # already-loaded values exactly, cross-confirming the column read).
        5: (1776.0, "1. 보통주"),
        6: (0.0, "2. 자본항목 중 보통주 이외의 자본증권"),
        7: (4310.0, "3. 이익잉여금"),
        8: (0.0, "4. 자본조정"),
        9: (-214.0, "5. 기타포괄손익누계액"),
        11: (1261.0, "7. 조정준비금"),
        12: (0.0, "Ⅱ. 지급여력금액으로 불인정하는 항목 (지급이 예정된 주주배당액 등)"),
        13: (1109.0, "Ⅲ. 보완자본으로 재분류하는 항목 (기본자본 자본증권의 인정한도를 초과한 금액 등)"),
        15: (3225.0, "Ⅰ. 기본요구자본"),
        16: (759.0, "- 분산효과 : (1+2+3+4+5) - Ⅰ"),
        17: (2797.0, "1. 생명장기손해보험위험액"),
        18: (510.0, "2. 일반손해보험위험액"),
        19: (357.0, "3. 시장위험액"),
        20: (92.0, "4. 신용위험액"),
        21: (229.0, "5. 운영위험액"),
        22: (683.0, "Ⅱ. 법인세조정액"),
        23: (0.0, "Ⅲ. 기타 요구자본(1+2+3)"),
        24: (0.0, "1. 업권별 자본규제를 활용한 종속회사의 요구자본 환산치"),
        25: (0.0, "2. 비례성원칙을 적용한 종속회사의 요구자본 대응치"),
        26: (0.0, "3. 업권별 자본규제를 활용한 관계회사의 요구자본 환산치"),
        27: (280.58, "다. 지급여력비율 : 가 ÷ 나 × 100"),
        # TFI table (raw PDF p.11, "(1) 공통적용 경과조치 관련" -- both
        # 전/후 columns printed and equal, non-applier). item48 already in
        # master but wrong (item3-mislabel bug, same pattern as other
        # quarters) -- override's FIX-on-disagree path corrects it.
        47: (0.0, "보완자본 한도 적용 전"),
        48: (1270.93, "보완자본 한도"),
        49: (1108.82, "해약환급금 부족분 상당액 중 해약환급금 상당액 초과분"),
        50: (6023.06, "기본자본(TFI표, 공통적용경과조치)"),
        51: (1108.82, "보완자본(TFI표, 공통적용경과조치)"),
        53: (0.0, "(기발행 신종자본증권)"),
        54: (0.0, "(기발행 후순위채무)"),
    },
    "FY2024_Q4": {
        # 90-page filing (largest of AIG's 11 backfilled quarters) --
        # docling's keyword-window captured ⑤외환/⑥자산집중 (raw p.56) but
        # dropped ③주식위험액현황 (raw p.55, just above/interleaved with the
        # 금리위험액 continuation table) entirely from the MD. Read via fitz
        # p.55 "Ⅲ.합계주2)" 당기(24.4Q)=2,259백만원; comparative 직전반기
        # (24.2Q)=1,661 matches already-loaded item37 exactly.
        37: (22.59, "3-2. 주식위험액"),
        # Also missing from the auto-extraction (same as item37 -- fill_
        # market_subitems didn't capture raw p.56 either). Read from the
        # same fitz dump: ⑤외환 "계" 당기(24.4Q)=2,970백만원, ⑥자산집중
        # "계" 당기=34,108백만원, ④부동산=해당사항없음(0).
        38: (0.0, "3-3. 부동산위험액"),
        39: (29.70, "3-4. 외환위험액"),
        40: (341.08, "3-5. 자산집중위험액"),
    },
    "FY2024_Q2": {
        30: (0.0, "1-2. 장수위험액"),
        37: (16.61, "3-2. 주식위험액"),
        38: (0.0, "3-3. 부동산위험액"),
        39: (16.74, "3-4. 외환위험액"),
        40: (280.55, "3-5. 자산집중위험액"),
        # TFI table (1) 공통적용 for this quarter has a severe docling
        # header/row corruption ("경과조치 적용" | "전 경과조치" | "적용 후"
        # -- the "전" landed in the SECOND header cell, and the 기발행
        # 신종자본증권/후순위채무 labels split across two table rows), which
        # defeats find_tfi_table's column-position logic entirely (0 rows
        # auto-matched). Hand-read from md_inbox/FY2024_Q2/KR0029_AIG손해보험.md
        # L203-214 by POSITION (전/후 always equal, non-applier), self-checked:
        # item48=1299.46 ~= item14(2599)*50%=1299.5 (diff 0.04); CAPPED
        # min(47,48)+49+54 = min(0,1299.46)+0+0 = 0 = item51 (all zero, trivial).
        47: (0.0, "보완자본 한도 적용 전"),
        48: (1299.46, "보완자본 한도"),
        49: (0.0, "해약환급금 부족분 상당액 중 해약환급금 상당액 초과분"),
        50: (6569.05, "기본자본(TFI표, 공통적용경과조치)"),
        51: (0.0, "보완자본(TFI표, 공통적용경과조치)"),
        52: (6569.05, "지급여력금액(TFI표, 공통적용경과조치)"),
        53: (0.0, "(기발행 신종자본증권)"),
        54: (0.0, "(기발행 후순위채무)"),
    },
}

TFI_LABELS = {
    # canonical (space-stripped) row label -> (item_no, display name)
    "지급여력금액": (52, "지급여력금액(TFI표, 공통적용경과조치)"),
    "기본자본": (50, "기본자본(TFI표, 공통적용경과조치)"),
    "보완자본": (51, "보완자본(TFI표, 공통적용경과조치)"),
    "보완자본한도적용전": (47, "보완자본 한도 적용 전"),
    "보완자본한도": (48, "보완자본 한도"),
    "해약환급금부족분상당액중해약환급금상당액초과분": (49, "해약환급금 부족분 상당액 중 해약환급금 상당액 초과분"),
    "(기발행신종자본증권)": (53, "(기발행 신종자본증권)"),
    "(기발행후순위채무)": (54, "(기발행 후순위채무)"),
}


def _num_tfi_cell(v):
    """Like _num, but a bare dash in a TFI-table VALUE cell means "row is
    printed, amount is 0" (e.g. 47/49 when 보완자본=0 that quarter -- AIG
    2023.4Q/2024.1Q raw shows literal '-' for these, not '0'), whereas a
    genuinely EMPTY cell (no dash at all) still means "not printed" (kept
    None, matching the established item53/54 blank-후 precedent). Only
    matters for cells inside a row we've already matched to a TFI_LABELS
    entry, i.e. the row itself is confirmed present in the source table --
    this never fabricates a row that isn't there."""
    if v is None:
        return None
    s = str(v).strip()
    if s == "":
        return None
    if s in ("-", "N/A"):
        return 0.0
    return _num(v)


def _num(v):
    if v is None:
        return None
    s = str(v).strip()
    if s in ("", "-", "N/A"):
        return None
    neg = False
    if s.startswith("△") or s.startswith("▲") or s.startswith("▽") or s.startswith("▼"):
        neg = True
        s = s[1:]
    if s.startswith("(") and s.endswith(")"):
        neg = True
        s = s[1:-1]
    s = s.replace(",", "").replace(" ", "")
    try:
        val = float(s)
    except ValueError:
        return None
    return -val if neg else val


def _fmt(x: float) -> str:
    if x == int(x):
        return str(int(x))
    s = f"{x:.2f}".rstrip("0").rstrip(".")
    return s or "0"


def _fmt_ratio(x: float) -> str:
    s = f"{x:.8f}".rstrip("0").rstrip(".")
    return s or "0"


def _split_row(line: str) -> list[str]:
    inner = line.strip()
    if inner.startswith("|"):
        inner = inner[1:]
    if inner.endswith("|"):
        inner = inner[:-1]
    return [c.strip() for c in inner.split("|")]


def _is_sep(cells: list[str]) -> bool:
    return bool(cells) and all(set(c) <= set("-: ") for c in cells)


def _tables_with_pos(lines: list[str]) -> list[tuple[int, list[list[str]]]]:
    out = []
    cur: list[list[str]] = []
    start = 0
    for i, line in enumerate(lines):
        if TABLE_ROW_RE.match(line):
            cells = _split_row(line)
            if _is_sep(cells):
                continue
            if not cur:
                start = i
            cur.append(cells)
        else:
            if cur:
                out.append((start, cur))
                cur = []
    if cur:
        out.append((start, cur))
    return out


def find_tfi_table(md_text: str) -> tuple[dict, dict, float] | None:
    """Returns (values_before, values_after, unit_scale) or None if not found.

    Column position is deliberately NOT resolved via header text -- observed
    header variants across AIG's own quarters (docling mangles this specific
    header worse each time): 2023.1Q "경과조치 적용 전|경과조치 적용 후"
    (clean); 2023.2Q "...전|경과조치|적용 후" (header cell split in two);
    2023.4Q/2024.1Q "...전|적용 후" (no "경과조치" prefix on 후); 2024.3Q
    "전 경과조치|적용 후" (word order reversed, no "적용" at all in the 전
    cell). No single header-text rule survives all four.

    Instead: identify the table by BODY CONTENT (지급여력금액 +
    지급여력기준금액 rows, both required in every variant seen), then per
    data row take value_전 = the FIRST non-empty value cell (after the
    label) and value_후 = the LAST non-empty value cell. For a confirmed
    non-applier (전==후 always, checked by the caller before this table is
    trusted) this is correct even when docling's OWN column boundaries shift
    row-to-row within the same table (2024.2Q has this -- see that quarter's
    QUARTER_OVERRIDE instead, this heuristic still isn't enough for a header
    where "전" migrates into a DIFFERENT column than where 전's own value
    prints), because whichever cell actually holds a number, it's read as
    both endpoints of the same equal-by-construction pair when the row has
    only one non-empty value; when it has two, first/last picks each side
    correctly since 전 always prints left of 후 in every variant seen.
    """
    lines = md_text.splitlines()
    tables = _tables_with_pos(lines)
    for start_idx, tbl in tables:
        if len(tbl) < 4:
            continue
        body_labels = "".join((r[0] if r else "") for r in tbl[1:]).replace(" ", "")
        if "지급여력금액" not in body_labels or "지급여력기준금액" not in body_labels:
            continue
        header_join = "".join(tbl[0]).replace(" ", "")
        if "경과조치" not in header_join or "적용" not in header_join:
            continue
        # unit scale: search backward for nearest '(단위: ...)' marker
        scale = 1.0
        for j in range(start_idx - 1, max(0, start_idx - 40) - 1, -1):
            l = lines[j]
            if "단위" not in l:
                continue
            if "백만원" in l:
                scale = 100.0
            elif "천원" in l:
                scale = 100_000.0
            else:
                scale = 1.0
            break
        before: dict[str, float] = {}
        after: dict[str, float] = {}
        for row in tbl[1:]:
            if not row:
                continue
            label = row[0].replace(" ", "")
            if label not in TFI_LABELS:
                continue
            item_no, _name = TFI_LABELS[label]
            vb = None
            for j in range(1, len(row)):
                vb = _num_tfi_cell(row[j])
                if vb is not None:
                    break
            va = None
            for j in range(len(row) - 1, 0, -1):
                va = _num_tfi_cell(row[j])
                if va is not None:
                    break
            if vb is not None:
                before[item_no] = vb / scale
            if va is not None:
                after[item_no] = va / scale
        return before, after, scale
    return None


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: _20260831_aig_quarter_postprocess.py FYxxxx_Qn [--dry-run]")
        return 1
    period = sys.argv[1]
    dry = "--dry-run" in sys.argv
    m = re.match(r"^FY(\d{4})_Q([1-4])$", period)
    if not m:
        print(f"bad period {period!r}")
        return 1
    quarter = f"{m.group(1)}.{m.group(2)}Q"

    md_path = MD_INBOX / period / f"{CODE}_{CNAME}.md"
    if not md_path.exists():
        print(f"ABORT: MD not found: {md_path}")
        return 1
    md_text = md_path.read_text(encoding="utf-8")

    data = json.loads(TARGET.read_text(encoding="utf-8"))
    bucket = {r["항목번호"]: r for r in data if r.get("원보험사코드") == CODE and r.get("공시분기") == quarter}
    other_quarter_row = next((r for r in data if r.get("원보험사코드") == CODE), None)
    if not bucket and other_quarter_row is None:
        print(f"ABORT: no rows for {CODE} anywhere -- run fill_period_to_disclosure.py first")
        return 1
    if not bucket:
        # fill_period/fill_subitems/fill_market found nothing at all this
        # quarter (e.g. FY2025_Q1: docling parsed in a degraded fallback
        # mode and the MD never reached the K-ICS section) -- QUARTER_
        # OVERRIDES is the only path in, so borrow the code/cname/ticker/
        # kind template from any other quarter of this same company instead
        # of aborting.
        print(f"NOTE: no existing rows for {CODE} {quarter} -- using another quarter's row as field template (QUARTER_OVERRIDES-only path)")
        template = other_quarter_row
    else:
        template = bucket[min(bucket)]
    changes: list[str] = []

    # --- confirm non-applier text present this quarter (never assume) ---
    # FY2025_Q1: docling's degraded parse never reached the K-ICS section at
    # all (md_inbox MD ends at the preceding IFRS17 B/S table), so the
    # confirming phrase can't be found in THIS md_text no matter what it
    # says -- independently confirmed non-applier via raw PDF p.11 (적용여부
    # table: RPT=O only, TFI/TAC/TIR/TER/TIRR/PCA_DEFER all X, same pattern
    # as every other AIG quarter) and p.15 (explicit "당사는 ... 경과조치를
    # 적용하지 않아 경과조치 전·후 금액 및 비율이 동일함" for options ①②③,
    # plus the TFI table's 전==후 for every row).
    _RAW_PDF_CONFIRMED_NON_APPLIER = {"FY2025_Q1"}
    non_applier_ok = (
        "경과조치를 적용하지 않" in md_text
        or "경과조치를  적용하지  않" in md_text
        or period in _RAW_PDF_CONFIRMED_NON_APPLIER
    )
    print(f"non-applier phrase found in MD: {non_applier_ok}")
    if not non_applier_ok:
        print("WARNING: non-applier confirmation phrase NOT found -- 값_적용후 mirror step will be SKIPPED for manual review")

    # --- A. item10 via exact closure (only if item10 absent) ---
    if 10 not in bucket:
        need = [4, 5, 6, 7, 8, 9, 11]
        vals = {n: _num(bucket[n]["값"]) if n in bucket else None for n in need}
        if all(v is not None for v in vals.values()):
            implied = vals[4] - (vals[5] + vals[6] + vals[7] + vals[8] + vals[9] + vals[11])
            # tol 1.5: each of the 6 addends + item4 itself is independently
            # rounded to the nearest 억원 in AIG's older-template table, so
            # up to ~1-unit closure noise is expected rounding, not a real
            # missing value (verified: 2023.1Q closes exactly at 0, 2023.2Q
            # at -1 -- both with item10's row structurally absent from the
            # source table, not printed as an explicit 0).
            if abs(implied) < 1.5:
                row10 = {
                    "원보험사코드": template["원보험사코드"], "원수사명": template["원수사명"],
                    "티커": template["티커"], "생손보여부": template["생손보여부"],
                    "항목번호": 10, "항목명": "6. 비지배지분", "공시분기": quarter, "값": "0",
                }
                data.append(row10)
                bucket[10] = row10
                changes.append(f"ADD item10=0 (closure: item4={vals[4]} - sum(5,6,7,8,9,11)={vals[4]-implied} = {implied:.4f} ~= 0)")
            else:
                changes.append(f"SKIP item10 -- closure does NOT hold without it (implied={implied:.2f}, NOT close to 0) -- NEEDS MANUAL REVIEW")
        else:
            missing = [n for n, v in vals.items() if v is None]
            changes.append(f"SKIP item10 -- inputs missing for closure check: items {missing}")
    else:
        changes.append(f"SKIP item10 -- already present 값={bucket[10]['값']}")

    # --- B. item28 = item2/item14*100 ---
    if 28 not in bucket:
        i2 = _num(bucket[2]["값"]) if 2 in bucket else None
        i14 = _num(bucket[14]["값"]) if 14 in bucket else None
        if i2 is not None and i14:
            val28 = i2 / i14 * 100.0
            row28 = {
                "원보험사코드": template["원보험사코드"], "원수사명": template["원수사명"],
                "티커": template["티커"], "생손보여부": template["생손보여부"],
                "항목번호": 28, "항목명": "기본자본비율", "공시분기": quarter, "값": _fmt_ratio(val28),
            }
            data.append(row28)
            bucket[28] = row28
            changes.append(f"ADD item28={row28['값']} (=item2/item14*100={i2}/{i14}*100)")
        else:
            changes.append(f"SKIP item28 -- item2 or item14 missing")
    else:
        changes.append(f"SKIP item28 -- already present 값={bucket[28]['값']}")

    # --- B2. QUARTER_OVERRIDES gap-fill (hand-verified, additive only) ---
    for item_no, (val_eok, name) in QUARTER_OVERRIDES.get(period, {}).items():
        if item_no in bucket:
            existing = bucket[item_no]
            old_val = _num(existing.get("값"))
            if old_val is not None and abs(old_val - val_eok) <= max(0.5, 0.005 * abs(val_eok or 1)):
                changes.append(f"SKIP item{item_no} override -- already present and matches 값={existing['값']}")
            else:
                changes.append(f"FIX item{item_no} override 값 {existing.get('값')!r} -> {_fmt(val_eok)!r} ({name}) -- disagreed with hand-verified value")
                existing["값"] = _fmt(val_eok)
                existing["항목명"] = name
                if 47 <= item_no <= 52 and existing.get("값_적용후") in (None, ""):
                    existing["값_적용후"] = _fmt(val_eok)
            continue
        row = {
            "원보험사코드": template["원보험사코드"], "원수사명": template["원수사명"],
            "티커": template["티커"], "생손보여부": template["생손보여부"],
            "항목번호": item_no, "항목명": name, "공시분기": quarter, "값": _fmt(val_eok),
        }
        # items 47-54 are non-applier TFI memo rows read directly off the
        # source's 전/후 columns (both equal) -- set 값_적용후 immediately so
        # they don't depend on the items-1-46-only mirror step below. Items
        # 30/37-40 (core sub-risk overrides) get 값_적용후 from that mirror
        # step instead, same as their auto-extracted siblings.
        if 47 <= item_no <= 52:
            row["값_적용후"] = row["값"]
        # item53/54 값_적용후 deliberately left unset here even when >= 47 --
        # every other quarter's TFI table shows a genuinely BLANK 후 cell for
        # these two memo rows (not a dash), and FY2024_Q2's row-split
        # corruption (L212-213) makes that cell unreadable with confidence
        # for THIS quarter specifically -- matches established precedent
        # rather than guessing.
        data.append(row)
        bucket[item_no] = row
        changes.append(f"ADD item{item_no}={row['값']} 값_적용후={row.get('값_적용후')} ({name}) [hand-verified QUARTER_OVERRIDE, source table has no general extractor]")

    # --- C. TFI 47-54, auto-parsed from MD ---
    tfi = find_tfi_table(md_text)
    if tfi is None:
        changes.append("TFI table NOT FOUND in MD -- items 47-54 left untouched")
    else:
        before, after, scale = tfi
        print(f"TFI table found (unit scale={scale}x): before={before}")
        print(f"                                        after={after}")
        # self-check 1: item48 ~= item14(core, 적용전) * 50%
        i14_core = _num(bucket[14]["값"]) if 14 in bucket else None
        if i14_core is not None and 48 in before:
            expected48 = i14_core * 0.5
            diff48 = abs(expected48 - before[48])
            print(f"self-check item48: before[48]={before[48]:.2f} vs item14*50%={expected48:.2f} diff={diff48:.2f}")
            if diff48 > max(2.0, 0.02 * expected48):
                changes.append(f"ABORT-TFI: item48 self-check FAILED (before[48]={before[48]:.2f} != item14*50%={expected48:.2f})")
                tfi = None
        # self-check 2: CAPPED formula min(47,48)+49[+54] == 51 (both columns)
        if tfi is not None:
            for label, vals in (("전", before), ("후", after)):
                if all(k in vals for k in (47, 48, 49, 51)):
                    m47, m48, m49, m51 = vals[47], vals[48], vals[49], vals[51]
                    m54 = vals.get(54, 0.0)
                    expected51 = min(m47, m48) + m49 + m54
                    diff51 = abs(expected51 - m51)
                    print(f"self-check item51({label}): min({m47:.2f},{m48:.2f})+{m49:.2f}+{m54:.2f}={expected51:.2f} vs actual={m51:.2f} diff={diff51:.2f}")
                    if diff51 > max(2.0, 0.02 * abs(m51 or 1)):
                        changes.append(f"ABORT-TFI: item51({label}) CAPPED-formula self-check FAILED (expected={expected51:.2f} actual={m51:.2f})")
                        tfi = None
        if tfi is not None:
            for item_no in sorted(TFI_LABELS[k][0] for k in TFI_LABELS):
                name = next(n for k, (i, n) in TFI_LABELS.items() if i == item_no)
                vb = before.get(item_no)
                va = after.get(item_no)
                if vb is None and va is None:
                    continue
                row = bucket.get(item_no)
                if row is None:
                    new_row = {
                        "원보험사코드": template["원보험사코드"], "원수사명": template["원수사명"],
                        "티커": template["티커"], "생손보여부": template["생손보여부"],
                        "항목번호": item_no, "항목명": name, "공시분기": quarter,
                        "값": _fmt(vb) if vb is not None else _fmt(va),
                    }
                    if va is not None:
                        new_row["값_적용후"] = _fmt(va)
                    data.append(new_row)
                    bucket[item_no] = new_row
                    changes.append(f"ADD item{item_no} 값={new_row['값']} 값_적용후={new_row.get('값_적용후')} ({name})")
                else:
                    # self-check-validated vb/va is trusted ground truth here
                    # (tfi would be None and this branch unreached otherwise).
                    # If a pre-existing value disagrees, that's the known
                    # item48-label-confusion bug pattern (e.g. item48 storing
                    # item3/item51's value instead of its own) -- fix it,
                    # don't silently keep the wrong number.
                    old_val = _num(row.get("값"))
                    new_val = vb if vb is not None else va
                    if new_val is not None and (old_val is None or abs(old_val - new_val) > max(0.5, 0.005 * abs(new_val))):
                        changes.append(f"FIX item{item_no} 값 {row.get('값')!r} -> {_fmt(new_val)!r} ({name}) -- disagreed with self-check-validated TFI table value")
                        row["값"] = _fmt(new_val)
                        row["항목명"] = name
                    else:
                        changes.append(f"SKIP item{item_no} -- already present and matches 값={row.get('값')}")
                    if va is not None and row.get("값_적용후") in (None, ""):
                        row["값_적용후"] = _fmt(va)
                        changes.append(f"  + also filled 값_적용후={_fmt(va)} (was missing)")

    # --- D. mirror 값_적용후 = 값 for items 1-46 present this quarter (non-applier only) ---
    if non_applier_ok:
        mirrored = 0
        for item_no in range(1, 47):
            row = bucket.get(item_no)
            if row is None:
                continue
            if row.get("값_적용후") not in (None, ""):
                continue
            if row.get("값") in (None, ""):
                continue
            row["값_적용후"] = row["값"]
            mirrored += 1
        changes.append(f"MIRROR 값_적용후=값 for {mirrored} rows (items 1-46 present, previously missing 값_적용후)")

    print(f"\n{'DRY-RUN: ' if dry else ''}{len(changes)} change groups for {CODE} {quarter}:")
    for c in changes:
        print(" ", c)

    if dry:
        return 0

    if any(c.startswith("ABORT") for c in changes):
        print("\nABORTED -- not writing (see ABORT lines above)")
        return 1

    TARGET.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nwrote {len(data)} rows")
    return 0


if __name__ == "__main__":
    sys.exit(main())
