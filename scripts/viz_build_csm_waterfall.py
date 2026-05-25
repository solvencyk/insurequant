"""Build CSM Movement Waterfall data for the HTML prototype.

Reads data/ifrs17/extracted/*_measurement.json and emits
data/ifrs17/viz/csm_waterfall.json — a single JSON file with the
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
SRC_DIR = ROOT / "data" / "ifrs17" / "extracted"
OUT_DIR = ROOT / "data" / "ifrs17" / "viz"
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
    ],
    "interest": [
        "순보험금융손익",
        "보험계약의 순 금융손익",
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
        "보험계약마진 상각액",
        "보험계약마진 상각",
        "보험계약마진상각",
        "보험계약마진의 상각",
        "당기손익으로 인식한 보험계약마진 금액",
    ],
    "closing": [
        "순부채(자산) (K",
        "기말 보험계약마진",
        "기말 순장부금액",
        "기말 보험계약 순부채",
        "보험계약 순부채(자산)(기말)",
        "기말잔액",
        "기말",
    ],
}

# Stages where the row label MUST itself mention CSM (보험계약마진).
# Other stages live in the CSM column of a non-CSM-labelled row.
CSM_LABEL_REQUIRED = {"amortization", "assumption"}


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


def find_csm_leaf_cols(header_rows: list[list[str]]) -> list[int]:
    """Return CSM leaf-column indices (0-based among measurement cells).

    Indices index into ``row[value_start:]`` where ``value_start`` comes from
    :func:`row_value_start`.
    """
    if not header_rows:
        return []

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

    # Compressed layout seen in Dongyang Life & Mirae: trailing 7 cols
    # (implicit BEL, RA, CSM × 4 방법, 합계) under a triplet sub-header + 4 방법.
    if (
        sub
        and sub2
        and len(sub) == 3
        and len(sub2) == 4
        and isinstance(sub[2], str)
        and "보험계약마진" in sub[2]
    ):
        return [2, 3, 4, 5]

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
                return list(range(start, start + len(sub)))
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


def pick_main_block(blocks: list[dict]) -> dict | None:
    """Pick the most informative CSM-bearing direct-business block."""
    candidates: list[tuple[int, float, dict]] = []
    for blk in blocks:
        header = blk.get("header") or []
        rows = blk.get("rows") or []
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
        csm_cols = find_csm_leaf_cols(header)
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
        candidates.append((period, completeness, score, _new_business_abs(blk), blk))
    if not candidates:
        return None
    candidates.sort(key=lambda t: (t[0], t[1], t[2], t[3]), reverse=True)
    return candidates[0][4]


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
    csm_cols = find_csm_leaf_cols(header)
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
    csm_cols = find_csm_leaf_cols(main.get("header", []))
    unit_div = detect_unit_scale(blocks)
    # Heuristic fallback: when caption/header has no unit annotation we infer
    # from magnitude. A Korean insurer's CSM realistically sits between ~0.05
    # trillion KRW and ~30 trillion KRW. Expressed in different units:
    #   million KRW: 5e4   .. 3e7
    #   thousand   : 5e7   .. 3e10
    #   raw KRW    : 5e10  .. 3e13
    if unit_div == 1.0 and stages.get("opening"):
        opv = abs(stages["opening"]["value_mn_krw"])
        if opv > 1e10:  # raw KRW
            unit_div = 1_000_000.0
        elif opv > 1e8:  # thousand KRW
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
