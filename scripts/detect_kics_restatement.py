# -*- coding: utf-8 -*-
"""K-ICS 소급재작성(restatement) 탐지기 — 분기 라운드마다 한 번 돌린다.

## 무엇을 재나

한 분기 공시본의 `[경과조치 적용 전 지급여력비율 세부]` 표는 **3개 열**을 인쇄한다:
해당분기 · 직전분기 · 전전분기. 그러므로 같은 (회사, 분기) 값이 **두 번(또는 세 번)
인쇄**된다 — 그 분기 자신의 공시본에서 한 번, 다음 분기 공시본의 '직전분기' 칸에서 또 한 번.

**둘이 다르면 발행사가 그 분기를 소급재작성한 것이다.** 이 탐지기는 그 두 인쇄값을
**필링 대 필링**으로 대조한다. 마스터는 판정에 끼지 않는다(마스터가 틀렸을 가능성과
발행사가 재작성했을 가능성을 섞지 않기 위해서다). 마스터는 **셋째 축**으로만 쓴다 —
마스터 `값` 이 원(原)공시본과 같은지(= 마스터가 as-filed 기준인지) 따로 본다.

## 왜 필요했나 (2026-09-01)

2026.1Q 대비 2026.2Q 변동 분석 중 교보생명(KR0073)이 2026.1Q 를 소급재작성한 것이
**손으로** 발견됐다. 그때까지 이 축을 재는 검사기는 저장소에 **0개**였다. 재작성은
회사의 정당한 행위지만, 탐지되지 않으면 두 가지가 조용히 일어난다:
  ① 다음 라운드에 누가 또 발견해서 같은 조사를 반복한다(이번이 그랬다).
  ② 마스터가 재작성값으로 갈아끼워져도(= 분기별 기준이 갈라져도) 아무도 모른다.
     이 저장소에는 이미 그 사고가 있다 — `csm_amort_identity_ledger.json` 의
     `RESTATEMENT_BASIS` 3건(DB손해 2023.1~3Q): 루트 CSM_waterfall 은 2024년 필링의
     비교컬럼(=재작성값)이고 PL 은 2023년 원 필링값이라 두 마스터가 서로 안 닫힌다.

## 오탐 방지 (1차 손스캔이 낸 오탐의 원인 3가지를 전부 막았다)

1. **표를 정확히 하나 특정한다.** 라벨만 느슨하게 찾으면 단위가 다른 다른 표
   (백만원 단위 경과조치표 · 요약재무상태표)를 긁는다. 여기서는 `분산효과` +
   `기본요구자본` + `지급여력기준금액` 이 **같은 페이지**에 있는 곳만 표로 인정하고,
   그 페이지의 숫자 x좌표 히스토그램에서 우측 3개 컬럼대만 취한다.
2. **소수자리를 원 토큰에서 센다.** 인쇄값을 float 로 바꾼 뒤 문자열화하면 정수
   `"4160"` 이 `"4160.0"` 이 되어 1자리로 잡히고, 소수를 가진 마스터(4159.89)와의
   반올림 차가 전부 '재작성' 으로 둔갑한다(악사 8건이 그렇게 나왔다).
3. **item27(지급여력비율)은 파생값이라 축에서 뺀다.** 마스터는 item1/item14x100 을
   소수 8자리로 담는데 공시본은 1~2자리로 인쇄한다 — 항상 어긋난다. 대신 부모
   item1/item14 의 재작성이 그 사실을 이미 말해 준다(참고용으로 같이 인쇄한다).

## 스캔 PDF (텍스트레이어 없음) 처리

`data/disclosure/` 는 .gitignore 대상이고, 5사는 PDF 가 이미지라 fitz 로 못 읽는다
(2026.2Q 라운드 실측: KR0010 · KR0049 · KR0079 · KR0080 · KR0087 중 하나 이상의 분기).
**"키워드 0회 = 원문 없음" 으로 단정하지 않는다** — 그 분기 페이지를 렌더링해 육안 판독한
값을 `VISION_ANCHORS` 에 인용(파일·페이지)과 함께 박아 두고, 판정에 그대로 쓴다.
판독 근거가 없는 (회사,분기)는 조용히 빠지지 않고 **UNCOVERED 로 센다.**
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DISC = ROOT / "data" / "disclosure"
MASTER = ROOT / "kics_disclosure.json"
LEDGER = ROOT / "data" / "_gold" / "kics_restatement_ledger.json"

NUM_RE = re.compile(r"^[\(\[]?[-△▲−]?[\d,]+(?:\.\d+)?[\)\]]?%?$")

# 표의 행 순서는 감독원 서식이라 고정이다. 정규화 라벨(한글+숫자만)에 대한 앵커를
# **순서대로 소비**한다 — 같은 앵커가 뒤 항목에 다시 걸리는 것을 막는다.
ANCHORS = [
    (1,  ("지급여력금액기본자본", "지급여력금액")),
    (2,  ("기본자본",)),
    (3,  ("보완자본",)),
    (4,  ("건전성감독기준재무상태표",)),
    (5,  ("보통주",)),
    (6,  ("자본항목중보통주이외",)),
    (7,  ("이익잉여금",)),
    (8,  ("자본조정",)),
    (9,  ("기타포괄손익누계액",)),
    (10, ("비지배지분",)),
    (11, ("조정준비금",)),
    # KR0099(KB라이프)는 이 행 라벨을 "**지분**여력금액으로 불인정하는 항목" 으로 오식한다
    # (2026.1Q·2Q 양쪽 동일). 변형을 안 넣으면 그 회사 item12 가 통째로 미비교로 빠진다.
    (12, ("지급여력금액으로불인정", "지분여력금액으로불인정")),
    (13, ("보완자본으로재분류",)),
    (14, ("지급여력기준금액",)),
    (15, ("기본요구자본",)),
    (16, ("분산효과",)),
    (17, ("생명장기손해보험위험액", "생명장기위험액")),
    (18, ("일반손해보험위험액",)),
    (19, ("시장위험액",)),
    (20, ("신용위험액",)),
    (21, ("운영위험액",)),
    (22, ("법인세조정액",)),
    (23, ("기타요구자본",)),
    (24, ("업권별자본규제",)),
    (25, ("비례성원칙",)),
    (26, ("업권별자본규제",)),
    (27, ("지급여력비율",)),
]
DISAMBIG = {24: "종속회사", 26: "관계회사"}

# item27 은 마스터에서 item1/item14x100 파생이고 공시본은 1~2자리로 인쇄한다.
# 재작성 판정에서 뺀다(부모 item1/item14 가 이미 말해 준다).
DERIVED_ITEMS = {27}

# ---------------------------------------------------------------------------
# 육안 판독 앵커 — 텍스트레이어가 없는 PDF. 값은 240dpi 렌더링 이미지에서 직접 읽었다.
# `method: vision` 으로 등재부에 기록된다. 새 분기를 스캔할 때 그 분기의 스캔 PDF 도
# 같은 방식으로 여기에 추가한다(추가하지 않으면 UNCOVERED 로 센다 — 조용히 빠지지 않는다).
# ---------------------------------------------------------------------------
VISION_ANCHORS = {
    # (period, code, column) -> {item: value}
    #   column "cur"  = 그 공시본의 '해당분기' 열
    #   column "prev" = 그 공시본의 '직전분기' 열
    ("FY2026_Q1", "KR0010", "cur"): {
        "_src": "data/disclosure/FY2026_Q1/raw/KR0010_KB손해보험.pdf p18 (인쇄 16)",
        "_read": "validation 2026-09-01, fitz 150dpi 렌더링 육안 판독",
        1: 123858, 2: 51081, 3: 72778, 4: 112004, 5: 665, 6: None, 7: 71334, 8: 0,
        9: -12864, 10: 66, 11: 52804, 12: 508, 13: 60415, 14: 66638, 15: 91178,
        16: 35581, 17: 62532, 18: 10624, 19: 33994, 20: 14515, 21: 5095, 22: 24671,
        23: 131, 24: None, 25: 131, 26: None,
    },
    ("FY2026_Q2", "KR0010", "prev"): {
        "_src": "data/disclosure/FY2026_Q2/pdf/KR0010_KB손해보험.pdf p20 (인쇄 18)",
        "_read": "validation 2026-09-01, fitz 150dpi 렌더링 육안 판독",
        1: 123858, 2: 51081, 3: 72778, 4: 112004, 5: 665, 6: None, 7: 71334, 8: 0,
        9: -12864, 10: 66, 11: 52804, 12: 508, 13: 60415, 14: 66638, 15: 91178,
        16: 35581, 17: 62532, 18: 10624, 19: 33994, 20: 14515, 21: 5095, 22: 24671,
        23: 131, 24: None, 25: 131, 26: None,
    },
    ("FY2026_Q1", "KR0049", "cur"): {
        "_src": "data/disclosure/FY2026_Q1/raw/KR0049_악사손해보험.pdf p16-17 (인쇄 15-16)",
        "_read": "validation 2026-09-01, fitz 150dpi 렌더링 육안 판독",
        1: 4160, 2: 1526, 3: 2634, 4: 3820, 5: 2509, 6: 0, 7: 558, 8: 124, 9: -59,
        10: 0, 11: 689, 12: 0, 13: 2294, 14: 2677, 15: 2849, 16: 1314, 17: 1844,
        18: 1364, 19: 584, 20: 131, 21: 241, 22: 172, 23: 0, 24: 0, 25: 0, 26: 0,
    },
    ("FY2026_Q1", "KR0079", "cur"): {
        "_src": "data/disclosure/FY2026_Q1/raw/KR0079_미래에셋생명.pdf p18-19 (인쇄 18-19/32)",
        "_read": "validation 2026-09-01, fitz 150dpi 렌더링 육안 판독",
        1: 37179, 2: 23151, 3: 14028, 4: 31231, 5: 10671, 6: None, 7: 17783, 8: -218,
        9: -5174, 10: None, 11: 8170, 12: None, 13: 8081, 14: 22187, 15: 26781,
        16: 8030, 17: 18358, 18: None, 19: 10739, 20: 3882, 21: 1832, 22: 4594,
        23: None, 24: None, 25: None, 26: None,
    },
    ("FY2026_Q2", "KR0079", "prev"): {
        "_src": "data/disclosure/FY2026_Q2/pdf/KR0079_미래에셋생명.pdf p19-20 (인쇄 19-20/65)",
        "_read": "validation 2026-09-01, fitz 150dpi 렌더링 육안 판독",
        1: 37179, 2: 23151, 3: 14028, 4: 31231, 5: 10671, 6: None, 7: 17783, 8: -218,
        9: -5174, 10: None, 11: 8170, 12: None, 13: 8081, 14: 22187, 15: 26781,
        16: 8030, 17: 18358, 18: None, 19: 10739, 20: 3882, 21: 1832, 22: 4594,
        23: None, 24: None, 25: None, 26: None,
    },
    ("FY2026_Q1", "KR0080", "cur"): {
        "_src": "data/disclosure/FY2026_Q1/raw/KR0080_에이아이에이생명보험.pdf p18 (인쇄 18/36)",
        "_read": "validation 2026-09-01, fitz 150dpi 렌더링 육안 판독",
        1: 29617, 2: 25338, 3: 4280, 4: 29635, 5: 15082, 6: None, 7: 14183, 8: None,
        9: -3950, 10: None, 11: 4320, 12: 18, 13: 4280, 14: 15350, 15: 20197,
        16: 6307, 17: 12892, 18: None, 19: 8281, 20: 3509, 21: 1823, 22: 4847,
        23: None, 24: None, 25: None, 26: None,
    },
    ("FY2026_Q1", "KR0087", "cur"): {
        "_src": "data/disclosure/FY2026_Q1/raw/KR0087_동양생명.pdf p16-17 (인쇄 16-17)",
        "_read": "validation 2026-09-01, fitz 150dpi 렌더링 육안 판독",
        1: 43457, 2: 15920, 3: 27537, 4: 31994, 5: 12705, 6: None, 7: 16443,
        8: -1169, 9: -9493, 10: None, 11: 13508, 12: 943, 13: 16074, 14: 22926,
        15: 27456, 16: 7489, 17: 19842, 18: None, 19: 6650, 20: 5766, 21: 2687,
        22: 4530, 23: None, 24: None, 25: None, 26: None,
    },
    ("FY2026_Q2", "KR0087", "prev"): {
        "_src": "data/disclosure/FY2026_Q2/pdf/KR0087_동양생명.pdf p16 (인쇄 16)",
        "_read": "validation 2026-09-01, fitz 150dpi 렌더링 육안 판독",
        1: 43457, 2: 15920, 3: 27537, 4: 31994, 5: 12705, 6: None, 7: 16443,
        8: -1169, 9: -9493, 10: None, 11: 13508, 12: 943, 13: 16074, 14: 22926,
        15: 27456, 16: 7489, 17: 19842, 18: None, 19: 6650, 20: 5766, 21: 2687,
        22: 4530, 23: None, 24: None, 25: None, 26: None,
    },
}


# ---------------------------------------------------------------------------
# 좌표 추출이 못 잡는 잔여 셀 — raw 텍스트에서 직접 판독한 값. 인용을 같이 둔다.
# **비지 않게 두는 것이 목적이다**: 미비교 칸을 CLEAN 에 섞으면 그게 false-green 이다.
# 형식: (period, code, column, item) -> (값, "원문 인용")
# ---------------------------------------------------------------------------
MANUAL_CELL_ANCHORS = {
    ("FY2026_Q1", "KR0005", "cur", 17): (21398, "'1. 생명장기손해보험'/'위험액' 다음 '21,398' (p14)"),
    ("FY2026_Q2", "KR0005", "prev", 17): (21398, "'1. 생명장기손해보험'/'위험액' 다음 2번째 '21,398' (p16)"),
    ("FY2026_Q1", "KR0009", "cur", 17): (69044, "'1. 생명장기손해보험 '/'위험액 ' 다음 '69,044' (p18)"),
    ("FY2026_Q2", "KR0009", "prev", 17): (69044, "'1. 생명장기손해보험 '/'위험액 ' 다음 2번째 '69,044' (p19)"),
    ("FY2026_Q1", "KR0050", "cur", 13): (5434, "'Ⅲ. 보완자본으로 재분류하는 항목' 다음 '5,434' (p17)"),
    ("FY2026_Q2", "KR0050", "prev", 13): (5434, "'Ⅲ. 보완자본으로 재분류하는 항목' 다음 2번째 '5,434' (p18)"),
    ("FY2026_Q1", "KR0068", "cur", 6): (30685, "'2. 자본항목 중 보통주 이외의 자본증권' 다음 '30,685' (p18)"),
    ("FY2026_Q2", "KR0068", "prev", 6): (30685, "'자본항목 중 보통주 이외의 '/'자본증권' 다음 2번째 '30,685' (p18)"),
    ("FY2026_Q1", "KR0003", "cur", 13): (23147, "'Ⅲ. 보완자본으로 재분류하는 항목' 다음 '23,147' (p21)"),
    ("FY2026_Q2", "KR0003", "prev", 13): (23147, "'Ⅲ. 보완자본으로 재분류하는 항목' 다음 2번째 '23,147' (p22)"),
}


def norm(s: str) -> str:
    return re.sub(r"[^0-9가-힣]", "", s or "")


def parse_num(tok: str):
    """(값, 소수자리). 소수자리는 **원 토큰**에서 센다 — float 화 후에 세면 안 된다."""
    t = (tok or "").strip().replace(",", "").replace("%", "").replace(" ", "")
    neg = False
    if t.startswith("(") and t.endswith(")"):
        neg, t = True, t[1:-1]
    if t[:1] in ("△", "▲", "-", "−"):
        neg, t = True, t[1:]
    if t in ("", "-", "–", "—"):
        return None, 0
    try:
        v = float(t)
    except ValueError:
        return None, 0
    return (-v if neg else v), (len(t.split(".")[1]) if "." in t else 0)


def find_pdf(period: str, code: str):
    """분기마다 디렉토리와 회사명 표기가 다르다 (FY2026_Q1 은 raw/ 이고
    KR0004_예별손해보험 / KR0069_삼성생명보험 / KR0099_KB라이프생명). 코드로만 찾는다."""
    for sub in ("pdf", "raw"):
        d = DISC / period / sub
        if d.is_dir():
            hits = sorted(d.glob(f"{code}_*.pdf"))
            if hits:
                return hits[0]
    return None


_HEAD_RE = re.compile(r"경과조치적용전지급여력비율세부")

# 표에서 '새 행의 머리' 처럼 보이는 줄. 괄호 설명줄·이어짐줄은 여기 안 걸린다.
_ROW_START = re.compile(r"^\s*(?:[0-9]{1,2}\s*[.)]|[ⅠⅡⅢⅣIV]+\s*\.|[가나다]\s*[.)]|-\s*분산)")

# 표의 마지막 행: `다. 지급여력비율 : 가 ÷ 나 × 100` (공백 제거 후). 회사마다 구두점이
# 달라서 나눗셈 기호·곱셈 기호·100 만 본다.
_RATIO_ROW_RE = re.compile(r"지급여력비율[^가-힣]{0,12}가[^가-힣]{0,4}나[^0-9]{0,4}100")


def table_pages(doc):
    """표가 걸쳐 있는 페이지들. **한 페이지만 보면 안 된다** — 2026.2Q 실측에서 삼성생명은
    항목1~13 이 앞 페이지에, 14~27 이 뒷 페이지에 있어서 단일 페이지 스캔이 13개 항목을
    통째로 못 보고도 'CLEAN' 을 찍었다(그 축이 깨끗한 게 아니라 순회조차 안 된 것).
    신한이지·카카오페이·처브·BNP 는 반대로 22~26 이 다음 장에 있었다."""
    start = None
    for pno in range(doc.page_count):
        if _HEAD_RE.search(re.sub(r"\s", "", doc[pno].get_text())):
            start = pno
            break
    if start is None:                       # 헤딩 변형 — 대표 행 라벨로 재탐색
        for pno in range(doc.page_count):
            t = doc[pno].get_text()
            if "분산효과" in t and "기본요구자본" in t and "지급여력기준금액" in t:
                start = pno
                break
    if start is None:
        return []
    # 표의 **마지막 행**은 `다. 지급여력비율 : 가 ÷ 나 x 100` 이다. 그 행이 나온 페이지에서
    # 멈춘다 — 뒤로 더 가면 같은 절의 백만원 단위 경과조치표를 같이 긁어서 매핑이 오염된다
    # (KR0097 실측: 3페이지를 통째로 먹어 item11 이 item10 으로 밀렸고 가짜 재작성 1건이 났다).
    pages = []
    for pno in range(start, min(start + 3, doc.page_count)):
        pages.append(pno)
        if _RATIO_ROW_RE.search(re.sub(r"\s", "", doc[pno].get_text())):
            break
    return pages


def pdf_rows(page, cols=None):
    """[(라벨, [(값,소수) x3])] — y로 줄을 묶고, 숫자 없는 줄은 가장 가까운 숫자 줄의
    라벨로 합친다(셀이 2~3줄에 걸치는 서식). 단, 서로 다른 항목 앵커를 가진 줄끼리는
    합치지 않는다 — 합치면 두 항목이 한 행으로 뭉쳐 매핑이 밀린다."""
    words = sorted(page.get_text("words"), key=lambda w: ((w[1] + w[3]) / 2, w[0]))
    lines = []
    for w in words:
        yc = (w[1] + w[3]) / 2
        if lines and abs(lines[-1][0] - yc) <= 3.0:
            lines[-1][1].append(w)
        else:
            lines.append([yc, [w]])

    if cols is None:
        xs = sorted((w[0] + w[2]) / 2 for _, ws in lines for w in ws if NUM_RE.match(w[4]))
        if len(xs) < 20:
            return [], None
        cl = []
        for x in xs:
            if cl and x - cl[-1][-1] <= 12:
                cl[-1].append(x)
            else:
                cl.append([x])
        cl = [c for c in cl if len(c) >= 8]
        if len(cl) < 3:
            return [], None
        cols = cl[-3:]
    col_lo = min(cols[0]) - 30

    numl, lbll = [], []
    for yc, ws in lines:
        # **떨어진 음수부호를 붙인다.** 일부 발행사는 `- 21,170` 처럼 마이너스와 숫자 사이에
        # 공백을 둬서 fitz 가 두 단어로 준다. 그대로 두면 부호가 사라져 음수가 양수로
        # 읽힌다(삼성생명 2026.1Q 자본조정 -21,170 -> +21,170, Δ 42,340억 오탐).
        toks = []
        for i, w in enumerate(ws):
            t = w[4]
            if NUM_RE.match(t) and t[:1] not in ("-", "△", "▲", "−", "(") and i > 0:
                prev = ws[i - 1]
                if prev[4].strip() in ("-", "△", "▲", "−") and (w[0] - prev[2]) <= 6:
                    t = "-" + t
            toks.append((w, t))
        nums = [((w[0] + w[2]) / 2, t) for w, t in toks
                if NUM_RE.match(t) and (w[0] + w[2]) / 2 >= col_lo]
        ws = [w for w, _t in toks]
        lbl = " ".join(w[4] for w in ws if (w[0] + w[2]) / 2 < col_lo)
        if len(nums) >= 2:
            # [y, 병합라벨, 숫자, **그 줄 자신의 라벨**]. 자기 라벨을 따로 들고 있는 이유:
            # 이웃 행의 라벨이 병합돼 들어오면 앵커가 두 개 잡혀 매핑이 밀린다
            # (KR0097 실측: 조정준비금 행에 '6. 비지배지분' 이 붙어 item10 으로 매핑됐고
            #  가짜 재작성 1건이 났다). 매핑은 **자기 라벨 우선**으로 판정한다.
            numl.append([yc, lbl, nums, lbl])
        elif lbl.strip():
            lbll.append([yc, lbl])

    def anchors_of(s):
        n = norm(s)
        return {it for it, aa in ANCHORS if any(a in n for a in aa)}

    # 라벨 전용 줄은 **가장 가까운 숫자 줄**에 붙인다(셀이 2~3줄에 걸치는 서식).
    # '아래 첫 숫자행' 모델도 시험해 봤으나 실측이 더 나빴다(비교 817 -> 808칸).
    for yc, lbl in lbll:
        if not numl:
            continue
        near = min(numl, key=lambda n: abs(n[0] - yc))
        if abs(near[0] - yc) > 14:
            continue
        # 다른 항목 두 개를 한 행으로 뭉치지 않는다 — 단 **양쪽 다 행 머리처럼 생겼을 때만**.
        # 괄호 설명줄("(기본자본 자본증권의 인정한도를 초과한 금액 등)")은 새 행이 아니라
        # 앞 행의 이어짐인데, 그 안의 '기본자본' 이 item2 앵커에 걸린다. 이 조건을
        # 한쪽만 보고 걸었을 때 **item13 이 12개사에서 통째로 미비교**였다(2026.2Q 실측).
        if _ROW_START.match(lbl.strip()) and _ROW_START.match(near[1].strip()) \
                and anchors_of(near[1]) and anchors_of(lbl) \
                and not (anchors_of(near[1]) & anchors_of(lbl)):
            continue
        near[1] = (near[1] + " " + lbl) if near[0] > yc else (lbl + " " + near[1])

    out = []
    for _yc, lbl, nums, own in numl:
        vals = []
        for c in cols:
            lo, hi = min(c) - 22, max(c) + 22
            got = [t for x, t in nums if lo <= x <= hi]
            vals.append(parse_num(got[0]) if got else (None, 0))
        out.append((lbl, vals, own))
    return out, cols


def map_items(rows):
    """행 -> 항목번호. 앵커를 **순서대로 소비**해 단조성을 강제한다(같은 앵커가 뒤 항목에
    다시 걸리는 것을 막는다). 판정은 그 행 **자신의 라벨 우선**, 못 잡으면 병합 라벨."""
    mapped, unmatched, ai = {}, [], 0
    labels = {}
    for row in rows:
        lbl, vals = row[0], row[1]
        own = row[2] if len(row) > 2 else lbl

        def probe(text, start):
            n = norm(text)
            if not n:
                return None
            for k in range(start, len(ANCHORS)):
                item, aa = ANCHORS[k]
                if any(a in n for a in aa):
                    if item in DISAMBIG and DISAMBIG[item] not in n:
                        continue
                    return k, item
            return None

        hit = probe(own, ai) or probe(lbl, ai)
        if hit is None:
            if norm(lbl):
                unmatched.append(lbl.strip()[:60])
            continue
        ai = hit[0] + 1
        mapped[hit[1]] = vals
        labels[hit[1]] = (own or lbl).strip()[:60]
    return mapped, labels, unmatched


def extract(period: str, code: str, column: str):
    """(값맵 {item: (값,소수)}, 출처문자열, 방법, 에러). column = 'cur' | 'prev'."""
    va = VISION_ANCHORS.get((period, code, column))
    if va:
        vals = {k: (float(v), 0) for k, v in va.items()
                if isinstance(k, int) and isinstance(v, (int, float))}
        return vals, va["_src"], "vision", None
    p = find_pdf(period, code)
    if p is None:
        return None, None, None, f"{period} 에 {code} PDF 가 없다"
    import fitz
    doc = fitz.open(p)
    pages = table_pages(doc)
    if not pages:
        doc.close()
        return None, None, None, ("텍스트레이어 없음(스캔 PDF) — 렌더링 육안 판독 후 "
                                  "VISION_ANCHORS 에 등재할 것")
    rows, cols = [], None
    for pno in pages:
        r, cols = pdf_rows(doc[pno], cols)
        rows.extend(r)
    doc.close()
    if not rows:
        return None, None, None, "표 페이지는 찾았으나 숫자 그리드를 못 잡았다"
    mapped, _labels, unmatched = map_items(rows)
    idx = {"cur": 0, "prev": 1, "prev2": 2}[column]
    src = f"{p.relative_to(ROOT).as_posix()} p{'+'.join(str(x+1) for x in pages)}"
    vals = {it: v[idx] for it, v in mapped.items()}
    manual = 0
    for it in range(1, 28):
        if vals.get(it, (None, 0))[0] is not None:
            continue
        hit = MANUAL_CELL_ANCHORS.get((period, code, column, it))
        if hit:
            vals[it] = (float(hit[0]), 0)
            manual += 1
    return vals, (src + (f" +manual x{manual}" if manual else "")), "pdf_text", None


def differs(a, b):
    """(값,소수) 두 개. 거친 쪽 소수자리로 맞춘 뒤 반올림 폭 밖인지."""
    (va, da), (vb, db) = a, b
    if va is None or vb is None:
        return None, False
    dec = min(da, db)
    d = round(round(va, dec) - round(vb, dec), max(dec, 3))
    tol = 0.5 if dec == 0 else 0.5 * (10 ** -dec)
    return d, abs(d) > tol + 1e-9


def _num(v):
    if isinstance(v, (int, float)):
        return float(v)
    if isinstance(v, str):
        try:
            return float(v.replace(",", "").strip())
        except ValueError:
            return None
    return None


def period_to_quarter(period: str) -> str:
    m = re.match(r"FY(\d{4})_Q(\d)", period)
    return f"{m.group(1)}.{m.group(2)}Q" if m else period


def load_master():
    mv = defaultdict(dict)
    names = {}
    for r in json.loads(MASTER.read_text(encoding="utf-8")):
        if isinstance(r.get("항목번호"), int):
            mv[(r.get("원보험사코드"), r.get("공시분기"))][r["항목번호"]] = r.get("값")
        names.setdefault(r.get("원보험사코드"), r.get("원수사명"))
    return mv, names


def scan(period: str, prior: str):
    """restating filing(period) 의 '직전분기' 열  vs  prior filing 의 '해당분기' 열."""
    q_restated = period_to_quarter(prior)
    mv, names = load_master()
    codes = sorted({c for (c, _q) in mv} )
    out = {"restating_period": period, "restated_period": prior,
           "restated_quarter": q_restated, "companies": {}}
    for code in codes:
        cur, src_cur, m_cur, e_cur = extract(period, code, "prev")
        pri, src_pri, m_pri, e_pri = extract(prior, code, "cur")
        rec = {"name": names.get(code), "err_restating": e_cur, "err_prior": e_pri,
               "src_restating": src_cur, "src_prior": src_pri,
               "method": f"{m_cur or '-'}/{m_pri or '-'}",
               "compared": 0, "restated": [], "unavailable": []}
        if cur is None or pri is None:
            rec["status"] = "UNCOVERED"
            out["companies"][code] = rec
            continue
        master_q = mv.get((code, q_restated), {})
        rec["partial"] = []
        rec["uncompared"] = []
        for it in range(1, 28):
            if it in DERIVED_ITEMS:
                continue
            a, b = cur.get(it), pri.get(it)
            av = a[0] if a else None
            bv = b[0] if b else None
            if av is not None and bv is not None:
                rec["compared"] += 1
                d, bad = differs(a, b)
                if bad:
                    rec["restated"].append({
                        "item": it,
                        "as_filed": bv,         # 원공시본이 인쇄한 값
                        "restated": av,         # 다음 분기 공시본이 인쇄한 값
                        "delta": round(av - bv, 3),
                        "master": master_q.get(it),
                        "basis": "filing_vs_filing",
                    })
                continue

            # --- 한쪽만 추출된 칸: 마스터를 남은 한쪽의 대역(代役)으로 쓴다 ---
            # 약한 검사다(마스터 자신이 as-filed 라는 가정이 한 겹 들어간다) → basis 를 남긴다.
            mnum = _num(master_q.get(it))
            one = av if av is not None else bv
            if one is not None and mnum is not None:
                rec["compared"] += 1
                rec["partial"].append(it)
                d = round(one - mnum, 3)
                if abs(d) > 0.5:
                    rec["restated"].append({
                        "item": it,
                        "as_filed": mnum if av is not None else bv,
                        "restated": av if av is not None else mnum,
                        "delta": d if av is not None else -d,
                        "master": master_q.get(it),
                        "basis": "partial_master_proxy",
                    })
                continue

            rec["unavailable"].append(it)
            # 원문이 '-' 인 칸(마스터도 0/없음)은 정상. 마스터가 값을 갖고 있는데 비교를
            # 못 했으면 그건 **검사 사각**이라 따로 센다 — CLEAN 에 섞지 않는다.
            if mnum is not None and abs(mnum) >= 0.5:
                rec["uncompared"].append(it)
        rec["status"] = "RESTATED" if rec["restated"] else "CLEAN"
        out["companies"][code] = rec
    return out


def build_ledger(scan_result: dict, reason: dict[str, str] | None = None) -> dict:
    reason = reason or {}
    q = scan_result["restated_quarter"]
    entries = {}
    for code, rec in scan_result["companies"].items():
        for c in rec["restated"]:
            entries[f"{code}|{q}|{c['item']}"] = {
                "company": code, "company_name": rec["name"], "quarter": q,
                "item": c["item"],
                "as_filed": c["as_filed"],
                "restated": c["restated"],
                "delta": c["delta"],
                "as_filed_source": rec["src_prior"],
                "restated_source": rec["src_restating"],
                "method": rec["method"],
                "issuer_reason": reason.get(code, ""),
                "detected_by": "scripts/detect_kics_restatement.py (validation 2026-09-01)",
            }
    covered = {c: r["status"] for c, r in scan_result["companies"].items()}
    return {
        "_what": ("K-ICS 소급재작성 등재부. 발행사가 **이미 공시한 분기의 값을 다음 분기 "
                  "공시본의 '직전분기' 칸에서 다르게 인쇄**한 셀의 건별 기록이다. "
                  "재작성 자체는 발행사의 정당한 행위라 RED 이 아니다 — 이 등재부의 목적은 "
                  "(1) 다음 라운드가 같은 조사를 반복하지 않게 하고 "
                  "(2) **마스터가 조용히 재작성 기준으로 갈아끼워지는 것을 잡는 것**이다."),
        "_policy": ("이 저장소의 K-ICS 마스터는 각 분기의 **원공시본(as-filed)** 을 담는다. "
                    "재작성값으로 백필하지 않는다. 근거·유의사항은 `_policy_note` 참조."),
        "_policy_note": (
            "2026-09-01 실측: 이 정책은 그때까지 저장소 어디에도 **선언돼 있지 않았다.** "
            "가장 가까운 서술은 `data/_gold/kics_exemption_provenance.json` 의 KR0032 "
            "2024.3Q 엔트리(‘as-disclosed 를 그대로 두는 것이 이 저장소의 발행사 기재대로 "
            "원칙과 일치한다’)인데, 같은 엔트리가 **‘as-disclosed 를 유지할지 as-restated 를 "
            "채택할지는 owner/parser 정책 결정이고 이 세션은 정하지 않았다’** 라고 명시한다. "
            "즉 관행일 뿐 결정이 아니었다. 그리고 **IFRS17 CSM 축에서는 owner 가 반대로 "
            "결정했다** — 2026-06-20 교보/라이나 건에서 '후속 분기 공시의 전기(비교) 테이블에서 "
            "재작성값을 pull 해 마스터를 재작성 기준으로 통일' 을 채택했다"
            "(`scripts/validate_master_tables.py` L797-799 주석 · "
            "`inbox/_resolved/20260620T0600Z__validation__KR0073__kyobo_csm_priorperiod_pull_from_comparative.md` · "
            "`data/_gold/user_csm_cells.json` 의 '교보 재작성 기준 통일 58,249.2'). "
            "따라서 **저장소 전체가 as-filed 로 정렬돼 있다는 서술은 사실이 아니다** — "
            "K-ICS 는 as-filed, CSM_waterfall 은 일부 셀이 as-restated 다. "
            "이 등재부가 선언하는 것은 **K-ICS 마스터의 기준**이며, 바꾸려면 owner 결정이 필요하다."),
        "_severity": ("등재된 재작성 셀 자체 = YELLOW(정보). 마스터가 그 셀에서 as_filed 를 "
                      "벗어나면 = RED(기준이 갈라진다). 결측 = RED(SKIP 아님)."),
        "_scanned": {"restating_period": scan_result["restating_period"],
                     "restated_period": scan_result["restated_period"],
                     "restated_quarter": q,
                     "companies_total": len(covered),
                     "clean": sum(1 for v in covered.values() if v == "CLEAN"),
                     "restated": sum(1 for v in covered.values() if v == "RESTATED"),
                     "uncovered": sorted(c for c, v in covered.items() if v == "UNCOVERED"),
                     "per_company_status": covered},
        "entries": entries,
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--period", default="FY2026_Q2", help="재작성한(=최신) 공시본")
    ap.add_argument("--prior", default="FY2026_Q1", help="재작성당한(=직전) 공시본")
    ap.add_argument("--write", action="store_true", help=f"{LEDGER.name} 갱신")
    ap.add_argument("--json-out", help="스캔 원본을 이 경로에 저장")
    a = ap.parse_args(argv)

    res = scan(a.period, a.prior)
    if a.json_out:
        Path(a.json_out).write_text(json.dumps(res, ensure_ascii=False, indent=1),
                                    encoding="utf-8")

    print(f"{'code':8s} {'company':26s} {'status':10s} {'비교':>4s} {'재작성':>5s} "
          f"{'부분':>4s} {'미비교':>5s}  method")
    nre = ncl = nun = 0
    for code, r in sorted(res["companies"].items()):
        st = r["status"]
        nre += st == "RESTATED"
        ncl += st == "CLEAN"
        nun += st == "UNCOVERED"
        print(f"{code:8s} {(r['name'] or '')[:26]:26s} {st:10s} {r['compared']:4d} "
              f"{len(r['restated']):5d} {len(r.get('partial') or []):4d} "
              f"{len(r.get('uncompared') or []):5d}  {r['method']}")
        if st == "UNCOVERED":
            print(f"         ! {r['err_restating'] or ''} | {r['err_prior'] or ''}")
        if r.get("uncompared"):
            print(f"         UNCOMPARED items {r['uncompared']} — 마스터는 값을 갖고 있는데 "
                  f"양쪽 공시본에서 다 못 뽑았다(검사 사각)")
        for c in r["restated"]:
            print(f"         RESTATED item{c['item']:<3d} 원공시={c['as_filed']:>12,.2f} "
                  f"→ 재작성={c['restated']:>12,.2f}  Δ{c['delta']:+,.2f}  "
                  f"master={c['master']}  [{c['basis']}]")
    print()
    print(f"companies={len(res['companies'])}  CLEAN={ncl}  RESTATED={nre}  UNCOVERED={nun}")
    print(f"재작성 셀 합계 = {sum(len(r['restated']) for r in res['companies'].values())}")
    print(f"비교 셀 합계   = {sum(r['compared'] for r in res['companies'].values())} "
          f"(그중 부분(마스터 대역) {sum(len(r.get('partial') or []) for r in res['companies'].values())})")
    print(f"미비교(검사 사각) = "
          f"{sum(len(r.get('uncompared') or []) for r in res['companies'].values())}")

    if a.write:
        led = build_ledger(res, reason=ISSUER_REASONS)
        # 손으로 붙인 최상위 필드(`_severity_rationale` · `_history_probe` 등)를 **보존**한다.
        # 통째 덮어쓰면 다음 --write 한 번에 조용히 사라진다 — 이 저장소가 반복해서 데인
        # lost-update 형태다(project_master_json_lost_update).
        if LEDGER.exists():
            try:
                old = json.loads(LEDGER.read_text(encoding="utf-8"))
            except Exception:                       # noqa: BLE001
                old = {}
            kept = [k for k in old
                    if k.startswith("_") and k not in led and k != "_unreadable"]
            for k in kept:
                led[k] = old[k]
            if kept:
                print(f"  (보존한 수기 필드: {kept})")
        LEDGER.parent.mkdir(parents=True, exist_ok=True)
        LEDGER.write_text(json.dumps(led, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"\nwrote {LEDGER.relative_to(ROOT).as_posix()} "
              f"({len(led['entries'])} entries)")
    return 0


# 발행사가 공시본에 직접 적어 놓은 재작성 사유. 인용은 등재부에 그대로 실린다.
ISSUER_REASONS = {
    "KR0073": ("발행사 자기 기술(2026.2Q 공시본 '* 주요변동요인 (경과조치 적용 전)'): "
               "\"지급여력기준금액 : 종속회사 인수에 따른 기타요구자본 증가, 감독원 "
               "계리적가정 가이드라인 반영으로 인한 보험위험액 증가 등으로 직전 분기 대비 증가\". "
               "data/disclosure/FY2026_Q2/parsed/KR0073_교보생명보험.md L455."),
}


if __name__ == "__main__":
    sys.exit(main())
