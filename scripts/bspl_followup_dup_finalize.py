#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""2026-10-11 BS/PL follow-up (parser/ifrs17), step 3d: assemble the deliverable consecutive_duplicates_20261011.json (ticket name) from
the scan + triage passes + the by-hand source checks, with a verdict and a reason per record.

Verdicts
  CORRECTED                  a copy error found by this scan and fixed in the master (KR1000 2023.1Q = 2023.2Q block)
  CONFIRMED_SOURCE_EQUAL     the source (disclosure / DART) itself prints the equal value in every quarter of the run
  CONFIRMED_ARITHMETIC       a 값_당분기 run whose YTD cells are distinct and source-confirmed: the quarterly figure is a YTD difference, so
                             equal consecutive figures cannot be a copy
  CONFIRMED_BY_FS_CACHE      the cached DART FS-API response of each quarter, re-parsed with the production parser, gives the master value
  ROUNDING_ARTIFACT          the disclosure prints the line in 억원: equal figures are an equal rounded print
  DEFECT_FOUND               source disagrees with the master (handler took the wrong column); master NOT changed (outside this ticket's
                             write scope: needs a handler fix + PL golden regeneration) -> reported
Output: data/_derived/bspl_granularity_20261011/consecutive_duplicates_20261011.json (+ copy in bspl_followup_20261011/).
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.stdout.reconfigure(encoding="utf-8")
W = ROOT / "data" / "_derived" / "bspl_followup_20261011"
OUT_TICKET = ROOT / "data" / "_derived" / "bspl_granularity_20261011" / "consecutive_duplicates_20261011.json"

BY_HAND = {
    ("BS", "KR0005", 21, "값", "2023.1Q"): ("CONFIRMED_SOURCE_EQUAL",
        "재보험계약부채 14백만원: 2023.1Q 경영공시 8-1 p23(백만원) 14, 2023.2Q 경영공시 p52 재무상태표 14 · p116 기말 재보험계약부채 14(기초 14). 원천이 같은 값을 인쇄."),
    ("BS", "KR0029", 11, "값", "2024.1Q"): ("ROUNDING_ARTIFACT", "AIG 당기손익-공정가치측정금융자산: 요약 재무상태표가 억원 단위로 14억을 3개 분기 인쇄(Stage B EXISTS_SAME). 반올림 값."),
    ("BS", "KR0029", 11, "값", "2025.1Q"): ("ROUNDING_ARTIFACT", "AIG 당기손익-공정가치측정금융자산: 요약 재무상태표가 억원 단위로 14억을 3개 분기 인쇄(Stage B EXISTS_SAME). 반올림 값."),
    ("BS", "KR0050", 21, "값", "2023.2Q"): ("ROUNDING_ARTIFACT", "하나손보 재보험계약부채 2억: 억원 단위 인쇄 값(Stage B EXISTS_SAME)."),
    ("BS", "KR1010", 13, "값", "2023.2Q"): ("CONFIRMED_SOURCE_EQUAL", "교보라이프플래닛 상각후원가측정금융자산 3,385억: 두 분기 요약 BS 가 같은 값을 인쇄(Stage B EXISTS_SAME, 억원 정밀도)."),
    ("BS", "KR1010", 13, "값", "2024.2Q"): ("CONFIRMED_SOURCE_EQUAL", "교보라이프플래닛 상각후원가측정금융자산 260억: 두 분기 요약 BS 가 같은 값을 인쇄(Stage B EXISTS_SAME, 억원 정밀도)."),
    ("PL", "KR0005", 10, "값_당분기", "2025.3Q"): ("CONFIRMED_ARITHMETIC",
        "흥국화재 재보험 위험조정 변동: YTD −1,001(2Q) · −1,667(3Q) · −2,333(4Q) 로 서로 다르고 당분기는 YTD 차이라 같은 −666 은 복사가 될 수 없다(핸들러 출력 2025.3Q −1,667, 2025.2Q −1,001 확인)."),
    ("PL", "KR0099", 10, "값_당분기", "2024.3Q"): ("CONFIRMED_ARITHMETIC",
        "KB라이프 재보험 위험조정 변동: 당분기 −74 −72 −69 −69 로 완만하게 변하는 계열이고 YTD(−146 · −215 · −284)는 서로 다르다. YTD 차이가 같은 값이 된 것."),
    ("PL", "KR0104", 5, "값_당분기", "2025.1Q"): ("CONFIRMED_SOURCE_EQUAL",
        "농협생명 원수 위험조정 변동: 2025.1Q 보고서(rcept 20250515001350)에 10,937, 2025.2Q 반기보고서(rcept 20250814002779)에 3개월 10,937 · 누적 21,874 가 모두 인쇄(raw XML 대조). 위험조정 해제가 분기별 같은 액수."),
    ("PL", "KR0072", 10, "값", "2024.1Q"): ("DEFECT_FOUND",
        "케이디비생명 재보험 위험조정 변동 2024.2Q: 마스터 YTD −162 는 2024.1Q 값과 같으나, 2024.2Q 반기보고서(rcept 20240814000801) 재보험 위험조정 변동분 표(line 19773)는 누적 (324), 보험손익 상세 표(line 23773)는 3개월 162 · 누적 324(전년 반기 1,410 · 1,499)로 인쇄된다. "
        "핸들러 extract_tier2_life_comprehensive 가 머리글이 없는 두 번째(재보험) 표에서 첫 숫자(3개월)를 집었다. 올바른 값은 YTD −324, 당분기 −162. 같은 열 선택 결함이 이 회사 항목 10 의 2Q·3Q 다른 해(2023.2Q −1,410 = 3개월, 누적 −1,499)에도 있을 수 있다. "
        "마스터 미변경(핸들러 수정 + PL 골든 재생성이 필요한 PL 레인 작업, 이 티켓 쓰기 범위 밖) — 보고."),
}


def main():
    scan = json.loads((W / "consecutive_duplicates_20261011.json").read_text(encoding="utf-8"))
    before = json.loads((W / "consecutive_duplicates_before_20261011.json").read_text(encoding="utf-8"))
    tri = {(r["master"], r["code"], str(r["item"]), r["field"], r["quarters"][0]): r for r in json.loads((W / "consecutive_duplicates_triage_20261011.json").read_text(encoding="utf-8"))}
    tri2 = {(r["code"], str(r["item"]), r["field"], r["quarters"][0]): r for r in json.loads((W / "consecutive_duplicates_triage2_20261011.json").read_text(encoding="utf-8"))}
    recs = []
    for r in scan["records"]:
        k = (r["master"], r["code"], r["item"], r["field"], r["quarters"][0])
        t = tri[(r["master"], r["code"], str(r["item"]), r["field"], r["quarters"][0])]
        verdict, reason = None, None
        if k in BY_HAND:
            verdict, reason = BY_HAND[k]
        elif r["master"] == "BS" and r["item"] == 30:
            if t["verdict"] == "CONFIRMED":
                verdict, reason = "CONFIRMED_SOURCE_EQUAL", "자본금 불변: 경영공시 자기자본 표(4-1)·재무상태표(8-1)의 열이 이 회사 자본금을 모든 관측 분기에서 같은 값으로 인쇄(equity_scan)."
            else:
                verdict, reason = "CONFIRMED_SOURCE_EQUAL", ("자본금 불변: 경영공시가 자체 공시본을 가진 분기에서 같은 값을 인쇄(equity_scan 재현), 나머지 분기는 DART 자본금 태그(IssuedCapital)가 같은 값. 증자 흔적 없음.")
        elif r["master"] == "PL":
            t2 = tri2.get((r["code"], str(r["item"]), r["field"], r["quarters"][0]))
            if t["verdict"] == "CONFIRMED":
                verdict, reason = "CONFIRMED_SOURCE_EQUAL", "경영공시 요약 PL 의 해당 분기 누계가 같은 값을 인쇄(pl_candidates EXISTS_SAME, 분기별 각자 공시본)."
            elif t2 and t2["verdict"] == "CONFIRMED_ARITHMETIC":
                verdict, reason = "CONFIRMED_ARITHMETIC", "당분기 = YTD 차이. 관련 YTD 칸이 모두 원천 확인(EXISTS_SAME)이고 YTD 는 서로 다르다: 같은 당분기 값은 산술 결과."
            elif t2 and t2["verdict"] == "CONFIRMED_BY_FS_CACHE":
                verdict, reason = "CONFIRMED_BY_FS_CACHE", "DART FS-API 캐시를 생산 파서로 다시 읽은 값이 마스터와 일치 — 같은 값은 DART 자료 그대로(후행 복사 아님)."
        if verdict is None:
            verdict, reason = "UNRESOLVED", "분류 안 됨"
        recs.append({**r, "verdict": verdict, "reason": reason})
    corrected = [{**r, "verdict": "CORRECTED",
                  "reason": "KR1000 2023.1Q = 2023.2Q 복사 묶음(전환일 비교표를 별도 재무상태표로 오선택). 이 후속 작업 단계 2 에서 정정(오버레이·사이드카·파트 파일 동기), 정정 후 이 스캔에서 사라짐."}
                 for r in before["records"] if r["master"] == "BS" and r["code"] == "KR1000" and r["item"] != 30]
    cnt = Counter((r["master"], r["verdict"]) for r in recs)
    payload = {"_what": scan["_what"], "scan_date": "2026-10-11",
               "method": "scripts/bspl_followup_consecutive_dups.py (scan) -> bspl_followup_dup_triage.py / _triage2.py (source evidence) -> bspl_followup_dup_finalize.py (this file)",
               "counts_after_correction": {f"{m}:{v}": n for (m, v), n in sorted(cnt.items())},
               "corrected_before_scan_records": len(corrected), "corrected": corrected, "records": recs}
    for p in (OUT_TICKET, W / "consecutive_duplicates_20261011.json"):
        p.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    print(payload["counts_after_correction"], "corrected block records:", len(corrected))
    for r in recs:
        if r["verdict"] in ("DEFECT_FOUND", "UNRESOLVED"):
            print(r["verdict"], r["code"], r["item"], r["field"], r["quarters"])


if __name__ == "__main__":
    main()
