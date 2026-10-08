#!/usr/bin/env python3
"""채널 합 vs 회사 지표(management_indicators.json 1-2 표) 대조에서 |차이| > 0.5%p 인 칸의 원인 분류표를 쓴다.

입력  data/persistency/selfcheck.csv 의 COMPANY_SUM 행 (extract_persistency_channel.py 가 쓴다)
출력  data/persistency/company_sum_triage.csv (utf-8-sig)
      열: 원보험사코드, 공시분기, 회차, 채널합, 회사지표, 차이, 분류, 근거
      채널합 = Σ유지계약액 / Σ대상신계약액 x 100 (값 3개가 다 있는 채널만), 회사지표 = MI 계약유지율_n회차, 차이 = 채널합 - 회사지표

분류 (2026-10-07 owner/orchestrator 지시)
  MI_COLUMN_SHIFT  management_indicators.json 이 원문 1-2 표를 엉뚱한 행·열에서 읽음 (채널합은 원문 인쇄값과 일치)
  DEFINITION       회사 지표(1-2)가 7-6 과 다른 기준임을 원문 주석이 말함 -- 근거에 주석을 인용
  PARSE_ERROR      우리 파서 오류 (고친다). 이번 87칸에는 없음
  SOURCE           원문 자체 불일치: 1-2 와 7-6 두 표 모두 인쇄 그대로 확인했는데 서로 다르고 산식 차이 설명이 없거나,
                   원문 인쇄 오기(자리수 결락·금액 행 뒤바뀜)가 합을 틀어 놓음
  UNKNOWN          위 어디에도 확정 못 함 (판독 근거 부족)

판정 절차(칸마다): ① MI 가 원문 1-2 인쇄값과 같은가(아니면 MI_COLUMN_SHIFT) ② 7-6 파서 값이 원문과 같은가(토큰 순서 독립 판독 +
칸별 항등식 + 렌더 대조) ③ 같은 쪽 주석에 기준 차이 설명이 있는가(있으면 DEFINITION, 없으면 SOURCE).
판정과 근거는 아래 DECISIONS 표에 사람이 PDF 쪽을 보고 적는다 -- 표에 없는 새 칸은 UNKNOWN 으로 나오니 PDF 를 보고 표에 추가한다.
selfcheck.csv 가 바뀌면(추출기 재실행) 이 스크립트를 다시 돌려 숫자(채널합·회사지표·차이)만 갱신한다.

실행: C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/triage_persistency_company_sum.py
"""
from __future__ import annotations

import csv
import io
import os
import sys
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SELFCHECK = REPO / "data" / "persistency" / "selfcheck.csv"
OUT = REPO / "data" / "persistency" / "company_sum_triage.csv"
THRESH = 0.5
EXACT = 0.06

if sys.stdout.encoding is None or "utf" not in sys.stdout.encoding.lower():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

CLASSES = ("MI_COLUMN_SHIFT", "DEFINITION", "PARSE_ERROR", "SOURCE", "UNKNOWN")

# 파서 값 확인 문구
V_FULL = "7-6 쪽 토큰 순서 독립 판독이 파서 값과 12/12행 일치"
V_RMISS = "7-6 쪽 독립 판독: 금액 8/8행 일치(유지율 행은 텍스트 순서상 미판독이나 칸별 항등식 전부 통과)"
V_DUMP = "7-6 쪽 텍스트 덤프를 눈으로 대조해 파서 값 일치 확인(칸별 항등식 전부 통과)"
V_RENDER = "7-6 쪽 렌더 육안 대조로 파서 값 일치 확인(칸별 항등식 전부 통과)"

# 2Q 한정 불일치의 추정 원인 -- 원문에 명시가 없는 칸에만 덧붙인다
HYP_2Q = ("[추정] 같은 회사가 2Q 공시에서만 어긋나 1-2 가 상반기 누계(업무보고서 산출표), 7-6 이 직전 12개월 창일 가능성 "
          "-- 이 파일 원문에는 명시 없음(삼성화재·DB생명·생보 업계 주석이 그렇게 말함)")

SRC_PLAIN = "원문 1-2 표(회사 지표, MI=인쇄값)와 7-6 채널표가 서로 다름: 두 표 모두 PDF 인쇄 그대로 확인, 1-2 쪽에 유지율 산식 차이 설명 없음 -> 원문 자체 불일치"
# (코드, 분기) -> (분류, 판정 문구, 파서 확인 문구, 추정 문구 덧붙임 여부)
DECISIONS: dict[tuple[str, str], tuple[str, str, str, bool]] = {
    # ---- MI_COLUMN_SHIFT -------------------------------------------------------------
    ("KR0051", "2024.4Q"): ("MI_COLUMN_SHIFT",
        "원문 1-2(p6, 렌더 확인) 2024년도 열 인쇄: 13회차 68.14 · 25/37회차 '-' · 49회차 81.45 · 61회차 74.91 · 73회차 77.74 · 85회차 77.79. "
        "MI(13회차 77.79 · 25회차 43.76 · 37회차 35.36 · 61회차 39.47)는 이 표의 다른 칸을 읽은 값으로 행·열이 밀림(텍스트 순서가 뒤섞인 PDF). "
        "채널합은 인쇄값과 일치. 티켓 20261007T1300Z 에 이 칸(KR0051 2024.4Q)이 빠져 있음 -> 추가 필요",
        "7-6(p61) 텍스트 순서 독립 판독: 유지율 4/4행 일치(13·61회차 설계사 1칸만 값 있음), 금액 4/8행 일치(나머지는 전부 '-' 라 판독 행이 비어 있음)", False),
    ("KR0051", "2025.2Q"): ("MI_COLUMN_SHIFT",
        "원문 1-2(p4, 렌더 확인) 해당분기 열 인쇄: 13회차 66.88 · 25회차 57.04 · 37/49회차 '-' · 61회차 29.82 · 73회차 25.00 · 85회차 18.89. "
        "MI 13회차 54.2 는 같은 표의 보험금지급률 칸, 37·49·61회차 -79.8/-45.0/-55.6 은 증감 열 값(행·열 밀림, 티켓 20261007T1300Z 등재분). "
        "채널합은 인쇄값과 |차|<=0.18(소액 반올림) 일치",
        "7-6(p41) 렌더 육안 대조: 13회차 설계사 222/336·다이렉트 9/10, 25회차 설계사 96/168, 61회차 설계사 24/80 이 파서 값과 일치(나머지 칸 '-')", False),
    ("KR0076", "2024.4Q"): ("MI_COLUMN_SHIFT",
        "원문 1-2(p4) 인쇄 13/25/37/61회차 = 91.64/67.42/61.33/51.51 이 채널합과 소수 둘째 자리까지 일치. "
        "MI(△1.27 · 3.42 · △10.03 · △1.47)는 증감 열을 읽은 값(티켓 20261007T1300Z 등재분)",
        V_FULL, False),
    # ---- DEFINITION ------------------------------------------------------------------
    ("KR0008", "2023.2Q"): ("DEFINITION",
        "1-2 주3) '유지율 : 상반기 유지계약액 / 대상 신계약액' 인 반면 7-6 주3) '유지계약액 대상기간 : 2022.07.01.~2023.06.30.'(직전 12개월) -> 산출기간이 달라 2Q 에서만 어긋남. "
        "2025.2Q 부터 1-2 주석이 12개월 창으로 바뀌어 차이가 <=0.005 로 닫힘",
        V_FULL, False),
    ("KR0008", "2024.2Q"): ("DEFINITION",
        "1-2 주5) '유지율 : 상반기 유지계약액 / 대상 신계약액 x 100' 인 반면 7-6 '유지계약액 대상기간: 2023년 7월 ~ 2024년 6월'(직전 12개월) -> 산출기간 차이. "
        "2025.2Q 부터 1-2 주석이 12개월 창으로 바뀌어 차이가 <=0.005 로 닫힘",
        V_DUMP, False),
    ("KR0071", "2023.2Q"): ("DEFINITION",
        "흥국생명 2024.2Q 1-2 주석: '계약유지율 : 업무보고서 산출 기준 정비(23년 결산부터 적용)에 따라 해당분기와 전년동기 산정 방식 상이' -> "
        "2023.2Q 1-2 값은 정비 이전 기준으로 산정된 것으로 보임(이 파일 1-2 에는 주석 없음; 1-2 인쇄는 25회차 41.76 < 37회차 56.36 으로 비단조인 반면 7-6 채널합은 52.01 > 47.27 로 단조)",
        V_FULL, False),
    # 2026-10-07 P4(YELLOW-4): 이 칸은 분류기 자신의 DEFINITION 규칙(원문 주석이 기준 차이를 말함 + 주석 인용)을 못 채워 SOURCE 로 내렸다.
    # 이 파일 p4 1-2 표에는 유지율 기준 주석이 없고(텍스트층 확인), 2024.2Q 파일 주석은 '23년 결산부터 적용'이라 2023.4Q 는 오히려 새 기준이다.
    ("KR0071", "2023.4Q"): ("SOURCE",
        "원문 1-2(p4, MI=인쇄값 37회차 48.37 · 61회차 32.38)와 7-8 채널표(p81, 렌더 확인)가 서로 다름: 두 표 모두 PDF 인쇄 그대로. 이 파일 1-2 표에는 유지율 산식·기준 주석이 없다"
        "(텍스트층 확인; 있는 것은 신계약률·보험금지급률·신용평가등급 주요변동요인뿐). 같은 회사 2024.2Q 파일 1-2 의 주석('업무보고서 산출 기준 정비(23년 결산부터 적용)에 따라 "
        "해당분기와 전년동기 산정 방식 상이')은 2023 결산부터 새 기준이라는 말이라 2023.4Q 의 차이를 설명하지 못한다 -> 이 파일에 기준 차이를 말하는 문장이 없어 SOURCE 로 둠(원인 추정 안 함)",
        V_FULL, False),
    ("KR0071", "2024.2Q"): ("DEFINITION",
        "1-2 주석: '계약유지율 : 업무보고서 산출 기준 정비(23년 결산부터 적용)에 따라 해당분기와 전년동기 산정 방식 상이, "
        "해당분기 대상기간 23.7월~24.6월, 전년동기 대상기간 23.4월~23.6월' -> 1-2 는 업무보고서 산출 기준, 7-6 은 경영공시 채널표 산출",
        V_FULL, False),
    ("KR0072", "2023.2Q"): ("DEFINITION",
        "같은 회사 2024.2Q 1-2 주석: '계약유지율 업무보고서 산출기준 정비(23년 결산부터 적용)에 따라 해당 분기와 전년 동기 산정방식 상이"
        "(전년동기 수치 : 23.2Q 경영공시 당시 제출값 사용)' -> 2023.2Q 1-2 값은 정비 이전 기준. 이 파일 1-2 에는 주석 없음",
        V_FULL, False),
    ("KR0082", "2023.2Q"): ("DEFINITION",
        "1-2 주5) '계약유지율 : 업무보고서 AH124(계약유지율) 참조' + <계약유지율 산출표>(산출월 1~12월 전년동월 대상신계약액 A, 그중 산출월 현재 유지계약액 B 의 합계) "
        "vs 7-6 '유지계약액 대상 기간 : 22.7.1~23.6.30' -> 산출 기준이 다름. 같은 회사 2024.2Q 주석: '업무보고서 산출기준 정비(23년 결산부터 적용)', 2024.2Q 부터 일치",
        V_FULL, False),
    ("KR0099", "2024.2Q"): ("DEFINITION",
        "1-2 주석: '계약유지율 업무보고서 산출기준 정비(23년 결산부터 적용)에 따라 해당 분기와 전년 동기 산정방식 상이(전년동기 수치 : 23.2Q 경영공시 당시 제출값 사용)' "
        "-> 1-2 는 업무보고서 산출기준, 7-6 은 경영공시 채널표 산출",
        "7-6 쪽 독립 판독: 유지율 4/4행 일치(금액 행은 독립 판독이 일부 칸에서 끊겨 칸별 항등식 전부 통과로 갈음)", False),
    ("KR1010", "2023.2Q"): ("DEFINITION",
        "같은 회사 2024.2Q 1-2 주석: '계약유지율 업무보고서 산출기준 정비(’23년 결산부터 적용)에 따라 해당 분기와 전년 동기 산정방식 상이"
        "(전년동기 수치 : ’23.2Q 경영공시 당시 제출값 사용)' -> 2023.2Q 1-2 값은 정비 이전 기준. 이 파일 1-2 주석: '계약유지율 25회차, 73회차는 유지율이 낮은 저축성 상품이 높은 비중'. "
        "7-6 은 방카·다이렉트 두 열만 값이 있어 13회차 차이(-15.23%p)가 큼 -- 정비 전 기준 외의 모집단 차이가 섞였을 수 있음",
        V_FULL, False),
    # ---- SOURCE ----------------------------------------------------------------------
    ("KR0002", "2023.2Q"): ("SOURCE", SRC_PLAIN,
        "7-6(p46) 독립 판독: 금액 8/8행 일치, 유지율 3/4행(37회차 법인대리점_기타 `63,43` 은 원문 오타를 항등식으로 보정)", True),
    ("KR0002", "2023.4Q"): ("SOURCE",
        "원문 p79 61회차 설계사 대상신계약액이 `319,76` 으로 인쇄(자리수 결락, 렌더 확인) -> 그 칸 값이 null 이라 설계사 유지계약액 123,092 도 합에서 빠져 합이 부풀음. "
        "유지율 38.50 에서 역산한 대상신계약액 약 319,720 을 넣으면 합 44.19 = 회사지표 44.20. 13/25/37회차는 일치",
        "7-6(p79) 독립 판독: 금액 7/8행 일치(결락 칸만 다름), 유지율 3/4행(61회차 설계사 외 열의 `39,77` 오타는 항등식 보정)", False),
    ("KR0002", "2025.2Q"): ("SOURCE", SRC_PLAIN, V_RMISS, True),
    ("KR0004", "2023.2Q"): ("SOURCE", SRC_PLAIN, V_FULL, True),
    ("KR0005", "2025.2Q"): ("SOURCE",
        "원문 1-2(p4, MI=인쇄값 85.52/72.31/65.22/63.66/56.71)와 7-6(p57)가 서로 다름: 두 표 모두 인쇄 그대로 확인. 1-2 주석은 '유지율 : 업무보고서(AI124) 작성기준' 만 말할 뿐 "
        "7-6 과 다른 산식을 특정하지 않음 -> 원문 자체 불일치",
        V_RMISS, False),
    ("KR0010", "2023.2Q"): ("SOURCE", SRC_PLAIN, "7-6(p39-40) 독립 판독 12/12행 일치(9번째 수는 쪽번호)", True),
    ("KR0010", "2024.2Q"): ("SOURCE",
        "원문 1-2(p4)와 7-6(p51-52)가 서로 다름. 1-2 주석은 '유지율의 전년동기는 23년 2분기 경영공시 현황과 일치하게 작성'(전년동기 열 설명)뿐이라 당기 기준 차이의 근거 없음 -> 원문 자체 불일치",
        V_DUMP, False),
    ("KR0011", "2023.2Q"): ("SOURCE", SRC_PLAIN, V_FULL, True),
    ("KR0011", "2024.2Q"): ("SOURCE",
        "원문 1-2(p4)와 7-6(p51)가 서로 다름. 1-2 주석 '동 자료는 금융감독원 업무보고서 기준으로 작성되었으며 전년 동기 금액은 외부감사인 검토보고서(재작성) 금액' 은 "
        "재무 수치 설명이라 유지율 산식 차이의 근거가 못 됨 -> 원문 자체 불일치. " + HYP_2Q,
        V_RMISS, False),
    ("KR0011", "2025.2Q"): ("SOURCE", SRC_PLAIN, V_RMISS, True),
    ("KR0029", "2023.2Q"): ("SOURCE", SRC_PLAIN, V_FULL, True),
    ("KR0050", "2023.2Q"): ("SOURCE",
        SRC_PLAIN + ". 7-6(p39) 머리 단위가 `(단위 : 건, %)` 로 인쇄(같은 서식의 불완전판매 표 단위가 복사된 것으로 보이나 금액 행은 2023.4Q 백만원 규모와 같음, 확정 불가)",
        V_FULL, True),
    ("KR0069", "2023.2Q"): ("SOURCE", SRC_PLAIN, V_FULL, True),
    ("KR0070", "2025.4Q"): ("SOURCE",
        "원문 p95 법인대리점_기타·직영_임직원 13회차에서 유지계약액>대상신계약액 으로 두 금액 행이 뒤바뀌어 인쇄(원문 오기, source_errata.csv 등재). "
        "두 칸을 바꿔 읽으면 합 90.55 = 회사지표 90.55",
        V_FULL, False),
    ("KR0075", "2025.2Q"): ("SOURCE",
        "원문 1-2(p4, MI=인쇄값 64.66/64.53/28.33/9.33)와 7-6(p55)가 서로 다름: 두 표 모두 인쇄 그대로(7-6 은 렌더 확인, 61회차 방카 `10..00` 은 오타를 항등식으로 보정). "
        "1-2 주석은 '자산연계형 저축보험과 변액보험의 해약증감에 의한 유지율 변동'뿐이고 산식 차이 설명 없음 -> 원문 자체 불일치(1-2 모집단이 7-6 과 다를 가능성)",
        V_RENDER, False),
    ("KR0075", "2026.2Q"): ("SOURCE",
        "원문 1-2(p4, MI=인쇄값 69.11/39.52/53.52)와 7-6(p55)가 서로 다름: 두 표 모두 인쇄 그대로. 1-2 주석은 '자산연계형 저축보험과 변액보험의 해약증감에 의한 유지율 변동'뿐 -> "
        "원문 자체 불일치. 7-6 25회차(2026.2Q) 대상 169,691 은 2025.2Q 13회차 대상 169,792 와 같은 코호트라 7-6 쪽이 내적으로 일관",
        V_FULL, False),
    ("KR0076", "2026.2Q"): ("SOURCE",
        "원문 p51 25회차 법인대리점_금융기관에서 유지계약액 6,556 > 대상신계약액 4,014 로 두 금액 행이 뒤바뀌어 인쇄(원문 오기, source_errata.csv 등재). "
        "바꿔 읽으면 합 81.55 = 회사지표 81.55",
        V_FULL, False),
    ("KR0099", "2025.2Q"): ("SOURCE",
        "원문 1-2(p4, MI=인쇄값)와 7-6(p54)가 서로 다름: 두 표 모두 인쇄 그대로, 이 파일 1-2 에 산식 주석 없음. 같은 회사 2024.2Q 1-2 에는 '업무보고서 산출기준 정비' 주석이 있고 "
        "2025.2Q 전년동기 열(91.00 등)이 2024.2Q 당기(82.4 등)와 달라 1-2 가 다시 산정되는 값이나, 이 파일에는 기준을 말하는 문장이 없어 SOURCE 로 둠",
        V_FULL, False),
    ("KR0099", "2026.2Q"): ("SOURCE",
        "원문 1-2(p4, MI=인쇄값)와 7-6(p54)가 서로 다름: 두 표 모두 인쇄 그대로, 이 파일 1-2 에 산식 주석 없음. 같은 회사 2024.2Q 1-2 주석('업무보고서 산출기준 정비')과 같은 계열 차이로 보이나 "
        "이 파일에 명시가 없어 SOURCE 로 둠",
        "7-6 쪽 독립 판독: 유지율 4/4행 일치(금액 행은 독립 판독이 일부 칸에서 끊겨 칸별 항등식 전부 통과로 갈음)", False),
    ("KR1098", "2025.2Q"): ("SOURCE",
        "다이렉트 1열만 값이 있고 금액이 백만원 단위 소액(유지 94 / 대상 123): 인쇄 유지율 75.92(=MI)는 금액비 76.42 와 금액 반올림 허용구간(75.71~77.14) 안 -> 금액 반올림 한계(실질 불일치 아님)",
        "7-6(p43) 독립 판독: 금액 8/8행 일치, 칸별 항등식 통과", False),
}

# MI_COLUMN_SHIFT 칸의 원문 1-2 인쇄값 (렌더로 확인한 값)
PRINTED = {
    ("KR0051", "2024.4Q"): {13: 68.14, 61: 74.91},
    ("KR0051", "2025.2Q"): {13: 66.88, 61: 29.82},
    ("KR0076", "2024.4Q"): {13: 91.64, 25: 67.42, 37: 61.33, 61: 51.51},
}


def read_company_sum():
    rows = []
    with open(SELFCHECK, encoding="utf-8-sig", newline="") as fh:
        for r in csv.DictReader(fh):
            if r["kind"] == "COMPANY_SUM":
                rows.append(r)
    return rows


def main():
    cs = read_company_sum()
    maxd = defaultdict(float)
    for r in cs:
        k = (r["code"], r["quarter"])
        maxd[k] = max(maxd[k], abs(float(r["a"]) - float(r["b"])))
    flagged = [r for r in cs if abs(float(r["a"]) - float(r["b"])) > THRESH]
    out = []
    unknown = []
    used = set()
    for r in sorted(flagged, key=lambda r: (r["code"], r["quarter"], int(r["round"]))):
        code, q, rnd = r["code"], r["quarter"], int(r["round"])
        a, b = float(r["a"]), float(r["b"])
        dec = DECISIONS.get((code, q))
        if dec is None:
            cls, text = "UNKNOWN", "미분류 -- PDF 를 보고 DECISIONS 표에 추가"
            unknown.append((code, q, rnd))
        else:
            used.add((code, q))
            cls, claim, verify, hyp = dec
            parts = [claim, verify]
            pr = PRINTED.get((code, q), {}).get(rnd)
            if pr is not None:
                parts.insert(1, f"이 회차 원문 인쇄 {pr:g}")
            ex = sorted(qq for (cc, qq), d in maxd.items() if cc == code and d <= EXACT)
            if ex and cls in ("SOURCE", "DEFINITION"):
                parts.append("같은 회사 일치(|차|<=0.06) 분기: " + ",".join(ex))
            if hyp:
                parts.append(HYP_2Q)
            text = " | ".join(parts)
            if cls not in CLASSES:
                raise SystemExit(f"잘못된 분류 {cls}")
        out.append({"원보험사코드": code, "공시분기": q, "회차": f"{rnd}회차", "채널합": f"{a:.2f}", "회사지표": f"{b:g}",
                    "차이": f"{a - b:+.2f}", "분류": cls, "근거": text})
    for k in sorted(set(DECISIONS) - used):
        print(f"[경고] DECISIONS 의 {k} 는 이번 selfcheck 에서 |차이|>{THRESH} 칸이 아님 -- 표 점검")
    buf = io.StringIO(newline="")
    w = csv.DictWriter(buf, fieldnames=["원보험사코드", "공시분기", "회차", "채널합", "회사지표", "차이", "분류", "근거"])
    w.writeheader()
    w.writerows(out)
    tmp = OUT.with_name(OUT.name + f".tmp{os.getpid()}")
    with open(tmp, "w", encoding="utf-8-sig", newline="") as f:
        f.write(buf.getvalue())
    os.replace(tmp, OUT)
    cnt = Counter(r["분류"] for r in out)
    print(f"COMPANY_SUM {len(cs)}칸 중 |차이|>{THRESH}: {len(out)}칸 ({len({(r['원보험사코드'], r['공시분기']) for r in out})}개 회사·분기)")
    print("분류별 칸 수:", {c: cnt.get(c, 0) for c in CLASSES})
    cq = Counter(DECISIONS[k][0] for k in {(r["원보험사코드"], r["공시분기"]) for r in out} if k in DECISIONS)
    print("분류별 회사·분기 수:", dict(cq))
    if unknown:
        print("UNKNOWN(미분류):", unknown)
    print(f"WROTE {OUT.relative_to(REPO).as_posix()}")


if __name__ == "__main__":
    main()
