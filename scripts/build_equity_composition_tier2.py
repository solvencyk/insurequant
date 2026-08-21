#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""equity_composition.json Tier-2 (non-listed, 감사보고서-only filers) — body XML.

Scope trimmed per owner (2026-08-13, mid-session): NOT the full SCE rollforward (items
20-30) -- just item 10 (해약환급금준비금, the actual target), item 6 (AOCI point-in-time,
already on the BS), and the L1 headline (1/40/41, 자본/자산/부채총계). Annual-only (these
companies file 감사보고서, not quarterly reports) -- one row per company per FY, quarter
label "<year>.4Q".

Two table shapes, found by ROW CONTENT not caption (captions from `_iter_tables_with_context`
often pick up unrelated preceding boilerplate for these filings -- verified against 라이나생명,
where the 해약환급금준비금 table's captured caption was an unrelated 이익준비금 paragraph):

  BS: header row contains "기말" twice (당기/전기 columns); first data row's label strips to
      "자산". Columns = [label, note?, 당기, 전기] (예별) or [label, 당기, 전기] depending on
      note-column presence -- detected by column count, not assumed fixed.
  Reserve note: a row whose label starts with the concept name ("해약환급금준비금") and
      contains "기 적립액" / "적립" + "예정". Columns = [label, 당기, 전기], no note column.

Unit: DART audit-report tables almost always state "단위 : 원|천원|백만원" in a <P> shortly
before the table (NOT reliably captured as that table's own `.caption` -- see above), so this
searches the raw file text backward from each table's approximate position instead of trusting
`.caption`. Falls back to 원 (matches 예별's own BS) if no marker is found nearby -- flagged in
the diag output for manual check rather than silently guessing on a magnitude heuristic.

Run: C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/build_equity_composition_tier2.py
"""
from __future__ import annotations

import glob
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.stdout.reconfigure(encoding="utf-8")

from src.ifrs17.csm_extractor import _iter_tables_with_context

OUT = ROOT / "equity_composition.json"

TIER2 = {
    "KR0004": "예별손해보험", "KR0029": "AIG손해보험", "KR0049": "악사손해보험",
    "KR0050": "하나손해보험", "KR0051": "신한이지손해보험", "KR0074": "라이나생명보험",
    "KR0075": "비엔피파리바카디프생명보험", "KR0076": "아이엠라이프생명보험",
    "KR0080": "에이아이에이생명보험", "KR0095": "메트라이프생명보험",
    "KR0097": "하나생명보험", "KR0100": "처브라이프생명보험",
    "KR1010": "교보라이프플래닛생명보험", "KR1011": "IBK연금보험",
    "KR1098": "카카오페이손해보험",
}
SB_OF = {}  # kr -> 생손보여부, filled from kics_disclosure.json below
TICKER_OF = {}

for r in json.loads((ROOT / "kics_disclosure.json").read_text(encoding="utf-8")):
    c = r.get("원보험사코드")
    if c in TIER2 and c not in SB_OF:
        SB_OF[c] = r.get("생손보여부")
        TICKER_OF[c] = r.get("티커")

_UNIT_SCALE = {"원": 1e-6, "천원": 1e-3, "백만원": 1.0, "천 원": 1e-3, "백만 원": 1.0}


def _num(s):
    if s is None:
        return None
    s = s.strip().replace(",", "")
    if not s or s == "-":
        return None
    neg = s.startswith("(") and s.endswith(")")
    s = s.strip("()")
    try:
        v = float(s)
    except ValueError:
        return None
    return -v if neg else v


def _strip(s):
    return re.sub(r"\s+", "", s or "")


def _unit_markers_by_line(raw_lines: list[str]) -> list[tuple[int, float]]:
    """[(line_no, scale), ...] sorted ascending, one per '단위:X' marker in the file."""
    out = []
    for i, line in enumerate(raw_lines, start=1):
        for m in re.finditer(r"단위\s*[:：]\s*([가-힣]+)", line):
            if m.group(1) in _UNIT_SCALE:
                out.append((i, _UNIT_SCALE[m.group(1)]))
    return out


def _find_unit(markers: list[tuple[int, float]], line_no: int) -> float:
    """Scale for the LAST unit marker at or before line_no (lxml sourceline is 1-indexed
    and, critically, robust to whitespace-normalization -- unlike a raw_text.find() of the
    table's PARSED cell text, which silently fails whenever the source markup splits a
    label across tags/entities (verified: AIA생명's "자 산 총 계" cell text, built by
    _text()'s whitespace-joining of child nodes, does not appear as that literal substring
    anywhere in the raw bytes -- find() returned -1, silently defaulting to the wrong unit
    for every AIA row). No marker at/before line_no -> default 원 (matches 예별, which has
    no marker before its own BS table)."""
    scale = 1e-6
    for ln, sc in markers:
        if ln > line_no:
            break
        scale = sc
    return scale


def _bs_row_value(row, ncols):
    # [label, note, 당기, 전기] or [label, 당기, 전기]
    return row[-2] if ncols >= 3 else (row[-1] if ncols == 2 else None)


_PERIOD_HDR_RE = re.compile(r"제\s*\d+\s*\(?\s*[당전]?\s*\)?\s*기|당[반분]?기|전[반분]?기|\d{4}[.\-년]")


def _bs_period_layout(header, ncols: int):
    """(당기 열 인덱스, 기간당 열 수). 판정 불가면 None.

    `_bs_row_value` 의 `row[-2]` 규칙은 [라벨, 당기, 전기] / [라벨, 주석, 당기, 전기] 두 모양만
    맞다. 실제 공시에는 그 밖의 모양이 흔하고, 둘 다 **조용히 전기(또는 주석) 열을 읽는다**:

    * 3기간 표 -- 예별손해보험 FY2023:
      header ['과 목','주석','제11(당)기말','제10(전)기말','제 10(전)기초'] (5열)
      `row[-2]` = 제10(전)기말 -> **BS 전체가 한 해 밀린다.**
    * 들여쓰기형(한 기간이 2열) -- 카카오페이손해보험:
      header ['과 목','제5(당)기','제4(전)기'] 인데 행은 5열
      [라벨, 자식-당기, 부모-당기, 자식-전기, 부모-전기] -> `row[-2]` = 전기-자식.

    그래서 **헤더에서 기간 열의 위치를 직접 찾는다.** 행 길이가 헤더와 같으면 첫 기간 열이
    곧 당기; 다르면(병합 헤더) 남은 열을 기간 수로 나눈 블록의 첫 유효값을 쓴다.
    """
    if not header:
        return None
    hdr = header[-1]
    idxs = [i for i, c in enumerate(hdr) if _PERIOD_HDR_RE.search(str(c or ""))]
    if not idxs:
        return None
    start, nper = idxs[0], len(idxs)
    if len(hdr) == ncols:
        return (start, 1) if start < ncols else None
    if nper >= 2 and start < ncols:
        block, rem = divmod(ncols - start, nper)
        if rem == 0 and block >= 2:
            return start, block
    return None


def _bs_period_value(row, layout):
    """당기 열의 값. layout 이 없으면 기존 `_bs_row_value` 규칙으로 떨어진다."""
    if layout:
        start, block = layout
        if start < len(row):
            for cell in row[start:start + block]:
                if _num(cell) is not None:
                    return cell
            return None
    return _bs_row_value(row, len(row))


# 본문 XML BS 세부 라벨 -> 마스터 항목번호(200 + 항목번호). 회사마다 계정명이 다르므로
# 전 필링 라벨 census(2026-08-20, 345 필링)에서 실제로 쓰이는 표기만 담았다. FS-API 쪽
# ACCOUNT_IDS의 대안 태그 체인과 같은 개념 묶음이다(build_ifrs17_bs.py 참조).
_BS_DETAIL_LABELS = {
    210: ("현금및현금성자산", "현금및예치금", "현금및상각후원가측정예치금"),
    211: ("당기손익-공정가치측정금융자산", "당기손익공정가치측정금융자산",
          "당기손익인식-공정가치측정금융자산"),
    212: ("기타포괄손익-공정가치측정금융자산", "기타포괄손익공정가치측정금융자산",
          "기타포괄손익인식-공정가치측정금융자산"),
    214: ("재보험계약자산",),
    215: ("유형자산",),
    220: ("보험계약부채",),
    221: ("재보험계약부채",),
    222: ("투자계약부채",),
    223: ("차입부채",),
    224: ("기타부채",),
    230: ("자본금",),
    231: ("이익잉여금", "이익잉여금(결손금)"),
}
_AC_PARENT_LABELS = ("상각후원가측정금융자산",)
_AC_CHILD_LABELS = ("상각후원가측정대출채권", "상각후원가측정유가증권",
                    "상각후원가측정기타금융자산", "상각후원가측정대출채권및수취채권",
                    "상각후원가측정기타수취채권", "상각후원가측정예치금")


# --- BS table selection (2026-08-20) ---------------------------------------------------
# 이 파일이 원래 쓰던 규칙은 "첫 번째 행 라벨이 '자산'인 표를 하나 잡고 break" 였는데,
# 정기보고서 본문에는 그런 표가 한 필링에 4~6개 들어 있다 -- 요약연결재무정보 / 연결재무상태표
# / 요약재무정보 / (별도)재무상태표 / IFRS17 전환일 소급표 / 심지어 '자산부채 현황' 같은
# 증감표까지. 문서 순서상 **연결이 별도보다 먼저** 나오므로 "첫 표"는 사실상 연결을 고르는
# 규칙이었다. 이 마스터의 계약은 OFS(별도) 고정이라(owner 2026-08-14 P-1) 그대로 두면
# "산수는 맞고 소스가 틀린" 셀이 된다 -- 실측 2026-08-20: DB손해 2023.1Q 57.5조(연결)가
# 별도 44.6조 자리에, 한화생명 2023.1Q 146.6조(연결)가 별도 109.4조 자리에 들어가 있었고,
# 현대해상 2023.1Q/2Q는 '자산부채 현황' 증감표를 물어 **자산총계가 음수**였다.
#
# 새 규칙: 후보를 전부 모은 뒤 순위를 매겨 하나만 고른다.
#   1) 전환일 소급표("2022년 12월 31일 기준 재무상태표")는 항상 최후순위 -- 당기가 아니다.
#   2) 별도(OFS) > 불명(?) > 연결(CFS). 판정은 캡션 우선, 없으면 표 앞의 최근 섹션 제목
#      ("2. 연결재무제표" / "4-1. 재무상태표" -- DART 표준 절 번호)을 line_no로 역추적.
#   3) 마감항등식(자산 = 부채 + 자본, 0.5%)이 닫히는 표 우선 -- 증감표/음수표를 걸러낸다.
#   4) 요약표보다 전체표, 행 많은 쪽, 그다음 문서 순서.
_BS_BASIS_RE = re.compile(r"(연결)?재무(?:상태표|제표)")
# 전환일 소급표 마커: "(가) 2022년 12월 31일 기준 재무상태표"(IFRS17 최초적용 비교표시)와
# "기업회계기준서 제1117호를 적용할 경우 2022.12.31. ..."(에이아이에이생명 감사보고서).
# 둘 다 당기 BS가 아니라 소급 재작성치라 항상 최후순위로 민다.
_TRANSITION_CAP_RE = re.compile(r"\d{4}년\d{1,2}월\d{1,2}일기준|1117호를적용할경우")
_BASIS_RANK = {"OFS": 0, "?": 1, "CFS": 2}
_BS_TOTAL_LABELS = {"자산총계": "A", "부채총계": "L", "자본총계": "E"}


def _bs_basis_markers(raw_lines: list[str]) -> list[tuple[int, str]]:
    """[(line_no, 'OFS'|'CFS'), ...] -- 본문의 재무제표 절 제목만 (짧은 줄로 한정해서
    '연결재무제표는 ...' 같은 서술 문장은 제외; 그래도 새는 건 캡션 판정이 덮는다)."""
    out = []
    for i, line in enumerate(raw_lines, start=1):
        s = re.sub(r"\s+", "", re.sub(r"<[^>]+>", "", line))
        if not s or len(s) > 70:
            continue
        m = _BS_BASIS_RE.search(s)
        if not m:
            continue
        cfs = bool(m.group(1)) and not (m.start() > 0 and s[m.start() - 1] == "비")
        out.append((i, "CFS" if cfs else "OFS"))
    return out


def _find_basis(markers: list[tuple[int, str]], line_no: int) -> str:
    basis = "?"
    for ln, b in markers:
        if ln > line_no:
            break
        basis = b
    return basis


def _bs_label(raw: str) -> str:
    """BS 행 라벨 정규화 -- 로마숫자/번호 prefix와 각주 suffix를 벗긴다.
    각주 표기는 `(주석29)` 뿐 아니라 `(주21)` · `(주5,6,7,8)` 형태도 흔하다(카카오페이손해보험은
    거의 모든 행이 후자라 AOCI 가 통째로 안 잡혔다 -- 2026-08-20 실측)."""
    lab = _strip(raw)
    lab = re.sub(r"^[IVXⅠ-Ⅹ]+[.\s]*", "", lab)
    lab = lab.lstrip("ⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩ.0123456789()가나다라마바사")
    return re.sub(r"\(주[석]?[\d,\s]*\)$", "", lab)


def _pick_bs_table(tables, markers, raw_lines):
    """후보 BS 표 중 하나를 고른다. 없으면 None."""
    bmarks = _bs_basis_markers(raw_lines)
    cands = []
    for t in tables:
        raw0 = t.rows[0][0] if t.rows and t.rows[0] else ""
        if _bs_label(raw0) != "자산":
            continue
        scale = _find_unit(markers, t.line_no)
        layout = _bs_period_layout(t.header, max((len(r) for r in t.rows), default=0))
        tot = {}
        for r in t.rows:
            if not r or not r[0]:
                continue
            key = _BS_TOTAL_LABELS.get(_bs_label(r[0]))
            if key and key not in tot:
                v = _num(_bs_period_value(r, layout))
                if v is not None:
                    tot[key] = v * scale
        cap = _strip(t.caption or "")
        basis = _find_basis(bmarks, t.line_no)
        if "연결" in cap.replace("비연결", ""):
            basis = "CFS"
        elif "별도" in cap:
            basis = "OFS"
        closed = (len(tot) == 3 and tot["A"] > 0
                  and abs(tot["A"] - tot["L"] - tot["E"]) <= abs(tot["A"]) * 0.005)
        if "A" in tot and tot["A"] <= 0:
            # 증감표(현대해상 '(1) 자산부채 현황')는 자산총계가 음수로 나온다 -- BS가 아니다.
            # 자산총계 행이 아예 **없는** 표는 버리지 않는다: Tier-2 감사보고서 BS는 총계
            # 라벨이 표에 안 잡히는 경우가 있고(에이아이에이생명 2022.4Q), 그래도 AOCI·자본총계는
            # 정상이라 버리면 그 셀들이 통째로 사라진다.
            continue
        cands.append((t, scale, basis, closed, bool(_TRANSITION_CAP_RE.search(cap)),
                      "요약" in cap, len(t.rows), len(tot), layout))
    if not cands:
        return None
    # 순위: 전환일표 최후 -> 별도(OFS) 우선 -> 총계를 많이 담은 표 우선(요약표라도 총계가
    # 있는 쪽이, 총계가 하나도 없는 '(전기)' 조각표보다 낫다 -- 서울보증 2024.4Q 실측) ->
    # 요약보다 전체 -> 행 많은 쪽 -> 항등식 닫힘 -> 문서 순서.
    cands.sort(key=lambda c: (c[4], _BASIS_RANK[c[2]], -c[7], c[5], -c[6], not c[3],
                              c[0].line_no))
    return cands[0]


_TRANSPOSED_RE_CONCEPTS = {
    "해약환급금준비금": 10, "비상위험준비금": 12, "대손준비금": 14,
    # 보증준비금은 17(item16은 item5 Part C의 전기컬럼 예약 번호라 충돌 방지)
    "보증준비금": 17,
}


def _transposed_re_row(t: "ExtractedTable"):
    """이익잉여금 구성 표가 준비금종류=컬럼 / 합계 한 줄=행으로 뒤집힌 경우 (한화생명류).
    마지막 헤더행이 컬럼명(예: ['', '이익준비금', '대손준비금', '해약환급금준비금', ...]),
    라벨이 "이익잉여금"인 데이터 행의 같은 위치가 그 컬럼의 값이다. 헤더에 타깃 개념이
    하나도 없으면 이 표가 아니므로 즉시 포기 -- 무관한 표에서 우연히 컬럼이 밀려 값을
    잘못 집는 일이 없게 개념명 존재를 먼저 확인한다."""
    if not t.header:
        return None
    concept_row = t.header[-1]
    idx = {item: i for i, cell in enumerate(concept_row)
           for concept, item in _TRANSPOSED_RE_CONCEPTS.items() if cell == concept}
    if not idx:
        return None
    for row in t.rows:
        if not row or _strip(row[0]) != "이익잉여금":
            continue
        out = {}
        for item, i in idx.items():
            if i < len(row):
                v = _num(row[i])
                if v is not None:
                    out[item] = v
        if out:
            return out
    return None


def parse_filing(xml_path: Path):
    """Returns {item: value_mn_krw} best-effort from one audit-report XML."""
    raw_lines = xml_path.read_text(encoding="utf-8", errors="replace").split("\n")
    markers = _unit_markers_by_line(raw_lines)
    tables = list(_iter_tables_with_context(xml_path))
    out = {}
    diag = []

    # --- BS: 자산/부채/자본총계 + AOCI + T자 드릴다운 세부 ---
    # 표 선택 규칙은 위 `_pick_bs_table` 참조 (2026-08-20에 "첫 표" -> 순위 선택으로 교체).
    bs_labels = {"자산총계": 40, "부채총계": 41, "자본총계": 1, "기타포괄손익누계액": 6,
                 "기타포괄손익누적액": 6}
    picked = _pick_bs_table(tables, markers, raw_lines)
    if picked is None:
        diag.append("no BS table found")
    else:
        t, scale, basis, closed, _tr, _sm, _n, _nt, layout = picked
        diag.append(f"BS table basis={basis} closed={int(closed)} line={t.line_no}")
        ac_children = []
        for r in t.rows:
            if not r or not r[0]:
                continue
            lab = _bs_label(r[0])
            for needle, item in bs_labels.items():
                if lab == needle and item not in out:
                    v = _num(_bs_period_value(r, layout))
                    if v is not None:
                        out[item] = v * scale
            # T자 드릴다운 세부 (항목 10-15/20-24/30/31). 본문 XML만 있는 (회사,분기)는
            # 지금까지 총계 4개만 채워져 화면 드릴다운이 통째로 비었다 -- 실측 2026-08-20:
            # 흥국화재 2026.2Q가 7행(FS-API 응답이 BS 1행짜리 빈 껍데기라 세부가 전무),
            # 동종사는 16~18행. 소스 번호는 준비금(10~18)과 겹치지 않게 200번대를 쓴다.
            for item, needles in _BS_DETAIL_LABELS.items():
                if lab in needles and item not in out:
                    v = _num(_bs_period_value(r, layout))
                    if v is not None:
                        out[item] = v * scale
            if lab in _AC_PARENT_LABELS and 213 not in out:
                v = _num(_bs_period_value(r, layout))
                if v is not None:
                    out[213] = v * scale
            elif lab in _AC_CHILD_LABELS:
                v = _num(_bs_period_value(r, layout))
                if v is not None:
                    ac_children.append(v * scale)
        # item13(상각후원가측정금융자산)은 FS-API와 같은 규칙 -- 부모 태그가 있으면 부모,
        # 없을 때만 자식 합산 (이중계상 위험이 있는 방향으로 기울지 않게).
        if 213 not in out and ac_children:
            out[213] = sum(ac_children)
        # 총계(자산총계)를 못 읽은 표에서는 세부도 신뢰하지 않는다. 실측: 카카오페이손해보험
        # 감사보고서 BS는 5열이라 `_bs_row_value`(row[-2])가 거의 모든 행에서 빈칸을 집고
        # 하위 한 행만 우연히 값이 잡혔다 -- 그 한 셀 때문에 (회사,분기) 키가 생겨 census가
        # 코어 4항목 결측 RED 8건을 냈다. 헤드라인 없는 드릴다운은 화면에서도 쓸모가 없다.
        if 40 not in out:
            for k in [k for k in out if k in _BS_DETAIL_LABELS or k == 213]:
                del out[k]

    # --- reserve notes: 해약환급금/비상위험/대손/보증 ---
    concepts = {
        "해약환급금준비금": (10, 11), "비상위험준비금": (12, 13), "대손준비금": (14, 15),
        "보증준비금": (17, 18),
    }
    # 보증준비금은 규정상(보험업감독규정 제6-11조의5) 해약환급금준비금을 먼저 적립한 후에만
    # 적립 가능해 거의 항상 같은 노트/표에 나란히 공시된다(census 2026-08-19: 흥국생명·
    # 동양생명·KB라이프·신한라이프·케이디비생명 전부 확인) -- 위 concepts에 추가만 하면 기존
    # 기적립액/적립+예정 매칭이 그대로 적용된다. 단 이 개념만 "적립" 없이 "환입 예정(금)액"
    # 단독으로 찍히는 케이스가 있다(흥국생명·케이디비생명, 현재 환입 국면이라 순수 반대말만
    # 씀) -- 아래 pending 매칭에서 이 개념만 "환입" 단독도 허용.
    def _pending_ok_default(rest):
        if "적립" in rest and "예정" in rest:
            return True
        # "적립액"(예정 없이, 하나생명 "해약환급금준비금 적립액(*1)")과 "전입액"/"전입"
        # (동양생명·DB생명 "...전입액"/"...전입")도 pending(당기 변동분)의 동의어다 --
        # 둘 다 accrued의 "기적립액"과 글자가 달라 혼동 안 됨, 정확일치로 좁게 인정
        # (owner census 2026-08-19, D-1: 6사 중 3사가 이 라벨 계열).
        return rest in ("적립액", "전입액", "전입")
    _PENDING_OK = {
        "보증준비금": lambda rest: "예정" in rest and ("적립" in rest or "환입" in rest),
    }
    # item16은 item5의 Part C(전기컬럼, 2022년말 소급) 예약 번호라 충돌 방지로 17/18을 쓴다.

    def _guarantee_scale(v, scale, concept=None, line_no=0):
        """대형 필링 매그니튜드 안전장치 (원래 보증준비금 전용이었다가 2026-08-19 D-1에서
        해약환급금준비금도 같은 증상 확인돼 4개 개념 전체로 일반화). `_find_unit`은 lxml
        `.sourceline`(부호없는 16비트, 65535 캡)로 단위마커 앞뒤를 판정하는데, 65535줄을
        넘는 대형 필링에서는 그 판정 자체가 무의미해진다 -- 실측 2건, 방향이 반대:
        (a) 한화생명 FY2023 '5. 보증준비금' 원표 183,194,432,055원인데 scale이 1.0(백만원
        오판)으로 나와 그대로 찍힘(실제 183,194.432055백만원, 1e6배 과다);
        (b) 같은 회사 FY2024.1Q '해약환급금준비금' 원표 2,504,752(이미 백만원 단위로 인쇄된
        표시)인데 다른 대형 표에서 scale이 1e-6(원 오판)로 나와 2.504752로 찍힘(화면엔
        반올림돼 "3"으로 보임, 1e6배 부족). line_no가 캡(65535)에 걸린 표에서만 이 방어를
        건다 -- 캡 안 걸린 정상 표는 `_find_unit`의 위치기반 판정을 그대로 신뢰(이 방어를
        걸면 오히려 진짜 소액값을 오판할 위험). 캡이 걸렸을 때는 위치정보가 무의미하므로
        스케일된 결과의 그럴듯한 범위(1~1억백만원)로 방향을 판정 -- 과다(>1억)면 1e6로
        나누고, 과소(<1이면서 원래 셀 숫자가 4자리 이상이라 소액이 아님)면 1e6를 곱한다."""
        out_v = v * scale
        if line_no < 65535:
            return out_v
        if abs(out_v) > 1e8:
            return v * scale * 1e-6
        # 100백만원(=1억원) 밑은 이 규모 회사의 법정준비금으로 비현실적으로 작다 -- 단
        # 원래 셀 자체가 4자리 미만(진짜 소액)이면 건드리지 않는다(오판 방지).
        if abs(out_v) < 100 and abs(v) >= 1000:
            return v * scale * 1e6
        return out_v

    def _row_value(r):
        """3/4셀 표는 r[-2]가 당기(기존 규약, item5도 이걸 씀 -- 안 건드림). 한화생명 FY2023
        '4-5. 이익잉여금처분계산서'만 5셀(['5. 보증준비금','183,194,432,055','','-','']
        -- 헤더는 당기/전기 2개뿐인데 데이터 행이 5칸인 건 기수 컬럼이 [값,빈칸] 2칸씩 펼쳐진
        것, 당기는 항상 인덱스1)이라 r[-2]가 전기 자리의 '-'를 집는다(오독). **주의**: "첫
        파싱되는 숫자를 스캔"하면 안 된다 -- 케이디비생명 3셀 ['...','-','2,913']처럼 당기가
        진짜 없고(dash) 전기만 값이 있는 정당한 케이스에서 전기를 당기로 오인하게 된다(실제로
        이 방식으로 한 번 잘못됨, 수정). 그래서 5셀일 때만 인덱스1 특례, 그 외엔 원래 규약대로."""
        if len(r) == 5:
            return r[1]
        return r[-2] if len(r) >= 3 else (r[-1] if len(r) == 2 else None)
    # Some filers' "조정이익" note frames the addition as a deduction FROM net income (e.g.
    # 흥국생명 FY2025 annual: caption "...결산에 반영한 준비금 적립예정액과 준비금 적립후의
    # 조정이익...", row value "(340,381)" -- parenthesized/negative) even though the SAME
    # filing's own plain-language sentence states it as a positive addition ("적립예정액은
    # 340,381백만원입니다"). The reserve's own addition is the opposite sign of that table's
    # number -- verified 2026-08-14 (owner hand-caught the flipped sign in
    # insurequant_master_tables.xlsx before this fix landed).
    # "조정손익"(DB생명 FY2023 "(6) 준비금 반영 후 조정손익" 표) 추가 -- "조정이익"과 같은
    # 프레이밍(준비금 반영 전/후 손익 비교)을 부르는 표현 변형일 뿐인데 글자가 달라(손익≠이익)
    # 기존 마커에 안 걸려 이 표의 부호반전이 누락됐었다 (owner census 2026-08-19, D-1).
    _NET_INCOME_FRAME_MARKERS = ("조정이익", "조정손익", "당기순이익")
    # accrued 값이 "...잔액" 행(=회사가 이미 기적립+예정을 합산해둔 총액)에서 온 개념의
    # pending item 번호. 함수 끝에서 0으로 눌러 호출부의 재합산을 무해화한다(아래 참조).
    _total_items: set[int] = set()
    for t in tables:
        scale = _find_unit(markers, t.line_no)
        caption = t.caption or ""
        net_income_framed = any(m in caption for m in _NET_INCOME_FRAME_MARKERS)
        for r in t.rows:
            if not r or not r[0]:
                continue
            lab = _strip(r[0])
            for concept, (accrued_item, pending_item) in concepts.items():
                # 번호 접두사("4. 해약환급금준비금...", 한화생명 처분계산서류) 제거 -- 원래
                # 보증준비금 한정이었으나 D-1 census(owner 2026-08-19)에서 하나생명 "4.
                # 해약환급금준비금 전입액"도 같은 패턴으로 확인돼 전 개념으로 일반화(안전:
                # 접두사가 없으면 lstrip은 그냥 no-op).
                stripped = lab.lstrip("0123456789.() ")
                if stripped.startswith(concept):
                    rest = stripped[len(concept):]
                else:
                    continue
                # 꼬리 각주표시("(*)"/"(*1)"/"(*2)", DB생명·하나생명 "해약환급금준비금(*)"/
                # "...적립액(*1)") 제거 -- 이것도 원래 없던 처리라 rest가 "(*)"/"적립액(*1)"
                # 같은 미매칭 문자열로 남아 기적립액/적립예정 매칭에서 전부 새 나갔다.
                rest = re.sub(r"\(\*+\d*\)$", "", rest)
                # Bare concept name (no suffix) inside a 이익잉여금 breakdown table is the
                # SAME 기적립액 balance, just not spelled out in the row label (verified:
                # 흥국생명 "당기말과 전기말 현재 이익잉여금의 내역은..." table, row
                # ['해약환급금준비금', '6,257', '-']). A bare name with exactly ONE value
                # cell (동양생명 "25-A. 자본" 표: header=['','','','공시금액'], row=
                # ['보증준비금','59,489']) is equally unambiguous regardless of caption --
                # there's nothing else a single-column concept-only row could mean, and
                # captions here are known-unreliable (this file's own docstring).
                #
                # "이익잉여금" 캡션 매칭에 "이익잉여금처분계산서"(이번 기 순이익을 어디로
                # 배분하는지 보여주는 FLOW 표)까지 걸리면 오분류가 난다 -- 처음엔 보증준비금
                # 한정(메트라이프 FY2023의 "5.보증준비금" 행, 당기 신규 적립예정액 971,720,131을
                # 기적립액/STOCK으로 오분류할 뻔했던 사례)이었으나, D-1(owner 2026-08-19)에서
                # 해약환급금준비금도 같은 함정 확인 -- 동양생명 FY2023 "4-5.이익잉여금처분계산서
                # (안)" 표의 "3. 해약환급금준비금" 행(640,200,999,200원=640,201백만원)이 "전입액"
                # 표의 같은 사건(부호반전 후 +640,201)과 중복 합산돼 item5가 2배(1,280,402)로
                # 뻥튀기됐었다. "이익잉여금의 내역/구성내역"(잔액 breakdown, DB생명 케이스로
                # 검증: 캡션 "이익잉여금의 내역"이지 처분계산서 아님, 안 건드림)과 "처분계산서"
                # (이번 기 배분)는 캡션에 둘 다 "이익잉여금"을 포함해 문자열만으론 구분이 안 되므로
                # 4개 개념 전체에서 처분계산서를 명시적으로 제외한다.
                _ok_caption = ("이익잉여금" in caption) and "처분계산서" not in caption
                # "...잔액" 접미사(예: "해약환급금준비금잔액")도 기적립액과 동급의 무조건적
                # STOCK 신호다 -- "잔액"은 캡션과 무관하게 그 자체로 balance를 뜻해 "기적립액"과
                # 똑같이 캡션게이팅 없이 인정 (owner census 2026-08-19: KB손보·교보·라이나 등
                # 9사가 이 라벨 단독 표기, inbox/parser/20260819T0116Z 섹션 F).
                #
                # ⚠ 단 "잔액"은 **기적립액과 의미가 다르다**: 회사가 이미 `기적립액 + 적립(환입)
                # 예정액`을 자기 손으로 더해놓은 **최종 합계**다(P2 표준 3행 표: 기적립액/
                # 적립예정액/잔액). 그래서 호출부가 관례대로 예정액을 또 더하면 예정액이 두 번
                # 들어간다 -- 실측: 라이나생명 2023.4Q가 2.25조여야 하는데 4.50조(정확히 2배)로,
                # 신한라이프 2023.4Q도 6.9조로 부풀어 업권 합계가 보도치를 +14.7% 넘겼다.
                # 아래 `_total_items`에 기록해뒀다가 함수 끝에서 그 개념의 예정액을 0으로 눌러
                # 호출부 산술(`v + vals.get(11, 0.0)`)을 무해하게 만든다.
                _is_total_row = (rest == "잔액")
                if (rest in ("기적립액", "잔액") or (rest == "" and (_ok_caption or len(r) == 2))) \
                        and accrued_item not in out:
                    raw_v = _row_value(r)
                    v = _num(raw_v)
                    if v is not None:
                        out[accrued_item] = _guarantee_scale(v, scale, concept, t.line_no)
                        if _is_total_row:
                            _total_items.add(pending_item)
                elif _PENDING_OK.get(concept, _pending_ok_default)(rest) \
                        and pending_item not in out \
                        and not ("처분계산서" in caption and accrued_item in out):
                    # 처분계산서 표의 "...전입"/"...전입액" 행이 이미 확보된 기적립액(accrued,
                    # 보통 "이익잉여금의 내역" 표에서 옴)과 같은 사건의 중복 표기인 사례 발견
                    # (DB생명보험 FY2023: 이익잉여금내역 표 1,633,087 확보 후 처분계산서의
                    # "해약환급금준비금전입" (1,633,087)이 별개 사건인 양 또 더해져 item5가
                    # 0으로 상쇄됐었다 -- 부호까지 반대라 원래 있던 정답이 사라지는 방향으로
                    # 망가짐). 단, 케이비라이프생명처럼 기적립액 행 자체가 "-"(진짜 미확보)인
                    # 회사는 처분계산서가 유일한 소스라 accrued_item이 아직 out에 없으므로 이
                    # 가드에 안 걸린다 -- 표 종류가 아니라 "이미 확보됐는지"로 가른다.
                    raw_v = _row_value(r)
                    v = _num(raw_v)
                    if v is not None:
                        # net_income_framed 반전은 해약환급금 전용으로 검증된 규칙이다(그
                        # 개념은 원표가 음수로 찍고 서술문은 양수라고 말하는 패턴). 보증준비금은
                        # 반대 사례로 검증됨(한화생명 FY2023, 캡션 "...보증준비금 적립 후
                        # 조정이익은..."(조정이익 프레임 O), 원표 "적립(환입)예정금액 29,678"
                        # (양수, 괄호 없음) -- 616,262-29,678=586,584로 정확히 닫혀 이게 진짜
                        # 양의 적립액임을 확인(반전하면 오히려 부호가 깨짐). 그래서 이 개념만
                        # net_income_framed 반전을 안 걸고, 라벨 단어("환입"단독)에만 의존한다.
                        if net_income_framed and concept != "보증준비금":
                            v = -v
                        # 라벨이 "환입"만 쓰고 "적립"을 안 쓴(적립/환입 겸용 라벨이 아닌) 순수
                        # 환입 케이스는 원표가 크기만 양수로 찍고 방향은 라벨 단어("환입")로만
                        # 알려주는 관행이 있다(흥국생명 "환입 예정금액: 14,670", 서술문도
                        # "환입 예정액은 14,670백만원" -- 부호 없이 크기만). 괄호로 이미 음수인
                        # 경우(케이디비생명 "(2,913)")는 원표가 스스로 부호를 냈으니 안 건드림.
                        if "환입" in rest and "적립" not in rest and v > 0:
                            v = -v
                        out[pending_item] = _guarantee_scale(v, scale, concept, t.line_no)
    # --- pending-reserve, concept-SUFFIXED label ("적립 예정인 X" / "환입 예정인 X", concept
    # name at the END not the start -- 동양생명 자본 노트: "적립 예정인 보증준비금" | 52,301,
    # a reversed word order the startswith()-based loop above can't reach at all). Scoped
    # narrowly (exact prefix words only) to avoid false-matching an unrelated "...인 X" row.
    for t in tables:
        scale = _find_unit(markers, t.line_no)
        for r in t.rows:
            if not r or not r[0]:
                continue
            lab = _strip(r[0])
            for concept, (accrued_item, pending_item) in concepts.items():
                if pending_item in out:
                    continue
                for prefix in ("적립예정인", "환입예정인", "적립(환입)예정인"):
                    if lab == prefix + concept:
                        raw_v = _row_value(r)
                        v = _num(raw_v)
                        if v is not None:
                            if "환입" in prefix and "적립" not in prefix and v > 0:
                                v = -v
                            out[pending_item] = _guarantee_scale(v, scale, concept, t.line_no)
                        break
    # --- reserve notes, transposed shape: 준비금종류=컬럼, 합계 한 줄="이익잉여금"=행
    # (한화생명류, 2026-08-13 발견 -- validation round-2 P2-5 item10 Tier-1 notes 확장).
    # 이 표들은 caption이 앞쪽 무관한 문단을 잘못 붙잡는 경우가 흔해서(위 파일 docstring의
    # 같은 함정) caption이 아니라 헤더 내용으로 식별한다.
    for t in tables:
        got = _transposed_re_row(t)
        if not got:
            continue
        scale = _find_unit(markers, t.line_no)
        for item, v in got.items():
            if item not in out:
                out[item] = _guarantee_scale(v, scale, "보증준비금" if item == 17 else None, t.line_no)
    # "잔액" 행에서 온 개념은 이미 총액이므로 예정액을 0으로 눌러 호출부(Tier-2 루프의
    # `v + vals.get(11, 0.0)`, Part A의 Q4 fold-in)가 두 번 더하지 못하게 한다. 값을 지우지
    # 않고 0으로 두는 이유: 호출부마다 `in vals` 존재검사 분기가 달라, 키를 없애면 "예정액
    # 미공시"로 오인돼 다른 경로가 열리는 부작용이 있다.
    for _pi in _total_items:
        out[_pi] = 0.0
    if 10 in out and 12 in out and 14 in out:
        out[19] = out[10] + out[12] + out[14]
    return out, diag


_P1_CONCEPTS = {"해약환급금준비금": 10, "비상위험준비금": 12, "대손준비금": 14}
# ⚠ **여기에 "보증준비금"을 추가하지 마라.** 같은 절에 「가. 준비금 적립내역[K-IFRS 제1104호
# 기준]」·「라. 책임준비금 적립 내역」 같은 표가 나란히 있는데, 그 표의 `보증준비금` 은
# **책임준비금(보험부채)의 구성요소**이지 이익잉여금 안의 법정준비금이 아니다 -- 다른 개념이다.
# 실측 2026-08-20: 농협생명 FY2026_Q2 는 그 표에 보증준비금 48,412 를 싣는 동시에 주석에서
# "보고기간종료일 현재 보증준비금의 잔액 및 적립예정금액은 **없습니다**" 라고 쓴다. 롯데손해도
# 「라. 책임준비금 적립 내역」의 보증준비금이 0 인데 이건 법정준비금 0 이 아니라 그 개념
# 미공시다. 위 3개 개념은 이 혼동이 없어서(책임준비금 소계 밖의 별도 행) 안전하다.
# 이 표는 "라벨이 개념명과 정확히 일치하는 행"으로만 식별하는데, 그 라벨은 3기간 잔액표
# 말고도 **여러 표에 똑같이 등장한다**. 전 366필링 스캔(2026-08-20) 실측: 후보행 156개 중
# 진짜 3기간표는 소수고 나머지는 ① 이연법인세 증감내역표(5~6셀) ② 준비금 변동표(헤더가
# 기초/증감/기말) ③ 계약유형별 분해표(한화손해 8셀, 천원 단위)였다. 예전엔 "마지막 세 열이
# 전부 숫자"라는 조건이 **우연히** 이것들을 막고 있었는데(변동표는 비교열 자리가 '-'라
# None), 신설제도(해약환급금준비금)의 '-' 비교열을 허용하는 순간 그 방어가 사라져
# KB손해 2021.4Q 해약환급금준비금 737,313 같은 **제도 시행 전 셀**이 생겼다(2026-08-20
# 실측으로 잡음). 그래서 우연한 방어를 표 형태 명시 배제로 바꾼다.
_P1_BAD_CAPTION = ("이연법인세", "일시적차이", "관계기업", "종속기업", "손상차손")
_P1_MOVEMENT_HEADER = ("기초", "기말", "증감", "당기손익", "기타포괄", "사업모형")


def parse_financial_soundness_periods(xml_path: Path):
    """'II. 사업의 내용 -> 5. 재무건전성 등 기타 참고사항' 절의 3기간(당기/전기/전전기) 표
    (owner 2026-08-19, inbox/parser/20260819T0116Z 상단 소스교체 지시). 이 표는 회사마다
    소제목("보험계약자산부채 및 준비금현황"/"준비금 적립내역"/"보험계약부채 및 자산 현황")과
    심지어 ATOC 마크업 유무(메리츠는 <SECTION-2><TITLE ENG="5. Financial soundness...">로
    구조화, 현대해상 라이브 확인: 이 마크업 자체가 파일에 없음 -- TITLE·ENG 태그 0건)까지
    달라서 절 경계를 구조적으로도 찾을 수 없다. 대신 **표 내용 자체**(라벨이 개념명과 정확히
    일치하는 행)로 식별한다 -- 검증: 이 방식으로 메리츠·현대해상 둘 다 정확한 실측치
    (메리츠 3,536,425/2,976,566/1,793,089, 현대해상 4,360,341/3,916,615/4,018,337)를 그대로
    재현했다(둘 다 owner 실측과 바이트 일치).

    각 개념은 이 표에서 [라벨, 당기, 전기, 전전기] 4셀(또는 각주열 포함 5셀 -- 마지막 3개가
    항상 기간값)로 정확히 한 번 나온다. **비교 열은 '-'일 수 있다**(신설 제도) -- 그때는
    None으로 돌려주고 당기만 쓴다. 단위는 이 절의 표준 공시 관행(owner 확인: 표에
    "(단위 : 백만원)" 명시)을 고정값으로 쓴다 -- 대형 필링에서 lxml sourceline이 65535로
    캡돼 역탐색 단위판정이 무의미해지는 문제(item8 _guarantee_scale에서 이미 확인된 것과
    동일 부류)를 이 표에서도 피하려는 것. 결과가 비정상적으로 크면(1억백만원=100조원 초과)
    단위 오판으로 보고 버린다(diag에 기록).

    Returns ({item: (당기, 전기|None, 전전기|None)}, diag)."""
    diag = []
    out: dict[int, tuple[float, float, float]] = {}
    try:
        tables = list(_iter_tables_with_context(xml_path))
    except Exception as e:
        return out, [f"parse EXC {e}"]
    for t in tables:
        cap = (t.caption or "")
        if any(w in cap for w in _P1_BAD_CAPTION):
            continue
        hdr = " ".join(str(h) for h in (t.header or []))
        if any(w in hdr for w in _P1_MOVEMENT_HEADER):
            continue
        for r in t.rows:
            if not r or not r[0]:
                continue
            lab = _strip(r[0])
            item = _P1_CONCEPTS.get(lab)
            # 4셀(라벨+3기간) 또는 각주열 포함 5셀. 그 이상은 3기간표가 아니다.
            if item is None or item in out or not (4 <= len(r) <= 5):
                continue
            vals = [_num(c) for c in r[-3:]]
            # 당기 열만 필수다. 비교 열("전기"/"전전기")이 '-'인 것은 결측이 아니라 **그
            # 개념이 그 시점에 존재하지 않았다**는 뜻이고, 실제로 흔하다 -- 해약환급금준비금은
            # 2023년 신설 제도라 2023년 필링의 전기·전전기 열이 전부 '-'다. 예전엔 세 열이
            # 다 숫자여야 행을 채택해서 **그 행을 통째로 버렸고**, 그래서 현대해상 2023.1Q
            # 해약환급금준비금 4,391,552(원문에 그대로 있음)가 안 잡혀 2023.3Q 값이 뒤로
            # 복사됐다(inbox/parser/20260820T1900Z). 비교 열은 None으로 남겨 호출부가 건너뛴다.
            if vals[0] is None:
                continue
            # 준비금 stock은 음수가 될 수 없다는 원칙(E절, 이 파일의 기존 방어)을 여기도
            # 적용 -- 이 표는 회사가 직접 공시한 잔액 표라 부호 반전 사례는 아직 미확인이지만,
            # 방어 비용이 0에 가까워 그대로 적용.
            vals = [abs(v) if v is not None else None for v in vals]
            if any(v is not None and v > 1e8 for v in vals):
                diag.append(f"{lab}: implausible magnitude {vals}, skipped")
                continue
            out[item] = (vals[0], vals[1], vals[2])
    return out, diag


def _fy_from_dir(raw_base: str):
    m = re.search(r"FY(\d{4})_Q4", raw_base)
    return int(m.group(1)) if m else None


def main():
    rows = json.loads(OUT.read_text(encoding="utf-8"))
    existing_keys = {(r["원보험사코드"], r["공시분기"]) for r in rows}
    LABELS = {1: "자본총계", 6: "기타포괄손익누계액", 10: "해약환급금준비금 기적립액",
              11: "해약환급금준비금 적립(환입)예정액", 12: "비상위험준비금 기적립액",
              13: "비상위험준비금 적립(환입)예정액", 14: "대손준비금 기적립액",
              15: "대손준비금 적립(환입)예정액", 17: "보증준비금 기적립액",
              18: "보증준비금 적립(환입)예정액", 19: "법정준비금 기적립액 합계",
              40: "자산총계", 41: "부채총계"}
    added = 0
    per_company_diag = {}
    for kr, name in TIER2.items():
        by_fy = {}
        for raw_base in sorted(glob.glob(str(ROOT / "data" / "dart" / "FY*_Q4" / "raw"))):
            fy = _fy_from_dir(raw_base)
            if not fy:
                continue
            dirs = sorted(glob.glob(f"{raw_base}/{kr}_*"))
            if not dirs:
                continue
            xmls = []
            for d in dirs:
                xmls.extend(glob.glob(f"{d}/*_00760.xml"))
            if not xmls:
                for d in dirs:
                    xmls.extend(glob.glob(f"{d}/*.xml"))
            if not xmls:
                continue
            xml_path = Path(sorted(xmls, key=os.path.getsize, reverse=True)[0])
            try:
                vals, diag = parse_filing(xml_path)
            except Exception as e:
                per_company_diag.setdefault(kr, []).append(f"{fy}: EXC {e}")
                continue
            if diag:
                per_company_diag.setdefault(kr, []).extend(f"{fy}: {d}" for d in diag)
            if vals:
                by_fy[fy] = vals
        for fy, vals in by_fy.items():
            quarter = f"{fy}.4Q"
            if (kr, quarter) in existing_keys:
                continue
            for item, v in vals.items():
                rows.append({
                    "원보험사코드": kr, "원수사명": name, "티커": TICKER_OF.get(kr),
                    "생손보여부": SB_OF.get(kr), "항목번호": item,
                    "항목명": LABELS.get(item, str(item)), "공시분기": quarter,
                    "값": round(v, 6), "값_당분기": round(v, 6),
                })
                added += 1

    rows.sort(key=lambda r: (r["원보험사코드"], r["항목번호"], r["공시분기"]))
    OUT.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {OUT}: {len(rows)} rows total (+{added} Tier-2 cells)")
    for kr, msgs in per_company_diag.items():
        print(f"  {kr} {TIER2[kr]}: {msgs[:3]}")


if __name__ == "__main__":
    main()
