"""Build CSM Movement Waterfall data for the HTML prototype.

Reads data/dart/extracted/*_measurement.json and emits
data/dart/viz/csm_waterfall.json — a single JSON file with the
6-stage waterfall (opening / new business / interest / assumption /
amortization / closing) per company, using the CURRENT-period block.

Rules (kept deliberately simple per CLAUDE.md "Simplicity First"):
- Only annual (당기) period — first unique block.
- Stage value = sum of CSM-only leaf columns for the matched row.
- Companies whose measurement extract has no CSM column/row are reported
  with status="no_csm_columns" and an empty waterfall.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "data" / "dart" / "extracted"
OUT_DIR = ROOT / "data" / "dart" / "viz"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Rows that indicate split assumption disclosure (sum CSM across siblings).
ASSUMPTION_SPLIT_PATTERNS = ("가정 변경", "물량차이", "예실차", "투자요소", "손실요소")
# Each stage matches if ANY substring in its pattern list appears in
# the row label (after stripping spaces). Order of patterns matters only
# for tie-breaking; first row that hits a stage wins.
STAGE_PATTERNS: dict[str, list[str]] = {
    "opening": [
        "순부채(자산) (A)",
        "기초 순장부금액",
        "기초 보험계약 순부채",
        "보험계약 순부채(자산)(기초)",
        "기초잔액",
        "기초 보험계약마진",
        "기초",
    ],
    "new_business": [
        "당기 최초 인식",
        "처음 인식한 계약",
        "해당 기간에 처음 인식",
        "신계약 인식",
        "신계약 인식효과",
        "당기 신계약",
        "최초 인식한 계약",
        "최초인식효과",
        "신계약 인식효과",
        "신계약효과",
        "신계약",
        "최초인식계약",
        "최초 인식 계약",
        "신규계약",
        # Samsung Fire §75: parent row empty; substance in sub-row.
        "손실부담계약을 제외한 집합",
        # IBK연금(KR1011): "당기에 최초로 인식한 계약" (particle 최초+로, not the
        # space-separated "최초 인식한" form the other patterns expect).
        "당기에 최초로 인식한 계약",
    ],
    "interest": [
        "순보험금융손익",
        "보험계약의 순 금융손익",
        "보험금융수익(비용)",  # 현대/한화: 보험금융수익(비용)에 따른 ... / 당기손익으로 인식한 ... 보험금융수익(비용)
        "보험금융손익",
        "당기손익 인식분",
        "이자비용",
        "보험금융비용(수익)",
        "보험금융비용",
        "순보험금융비용",
        "순보험금융손익",
    ],
    "assumption": [
        "보험계약마진금액을 조정",
        "보험계약마진 조정 추정치",
        "보험계약마진을 조정하는 추정치의 변동",
        "보험계약마진을 조정하는 추정치 변동",
        # 라이나생명(KR): "을" 조사 없이 "...변동분"으로 끝맺는 변형 (FY2023~FY2025
        # 3개년 raw 확인, validate_csm_waterfall balance_incomplete:assumption).
        "보험계약마진 조정하는 추정치의 변동",
        # 처브라이프생명(KR): "조정" 대신 "변경" 동사를 쓰는 변형 (FY2023~FY2025
        # 3개년 raw 확인, 동일 티켓).
        "보험계약마진을 변경하는 추정치",
        "보험계약마진에 반영된 추정치 변동",
        "보험계약마진 추정의 변경",
        "미래서비스와 관련된 변동",
        "미래 서비스와관련된 변동분",
        "미래서비스 관련 변동",
        "보험계약마진을 조정하는 변동",
        "가정 변경",
        "예실차",
        "추정의 변경",
        "가정변경",
        "가정 변경",
        "물량차이",
        "예실차",
    ],
    "amortization": [
        "서비스를 제공한 보험계약마진",
        "서비스 제공에 따른 보험계약마진 변동",
        "보험계약마진의 당기인식분",
        "서비스 이전을 반영하기 위해 당기손익으로 인식한 보험계약마진",
        "서비스 제공으로 당기손익으로 인식된 보험계약마진",
        "제공된 서비스 관련 당기손익 인식",
        "당기손익으로 인식한 보험계약마진",
        "제공한 서비스에 대해 인식한 보험계약마진",
        # 라이나생명(KR0074) 변형 — CSM 상각 행을 '제공된 서비스의 보험계약마진' /
        # '제공한 서비스 반영 인식한 보험계약마진' 으로 표기 (closing-identity SKIP 원인).
        # '보험취득현금흐름의 상각'(취득현금흐름 상각)은 substring 불일치라 안 걸림.
        "제공된 서비스의 보험계약마진",
        "제공한 서비스 반영 인식한 보험계약마진",
        "보험계약마진 상각액",
        "보험계약마진 상각",
        "보험계약마진상각",
        "보험계약마진의 상각",
        "당기손익으로 인식한 보험계약마진 금액",
        # IBK연금(KR1011): "제공된 서비스에 대해 인식한 보험계약마진" (제공된, not
        # 제공한 — one syllable off the closest existing pattern above).
        "제공된 서비스에 대해 인식한 보험계약마진",
        # 2026.2Q 반기보고서부터 DART 라벨 재구성(다수사 공통, PL_breakdown 측 동일 이슈—
        # scripts/pl_breakdown/companies.py의 _S2_CSM/_MA_CSM_KEYS/CSM_AMORT 참조):
        # "서비스의 이전으로 당기손익에 인식한 보험계약마진" → 아래 문구로 어순 변경.
        "보험계약서비스의 이전 때문에 당기손익으로 인식된 보험수익, 보험계약마진",
    ],
    "closing": [
        "순부채(자산) (K",
        "기말 보험계약마진",
        "기말 순장부금액",
        "기말 보험계약 순부채",
        "보험계약 순부채(자산)(기말)",
        "기말잔액",
        # 롯데손보 분기/반기 차이조정표 labels the closing balance 분기말/반기말
        # (분기말순보험계약부채 …) — must precede the bare "기말" so the net (순부채)
        # row is matched; the 자산인/부채인 sub-rows are already excluded by the caller.
        "당분기말",
        "당반기말",
        "분기말",
        "반기말",
        "기말",
        # Some filings label the closing balance 보고기간말 (end of reporting
        # period) instead of 기말 (e.g. 하나생명 13-4 rollforward).
        "보고기간말",
    ],
}

# Stages where the row label MUST itself mention CSM (보험계약마진).
# Other stages live in the CSM column of a non-CSM-labelled row.
CSM_LABEL_REQUIRED = {"amortization", "assumption"}

# Aggregate / grand-total stub markers that must NOT be accepted as the INTEREST
# (이자 부리) line. In the 2025 label form the 측정요소별 변동내역 note carries a
# grand-total row ("보험서비스결과 및 보험금융손익의 … 총 변동") whose stub merely
# CONTAINS the bare "보험금융손익" substring — its CSM-column value is the whole-note
# net (e.g. 동양생명 2025.4Q −228,193 백만), not the finance line (+108,715 백만). The
# genuine finance line says "보험금융손익 / 당기손익" and never mentions 보험서비스결과
# or a 총 변동 / 총 포괄손익 aggregate. (2024 filings used a lettered A/B/C layout whose
# total rows don't contain 보험금융손익, so this collision only fires in the 2025 form.)
INTEREST_AGG_MARKERS = ("보험서비스결과", "총변동", "총포괄손익")


# --- helpers -------------------------------------------------------------
def parse_num(s) -> float | None:
    if not isinstance(s, str):
        return None
    s = s.strip().replace(",", "").replace(" ", "")
    if s in ("", "-", "0", "—"):
        return 0.0
    neg = False
    if s.startswith("(") and s.endswith(")"):
        neg = True
        s = s[1:-1]
    s = s.replace(",", "")
    try:
        v = float(s)
        return -v if neg else v
    except ValueError:
        return None


# Product-line tokens used to detect product-SEGMENTED measurement tables, where
# several product columns (사망/건강/연금…) sit side by side, each carrying its
# own [미래CF, 위험조정, CSM(×전환방법), (합계)] block. 삼성생명·미래에셋 disclose
# the quarterly rollforward this way (one wide table) and the annual one as
# per-product separate tables — see find_product_segmented_csm_cols / sum logic.
_PRODUCT_TOKENS = (
    "사망보험", "건강보험", "연금보험", "저축보험", "기타보험", "연금저축보험",
    "보장성보험", "저축성보험", "변액보험",
)


def _is_subtotal_label(label) -> bool:
    """True for a 소계/합계/총계/계 column header (a per-group CSM subtotal that
    must NOT be summed alongside its component method columns)."""
    if not isinstance(label, str):
        return False
    s = label.strip().replace(" ", "")
    return s in ("소계", "합계", "총계", "계", "소 계", "합 계")


def _count_product_columns(header_rows: list[list[str]]) -> int:
    """Number of product-name cells in the richest product header row (>=2),
    else 0. Excludes the long 전환일 transition-method labels."""
    best = 0
    for hr in header_rows or []:
        names = [
            c for c in hr
            if isinstance(c, str) and c.strip()
            and any(t in c for t in _PRODUCT_TOKENS)
            and "전환" not in c
        ]
        if len(names) >= 2:
            best = max(best, len(names))
    return best


def _richest_value_slice(rows: list[list[str]], key: str) -> list | None:
    """Among rows whose label contains ``key`` (e.g. '기초'/'기말'), return the
    value slice (row[value_start:]) of the one with the most non-zero numeric
    cells. Picks the 부채 balance row over the all-dash 자산 row."""
    best = None
    best_nz = -1
    for r in rows:
        if not (r and isinstance(r[0], str) and key in r[0]):
            continue
        vs = row_value_start(r)
        data = r[vs:]
        nz = sum(1 for x in data if (parse_num(x) or 0) != 0)
        if nz > best_nz:
            best_nz = nz
            best = data
    return best


def find_product_segmented_csm_cols(
    header_rows: list[list[str]], rows: list[list[str]]
) -> list[int]:
    """CSM data-column indices for a product-SEGMENTED wide table.

    Layout: P products side by side, each a fixed-width group
    ``[미래CF, 위험조정, CSM_method1.., (합계)]``. Returns the CSM-method column
    indices across ALL products (0-based among ``row[value_start:]``), excluding
    each group's trailing 합계 column. Returns [] when the table isn't
    product-segmented or the width doesn't resolve cleanly — so single-aggregate
    companies are never affected.
    """
    P = _count_product_columns(header_rows)
    if P < 2:
        return []
    ref = _richest_value_slice(rows, "기초") or _richest_value_slice(rows, "기말")
    if not ref:
        return []
    N = len(ref)
    if N % P != 0:
        return []
    W = N // P
    if W < 3:  # need at least CF, RA, one CSM column
        return []
    # Detect a per-product 합계 column: group's last cell == sum of the others.
    has_sum = True
    for p in range(P):
        grp = [parse_num(x) or 0 for x in ref[p * W:(p + 1) * W]]
        if len(grp) < W:
            has_sum = False
            break
        body = grp[0] + grp[1] + sum(grp[2:W - 1])
        if abs(grp[-1] - body) > max(1.0, abs(grp[-1]) * 0.002):
            has_sum = False
            break
    cols: list[int] = []
    for p in range(P):
        base = p * W
        end = base + W - 1 if has_sum else base + W
        cols.extend(range(base + 2, end))  # skip CF(0), RA(1); CSM methods follow
    return cols


def header_has_detail_column(header_rows: list[list[str]]) -> bool:
    """True when the measurement table uses 구분 + 상세 (two leading label cols)."""
    hrows = [
        h
        for h in header_rows or []
        if not (len(h) == 1 and isinstance(h[0], str) and "단위" in h[0])
    ]
    if not hrows:
        return False
    top = hrows[0]
    return any(isinstance(c, str) and c.strip() == "상세" for c in top)


def row_value_start(row: list, _header_hint_detail: bool = False) -> int:
    """Index of first measurement cell — first parseable numeric or dash placeholder."""
    if not row or len(row) < 2:
        return 1
    for i in range(1, len(row)):
        v = parse_num(row[i])
        if v is not None:
            return i
        if isinstance(row[i], str) and row[i].strip() in ("-", "—"):
            return i
    return 1


def rollforward_row_stub(row: list) -> str:
    """Concatenate all label cells before numeric measurement slice (handles multi-column stubs)."""
    if not row:
        return ""
    vs = row_value_start(row)
    parts: list[str] = []
    for i in range(vs):
        if i < len(row) and isinstance(row[i], str):
            parts.append(row[i].strip())
    return "".join(parts)


def deduplicate(blocks: list[dict]) -> list[dict]:
    seen: set = set()
    out: list[dict] = []
    for blk in blocks:
        rows_t = tuple(tuple(r) for r in blk.get("rows", []))
        key = (blk.get("caption", ""), rows_t)
        if key in seen:
            continue
        seen.add(key)
        out.append(blk)
    return out


def find_csm_leaf_cols(
    header_rows: list[list[str]], rows: list[list[str]] | None = None
) -> list[int]:
    """Return CSM leaf-column indices (0-based among measurement cells).

    Indices index into ``row[value_start:]`` where ``value_start`` comes from
    :func:`row_value_start`. When ``rows`` is supplied a product-segmented wide
    layout (삼성생명/미래에셋 quarterly: several product lines side by side) is
    detected first.
    """
    if not header_rows:
        return []

    # Product-segmented wide table (highest priority — its ragged multi-level
    # header confuses every positional branch below, leaving these companies'
    # quarterly rollforwards unparsed). Needs the data rows for the 합계 test.
    if rows:
        seg = find_product_segmented_csm_cols(header_rows, rows)
        if seg:
            return seg

    # Strip the optional "(단위 : 백만원)" leading row.
    hrows = [
        h
        for h in header_rows
        if not (len(h) == 1 and isinstance(h[0], str) and "단위" in h[0])
    ]
    if not hrows:
        return []

    top = hrows[0]
    sub = hrows[1] if len(hrows) > 1 else []
    sub2 = hrows[2] if len(hrows) > 2 else []
    detail_col = header_has_detail_column(header_rows)
    extra_label_cols = 1 if detail_col else 0

    # Compressed layout seen in Dongyang Life & 미래에셋 (single-product annual):
    # trailing cols [BEL, RA, CSM_method1.., 소계] under a triplet sub-header +
    # method sub2. The 소계 is a per-product CSM subtotal — include the method
    # columns but DROP the 소계 so CSM isn't double-counted (was [2,3,4,5]).
    if (
        sub
        and sub2
        and len(sub) == 3
        and len(sub2) >= 3
        and isinstance(sub[2], str)
        and "보험계약마진" in sub[2]
    ):
        method_cols = [2 + i for i in range(len(sub2)) if not _is_subtotal_label(sub2[i])]
        return method_cols or [2, 3, 4]

    # Case 1: CSM keyword in top row → one or more leaf columns (Meritz: 3 methods).
    csm_top: list[int] = []
    for i, c in enumerate(top):
        if isinstance(c, str) and "보험계약마진" in c:
            data_idx = i - 1 - extra_label_cols
            if data_idx >= 0:
                csm_top.append(data_idx)
    if csm_top:
        if (
            len(csm_top) == 1
            and sub
            and len(sub) >= 2
            and not any("보험계약마진" in x for x in sub if isinstance(x, str))
        ):
            # Heuristic: sub items belong to CSM iff sub has fewer entries
            # than top's non-label columns (i.e. sub covers only the
            # spanned CSM cell). True for Samsung/Shinhan/Heungkuk Life.
            non_label_top_count = len(top) - 1  # excluding 구분
            if len(sub) <= non_label_top_count + 1:
                start = csm_top[0]
                # Drop a 소계/합계 sub-column (롯데손해: 수정소급/공정가치/이 외/
                # 소 계) so the per-method CSM isn't double-counted with its own
                # subtotal (was [2,3,4,5] → 2× the CSM). Filings whose sub has no
                # subtotal column are returned unchanged.
                method_cols = [
                    start + i
                    for i, lbl in enumerate(sub)
                    if not _is_subtotal_label(lbl)
                ]
                return method_cols or list(range(start, start + len(sub)))
        if sub:
            method_cols = [
                i
                for i, x in enumerate(sub)
                if isinstance(x, str)
                and any(k in x for k in ("공정가치", "그 외", "그밖", "완전소급", "수정소급"))
            ]
            if len(method_cols) >= 2:
                return method_cols
        return csm_top

    # Case 2: CSM keyword in sub-row (Dongyang/Mirae/Pubon style).
    for i, c in enumerate(sub):
        if isinstance(c, str) and "보험계약마진" in c:
            grp = len(sub2) if sub2 else 1
            flat_start = max(0, i * grp)
            if sub2 and grp >= 2:
                # This assumes EVERY sub column (PV/RA/합계 too) repeats `grp`
                # times, true for the Dongyang/Mirae/Pubon layout that
                # motivated this branch. Some filings (하나생명 13-3/14-4) instead
                # carry a narrow leading super-header row (e.g. ['구분',
                # '보험료배분접근법외 보험계약'], only 2 cells) that this function
                # reads as `top`, pushing the REAL [PV, RA, 보험계약마진, 합계]
                # labels down into `sub` — there PV/RA are single-width, so
                # grp-multiplying overshoots the real data (computes cols
                # [6,7,8] when the row only has 6 data cells -> every stage
                # silently empty, no_stage_match). Validate against the actual
                # data width and fall back to the single-width offset
                # (flat_start=i) when the multiplied range doesn't fit but the
                # unmultiplied one does.
                ref = None
                if rows:
                    ref = _richest_value_slice(rows, "기초") or _richest_value_slice(rows, "기말")
                if ref is not None and flat_start + grp > len(ref) and i + grp <= len(ref):
                    # sub2 here is CSM's OWN method breakdown (not repeated
                    # for every top-level column), so a trailing 소계
                    # (subtotal) sub-column must be dropped like the sibling
                    # method_cols builder above does — else it double-counts
                    # (하나생명 14-4 FY2025: sub2 = [수정소급법, 공정가치법,
                    # 이외모든계약, 소계]; 소계's value == the other 3 summed,
                    # verified against the row's own data, so including all 4
                    # doubled every CSM stage and blew up the balance check).
                    method_idx = [k for k in range(grp) if not _is_subtotal_label(sub2[k])]
                    return [i + k for k in method_idx] or list(range(i, i + grp))
                return list(range(flat_start, flat_start + grp))
            return [flat_start]

    # Case 3: sub2 row (Pubon Hyundai style) actually has the CSM label.
    if sub2:
        for i, c in enumerate(sub2):
            if isinstance(c, str) and "보험계약마진" in c:
                return [i]

    # Fallback: look for sub-row containing the standard 3-column CSM
    # naming (수정소급/공정가치/완전소급) even when label is missing.
    if sub and all(isinstance(x, str) for x in sub):
        kw_hits = sum(
            1
            for x in sub
            if any(k in x for k in ("수정소급", "공정가치", "완전소급", "전환이후", "그 외", "그밖"))
        )
        if kw_hits >= 2:
            return list(range(len(sub)))

    # Fallback: deep multi-row headers (2025+ quarterly te-tables) where the
    # leaf column labels (미래현금흐름의현재가치 | 위험조정 | 보험계약마진 | 합계) sit in
    # a lower header row, not in top/sub/sub2. Map 보험계약마진 to a value-column
    # index = how many measurement value-labels precede it (independent of the
    # 구분/empty label column). Scan from the bottom so the leaf row wins.
    _val_kw = ("미래현금흐름", "현재가치", "위험조정", "이행현금흐름", "보험계약마진")
    for hr in reversed(hrows):
        cells = [c if isinstance(c, str) else "" for c in hr]
        csm_pos = next((i for i, c in enumerate(cells) if "보험계약마진" in c), None)
        if csm_pos is None:
            continue
        val_before = sum(
            1 for c in cells[:csm_pos] if any(k in c for k in _val_kw)
        )
        return [val_before]

    return []


def _is_unit_row(r: list) -> bool:
    return len(r) == 1 and isinstance(r[0], str) and "단위" in r[0]


def _is_header_like_row(r: list) -> bool:
    """A row whose cells are all non-numeric text — looks like a header."""
    if not r:
        return False
    for c in r:
        if not isinstance(c, str):
            return False
        s = c.strip().replace(",", "").replace("(", "").replace(")", "")
        s = s.replace("-", "").replace(" ", "")
        if s and s.lstrip("+-").replace(".", "").isdigit():
            return False
    return True


def normalize_block_header(blk: dict) -> dict:
    """Recover header rows that were emitted inside `rows` (no THEAD).

    Some filings (e.g. 흥국화재 2024 §(5) 측정요소 변동내역) ship the
    measurement rollforward without a THEAD, so the extractor stores all
    cells under `rows` and leaves `header` empty. Without a header the
    CSM column locator returns nothing and the block is skipped.

    Heuristic: when `header` is empty, lift an optional unit annotation
    plus up to 3 leading text-only rows into `header` and trim them
    from `rows`.
    """
    header = blk.get("header") or []
    rows = blk.get("rows") or []
    if header or not rows:
        return blk
    hoisted: list = []
    i = 0
    while i < len(rows) and _is_unit_row(rows[i]):
        hoisted.append(rows[i])
        i += 1
    start = i
    while i < min(len(rows), start + 3) and _is_header_like_row(rows[i]):
        hoisted.append(rows[i])
        i += 1
    if not hoisted:
        return blk
    new_blk = dict(blk)
    new_blk["header"] = hoisted
    new_blk["rows"] = rows[i:]
    return new_blk


def _is_ceded_block(blk: dict) -> bool:
    """True iff the block is a *held* reinsurance (출재) rollforward.

    The CSM waterfall must show **direct/원수** business, not ceded
    reinsurance. Several filings put 원수 and 출재 측정요소 변동 tables
    side-by-side under the same section caption (e.g. 메리츠 §14(4),
    삼성생명 §(3)). Caption text is therefore ambiguous; row labels are
    the more reliable signal — ceded blocks open with
    `재보험계약자산/부채` while direct blocks open with `보험계약자산/부채`.
    """
    rows = blk.get("rows") or []
    direct_hits = 0
    ceded_hits = 0
    for r in rows[:6]:
        if not r or not isinstance(r[0], str):
            continue
        lab = r[0]
        if any(t in lab for t in ("재보험계약자산", "재보험계약부채",
                                  "재보험자산", "재보험부채", "순재보험")):
            ceded_hits += 1
        elif any(t in lab for t in ("보험계약자산", "보험계약부채", "순보험계약")):
            direct_hits += 1
    if ceded_hits > direct_hits:
        return True
    if direct_hits > 0:
        return False
    # Row labels inconclusive — fall back to caption.
    cap = blk.get("caption") or ""
    if "보유한 재보험" in cap:
        return True
    if "출재" in cap and "원수" not in cap:
        return True
    # Terse sibling sub-item caption whose ENTIRE subject (after stripping
    # leading numbering and a trailing <당기/전기> tag) is bare "재보험" — e.g.
    # 하나생명 "(2) 재보험 <당기>" paired with a "14-4 ...보험계약..." direct
    # sibling. Row labels can't catch this one: its sub-rows drop the 재
    # prefix (자산/부채, same as the direct block's), and only the combined
    # rollup row carries it, spelled "재보험계약순자산(부채)" — the extra 순
    # breaks every exact-substring token in the ceded list above (looks for
    # "재보험계약자산"/"재보험계약부채", not "...순자산(부채)").
    cap_bare = re.sub(r"^[(（]?\s*\d+[)）]\s*", "", cap.strip())
    cap_bare = re.sub(r"<(당기|전기|당분기|전분기|당반기|전반기)>\s*$", "", cap_bare).strip()
    if cap_bare == "재보험":
        return True
    return False


def _period_affinity(caption: str) -> int:
    """Score how likely a block is the *current* (당기) reporting period."""
    cap = (caption or "").strip()
    if not cap:
        return 0
    score = 0
    if re.search(r"\(전\)\s*기", cap) or re.search(r"제\d+\(전\)", cap):
        score -= 25
    if "<전기>" in cap or cap.endswith("전기") or cap.endswith("전기>"):
        score -= 20
    if re.search(r"\(당\)\s*기", cap) or re.search(r"제\d+\(당\)", cap):
        score += 25
    if "<당기>" in cap or cap.endswith("당기") or cap.endswith("당기>"):
        score += 20
    if "당기와 전기" in cap and (cap.endswith("당기") or "<당기>" in cap):
        score += 15
    # 분기/반기 reports label the comparative columns 당분기/당반기 (current) vs
    # 전분기/전반기 (prior). The 전기-only rules above miss these, so the picker
    # was choosing the prior-period block (e.g. 한화 2025.1Q == 2024.1Q values).
    has_cur_q = "당분기" in cap or "당반기" in cap
    has_prior_q = "전분기" in cap or "전반기" in cap
    if has_prior_q and not has_cur_q:
        score -= 22
    if has_cur_q:
        score += 22
    if "수재(원수 포함)" in cap or "1) 수재" in cap:
        score += 18
    if cap.startswith("2) 출재") or cap.startswith("2)출재"):
        score -= 18
    return score


def _nb_label_rank(label: str) -> int:
    """Prefer explicit 신계약 rows over generic sub-aggregates."""
    if any(k in label for k in ("신계약", "최초 인식", "처음 인식", "당기 최초")):
        return 3
    if "손실부담" in label:
        return 1
    return 2


def _caption_penalty(caption: str) -> int:
    cap = (caption or "").strip()
    if not cap:
        return 0
    score = 0
    if re.match(r"^[ivx]+[\)）]", cap, re.I):
        score -= 8
    if "출재" in cap and "원수" not in cap and "수재" not in cap:
        score -= 25
    if "수재(원수 포함)" in cap or ("원수" in cap and "출재" not in cap):
        score += 8
    return score


def _stage_completeness(blk: dict) -> int:
    return len(extract_stages(blk))


def _new_business_abs(blk: dict) -> float:
    """Non-zero NB CSM in block → prefer over empty 신계약효과 parent rows."""
    try:
        nb = (extract_stages(blk).get("new_business") or {}).get("value_mn_krw") or 0
        return abs(float(nb))
    except (TypeError, ValueError):
        return 0.0


def _disambiguate_basis_period(ranked: list[dict]) -> list[dict]:
    """Promote the current-period separate-basis (별도 당기) block when a filing
    discloses several near-identical 측정요소별 tables.

    생보사 file the measurement rollforward up to four times — 연결/별도 ×
    당기/전기 — under an identical caption ("(5) 당기와 전기 중 … 측정 요소별
    변동내역 … 1) 당기"), so the caption-based period scorer can't separate them
    and may land on the consolidated PRIOR-period copy (한화생명 observed: 연결
    전기 기초 13.59조 instead of 별도 당기 기초 9.24조 — the waterfall then misses
    ~1.1조 because opening/closing are 연결·전기 while the IR-aligned NB override
    is 별도·당기).

    Two signals, both already proven in ``transition_new_business``:
      * prior-period copy → its closing CSM ≈ another candidate's opening CSM;
      * 별도 (separate) basis → smaller opening CSM than 연결.
    Among the non-prior candidates whose opening CSM sits in the main magnitude
    band (≥20% of the largest, which drops small PAA/재보험 side tables), prefer
    the smallest opening. Returns ``ranked`` unchanged when no such duplicate set
    exists, so single-table filings are untouched.
    """
    if len(ranked) < 2:
        return ranked
    info = []
    for b in ranked:
        op, cl = _block_open_close_csm(b)
        info.append((b, op, cl))

    def _is_prior(i: int) -> bool:
        cl = info[i][2]
        if cl is None:
            return False
        for j, (_b, o, _c) in enumerate(info):
            if j == i or o is None:
                continue
            if abs(o) > 1.0 and abs(cl - o) <= max(1.0, abs(o) * 0.001):
                return True
        return False

    current = [t for i, t in enumerate(info) if not _is_prior(i)]
    # Never let a ceded (출재/재보험) block win here. `is_direct` is already
    # the PRIMARY sort key one level up in rank_main_blocks, but this
    # function's own magnitude-band pick (below) compares opening/closing
    # size only and can override that ordering whenever a real direct
    # block's opening happens to sit within 20% of a coexisting reinsurance
    # block's (에이아이에이생명 FY2025 필링, rcept 20260407002100: 재보험
    # 기초 521,402가 원수 기초 1,509,649의 34.5%로 20% 문턱을 넘어 함께
    # 살아남았고, "작은 쪽이 별도" 휴리스틱이 원수/재보험 — 전혀 다른 축 —
    # 쌍에도 그대로 적용돼 재보험 블록이 승격됐다: opening/closing 전부가
    # 재보험 것으로 바뀌며 amortization 스테이지까지 통째로 사라졌다).
    # Direct survivors are preferred whenever any exist among the non-prior
    # candidates; only fall back to the mixed set if none are direct (should
    # not happen for a company with real direct-business disclosure, but
    # avoids ever returning an empty candidate set).
    direct_current = [t for t in current if not _is_ceded_block(t[0])]
    if direct_current:
        current = direct_current
    # Exactly one non-prior survivor = no 별도/연결 ambiguity left to resolve
    # (that needs >=2 same-period candidates), just a plain 당기/전기 pair where
    # continuity already proves which one is current. Promote it outright —
    # don't fall through to the `len(full) < 2` "leave unchanged" branch below,
    # which used to silently keep a PROVEN-prior block as the winner whenever
    # its own score/nb_abs tiebreak happened to sort it first (IBK연금 FY2023
    # filing: only 당기/전기 of one table; 전기's larger nb_abs won the initial
    # sort, and the old code never re-checked prior-ness once `full` came up
    # short). >=2 survivors still go through the existing magnitude logic
    # unchanged (that's the genuine 별도-vs-연결 case, e.g. 한화생명).
    if len(current) == 1:
        best = current[0][0]
        if best is not ranked[0]:
            return [best] + [b for b in ranked if b is not best]
        return ranked
    open_mags = [abs(o) for _b, o, _c in current if o is not None]
    if not open_mags:
        return ranked
    max_open = max(open_mags)
    # Exclude 배당여부(dividend-basis) sub-segment tables — captions numbered
    # "1)유배당"/"2)유배당 외" (e.g. IBK연금; the lead-in "(7) …배당여부에 따른…"
    # sentence is a SEPARATE table whose own caption is just the bare "2) 유배당
    # 외<당기>" stub) — from the swap target. Such a block is BY CONSTRUCTION a
    # subset of the whole book, never a 연결/별도 duplicate, but a large 무배당
    # segment (~95% of a small-유배당 book) can still land inside the 20%-of-max
    # band and wrongly win via "smaller = 별도" (IBK: this picked the 무배당-only
    # table over the true whole-book "(6) 상품별…" one).
    _DIVIDEND_SEGMENT_RE = re.compile(r"^\d\)\s*유배당")
    full = [
        t for t in current
        if t[1] is not None and abs(t[1]) >= max_open * 0.20
        and not _DIVIDEND_SEGMENT_RE.match((t[0].get("caption") or "").strip())
    ]
    if not full:
        return ranked  # nothing survives the main-magnitude band
    if len(full) >= 3:
        # Whole-vs-parts collision: the 20%-of-max band can admit a company's
        # OWN product-segment sub-tables (무배당/변액/유배당 등) alongside the
        # whole-company aggregate when a segment is individually large enough
        # to look like a legitimate 연결/별도 peer. A genuine 연결/별도
        # duplicate never sums to another member of `full`; a product segment
        # does (메트라이프생명 FY2025 필링, rcept 20260403003824: "변액보험계약"
        # alone won via "smallest opening" even though the aggregate's closing
        # 2,608,160,261 ≈ 무배당 1,847,845,220 + 변액 755,779,349 =
        # 2,603,624,569, 0.17% off — the gap is exactly the excluded tiny
        # 유배당 segment). Reuses the same 5% "one block is the total of the
        # rest" tolerance collect_current_product_blocks already applies to
        # this identical signature. When found, the WHOLE wins outright — the
        # others are its own components, never alternate consolidation bases.
        # Requires >=3 members: for exactly 2, "sum of the other 1" degenerates
        # to plain equality, which a genuine 연결/별도 pair satisfies whenever
        # 별도 happens to sit close to 연결 (few/no subsidiaries) — that
        # false-fired on 교보생명보험 FY2024 필링(rcept 20250331004015, 연결
        # 6,458,257 vs 별도 6,438,058, 0.3% apart) and wrongly promoted 연결,
        # reversing the function's own documented 별도-preference below.
        closes = [t[2] for t in full]
        for i, c in enumerate(closes):
            if c is None:
                continue
            others = sum(abs(x) for j, x in enumerate(closes) if j != i and x is not None)
            if others > 0 and abs(abs(c) - others) / others <= 0.05:
                best = full[i][0]
                if best is ranked[0]:
                    return ranked
                return [best] + [b for b in ranked if b is not best]
    if len(full) == 1:
        # Same situation as the len(current)==1 branch above, just discovered
        # one filter later: after dropping proven-prior blocks, exactly one
        # main-magnitude-band survivor remains, so there is no genuine
        # 별도/연결 duplicate pair to disambiguate — promote it outright
        # rather than leaving a block that lost on being prior/tiny (but
        # still won the earlier nb_abs sort) as the winner (메트라이프생명
        # FY2024 필링, rcept 20250402000865: a footnote-captioned PRIOR block
        # — "(주1) 위험경감 선택권…" — outscored the real current-period block
        # on new_business magnitude; _is_prior already proves it prior, but
        # the old code only re-promoted when len(current)==1 and never
        # revisited the pick after the magnitude-band cut narrowed a tiny
        # reinsurance side-table away, leaving exactly this one survivor).
        best = full[0][0]
        if best is ranked[0]:
            return ranked
        return [best] + [b for b in ranked if b is not best]
    best = min(full, key=lambda t: abs(t[1]))[0]
    if best is ranked[0]:
        return ranked
    return [best] + [b for b in ranked if b is not best]


def rank_main_blocks(blocks: list[dict]) -> list[dict]:
    """Return CSM-bearing direct-business blocks, best candidate first.

    Same scoring pick_main_block used to do inline; exposed so callers with
    cross-period context (history builder) can apply a continuity tiebreak.
    """
    candidates: list[tuple[int, float, dict]] = []
    for blk in blocks:
        header = blk.get("header") or []
        rows = blk.get("rows") or []
        # Consolidated filings carry tables about associates/subsidiaries that
        # mention 보험계약마진 in passing (관계기업 지분의 장부금액 조정, 종속기업
        # 요약재무정보) but are NOT the insurer's own CSM rollforward. Exclude
        # them so they can't be mis-picked (e.g. 미래에셋 2025.4Q equity table).
        cap = blk.get("caption") or ""
        if any(k in cap for k in ("관계기업", "종속기업", "요약재무정보", "지분의 장부금액")):
            continue
        has_csm_label = any(
            isinstance(r[i], str) and "보험계약마진" in r[i]
            for r in rows
            if r
            for i in range(min(3, len(r)))
        )
        has_csm_col = any(
            "보험계약마진" in c
            for hdr in header
            for c in hdr
            if isinstance(c, str)
        )
        if not (has_csm_label and has_csm_col):
            continue
        # prefer the block with the most matched stages
        csm_cols = find_csm_leaf_cols(header, rows)
        if not csm_cols:
            continue
        score = sum_stage_hits(rows)
        if any(isinstance(r[0], str) and "기초 보험계약마진" in r[0] for r in rows if r):
            score += 8
        # Strong penalty so a ceded block only wins when no direct block
        # has any CSM stages at all.
        if _is_ceded_block(blk):
            score -= 10
        period = _period_affinity(blk.get("caption") or "")
        completeness = _stage_completeness(blk) + _caption_penalty(blk.get("caption") or "")
        # The waterfall must show direct (원수) business. A direct block always
        # ranks above a ceded one, so a <당기>-tagged ceded table can't win
        # over a direct table (e.g. 처브라이프 §(3) 보험계약부채 vs 재보험계약부채).
        is_direct = 0 if _is_ceded_block(blk) else 1
        candidates.append((is_direct, period, completeness, score, _new_business_abs(blk), blk))
    candidates.sort(key=lambda t: (t[0], t[1], t[2], t[3], t[4]), reverse=True)
    return _disambiguate_basis_period([c[5] for c in candidates])


def pick_main_block(blocks: list[dict]) -> dict | None:
    """Pick the most informative CSM-bearing direct-business block."""
    ranked = rank_main_blocks(blocks)
    return ranked[0] if ranked else None


def sum_stage_hits(rows: list[list[str]]) -> int:
    hits = 0
    for _label, patterns in STAGE_PATTERNS.items():
        for row in rows:
            if not row or not isinstance(row[0], str):
                continue
            stub = rollforward_row_stub(row)
            if any(p in stub for p in patterns):
                hits += 1
                break
    return hits


def filter_current_period_rows(rows: list[list[str]]) -> list[list[str]]:
    """When a table stacks 당기 then 전기, keep only the 당기 slice."""
    start: int | None = None
    end = len(rows)
    for i, r in enumerate(rows):
        if not r or not isinstance(r[0], str):
            continue
        tag = r[0].strip()
        if tag == "당기" and start is None:
            start = i
        elif tag == "전기" and start is not None:
            end = i
            break
    if start is None:
        return rows
    return rows[start:end]


def extract_stages(blk: dict) -> dict:
    header = blk.get("header") or []
    rows = filter_current_period_rows(blk.get("rows") or [])
    csm_cols = find_csm_leaf_cols(header, rows)
    out: dict[str, dict] = {}

    for stage, patterns in STAGE_PATTERNS.items():
        if stage == "assumption":
            split_vals: list[float] = []
            split_labels: list[str] = []
            for row in rows:
                if not row or not isinstance(row[0], str):
                    continue
                stub_roll = rollforward_row_stub(row)
                if not any(p in stub_roll for p in ASSUMPTION_SPLIT_PATTERNS):
                    continue
                vs = row_value_start(row)
                data_cells = row[vs:]
                vals = []
                for idx in csm_cols:
                    if idx < 0 or idx >= len(data_cells):
                        continue
                    v = parse_num(data_cells[idx])
                    if v is not None:
                        vals.append(v)
                if not vals:
                    continue
                total = sum(vals)
                if abs(total) < 1e-6:
                    continue
                label_parts = [
                    str(row[i]).strip()
                    for i in range(min(vs, len(row)))
                    if isinstance(row[i], str)
                ]
                split_labels.append(" / ".join(label_parts) if label_parts else row[0].strip())
                split_vals.append(total)
            if split_vals:
                out[stage] = {
                    "label": " + ".join(split_labels[:3]) + (" …" if len(split_labels) > 3 else ""),
                    "value_mn_krw": sum(split_vals),
                }
                continue

        candidates: list[tuple[float, int, str, float]] = []
        for row in rows:
            if not row or not isinstance(row[0], str):
                continue
            stub_roll = rollforward_row_stub(row)
            if not any(p in stub_roll for p in patterns):
                continue
            if stage in CSM_LABEL_REQUIRED and "보험계약마진" not in stub_roll:
                continue
            # Skip a grand-total / aggregate row that only CONTAINS "보험금융손익"
            # as part of a whole-note total (2025 label form) — prefer the genuine
            # finance line over the aggregate (동양생명 2025.4Q +108,715 not −228,193).
            if stage == "interest" and any(
                m in stub_roll.replace(" ", "") for m in INTEREST_AGG_MARKERS
            ):
                continue
            vs = row_value_start(row)
            data_cells = row[vs:]
            vals = []
            for idx in csm_cols:
                if idx < 0 or idx >= len(data_cells):
                    continue
                v = parse_num(data_cells[idx])
                if v is not None:
                    vals.append(v)
            if not vals:
                continue
            total = sum(vals)
            label_parts = [
                str(row[i]).strip()
                for i in range(min(vs, len(row)))
                if isinstance(row[i], str)
            ]
            picked_label = " / ".join(label_parts) if label_parts else row[0].strip()
            candidates.append((abs(total), _nb_label_rank(picked_label), picked_label, total))
        if not candidates:
            continue
        # Non-zero values beat empty parent rows (e.g. Samsung Fire §75 신계약효과).
        candidates.sort(
            key=lambda t: (abs(t[3]) > 1e-6, t[1], t[0]),
            reverse=True,
        )
        _, _, label, signed_total = candidates[0]
        out[stage] = {"label": label, "value_mn_krw": signed_total}

    # Rowspan-split balance blocks (e.g. 하나생명 13-4): the 기초/당기말 marker
    # only tags the 자산 sub-row; the net CSM lives in the next 보험계약순부채
    # row. Usually the 자산 sub-row is all zeros (resolves to ~0, the original
    # trigger below), but it can be genuinely non-zero too (하나생명 FY2025
    # 필링, rcept 20260325000201: 당기말 자산 sub-row = -19,577,929, picked as
    # "closing" via the bare "기말" fallback since only THIS sub-row's stub
    # carries the "당기말" tag — 부채/보험계약순부채 siblings don't repeat it —
    # while the true net 보험계약순부채 = 726,895,688 사라짐, residual 62%).
    # Also patch whenever the current pick's own label is that 자산 sub-row
    # specifically (last " / "-joined segment == "자산"), regardless of its
    # value, so companies whose opening/closing already resolve correctly via
    # a DIFFERENT label (기말잔액 등) are never touched.
    for stage, region in (("opening", rows[:6]), ("closing", rows[-6:])):
        cur = out.get(stage)
        cur_is_asset_subrow = False
        if cur is not None:
            label_parts = (cur.get("label") or "").split(" / ")
            cur_is_asset_subrow = label_parts[-1].strip() == "자산"
        if (
            cur is not None
            and abs(cur.get("value_mn_krw", 0.0)) > 1e-6
            and not cur_is_asset_subrow
        ):
            continue
        for row in region:
            if not row or not isinstance(row[0], str):
                continue
            if "순부채" not in row[0] and "순자산" not in row[0]:
                continue
            vs = row_value_start(row)
            data_cells = row[vs:]
            vals = [
                parse_num(data_cells[i])
                for i in csm_cols
                if 0 <= i < len(data_cells)
            ]
            vals = [v for v in vals if v is not None]
            if vals and abs(sum(vals)) > 1e-6:
                out[stage] = {"label": row[0].strip(), "value_mn_krw": sum(vals)}
                break

    # Supplementary additive CSM rollforward lines: some filings disclose a
    # component that never matches ANY of the 6 stage patterns above because
    # it sits as its OWN top-level rollforward line — not nested under a
    # matched parent, and not itself resembling any stage's usual wording —
    # so it would otherwise silently vanish from the balance identity. Each
    # entry is verified per-company via the row's own arithmetic (PV+RA+
    # CSM(+ext)=합계) and/or the balance-identity residual it exactly closes,
    # and gets SUMMED INTO whichever stage already resolved above — never
    # REPLACING it, unlike the main pattern loop, because these are always
    # siblings of the main pick, not alternates for it.
    _SUPPLEMENTARY_ADDITIVE: tuple[tuple[str, tuple[str, ...]], ...] = (
        # 라이나생명(FY2023 필링, rcept 20240409003674): 최초 IFRS17 연차 특유의
        # "계약의 경계" 재판정 catch-up. "미래서비스 관련 변동" 그룹(신계약/
        # 조정추정치/손실부담)과는 무관한 별개 최상위 라인("기타" 부모행의
        # 유일한 자식) — 잔차 3,439,401,606천원이 이 행 하나로 정확히 0에
        # 닫힘(항등식 검증 완료). 46개 필링 전수조회 결과 이 라벨은 이 회사
        # 이 연도에만 등장 — 다른 회사에 흡수될 위험 없음.
        ("assumption", ("계약의 경계 변경 효과",)),
        # 메트라이프생명(3개년 전부): "7. 환율변동효과 등"은 "6. 보험계약의
        # 순 금융손익" 바로 다음 줄의 자체 최상위 라인 — row5(보험서비스결과)
        # +row6(순금융손익)+row7(이 행)=row8(당기손익 및 기타포괄손익의 총
        # 변동) 항등식으로 검증(3개년 전부 확인). 트레일링 "등"까지 정확히
        # 일치시켜야 한다 — 케이비라이프는 같은 접두어로 시작하는 "환율변동
        # 효과 외"/"환율변동효과"가 "보험금융손익(PL)" 부모 행의 CHILD라
        # (123,071=102,487+20,584 항등식으로 확인) "환율변동효과"만 부분
        # 일치시키면 부모+자식 이중계상으로 이전엔 통과하던 필링을 깨뜨렸다
        # (실측 회귀: residual 0→102,487). 삼성생명도 정확히 "환율변동효과
        # 등" 라벨을 쓰지만 값이 0에 가까워(수백만원대) 흡수돼도 무해.
        ("interest", ("환율변동효과 등",)),
    )
    for target_stage, tokens in _SUPPLEMENTARY_ADDITIVE:
        for row in rows:
            if not row or not isinstance(row[0], str):
                continue
            stub_roll = rollforward_row_stub(row)
            if not any(t in stub_roll for t in tokens):
                continue
            vs = row_value_start(row)
            data_cells = row[vs:]
            vals = [parse_num(data_cells[i]) for i in csm_cols if 0 <= i < len(data_cells)]
            vals = [v for v in vals if v is not None]
            if not vals:
                continue
            add_total = sum(vals)
            if abs(add_total) < 1e-6:
                continue
            if target_stage in out:
                out[target_stage]["value_mn_krw"] += add_total
                out[target_stage]["label"] = out[target_stage]["label"] + " + " + row[0].strip()
            else:
                out[target_stage] = {"label": row[0].strip(), "value_mn_krw": add_total}
            break  # one matching row per filing — avoid double-adding repeats
    return out


def detect_unit_scale(blocks: list[dict]) -> float:
    """Return divisor to normalize values to million KRW.

    Korean filings usually annotate "(단위 : 백만원)" — million KRW.
    Some companies (Hanwha Sonhae, Hyundai Marine observed) keep raw
    KRW, which makes numbers ~1e6 larger. Heuristic: scan captions and
    header rows for the unit marker.
    """
    for blk in blocks:
        for hrow in blk.get("header") or []:
            for cell in hrow:
                if not isinstance(cell, str):
                    continue
                if "단위" in cell and "백만" in cell:
                    return 1.0
                if "단위" in cell and ("원" in cell) and "백만" not in cell and "천" not in cell:
                    return 1_000_000.0
        cap = blk.get("caption") or ""
        if "백만원" in cap:
            return 1.0
    return 1.0  # default assume already million KRW


def _block_open_close_csm(blk: dict) -> tuple[float | None, float | None]:
    st = extract_stages(blk)
    return (
        (st.get("opening") or {}).get("value_mn_krw"),
        (st.get("closing") or {}).get("value_mn_krw"),
    )


def collect_current_product_blocks(blocks: list[dict]) -> list[dict]:
    """Current-period direct product blocks to SUM, for per-product-split annual
    disclosures (삼성생명·미래에셋 file one rollforward table *per product line*).

    Returns [] for ordinary single-aggregate filings so their behaviour is
    untouched. Walks distinct direct CSM blocks in document order and keeps a
    'cycle', stopping BEFORE a block whose closing CSM ≈ the first block's
    opening CSM (the prior-period version of product #1). Gated hard:
    every collected block must be a NARROW single-product table (no side-by-side
    product columns) sharing the same CSM-column layout, and no block may equal
    the sum of the others (that would mean a real total already exists).
    """
    direct: list[tuple[dict, float | None, float | None, tuple]] = []
    seen: set = set()
    for blk in blocks:
        rows = blk.get("rows") or []
        header = blk.get("header") or []
        if _is_ceded_block(blk):
            continue
        cap = blk.get("caption") or ""
        if any(k in cap for k in ("관계기업", "종속기업", "요약재무정보", "지분의 장부금액")):
            continue
        # Skip prior-period (전분기/전반기/전기) sub-tables — they are the SAME
        # aggregate one period back, not a distinct product line, and would inflate
        # the sum. Match only the period MARKER (sub-caption "2) 전…" or a caption
        # ending in the prior-period word), not the descriptive "당분기와 전분기 중…"
        # that headlines a both-periods section (삼성생명's per-product caption).
        cap_s = cap.strip()
        if (
            cap_s.startswith(("2) 전", "2)전", "(전"))
            or cap_s.endswith(("전분기", "전반기", "전기", "전기>"))
            or "<전기>" in cap_s
        ):
            continue
        if _count_product_columns(header) >= 2:
            return []  # already a wide multi-product table — single pick sums it
        leaf = find_csm_leaf_cols(header, rows)
        if not leaf:
            continue
        op, cl = _block_open_close_csm(blk)
        if op is None and cl is None:
            continue
        key = tuple(tuple(r) for r in rows)
        if key in seen:
            continue
        seen.add(key)
        direct.append((blk, op, cl, tuple(leaf)))
    if len(direct) < 2:
        return []
    # A per-product split shows up as the dominant CSM-column layout among the
    # narrow blocks. Group by layout and keep the most common (≥2); blocks with a
    # stray layout (a misparsed neighbouring table) are skipped, not fatal.
    from collections import Counter
    layout_counts = Counter(d[3] for d in direct)
    layout0, n0 = layout_counts.most_common(1)[0]
    if n0 < 2:
        return []
    group = [d for d in direct if d[3] == layout0]  # preserves document order
    first_open, first_close = group[0][1], group[0][2]
    collected = [group[0]]

    def _near(a: float | None, b: float | None, tol: float = 0.05) -> bool:
        return (
            a is not None and b is not None and abs(a) > 1.0
            and abs(a - b) <= max(1.0, abs(a) * tol)
        )

    for blk, op, cl, _leaf in group[1:]:
        # Stop at the next *cycle*, i.e. when this block is product #1 again:
        #  - 전기 version: its closing == product #1's opening (balance carried fwd);
        #  - 연결→별도 duplicate: it matches product #1 in BOTH opening and closing.
        # Matching only the closing is too weak — a distinct sibling product can
        # share a similar closing (미래에셋 사망 979,617 vs 건강 951,273, 2.9%) while
        # differing in opening (969,133 vs 883,687, 8.8%); requiring BOTH avoids
        # collapsing real products, yet still catches 별도 restarts (삼성 ~2% on both).
        if _near(cl, first_open, tol=0.01):
            break  # prior-period (전기) version of product #1 (exact balance carry)
        if _near(op, first_open) and _near(cl, first_close):
            break  # 별도 duplicate set restarting at product #1 (~2% on both)
        collected.append((blk, op, cl, _leaf))
    # A genuine per-product split has ≥3 product lines (사망/건강/연금/…). A pair
    # of blocks is almost always 당기+전기 or 원수+출재 of ONE series, which must
    # not be summed — so require at least three.
    if len(collected) < 3:
        return []
    opens = [o for _b, o, _c, _l in collected if o is not None]
    closes = [c for _b, _o, c, _l in collected if c is not None]
    # Genuine product lines differ markedly in size (e.g. 사망 5조 vs 연금 1조);
    # near-equal closings mean these are 연결/별도/period variants of ONE aggregate
    # (e.g. 교보 5.1/5.0/4.9조), which must not be summed.
    mags = sorted(abs(c) for c in closes)
    if mags and mags[-1] > 0 and (mags[-1] - mags[0]) / mags[-1] < 0.5:
        return []
    # Period-continuity guard: if any block's opening exactly matches another's
    # closing, they are consecutive periods of one series (전기→당기), not
    # distinct products — reject (e.g. a 당기+전기+전전기 triple).
    for o in opens:
        for c in closes:
            if abs(o) > 1.0 and abs(o - c) <= max(1.0, abs(o) * 0.001):
                return []
    # Drop an aggregate 총계 block presented ALONGSIDE its own product breakdown:
    # if one collected block's |NB| ≈ the sum of all OTHER blocks' |NB| (tight 2%),
    # it is the company total and summing it with the components double-counts
    # (미래에셋 FY2025 _00760: a coarse 사망/기타 split whose 기타 == the fine 상품별
    # total → 2× NB). Drop the aggregate; keep the components.
    nbs = [_new_business_abs(b) for b, _o, _c, _l in collected]
    for i, nbi in enumerate(nbs):
        others_nb = sum(nbs[:i] + nbs[i + 1:])
        if nbi > 1.0 and others_nb > 1.0 and abs(nbi - others_nb) / others_nb <= 0.02:
            collected = collected[:i] + collected[i + 1:]
            closes = [c for _b, _o, c, _l in collected if c is not None]
            break
    abs_closes = [abs(c) for c in closes]
    for i, c in enumerate(abs_closes):
        others = sum(abs_closes[:i] + abs_closes[i + 1:])
        if others > 0 and abs(c - others) / others <= 0.05:
            return []  # one block is the total of the rest — not a product split
    return [b for b, _o, _c, _l in collected]


def extract_stages_summed(blocks: list[dict]) -> dict:
    """Sum each CSM stage across per-product blocks (label kept from the first)."""
    out: dict[str, dict] = {}
    for blk in blocks:
        for stage, v in extract_stages(blk).items():
            if stage not in out:
                out[stage] = {"label": v.get("label"), "value_mn_krw": 0.0}
            out[stage]["value_mn_krw"] += v.get("value_mn_krw", 0.0)
    return out


# --- Priority NB CSM path: 전환방법별 보험계약마진 변동 single-cell ----------
# Some life insurers (한화생명) additionally disclose a "(10) 보험수익 및
# 전환방법별 보험계약마진 변동 내역" table whose "신계약 인식효과 / 합계" cell
# is the cleanest source for new-business CSM — it matches the company's own IR
# (한화 FY24 합계 = 21,231억) whereas the 측정요소별 변동 table's
# "최초 인식한 계약의 효과" CSM column reports a different (larger) figure.
# This path takes priority over the csm_leaf_cols-based new_business when such a
# table exists; otherwise the regular extraction is kept (Meritz/Lotte 손보 do
# NOT file this table form — they fall back to the leaf-col path).
_TRANSITION_CAPTION_TOKENS = ("전환방법별", "전환 방법별")
_TRANSITION_NB_ROW_TOKENS = (
    "신계약 인식효과",
    "신계약인식효과",
    "처음 인식한 계약",
    "당기 처음 인식",
    "당기 최초 인식",
)


def _transition_table_blocks(blocks: list[dict]) -> list[dict]:
    """Blocks whose caption marks a *direct-business* 전환방법별 보험계약마진
    변동 table and which carry a 신계약/처음 인식 row plus a 합계 column.

    Excludes the sibling 전환방법별 재보험계약마진 (ceded reinsurance) table that
    quarterly filings disclose right after the direct one — its 신계약 효과 is the
    much smaller ceded figure, not the new-business CSM the waterfall needs."""
    out: list[dict] = []
    for blk in blocks:
        cap = blk.get("caption") or ""
        if "재보험" in cap:  # ceded reinsurance transition table — skip
            continue
        if not (any(t in cap for t in _TRANSITION_CAPTION_TOKENS)
                and "보험계약마진" in cap):
            continue
        rows = blk.get("rows") or []
        if any(
            r and isinstance(r[0], str)
            and any(t in r[0] for t in _TRANSITION_NB_ROW_TOKENS)
            for r in rows
        ):
            out.append(blk)
    return out


def _transition_row_value(rows: list[list[str]], tokens) -> float | None:
    """Sum the trailing 합계 column of the row(s) matching ``tokens``.

    The 전환방법별 table lays out transition-method columns
    (수정소급법/공정가치법/이외 모든계약) followed by a 합계 column. The
    company files the 신계약 효과 only under one method, so summing the method
    columns or reading the 합계 column gives the same total — we read 합계
    (the last cell) directly, which is the IR-reconciling figure."""
    for r in rows:
        if not (r and isinstance(r[0], str)
                and any(t in r[0] for t in tokens)):
            continue
        v = parse_num(r[-1])
        if v is not None:
            return v
    return None


def transition_new_business(blocks: list[dict]) -> dict | None:
    """Return {'label','value_mn_krw'} for new-business CSM from the
    전환방법별 보험계약마진 변동 table, or None when absent.

    When both 연결 and 별도 (plus their 전기 copies) tables are present, prefer
    the *current-period separate-basis* table: a 전기 copy carries its closing
    into another block's opening, and 별도 balances are smaller than 연결 — the
    IR series is disclosed on the 별도 basis. We therefore drop 전기 copies
    (closing ≈ some block's opening) and pick the survivor with the smallest
    기초 보험계약마진."""
    cands = _transition_table_blocks(blocks)
    if not cands:
        return None

    def _opening(blk) -> float | None:
        for r in blk.get("rows") or []:
            if r and isinstance(r[0], str) and "기초 보험계약마진" in r[0]:
                return parse_num(r[-1])
        return None

    def _closing(blk) -> float | None:
        for r in blk.get("rows") or []:
            if r and isinstance(r[0], str) and "기말 보험계약마진" in r[0]:
                return parse_num(r[-1])
        return None

    enriched = []
    for blk in cands:
        nb = _transition_row_value(blk.get("rows") or [], _TRANSITION_NB_ROW_TOKENS)
        if nb is None:
            continue
        enriched.append((blk, _opening(blk), _closing(blk), nb))
    if not enriched:
        return None

    def _is_prior_period(idx) -> bool:
        # A 전기 copy's closing balance carries forward into the *current*-period
        # opening of ANOTHER block in the same table-pair. Compare against other
        # blocks' openings only — never the block's own opening, which would
        # falsely flag a single quarterly table whose closing ≈ its opening.
        closing = enriched[idx][2]
        if closing is None:
            return False
        for j, (_b, o, _c, _n) in enumerate(enriched):
            if j == idx or o is None:
                continue
            if abs(o) > 1.0 and abs(closing - o) <= max(1.0, abs(o) * 0.001):
                return True
        return False

    current = [
        e for i, e in enumerate(enriched) if not _is_prior_period(i)
    ] or enriched

    # Drop tiny product-SEGMENT tables: some insurers file a 전환방법별 table per
    # product line plus a company-total one (e.g. KB라이프 — total 기초 ~3.1조 vs a
    # 348억 segment). A segment whose 기초 보험계약마진 is < 20% of the largest is
    # not the company total and must not win the smallest-opening pick below.
    open_mags = [abs(e[1]) for e in current if e[1] is not None]
    if open_mags:
        max_open = max(open_mags)
        full = [
            e for e in current
            if e[1] is None or abs(e[1]) >= max_open * 0.20
        ]
        if full:
            current = full

    # Among the full-company current-period tables, the 별도 (separate-basis) copy
    # has the smaller 기초 보험계약마진 and reconciles with the IR series (한화: 별도
    # 9.2조 vs 연결 13.3조). Pick the smallest remaining 기초.
    current.sort(key=lambda e: (e[1] if e[1] is not None else float("inf")))
    blk, _op, _cl, nb = current[0]
    label = next(
        (r[0].strip() for r in (blk.get("rows") or [])
         if r and isinstance(r[0], str)
         and any(t in r[0] for t in _TRANSITION_NB_ROW_TOKENS)),
        "신계약 인식효과",
    )
    return {"label": label, "value_mn_krw": nb, "source": "transition_table"}


# --- NB CSM path 2: 잔여보장(LRC) 구성요소별 변동 신계약 single-cell -----------
# Some 손보 filings (롯데손해 FY2025) over-state new-business CSM in the
# 측정요소별 변동 table (485,252); their IR-aligned figure sits in the
# *current-period direct-business* 잔여보장 구성요소별 변동내역 (LRC component
# rollforward) — the 신계약/최초인식계약 row's 보험계약마진 cell (롯데 FY25 =
# 412,168 = IR). Lower priority than transition_new_business so 전환방법별 filings
# (생보) are untouched; only used when no 전환방법별 table exists.
_RECON_NB_ROW_TOKENS = ("신계약", "최초인식계약", "최초 인식 계약")


def reconciliation_new_business(blocks: list[dict]) -> dict | None:
    """NB CSM from the current-period direct 잔여보장 구성요소별 변동 table.

    Gated tight: caption must carry both 잔여보장 and 구성요소, be 원수 (direct,
    not 재보험/출재/수재), and not be an explicit 전기 copy. Among matches, the
    whole-LOB total is the largest |CSM| (drops tiny per-segment tables)."""
    cands: list[tuple[str, float]] = []
    for blk in blocks:
        capf = (blk.get("caption") or "").replace(" ", "")
        if "잔여보장" not in capf or "구성요소" not in capf:
            continue
        if any(t in capf for t in ("재보험", "출재", "수재")):
            continue
        if "원수" not in capf:
            continue
        if "(전)" in capf or "전기>" in capf:  # explicit prior-period copy
            continue
        header = blk.get("header") or []
        rows = filter_current_period_rows(blk.get("rows") or [])
        csm_cols = find_csm_leaf_cols(header, rows)
        if not csm_cols:
            continue
        for r in rows:
            if not (r and isinstance(r[0], str)):
                continue
            rl = r[0].replace(" ", "")
            if not any(t.replace(" ", "") in rl for t in _RECON_NB_ROW_TOKENS):
                continue
            vs = row_value_start(r)
            data = r[vs:]
            vals = [parse_num(data[i]) for i in csm_cols if 0 <= i < len(data)]
            vals = [v for v in vals if v is not None]
            if vals:
                cands.append((r[0].strip(), sum(vals)))
                break
    if not cands:
        return None
    label, val = max(cands, key=lambda t: abs(t[1]))
    return {"label": label, "value_mn_krw": val, "source": "reconciliation_lrc"}


def build_for_file(path: Path) -> dict:
    raw = json.loads(path.read_text(encoding="utf-8"))
    blocks = [normalize_block_header(b) for b in deduplicate(raw)]
    # _measurement.json stem ends with "_measurement"; strip it.
    stem = path.stem
    if stem.endswith("_measurement"):
        stem = stem[: -len("_measurement")]
    parts = stem.split("_")
    company = parts[0]
    rcept = parts[1] if len(parts) >= 2 else ""

    product_blocks = collect_current_product_blocks(blocks)
    if product_blocks:
        # Per-product-split filing: sum CSM stages across product lines.
        main = product_blocks[0]
        stages = extract_stages_summed(product_blocks)
    else:
        main = pick_main_block(blocks)
        if main is None:
            return {
                "company": company,
                "rcept_no": rcept,
                "status": "no_csm_columns",
                "stages": {},
                "header": blocks[0].get("header") if blocks else None,
                "caption": blocks[0].get("caption") if blocks else None,
            }
        stages = extract_stages(main)
    # Priority new-business path: the 전환방법별 보험계약마진 변동 single-cell
    # (신계약 인식효과 / 합계) overrides the leaf-col new_business when present.
    nb_override = transition_new_business(blocks)
    if nb_override is None:
        nb_override = reconciliation_new_business(blocks)
    if nb_override is not None:
        stages["new_business"] = nb_override
    csm_cols = find_csm_leaf_cols(main.get("header", []), main.get("rows", []))
    unit_div = detect_unit_scale(blocks)
    # Heuristic fallback: when caption/header has no unit annotation we infer
    # from magnitude. A Korean insurer's CSM realistically sits between ~0.05
    # trillion KRW and ~30 trillion KRW. Expressed in different units:
    #   million KRW: 5e4   .. 3e7
    #   thousand   : 5e7   .. 3e10
    #   raw KRW    : 5e10  .. 3e13
    if unit_div == 1.0 and stages:
        # Use the largest-magnitude stage, not opening: some filings split the
        # 기초 row into 자산/부채 sub-rows (rowspan), so opening can match a
        # zero placeholder and miss the thousand-KRW scale (e.g. 하나생명).
        mag = max((abs(s.get("value_mn_krw", 0.0)) for s in stages.values()), default=0.0)
        if mag > 1e10:  # raw KRW
            unit_div = 1_000_000.0
        elif mag > 1e8:  # thousand KRW
            unit_div = 1_000.0
    if unit_div != 1.0:
        for s in stages.values():
            s["value_mn_krw"] = s["value_mn_krw"] / unit_div
    completeness = len(stages) / 6.0
    return {
        "company": company,
        "rcept_no": rcept,
        "status": "ok" if completeness >= 5 / 6 else ("partial" if stages else "no_stage_match"),
        "completeness": round(completeness, 2),
        "caption": main.get("caption"),
        "header": main.get("header"),
        "csm_leaf_cols": csm_cols,
        "unit_divisor_to_mn": unit_div,
        "stages": stages,
    }


def main() -> None:
    # Use the unfiltered _measurement.json (not _measurement_mvp.json).
    # The MVP filter strips some direct-business measurement-rollforward
    # blocks for 손보사 whose §14(4) caption lives apart from the table
    # (NH농협손해, 롯데손해, 메리츠화재, 삼성화재, 흥국화재). The
    # pick_main_block scorer here already prefers direct/원수 over ceded.
    files = sorted(SRC_DIR.glob("*_measurement.json"))
    # The `_batch_measurement_summary.json` housekeeping file would also
    # match the broader glob ifrs17_batch_measurement.py ever drops the
    # underscore prefix; defensively exclude any file starting with `_`.
    files = [f for f in files if not f.stem.startswith("_")]
    results = []
    for f in files:
        try:
            results.append(build_for_file(f))
        except Exception as e:  # noqa: BLE001
            results.append(
                {"company": f.stem.split("_")[0], "status": "error", "error": str(e)}
            )

    payload = {
        "unit": "million KRW",
        "period": "annual (fiscal 2024 reporting)",
        "source": "DART business reports (rcept_no in each entry)",
        "stage_order": ["opening", "new_business", "interest", "assumption", "amortization", "closing"],
        "stage_labels_en": {
            "opening": "Opening net",
            "new_business": "New business",
            "interest": "Interest accretion",
            "assumption": "Assumption / experience",
            "amortization": "CSM amortization",
            "closing": "Closing net",
        },
        "stage_labels_ko": {
            "opening": "기초",
            "new_business": "신계약",
            "interest": "이자부리",
            "assumption": "가정·경험 조정",
            "amortization": "상각",
            "closing": "기말",
        },
        "companies": results,
    }
    out = OUT_DIR / "csm_waterfall.json"
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {out}")
    # summary
    ok = sum(1 for r in results if r.get("status") == "ok")
    partial = sum(1 for r in results if r.get("status") == "partial")
    print(f"companies: total={len(results)} ok={ok} partial={partial}")
    for r in results:
        if r.get("status") != "ok":
            print(f"  - {r.get('company')}: {r.get('status')} stages={list(r.get('stages',{}).keys())}")


if __name__ == "__main__":
    main()
