# -*- coding: utf-8 -*-
"""경과조치 적용여부표 (transition-measure applicability) 전수 추출.

지금까지 게이트(`TIER2_TABLE_ABSENT_INTERMITTENT` -> RED 승격, 2026-08-21 orchestrator
결정)는 "item47-51 breakdown 표가 어느 분기에 없으면 추출 갭"이라 가정했는데, 교보라이프
플래닛(KR1010) 확인 결과 그 표는 **TFI(제도시행前 기발행자본증권 가용자본 인정범위 확대)
적용여부가 X인 분기에는 발행사가 아예 안 그린다** — 결측이 아니라 정상이다. 이 스크립트는
(회사 x 분기)마다 그 적용여부(TFI 포함 7종)를 O/X/UNKNOWN 으로 판정해 validation 이 조인할
수 있는 마스터를 만든다.

3-way 소스 우선순위 (한 번에 다 시도, 실패 시 다음 단계):
  1) md_inbox/ Docling MD 텍스트 (표 구조 파싱 + 문장형 판정) — 압도적 다수
  2) raw PDF fitz 텍스트 (md_inbox 파싱이 표를 깨먹은 경우 복구)
  3) vision(get_pixmap) — 스캔 전용 PDF, --vision-only 로 별도 후속 스크립트가 채움
     (이 스크립트는 vision 자체는 안 함 — 이미지 렌더는 Read 도구로 별도 수행)

표 3형식 (시간순, 회사마다 전환 시점 다를 수 있어 항상 구조 탐지 우선):
  Format 3 (2023.3Q~ 대다수) — "적용여부" 요약표, TFI/TAC/TIR/TER/TIRR 괄호코드 그대로 인쇄.
  Format 2 (예: KR1010 2023.2Q) — 서브섹션별 "해당 사항 없음" 문장(요약표 이전 형식).
  Format 1 (예: KR1010 2023.1Q) — 서브섹션별 전/후 breakdown 표 직접 인쇄(문장 없음).
Format1/2는 서브섹션 4개(1)공통적용=TFI / ①자본감소분=TAC / ②장수해지등=TIR /
③주식금리결합=TER+TIRR)로 나뉘어 있어 "해당사항없음" 문장 유무 + breakdown 표 유무로
O/X를 판정한다. ③은 TER/TIRR이 한 표에 같이 있어 금리위험/주식위험 개별 행의 전후값이
같은지(=X)/다른지(=O)로 분리 판정한다(2023.1Q KR1010에서 금리위험 15,544=15,544(X) vs
주식위험 16,932->10,159(O)로 검증됨, registry {IR,EQ}와 일치).

키: (원보험사코드, 공시분기). 값: O / X / NA / UNKNOWN. UNKNOWN은 절대 X로 메우지 않는다
(이 사고 자체가 "못 읽은 것을 X로 추정"해서 난 것이라 원칙을 코드로 강제한다). NA는 원문이
그 항목 칸에 O/X 대신 "-"를 직접 인쇄한 경우(에이비엘생명 등, "해당없음"에 가까움) — 못 읽은
게 아니라 원문 자체가 준 세 번째 값이라 UNKNOWN과 구분한다.

Usage:
  python scripts/extract_transition_applicability.py [--only KR1010,KR0080] [--out PATH]

Read-only against md_inbox/ and data/disclosure/*/raw/ — writes only to --out
(default data/_derived/kics_transition_applicability.json). Does NOT touch
kics_disclosure.json, validate_kics_disclosure.py, or any registry.
"""
from __future__ import annotations

import argparse
import glob
import json
import re
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

REPO = Path(__file__).resolve().parents[1]
MD_INBOX = REPO / "md_inbox"
DISCLOSURE = REPO / "data" / "disclosure"
DEFAULT_OUT = REPO / "data" / "_derived" / "kics_transition_applicability.json"

KNOWN_KINDS = ("TFI", "RPT", "TAC", "TIR", "TER", "TIRR", "PCA_DEFER")
KIND_LABEL = {
    "TFI": "공통적용/가용자본 - 제도시행前 기발행자본증권가용자본 인정범위 확대",
    "RPT": "공통적용/업무보고서 - 보고 및 공시기한 연장",
    "TAC": "선택적용/가용자본 - 시가평가로 인한 자본감소분 점진적 인식",
    "TIR": "선택적용/요구자본 - 신규도입 위험(신규 보험위험) 전진적 인식",
    "TER": "선택적용/요구자본 - 기존측정 위험(주식위험액 증가분) 점진적 인식",
    "TIRR": "선택적용/요구자본 - 금리위험액 증가분 점진적 인식",
    "PCA_DEFER": "선택적용/K-ICS비율 - 적기시정조치 적용 유예",
}
# _TRANSITION_KIND (validate_kics_disclosure.py) 축 이름 -> 이 표의 선택적용 코드.
# TFI/RPT/PCA_DEFER 는 registry에 대응 축이 없다(등록되지 않음, 등재된 4종만 대응).
KIND_TO_REGISTRY_AXIS = {"TAC": "AC", "TIR": "IR", "TER": "EQ", "TIRR": "INT"}


# ---------------------------------------------------------------- md parsing

def period_to_quarter(period: str) -> str:
    m = re.match(r"FY(\d{4})_Q(\d)", period)
    return f"{m.group(1)}.{m.group(2)}Q"


def quarter_to_period(q: str) -> str:
    m = re.match(r"(\d{4})\.(\d)Q", q)
    return f"FY{m.group(1)}_Q{m.group(2)}"


def _iter_table_blocks(text: str):
    lines = text.split("\n")
    block = []
    for ln in lines:
        if ln.lstrip().startswith("|"):
            block.append(ln)
        else:
            if block:
                yield block
                block = []
    if block:
        yield block


def _is_sep_row(line: str) -> bool:
    s = line.strip()
    if not s.startswith("|"):
        return False
    cells = [c.strip() for c in s.strip("|").split("|")]
    cells = [c for c in cells if c != ""]
    return bool(cells) and all(re.fullmatch(r":?-+:?", c) for c in cells)


def _split_row(line: str) -> list[str]:
    s = line.strip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|"):
        s = s[:-1]
    return [c.strip() for c in s.split("|")]


_KIND_CODE_RE = re.compile(r"\(([A-Z]{2,5})\)")


def _classify_row_kind(row_text: str) -> str | None:
    """Returns a kind code, or 'TER_TIRR_MERGED' when docling duplicated a rowspan
    cell so BOTH '(TER)' and '(TIRR)' land in the same row text (known artifact —
    original PDF has 기존측정위험 spanning 2 physical rows: TER row then TIRR row;
    docling repeats the spanned label into both). Caller resolves by row order."""
    codes = [m.group(1) for m in _KIND_CODE_RE.finditer(row_text) if m.group(1) in ("TFI", "TAC", "TIR", "TER", "TIRR")]
    if "TER" in codes and "TIRR" in codes:
        return "TER_TIRR_MERGED"
    if codes:
        return codes[0]
    # 삼성생명 등 일부사는 적용여부 표에 (TFI)/(TAC)/... 괄호코드를 아예 안 찍는다(라벨
    # 텍스트만 인쇄, 공백도 종종 없음: "제도시행전기발행자본증권가용자본인정범위확대").
    # 코드 없이도 각 종류 고유 키워드 조합으로 분류 — 이 함수는 이미 "적용여부" 표로
    # 확인된 블록 안에서만 호출되므로 다른 표와의 충돌 위험은 낮다.
    compact = row_text.replace(" ", "")
    if "기발행자본증권" in compact:
        return "TFI"
    if "자본감소분" in compact:
        return "TAC"
    if "신규보험위험" in compact or "신규도입위험" in compact:
        return "TIR"
    if "주식위험액" in compact and "증가분" in compact:
        return "TER"
    if "금리위험액" in compact and "증가분" in compact:
        return "TIRR"
    if ("보고" in row_text and "공시기한" in row_text and "연장" in row_text):
        return "RPT"
    if ("적기시정조치" in row_text and "유예" in row_text):
        return "PCA_DEFER"
    return None


def _norm_ox(cell: str) -> str | None:
    c = cell.strip()
    if c in ("O", "o", "○"):
        return "O"
    if c in ("X", "x", "×", "✕"):
        return "X"
    if c == "-":
        # a real 3rd mark some filers print (에이비엘생명 등) — distinct from O/X,
        # and NOT "we couldn't read this": raw PDF literally prints '-' in the
        # 적용여부 cell (confirmed via direct text: 에이비엘생명 2024.4Q TFI row
        # ends "...(TFI)\n-"). Treated as "해당없음"(not applicable to this filer/
        # quarter) rather than UNKNOWN, which would wrongly imply an extraction
        # failure. Kept distinct from X too: X = eligible-but-declined, NA = the
        # filer marked the row itself not applicable.
        return "NA"
    return None


def find_summary_table(text: str):
    """Format 3: explicit '적용여부' O/X table. Returns (dict[kind]->O/X, evidence_lines) or (None, None)."""
    for block in _iter_table_blocks(text):
        header_join = " ".join(block[:2])
        if "적용여부" not in header_join:
            continue
        result: dict[str, str] = {}
        evidence = []
        merged_seen = 0  # TER_TIRR_MERGED occurrence counter: 1st->TER, 2nd->TIRR
        for line in block:
            if _is_sep_row(line):
                continue
            cells = _split_row(line)
            if not cells:
                continue
            row_text = " ".join(cells)
            if "적용여부" in row_text and ("경과조치" in row_text or "구 분" in row_text or "구분" in row_text):
                continue  # header row
            kind = _classify_row_kind(row_text)
            if kind is None:
                continue
            val = None
            for c in reversed(cells):
                v = _norm_ox(c)
                if v is not None:
                    val = v
                    break
            if val is None:
                continue
            if kind == "TER_TIRR_MERGED":
                merged_seen += 1
                real_kind = "TER" if merged_seen == 1 else ("TIRR" if merged_seen == 2 else None)
                if real_kind is None:
                    continue
                result[real_kind] = val
                evidence.append(f"[merged-rowspan-artifact -> {real_kind}] " + line.strip())
                continue
            result[kind] = val
            evidence.append(line.strip())
        if result:
            return result, evidence
    return None, None


_NEGATIVE_RE = re.compile(r"해당\s*사항\s*없음|적용하지\s*않아|적용받지\s*않")
# 지급여력비율(%) / 지급여력비율: (4-2-2 style, KR1010/롯데손해/삼성화재) OR bare
# 가용자본+요구자본+지급여력비율 3-row delta table (하나생명-style 감사보고서 주석 C.3.1
# — no '(%)' suffix, values carry '%' inline instead: '131.1%').
_BREAKDOWN_ANCHOR_RE = re.compile(r"지급여력비율\s*\(%\)|지급여력비율\s*:|(?=.*가용자본)(?=.*요구자본)(?=.*지급여력비율)")

_SUBSECTION_ANCHORS = [
    ("TFI", re.compile(r"공통적용\s*경과조치\s*관련")),
    ("TAC", re.compile(r"자본감소분\s*경과조치")),
    # tolerant of both phrasings: "장수위험·사업비위험·해지위험 및 대재해위험 경과조치"
    # (KR1010/롯데손해) and "...중 장수위험액, 사업비위험액, 해지위험액, 대재해위험액 경과조치"
    # (하나생명 감사보고서 주석 style, '액' suffix + comma-joined).
    ("TIR", re.compile(r"장수위험.{0,60}대재해위험.{0,15}경과조치")),
    ("TER_TIRR", re.compile(r"주식위험\s*경과조치\s*또는\s*금리위험\s*경과조치")),
]


def _find_breakdown_table_after(text: str, start: int, end: int):
    """First markdown table within text[start:end] that looks like a 경과조치
    적용전/후 breakdown (anchored on a 지급여력비율(%) row), REQUIRING at least one
    data row with 2 genuine (non '-', non '') values. Anchor-text presence alone
    is not enough: 롯데손해's ①자본감소분 table prints a full row skeleton with
    '적용 전' filled and '적용 후' = '-' on every single row even when the filer
    means "not applied" (explicit "당사는 ... 적용하지 않아" appears in SOME but not
    all such quarters) — a dash-only shell must not read as O. Returns block
    lines or None."""
    window = text[start:end]
    for block in _iter_table_blocks(window):
        joined = " ".join(block)
        if not (_BREAKDOWN_ANCHOR_RE.search(joined) and "경과조치" in joined):
            continue
        for line in block:
            if _is_sep_row(line):
                continue
            cells = _split_row(line)
            if not cells:
                continue
            # column-header row ("구분 | 적용 전 | 경과조치 | 적용 후") is text, not
            # data, but passes the naive "not '' / not '-'" filter -> false O
            # (롯데손해 2026.1Q ①자본감소분: every DATA row is dash-only, only the
            # header row 'looked' like 2 real values). Require numeric-ish cells.
            vals = [c for c in cells[1:] if c not in ("", "-") and _looks_numeric(c)]
            if len(vals) >= 2:
                return block
    return None


_NUMERIC_CELL_RE = re.compile(r"^\(?-?[\d,]+(\.\d+)?\)?%?$")


def _looks_numeric(s: str) -> bool:
    return bool(_NUMERIC_CELL_RE.match(s.strip()))


def _row_before_after(block: list[str], label_substr: str):
    """Within a breakdown table block, find the row whose first cell contains
    label_substr and return (before, after) as raw strings, or None."""
    for line in block:
        if _is_sep_row(line):
            continue
        cells = _split_row(line)
        if not cells:
            continue
        if label_substr in cells[0]:
            vals = [c for c in cells[1:] if c not in ("", "-")]
            if len(vals) >= 2:
                return vals[0], vals[1]
            return None
    return None


def _num_eq(a: str, b: str) -> bool | None:
    def clean(s):
        s = s.replace(",", "").strip()
        s = s.replace("△", "-").replace("(", "-").replace(")", "")
        try:
            return float(s)
        except ValueError:
            return None
    x, y = clean(a), clean(b)
    if x is None or y is None:
        return None
    return abs(x - y) < 0.005 * max(1.0, abs(x), abs(y)) + 0.01


_NUM_TOKEN_RE = re.compile(r"^(?:[\d][\d,]*(?:\.\d+)?|\([\d][\d,]*(?:\.\d+)?\)|△[\d][\d,]*(?:\.\d+)?|-)$")


def _raw_text_breakdown_rows(segment: str, anchor_label: str = "지급여력비율"):
    """fitz linearizes a table as one cell per line (no pipes). Find `anchor_label`
    and read forward, splitting the stream of numeric-only lines into rows of 2
    (전/후) by re-detecting label lines (any line that is NOT a bare number).
    Returns list of (label, before, after) for whichever rows parse cleanly, or []
    if the anchor isn't followed by real tabular numbers (e.g. bare prose mention)."""
    idx = segment.find(anchor_label)
    if idx == -1:
        return []
    lines = [l.strip() for l in segment[idx:idx + 3000].split("\n") if l.strip()]
    rows = []
    i = 0
    cur_label = None
    nums: list[str] = []
    while i < len(lines) and len(rows) < 20:
        l = lines[i]
        if _NUM_TOKEN_RE.match(l):
            nums.append(l)
            if len(nums) == 2:
                if cur_label:
                    rows.append((cur_label, nums[0], nums[1]))
                cur_label, nums = None, []
        else:
            # a new label line -> flush an incomplete pair (single-column filings)
            cur_label = l
            nums = []
        i += 1
    return rows


def _raw_text_has_breakdown(segment: str) -> bool:
    """True if a real (전,후) breakdown table follows a '지급여력비율' mention —
    at least one row with 2 genuine (non-placeholder) numeric values, not just a
    prose sentence mentioning the ratio (Samsung F&M: '...지급여력비율은...270.13%
    이며,'), and not a dash-only shell table (롯데손해 ①자본감소분: every row prints
    '적용 전' once and '-' for '적용 후' even when the filer means X, not O)."""
    return any(b not in ("", "-") and a not in ("", "-") for _, a, b in _raw_text_breakdown_rows(segment))


_UNIT_CAPTION_RE = re.compile(r"\(단위\s*[:：]")
# sentence-final ending shortly after a match -> it's inside running prose
# ("...신청하여 적용하고 있습니다"), not a table heading.
_PROSE_CONTINUATION_RE = re.compile(r"습니다|었습니다|였습니다|합니다")


def _find_subsection_anchors(text: str):
    """Locate each subsection's real heading (not an early prose summary mentioning
    the same phrase — 롯데손해's intro paragraph says "...장수위험·사업비위험·해지위험
    및 대재해위험 경과조치를 신청하여 적용하고 있습니다" BEFORE the actual '②' heading,
    and re.search's default first-match would anchor there, at a text position
    *earlier* than TFI/TAC's real headings — scrambling every window boundary that
    follows). The real heading is always immediately followed by a '(단위: ...)'
    caption before the table; prose mentions never are. Prefer the first match with
    a caption within 40 chars. Among the rest, drop any match that looks like
    mid-sentence prose (ends in '습니다'/'니다.' shortly after — the intro sentence
    style) and fall back to the last non-prose match. If EVERY match for a kind
    is prose, the real heading was truncated out of the document (롯데손해
    2026.1Q: MD is cut before '②'/'③' ever appear) — skip the kind entirely
    rather than anchor on a wrong position, because a bad anchor there corrupts
    every OTHER kind's window too (TIR wrongly anchored at the too-early prose
    sentence pushed TAC's window out to a flat +6000-char fallback cap that
    swallowed an unrelated later table with real dual values -> false O)."""
    anchors = []
    for kind, rx in _SUBSECTION_ANCHORS:
        matches = list(rx.finditer(text))
        if not matches:
            continue
        chosen = None
        for mm in matches:
            if _UNIT_CAPTION_RE.search(text[mm.end():mm.end() + 40]):
                chosen = mm
                break
        if chosen is None:
            non_prose = [mm for mm in matches if not _PROSE_CONTINUATION_RE.search(text[mm.end():mm.end() + 20])]
            if non_prose:
                chosen = non_prose[-1]
        if chosen is None:
            continue
        anchors.append((chosen.start(), kind, chosen.end()))
    return anchors


def find_subsection_format_rawtext(text: str):
    """Raw-PDF-text counterpart of find_subsection_format: same anchors/negative
    regex, but the O-confirming 'is there a populated breakdown table' check uses
    _raw_text_has_breakdown (line-stream) instead of markdown-pipe parsing, and
    TER/TIRR row-equality uses _raw_text_breakdown_rows label matching."""
    anchors = _find_subsection_anchors(text)
    if not anchors:
        return {}, {}, False
    anchors.sort()
    result: dict[str, str] = {}
    evidence: dict[str, str] = {}
    for i, (pos, kind, endpos) in enumerate(anchors):
        window_end = anchors[i + 1][0] if i + 1 < len(anchors) else min(len(text), endpos + 1200)
        segment = text[endpos:window_end]
        neg = _NEGATIVE_RE.search(segment)
        has_table = _raw_text_has_breakdown(segment)
        if kind == "TER_TIRR":
            if has_table:
                rows = _raw_text_breakdown_rows(segment)
                ter_row = next((r for r in rows if "주식위험" in r[0] and "위험액" not in r[0].replace("주식위험액", "")), None)
                tirr_row = next((r for r in rows if "금리위험" in r[0]), None)
                if ter_row is not None:
                    eq = _num_eq(ter_row[1], ter_row[2])
                    if eq is not None:
                        result["TER"] = "X" if eq else "O"
                        evidence["TER"] = f"rawtext_row {ter_row}"
                if tirr_row is not None:
                    eq = _num_eq(tirr_row[1], tirr_row[2])
                    if eq is not None:
                        result["TIRR"] = "X" if eq else "O"
                        evidence["TIRR"] = f"rawtext_row {tirr_row}"
                result.setdefault("TER", "UNKNOWN")
                result.setdefault("TIRR", "UNKNOWN")
                evidence.setdefault("TER", "RAWTEXT_ROW_NOT_FOUND(주식위험)")
                evidence.setdefault("TIRR", "RAWTEXT_ROW_NOT_FOUND(금리위험)")
            elif neg is not None:
                result["TER"] = "X"
                result["TIRR"] = "X"
                evidence["TER"] = evidence["TIRR"] = f"rawtext_negative: {segment[max(0,neg.start()-10):neg.end()+10]!r}"
            else:
                result["TER"] = "UNKNOWN"
                result["TIRR"] = "UNKNOWN"
                evidence["TER"] = evidence["TIRR"] = "RAWTEXT_AMBIGUOUS(no table, no negative text)"
            continue
        if has_table:
            table_pos = segment.find("지급여력비율")
            if neg is not None and table_pos != -1 and neg.start() < table_pos:
                result[kind] = "X"
                evidence[kind] = f"rawtext_negative_before_table: {segment[max(0,neg.start()-10):neg.end()+10]!r}"
            else:
                result[kind] = "O"
                evidence[kind] = "rawtext_breakdown_table_present"
        elif neg is not None:
            result[kind] = "X"
            evidence[kind] = f"rawtext_negative: {segment[max(0,neg.start()-10):neg.end()+10]!r}"
        else:
            result[kind] = "UNKNOWN"
            evidence[kind] = "RAWTEXT_AMBIGUOUS(no table, no negative text)"
    return result, evidence, True


def find_subsection_format(text: str):
    """Format 1/2 fallback: per-subsection '해당사항없음' vs breakdown-table presence.
    Returns (dict[kind]->O/X/'UNKNOWN', evidence dict, found_any: bool)."""
    anchors = _find_subsection_anchors(text)
    if not anchors:
        return {}, {}, False
    anchors.sort()
    result: dict[str, str] = {}
    evidence: dict[str, str] = {}
    for i, (pos, kind, endpos) in enumerate(anchors):
        # Bound strictly by the next subsection anchor (or a generous flat cap for
        # the last one). Do NOT cap at the next markdown H2 heading: docling
        # sometimes tags a centered "해당 사항 없음" line itself as an H2 (KR1010
        # 2023.2Q TAC), which would truncate the window before the negative-text
        # match — i.e. the exact text we need to see would get cut off.
        window_end = anchors[i + 1][0] if i + 1 < len(anchors) else min(len(text), endpos + 1200)
        segment = text[endpos:window_end]
        neg = _NEGATIVE_RE.search(segment)
        table = _find_breakdown_table_after(text, endpos, window_end)
        if kind == "TER_TIRR":
            if table is not None:
                ter_row = _row_before_after(table, "주식위험")
                tirr_row = _row_before_after(table, "금리위험")
                if ter_row is not None:
                    eq = _num_eq(*ter_row)
                    if eq is not None:
                        result["TER"] = "X" if eq else "O"
                        evidence["TER"] = f"format1_row 주식위험 {ter_row[0]}/{ter_row[1]}"
                if tirr_row is not None:
                    eq = _num_eq(*tirr_row)
                    if eq is not None:
                        result["TIRR"] = "X" if eq else "O"
                        evidence["TIRR"] = f"format1_row 금리위험 {tirr_row[0]}/{tirr_row[1]}"
                if "TER" not in result:
                    result["TER"] = "UNKNOWN"
                    evidence["TER"] = "FORMAT1_ROW_NOT_FOUND(주식위험)"
                if "TIRR" not in result:
                    result["TIRR"] = "UNKNOWN"
                    evidence["TIRR"] = "FORMAT1_ROW_NOT_FOUND(금리위험)"
            elif neg is not None:
                # no breakdown table at all, but a negative statement -> both X
                result["TER"] = "X"
                result["TIRR"] = "X"
                evidence["TER"] = evidence["TIRR"] = f"format2_negative: ...{segment[max(0,neg.start()-10):neg.end()+10]!r}"
            else:
                result["TER"] = "UNKNOWN"
                result["TIRR"] = "UNKNOWN"
                evidence["TER"] = evidence["TIRR"] = "FORMAT1_2_AMBIGUOUS(no table, no negative text)"
            continue
        # single-kind subsections (TFI/TAC/TIR)
        if table is not None:
            # table found; treat as O unless a negative statement appears *before* the table start
            table_pos_in_segment = segment.find(table[0])
            if neg is not None and table_pos_in_segment != -1 and neg.start() < table_pos_in_segment:
                result[kind] = "X"
                evidence[kind] = f"format2_negative_before_table: {segment[max(0,neg.start()-10):neg.end()+10]!r}"
            else:
                result[kind] = "O"
                evidence[kind] = "format1_breakdown_table_present: " + table[0][:80]
        elif neg is not None:
            result[kind] = "X"
            evidence[kind] = f"format2_negative: {segment[max(0,neg.start()-10):neg.end()+10]!r}"
        else:
            result[kind] = "UNKNOWN"
            evidence[kind] = "FORMAT1_2_AMBIGUOUS(no table, no negative text)"
    return result, evidence, True


# --------------------------------------------------------------- file layer

# ------------------------------------------------- pass 2: raw PDF (fitz) fallback
# Docling MD sometimes truncates a filing before the 경과조치 section even for
# perfectly-текст (non-scanned) PDFs (observed: 삼성화재 2026.1Q MD ends at 201
# lines, no [지급여력비율의 경과조치 적용에 관한 사항] section at all) — fitz's raw
# text layer has it in full. This is NOT the scanned-PDF case; it's an MD-generation
# gap. Only used when Pass 1 (md_inbox) left TFI == UNKNOWN.

_PAGE_MARK_RE = re.compile(r"^<<<P(\d+)>>>$")


def _pdf_pages_text(pdf_path: Path):
    import fitz
    doc = fitz.open(str(pdf_path))
    pages = [(i + 1, doc[i].get_text() or "") for i in range(doc.page_count)]
    doc.close()
    return pages


def find_summary_table_rawtext(pages: list[tuple[int, str]]):
    """Same 적용여부 O/X row logic as find_summary_table, but for fitz's
    non-tabular (no pipes) linearized text: cells are one-per-line in reading
    order, so a kind marker line is followed within a few lines by a bare 'O'/'X'
    line. Returns (dict[kind]->val, evidence_list_with_page) or (None, None)."""
    marked = "\n".join(f"<<<P{pno}>>>\n{txt}" for pno, txt in pages)
    idx = marked.find("적용여부")
    if idx == -1:
        return None, None
    pre_pages = _PAGE_MARK_RE.findall("\n".join(marked[:idx].split("\n")))
    cur_page = int(pre_pages[-1]) if pre_pages else None
    lines = marked[idx:idx + 8000].split("\n")
    result: dict[str, str] = {}
    evidence = []
    merged_seen = 0
    for i, raw_line in enumerate(lines):
        pm = _PAGE_MARK_RE.match(raw_line.strip())
        if pm:
            cur_page = int(pm.group(1))
            continue
        s = raw_line.strip()
        if not s:
            continue
        kind = _classify_row_kind(s)
        if kind is None:
            continue
        val = None
        seen = 0
        j = i + 1
        while j < len(lines) and seen < 8:
            cand = lines[j].strip()
            if _PAGE_MARK_RE.match(cand):
                j += 1
                continue
            if cand:
                seen += 1
                v = _norm_ox(cand)
                if v is not None:
                    val = v
                    break
                if _classify_row_kind(cand) is not None:
                    break  # hit the next labeled row before an O/X token -> give up on this one
            j += 1
        if val is None:
            continue
        if kind == "TER_TIRR_MERGED":
            merged_seen += 1
            real_kind = "TER" if merged_seen == 1 else ("TIRR" if merged_seen == 2 else None)
            if real_kind is None:
                continue
            result[real_kind] = val
            evidence.append(f"[p{cur_page}, merged-rowspan-artifact->{real_kind}] {s} -> {val}")
            continue
        result[kind] = val
        evidence.append(f"[p{cur_page}] {s} -> {val}")
    if result:
        return result, evidence
    return None, None


def pdf_fallback(period: str, code: str):
    """Returns (result_dict, evidence, reason_if_nothing) using the raw PDF."""
    pdfs = sorted(glob.glob(str(DISCLOSURE / period / "raw" / f"{code}_*.pdf")))
    if not pdfs:
        return None, None, "NO_RAW_PDF"
    try:
        pages = _pdf_pages_text(Path(pdfs[-1]))
    except Exception as e:
        return None, None, f"PDF_OPEN_ERROR({e.__class__.__name__})"
    total_text = sum(len(t.strip()) for _, t in pages)
    if total_text < 200:
        return None, None, "SCANNED_NO_TEXT_RAW_PDF"
    summary, ev = find_summary_table_rawtext(pages)
    if summary:
        return summary, ev, None
    # subsection (Format1/2) fallback, raw-text line-stream variant (handles
    # companies — e.g. 롯데손해, BNP카디프 — that never adopted the 적용여부
    # summary table even in 2026, in *either* md_inbox or the raw PDF).
    full_text = "\n".join(t for _, t in pages)
    sub, sub_ev, found_any = find_subsection_format_rawtext(full_text)
    if found_any and sub:
        return sub, {"subsection_rawtext": sub_ev}, None
    if "경과조치" not in full_text:
        return None, None, "RAW_PDF_NO_경과조치_KEYWORD"
    return None, None, "RAW_PDF_TABLE_UNPARSED"


def _md_path(period: str, code: str) -> Path | None:
    d = MD_INBOX / period
    if not d.is_dir():
        return None
    cands = sorted(d.glob(f"{code}_*.md"))
    cands = [c for c in cands if not c.name.endswith(".stale")]
    if not cands:
        return None
    if len(cands) == 1:
        return cands[0]
    # prefer the highest amendment (amended2 > amended > base)
    def rank(p: Path):
        n = p.stem
        m = re.search(r"amended(\d*)$", n)
        if not m:
            return 0
        return int(m.group(1)) if m.group(1) else 1
    return sorted(cands, key=rank)[-1]


def _all_buckets():
    """Enumerate every (period, code, name) present in md_inbox (dedup by rank above)."""
    out = []
    for period_dir in sorted(MD_INBOX.iterdir()):
        if not period_dir.is_dir() or not re.match(r"FY\d{4}_Q\d$", period_dir.name):
            continue
        seen = set()
        files = sorted(period_dir.glob("*.md"))
        files = [f for f in files if not f.name.endswith(".stale")]
        by_code: dict[str, list[Path]] = {}
        for f in files:
            m = re.match(r"(KR\d+)_", f.name)
            if not m:
                continue
            by_code.setdefault(m.group(1), []).append(f)
        for code, paths in by_code.items():
            path = _md_path(period_dir.name, code)
            name = re.sub(r"_amended\d*$", "", path.stem.split("_", 1)[1]) if path else None
            out.append((period_dir.name, code, name, path))
    return out


def classify_unknown_reason(text: str, path: Path) -> str:
    if len(text.strip()) < 200:
        return "SCANNED_NO_TEXT"
    fm = text.split("---", 2)
    if len(fm) >= 2 and "head_fallback" in fm[1]:
        img_count = text.count("<!-- image -->")
        if img_count > 5 and "경과조치" not in text:
            return "SCANNED_HEAD_FALLBACK"
    if "경과조치" not in text:
        return "SECTION_NOT_FOUND(no 경과조치 keyword at all)"
    if "지급여력비율" not in text:
        return "SECTION_NOT_FOUND(no 지급여력비율 keyword)"
    return "TABLE_UNPARSED(경과조치 keyword present but no recognizable table/sentence)"


def extract_one(period: str, code: str, name: str, path: Path, use_pdf_fallback: bool = True) -> dict:
    quarter = period_to_quarter(period)
    rec = {
        "code": code, "name": name, "quarter": quarter,
        "md_path": str(path.relative_to(REPO)) if path else None,
    }
    for k in KNOWN_KINDS:
        rec[k] = "UNKNOWN"
    rec["format"] = None
    rec["evidence"] = {}
    rec["unknown_reason"] = None
    rec["pdf_fallback_used"] = False

    if path is None:
        rec["unknown_reason"] = "NO_MD_FILE"
    else:
        text = path.read_text(encoding="utf-8", errors="replace")
        summary, ev = find_summary_table(text)
        if summary:
            rec["format"] = "summary_table_format3"
            for k in KNOWN_KINDS:
                if k in summary:
                    rec[k] = summary[k]
            rec["evidence"]["summary_table_rows"] = ev
        else:
            sub, sub_ev, found_any = find_subsection_format(text)
            if found_any:
                rec["format"] = "subsection_format1_2"
                for k in ("TFI", "TAC", "TIR", "TER", "TIRR"):
                    if k in sub:
                        rec[k] = sub[k]
                rec["evidence"]["subsection"] = sub_ev
                if rec["TFI"] == "UNKNOWN":
                    # a subsection *was* located (found_any=True) but TFI's own
                    # anchor was missing or its window was ambiguous -> surface
                    # that per-kind reason at the top level too, so no UNKNOWN
                    # record is left with a blank unknown_reason.
                    rec["unknown_reason"] = "TFI_SUBSECTION_" + sub_ev.get("TFI", "ANCHOR_NOT_FOUND")
            else:
                rec["unknown_reason"] = classify_unknown_reason(text, path)

    if use_pdf_fallback and rec["TFI"] == "UNKNOWN":
        fb_result, fb_ev, fb_reason = pdf_fallback(period, code)
        if fb_result:
            rec["pdf_fallback_used"] = True
            for k, v in fb_result.items():
                if rec.get(k, "UNKNOWN") == "UNKNOWN":
                    rec[k] = v
            rec["evidence"]["pdf_fallback"] = fb_ev
            rec["format"] = (rec["format"] or "NONE") + "+pdf_fallback"
            if rec["TFI"] != "UNKNOWN":
                rec["unknown_reason"] = None
        elif fb_reason:
            rec["unknown_reason"] = (rec["unknown_reason"] or "") + f" | pdf_fallback:{fb_reason}"

    return rec


# ------------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", help="comma-separated company codes to restrict to")
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    ap.add_argument("--no-pdf-fallback", action="store_true", help="skip pass 2 (raw PDF fitz fallback); md_inbox only")
    args = ap.parse_args()

    only = set(args.only.split(",")) if args.only else None
    buckets = _all_buckets()
    if only:
        buckets = [b for b in buckets if b[1] in only]

    records = []
    for period, code, name, path in buckets:
        records.append(extract_one(period, code, name, path, use_pdf_fallback=not args.no_pdf_fallback))

    records.sort(key=lambda r: (r["code"], r["quarter"]))

    counts = {k: {"O": 0, "X": 0, "NA": 0, "UNKNOWN": 0} for k in KNOWN_KINDS}
    unknown_reasons: dict[str, int] = {}
    fmt_counts: dict[str, int] = {}
    pdf_fallback_used = 0
    for r in records:
        for k in KNOWN_KINDS:
            counts[k][r[k]] += 1
        fmt_counts[r["format"] or "NONE"] = fmt_counts.get(r["format"] or "NONE", 0) + 1
        if r["unknown_reason"]:
            unknown_reasons[r["unknown_reason"]] = unknown_reasons.get(r["unknown_reason"], 0) + 1
        if r.get("pdf_fallback_used"):
            pdf_fallback_used += 1

    out = {
        "_meta": {
            "generated_by": "scripts/extract_transition_applicability.py",
            "purpose": (
                "경과조치 적용여부표(O/X, 7종) 전수 추출 - TIER2_TABLE_ABSENT_INTERMITTENT RED 승격이 "
                "TFI=X(공통적용 가용자본 경과조치 미적용)라 breakdown 표 자체가 없는 정상 케이스를 "
                "추출갭으로 오판한 사고를 고치기 위한 참조 마스터. 게이트 룰에서 아직 미소비."
            ),
            "kinds": KIND_LABEL,
            "kind_to_registry_axis": KIND_TO_REGISTRY_AXIS,
            "key": ["code", "quarter"],
            "values": "O | X | NA | UNKNOWN (UNKNOWN은 절대 X로 추정하지 않음; NA=원문이 '-'를 "
                      "직접 인쇄한 3번째 실측값, UNKNOWN=우리가 못 읽음)",
            "total_records": len(records),
            "counts_by_kind": counts,
            "format_counts": fmt_counts,
            "unknown_reason_counts": unknown_reasons,
            "pdf_fallback_used_count": pdf_fallback_used,
        },
        "records": records,
    }

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"wrote {len(records)} records -> {out_path}")
    print(json.dumps(counts, ensure_ascii=False, indent=1))
    print("format_counts:", fmt_counts)
    print("unknown_reason_counts:", unknown_reasons)


if __name__ == "__main__":
    main()
