# -*- coding: utf-8 -*-
"""법정준비금 4종(item5 해약환급금준비금·item6 비상위험준비금·item7 대손준비금·item8
보증준비금)을 **경영공시 PDF**의 '~등의 적립' 표(생보 대개 7-2/7-3 또는 5-3, 손보 5-3 --
절 번호로 찾지 않는다)와 전수 대조한다.

동기(owner 2026-09-02): "해약환급금준비금을 경영공시 PDF 기준으로 비교해서 DART랑 차이 큰
애들은 갈아끼우라고 했는데 하나도 안 고쳐져 있다." 마스터의 item5-8 은 DART 주석(기적립액+
예정액)에서 오는데, 경영공시 표는 그 분기의 **잔액**을 직접 싣는다 -- 개념이 어긋나면
경영공시가 정본이다.

[2026-09-03 3차 수정 -- owner 판정 반영: "기적립액 + 적립예정액 = 잔액" 통일]

2차 수정(find_tables() 구조 기반)까지도 **개념이 여전히 섞여 있었다**. 실측(악사손해
KR0049): 같은 회사 안에서도 분기마다 "적립예정액"이 실리는 자리가 다르다 --
  - 2024.2Q~2024.3Q: 표에 "기적립액"과 "(적립예정액)" 이 **별개 행**으로 있다(둘을 더해야
    잔액). 이건 이미 대응돼 있었다(pair-sum 클러스터 경로).
  - 2025.1Q: 표엔 "해약환급금준비금 773"(기적립액, 단독행)뿐이고, "적립예정액"은 **각주
    문장**에만 있다("당분기 적립예정액은 해약환급금준비금 72억원") -- 최종 합계는 문장이
    안 알려주므로 **우리가 773+72=845억을 계산**해야 한다.
  - 2025.2Q/2025.3Q: 표는 여전히 "773"(기적립액) 단독행인데, 각주가 증분에 이어 **최종
    잔액까지 직접 말해준다**("이를 적립할 경우 당분기 해약환급금준비금은 839억원") --
    이 경우는 **문장이 준 최종값을 그대로 채택**해야 한다(우리가 더하다 반올림오차를
    만들 위험이 없다).
  - 2024.4Q: 각주에 "적립예정액" 언급 자체가 없다 -- 이 분기는 표값(773)이 그대로 잔액.
같은 회사, 같은 표 캡션인데 분기마다 이 넷 중 뭐가 나올지 다르다. 그래서 "요약표에서 라벨
단독행을 찾으면 그게 잔액"이라는 2차 수정의 전제 자체가 틀렸었다 -- **단독행은 기적립액일
수도 잔액일 수도 있고, 페이지의 각주 문장을 봐야 구분된다.**

새로 추가한 것: `_narrative_totals()` -- 페이지 전체 텍스트에서
  1. "이를 적립(환입)?할 경우 ... 입니다" 문장 -- 회사가 **직접 계산한 최종 잔액**
     (항목별로 "~은/는 NNN억원" 나열). 있으면 최우선으로 채택(문장 값을 그대로 씀,
     우리가 손으로 더하지 않는다 -- 발행사 계산이 반올림까지 반영돼 있다).
  2. "적립(환입)?예정액은 ... 입니다" 문장(위 1이 없을 때) -- **증분만** 준다. 표의
     기적립액(단독행) 값에 이 증분을 더해 잔액을 만든다. 부호는 그대로 지킨다(환입은
     음수 -- 실측: 악사손해 2025.3Q "해약환급금준비금 -15억원").
항목 4종(대손준비금·비상위험준비금·해약환급금준비금·보증준비금)이 **같은 구조**를 공유한다
(같은 문장 안에 여러 항목이 같이 나온다, 예: "해약환급금준비금 66억원, 비상위험준비금
20억원"). 그래서 LABEL_PREFIXES 를 항목별 딕셔너리로 바꾸고, 표/문장 스캔을 페이지당 한 번만
돌려 4개 항목을 동시에 뽑는다(4배 재스캔 낭비 방지).

**허용오차도 이번에 절대값으로 바꿨다.** 경영공시는 억원 단위 반올림이라 공시값×100(백만)과
마스터의 정당한 차이는 최대 ±50백만(0.5억)뿐이다 -- 그보다 크면 항목 규모와 무관하게 전부
실오차다. owner 실측: 삼성생명 2026.1Q 대손준비금이 경영공시 2,999억(299,900백만)인데
마스터는 299,321백만 -- 579백만 차이인데 예전 기준(상대 1%)으론 299,900의 0.5%=1,497백만
안에 들어가 통과했었다. `ABS_TOL_MILLION = 50.0` 로 교체.

[2026-09-02 2차 수정 -- v1(라인기반 exact-match)의 결함과 교체 이유]

v1 은 `페이지 텍스트를 줄 단위로 쪼개 라벨과 정확히 일치하는 줄을 찾고, 그 다음 몇 줄에서
숫자를 줍는다`는 방식이었다. 이게 깨지는 이유는 전부 **한국 경영공시 PDF가 표를 세로쓰기/열
분리 렌더링**하기 때문이다: (1) 캡션("7-2. ~등의 적립")이 붙은 진짜 표는 "줄 전체가 라벨과
정확히 같아야 함" 조건을 통과 못 하는데, 같은 페이지 세로쓰기 라벨열에 라벨만 홀로 찍히는
자리가 생겨 각주성 잡음을 숫자로 읽었다(신한라이프 2025.1Q "24"). (2) 4Q/연차 공시는 같은
라벨이 이연법인세 롤포워드·처분계산서·구성내역 노트 등 **개념이 다른 표**에도 나와 첫 매치를
집었다(하나생명 2024.4Q "6,213,693,900"). (3) 삼성생명은 생보인데도 "7-2/7-3"이 아니라
"5-3"을 쓴다(절 번호로 표를 찾으면 안 되는 이유).

`find_tables()` 표 구조 기반 알고리즘(2차 수정, 지금도 유효):
1. "준비금" 부분문자열이 있는 페이지만 후보로 삼는다(4개 항목 라벨 전부 이 글자를 포함).
2. 표마다 헤더 행에서 **당기열/전기열**을 키워드(당기말/당분기/해당분기/전기말/전분기/
   직전분기, 열0 라벨열은 절대 제외)로 찾는다. 못 찾으면 날짜 패턴("YYYY년MM월"/
   "YYYY년Q/4분기"/"YY.QQ"/"YYYY년 상반기·하반기")을 파싱해 최근값=당기로 판정.
3. 라벨 뒤 접미사가 ""(단독)/"잔액"/"예정액"이면 잔액개념 후보, "기적립액"/"적립(환입)
   예정액"/"처분액" 등은 버린다. 세로쓰기 병합셀(신한라이프/코리안리 유형)·2차원 그리드
   (미래에셋류, 구분×기간이 열 방향)·기적립액+적립예정액 별행 합산(악사손해 2024.2Q류)
   전용 경로가 있다.
4. 단위는 표 바로 위 텍스트 블록의 "단위: 억원/백만원/천원/원"으로 백만원 환산.
5. 우선순위: (P1=NARRATIVE) 각주 문장이 준 최종 잔액 또는 3행노트 잔액/예정액 행 >
   (P2=COMPUTED) 표의 기적립액 + 각주 증분을 합산 > (P3=SUMMARY) 요약표 단독라벨(단위=억원,
   각주에 증분 신호 없음 -- 표값 그대로 잔액) > (P4=CLUSTER) 세로쓰기 병합셀 위치대응 >
   (P5=LOW) 단위 불명 등.

각주 처리: 값이 '-'/'–'/'—' 면 그 분기 **미적립**이라는 뜻이지 결측이 아니다.
"""
from __future__ import annotations
import contextlib
import io
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.stdout.reconfigure(encoding="utf-8")
import fitz  # noqa: E402
sys.path.insert(0, str(ROOT / "scripts"))
from _disclosure_pdf_paths import disclosure_pdfs  # noqa: E402

# 항목번호 -> 라벨 변형들(긴 것부터 매치되도록 등록 순서 유지, _match_item_label 이 처리)
ITEM_LABELS = {
    5: ("해약환급금준비금", "해약환급준비금"),
    6: ("비상위험준비금",),
    7: ("대손준비금",),
    8: ("보증준비금",),
}
ITEM_NAMES = {n: 5 for n in ITEM_LABELS[5]}
for _item, _prefixes in ITEM_LABELS.items():
    for _p in _prefixes:
        ITEM_NAMES[_p] = _item
# 매치용 (라벨, 항목번호) 목록, 긴 라벨 우선(부분문자열 충돌 방지 -- 지금은 겹치는 라벨이
# 없지만 안전하게 정렬해 둔다)
_ALL_LABELS = sorted(ITEM_NAMES.items(), key=lambda kv: -len(kv[0]))

PAGE_FILTER = "준비금"  # 4개 항목 라벨이 전부 이 글자를 포함 -- 페이지 후보 필터는 넓게

# 4Q/연차 필링은 같은 노트를 별도(standalone)/연결(consolidated) 두 번 싣는다(실측: 교보생명·
# 삼성생명 -- 대손준비금 3행노트가 두 페이지에 따로 있고 값도 다르다, 연결 쪽 노트 텍스트가
# "연결법인은.../연결실체는..."으로 자기 신원을 밝힌다). 마스터는 전사 OFS(별도) 고정 관례라
# (memory reference_dart_fs_api_bs_basis) 연결 쪽은 감점해 같은 우선순위 안에서도 별도가
# 먼저 온다 -- 우연한 페이지 순서에 기대지 않는다.
CONSOLIDATED_MARKERS = ("연결법인", "연결실체")

CUR_KW = ("당기말", "당분기", "해당분기", "당기")
PRIOR_KW = ("전기말", "전분기", "직전분기", "전기")
_HANGUL = "가-힣"


def _kw_hit(text: str, keywords) -> bool:
    """text 에 keywords 중 하나가 매치하는지. 바로 뒤에 한글 음절이 더 오면(예: '당기'가
    '당기손익반영'/'전기'가 '전기이월'의 일부인 경우) 매치로 안 본다 -- 짧은 키워드(당기/전기)가
    복합어 일부로 걸려 무관한 열을 기간열로 오판하는 것을 막는다(실측: 신한라이프 2023.4Q
    이연법인세 롤포워드 표의 '당기손익반영' 열이 '당기'로 오매치돼 그 표를 기간비교표로
    오인, 세금효과 값을 잔액인 양 반환했었다). 단 뒤에 오는 게 "주1)" 류 각주표시(악사손해
    "당분기주1)")면 예외로 매치를 인정한다 -- 각주표시는 한글이 섞여 있지만 복합어가 아니다."""
    t = text or ""
    for k in keywords:
        pat = re.escape(k) + f"(?:(?![{_HANGUL}])|(?=주\\d))"
        if re.search(pat, t):
            return True
    return False


FINAL_SUFFIXES = {"잔액", "예정액", "예정잔액"}  # "이미 최종 잔액이 명시된 행"의 접미사들.
TARGET_SUFFIXES = {""} | FINAL_SUFFIXES  # 접미사가 이 중 하나여야 "잔액 개념" 채택.
# "예정잔액"은 "예정 잔액"(어순이 반대, 실측: AIA 대손준비금 3행노트 마지막행 "대손준비금
# 예정 잔액" -- 해약환급금준비금/보증준비금은 같은 회사·같은 노트에서 "~예정액"으로 쓰는데
# 대손준비금만 어순이 다르다). 못 잡으면 이 행이 P5(단독라벨, 저신뢰)로 떨어져 구성내역
# 노트의 기적립액과 혼동될 위험이 있다.

UNIT_RE = re.compile(r"단위[:：]?\(?\s*(억원|백만원|천원|원)\)?")
UNIT_MULT = {"억원": 100.0, "백만원": 1.0, "천원": 0.001, "원": 0.000001}

NUM_TOKEN = re.compile(r"^\(?-?[\d,]+\)?$")

# 신뢰도(우선순위) 등급 -- 작을수록 우선
P_NARRATIVE = 1   # 각주 문장이 직접 준 최종 잔액, 또는 3행노트의 잔액/예정액 행(둘 다 회사가
                   # 명시한 최종값)
P_COMPUTED = 2      # 표의 기적립액(단독행) + 각주 문장의 증분을 우리가 합산
P_SUMMARY = 3        # 요약표 단독 라벨, 단위=억원, 이 페이지에 증분 신호(각주) 없음 -- 표값을
                     # 그대로 잔액으로 채택
P_CLUSTER = 4          # 세로쓰기 병합 셀에서 위치 대응으로 복원
P_LOW = 5               # 단위 불명 또는 단독 라벨인데 단위!=억원(구성내역 오염 위험)

ABS_TOL_MILLION = 50.0  # 경영공시 억원 반올림의 정당한 오차 한계(=0.5억원). owner 실측
                        # (삼성생명 2026.1Q 대손준비금 579백만 차이가 옛 상대오차 1%에 삼켜짐)
                        # 이후 절대값 기준으로 교체. 상대오차(%)는 더 이상 판정에 안 쓴다.


def _cell(c) -> str:
    return (c or "").strip()


def _norm(s: str) -> str:
    return re.sub(r"\s+", "", s or "")


def _num(tok: str):
    """숫자/미적립('-')/None(파싱불가) 중 하나."""
    t = (tok or "").strip()
    if t in ("", "-", "–", "—"):
        return "none"
    core = t.replace(",", "").replace(" ", "")
    neg = core.startswith("(") or core.startswith("-")
    core = core.strip("()-")
    if not core.isdigit():
        return None
    v = int(core)
    return -v if neg else v


def _date_key(text: str):
    """헤더 셀 텍스트에서 (연도, 월-근사치) 정렬키를 뽑는다. 못 찾으면 None."""
    t = text or ""
    m = re.search(r"(\d{4})년\s*(\d{1,2})월", t)
    if m:
        return (int(m.group(1)), int(m.group(2)))
    m = re.search(r"(\d{4})년.{0,3}?(\d)\s*/\s*4?\s*분기", t)
    if m:
        return (int(m.group(1)), int(m.group(2)) * 3)
    # "2024년 상반기"(6월 말) / "하반기"(12월 말) -- 숫자 분기가 아닌 반기 표기(실측: 삼성화재
    # 2024.2Q가 "2024년 상반기"(당분기) vs "2024년 1/4분기"(직전분기) 헤더를 쓰는데, 이 패턴이
    # 없으면 상반기가 (연도,0)으로 떨어져 1/4분기((연도,3))보다 더 오래된 것처럼 보여 직전분기
    # 열을 당분기로 오판했었다).
    m = re.search(r"(\d{4})년\s*상반기", t)
    if m:
        return (int(m.group(1)), 6)
    m = re.search(r"(\d{4})년\s*하반기", t)
    if m:
        return (int(m.group(1)), 12)
    m = re.search(r"(\d{2,4})[.](\d)\s*[Qq분]", t)
    if m:
        y = int(m.group(1))
        if y < 100:
            y += 2000
        return (y, int(m.group(2)) * 3)
    m = re.search(r"(\d{4})", t)
    if m:
        return (int(m.group(1)), 0)
    return None


def _pick_columns(rows):
    """rows(find_tables().extract() 결과)에서 당기/전기 열 인덱스를 찾는다. 열0(라벨열)은
    후보에서 제외. 캡션/공백 행이 위에 여러 줄 끼어들어 진짜 헤더 행이 아래로 밀리는 경우가
    흔해(예: 신한라이프 -- 표 앞에 "VII. 기타 일반현황" 등 5줄이 같은 table 객체에 병합됨)
    전체 행을 스캔한다. 못 찾으면 (None, None)."""
    cur_idx = prior_idx = None
    for r in rows:
        for ci in range(1, len(r)):
            c = _norm(_cell(r[ci]))
            if not c:
                continue
            if cur_idx is None and _kw_hit(c, CUR_KW):
                cur_idx = ci
            if prior_idx is None and _kw_hit(c, PRIOR_KW):
                prior_idx = ci
    if cur_idx is not None:
        return cur_idx, prior_idx
    dk = {}
    for r in rows:
        for ci in range(1, len(r)):
            k = _date_key(_cell(r[ci]))
            if k and ci not in dk:
                dk[ci] = k
    if dk:
        order = sorted(dk.items(), key=lambda kv: kv[1], reverse=True)
        cur_idx = order[0][0]
        prior_idx = order[1][0] if len(order) > 1 else None
        return cur_idx, prior_idx
    return None, None


def _match_item_label(text_norm: str):
    """정규화된 텍스트 안에서 4개 항목 라벨 중 가장 먼저(그리고 가장 길게) 매치하는 것을
    찾는다. 반환 (item_no, label, start_idx) 또는 None."""
    best = None
    for label, item in _ALL_LABELS:
        i = text_norm.find(label)
        if i == -1:
            continue
        if best is None or i < best[2] or (i == best[2] and len(label) > len(best[1])):
            best = (item, label, i)
    return best


def _suffix_after_label(text: str):
    """라벨 텍스트에서 매치한 항목번호와 그 이후 남는 접미사. 라벨이 없으면 (None, None)."""
    norm = _norm(text)
    m = _match_item_label(norm)
    if m is None:
        return None, None
    item, label, idx = m
    suffix = norm[idx + len(label):]
    suffix = re.sub(r"\(\*?\d*\)$", "", suffix)  # 각주표시 (*1) 등 제거
    suffix = suffix.strip(")")  # "(해약환급금준비금 적립예정액)"처럼 라벨 전체가 괄호에 싸인 경우의 잔여 ")"
    return item, suffix


def _unit_before(page, table_bbox):
    """표 bbox 바로 위(같은 페이지)에서 가장 가까운 '단위 : XXX' 를 찾는다."""
    try:
        blocks = page.get_text("blocks")
    except Exception:
        return None
    blocks = sorted(blocks, key=lambda b: b[1])
    top = table_bbox[1]
    unit = None
    for b in blocks:
        y0 = b[1]
        text = b[4] if len(b) > 4 else ""
        if y0 > top + 3:
            break
        m = UNIT_RE.search(text.replace(" ", ""))
        if m:
            unit = m.group(1)
    if unit is None:
        # 페이지 전체에서 최초 1건으로 폴백
        try:
            m = UNIT_RE.search(page.get_text().replace(" ", ""))
            if m:
                unit = m.group(1)
        except Exception:
            pass
    return unit


def _cell_near(row, idx, min_idx, num_ok=True, max_window=3):
    """row[idx] 근처(±max_window)에서 숫자/미적립으로 파싱되는 첫 셀을 찾는다.
    find_tables() 는 헤더 행과 데이터 행의 그리드 경계를 살짝 다르게 잡을 때가 많아(같은
    표 안에서도 행마다 1칸씩 어긋난다 -- 실측: 동양생명/악사손해 사례), 헤더에서 판정한
    열 인덱스를 데이터 행에 그대로 적용하면 빈 칸을 짚는다. idx 에 가까운 순서
    (0,-1,+1,-2,+2,...)로 훑되 라벨 열(min_idx 이하)은 넘어가지 않는다."""
    if idx is None:
        return None
    offsets = [0]
    for d in range(1, max_window + 1):
        offsets += [-d, d]
    for off in offsets:
        j = idx + off
        if j <= min_idx or j < 0 or j >= len(row):
            continue
        raw = _cell(row[j])
        if not raw:
            continue  # 완전 공백 셀(None/"")은 "값이 없다"가 아니라 "아직 못 찾았다" -- 계속 탐색.
                       # raw="-" 처럼 명시적 대시는 _num()이 'none'(미적립)으로 채택한다.
        v = _num(raw)
        if v is not None:
            return v
    return None


def _parse_signed_eok(tok: str):
    """'-15'/'△15'/'15' 등 각주 문장에서 뽑은 숫자 토큰(억원 단위) -> signed int. 실패시 None."""
    t = (tok or "").strip()
    neg = t.startswith("-") or t.startswith("△") or t.startswith("(")
    core = t.lstrip("-△(").rstrip(")").replace(",", "")
    if not core.isdigit():
        return None
    v = int(core)
    return -v if neg else v


_NARR_NUM = r"([△\-(]?[\d,]+)\)?억원"


def _narrative_totals(page_text: str):
    """페이지 전체 텍스트에서 각주 문장의 항목별 적립예정액을 뽑는다(단위 억원, 부호 유지).
    반환: {item_no: {"stated": int_or_None, "increment": int_or_None}}.

    두 문형을 각각 스캔한다(실측: 악사손해 KR0049, 같은 회사 안에서도 분기마다 어느 쪽이
    나오는지 다르다):
      1. "이를 적립(환입)?할 경우 ... 해약환급금준비금은 839억원 ... 입니다" -- 회사가 직접
         계산한 **최종 잔액**. 있으면 이 값을 그대로 쓴다(우리가 손으로 더하지 않는다).
      2. "적립(환입)?예정액은 해약환급금준비금 72억원 ... 입니다" -- **증분만**. 표의
         기적립액(단독행)에 이 증분을 더해야 잔액이 나온다(_candidates_from_table 에서 처리).
    """
    norm = _norm(page_text)
    out: dict[int, dict[str, int]] = {}

    def _scan(clause: str, key: str):
        for label, item in _ALL_LABELS:
            for m in re.finditer(re.escape(label) + r"(?:은|는)?" + _NARR_NUM, clause):
                v = _parse_signed_eok(m.group(1))
                if v is not None:
                    out.setdefault(item, {})[key] = v

    for m in re.finditer(r"적립(?:\(환입\))?할경우(.{0,200}?)(?:입니다|\.|$)", norm):
        _scan(m.group(1), "stated")
    for m in re.finditer(r"적립(?:\(환입\))?예정액은(.{0,200}?)(?:입니다|\.|$)", norm):
        _scan(m.group(1), "increment")
    return out


def _candidates_from_table(page, page_no, rows, table_bbox, narrative):
    """표 하나에서 (item_no, priority, value_million, unit, header_cur_text, row_label,
    method, page_no) 후보들. narrative 는 _narrative_totals() 의 반환값(이 페이지 전체 공용,
    표마다 새로 안 만든다)."""
    cur_idx, prior_idx = _pick_columns(rows)
    if cur_idx is None:
        return []
    out = []
    header_cur_text = None
    for r in rows:
        c = _cell(r[cur_idx]) if cur_idx < len(r) else ""
        cn = _norm(c)
        if c and (_kw_hit(cn, CUR_KW) or _date_key(c)):
            header_cur_text = c.replace("\n", " ")
            break
    unit = _unit_before(page, table_bbox)
    mult = UNIT_MULT.get(unit)

    # 이익잉여금**처분**계산서류 표는 구분 나열이 요약표/3행노트와 판박이라 그 회계연도의
    # **전입액**(플로우)을 잔액인 양 집어낼 위험이 있다(실측: 신한라이프 2023.4Q p501·
    # 2024.4Q p184 둘 다 "처분예정일/처분확정일"이 박힌 이익잉여금처분계산서인데, 라벨은
    # "3. 해약환급금준비금"처럼 접미사 없이 깨끗해 직접매치/클러스터 둘 다 통과해 버린다).
    # 당기열 헤더나 표 앞머리에 "처분"이 보이면 이 표는 잔액/요약표가 아니라고 보고 통째로
    # 건너뛴다 -- "예정액"/"잔액" 접미사가 명시된 진짜 3행노트는 그런 헤더를 쓰지 않는다.
    if (header_cur_text and "처분" in header_cur_text) or \
            any("처분" in _norm(_cell(c)) for r in rows[:4] for c in r):
        return []

    def _emit_bare(item, val, label_text, method):
        """단독행(접미사="") 값 하나 -- 각주에 그 항목의 증분/최종잔액 신호가 있으면 그걸
        우선 채택하고, 없으면 표값을 그대로 잔액으로 채택(P_SUMMARY)."""
        narr = narrative.get(item, {})
        vm_raw = None if val == "none" else (val * mult if mult else None)
        if narr.get("stated") is not None:
            sv = narr["stated"]
            svm = sv * 100.0  # 각주 문장은 항상 억원 단위
            out.append((item, P_NARRATIVE, svm, unit, header_cur_text, label_text,
                        f"{method}+narrative_stated", page_no))
        elif narr.get("increment") is not None and val != "none" and mult:
            base_eok = val if unit == "억원" else val / mult * (1 / 100.0) if mult else None
            # unit 이 억원이 아니면 표값 기준으로 억원 환산이 불명확해질 수 있어 안전하게
            # "표값(백만원) + 증분(백만원)"으로 바로 합산한다(억원 왕복 없이).
            comb = vm_raw + narr["increment"] * 100.0 if vm_raw is not None else None
            if comb is not None:
                out.append((item, P_COMPUTED, comb, unit, header_cur_text, label_text,
                            f"{method}+narrative_increment({narr['increment']}억)", page_no))
            if vm_raw is not None:
                out.append((item, P_SUMMARY if unit == "억원" else P_LOW, vm_raw, unit,
                            header_cur_text, label_text, method, page_no))
        else:
            if val == "none":
                out.append((item, P_SUMMARY, "none", unit, header_cur_text, label_text,
                            method, page_no))
            elif vm_raw is not None:
                prio = P_SUMMARY if unit == "억원" else P_LOW
                out.append((item, prio, vm_raw, unit, header_cur_text, label_text, method,
                            page_no))
            elif val is not None:
                out.append((item, P_LOW, val, unit, header_cur_text, label_text, method,
                            page_no))

    # 1) 직접매치: 라벨이 '한 셀'에 단독으로 들어있는 행(그 셀 안에 개행으로 다른 라벨과
    #    뭉쳐있지 않음). 값은 그 라벨 셀의 인덱스보다 뒤에서, cur_idx 근처를 허용오차 내로
    #    찾는다(절대 인덱스를 그대로 믿지 않음 -- 위 _cell_near 사유 참조).
    direct_hits = []
    for ri, row in enumerate(rows):
        label_col = None
        label_cell_text = None
        item_found = None
        for ci, c in enumerate(row):
            ct = _cell(c)
            if not ct:
                continue
            it, _lbl, _idx = _match_item_label(_norm(ct)) or (None, None, None)
            if it is not None:
                label_col, label_cell_text, item_found = ci, ct, it
                break
        if label_col is None:
            continue
        n_lines = len([s for s in label_cell_text.split("\n") if s.strip()])
        if n_lines > 1:
            continue  # 병합셀은 아래 cluster 처리로
        item, sub = _suffix_after_label(label_cell_text)
        if item is None or sub not in TARGET_SUFFIXES:
            continue
        val = _cell_near(row, cur_idx, label_col)
        if val is None:
            continue
        label_disp = label_cell_text.replace("\n", "/")
        if sub in FINAL_SUFFIXES:
            vm = None if val == "none" else (val * mult if mult else None)
            if val != "none" and vm is None:
                direct_hits.append((item, P_LOW, val, unit, header_cur_text, label_disp,
                                     f"direct:{sub}", page_no))
            else:
                direct_hits.append((item, P_NARRATIVE, vm if vm is not None else val, unit,
                                     header_cur_text, label_disp, f"direct:{sub}", page_no))
        else:  # sub == "" (bare) -- 각주 확인 필요
            saved_len = len(out)
            _emit_bare(item, val, label_disp, "direct:(bare)")
            direct_hits.extend(out[saved_len:])
            del out[saved_len:]
    if direct_hits:
        out.extend(direct_hits)
        return out  # 직접매치가 있으면 병합셀 추정은 안 씀(더 신뢰도 높음)

    # (처분계산서 배제는 위에서 표 전체에 이미 적용됨 -- 여기 도달했다는 건 통과했다는 뜻)

    # 2) 병합셀(세로쓰기 라벨 여러 개가 한 셀에 개행으로 뭉친 경우, 또는 라벨이 col0에
    #    뭉쳐있고 값행이 뒤따르는 경우). 라벨 열 인덱스는 label_end 이내로 근사한다.
    label_end = cur_idx if prior_idx is None else min(cur_idx, prior_idx)
    label_end = max(label_end, 1)
    for ri, row in enumerate(rows):
        label_text = " ".join(_cell(c) for c in row[:label_end] if _cell(c))
        norm_label = _norm(label_text)
        if _match_item_label(norm_label) is None:
            continue
        sublabels = []
        for c in row[:label_end]:
            ct = _cell(c)
            if ct:
                sublabels.extend([s.strip() for s in ct.split("\n") if s.strip()])
        if len(sublabels) <= 1:
            continue
        # 개행이 "서로 다른 준비금 종류의 나열"이 아니라 긴 라벨 하나가 줄바꿈된 것일 수
        # 있다(실측: 신한라이프 처분계산서의 "보증준비금 및\n해약환급금준비금"은 두 준비금을
        # **합산**한 한 줄짜리 항목인데 개행 때문에 별개 항목처럼 보였다 -- "및/와/과"로
        # 끝나는 조각이 있으면 그건 나열이 아니라 줄바꿈이니 클러스터로 다루지 않는다).
        if any(re.search(r"(및|와|과)$", _norm(s)) for s in sublabels):
            continue
        # 이 사업연도부터 표 형식이 바뀌어 "기적립액"과 "(적립예정액)"을 별개 줄로 쪼개는
        # 회사가 있다(실측: 악사손해 2024.2Q부터 -- "해약환급금준비금 기적립액"(794)과
        # "(해약환급금준비금 적립예정액)"(189)이 따로 있고 둘을 더해야 잔액 983이다). 접미사가
        # ""/잔액/예정액이면 그 자리 값을 그대로 쓰고, "기적립액"이면 바로 다음 자리가
        # "적립예정액"/"환입예정액"인지 확인해 둘을 더한다 -- 그 외 접미사(적립액/적립(환입)
        # 등, 처분계산서류)는 버린다.
        # 한 뭉친 셀에 항목이 **여러 개** 들어있을 수 있다(실측: 악사손해 2024.2Q -- 대손/
        # 비상위험/해약환급금/보증준비금 기적립액이 전부 한 셀에 나열, 각각 자기 적립예정액
        # 짝을 갖는다). 첫 매치에서 멈추면 뒤쪽 항목을 놓친다 -- 전부 스캔한다.
        found = []  # [(item, target_pos, pair_pos), ...]
        pi = 0
        while pi < len(sublabels):
            it, sfx = _suffix_after_label(sublabels[pi])
            if it is None:
                pi += 1
                continue
            if sfx in TARGET_SUFFIXES:
                found.append((it, pi, None))
                pi += 1
                continue
            if sfx == "기적립액" and pi + 1 < len(sublabels):
                _it2, nxt_sfx = _suffix_after_label(sublabels[pi + 1])
                nxt_norm = nxt_sfx if nxt_sfx is not None else _norm(sublabels[pi + 1])
                if "적립예정액" in nxt_norm or "환입예정액" in nxt_norm:
                    found.append((it, pi, pi + 1))
                    pi += 2
                    continue
            pi += 1
        if not found:
            continue
        cur_cell = _cell(row[cur_idx]) if cur_idx < len(row) else ""
        parts = [p.strip() for p in cur_cell.split("\n") if p.strip()] if cur_cell else []
        if len(parts) == len(sublabels):
            resolved = [_num(p) for p in parts]
        else:
            # 클러스터 행 자신의 값(허용오차 탐색) + 곧바로 뒤따르는 (len(sublabels)-1)개
            # 물리행을 "라벨 순서와 1:1 대응"으로 모은다(신한라이프처럼 회사가 값을 라벨당
            # 한 물리행씩 흩어놓는 레이아웃 대응, 값이 빈칸인 라벨도 자리를 지켜야 순번이 안
            # 밀린다 -- 실측: 대손준비금 당분기값이 빈칸인데 이걸 건너뛰면 그 다음
            # 해약환급금준비금 값이 한 칸씩 당겨져 대손준비금 자리 값(엉뚱한 숫자)을 집는다).
            # 빈 칸은 _cell_near 가 None 을 돌려주므로 그대로 자리만 차지한다. resolved 는
            # 이미 파싱된 값(int/"none"/None)을 담는다 -- 문자열로 왕복시키면 "none" 이 깨진다.
            resolved = [_cell_near(row, cur_idx, label_end - 1)]
            for rj in range(ri + 1, min(ri + len(sublabels), len(rows))):
                resolved.append(_cell_near(rows[rj], cur_idx, label_end - 1))
        label_note = "/".join(sublabels)
        for target_item, target_pos, pair_pos in found:
            need_pos = max(target_pos, pair_pos) if pair_pos is not None else target_pos
            if need_pos >= len(resolved):
                continue
            val = resolved[target_pos]
            if pair_pos is not None:
                pv = resolved[pair_pos]
                # 기적립액+적립예정액을 더해 잔액을 만든다 -- 둘 중 하나라도 못 찾으면(None)
                # 포기, "none"(미적립, 대시)은 0으로 취급해 더한다.
                if val is None or pv is None:
                    continue
                v0 = 0 if val == "none" else val
                v1 = 0 if pv == "none" else pv
                val = v0 + v1 if not (val == "none" and pv == "none") else "none"
                if val is None:
                    continue
                vm = None if val == "none" else (val * mult if mult else None)
                prio = P_CLUSTER if vm is not None or val == "none" else P_LOW
                out.append((target_item, prio, vm if vm is not None else val, unit,
                            header_cur_text, label_note + f"[{target_pos}+{pair_pos}]",
                            "cluster", page_no))
            else:
                if val is None:
                    continue
                saved_len = len(out)
                _emit_bare(target_item, val, label_note + f"[{target_pos}]", "cluster")
                # _emit_bare 는 P_SUMMARY/P_LOW/P_NARRATIVE/P_COMPUTED 로 이미 넣었지만, 각주
                # 신호가 전혀 없는 기본 케이스는 P_SUMMARY 가 아니라 P_CLUSTER 로 강등한다
                # (클러스터 위치대응 자체의 불확실성이 남아 있으므로).
                for k in range(saved_len, len(out)):
                    if out[k][1] == P_SUMMARY:
                        out[k] = (out[k][0], P_CLUSTER, *out[k][2:])
    return out


def _wide_grid_candidates(page, page_no, rows, table_bbox, narrative):
    """구분(대손준비금/해약환급금준비금/보증준비금 등) x 기간(당기말/전기말)이 열 방향으로
    나란히 놓이는 2차원 그리드 표 전용 경로(미래에셋생명류). 이런 표는 데이터 행 라벨이
    "준비금 잔액"처럼 준비금 종류를 안 담고 있어 직접매치가 못 잡는다. 이 표는 이미 행이
    기적립액/적립예정액/잔액 3개로 명시돼 있어(합산까지 자체적으로 함) 각주 문장을 또
    확인할 필요가 없다 -- 있어도 같은 개념일 뿐이라 무시한다."""
    out = []
    unit = _unit_before(page, table_bbox)
    mult = UNIT_MULT.get(unit)
    for hi, hrow in enumerate(rows):
        label_cols = {}  # ci -> item_no
        for ci, c in enumerate(hrow):
            ct = _norm(_cell(c))
            if not ct:
                continue
            m = _match_item_label(ct)
            if m is not None:
                label_cols[ci] = m[0]
        # 이 표가 "구분 x 기간" 2차원 그리드라는 신호 = 한 행에 서로 다른 준비금 종류가
        # 2개 이상 나열됨(실측: 대손/해약환급금/보증준비금이 같은 행에 반복). 예전엔 항목이
        # 하나뿐이라(item5만) "해약환급금준비금 외에 다른 준비금 이름이 있는가"로 이 신호를
        # 잡았는데, 지금은 4개 항목을 전부 label_cols 로 잡아버려 "다른" 이름이 안 남는다 --
        # distinct 항목 수 자체로 판정한다.
        if len(set(label_cols.values())) < 2:
            continue
        # 위쪽 몇 줄에서 기간(당기말/전기말) 그룹 헤더 행을 찾는다.
        group_row = None
        for gi in range(hi - 1, max(hi - 3, -1), -1):
            grow = rows[gi]
            if any(_kw_hit(_norm(_cell(c)), CUR_KW + PRIOR_KW) for c in grow):
                group_row = grow
                break
        if group_row is None:
            continue

        def _group_label_of(ci):
            for j in range(ci, -1, -1):
                if j < len(group_row) and _cell(group_row[j]):
                    return _norm(_cell(group_row[j]))
            return None

        cur_cols = {}  # item_no -> col_idx (당기 그룹에 속한 것만)
        for ci, item in label_cols.items():
            g = _group_label_of(ci)
            if g and _kw_hit(g, CUR_KW) and item not in cur_cols:
                cur_cols[item] = ci
        if not cur_cols:
            continue
        header_cur_text = _group_label_of(next(iter(cur_cols.values())))

        for ri in range(hi + 1, len(rows)):
            row = rows[ri]
            row_label = _cell(row[0]) if row else ""
            if not row_label:
                continue
            norm_rl = _norm(row_label)
            if not norm_rl.endswith("잔액"):
                continue  # "기적립액"/"적립(환입)예정액" 행은 건너뛰고 마지막 "잔액" 행만
            for item, col in cur_cols.items():
                val = _cell_near(row, col, 0)
                if val is None:
                    continue
                vm = None if val == "none" else (val * mult if mult else None)
                prio = P_NARRATIVE if (vm is not None or val == "none") else P_LOW
                out.append((item, prio, vm if vm is not None else val, unit, header_cur_text,
                            row_label, "wide-grid", page_no))
            break  # 표 하나당 "잔액" 행 하나만 채택
    return out


def parse_pdf(path: Path):
    """항목번호(5/6/7/8) -> (최고우선순위 후보 리스트, distinct_vals) 또는 결측이면 키 자체가
    없음. 페이지 전체가 무관하면(라벨 자체가 없음) 4개 항목 다 없음."""
    try:
        doc = fitz.open(path)
    except Exception:
        return None
    try:
        all_candidates: dict[int, list] = {}
        for i, pg in enumerate(doc):
            t = pg.get_text()
            if PAGE_FILTER not in t:
                continue
            narrative = _narrative_totals(t)
            is_consol = any(m in t for m in CONSOLIDATED_MARKERS)
            with contextlib.redirect_stdout(io.StringIO()):
                try:
                    tabs = pg.find_tables()
                except Exception:
                    continue
            for tbl in tabs.tables:
                try:
                    rows = tbl.extract()
                except Exception:
                    continue
                cands = _candidates_from_table(pg, i + 1, rows, tbl.bbox, narrative)
                if not cands:
                    cands = _wide_grid_candidates(pg, i + 1, rows, tbl.bbox, narrative)
                for c in cands:
                    # c = (item, priority, value, unit, hdr, label, method, page_no) -- 연결
                    # 표시(is_consol)를 끝에 덧붙여 같은 우선순위 안에서 별도를 먼저 오게 한다.
                    all_candidates.setdefault(c[0], []).append(c[1:] + (is_consol,))
        if not all_candidates:
            return None
        result = {}
        for item, cands in all_candidates.items():
            cands.sort(key=lambda c: (c[0], c[-1]))  # (priority, is_consol) -- 별도(False) 먼저
            best_prio, best_consol = cands[0][0], cands[0][-1]
            # "같은 우선순위 안에서도 별도가 있으면 연결은 아예 비교 대상에서 뺀다" -- 별도/
            # 연결 차이만으로 값이 갈리는 건 이제 "충돌"이 아니라 결정론적으로 별도를 채택한다
            # (실측: 교보생명·삼성생명 대손준비금 3행노트가 두 기준으로 각각 실려 값이 달랐다).
            best = [c for c in cands if c[0] == best_prio and c[-1] == best_consol]
            distinct_vals = {c[1] for c in best}
            result[item] = (best, distinct_vals)
        return result
    finally:
        doc.close()


ITEM_REPORT_NAME = {5: "해약환급금준비금", 6: "비상위험준비금", 7: "대손준비금", 8: "보증준비금"}


def main():
    master = json.loads((ROOT / "IFRS17_BS.json").read_text(encoding="utf-8"))
    mi_by_item = {item: {(r["원보험사코드"], r["공시분기"]): r["값"]
                          for r in master if r["항목번호"] == item}
                  for item in ITEM_REPORT_NAME}
    name = {r["원보험사코드"]: r["원수사명"] for r in master}

    # period -> [(code, pdf_path)]. raw/ 우선, 없으면 pdf/ 폴백은 disclosure_pdfs()가 알아서
    # 처리한다(2026.2Q가 한동안 pdf/ 에만 있었던 사고 -- scripts/_disclosure_pdf_paths.py
    # 참조. 여기서 직접 "FY*/raw/*.pdf"만 globbing하면 raw/ 가 비고 pdf/ 만 있는 분기를
    # 조용히 건너뛴다).
    DISCLOSURE = ROOT / "data" / "disclosure"
    periods = sorted(p.name for p in DISCLOSURE.glob("FY*_Q*") if p.is_dir())

    rows_out = {item: [] for item in ITEM_REPORT_NAME}
    conflicts = {item: [] for item in ITEM_REPORT_NAME}

    for period in periods:
        quarter = f"{period[2:6]}.{period[-1]}Q"
        codes = set()
        for sub in ("raw", "pdf"):
            d = DISCLOSURE / period / sub
            if d.is_dir():
                codes.update(f.stem.split("_", 1)[0] for f in d.glob("*.pdf"))
        for code in sorted(codes):
            if not re.fullmatch(r"KR\d{4}", code):
                continue
            paths = disclosure_pdfs(period, code, root=DISCLOSURE)
            if not paths:
                continue
            pdf = paths[0]
            got = parse_pdf(pdf)
            for item in ITEM_REPORT_NAME:
                mv = mi_by_item[item].get((code, quarter))
                if got is None or item not in got:
                    rows_out[item].append((code, quarter, None, mv, "표없음", None))
                    continue
                best, distinct_vals = got[item]
                if len(distinct_vals) > 1:
                    conflicts[item].append((code, quarter, best))
                c0 = best[0]
                prio, val, unit, hdr, label, method, page_no = c0
                provenance = f"p{page_no}[{method}]{'col=' + hdr if hdr else ''}"
                if val == "none":
                    rows_out[item].append((code, quarter, "미적립", mv, "미적립", provenance))
                    continue
                if prio == P_LOW and unit is None:
                    rows_out[item].append((code, quarter, val, mv, "단위불명(저신뢰)", provenance))
                    continue
                disc = val
                if mv is None:
                    rows_out[item].append((code, quarter, disc, None, "마스터결측", provenance))
                else:
                    absdiff = abs(disc - mv)
                    tag = f"{absdiff:,.0f}백만"
                    if len(distinct_vals) > 1:
                        tag += "*충돌"
                    rows_out[item].append((code, quarter, disc, mv, tag, provenance))

    def abs_diff(tag):
        m = re.match(r"([\d,]+)백만", tag)
        return float(m.group(1).replace(",", "")) if m else -1

    grand_total_scanned = 0
    grand_total_big = 0
    for item in (5, 6, 7, 8):
        rows = rows_out[item]
        grand_total_scanned += len(rows)
        big = [r for r in rows if r[4] not in ("표없음", "미적립", "마스터결측", "단위불명(저신뢰)")
               and abs_diff(r[4]) > ABS_TOL_MILLION]
        grand_total_big += len(big)
        miss = [r for r in rows if r[4] == "마스터결측"]
        nonacc = [r for r in rows if r[4] == "미적립"]
        notab = [r for r in rows if r[4] == "표없음"]
        lowconf = [r for r in rows if r[4] == "단위불명(저신뢰)"]
        comparable = len(rows) - len(notab) - len(nonacc) - len(miss) - len(lowconf)

        print(f"=== item{item} {ITEM_REPORT_NAME[item]} ===")
        print(f"PDF 스캔 {len(rows)}개 (회사-분기)")
        print(f"  표 인식 실패 {len(notab)} · 경영공시 미적립('-') {len(nonacc)} · 마스터 결측 {len(miss)}"
              f" · 저신뢰(단위불명) {len(lowconf)}")
        print(f"  대조 가능 {comparable}"
              f" · **절대차 {ABS_TOL_MILLION:.0f}백만 초과 {len(big)}건** ·"
              f" 충돌(동순위 값 불일치) {len(conflicts[item])}건")
        print()
        for code, q, disc, mv, tag, prov in sorted(big, key=lambda r: -abs_diff(r[4])):
            print(f"  {name.get(code, code):<12} {q}  공시={disc:>12,.0f}  마스터={mv:>12,.0f}"
                  f"  차이={tag:<12} {prov}")
        if lowconf:
            print("\n-- 저신뢰(단위 확인 못함, 자동교체 금지) --")
            for code, q, disc, mv, tag, prov in sorted(lowconf):
                print(f"  {name.get(code, code):<12} {q}  원값={disc}  마스터={mv}  {prov}")
        if conflicts[item]:
            print("\n-- 충돌(동일 우선순위인데 값이 갈림, 수동확인 필요) --")
            for code, q, best in conflicts[item]:
                print(f"  {name.get(code, code):<12} {q}")
                for c in best:
                    print(f"      후보: val={c[1]} unit={c[2]} p{c[6]} {c[5]} label={c[4]}")
        if miss:
            print(f"\n-- 경영공시엔 값이 있는데 마스터가 비어 있는 칸 ({len(miss)}) --")
            for code, q, disc, mv, tag, prov in sorted(miss):
                print(f"  {name.get(code, code):<12} {q}  공시={disc:,.0f}  {prov}")
        if notab:
            print(f"\n-- 표 인식 실패 {len(notab)}건 --")
            for code, q, disc, mv, tag, prov in sorted(notab):
                print(f"  {name.get(code, code):<12} {q}  (마스터={mv})")
        print()

    print(f"=== 총계: {grand_total_scanned}개 셀(4항목 합산) 스캔, 절대차{ABS_TOL_MILLION:.0f}백만"
          f" 초과 {grand_total_big}건 ===")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
