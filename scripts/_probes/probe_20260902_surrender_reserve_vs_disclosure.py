# -*- coding: utf-8 -*-
"""IFRS17_BS.json item5(해약환급금준비금)를 **경영공시 PDF**의 '해약환급금준비금 등의 적립'
표(생보 대개 7-2/7-3 또는 5-3, 손보 5-3 -- 절 번호는 회사·생손보 불문 다 섞여 나온다, 절
번호로 찾지 않는다)와 전수 대조한다.

동기(owner 2026-09-02): "해약환급금준비금을 경영공시 PDF 기준으로 비교해서 DART랑 차이 큰
애들은 갈아끼우라고 했는데 하나도 안 고쳐져 있다. 삼성생명·한화생명이 특히 1~3분기 오차가
크다." 마스터의 item5 는 DART 주석(기적립액+예정액)에서 오는데, 경영공시 표는 그 분기의
**잔액**을 직접 싣는다 -- 개념이 어긋나면 경영공시가 정본이다.

[2026-09-02 2차 수정 -- v1(라인기반 exact-match)의 결함과 교체 이유]

v1 은 `페이지 텍스트를 줄 단위로 쪼개 "해약환급금준비금"과 정확히 일치하는 줄을 찾고, 그
다음 몇 줄에서 숫자를 줍는다`는 방식이었다. 이게 깨지는 이유는 전부 **한국 경영공시 PDF가
표를 세로쓰기/열 분리 렌더링**하기 때문이다:

1. **분기공시(짧은 PDF)도 라벨이 다른 무관 표에 다시 등장한다.** 신한라이프 2025.1Q/2026.1Q
   는 실제 5-3(7-2) 표가 캡션("7-2. 해약환급금준비금 등의 적립")을 달고 있어 v1의 "줄 전체가
   LABEL과 정확히 같아야 함" 조건을 통과 못 하는데(캡션엔 "등의 적립"이 붙어 있다), 같은
   페이지 안에 세로쓰기 라벨열이 뒤섞이며 라벨만 홀로 한 줄에 찍히는 자리가 생겨("...구분/
   이/익/잉/여/금/대/손/준/비/금/해약환급금준비금/24") 거기 걸려 "24"라는 각주성 잡음을
   숫자로 읽었다. **find_tables() 로 표 구조를 복원하면 진짜 표(캡션이 있는 page)가 정확히
   당분기=39,046억/직전분기=36,381억(2025.1Q 기준)으로 나오고, 마스터(3,904,563)와 39,046
   백만원 단위 환산치가 0.001% 이내로 맞는다** -- 즉 마스터는 원래 옳았고 v1 프로브가
   틀렸다.
2. **4Q(연차) 공시는 같은 라벨이 여러 완전히 다른 표에 나온다.** 이연법인세 롤포워드
   (기초/손익계산서/자본/기말, 값은 세금영향액), 이익잉여금 처분계산서(당기/전기, 값은
   그 회계연도의 **증분**, 괄호=차감), 이익잉여금 구성내역(당기말/전기말, 값은 **기적립액
   단독** -- 예정액이 빠짐), 그리고 우리가 원하는 "기적립액/적립예정액/잔액(또는 예정액)"
   3행 노트 -- 넷 다 "해약환급금준비금"을 라벨로 쓴다. v1 은 페이지의 **첫** 정확일치 줄을
   그냥 집어 이연법인세나 처분계산서 값을 잔액인 양 반환했다(하나생명 2024.4Q "공시=
   6,213,693,900"처럼 자릿수가 완전히 깨진 값이 나온 것도 여러 표의 숫자가 줄 단위로
   잘못 이어붙은 결과). **AIA 2024.4Q 실측**: 이연법인세 표(p233)엔 `해약환급금준비금 |
   (175,972) | 34,152 | - | (141,820)`(무관, 세금효과)가 있고, 우리가 원하는 표는 p240
   `해약환급금준비금 예정액 | 613,943 | 761,784`(당기말/전기말) -- 이게 곧 현재 마스터값
   613,943 과 정확히 일치한다. **하나생명 2024.4Q**도 마찬가지로 p55 요약표(억원,
   `해약환급금준비금 | 809 | 1,082`)와 p199 노트(`해약환급준비금 잔액 | 80,882,732 |
   62,136,939`, 천원)가 서로 검산되고 809억원=80,900백만원≈80,883(마스터, 오차는 표시
   단위의 반올림)으로 일치한다. **즉 4Q "큰 차이"로 찍힌 사례들은 거의 다 v1의 페이지
   오선택이었지 마스터 오류가 아니었다.**
3. **삼성생명은 생보인데도 "7-2/7-3"이 아니라 "5-3"을 쓴다**(목차 실측, FY2025_Q4 p3)
   -- 절 번호로 표를 찾으면 안 되는 이유의 실측 근거.

새 알고리즘(라인기반 완전 폐기, `find_tables()` 표 구조 기반으로 교체):

1. "해약환급" 부분문자열이 있는 페이지만 후보로 삼는다(더 넓게 -- 일부 회사는 중간 "금"자를
   빼고 "해약환급준비금"이라 쓴다, 아래 3항).
2. 그 페이지의 각 표에서 헤더 행을 스캔해 **당기열/전기열**을 키워드
   (당기말/당분기/해당분기/당기 vs 전기말/전분기/직전분기/전기)로 찾는다. 못 찾으면
   "YYYY년MM월"/"YYYY년Q/4분기"/"YY.QQ" 류 날짜 패턴을 파싱해 **더 최근 날짜 = 당기**로
   판정한다(삼성생명 요약표처럼 헤더가 "2025년4/4분기(2025년12월)" 식으로 당/전 단어가 아예
   없는 경우 대응). 열0(라벨열)은 절대 값열 후보에서 제외한다 -- 이게 이연법인세표의
   `당기\n기초\n손익계산서\n자본\n기말` 같은 열0 헤더 오탐(열0="당기"는 "이 표 전체가
   당기 데이터"라는 제목이지 값열이 아니다)을 걸러낸다.
3. 각 행의 라벨열 텍스트에서 "해약환급금준비금" 또는 "해약환급준비금"을 찾는다. 라벨 뒤
   접미사로 채택 여부를 가른다:
     - 접미사가 ""(라벨 단독, 5-3/7-2 요약표 행) 또는 "잔액" 또는 "예정액"(3행 노트의
       마지막 행) -> **채택**(잔액 개념).
     - 접미사가 "기적립액"/"적립예정액"/"환입예정액"/"적립액"/"적립(환입)" 등 -> **버림**
       (구성요소 단독값 또는 처분계산서 증분 -- 잔액이 아니다).
   한 표 안에서 라벨이 여러 개 개행으로 뭉친 셀(세로쓰기 병합, 신한라이프/코리안리 유형)도
   대응: 코리안리처럼 후속 행이 라벨을 열1에 다시 찍어주면 그 "직접 매치" 행을 최우선
   사용하고, 신한라이프처럼 재언급이 전혀 없으면 뭉친 셀의 개행분리 순번과 값열의 개행분리
   (또는 후속 물리행 시퀀스)를 같은 순서로 대응시킨다.
4. 단위는 표 바로 위(같은 페이지, 표 bbox보다 위쪽) 텍스트 블록에서 최근접
   "단위 : 억원/백만원/천원/원"을 찾아 백만원으로 환산한다. 단위를 못 찾으면 그 후보는
   낮은 신뢰도로 강등한다(추측 금지 원칙 -- "틀린 값을 싣느니 빈 칸").
5. 우선순위: (P1) 3행 노트의 잔액/예정액 행 > (P2) 요약표의 단독 라벨 행(단위=억원 확인) >
   (P3) 세로쓰기 병합 셀에서 위치 대응으로 복원한 값 > (P4) 단위 미확인 또는 단독 라벨인데
   단위가 억원이 아닌 행(구성내역 노트처럼 기적립액만 담은 표일 위험 -- 최후수단, 표시에
   경고를 남긴다). 페이지 전체에서 후보를 다 모아 최고 우선순위를 취하고, 같은 우선순위에서
   값이 서로 다르면(드묾) 전부 표시해 수동 확인을 요구한다(자동으로 아무거나 고르지 않는다).
6. **2차원 그리드 표**(미래에셋생명류): 구분(대손준비금/해약환급금준비금/보증준비금) ×
   기간(당기말/전기말)이 **열 방향으로 나란히** 놓이고, 행은 "준비금 기적립액/적립(환입)
   예정액/잔액" 3개뿐이라 행 라벨엔 개별 준비금 이름이 없다(예: 미래에셋 2025.4Q p340,
   `준비금 잔액 | 8,123 | 1,219,968 | 201,039 | 13,211 | 992,343 | 183,597`). 이 표를 4)의
   "직접매치"로 잡으면 행 라벨이 "준비금 잔액"뿐이라 LABEL_PREFIXES 매치가 안 돼 통째로
   놓친다 -- 놓치면 P4(같은 페이지의 note 31 "이익잉여금 구성내역", 기적립액 단독값
   992,343)로 떨어져 **개념이 절단된 값을 저신뢰로 보고**하게 된다(실측: 이 경로로 여기
   992,343 이 나왔었는데, p340 의 진짜 잔액은 1,219,968 -- 마스터가 그동안 옳았던 이유).
   전용 경로(`_wide_grid_candidates`)로 구분 행에서 LABEL 열을 찾고, 그 열이 당기말/전기말
   중 어느 그룹에 속하는지 상위 헤더 행에서 판정해 P_BREAKDOWN 급으로 채택한다.

각주 처리(v1과 동일): 값이 '-'/'–'/'—' 면 그 분기 **미적립**이라는 뜻이지 결측이 아니다.
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

LABEL_PREFIXES = ("해약환급금준비금", "해약환급준비금")
PAGE_FILTER = "해약환급"  # 페이지를 후보로 볼지 말지 -- LABEL_PREFIXES보다 넓게 잡는다

CUR_KW = ("당기말", "당분기", "해당분기", "당기")
PRIOR_KW = ("전기말", "전분기", "직전분기", "전기")
_HANGUL = "가-힣"


def _kw_hit(text: str, keywords) -> bool:
    """text 에 keywords 중 하나가 매치하는지. 바로 뒤에 한글 음절이 더 오면(예: '당기'가
    '당기손익반영'/'전기'가 '전기이월'의 일부인 경우) 매치로 안 본다 -- 짧은 키워드(당기/전기)가
    복합어 일부로 걸려 무관한 열을 기간열로 오판하는 것을 막는다(실측: 신한라이프 2023.4Q
    이연법인세 롤포워드 표의 '당기손익반영' 열이 '당기'로 오매치돼 그 표를 기간비교표로
    오인, 세금효과 값을 잔액인 양 반환했었다)."""
    t = text or ""
    for k in keywords:
        if re.search(re.escape(k) + f"(?![{_HANGUL}])", t):
            return True
    return False

TARGET_SUFFIXES = {"", "잔액", "예정액"}  # 접미사가 이 중 하나여야 "잔액 개념" 채택

UNIT_RE = re.compile(r"단위[:：]?\(?\s*(억원|백만원|천원|원)\)?")
UNIT_MULT = {"억원": 100.0, "백만원": 1.0, "천원": 0.001, "원": 0.000001}

NUM_TOKEN = re.compile(r"^\(?-?[\d,]+\)?$")

# 신뢰도(우선순위) 등급 -- 작을수록 우선
P_BREAKDOWN = 1     # 3행 노트(기적립액/적립예정액/잔액|예정액)의 마지막 행
P_SUMMARY = 2        # 5-3/7-2 요약표, 단독 라벨, 단위=억원 확인
P_CLUSTER = 3         # 세로쓰기 병합 셀에서 위치 대응으로 복원
P_LOW = 4            # 단위 불명 또는 단독 라벨인데 단위!=억원(구성내역 오염 위험)


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
            if cur_idx is None and any(k in c for k in CUR_KW):
                cur_idx = ci
            if prior_idx is None and any(k in c for k in PRIOR_KW):
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


def _suffix_after_label(text: str):
    """라벨 텍스트에서 LABEL_PREFIXES 이후 남는 접미사. 라벨이 없으면 None."""
    norm = _norm(text)
    idx = -1
    matched_len = 0
    for p in LABEL_PREFIXES:
        i = norm.find(p)
        if i != -1 and (idx == -1 or i < idx):
            idx = i
            matched_len = len(p)
    if idx == -1:
        return None
    suffix = norm[idx + matched_len:]
    suffix = re.sub(r"\(\*?\d*\)$", "", suffix)  # 각주표시 (*1) 등 제거
    return suffix


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


def _candidates_from_table(page, page_no, rows, table_bbox):
    """표 하나에서 (priority, value_million, unit, header_cur_text, row_label, method) 후보들."""
    cur_idx, prior_idx = _pick_columns(rows)
    if cur_idx is None:
        return []
    out = []
    header_cur_text = None
    for r in rows:
        c = _cell(r[cur_idx]) if cur_idx < len(r) else ""
        cn = _norm(c)
        if c and (any(k in cn for k in CUR_KW) or _date_key(c)):
            header_cur_text = c.replace("\n", " ")
            break
    unit = _unit_before(page, table_bbox)
    mult = UNIT_MULT.get(unit)

    # 1) 직접매치: 라벨이 '한 셀'에 단독으로 들어있는 행(그 셀 안에 개행으로 다른 라벨과
    #    뭉쳐있지 않음). 값은 그 라벨 셀의 인덱스보다 뒤에서, cur_idx 근처를 허용오차 내로
    #    찾는다(절대 인덱스를 그대로 믿지 않음 -- 위 _cell_near 사유 참조).
    direct_hits = []
    for ri, row in enumerate(rows):
        label_col = None
        label_cell_text = None
        for ci, c in enumerate(row):
            ct = _cell(c)
            if ct and any(p in _norm(ct) for p in LABEL_PREFIXES):
                label_col = ci
                label_cell_text = ct
                break
        if label_col is None:
            continue
        n_lines = len([s for s in label_cell_text.split("\n") if s.strip()])
        if n_lines > 1:
            continue  # 병합셀은 아래 cluster 처리로
        sub = _suffix_after_label(label_cell_text)
        if sub is None or sub not in TARGET_SUFFIXES:
            continue
        val = _cell_near(row, cur_idx, label_col)
        if val is None:
            continue
        if sub in ("잔액", "예정액"):
            prio = P_BREAKDOWN
        elif unit == "억원":
            prio = P_SUMMARY
        else:
            prio = P_LOW
        vm = None if val == "none" else (val * mult if mult else None)
        if val != "none" and vm is None:
            prio = P_LOW  # 단위 불명 -- 값은 있지만 신뢰도 강등, 원값 그대로 보고(변환불가 표시)
        direct_hits.append((prio, vm if vm is not None else val, unit, header_cur_text,
                             label_cell_text.replace("\n", "/"), f"direct:{sub or '(bare)'}", page_no))
    if direct_hits:
        out.extend(direct_hits)
        return out  # 직접매치가 있으면 병합셀 추정은 안 씀(더 신뢰도 높음)

    # 2) 병합셀(세로쓰기 라벨 여러 개가 한 셀에 개행으로 뭉친 경우, 또는 라벨이 col0에
    #    뭉쳐있고 값행이 뒤따르는 경우). 라벨 열 인덱스는 label_end 이내로 근사한다.
    label_end = cur_idx if prior_idx is None else min(cur_idx, prior_idx)
    label_end = max(label_end, 1)
    for ri, row in enumerate(rows):
        label_text = " ".join(_cell(c) for c in row[:label_end] if _cell(c))
        norm_label = _norm(label_text)
        if not any(p in norm_label for p in LABEL_PREFIXES):
            continue
        sublabels = []
        for c in row[:label_end]:
            ct = _cell(c)
            if ct:
                sublabels.extend([s.strip() for s in ct.split("\n") if s.strip()])
        if len(sublabels) <= 1:
            continue
        target_pos = None
        for pi, sl in enumerate(sublabels):
            if any(p in _norm(sl) for p in LABEL_PREFIXES):
                target_pos = pi
                break
        if target_pos is None:
            continue
        cur_cell = _cell(row[cur_idx]) if cur_idx < len(row) else ""
        parts = [p.strip() for p in cur_cell.split("\n") if p.strip()] if cur_cell else []
        val = None
        if len(parts) == len(sublabels):
            val = _num(parts[target_pos])
        else:
            # 클러스터 행 자신의 값(허용오차 탐색) + 곧바로 뒤따르는 (len(sublabels)-1)개
            # 물리행을 "라벨 순서와 1:1 대응"으로 모은다(신한라이프처럼 회사가 값을 라벨당
            # 한 물리행씩 흩어놓는 레이아웃 대응, 값이 빈칸인 라벨도 자리를 지켜야 순번이 안
            # 밀린다 -- 실측: 대손준비금 당분기값이 빈칸인데 이걸 건너뛰면 그 다음
            # 해약환급금준비금 값이 한 칸씩 당겨져 대손준비금 자리 값(엉뚱한 숫자)을 집는다).
            # 빈 칸은 _cell_near 가 None 을 돌려주므로 그대로 자리만 차지한다. collected 는
            # 이미 파싱된 값(int/"none"/None)을 담는다 -- 문자열로 왕복시키면 "none" 이 깨진다.
            collected = [_cell_near(row, cur_idx, label_end - 1)]
            for rj in range(ri + 1, min(ri + len(sublabels), len(rows))):
                collected.append(_cell_near(rows[rj], cur_idx, label_end - 1))
            if target_pos < len(collected):
                val = collected[target_pos]
        if val is None:
            continue
        vm = None if val == "none" else (val * mult if mult else None)
        prio = P_CLUSTER if vm is not None or val == "none" else P_LOW
        out.append((prio, vm if vm is not None else val, unit, header_cur_text,
                     "/".join(sublabels) + f"[{target_pos}]", "cluster", page_no))
    return out


RESERVE_SIBLING_LABELS = ("대손준비금", "비상위험준비금", "보증준비금")


def _wide_grid_candidates(page, page_no, rows, table_bbox):
    """구분(대손준비금/해약환급금준비금/보증준비금) x 기간(당기말/전기말)이 열 방향으로
    나란히 놓이는 2차원 그리드 표 전용 경로(미래에셋생명류, docstring 6항 참조). 이런 표는
    데이터 행 라벨이 "준비금 잔액"처럼 준비금 종류를 안 담고 있어 직접매치가 못 잡는다."""
    out = []
    unit = _unit_before(page, table_bbox)
    mult = UNIT_MULT.get(unit)
    for hi, hrow in enumerate(rows):
        label_cols = []
        sibling_hits = 0
        for ci, c in enumerate(hrow):
            ct = _norm(_cell(c))
            if not ct:
                continue
            if any(p in ct for p in LABEL_PREFIXES):
                label_cols.append(ci)
            elif any(p in ct for p in RESERVE_SIBLING_LABELS):
                sibling_hits += 1
        if not label_cols or sibling_hits < 1:
            continue
        # 위쪽 몇 줄에서 기간(당기말/전기말) 그룹 헤더 행을 찾는다.
        group_row = None
        for gi in range(hi - 1, max(hi - 3, -1), -1):
            grow = rows[gi]
            if any(any(k in _norm(_cell(c)) for k in CUR_KW + PRIOR_KW) for c in grow):
                group_row = grow
                break
        if group_row is None:
            continue

        def _group_label_of(ci):
            for j in range(ci, -1, -1):
                if j < len(group_row) and _cell(group_row[j]):
                    return _norm(_cell(group_row[j]))
            return None

        cur_col = None
        for lc in label_cols:
            g = _group_label_of(lc)
            if g and any(k in g for k in CUR_KW):
                cur_col = lc
                break
        if cur_col is None:
            continue
        header_cur_text = _group_label_of(cur_col)

        for ri in range(hi + 1, len(rows)):
            row = rows[ri]
            row_label = _cell(row[0]) if row else ""
            if not row_label:
                continue
            norm_rl = _norm(row_label)
            if not norm_rl.endswith("잔액"):
                continue  # "기적립액"/"적립(환입)예정액" 행은 건너뛰고 마지막 "잔액" 행만
            val = _cell_near(row, cur_col, 0)
            if val is None:
                continue
            vm = None if val == "none" else (val * mult if mult else None)
            prio = P_BREAKDOWN if (vm is not None or val == "none") else P_LOW
            out.append((prio, vm if vm is not None else val, unit, header_cur_text,
                         row_label, "wide-grid", page_no))
            break  # 표 하나당 "잔액" 행 하나만 채택
    return out


def parse_pdf(path: Path):
    """최고 우선순위 후보 하나를 (value_million_or_'none', page_no, method, note) 로 반환.
    후보가 전혀 없으면 None."""
    try:
        doc = fitz.open(path)
    except Exception:
        return None
    try:
        all_candidates = []
        for i, pg in enumerate(doc):
            t = pg.get_text()
            if PAGE_FILTER not in t:
                continue
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
                cands = _candidates_from_table(pg, i + 1, rows, tbl.bbox)
                if not cands:
                    cands = _wide_grid_candidates(pg, i + 1, rows, tbl.bbox)
                all_candidates.extend(cands)
        if not all_candidates:
            return None
        all_candidates.sort(key=lambda c: c[0])
        best_prio = all_candidates[0][0]
        best = [c for c in all_candidates if c[0] == best_prio]
        # 동일 우선순위에서 값이 갈리면(단위 다른 표끼리 우연히 같은 접미사) 전부 보고
        distinct_vals = {c[1] for c in best}
        return best, distinct_vals
    finally:
        doc.close()


def main():
    master = json.loads((ROOT / "IFRS17_BS.json").read_text(encoding="utf-8"))
    mi = {(r["원보험사코드"], r["공시분기"]): r["값"]
          for r in master if r["항목번호"] == 5}
    name = {r["원보험사코드"]: r["원수사명"] for r in master}

    rows_out = []
    conflicts = []
    for pdf in sorted((ROOT / "data" / "disclosure").glob("FY*/raw/*.pdf")):
        qdir = pdf.parts[-3]
        quarter = f"{qdir[2:6]}.{qdir[-1]}Q"
        code = pdf.stem.split("_", 1)[0]
        if not re.fullmatch(r"KR\d{4}", code):
            continue
        got = parse_pdf(pdf)
        if got is None:
            rows_out.append((code, quarter, None, mi.get((code, quarter)), "표없음", None))
            continue
        best, distinct_vals = got
        if len(distinct_vals) > 1:
            conflicts.append((code, quarter, best))
            # 충돌 시엔 첫 후보를 대표값으로 쓰되 표시에 conflict 플래그
        c0 = best[0]
        prio, val, unit, hdr, label, method, page_no = c0
        mv = mi.get((code, quarter))
        provenance = f"p{page_no}[{method}]{'col=' + hdr if hdr else ''}"
        if val == "none":
            rows_out.append((code, quarter, "미적립", mv, "미적립", provenance))
            continue
        if prio == P_LOW and unit is None:
            rows_out.append((code, quarter, val, mv, "단위불명(저신뢰)", provenance))
            continue
        disc = val
        if mv is None:
            rows_out.append((code, quarter, disc, None, "마스터결측", provenance))
        else:
            diff = abs(disc - mv) / max(abs(disc), 1.0)
            tag = f"{diff:.1%}"
            if len(distinct_vals) > 1:
                tag += "*충돌"
            rows_out.append((code, quarter, disc, mv, tag, provenance))

    def diff_pct(tag):
        m = re.match(r"([\d.]+)%", tag)
        return float(m.group(1)) if m else -1

    big = [r for r in rows_out if r[4] not in ("표없음", "미적립", "마스터결측", "단위불명(저신뢰)")
           and diff_pct(r[4]) > 1.0]
    miss = [r for r in rows_out if r[4] == "마스터결측"]
    nonacc = [r for r in rows_out if r[4] == "미적립"]
    notab = [r for r in rows_out if r[4] == "표없음"]
    lowconf = [r for r in rows_out if r[4] == "단위불명(저신뢰)"]

    print(f"PDF 스캔 {len(rows_out)}개 (회사-분기)")
    print(f"  표 인식 실패 {len(notab)} · 경영공시 미적립('-') {len(nonacc)} · 마스터 결측 {len(miss)}"
          f" · 저신뢰(단위불명) {len(lowconf)}")
    print(f"  대조 가능 {len(rows_out) - len(notab) - len(nonacc) - len(miss) - len(lowconf)}"
          f" · **차이 1% 초과 {len(big)}건** · 충돌(동순위 값 불일치) {len(conflicts)}건")
    print()
    for code, q, disc, mv, tag, prov in sorted(big, key=lambda r: -diff_pct(r[4])):
        print(f"  {name.get(code, code):<12} {q}  공시={disc:>12,.0f}  마스터={mv:>12,.0f}"
              f"  차이={tag:<10} {prov}")
    if lowconf:
        print("\n-- 저신뢰(단위 확인 못함, 자동교체 금지) --")
        for code, q, disc, mv, tag, prov in sorted(lowconf):
            print(f"  {name.get(code, code):<12} {q}  원값={disc}  마스터={mv}  {prov}")
    if conflicts:
        print("\n-- 충돌(동일 우선순위인데 값이 갈림, 수동확인 필요) --")
        for code, q, best in conflicts:
            print(f"  {name.get(code, code):<12} {q}")
            for c in best:
                print(f"      후보: val={c[1]} unit={c[2]} p{c[6]} {c[5]} label={c[4]}")
    if miss:
        print("\n-- 경영공시엔 값이 있는데 마스터가 비어 있는 칸 --")
        for code, q, disc, mv, tag, prov in sorted(miss):
            print(f"  {name.get(code, code):<12} {q}  공시={disc:,.0f}  {prov}")
    if notab:
        print(f"\n-- 표 인식 실패 {len(notab)}건 --")
        for code, q, disc, mv, tag, prov in sorted(notab):
            print(f"  {name.get(code, code):<12} {q}  (마스터={mv})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
