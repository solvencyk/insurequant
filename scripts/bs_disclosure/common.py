# -*- coding: utf-8 -*-
"""17BS 경영공시 백필 공용 라이브러리 (2026-09-11, inbox/parser/20260911T0109Z).

정기경영공시 raw PDF(data/disclosure/FY*_Q*/{raw,pdf}/*.pdf) 에서 재무상태표(BS) 를 찾아
IFRS17_BS.json 스키마의 항목(1·2·3·4·10·11·12·13·14·15·20·21·22·23·24·30·31)을 뽑는다.
법정준비금 5/6/7/8 은 이미 검증된 scripts/_probes/probe_20260902_surrender_reserve_vs_
disclosure.py 를 그대로 재사용한다(scripts/bs_disclosure/reserve.py 가 얇게 감싼다) --
이 모듈은 코어+세부 항목만 다룬다.

## 설계 원칙 (owner 확정, 되묻지 않음 -- inbox/parser/20260911T0109Z)

- **틀린 값을 싣느니 빈 칸.** 애매하면 skip_reason 을 남기고 넘어간다. 추측·보간 금지.
- **표 고정**: `재무상태표` 신호 AND `비지배지분` 행 부재 AND
  `업무보고서`/`감독회계`/`건전성감독기준`/`시장위험`/`익스포져`/`6-4.` 페이지 마커 부재.
  (생손보 감독규정 별표 서식·시장위험 익스포져 표 decoy 배제 -- 둘 다 `자산총계` 류 행을
  갖고 있어 라벨 매칭만으로는 못 거른다, 조사 20260911 트랩#2/#4.) `운용자산` 행 존재는
  2026-09-11 round2 부터 전면배제가 아니라 **낮은 우선순위 후보**다(`best_bs_table` 참조) --
  일부 회사는 이 서식이 유일한 공시 형식이라 무조건 배제하면 코어까지 통째로 못 뽑는다.
- **열 고정**: 열 위치가 아니라 머리글의 `(당)`/`(전)`/`증감` 마커로 판정한다. 전기(비교)열은
  **소급재작성 위험**이 있어 절대 값으로 쓰지 않는다(농협생명·KR1010·삼성생명 실측 사고,
  조사 20260911 트랩#8). `증감` 열이 있으면 `당기-전기==증감` 자기검산으로 열 매핑 자체를
  검증한다(트랩#1 -- 3열 표를 유량/저량 혼동하는 사고 방지).
- **축척 판정**: 후보 4종(원·천원·백만원·억원)을 전부 계산해 앵커(같은 회사·항목의 가장 가까운
  기존 관측치, 백만원)와 ±50백만원 이내로 맞는 후보가 **정확히 하나**일 때만 채택. 단위 캡션은
  참고만 하고 신뢰하지 않는다(210건 중 87건이 텍스트층에 캡션이 없다, 조사 20260911).
- **항목별 보정 게이트는 호출부(extract_bs_from_disclosure.py) 책임.** 이 모듈은 상태 없는
  순수 함수만 제공한다 -- 회사·항목별로 "Q4 앵커와 같은 방법으로 재현되는지" 확인한 뒤에만
  나머지 분기에 적용하는 로직은 오케스트레이터가 분기를 시간순으로 순회하며 수행한다.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

import fitz  # PyMuPDF

ROOT = Path(__file__).resolve().parents[2]
MASTER = ROOT / "IFRS17_BS.json"

sys.path.insert(0, str(ROOT / "scripts"))
from _disclosure_pdf_paths import disclosure_pdfs, period_of  # noqa: E402  (이미 존재하는 헬퍼)

# ---------------------------------------------------------------------------
# 분기 유틸
# ---------------------------------------------------------------------------


def qkey(q: str) -> tuple[int, int]:
    y, n = q.split(".")
    return int(y), int(n[0])


def qdist(a: str, b: str) -> int:
    ay, an = qkey(a)
    by, bn = qkey(b)
    return abs((ay * 4 + an) - (by * 4 + bn))


def pick_pdf(quarter: str, kr: str) -> Path | None:
    """해당 (회사,분기) 의 경영공시 PDF 하나를 고른다. 원본·정정본(_amended) 이 공존하면
    정정본을 우선한다 -- 정정본이 최신 확정치라는 가장 안전한 기본값이다(조사 20260911
    트랩#12: 이 저장소에 버전 병존 정책이 아직 없어 이번 백필에서 새로 정하지 않고 최소
    위험 선택만 한다). `disclosure_pdfs()`가 raw/ 우선, 없으면 pdf/ 를 본다(기존 계약)."""
    pdfs = disclosure_pdfs(period_of(quarter), kr)
    if not pdfs:
        return None
    amended = [p for p in pdfs if "amended" in p.stem]
    return amended[-1] if amended else pdfs[-1]


def sha256_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


# ---------------------------------------------------------------------------
# 마스터 인덱스 (축척 판정·QoQ·보정게이트의 앵커)
# ---------------------------------------------------------------------------


# 앵커/QoQ 판정에서 절대 쓰면 안 되는 분기(owner 확정, 되묻지 않음: IFRS4<->IFRS17 경계).
# 백필 대상에서만 빼는 게 아니라 -- **참조값(anchor)으로도 쓰면 안 된다.** 실측(2026-09-11,
# 첫 실행): KR1010 자본총계가 2022.4Q(35,460백만) -> 2023.1Q(103,768백만) 로 튀는데, 이건
# 2023.1Q 가 잘못 읽힌 게 아니라 2022.4Q 쪽이 **아직 IFRS4 기준이라 비교 기준 자체가 다르다**
# (티켓 실측: KR0051 도 이 경계에서 자본 +10,328백만 가짜 점프). 이 두 분기를 앵커 후보에서
# 빼지 않으면 2023.1Q 가 QoQ 게이트에 걸려 정상 값이 hold 된다.
ANCHOR_FORBIDDEN_QUARTERS = frozenset({"2021.4Q", "2022.4Q"})


def load_master_index() -> dict[tuple[str, int], dict[str, float]]:
    rows = json.loads(MASTER.read_text(encoding="utf-8"))
    idx: dict[tuple[str, int], dict[str, float]] = {}
    for r in rows:
        kr, item, q, v = (r.get("원보험사코드"), r.get("항목번호"),
                          r.get("공시분기"), r.get("값"))
        if kr is None or item is None or q is None or v is None or q in ANCHOR_FORBIDDEN_QUARTERS:
            continue
        idx.setdefault((kr, item), {})[q] = v
    return idx


def nearest_known(known: dict[tuple[str, int], dict[str, float]], kr: str, item: int,
                   quarter: str) -> tuple[float, str] | None:
    """(값, 그 분기) -- 같은 (회사,항목) 에서 quarter 와 가장 가까운(자기 자신 제외) 관측치.
    방향 무관 -- QoQ 게이트처럼 "직전·직후 양쪽 다 확인" 이 필요하면 `nearest_before`/
    `nearest_after` 를 대신 쓸 것(2026-09-11 round2: 이 함수 하나만 쓰면 두 방향 중 더 가까운
    쪽만 보게 돼, 유상증자처럼 계단식으로 뛴 값을 "먼(하지만 맞는) 방향" 앵커로 검증할
    기회를 놓친다)."""
    d = known.get((kr, item)) or {}
    best = None
    best_dist = None
    for q, v in d.items():
        if q == quarter:
            continue
        dist = qdist(q, quarter)
        if best_dist is None or dist < best_dist:
            best, best_dist = (v, q), dist
    return best


def nearest_before(known: dict[tuple[str, int], dict[str, float]], kr: str, item: int,
                    quarter: str) -> tuple[float, str] | None:
    """(값, 그 분기) -- quarter 보다 엄격히 이전인 관측치 중 가장 가까운 것."""
    d = known.get((kr, item)) or {}
    best = None
    best_dist = None
    for q, v in d.items():
        if qkey(q) >= qkey(quarter):
            continue
        dist = qdist(q, quarter)
        if best_dist is None or dist < best_dist:
            best, best_dist = (v, q), dist
    return best


def nearest_after(known: dict[tuple[str, int], dict[str, float]], kr: str, item: int,
                   quarter: str) -> tuple[float, str] | None:
    """(값, 그 분기) -- quarter 보다 엄격히 이후인 관측치 중 가장 가까운 것."""
    d = known.get((kr, item)) or {}
    best = None
    best_dist = None
    for q, v in d.items():
        if qkey(q) <= qkey(quarter):
            continue
        dist = qdist(q, quarter)
        if best_dist is None or dist < best_dist:
            best, best_dist = (v, q), dist
    return best


# ---------------------------------------------------------------------------
# 숫자 파싱
# ---------------------------------------------------------------------------

_DASH_ONLY = {"-", "－", "‐", "—", "–", ""}


def parse_number(cell) -> float | None:
    """콤마·괄호(음수)·대시(결측)·△(음수, 한국 회계 관행) 처리. 원문 그대로의 raw 값(단위
    불명)을 돌려준다."""
    if cell is None:
        return None
    s = str(cell).strip().replace("　", "").replace(" ", "")
    if s in _DASH_ONLY:
        return None
    neg = False
    if (s.startswith("(") and s.endswith(")")) or (s.startswith("（") and s.endswith("）")):
        neg = True
        s = s[1:-1]
    # "△244,064,855,740" 류 -- 괄호가 아니라 세모(△)로 음수를 표기하는 한국 회계 관행
    # (실측 2026-09-11 round2, KR0004 2025.1Q '자본 총계' 행: 이걸 못 걸러 float() 변환이
    # ValueError 로 죽고 그 행 전체가 조용히(스킵 사유 없이) 통째로 유실됐다 -- 항목이 음수인
    # 분기마다 재발할 수 있는 구조적 함정).
    if s.startswith("△") or s.startswith("▲"):
        neg = True
        s = s[1:]
    s = s.replace(",", "")
    if not s or s in _DASH_ONLY:
        return None
    try:
        v = float(s)
    except ValueError:
        return None
    return -v if neg else v


# ---------------------------------------------------------------------------
# 라벨 정규화 + 항목 매칭
# ---------------------------------------------------------------------------

# 앞자리 순번(아라비아/로마자 ASCII/유니코드 로마숫자 Ⅰ-Ⅹ) 제거. 자간 붕괴 후에 적용한다.
_NUM_PREFIX_RE = re.compile(r'^(?:[0-9]{1,3}|[IVXLCivxlc]{1,4}|[Ⅰ-Ⅹ]{1,2})[.)]\s*')
_FOOTNOTE_RE = re.compile(r'주\d+\)$')


_BRACKET_CHARS = "【】〔〕[]"  # 실측(삼성생명 2023.1Q): 총계 행이 "【자 산 총 계】"로 CJK
# 렌티큘러 괄호에 싸여 나온다 -- 안 벗기면 "자산총계"와 정확일치가 영원히 안 된다.


def clean_label(s: str) -> str:
    """자간(모든 공백류) 붕괴 + 앞자리 순번/꼬리 각주/총계행 감싸는 괄호 제거. 정확일치
    매칭이 decoy 를 더 잘 고르는 함정이 있어(조사 20260911 트랩#6) 자간만 관대하게 받고
    나머지는 엄격하게 둔다."""
    t = "".join(str(s or "").split())
    for c in _BRACKET_CHARS:
        t = t.replace(c, "")
    t = _NUM_PREFIX_RE.sub("", t)
    t = _FOOTNOTE_RE.sub("", t)
    return t


LABEL_VARIANTS: dict[int, tuple[str, ...]] = {
    1: ("자산총계",),
    2: ("부채총계",),
    3: ("자본총계",),
    4: ("기타포괄손익누계액", "기타자본구성요소"),  # 한화생명·흥국생명 실측(build_ifrs17_bs.py
        # AOCI_FALLBACK_ID 와 동일 근거) -- 표준태그 대신 이 라벨로 AOCI 를 싣는다
    10: ("현금및현금성자산", "현금및예치금", "현금및현금성자산등"),
    11: ("당기손익-공정가치측정금융자산", "당기손익-공정가치측정유가증권",
         "당기손익공정가치측정금융자산", "당기손익공정가치측정유가증권",
         "당기손익인식금융자산"),  # IBK연금 실측(2026-09-11): "인식"="공정가치측정" 변형
    12: ("기타포괄손익-공정가치측정금융자산", "기타포괄손익-공정가치측정유가증권",
         "기타포괄손익공정가치측정금융자산", "기타포괄손익공정가치측정유가증권",
         "기타포괄손익인식금융자산"),  # 위와 동일 변형
    # 13(상각후원가측정금융자산)은 부모/자식 혼재라 아래 AMORT_* 로 별도 처리한다.
    14: ("재보험계약자산",),
    15: ("유형자산",),
    20: ("보험계약부채",),
    21: ("재보험계약부채",),
    22: ("투자계약부채",),
    23: ("차입부채", "차입금"),
    24: ("기타부채",),
    30: ("자본금",),
    31: ("이익잉여금", "결손금", "미처리결손금"),
}
CORE_ITEMS = (1, 2, 3, 4)
AMORT_COST_PARENT = "상각후원가측정금융자산"
AMORT_COST_CHILD_PREFIX = "상각후원가측정"
# 항목13(상각후원가측정금융자산)의 '자식 중 하나만' 마스터 관행인 회사가 있다(조사 20260911
# 실측: "KR1010 마스터는 대출채권 계열"). 부모/전체합만으로는 못 맞히므로 종류별로도 후보를
# 만든다 -- 라벨에 이 마커가 있으면 그 종류로 묶는다(회사마다 "대출채권"/"수취채권" 앞에
# 붙는 수식어가 달라 정확일치 대신 부분일치로 넓게 잡는다).
AMORT_CHILD_KIND_MARKERS = ("대출채권", "유가증권", "수취채권", "미수금", "기타")

_LABEL_TO_ITEM = {v: item for item, variants in LABEL_VARIANTS.items() for v in variants}


def match_item(label: str) -> int | None:
    return _LABEL_TO_ITEM.get(label)


# ---------------------------------------------------------------------------
# 표 탐색 + 자격 판정 (표 고정)
# ---------------------------------------------------------------------------

# 이 마커가 페이지 텍스트에 있으면 그 페이지는 BS 후보에서 제외한다 -- 감독규정 별표(업무보고서
# 기준) 요약표·시장위험 익스포져 표 decoy(조사 20260911 트랩#2/#4). 둘 다 "자산총계" 류 행이
# 있어 라벨 매칭만으로는 못 거른다.
EXCLUDE_PAGE_MARKERS = (
    "업무보고서 기준으로 작성", "감독회계기준", "건전성감독기준", "요약재무상태표",
    "시장위험", "익스포져", "6-4.",
    # 실측 2026-09-11 (KR0051 2023.4Q): 연차(Q4) 공시 본문이 "감사보고서, 재무상태표, ...
    # 등은 첨부파일 참조"라고만 쓰고 실제 표는 없는데, "재무상태표" 라는 단어 자체가 이
    # 안내문에 들어 있어 후보페이지 필터를 통과했다. 그 페이지의 다른 표(금융상품 note 등)가
    # 우연히 "당기/전기" 헤더를 가져 오분류될 뻔했다 -- 명시적으로 배제.
    "첨부파일 참조",
)
# "6-4"(마침표 없이)는 2026-09-11 round2 실측(AIG손해 2026.1Q p24)으로 오탐이 확인됐다 --
# "...12,374,206" (당기값) 바로 뒤에 "-4,558,932"(음수 증감값)가 공백 없이 이어 붙으면
# "206-4,558,932" 안에 우연히 "6-4" 부분문자열이 생긴다(숫자 조판 우연 -- 섹션번호와 무관).
# 진짜 "6-4. 시장위험 관리" 절 번호는 마침표가 붙으므로 그것만 요구하도록 좁혔다.


def _compact(txt: str) -> str:
    return txt.replace("\n", "").replace(" ", "").replace("　", "")


def iter_candidate_pages(pdf_path: Path):
    """(page_index, page_text) -- '재무상태표' 신호가 있고 decoy 마커가 없는 페이지만."""
    doc = fitz.open(pdf_path)
    try:
        for i, page in enumerate(doc):
            txt = page.get_text()
            compact = _compact(txt)
            if "재무상태표" not in compact:
                continue
            # 마커 상수 자체에 공백이 들어있어("첨부파일 참조" 등, 소스 가독성 때문) compact
            # 텍스트(공백 전부 제거)와 직접 비교하면 절대 안 걸린다 -- 마커도 같이 compact
            # 해야 매칭된다(버그 실측 2026-09-11 round2: 하나손해 2023.1Q p15 "...등은
            # 첨부파일 참조."가 compact 후 "첨부파일참조"가 되는데 마커는 공백 포함 그대로라
            # 이 결정적 decoy 배제 신호가 조용히 무력화돼 있었다).
            if any(_compact(m) in compact for m in EXCLUDE_PAGE_MARKERS):
                continue
            yield i, txt
    finally:
        doc.close()


def find_tables_on_page(pdf_path: Path, page_index: int):
    """해당 페이지의 fitz 구조화 표(rows 리스트)들을 돌려준다. 범위 밖(문서 끝 다음 페이지를
    이어짐 후보로 확인하려다 넘어가는 경우, `_continuation_rows` 실측 2026-09-11)이면 빈
    리스트 -- 조용히 통과시킨다(이어짐이 없다는 뜻일 뿐 오류가 아니다)."""
    doc = fitz.open(pdf_path)
    try:
        if not (0 <= page_index < doc.page_count):
            return []
        page = doc[page_index]
        try:
            tabs = page.find_tables()
        except Exception:
            return []
        out = []
        for t in tabs.tables:
            try:
                rows = t.extract()
            except Exception:
                continue
            out.append(rows)
        return out
    finally:
        doc.close()


def qualify_table(rows: list[list],
                   groups: dict[str, tuple[int, int]] | None = None) -> tuple[bool, str, bool]:
    """(ok, reason, is_regulatory_form). '별도재무상태표' 신호는 페이지 텍스트에서 별도로
    확인(caller) -- 여기서는 표 구조 자체(비지배지분 부재·총계 3종 존재)만 본다.

    **라벨 칸만** 본다 -- 행 전체를 이어붙이면 총계 행의 숫자까지 라벨 문자열에 달라붙어
    "자산총계683,734,..." 처럼 정확일치가 깨진다(2026-09-11 첫 실행에서 실측한 버그: KR1010
    2023.1Q 별도표가 이 때문에 자산총계 행 없음으로 오판됐다).

    `운용자산` 행 존재는 **더 이상 전면 배제가 아니다**(2026-09-11 round2 실측: AIG손해
    2023.1Q -- 이 서식뿐인 표가 자산총계=부채총계+자본총계 항등식 0 이탈로 정확했다). 원래
    의도(생손보 감독규정 별표·시장위험 익스포져 표 decoy 배제, 트랩#2/#4)는 이미 페이지 레벨
    `EXCLUDE_PAGE_MARKERS`(요약재무상태표/6-4/시장위험/익스포져 등)가 잡는다 -- 이 표 레벨
    체크는 "같은 PDF 안에 더 나은(비-운용자산) 별도표가 있으면 그쪽을 우선"하는 **낮은 우선
    순위 신호**로 다운그레이드한다(`best_bs_table` 이 처리). 세부항목(10~31)의 안전장치는
    여전히 `calibrate_detail_items` 의 Q4 재현검사가 담당하므로 이 표만 있어도 안전하다."""
    label_span = (groups or {}).get("라벨")
    labels = []
    for r in rows:
        raw = "".join(str(c) for c in r[label_span[0]:label_span[1]] if c) if label_span \
            else "".join(str(c) for c in r if c)
        lbl = clean_label(raw)
        if lbl:
            labels.append(lbl)
    if any(l == "비지배지분" or l.startswith("비지배지분") for l in labels):
        return False, "비지배지분 행 존재 -- 연결재무상태표로 판정, 별도만 채택", False
    is_reg_form = any(l == "운용자산" for l in labels)
    if "자산총계" not in labels:
        return False, "자산총계 행 없음 -- BS 표 아님", False
    if "부채총계" not in labels:
        return False, "부채총계 행 없음 -- BS 표 아님", False
    if "자본총계" not in labels:
        return False, "자본총계 행 없음 -- BS 표 아님", False
    return True, "ok", is_reg_form


def page_is_consolidated(page_text: str) -> bool | None:
    """True=연결, False=별도, None=신호 없음(단일표 회사 -- 표 구조의 비지배지분 부재로 이미
    걸러졌으므로 별도로 취급해도 안전).

    "별도"/"연결" 가 "재무상태표" **뒤에** 오는 표제도 받는다(실측 2026-09-11 round2,
    AIG손해 2026.1Q p24/25: 소제목이 "재무제표.Ⅷ재무상태표별도"/"...재무상태표연결" 순으로
    추출된다 -- PDF 내부적으로 "(별도)"/"(연결)" 괄호수식어가 별개 텍스트런이라 fitz 추출
    순서가 시각적 순서와 다르다). 순서를 안 가리면 둘 다 신호없음(None)으로 떨어져
    최악의 경우 연결표를 별도표로 오인할 위험이 있었다."""
    has_yeon = "연결재무상태표" in page_text or "재무상태표연결" in page_text
    has_byeoldo = "별도재무상태표" in page_text or "재무상태표별도" in page_text
    if has_yeon and not has_byeoldo:
        return True
    if has_byeoldo:
        return False
    return None


# ---------------------------------------------------------------------------
# 열 고정 (머리글 기수 표기로 당기/전기/증감 열 판정)
# ---------------------------------------------------------------------------


_YEAR_RE = re.compile(r'(20\d\d)\s*년')
# 2자리 연도 축약 표기 'NN년도' (AIG 실측 2026-09-11: '23년도 1/4분기'/'22년도 4/4분기' -- 4자리
# 연도가 전혀 없는 회사가 있다). `(?<!\d)` 로 4자리 연도의 뒷 2자리('2023년도'의 '23')를
# 오매칭하지 않도록 막는다 -- 그 경우 바로 앞이 숫자('0')라 lookbehind 가 막는다.
_YEAR2_RE = re.compile(r'(?<!\d)(\d{2})년도')
# 당기(현재기간) 마커 -- 회사마다 표기가 갈린다(실측 2026-09-11, round2 백필): 순수 '당기'
# 뿐 아니라 '당분기'/'당기말'/'당분기말'/'해당분기' 도 전부 "현재기간" 을 가리키는 동의어다.
# 기존엔 '당기' 리터럴만 봐서 '당분기'(당+분기, '당기' 부분문자열이 아니다)를 놓쳤다 --
# 악사손해 다수 분기가 이 때문에 헤더 인식 자체가 실패했다.
_CUR_WORD_RE = re.compile(r'(?<![가-힣])(당분기말|당분기|당기말|해당분기|당기)(?![가-힣])')
_PREV2_WORD_RE = re.compile(r'(?<![가-힣])(전전기|전전분기|전전년)(?![가-힣])')
# "전년동기"(작년 같은 기간)처럼 숫자 연도가 안 박힌 비교열 표기까지 넓게 잡는다(실측
# 2026-09-11: 삼성생명 2023.1Q 헤더가 '2023년1/4분기 | 전년동기 | 증감' -- 비교열엔 연도
# 숫자가 아예 없다. 전기 판정을 연도매칭에만 의존하면 이런 표를 통째로 못 잡는다).
# '전기기말'(악사손해 2025.2Q 실측)도 '전기말'과 다른 리터럴이라 별도로 추가.
_PREV_WORD_RE = re.compile(r'(?<![가-힣])(전년동기|전년말|전기기말|전기말|전분기말|직전분기|전분기|'
                           r'전기|전년)(?![가-힣])')


def _classify_header_cell(text: str) -> str | None:
    """헤더 칸 하나 -> '당기'/'전기'/'전전기'/'증감'/None. 괄호 마커(`(당)`/`(전)`)를
    최우선으로, 그 다음 바레 단어(`당기`/`전년동기` 등)를 본다 -- 트랩#8(전기 비교열을
    당기로 오인 금지) 은 이 함수 하나로 전부 처리한다."""
    if "(당)" in text:
        return "당기"
    if "(전전)" in text or _PREV2_WORD_RE.search(text):
        return "전전기"
    if "(전)" in text:
        return "전기"
    if _CUR_WORD_RE.search(text):
        return "당기"
    if _PREV_WORD_RE.search(text):
        return "전기"
    if "증감" in text:
        return "증감"
    return None


def _find_header_row(rows: list[list], marker_fn) -> list | None:
    """마커가 있고 **머리글로 쓸 수 있는(열 경계가 2개 이상)** 첫 행을 고른다. 처음 3행이
    아니라 6행까지 보는 이유(실측 2026-09-11, AIA생명 KR0080): 일부 회사는 실제 열 헤더 앞에
    '제N(당)기 ... 현재'/'제N(전)기 ... 현재' 라는 별도 타이틀행 2개(그 자체로 '(당)'/'(전)'
    마커를 포함하지만 칸이 통째로 병합돼 있어 라벨/당기/전기 열 경계를 못 만든다) + 빈 행까지
    최대 3행이 낀다. 마커 매치만 보면 이 타이틀행을 헤더로 잘못 고르고 그 자리에서 멈춰(spans
    가 0~1개라 `header_groups` 가 그 시도를 포기) 진짜 헤더행(4번째)까지 못 간다 -- 그래서
    마커뿐 아니라 `_spans_of` 로 실제 열 경계(>=2)가 나오는 행인지까지 같이 본다."""
    for candidate in rows[:6]:
        if any(c and marker_fn(str(c)) for c in candidate) and len(_spans_of(candidate)) >= 2:
            return candidate
    return None


def _spans_of(header: list) -> list[tuple[int, int, str]]:
    n = len(header)
    boundaries = [j for j, c in enumerate(header) if c and str(c).strip() not in ("", "　")]
    if len(boundaries) < 2:
        return []
    spans = []
    for bi, j in enumerate(boundaries):
        end = boundaries[bi + 1] if bi + 1 < len(boundaries) else n
        spans.append((j, end, str(header[j])))
    return spans


def header_groups(rows: list[list]) -> dict[str, tuple[int, int]] | None:
    """헤더행에서 당기/전기/증감 열의 [시작,끝) 범위를 잡는다. 열 위치가 아니라 머리글
    문자열로 판정한다(트랩#8: 전기 비교열을 당기로 오인하면 소급재작성 값이 들어간다).

    헤더가 항상 0행은 아니다 -- 실측(2026-09-11, KR1010 2026.1Q): 회사명+단위캡션 행이
    표 구조에 0행으로 딸려 들어오고 실제 헤더행은 1행이다. 그래서 처음 3행 중 마커가 있는
    첫 행을 헤더로 삼는다.

    회사마다 당기 마커 표기가 세 갈래다(실측, `_classify_header_cell` 이 전부 처리):
      1순위 `제N(당)기...`/맨 `당기` (괄호 유무 무관) -- 가장 흔함, 비교열은 `(전)`/`전기`/
      `전년동기`류.
      2순위 역년(曆年) `2023년도`/`2023년1/4분기`(AIG·삼성생명 실측) -- 당기열에만 연도
      숫자가 박히고 비교열은 숫자 없이 `전년동기` 류 단어만 쓰는 경우가 있어, 당기는 연도
      숫자로 비교열은 `_classify_header_cell`(전기류 단어)로 각각 잡는다.
    """
    if not rows:
        return None

    header = _find_header_row(rows, lambda s: _classify_header_cell(s) == "당기")
    if header is not None:
        spans = _spans_of(header)
        if spans:
            label_end, rest = _pad_shift(spans)
            out: dict[str, tuple[int, int]] = {"라벨": (0, label_end)}
            for j, end, text in rest:
                kind = _classify_header_cell(text)
                if kind and kind not in out:
                    out[kind] = (j, end)
            if "당기" in out:
                return out

    # 2순위: 역년(4자리) 표기. 당기 열은 더 큰 연도 숫자로, 비교열은 숫자 없이
    # `_classify_header_cell` 이 잡는 전기류 단어로 -- 반드시 둘 다 있어야 채택한다(비교열을
    # 못 찾으면 열 매핑을 신뢰할 수 없다, 트랩#8과 같은 이유).
    out = _year_based_header_groups(rows, _YEAR_RE)
    if out is not None:
        return out

    # 3순위: 역년(2자리 축약, 'NN년도') 표기 -- AIG 실측(2026-09-11 round2): 4자리 연도가
    # 전혀 없는 회사가 있다. 로직은 2순위와 동일(연도 큰 쪽이 당기), 정규식만 다르다.
    out = _year_based_header_groups(rows, _YEAR2_RE)
    if out is not None:
        return out

    return None


def _pad_shift(spans: list[tuple[int, int, str]]) -> tuple[int, list[tuple[int, int, str]]]:
    """(라벨_end, 이후_spans) -- 일부 표는 헤더 텍스트가 데이터보다 그리드 1칸(이상) 뒤에
    앉는다(실측 2026-09-11 round2: 악사손해·AIA생명 -- 헤더 '과목'은 col1 에, 데이터 라벨은
    col0 에; 헤더 '제N(당)기'는 col4, 데이터 당기값은 col3. 병합폭 안에서 헤더 텍스트가
    오른쪽으로 밀려 찍히는데 본문 값은 왼쪽 정렬이라 생기는 어긋남). 헤더의 첫 칸(라벨)
    자체가 0열에서 시작하지 않으면(=앞에 빈 패딩열이 있으면) 그 폭(`pad`)만큼 모든 경계를
    왼쪽으로 당겨 데이터 열과 맞춘다. 패딩이 없는(가장 흔한) 표는 pad=0 이라 항등 -- 회귀
    위험 없음. 이 보정을 안 하면 라벨 칸에 다음 칸(당기값)까지 섞여 들어가 정확일치 매칭이
    깨지고, 당기/전기/증감 칸은 하나씩 밀려 서로 바뀐 값을 읽는다."""
    pad = spans[0][0]
    label_end = spans[0][1] - pad
    rest = [(j - pad, end - pad, text) for j, end, text in spans[1:]]
    return label_end, rest


def _year_based_header_groups(rows: list[list], year_re: "re.Pattern[str]") -> dict[str, tuple[int, int]] | None:
    """연도 숫자 기반 열 판정 공용 로직(4자리 `_YEAR_RE`/2자리 `_YEAR2_RE` 공통)."""
    header = _find_header_row(rows, lambda s: year_re.search(s) is not None)
    if header is None:
        return None
    spans = _spans_of(header)
    year_spans = [(j, end, int(year_re.search(text).group(1)))
                  for j, end, text in spans if year_re.search(text)]
    if not year_spans:
        return None
    year_spans.sort(key=lambda t: -t[2])   # 최신 연도(당기) 먼저
    pad = spans[0][0]
    label_end = min(j for j, _e, _y in year_spans) - pad
    out: dict[str, tuple[int, int]] = {"라벨": (0, label_end),
                                        "당기": (year_spans[0][0] - pad, year_spans[0][1] - pad)}
    if len(year_spans) >= 2:
        out["전기"] = (year_spans[1][0] - pad, year_spans[1][1] - pad)
    if len(year_spans) >= 3:
        out["전전기"] = (year_spans[2][0] - pad, year_spans[2][1] - pad)
    for j, end, text in spans:
        j, end = j - pad, end - pad
        kind = _classify_header_cell(text)
        if kind and kind not in out:
            out[kind] = (j, end)
    if "당기" in out and "전기" in out:
        return out
    return None


def cell_value(row: list, span: tuple[int, int]) -> float | None:
    j0, j1 = span
    for j in range(j0, min(j1, len(row))):
        v = parse_number(row[j])
        if v is not None:
            return v
    return None


def row_label(row: list, label_span: tuple[int, int]) -> str:
    j0, j1 = label_span
    parts = [str(c).strip() for c in row[j0:min(j1, len(row))]
             if c and str(c).strip() not in ("", "　")]
    return clean_label("".join(parts))


def qoq_column_self_check(rows: list[list], groups: dict[str, tuple[int, int]]) -> bool:
    """증감 열이 있으면 당기-전기==증감 자기검산으로 열 매핑을 검증한다(트랩#1: 3열 표
    유량/저량 혼동 방지). 검산 대상 행이 없으면(비교 불가) 통과로 둔다."""
    if "증감" not in groups or "전기" not in groups:
        return True
    checks = ok = 0
    for row in rows[1:]:
        a = cell_value(row, groups["당기"])
        b = cell_value(row, groups["전기"])
        c = cell_value(row, groups["증감"])
        if a is None or b is None or c is None:
            continue
        checks += 1
        if abs((a - b) - c) <= max(1.0, abs(a) * 0.001):
            ok += 1
    if checks == 0:
        return True
    return (ok / checks) >= 0.8


def extract_row_values(rows: list[list], groups: dict[str, tuple[int, int]]) -> dict:
    """표 하나에서 항목별 당기 raw 값(단위 불명, 원문 그대로) + 상각후원가측정 부모/자식
    후보. 축척 판정은 호출부가 앵커로 한다."""
    label_span, val_span = groups["라벨"], groups["당기"]
    out: dict[int, float] = {}
    amort_parent = None
    amort_children: dict[str, float] = {}   # 라벨 -> raw값. 개별 후보로도 검사한다(트랩:
    # 항목13은 "부모" 도, "자식 합" 도 아니고 **자식 중 하나만**(예: 대출채권 계열)이 마스터
    # 관행인 회사가 있다 -- 티켓 실측 "KR1010 마스터는 대출채권 계열").
    for row in rows[1:]:
        label = row_label(row, label_span)
        if not label:
            continue
        val = cell_value(row, val_span)
        if val is None:
            continue
        item = match_item(label)
        if item is not None:
            out.setdefault(item, val)
            continue
        if label == AMORT_COST_PARENT:
            amort_parent = val
        elif label.startswith(AMORT_COST_CHILD_PREFIX):
            amort_children[label] = amort_children.get(label, 0.0) + val
    amort_children_sum = sum(amort_children.values()) if amort_children else None
    return {"items": out, "amort_parent": amort_parent,
            "amort_children_sum": amort_children_sum, "amort_children": amort_children}


def amort_candidates(extracted: dict) -> dict[str, float]:
    """항목13 후보: 'parent' / 'children_sum' / 'child:<종류>' -> raw 값(단위 불명).
    부모행·전체합·종류별 부분합을 전부 후보로 낸다(회사마다 마스터 관행이 다르므로 -- 조사
    20260911)."""
    cands: dict[str, float] = {}
    if extracted.get("amort_parent") is not None:
        cands["parent"] = extracted["amort_parent"]
    if extracted.get("amort_children_sum") is not None:
        cands["children_sum"] = extracted["amort_children_sum"]
    children = extracted.get("amort_children") or {}
    for marker in AMORT_CHILD_KIND_MARKERS:
        total = sum(v for lbl, v in children.items() if marker in lbl)
        if total:
            cands.setdefault(f"child:{marker}", total)
    return cands


# ---------------------------------------------------------------------------
# 축척 판정 + 게이트
# ---------------------------------------------------------------------------

SCALE_CANDIDATES = {"원": 1e-6, "천원": 1e-3, "백만원": 1.0, "억원": 100.0}
# 앵커(같은 회사·항목의 가장 가까운 "다른 분기" 관측치) 대비 후보값의 배수가 이 구간 안이어야
# 채택한다. **티켓 원문의 "±50백만원"을 그대로 쓰지 않았다 -- 실측(2026-09-11, KR1010
# 2023.1Q)으로 이유가 확인됐다**: ±50백만원은 같은 분기를 두 원천(DART 주석 vs 경영공시)으로
# 대조할 때(법정준비금 P1 축, ABS_TOL_MILLION)처럼 "사실상 같은 수"를 비교하는 데 맞춘 값이다.
# 여기서는 **인접 분기**(자산총계 같은 저량은 분기마다 실질적으로 움직인다)를 앵커로 쓰므로
# 그 절대오차를 그대로 적용하면 정상 성장조차 걸린다 -- KR1010 은 2022.4Q->2023.1Q 자산총계가
# 642,566->683,735백만원(+6.4%, 41,168백만원 증가)으로 정상 성장했는데 ±50백만원 기준으로는
# "정합 후보 0개"가 돼 첫 분기부터 전부 스킵됐다. 대신 **후보 4종이 서로 100~1000배 차이**라는
# 사실을 쓴다 -- 아무리 급성장해도 분기당 5배(500%) 넘게 뛰는 보험사는 없으므로, 이 폭으로도
# 자릿수 오류(스케일 오판)와 정상 변동은 절대 안 섞인다.
SCALE_BAND = (0.2, 5.0)
IDENTITY_TOL_REL = 0.001
IDENTITY_TOL_ABS = 1.0     # 백만원 -- 게이트(IFRS17_BS_TOL_ABS)와 동일 기준
QOQ_TOL_REL = 0.30


def resolve_scale(raw_value: float, anchor_mn: float | None) -> tuple[float, str] | None:
    """raw_value(단위 불명) -> (백만원값, 후보단위이름) 또는 None(스킵). anchor_mn 없으면
    판정 불가. raw_value==0 은 축척 무관하게 0 으로 확정(모든 후보가 0 이라 모호하지 않다)."""
    if raw_value == 0:
        return 0.0, "영값(축척무관)"
    if not anchor_mn:
        return None
    lo, hi = SCALE_BAND
    hits = []
    for unit, factor in SCALE_CANDIDATES.items():
        v = raw_value * factor
        ratio = v / anchor_mn
        if lo <= ratio <= hi:
            hits.append((v, unit))
    return hits[0] if len(hits) == 1 else None


def resolve_table_scale(items_raw: dict[int, float],
                         known: dict[tuple[str, int], dict[str, float]],
                         kr: str, quarter: str) -> tuple[float, str, int] | None:
    """표 하나는 단위가 하나다 -- 항목마다 따로 축척을 추정하지 않고, 항목1(안 되면 2, 3)의
    raw 값을 그 회사의 가장 가까운 기존 관측치와 맞춰 **표 전체의 배율**을 한 번만 정한다.
    반환 (배율, 후보단위이름, 앵커로 쓴 항목번호) 또는 None(세 항목 다 판정 불가 -- 표 스킵)."""
    for anchor_item in (1, 2, 3):
        raw = items_raw.get(anchor_item)
        if raw is None:
            continue
        nk = nearest_known(known, kr, anchor_item, quarter)
        if nk is None:
            continue
        anchor_mn, _anchor_q = nk
        resolved = resolve_scale(raw, anchor_mn)
        if resolved is not None:
            value_mn, unit = resolved
            factor = value_mn / raw if raw else 0.0
            return factor, unit, anchor_item
    return None


MAX_CONTINUATION_PAGES = 8
# 처브라이프(KR0100, 감독규정 별표 간이분기 서식)는 자산총계(1p)->부채총계(4p)->자본총계(5p)
# ->부채와자본총계(6p) 로 표 하나가 **6페이지**에 걸친다(실측 2026-09-11 round2). 넉넉히
# 잡되 무한정은 아니다 -- 그 뒤 페이지는 무관한 주석표(같은 3열 구조)로 이어지므로 상한이
# 있어야 엉뚱한 내용까지 계속 흡수하지 않는다.


def _continuation_page_rows(pdf_path: Path, page_idx: int, ncols: int,
                             groups: dict[str, tuple[int, int]] | None) -> list[list]:
    """한 페이지 안의, 이어지는 열 구조와 맞는 표(들)의 데이터행을 순서대로 모아 돌려준다
    (표 하나가 페이지 안에서도 여러 fitz 표 객체로 쪼개지는 경우가 있다 -- 실측 2026-09-11
    round2, 처브라이프: 이어지는 각 페이지가 table0/table1 두 조각으로 나온다). 못 찾으면 [].

    열 수가 원표와 다른 이어짐도 받는다(실측: AIA생명 KR0080 2024.1Q -- 원표는 9열(패딩
    포함)인데 이어지는 페이지는 헤더가 없어 fitz 가 패딩 없는 3열[라벨/당기/전기]로 다시
    그리드화한다). `groups` 의 논리 열 개수(라벨/당기/전기[/증감])와 정확히 일치하면 그
    순서로 보고 원표의 실제 칼럼 인덱스에 재배치한다 -- 순서·의미는 같고 패딩만 다른
    경우이므로 안전하다."""
    out: list[list] = []
    order = [k for k in ("라벨", "당기", "전기", "증감") if k in groups] if groups else []
    for rows in find_tables_on_page(pdf_path, page_idx):
        if not rows:
            continue
        if len(rows[0]) == ncols:
            piece = rows[1:] if any(c and "(당)" in str(c) for c in rows[0]) else rows
            out.extend(piece)
        elif order and rows[0] and len(rows[0]) == len(order):
            start = 1 if any(c and "(당)" in str(c) for c in rows[0]) else 0
            for row in rows[start:]:
                newrow: list = [None] * ncols
                for pos, key in enumerate(order):
                    j0 = groups[key][0]
                    if j0 < ncols:
                        newrow[j0] = row[pos] if pos < len(row) else None
                out.append(newrow)
    return out


def _continuation_rows(pdf_path: Path, page_idx: int, ncols: int,
                        groups: dict[str, tuple[int, int]] | None = None) -> list[list] | None:
    """표가 페이지 경계에서 잘렸을 수 있다(실측 2026-09-11: AIA생명 2023.4Q 별도BS 는 36행에서
    끊기고 다음 페이지가 '과목/제N(당)기말/...' 헤더를 반복한 뒤 '5.이익잉여금'부터 이어받아
    자본총계·부채와자본총계가 그 페이지에만 있다). 다음 페이지부터 최대 `MAX_CONTINUATION_
    PAGES`쪽까지 같은(또는 재배치 가능한) 열 구조인 표가 있으면 그 데이터행을 순서대로
    모아 돌려준다. 오탐 방지는 여기서 안 걸고 호출부의 병합 후 qualify_table 전체통과
    (자산총계/부채총계/자본총계 실라벨 3개 요구)에 맡긴다."""
    acc: list[list] = []
    for offset in range(1, MAX_CONTINUATION_PAGES + 1):
        piece = _continuation_page_rows(pdf_path, page_idx + offset, ncols, groups)
        if not piece:
            break
        acc.extend(piece)
    return acc or None


_LABEL_LINE_PREFIX_RE = re.compile(r'^(?:[0-9]{1,3}|[IVXLCivxlc]{1,4}|[Ⅰ-Ⅹ]{1,2})[.)]')
_TOTAL_LABEL_KEYWORDS = ("자산총계", "부채총계", "자본총계", "부채와자본총계",
                         "자산", "부채", "자본")


def _merge_wrapped_label_lines(labels: list[str]) -> list[str]:
    """줄바꿈으로 쪼개진 라벨 목록에서, 번호매김 접두(`1.`/`Ⅰ.`/`I.`) 가 없고 총계류
    키워드도 아닌 줄은 그 자체가 새 항목이 아니라 **앞줄이 줄바꿈으로 잘린 나머지**로 보고
    병합한다(실측 2026-09-11 round2, IBK연금: 'Ⅱ.기타포괄손익누계' 다음 줄이 '액' 하나뿐 --
    원래 한 단어 '기타포괄손익누계액' 이 폭 제약으로 줄바꿈된 것이다. 이걸 별도 항목으로 세면
    라벨 줄 수가 값 줄 수와 어긋나 표 전체가 분할을 포기하게 된다)."""
    if not labels:
        return labels
    out = [labels[0]]
    for line in labels[1:]:
        stripped = line.strip()
        if stripped and not _LABEL_LINE_PREFIX_RE.match(stripped) and \
                clean_label(stripped) not in _TOTAL_LABEL_KEYWORDS:
            out[-1] = out[-1] + stripped
        else:
            out.append(line)
    return out


def _reconcile_two_blob_span(labels: list[str], blob_items: list[str],
                              blob_totals: list[str]) -> tuple[list[str] | None, bool]:
    """한 논리열(예: '당기') 안에 값 뭉치가 두 칸으로 쪼개져 있을 때(실측 2026-09-11 round2,
    IBK연금: 총계류 4개 행(자산총계/부채총계/자본총계/부채와자본총계)만 별도 칸에 찍히고
    나머지 일반 항목은 다른 칸에 찍힌다 -- 헤더 폭 안에서 총계 행이 시각적으로 다르게
    정렬되는 탓으로 보인다) `labels` 순서를 따라가며 총계류 키워드 라벨은 `blob_totals`
    에서, 나머지는 `blob_items`에서 순서대로 뽑아 하나의 값 리스트로 재구성한다. 두 뭉치
    길이의 합이 라벨 개수와 맞고 `blob_totals` 길이가 라벨 중 총계류 키워드 개수와 정확히
    같을 때만 성공 -- 그 외엔 원래 구조를 못 믿으므로 포기(원본 행 그대로 둔다)."""
    if len(blob_items) + len(blob_totals) != len(labels):
        return None, False
    n_totals_in_labels = sum(1 for l in labels if clean_label(l) in _TOTAL_LABEL_KEYWORDS)
    if len(blob_totals) != n_totals_in_labels or n_totals_in_labels == 0:
        return None, False
    merged: list[str] = []
    i_items = i_totals = 0
    for lbl in labels:
        if clean_label(lbl) in _TOTAL_LABEL_KEYWORDS:
            merged.append(blob_totals[i_totals])
            i_totals += 1
        else:
            merged.append(blob_items[i_items])
            i_items += 1
    return merged, True


def _split_multiline_rows(rows: list[list],
                          groups: dict[str, tuple[int, int]]) -> list[list]:
    """일부 페이지에서 fitz find_tables() 가 섹션 전체(예: 부채 9개 행)를 라벨 셀 하나에
    `\\n` 으로 뭉쳐 넣고 같은 자리의 당기/전기 값 셀도 같은 개수로 뭉친다(실측 2026-09-11,
    AIA생명 2023.1Q p14 부채 섹션). 라벨 칸과 값 칸들의 줄바꿈 분할 개수가(2개 이상)
    서로 같은 행만 N개 행으로 쪼갠다 -- 개수가 안 맞으면 원래 구조를 믿을 수 없으므로 건드리지
    않는다(잘못 쪼개느니 원본 그대로 둬서 qualify_table 이 스스로 거르게 한다)."""
    label_span = groups.get("라벨")
    if not label_span:
        return rows
    out = [rows[0]]
    for row in rows[1:]:
        label_hit = None
        for j in range(label_span[0], min(label_span[1], len(row))):
            if row[j] and "\n" in str(row[j]):
                label_hit = (j, str(row[j]).split("\n"))
                break
        if not label_hit:
            out.append(row)
            continue
        j_label, labels = label_hit
        labels = _merge_wrapped_label_lines(labels)
        n = len(labels)
        if n < 2:
            out.append(row)
            continue
        # 라벨 첫 줄이 "자산"/"부채"/"자본"(값 없는 순수 섹션 헤더)이면, 값 목록은 그 한 줄만큼
        # 짧은 게 정상이다(실측 2026-09-11, 한화생명 2023.1Q: 라벨 24줄=섹션헤더1+항목23,
        # 값은 23개뿐). 이 경우를 "개수 불일치"로 버리지 않고 헤더 줄을 떼어내고 맞춘다.
        header_drop = clean_label(labels[0]) in ("자산", "부채", "자본") and n >= 3
        split_cols: dict[int, list[str]] = {}
        consistent = True
        for key in ("당기", "전기", "증감"):
            span = groups.get(key)
            if not span:
                continue
            blobs = [(j, str(row[j]).split("\n")) for j in range(span[0], min(span[1], len(row)))
                     if row[j] and "\n" in str(row[j])]
            if not blobs:
                continue
            j0, parts = blobs[0]
            if len(parts) == n:
                split_cols[j0] = parts
                continue
            if header_drop and len(parts) == n - 1:
                split_cols[j0] = parts
                continue
            # 총계류가 같은 논리열의 다른 칸에 따로 찍힌 경우(실측: IBK연금) -- 두 번째
            # 뭉치와 합쳐서 재구성해본다. header_drop(첫 라벨이 값 없는 순수 섹션헤더)이면
            # 그 라벨을 뺀 목록(n-1) 기준으로도 시도한다(실측: IBK연금 2025.1Q, 라벨 첫 줄이
            # '자 산' 뿐이라 header_drop 과 두 칸 분산이 같이 나타난다).
            merged = None
            if len(blobs) >= 2:
                _j1, parts2 = blobs[1]
                merged, ok_merge = _reconcile_two_blob_span(labels, parts, parts2)
                if not ok_merge and header_drop:
                    merged, ok_merge = _reconcile_two_blob_span(labels[1:], parts, parts2)
            if merged is not None:
                split_cols[j0] = merged
            else:
                consistent = False
                split_cols[j0] = parts
        if not consistent or not split_cols:
            out.append(row)
            continue
        use_labels = labels[1:] if (header_drop and
                                     all(len(p) == n - 1 for p in split_cols.values())) \
            else labels
        m = len(use_labels)
        for i in range(m):
            newrow = list(row)
            newrow[j_label] = use_labels[i]
            for j, parts in split_cols.items():
                newrow[j] = parts[i] if i < len(parts) else ""
            out.append(newrow)
    return out


def best_bs_table(pdf_path: Path):
    """이 PDF 에서 가장 그럴듯한 별도재무상태표 표 하나를 고른다.
    반환 (rows, groups, page_index) 또는 None. 4단 우선순위(숫자가 작을수록 우선):
      0: 페이지 텍스트가 명시적으로 '별도재무상태표'라고 밝힌 표, 비-운용자산 서식
      1: 신호가 아예 없는(단일표 회사) 표, 비-운용자산 서식
      2: '별도재무상태표' 명시 + 운용자산(감독규정 별표) 서식
      3: 신호 없음 + 운용자산 서식
    '연결재무상태표'로 명시된 표는 qualify_table 의 비지배지분 체크로 대개 걸러지지만, 라벨이
    없는 연결 표는 page_is_consolidated() 로 한 번 더 배제한다(모든 tier 공통, 절대 후보 안 됨).

    운용자산 서식을 하위 tier 로 남겨두는 이유(2026-09-11 round2): AIG·악사손해 등은 이
    서식이 **유일한** 공시 형식이라 무조건 배제하면 코어(1/2/3)까지 통째로 못 뽑는다. 같은
    PDF 에 더 나은 표가 있으면(한화생명 등 트랩#2/#4 사례) tier 0/1 이 먼저 채워져 이긴다."""
    candidates: dict[int, tuple[list[list], dict[str, tuple[int, int]], int]] = {}
    for page_idx, page_text in iter_candidate_pages(pdf_path):
        consolidated = page_is_consolidated(page_text)
        if consolidated is True:
            continue
        page_tables = list(find_tables_on_page(pdf_path, page_idx))
        for rows in page_tables:
            groups = header_groups(rows)
            if not groups:
                continue
            rows = _split_multiline_rows(rows, groups)
            ok, reason, is_reg_form = qualify_table(rows, groups)
            if not ok and reason.endswith("행 없음 -- BS 표 아님"):
                ncols0 = len(rows[0]) if rows else 0
                # 같은 페이지 안에서 표 하나가 fitz 표 객체 여러 개로 쪼개지는 경우(실측
                # 2026-09-11 round2, 처브라이프 KR0100 2023.3Q: 짧은 축약본이라 자산+부채
                # 앞부분과 자본총계 뒷부분이 한 페이지 안에서 별개 표 객체 2개로 나뉜다 --
                # 페이지 간 이어짐과 달리 fitz 반환 순서가 실제 읽기 순서와 다를 수 있어
                # 두 순서를 다 시도한다) -- 실패하면 다음 페이지로의 이어짐도 시도한다.
                other_same_page = [r for r in page_tables if r is not rows and r
                                    and len(r[0]) == ncols0]
                for other in other_same_page:
                    for merged_try in (rows + other, other + rows):
                        merged_try = _split_multiline_rows(merged_try, groups)
                        ok3, _r3, is_reg_form3 = qualify_table(merged_try, groups)
                        if ok3:
                            rows, ok, is_reg_form = merged_try, True, is_reg_form3
                            break
                    if ok:
                        break
            if not ok and reason.endswith("행 없음 -- BS 표 아님"):
                cont = _continuation_rows(pdf_path, page_idx, len(rows[0]) if rows else 0, groups)
                if cont:
                    cont = _split_multiline_rows([rows[0]] + cont, groups)[1:]
                    merged = rows + cont
                    ok2, _r2, is_reg_form2 = qualify_table(merged, groups)
                    if ok2:
                        rows, ok, is_reg_form = merged, True, is_reg_form2
            if not ok:
                continue
            if not qoq_column_self_check(rows, groups):
                continue
            tier = (0 if consolidated is False else 1) + (2 if is_reg_form else 0)
            if tier not in candidates:
                candidates[tier] = (rows, groups, page_idx)
    if not candidates:
        return None
    return candidates[min(candidates)]


def identity_ok(a: float | None, l: float | None, e: float | None) -> bool:
    """항목1 == 항목2 + 항목3. 셋 중 하나라도 없으면 검산 불가 -- True(통과, 별도 처리)."""
    if a is None or l is None or e is None:
        return True
    s = l + e
    return abs(a - s) <= max(IDENTITY_TOL_ABS, IDENTITY_TOL_REL * max(abs(a), abs(s)))


def qoq_ok(new_value: float, prev_value: float | None) -> bool:
    if prev_value is None or prev_value == 0:
        return True
    return abs(new_value / prev_value - 1.0) <= QOQ_TOL_REL
