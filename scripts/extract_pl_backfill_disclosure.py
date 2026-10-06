# -*- coding: utf-8 -*-
"""정기경영공시 PDF §2-1 요약 포괄손익계산서(총괄) -> PL_breakdown 8항목 백필 추출기.

배경: inbox/parser/20260918T0205Z (orchestrator) Phase 1a. DART 분기보고서를 내지 않는
16개 비상장사의 비-4Q 분기(2023~2025 1/2/3Q + 2026 1/2Q, KR0150 서울보증만 2023.4Q 포함
7분기)에 대해 PL_breakdown.json 이 결손인 172개 (회사,분기) 셀을 경영공시 PDF 로 채운다.

**이번 라운드는 스테이징만 한다 -- 루트 마스터 PL_breakdown.json 은 절대 건드리지 않는다.**
산출은 data/_derived/pl_backfill_disclosure_20260918.json 하나뿐이다. 마스터 병합은 validation
판정 이후 별도 라운드.

방법: fitz(PyMuPDF) find_tables() 로 §2-1 표를 grid 로 뽑는다. 초기 라인기반 프로브
(_probes/probe_20260918_disclosure_pl_backfill.py) 는 (a) 소수점 억원 값(예: 121.97)을
정수 전용 정규식이 통째로 버리는 버그, (b) fitz 의 plain get_text() 가 이 표에서 라벨/숫자를
시각 순서와 다르게 뱉는 문서를 만나면 못 읽는 한계가 있었다 -- 실측(KR0051 2024.1Q, KR1098
2025.1Q)으로 확인. find_tables() 는 좌표 기반 grid 라 두 문제 다 없다(같은 두 파일로 재확인,
값 100% 일치).

표 레이아웃 변형 (전부 find_tables() 로 통일 처리, 전부 실측 근거):
  1. 표준형(대다수, 예 KR0004/KR0029): col0=상위 라벨(보험손익 등, 하위 항목 미리보기 텍스트
     포함한 병합셀), col1=None 또는 하위 항목 라벨("(보험수익)" 등), 값은 헤더 열개수와 무관하게
     "보험손익" 행 자신의 첫 실값 칸으로 위치를 역산한다(아래 `_find_idx_cur`).
  2. 그룹형(KR1098/AIA 계열 소액 신설사): col0="보험\\n부문" 등 그룹명, col1=실제 항목 라벨.
     하위 5항목이 한 grid row 에 "\\n" 조인으로 뭉쳐 나옴(대시선이라 find_tables 가 행 경계로
     안 봄) -- 라벨/값을 같은 개수로 split 후 zip 으로 복원.
  3. 과분할형(KR0049/KR0074 등): find_tables 가 시각적 표 하나를 라벨행/값행/빈행 3개로
     쪼갠다(같은 항목의 라벨과 값이 다른 grid row 에 있음, 방향은 항목마다 다름 -- 위/아래
     둘 다 관측). `_nearest_value`가 반경 1~3 행을 탐색해 "라벨이 전혀 없는(그래서 다른
     항목이 이미 못 쓸) 값 전용 행"만 빌려온다.
  4. 라벨 소실형(KR1098 2026.1Q 등): 영업이익/세전이익/법인세비용 3행이 라벨 칸까지 통째로
     빈 문자열로 나온다(원인 미상 -- 아마 그리드선 없는 셀). `_positional_bracket_fill`이
     인접해서 이미 확정된 항목(17,21,24) 사이의 "값은 있는데 라벨이 없는" 행을 규정된 표
     순서(1,16,17,20,21,22,23,24)대로 채우되, **항등식(20≈1+17, 22≈20+21)이 실제로 닫힐
     때만** 채택한다 -- 위치만 보고 추측하지 않는다.
  5. "2-1-1) 감독회계 기준 총괄계정 요약 포괄손익계산서" 제목 변형(AIG/카카오페이 등): 제목
     문자열만 다르고 표 구조는 표준형과 동일 -- "포괄손익계산서" 부분문자열은 공통이라 페이지
     탐지에 지장 없음.
  6. 순수 이미지 PDF(AIA 2025.1Q~2026.1Q 등 일부 최근 분기, KR0097/KR1098 일부 분기): 텍스트
     레이어 자체가 없어 find_tables 가 표를 못 찾는다. 이 스크립트는 그런 셀을
     TEXT_TABLE_NOT_FOUND 로 보고하고 끝낸다 -- 렌더링+비전 수기판독은 스크립트 밖(티켓 답변
     참고, 4셀 AIA 2025.1Q/2Q/3Q+2026.1Q 는 이 세션에서 렌더링 후 육안 판독 완료).

단위: 원문 억원 -> 마스터 관례 백만원 (x100), 소수점 그대로 보존(억원 2자리=백만원 정수와
정확 대응, 반올림 오차 없음).

"-" 처리: 이 표는 보험손익=보험수익-보험서비스비용+재보험수익-재보험서비스비용-기타사업비용
같은 항등식이 행 내부에서 닫히는 구조라, 소계 행의 "-" 는 결측이 아니라 "정확히 0" 인 경우가
실측으로 확인됐다(예: KR0051 2024.1Q 영업외손익 -=1-1=0). 단 find_tables() 가 쪼갠 **빈
문자열**("") 칸은 진짜 대시 문자와 다르다 -- "원문이 0" 이 아니라 "이 칸엔 원래 아무것도
없다"(값은 다른 grid row 에 있다)는 뜻이라 0 으로 단정하면 안 된다(KR0074 2023.1Q 항목24
당기순이익 행에서 실측: 라벨행의 값 칸이 빈 문자열이고 진짜 965 는 다음 grid row 에 있었다 --
빈 문자열을 0 으로 잘못 채울 뻔한 사고를 이 스크립트 안에서 잡았다). 그래서 진짜 대시 문자
집합과 빈 문자열을 코드에서 명시적으로 구분한다. 채택된 값에는 dash_zero 플래그를 남겨
검증측이 판단할 근거를 보존한다.

실행:
  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/extract_pl_backfill_disclosure.py
"""
import fitz
import io
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
fitz.TOOLS.mupdf_display_errors(False)

OUT_PATH = os.path.join(ROOT, "data", "_derived", "pl_backfill_disclosure_20260918.json")

# 추출 8항목 (원 발주 ticket 6절). 순서는 마스터 항목번호 순 = 표 상 등장 순서와 동일.
# 주의: 8개 전부를 마스터에 병합하는 게 아니다 -- BACKFILL_ITEMS 참조.
TARGET_ITEMS = {
    1: "보험손익", 16: "기타사업비용", 17: "투자손익", 20: "영업이익",
    21: "영업외손익", 22: "세전이익", 23: "법인세비용", 24: "당기순이익",
}
ITEM_ORDER = [1, 16, 17, 20, 21, 22, 23, 24]

# 실제 마스터 병합 대상 5항목 (validation 정정티켓 20260918T0700Z §A).
# 나머지 3개(17/20/21)는 check_only -- 아래 CHECK_ONLY_REASON 참조.
BACKFILL_ITEMS = [1, 16, 22, 23, 24]
CHECK_ONLY_ITEMS = [17, 20, 21]
CHECK_ONLY_REASON = (
    "경영공시 투자손익 = 투자수익 - 투자비용(감독회계) / 마스터 투자손익(#17) = 투자이익(#18) + "
    "보험금융손익(#19). 투자손익<->영업외손익 경계의 재분류라 개별 항목은 다른 개념이고 합계만 "
    "보존된다(validation 4Q 중첩 43칸 실측: #17 불일치 50.0% / #21 47.4% / #20 50.0%, 단 #17+#21 "
    "합은 10.8%). 발행사 자인 -- KR0004 FY2024 경영공시 §3-2-1 주3) '종속기업투자주식손상차손"
    "(환입) ... 감독회계에서는 투자손익, 일반회계에서는 영업외손익 관련 계정으로 분류'. "
    "따라서 17/20/21 은 수용 등식 검산에만 쓰고 마스터에는 싣지 않는다."
)

# 구성 행 8개 -- **검산 전용**이다. 마스터 항목번호가 없고 병합 대상이 아니다.
# 라벨 변형은 실측 census 로 확정(scripts/_probes/probe_20260918e_component_label_census.py,
# data/_derived/_probe_20260918e_component_labels.json): 괄호형 `(보험수익)` 이 대다수(151~154셀),
# 괄호 없는 `보험수익` 이 KR0049 FY2025 5셀, 그리고 `(보험서비스비)용` 처럼 괄호가 글자 중간에
# 끼어 닫히는 변형이 KR0080 2026.2Q 에 1건씩 있다. 괄호/공백을 제거한 뒤 비교하면 전부 흡수된다.
COMPONENT_ITEMS = {
    "보험수익": "보험수익", "보험서비스비용": "보험서비스비용",
    "재보험수익": "재보험수익", "재보험서비스비용": "재보험서비스비용",
    "투자수익": "투자수익", "투자비용": "투자비용",
    "영업외수익": "영업외수익", "영업외비용": "영업외비용",
}
COMPONENT_ORDER = ["보험수익", "보험서비스비용", "재보험수익", "재보험서비스비용",
                   "투자수익", "투자비용", "영업외수익", "영업외비용"]

# 회사코드 -> 회사명 (파일명 접두 검색용, 결과 JSON 표기용). 티켓 표 그대로.
COMPANIES = {
    "KR0004": "예별손해보험", "KR0029": "AIG손해보험", "KR0049": "악사손해보험",
    "KR0050": "하나손해보험", "KR0051": "신한이지손해보험", "KR0074": "라이나생명보험",
    "KR0075": "BNP파리바카디프생명보험", "KR0076": "아이엠라이프생명보험",
    "KR0080": "AIA생명보험", "KR0095": "메트라이프생명보험", "KR0097": "하나생명보험",
    "KR0100": "처브라이프생명보험", "KR0150": "서울보증보험",
    "KR1010": "교보라이프플래닛생명보험", "KR1011": "IBK연금보험", "KR1098": "카카오페이손해보험",
}

QUARTERS_NON4Q = [f"{fy}.{q}Q" for fy in (2023, 2024, 2025) for q in (1, 2, 3)] + ["2026.1Q", "2026.2Q"]
QUARTERS_KR0150 = ["2023.1Q", "2023.2Q", "2023.3Q", "2023.4Q", "2024.1Q", "2024.2Q", "2024.3Q"]


def target_cells():
    cells = []
    for code in COMPANIES:
        quarters = QUARTERS_KR0150 if code == "KR0150" else QUARTERS_NON4Q
        for q in quarters:
            cells.append((code, q))
    return cells


def quarter_to_folder(q):
    fy, qq = q.split(".")
    return f"FY{fy}_Q{qq[0]}"


def find_pdf(code, quarter):
    rawdir = os.path.join(ROOT, "data", "disclosure", quarter_to_folder(quarter), "raw")
    if not os.path.isdir(rawdir):
        return None
    cands = sorted(f for f in os.listdir(rawdir) if f.startswith(code + "_") and f.lower().endswith(".pdf"))
    if not cands:
        return None
    return os.path.join(rawdir, cands[0])


# ---------------------------------------------------------------------------
# 숫자 파싱 -- 콤마/괄호(음수)/세모(음수, 한국 회계 관행)/대시(정확히 0) 처리.
# 전부 \uXXXX 이스케이프로 적어 인코딩 경유 손상 위험을 없앤다(에디터/전송 과정에서
# 유니코드 리터럴이 뭉개지는 사고가 이 파일 초안 작성 중 실제로 있었다).
# ---------------------------------------------------------------------------
_DASH_ONLY = {"-", "\uff0d", "\u2010", "\u2014", "\u2013", "\u2015"}  # - full-width- hyphen em en horiz-bar


def parse_value(cell):
    """-> (value_eok: float|None, is_dash_zero: bool). 빈 문자열/None 은 (None, False) --
    find_tables() 가 쪼갠 빈 grid 셀은 "원문이 0" 이 아니라 "이 칸엔 원래 아무것도 없다"는
    뜻이라, 0 으로 단정하면 실제 값이 다른 행에 있는 경우(KR0074 등) 조용히 틀린 0 을 심는다."""
    if cell is None:
        return None, False
    s = str(cell).strip().replace("\u3000", "").replace(" ", "")
    if s == "":
        return None, False
    if s in _DASH_ONLY:
        return 0.0, True
    neg = False
    if (s.startswith("(") and s.endswith(")")) or (s.startswith("\uff08") and s.endswith("\uff09")):
        neg = True
        s = s[1:-1]
    if s.startswith("\u25b3") or s.startswith("\u25b2"):  # 세모(음수 대체 표기)
        neg = True
        s = s[1:]
    s = s.replace(",", "")
    if not s or s in _DASH_ONLY:
        return 0.0, True
    try:
        v = float(s)
    except ValueError:
        return None, False
    return (-v if neg else v), False


def looks_like_real_value(cell):
    """이 칸이 '진짜 값(혹은 진짜 대시)'인지 -- 빈 문자열/None 은 아니다."""
    if cell is None:
        return False
    s = str(cell).strip()
    if s == "":
        return False
    if s in _DASH_ONLY:
        return True
    return any(ch.isdigit() for ch in s)


def classify(label_line):
    """행 라벨(첫 줄) -> (항목번호, 항목명) | None. 순서 중요 (더 구체적인 것 먼저)."""
    l = (label_line or "").strip()
    if not l:
        return None
    if "법인세비용차감전" in l:
        return 22, TARGET_ITEMS[22]
    if l.startswith("법인세비용") and "차감전" not in l:
        return 23, TARGET_ITEMS[23]
    if "당기순" in l:
        return 24, TARGET_ITEMS[24]
    if "영업외손익" in l:
        return 21, TARGET_ITEMS[21]
    if "기타사업비용" in l:
        return 16, TARGET_ITEMS[16]
    if "투자손익" in l:
        return 17, TARGET_ITEMS[17]
    if "영업이익" in l or ("영업" in l and "손실" in l and "외" not in l):
        return 20, TARGET_ITEMS[20]
    if l.startswith("보험손익"):
        return 1, TARGET_ITEMS[1]
    return None


def _strip_brackets(label_line):
    """괄호(반각/전각)와 공백을 전부 제거 -- 구성 행 라벨 정규화 전용.
    `(보험수익)` -> `보험수익`, `(보험서비스비)용` -> `보험서비스비용`(KR0080 2026.2Q 실측)."""
    s = (label_line or "").strip()
    for ch in ("(", ")", "（", "）", "[", "]", " ", "　"):
        s = s.replace(ch, "")
    return s


def classify_component(label_line):
    """행 라벨 -> 구성행 key | None. classify() 가 None 을 낸 라벨에만 적용한다.
    순서 중요: `재보험수익` 은 `보험수익` 을 부분문자열로 포함하므로 재보험을 먼저 본다."""
    s = _strip_brackets(label_line)
    if not s:
        return None
    if s.startswith("재보험수익"):
        return "재보험수익"
    if s.startswith("재보험서비스비용"):
        return "재보험서비스비용"
    if s.startswith("보험수익"):
        return "보험수익"
    if s.startswith("보험서비스비용"):
        return "보험서비스비용"
    if s.startswith("투자수익"):
        return "투자수익"
    if s.startswith("투자비용"):
        return "투자비용"
    if s.startswith("영업외수익"):
        return "영업외수익"
    if s.startswith("영업외비용"):
        return "영업외비용"
    return None


def _label_col_text(row, idx_cur):
    """row[0..idx_cur-1] 중 값 컬럼에 가장 가까운(가장 오른쪽) non-empty 라벨 텍스트."""
    for i in range(idx_cur - 1, -1, -1):
        if i < len(row) and row[i]:
            return row[i]
    return None


# 그룹명 비계(scaffold) 칸 -- 표의 세로 병합 그룹 라벨("보험\n부문" 등)이 find_tables 의 과분할로
# 값 행에 홀로 남은 것. 항목 라벨이 아니다. 실측 census(probe_20260918e): 구성행/항목 어느
# 분류에도 안 걸리는 라벨은 이 여섯 토큰뿐이었다.
# 이 칸을 '라벨 있음'으로 치면 값 전용 donor 행이 배제돼 _nearest_value 가 더 먼 엉뚱한 행을
# 빌려온다 -- KR0074 2023.2Q 재보험수익(정답 322, r9 `['', '부문', '322', ...]` 배제 -> r13 의
# 재보험서비스비용 331 을 차용) / KR0080 2024.1Q 보험서비스비용(정답 2,499, r11 `['부문', '',
# '2,499', ...]` 배제 -> r15 재보험수익 446 차용), 2024.2Q/3Q 동일. 수용 등식 E1 이 잡아냈다.
# 헤더 토큰 '구 분' 은 **넣지 않는다** -- 넣으면 헤더 행 `['구 분', '', '해당 분기\n(24.3Q)', ...]`
# 이 donor 후보가 돼(숫자 "24.3Q" 가 실값처럼 보임) 보험손익 값 행과 모호 충돌 -> item1 유실
# (KR0075 2024.3Q / KR0100 2025.1Q / 2025.3Q 실측 회귀, 즉시 되돌림).
_GROUP_SCAFFOLD = {"보험", "투자", "영업외", "부문", "보험부문", "투자부문", "영업외부문"}


def _is_scaffold(text):
    s = str(text).replace("\n", "").replace(" ", "").replace("　", "").strip()
    return s in _GROUP_SCAFFOLD


def _row_is_label_blank(row, idx_cur):
    """라벨 칸(0..idx_cur-1) 전부가 None/빈 문자열/그룹명 비계인가 -- '값 전용' 행 판정용."""
    for i in range(min(idx_cur, len(row))):
        v = row[i]
        if v is not None and str(v).strip() != "" and not _is_scaffold(v):
            return False
    return True


def _find_idx_cur(rows):
    """헤더 열개수를 믿지 않는다(KR0049 실측: 헤더가 13열인데 데이터 행 실값은 인덱스4에
    있어 헤더 기준 인덱스5와 어긋남 -- 시각적 그룹 스팬 때문에 헤더/바디 컬럼 경계가 다르게
    잡히는 find_tables() 산출물이 실재한다). 대신 '보험손익' 행 자신에서 첫 실값 칸 위치를
    역산한다 -- 이 표는 100% '보험손익'이 첫 데이터 행이라는 티켓 §2 표준서식을 anchor 로 쓴다."""
    for ridx in range(1, len(rows)):
        row = rows[ridx]
        label_idx = None
        for ci in range(min(6, len(row))):
            if row[ci] and str(row[ci]).split("\n")[0].strip().startswith("보험손익"):
                label_idx = ci
                break
        if label_idx is None:
            continue
        for i in range(label_idx + 1, len(row)):
            if i < len(row) and looks_like_real_value(row[i]):
                return i
        # 라벨 행 자체엔 값이 비어 있고 다음 행에 값이 실린 문서(KR0075/KR0100 실측: 상위
        # 항목 라벨/값이 서로 다른 grid row) -- 바로 다음 행에서 같은 위치의 값을 본다.
        if ridx + 1 < len(rows):
            nxt = rows[ridx + 1]
            for i in range(label_idx + 1, len(nxt)):
                if i < len(nxt) and looks_like_real_value(nxt[i]):
                    return i
    return None


def _nearest_value(rows, row_idx, idx_cur, max_radius=3):
    """rows[row_idx] 자신의 idx_cur 칸이 비었을 때, 반경 내에서 '라벨이 전혀 없는'(다른
    항목이 이미 못 쓸) 값 전용 행을 찾는다. 양쪽에서 서로 다른 값이 나오면(모호) 포기한다."""
    candidates = []
    for r in range(1, max_radius + 1):
        for j in (row_idx - r, row_idx + r):
            if 0 <= j < len(rows) and j != row_idx:
                cand = rows[j]
                if idx_cur < len(cand) and looks_like_real_value(cand[idx_cur]) and _row_is_label_blank(cand, idx_cur):
                    candidates.append((r, j, cand[idx_cur]))
        if candidates:
            break  # 이 반경에서 찾았으면 더 넓게 안 본다(가장 가까운 것 우선)
    if not candidates:
        return None, None
    if len(candidates) > 1:
        vals = {c[2] for c in candidates}
        if len(vals) > 1:
            return None, None  # 모호 -- 추측하지 않는다
    _, j, v = candidates[0]
    return v, j


def _positional_bracket_fill(rows, idx_cur, found):
    """라벨 칸까지 통째로 빈 '값만 있는 고아 행'을 표 순서(1,16,17,20,21,22,23,24)로 채운다.
    (17,21) 또는 (21,24) 처럼 이미 확정된 두 항목 사이 구간에서, 그 사이에 낀 목표 항목
    개수와 '라벨없는 값 전용 행' 개수가 정확히 같을 때만 순서대로 배정 -- 그리고 그 값을
    받아들이기 전에 반드시 항등식으로 검산한다(20=1+17, 22=20+21). 검산이 안 맞으면 버린다."""
    row_of = {}
    for item_no, rec in found.items():
        row_of[item_no] = rec["row_idx"]

    def orphan_rows_between(i0, i1):
        out = []
        for j in range(i0 + 1, i1):
            row = rows[j]
            if idx_cur < len(row) and looks_like_real_value(row[idx_cur]) and _row_is_label_blank(row, idx_cur):
                out.append(j)
        return out

    # 구간 1: item17 -> item21, 사이엔 item20 하나만.
    if 17 in row_of and 21 in row_of and 20 not in found:
        orphans = orphan_rows_between(row_of[17], row_of[21])
        if len(orphans) == 1:
            v, _ = parse_value(rows[orphans[0]][idx_cur])
            if v is not None:
                expect = found[1]["value_eok"] + found[17]["value_eok"]
                if abs(v - expect) < 0.06:  # 반올림 오차만 허용(소수 2자리 표)
                    dz = rows[orphans[0]][idx_cur] and str(rows[orphans[0]][idx_cur]).strip() in _DASH_ONLY
                    found[20] = {"value_eok": v, "dash_zero": bool(dz), "raw_label": "(positional:영업이익)",
                                 "raw_value": rows[orphans[0]][idx_cur], "row_idx": orphans[0], "positional": True}

    # 구간 2: item21 -> item24, 사이엔 item22, item23 순서대로.
    if 21 in row_of and 24 in row_of and (22 not in found or 23 not in found) and 20 in found:
        orphans = orphan_rows_between(row_of[21], row_of[24])
        if len(orphans) == 2:
            v22, _ = parse_value(rows[orphans[0]][idx_cur])
            if v22 is not None and 22 not in found:
                expect22 = found[20]["value_eok"] + found[21]["value_eok"]
                if abs(v22 - expect22) < 0.06:
                    dz = str(rows[orphans[0]][idx_cur]).strip() in _DASH_ONLY
                    found[22] = {"value_eok": v22, "dash_zero": dz, "raw_label": "(positional:세전이익)",
                                 "raw_value": rows[orphans[0]][idx_cur], "row_idx": orphans[0], "positional": True}
            if 22 in found and 23 not in found:
                v23, _ = parse_value(rows[orphans[1]][idx_cur])
                if v23 is not None:
                    expect24 = found[22]["value_eok"] - v23
                    ok = 24 in found and abs(expect24 - found[24]["value_eok"]) < 0.06
                    if ok:
                        dz = str(rows[orphans[1]][idx_cur]).strip() in _DASH_ONLY
                        found[23] = {"value_eok": v23, "dash_zero": dz, "raw_label": "(positional:법인세비용)",
                                     "raw_value": rows[orphans[1]][idx_cur], "row_idx": orphans[1], "positional": True}
    return found


def _process_rows(table_rows, idx_cur, start_row, found, warnings):
    """table_rows[start_row:] 를 훑어 found(dict, in-place)에 새 항목을 채운다.
    이미 있는 항목은 덮어쓰지 않는다(페이지 넘어간 이어붙이기에서 재사용하기 위함)."""
    for row_idx in range(start_row, len(table_rows)):
        row = table_rows[row_idx]
        if idx_cur >= len(row):
            continue
        label_text = _label_col_text(row, idx_cur)
        value_text = row[idx_cur]
        if label_text is None:
            continue
        label_lines = label_text.split("\n")
        value_lines = value_text.split("\n") if isinstance(value_text, str) else ([value_text] if value_text is not None else [])
        if len(label_lines) != len(value_lines) and len(value_lines) > 1:
            value_lines = _repair_value_lines(value_lines)
        if len(label_lines) == len(value_lines) and len(label_lines) > 1:
            pairs = [(lab, val, row_idx) for lab, val in zip(label_lines, value_lines)]
        else:
            v0 = value_lines[0] if value_lines else None
            pairs = [(label_lines[0], v0, row_idx)]
            if len(label_lines) != len(value_lines) and len(value_lines) > 1:
                warnings.append(f"line-count mismatch label={label_lines!r} value={value_lines!r}")
        for lab, val, ridx in pairs:
            item = classify(lab)
            if item is None:
                # 구성 행(검산 전용). found 안에 **문자열 키**로 담는다 -- 정수 항목번호
                # 키와 네임스페이스가 겹치지 않아 기존 8항목 추출 경로를 전혀 건드리지 않는다
                # (베이스라인 대조로 확인: 8항목 1,328값 전부 불변).
                comp_key = classify_component(lab)
                if comp_key is None:
                    continue
                item_no = comp_key
            else:
                item_no = item[0]
            if item_no in found:
                continue  # 첫 매치 우선(중복 방지)
            if not looks_like_real_value(val):
                # 같은 행, 인접 컬럼 먼저 본다 (KR1098 2023년형 실측: 행 안에서 라벨/값 컬럼
                # 인덱스가 행마다 1칸씩 밀린다 -- 같은 논리행인데 그룹칸 개수가 달라서 생김).
                same_row_hit = None
                for adj in (idx_cur + 1, idx_cur - 1):
                    if 0 <= adj < len(row) and looks_like_real_value(row[adj]):
                        same_row_hit = row[adj]
                        break
                if same_row_hit is not None:
                    val = same_row_hit
                else:
                    # 그래도 없으면 과분할 문서(KR0049/KR0074류)일 수 있으니 이웃 행에서 찾는다.
                    borrowed, donor_idx = _nearest_value(table_rows, row_idx, idx_cur)
                    if borrowed is None:
                        warnings.append(f"item{item_no} label found (row {row_idx}) but no value nearby")
                        continue
                    val = borrowed
                    ridx = donor_idx
            v, dash_zero = parse_value(val)
            if v is None:
                warnings.append(f"item{item_no} unparseable value {val!r} (label={lab!r})")
                continue
            found[item_no] = {"value_eok": v, "dash_zero": dash_zero, "raw_label": lab, "raw_value": val,
                               "row_idx": ridx}


def _is_paren_wrapped(raw):
    s = str(raw if raw is not None else "").strip().replace(" ", "")
    return len(s) >= 3 and ((s[0] == "(" and s[-1] == ")") or (s[0] == "（" and s[-1] == "）"))


def _reinterpret_uniform_brackets(found, warnings):
    """괄호 값의 의미를 표 자신의 타이포그래피로 판정한다.

    회계 관행에서 `(123)` 은 음수다. 그런데 경영공시 표준서식은 소계 행 **라벨**을 `(보험수익)`
    처럼 괄호로 적고, 일부 문서는 그 소계 행의 **값**까지 같은 괄호로 감싼다(KR0050 하나손해
    2023.1Q 실측: r2 `(1,162)|(1,180)|(41)|(75)|(13)` -- 보험수익 1,162 는 수익이라 음수일 수
    없고, 같은 표의 상위 행은 음수를 `△65` 세모로 적는다). 이 경우 괄호는 '~중' 을 뜻하는 소계
    괄호이지 부호가 아니다.

    판정 규칙(문서 내부 근거만 사용, 답을 맞추려는 보정이 아니다):
      소계 행 값(구성행 8개 + 기타사업비용) 이 6개 이상 있고 **전부** 괄호이며, 상위 행 값
      (1/17/20/21/22/23/24) 은 **하나도** 괄호가 아닐 때만 소계 괄호로 본다. 음수는 산발적으로
      나타나지 소계 행 전부에 균일하게 나타나지 않는다. 반례 확인: KR1098 2023.2Q 는 상위 행이
      `(163)` 이고 소계 행은 `1|153|0|0|12` 로 맨 숫자 -> 규칙 미발동, 괄호는 음수(정답).
      KR0051 2026.1Q / KR0076 / KR0080 2023.1Q 도 괄호가 상위·증감 행에 산발 -> 미발동.
    census: scripts/_probes/probe_20260918h_paren_marker_census.py (괄호 값 있는 23셀 전건 검토).
    발동 시 괄호를 벗긴 문자열을 다시 parse_value 에 넣는다(안쪽 세모가 있으면 그 부호는 보존)."""
    sub_keys = [k for k in found if isinstance(k, str)] + ([16] if 16 in found else [])
    parent_keys = [k for k in found if isinstance(k, int) and k != 16]
    if len(sub_keys) < 6:
        return
    sub_paren = [k for k in sub_keys if _is_paren_wrapped(found[k].get("raw_value"))]
    parent_paren = [k for k in parent_keys if _is_paren_wrapped(found[k].get("raw_value"))]
    if len(sub_paren) != len(sub_keys) or parent_paren:
        return
    evidence = (f"소계 행 값 {len(sub_keys)}개 전부 괄호, 상위 행 값 {len(parent_keys)}개 전부 비괄호 "
                f"(상위 행 음수 표기: {sorted({str(found[k]['raw_value'])[0] for k in parent_keys if str(found[k]['raw_value']).startswith(('△', '▲', '-'))}) or '없음'})"
                " -> 괄호는 소계 표기, 부호 아님")
    for k in sub_keys:
        rec = found[k]
        s = str(rec["raw_value"]).strip().replace(" ", "")[1:-1]
        v, dz = parse_value(s)
        if v is None:
            continue
        rec["value_eok"] = v
        rec["dash_zero"] = dz
        rec["paren_reinterpreted_as_bracket"] = True
        rec["paren_evidence"] = evidence
    warnings.append("괄호 소계 표기 재해석: " + evidence)


def extract_table_rows(table_rows):
    """find_tables().extract() 결과(list of list) -> (found_dict, warnings, idx_cur) | None."""
    if not table_rows or len(table_rows) < 5:
        return None
    idx_cur = _find_idx_cur(table_rows)
    if idx_cur is None:
        return None
    found, warnings = {}, []
    _process_rows(table_rows, idx_cur, 1, found, warnings)  # row0 = 헤더, 건너뜀
    found = _positional_bracket_fill(table_rows, idx_cur, found)
    return found, warnings, idx_cur


def extract_continuation_rows(table_rows, idx_cur, found, warnings):
    """다음 페이지로 넘어간 표 꼬리 -- 헤더 행이 없으므로 0행부터 처리."""
    if not table_rows:
        return
    _process_rows(table_rows, idx_cur, 0, found, warnings)
    _positional_bracket_fill(table_rows, idx_cur, found)


CORE_LABELS = ("보험손익", "투자손익", "영업이익", "당기순이익")


def _core_label_hits(t):
    """전분기 손실 전용 서식(예: KR0051 -- '영업이익'/'당기순이익' 문구 자체가 없고
    '영업 손실'/'당기순손실' 만 존재) 을 놓치지 않도록 이익/손실 두 변형을 다 받는다."""
    hits = 0
    if "보험손익" in t:
        hits += 1
    if "투자손익" in t:
        hits += 1
    if "영업이익" in t or "영업손실" in t:
        hits += 1
    if "당기순이익" in t or "당기순손실" in t:
        hits += 1
    return hits


def find_and_extract(pdf_path, max_pages=40):
    """-> (status, page_no|None, found_dict|None, warnings, table_bbox|None)"""
    doc = fitz.open(pdf_path)
    try:
        n = min(max_pages, doc.page_count)
        any_text_candidate = False
        for i in range(n):
            page = doc[i]
            t = page.get_text()
            if "포괄손익계산서" not in t:
                continue
            hits = _core_label_hits(t)
            if hits < 3:
                continue
            any_text_candidate = True
            try:
                tabs = page.find_tables()
            except Exception:  # pragma: no cover - defensive
                continue
            for tab in tabs.tables:
                rows = tab.extract()
                res = extract_table_rows(rows)
                if res is None:
                    continue
                found, warnings, idx_cur = res
                if 1 in found:  # 보험손익(item1) 확보 = 이 표가 맞다는 anchor
                    missing = [it for it in ITEM_ORDER if it not in found]
                    if missing and i + 1 < n:
                        # 표가 페이지 경계에서 잘렸을 수 있다(AIA 2023.3Q 실측: 항목1/16/17
                        # 은 이 페이지, 20/21/22/23/24 는 다음 페이지 표 꼬리). 다음 페이지의
                        # 모든 표를 이어붙이기 후보로 시도 -- 헤더가 없으므로 idx_cur 는
                        # 이 페이지에서 이미 구한 값을 그대로 재사용한다.
                        try:
                            next_tabs = doc[i + 1].find_tables()
                        except Exception:  # pragma: no cover - defensive
                            next_tabs = None
                        if next_tabs is not None:
                            for ntab in next_tabs.tables:
                                if not any(it not in found for it in missing):
                                    break
                                extract_continuation_rows(ntab.extract(), idx_cur, found, warnings)
                    _reinterpret_uniform_brackets(found, warnings)
                    return "OK", i + 1, found, warnings, list(tab.bbox)
        if any_text_candidate:
            return "TABLE_STRUCTURE_UNRECOGNIZED", None, None, [], None
        return "TEXT_TABLE_NOT_FOUND", None, None, [], None
    finally:
        doc.close()


# ---------------------------------------------------------------------------
# 순수 이미지 PDF(텍스트 레이어 없음, find_tables 로 자동추출 불가) 7칸 -- 240dpi 렌더링
# 후 육안 판독(이 세션에서 실시, 재현 스크린샷은 세션 scratchpad 에만 있음). 전부 표 내부
# 항등식(영업이익=보험손익+투자손익, 세전이익=영업이익+영업외손익, 당기순이익=세전이익-
# 법인세비용)으로 자체검산 -- item20 이 원문표 자체의 반올림(성분별 독립 반올림)으로 ±1
# 억원 이내 어긋나는 경우가 있었으나(KR1098 2024.2Q/3Q), 그건 원문 표 자체의 특성이라
# 그대로 옮겼다(추측/보정 없음). page 는 그 값이 실제로 있는 렌더링 페이지 번호.
MANUAL_VISION_CELLS = {
    ("KR0080", "2025.1Q"): {"page": 4, "values": {1: 183, 16: 137, 17: 243, 20: 426, 21: -9, 22: 417, 23: 97, 24: 320}},
    ("KR0080", "2025.2Q"): {"page": 6, "values": {1: 428, 16: 283, 17: 536, 20: 964, 21: 37, 22: 1001, 23: 231, 24: 770}},
    ("KR0080", "2025.3Q"): {"page": 5, "values": {1: 260, 16: 454, 17: 1172, 20: 1432, 21: 68, 22: 1500, 23: 346, 24: 1154}},
    ("KR0080", "2026.1Q"): {"page": 4, "values": {1: 119, 16: 144, 17: 588, 20: 707, 21: 4, 22: 711, 23: 172, 24: 539}},
    ("KR0097", "2024.2Q"): {"page": 5, "values": {1: 146, 16: 61, 17: -22, 20: 124, 21: 0, 22: 124, 23: 32, 24: 92}},
    ("KR1098", "2024.2Q"): {"page": 5, "values": {1: -205, 16: 14, 17: -13, 20: -217, 21: -1, 22: -218, 23: 0, 24: -218}},
    ("KR1098", "2024.3Q"): {"page": 4, "values": {1: -308, 16: 21, 17: -41, 20: -348, 21: -1, 22: -349, 23: 0, 24: -349}},
}
# 원문에서 "-" 로 찍혀 정확히 0 인 항목(육안 확인). 위 정수 0 과 구분해 PRINTED_DASH 로 표시한다.
_MANUAL_DASH_ZERO = {
    ("KR0097", "2024.2Q"): {21},
    ("KR1098", "2024.2Q"): {23},
    ("KR1098", "2024.3Q"): {23},
}


# ---------------------------------------------------------------------------
# 값 방출 -- dash 3-state (validation 정정티켓 20260918T0700Z §D-2)
#
#   NORMAL        원문에 숫자가 찍혀 있다. 값을 싣는다.
#   PRINTED_DASH  원문에 진짜 대시("-")가 인쇄돼 있다. **기본은 값을 싣지 않는다(null)**.
#                 회사·항목별 근거가 서면 아래 adjudicate_printed_dashes() 가 0 으로 승격한다.
#   READ_FAILED   칸을 읽지 못했다. 절대 값을 싣지 않는다.
#
# 옛 `dash_zero: true` 는 이 셋을 구분 못 해 "못 읽은 칸"과 "진짜 0"을 같은 0.0 으로 뭉갰다.
# 그 필드는 제거하고 dash_state 로 대체한다.
# ---------------------------------------------------------------------------
def _dash_state(rec):
    raw = rec.get("raw_value")
    if rec.get("dash_zero"):
        if raw is None or str(raw).strip() == "":
            return "READ_FAILED"
        return "PRINTED_DASH"
    return "NORMAL"


def _emit_rec(rec, name, method):
    state = _dash_state(rec)
    out = {
        "항목명": name,
        "값_억원": None if state != "NORMAL" else rec["value_eok"],
        "값": None if state != "NORMAL" else round(rec["value_eok"] * 100, 6),  # 백만원
        "dash_state": state,
        "raw_label": rec["raw_label"],
        "raw_value": rec["raw_value"],
        "positional": rec.get("positional", False),
        "extraction_method": method,
    }
    if state == "PRINTED_DASH":
        # 등식 검산은 "대시=0" 가설로 돌린다. 값 자체는 승격 전까지 null 이다.
        out["dash_zero_candidate_억원"] = 0.0
        out["dash_promotion"] = {"promoted": False, "evidence": None}
    if rec.get("paren_reinterpreted_as_bracket"):
        out["paren_reinterpreted_as_bracket"] = True
        out["paren_evidence"] = rec.get("paren_evidence")
    return out


# ---------------------------------------------------------------------------
# 수용 등식 6개 (validation 정정티켓 §D). 허용오차 2.5억 = 억원 인쇄 반올림 5항 기준.
# 정수 key = 마스터 항목번호, 문자열 key = 구성 행.
# ---------------------------------------------------------------------------
EQ_TOL_EOK = 2.5
EQUATIONS = {
    "E1": (1, [(+1, "보험수익"), (-1, "보험서비스비용"), (+1, "재보험수익"),
               (-1, "재보험서비스비용"), (-1, 16)]),
    "E2": (17, [(+1, "투자수익"), (-1, "투자비용")]),
    "E3": (20, [(+1, 1), (+1, 17)]),
    "E4": (21, [(+1, "영업외수익"), (-1, "영업외비용")]),
    "E5": (22, [(+1, 20), (+1, 21)]),
    "E6": (24, [(+1, 22), (-1, 23)]),
}
EQ_TEXT = {
    "E1": "보험손익 = 보험수익 - 보험서비스비용 + 재보험수익 - 재보험서비스비용 - 기타사업비용",
    "E2": "투자손익 = 투자수익 - 투자비용",
    "E3": "영업이익 = 보험손익 + 투자손익",
    "E4": "영업외손익 = 영업외수익 - 영업외비용",
    "E5": "세전이익 = 영업이익 + 영업외손익",
    "E6": "당기순이익 = 세전이익 - 법인세비용",
}


def _rec_of(cell, key):
    if isinstance(key, int):
        return cell["items"].get(str(key))
    return cell["components"].get(key)


def _key_label(key):
    return TARGET_ITEMS[key] if isinstance(key, int) else key


def _eq_term(cell, key):
    """-> (value_eok|None, kind). kind in {value, dash, missing, read_failed}."""
    rec = _rec_of(cell, key)
    if rec is None:
        return None, "missing"
    state = rec.get("dash_state")
    if state == "PRINTED_DASH":
        return 0.0, "dash"       # 대시=0 가설
    if state == "READ_FAILED":
        return None, "read_failed"
    return rec.get("값_억원"), "value"


def run_equations(cell):
    """cell 에 equations / equation_summary 를 붙이고 (n_pass, n_fail, n_not_testable) 반환."""
    results = {}
    n_pass = n_fail = n_nt = 0
    for name, (lhs_key, rhs_terms) in EQUATIONS.items():
        terms = [(+1, lhs_key)] + [(s, k) for s, k in rhs_terms]
        missing, dashes, vals = [], [], {}
        for _sign, key in terms:
            v, kind = _eq_term(cell, key)
            if kind in ("missing", "read_failed"):
                missing.append(f"{_key_label(key)}({kind})")
                continue
            if kind == "dash":
                dashes.append(key)
            vals[key] = v
        if missing:
            results[name] = {"equation": EQ_TEXT[name], "status": "NOT_TESTABLE",
                             "missing_terms": missing}
            n_nt += 1
            continue
        lhs = vals[lhs_key]
        rhs = sum(sign * vals[key] for sign, key in rhs_terms)
        diff = round(lhs - rhs, 6)
        ok = abs(diff) <= EQ_TOL_EOK
        results[name] = {
            "equation": EQ_TEXT[name], "status": "PASS" if ok else "FAIL",
            "lhs_억원": round(lhs, 6), "rhs_억원": round(rhs, 6), "diff_억원": diff,
            "tolerance_억원": EQ_TOL_EOK,
            "dash_terms": [_key_label(k) for k in dashes],
        }
        if ok:
            n_pass += 1
        else:
            n_fail += 1
    cell["equations"] = results
    cell["equation_summary"] = {"pass": n_pass, "fail": n_fail, "not_testable": n_nt,
                                "failed": sorted(k for k, v in results.items() if v["status"] == "FAIL"),
                                "not_testable_list": sorted(k for k, v in results.items()
                                                            if v["status"] == "NOT_TESTABLE")}
    return n_pass, n_fail, n_nt


def adjudicate_printed_dashes(cell):
    """PRINTED_DASH 를 0 으로 승격할지 셀 안의 산수로 판정한다.

    승격 근거: 그 항목이 등장하는 등식 중 **PASS 이면서 그 항목이 유일한 대시 항**인 것이
    하나라도 있으면, 나머지 항이 전부 실값이므로 그 대시는 허용오차 안에서 0 임이 산수로
    증명된다. 대시가 둘 이상 낀 등식의 PASS 는 각각을 증명하지 못하므로 근거로 쓰지 않는다.
    근거가 없으면 null 로 남긴다 -- 추측으로 0 을 심지 않는다."""
    in_eq = {}
    for name, (lhs_key, rhs_terms) in EQUATIONS.items():
        for key in [lhs_key] + [k for _s, k in rhs_terms]:
            in_eq.setdefault(key, []).append(name)
    for store, keyfn in ((cell["items"], lambda s: int(s)), (cell["components"], lambda s: s)):
        for skey, rec in store.items():
            if rec.get("dash_state") != "PRINTED_DASH":
                continue
            key = keyfn(skey)
            proofs = []
            for name in in_eq.get(key, []):
                r = cell["equations"].get(name) or {}
                if r.get("status") != "PASS":
                    continue
                if r.get("dash_terms") != [_key_label(key)]:
                    continue  # 대시가 둘 이상 -> 개별 증명 불가
                proofs.append(f"{name}({EQ_TEXT[name]}) PASS, diff={r['diff_억원']}억 "
                              f"(허용 {EQ_TOL_EOK}억), 이 항이 유일한 대시")
            if proofs:
                rec["값_억원"] = 0.0
                rec["값"] = 0.0
                rec["dash_promotion"] = {"promoted": True, "evidence": "; ".join(proofs)}
            else:
                rec["dash_promotion"] = {
                    "promoted": False,
                    "evidence": None,
                    "reason": "표 안 산수로 0 임을 증명하는 등식이 없음 -- 값을 싣지 않는다(null)",
                }


def _quarter_end_iso(q):
    fy, qq = q.split(".")
    return {"1": f"{fy}-03-31", "2": f"{fy}-06-30", "3": f"{fy}-09-30", "4": f"{fy}-12-31"}[qq[0]]


# KR0004 예별손해 전체 제외 (validation 정정티켓 §B / 판정 결정 6).
KR0004_EXCLUDE_REASON = "KR0004_disclosure_vs_dart_scope_unresolved"
KR0004_EXCLUDE_NOTE = (
    "KR0004 2025.4Q 는 DART 감사보고서(제13기)와 마스터가 5개 항목 전건 일치하는데 경영공시 p.12 도 "
    "정확히 추출된다(보험손익 마스터 -221.36 vs 공시 -489 등) -- 양쪽 다 맞는데 다르다. 범위(P&A 전후 "
    "주체/감독회계 총괄계정) 불일치가 규명될 때까지 백필하지 않는다. 값은 규명용으로 남긴다. "
    "별건 티켓: inbox/parser/20260918T0705Z__validation__KR0004_2025.4Q__yebyeol_disclosure_vs_dart_scope.md"
)


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    cells_out = []
    status_counts = {}
    for code, q in target_cells():
        pdf_path = find_pdf(code, q)
        if pdf_path is None:
            cells_out.append({
                "원보험사코드": code, "원보험사명": COMPANIES[code], "공시분기": q,
                "status": "NO_PDF", "items": {}, "components": {},
            })
            status_counts["NO_PDF"] = status_counts.get("NO_PDF", 0) + 1
            continue
        status, page_no, found, warnings, bbox = find_and_extract(pdf_path)
        rel_pdf = os.path.relpath(pdf_path, ROOT).replace("\\", "/")
        manual = MANUAL_VISION_CELLS.get((code, q))
        if manual is not None and not found:
            status = "OK_VISION_MANUAL"
            page_no = manual["page"]
            found = {it: {"value_eok": float(v), "dash_zero": it in _MANUAL_DASH_ZERO.get((code, q), set()),
                          "raw_label": f"(vision:{TARGET_ITEMS[it]})", "raw_value": v}
                     for it, v in manual["values"].items()}
            warnings = (warnings or []) + [
                "순수 이미지 PDF -- find_tables 자동추출 불가, 240dpi 렌더링 후 육안 판독"
                "(항등식 20=1+17 / 22=20+21 / 24=22-23 자체검산 완료, 세션 기록 참고)."]
        cell = {
            "원보험사코드": code, "원보험사명": COMPANIES[code], "공시분기": q,
            "status": status, "source_file": rel_pdf, "page": page_no,
            "items": {}, "components": {},
        }
        if warnings:
            cell["warnings"] = warnings
        if found:
            method = "vision_manual" if status == "OK_VISION_MANUAL" else "geometry_table"
            for item_no in ITEM_ORDER:
                if item_no not in found:
                    continue
                cell["items"][str(item_no)] = _emit_rec(found[item_no], TARGET_ITEMS[item_no], method)
            for comp_key in COMPONENT_ORDER:
                if comp_key not in found:
                    continue
                cell["components"][comp_key] = _emit_rec(found[comp_key], comp_key, method)
        cells_out.append(cell)
        status_counts[status] = status_counts.get(status, 0) + 1

    # --- 수용 등식 + 대시 판정 + 병합 범위 확정 -------------------------------
    eq_counts = {"cells_all_pass": 0, "cells_reject": 0, "cells_not_testable": 0, "cells_no_data": 0}
    n_merge_candidates = 0
    prov_entries = []
    for cell in cells_out:
        if not cell["items"]:
            cell["acceptance"] = "NO_DATA"
            eq_counts["cells_no_data"] += 1
            continue
        _n_pass, n_fail, n_nt = run_equations(cell)
        adjudicate_printed_dashes(cell)
        if n_fail:
            cell["extraction_status"] = cell["status"]
            cell["status"] = "REJECT_SELF_CLOSURE"
            cell["acceptance"] = "REJECT_SELF_CLOSURE"
            eq_counts["cells_reject"] += 1
        elif n_nt:
            cell["acceptance"] = "EQ_NOT_TESTABLE"
            eq_counts["cells_not_testable"] += 1
        else:
            cell["acceptance"] = "ACCEPTED"
            eq_counts["cells_all_pass"] += 1

        excluded = cell["원보험사코드"] == "KR0004"
        if excluded:
            cell["backfill_excluded"] = KR0004_EXCLUDE_REASON
            cell["backfill_excluded_note"] = KR0004_EXCLUDE_NOTE

        merge_ok_cell = (cell["acceptance"] != "REJECT_SELF_CLOSURE") and not excluded
        for skey, rec in cell["items"].items():
            if int(skey) in CHECK_ONLY_ITEMS:
                rec["check_only"] = True
                rec["check_only_reason"] = CHECK_ONLY_REASON
                rec["merge_candidate"] = False
                continue
            rec["merge_candidate"] = bool(merge_ok_cell and rec["값"] is not None)
            if rec["merge_candidate"]:
                n_merge_candidates += 1
        for rec in cell["components"].values():
            rec["check_only"] = True
            rec["check_only_reason"] = "구성 행 -- 마스터 항목번호가 없다. 수용 등식 검산 전용."
            rec["merge_candidate"] = False

        if any(r.get("merge_candidate") for r in cell["items"].values()):
            prov_entries.append({
                "company_code": cell["원보험사코드"],
                "quarter": cell["공시분기"],
                "item_block": "income_statement",
                "source_id": "DISCLOSURE",
                "source_file": cell["source_file"],
                "as_of_date": _quarter_end_iso(cell["공시분기"]),
            })

    n_items_total = sum(len(c["items"]) for c in cells_out)
    n_comps_total = sum(len(c["components"]) for c in cells_out)
    n_cells_any = sum(1 for c in cells_out if c["items"])
    dash_counts = {"items": 0, "items_promoted": 0, "components": 0,
                   "components_promoted": 0, "read_failed": 0}
    for c in cells_out:
        for store, kind in ((c["items"], "items"), (c["components"], "components")):
            for rec in store.values():
                st = rec.get("dash_state")
                if st == "PRINTED_DASH":
                    dash_counts[kind] += 1
                    if rec["dash_promotion"]["promoted"]:
                        dash_counts[kind + "_promoted"] += 1
                elif st == "READ_FAILED":
                    dash_counts["read_failed"] += 1

    doc_out = {
        "note": ("경영공시 \u00a72-1 요약 포괄손익계산서(총괄) 백필 스테이징. 마스터 미반영"
                 "(PL_breakdown.json 은 이 스크립트가 절대 건드리지 않음). "
                 "단위: 값_억원=원문 그대로, 값=백만원(x100, 마스터 관례)."),
        "generated_by": "scripts/extract_pl_backfill_disclosure.py",
        "scope_source": ("inbox/parser/20260918T0700Z__validation__ALL_2023.1Q-2026.2Q__"
                         "disclosure_pl_backfill_scope_amend.md"),
        # 추출한 것(8) 과 마스터에 병합할 것(5) 은 다르다 -- 그 구분을 파일 안에 박아 둔다.
        # `target_item_numbers` 라는 옛 이름은 둘을 같은 것으로 읽게 해 혼동을 낳았다.
        "extracted_item_numbers": ITEM_ORDER,
        "backfill_item_numbers": BACKFILL_ITEMS,
        "check_only_item_numbers": CHECK_ONLY_ITEMS,
        "check_only_reason": CHECK_ONLY_REASON,
        "component_rows_note": ("구성 행 8개는 수용 등식 E1/E2/E4 검산 전용이다. 마스터 항목번호가 "
                                "없으므로 병합 대상이 아니며 items 와 섞지 않고 components 에 담는다."),
        "acceptance_equations": {k: EQ_TEXT[k] for k in sorted(EQ_TEXT)},
        "acceptance_tolerance_eok": EQ_TOL_EOK,
        "dash_state_policy": ("NORMAL=값 적재 / PRINTED_DASH=기본 null, 셀 안 산수로 0 이 증명될 "
                              "때만 승격(dash_promotion.evidence) / READ_FAILED=절대 적재 금지."),
        "merge_note": ("병합 시 값(백만원)만 쓴다. 값_당분기 는 build_root_masters.build_pl() 이 "
                       "모든 행의 값_당분기를 버리고 _flow_dangi(YTD) 로 무조건 재계산하므로 "
                       "여기서 만들지 않는다."),
        "status_counts": status_counts,
        "acceptance_counts": eq_counts,
        "dash_counts": dash_counts,
        "n_target_cells": len(cells_out),
        "n_cells_with_any_item": n_cells_any,
        "n_item_values_total": n_items_total,
        "n_component_values_total": n_comps_total,
        "n_merge_candidate_values": n_merge_candidates,
        "provenance_entries_note": ("마스터 병합 시 PL_breakdown_provenance.json 의 cells 에 "
                                    "그대로 append 할 항목. DISCLOSURE 계보이므로 DART 라벨을 "
                                    "달지 않는다."),
        "provenance_entries": prov_entries,
        "cells": cells_out,
    }
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(doc_out, f, ensure_ascii=False, indent=1)

    print("status_counts:", status_counts)
    print("acceptance:", eq_counts)
    print("dash:", dash_counts)
    print("cells with >=1 item:", n_cells_any, "/", len(cells_out))
    print("item-values:", n_items_total, " component-values:", n_comps_total)
    print("merge candidates (5 items, KR0004 excluded):", n_merge_candidates)
    print("provenance entries:", len(prov_entries))
    print("wrote:", OUT_PATH)


if __name__ == "__main__":
    main()
