# -*- coding: utf-8 -*-
"""Build data/_derived/_patch_2026q2_KR0005.json.

항목명 strings are extracted VERBATIM from the live kics_disclosure.json (this company's own
existing rows) -- never retyped by hand, to avoid the byte-mismatch trap (U+318D vs U+00B7 etc.)
that rejected an earlier patch this round."""
import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = Path(r"C:\Users\sangwook.cho\Desktop\insurequant")

with open(ROOT / "kics_disclosure.json", encoding="utf-8") as f:
    data = json.load(f)

rows = {
    r["항목번호"]: r
    for r in data
    if r.get("원보험사코드") == "KR0005" and r.get("공시분기") == "2026.2Q"
}

# item -> (new 값_적용후, 근거)
NEW_POST = {
    15: (23297.46,
         "R4(17후=16835.05,18후=824.74,19후_NEW=2710.62,20후=2369)+21후(4720) 재조합 = 23297.4596 "
         "-> 반올림 23297.46. 기존 23496.92는 item14(17718,헤드라인)+item22(5778.92,②표 단독)로 "
         "역산된 값이라 R4항등식과 79.07 어긋났음(② TIR축만 반영, ③EQ·④INT축 결합 누락). "
         "raw p18(② IR축)+p19(③ EQ축, ④ INT축)+p20(4-2-3, 헤드라인 SCR=17718) 결합 재계산."),
    16: (4161.95,
         "분산효과 = Σ(17,18,19_NEW,20,21)후 - item15후_NEW = 27459.4125-23297.4596=4161.9529 "
         "-> 4161.95. item15후 수정에 연쇄(R6 항등식 유지 목적, 그 자체가 별도 오류는 아니었음)."),
    19: (2710.62,
         "raw p19 ③주식위험경과조치·④금리위험경과조치 두 표를 MARKET_M으로 동시결합: "
         "sqrt(MARKET_M·[금리=0(④역산),주식=1912.77(③표 후),부동산=1484.51(불변),외환=384.04(불변),"
         "자산집중=0(불변)]) = 2710.6225 -> 2710.62. 기존 3358.88은 ③표 자체 소계(금리 경과조치 "
         "미반영, 전=1252 그대로 사용)를 그대로 복사한 값 -> 다중경과조치 혼합오류."),
    22: (5579.46,
         "법인세조정액후 = item15후_NEW - item14후(17718,헤드라인,불변) + item23후(0) = 5579.4596 "
         "-> 5579.46 (R5 항등식 잔차역산). 기존 5778.92는 raw p18 ②표(IR축 단독)의 법인세조정액후를 "
         "그대로 복사한 값 -> EQ/INT축 결합 누락(item19와 동일 패턴)."),
    23: (0.0,
         "raw p18 기본표 '[경과조치 적용 전 지급여력비율 세부]' Ⅲ.기타 요구자본(1+2+3) 전=- "
         "(=0) 및 raw p18/p19 선택경과조치 표 ②③④ 전부 '기타요구자본' 행이 전/후 공히 '-' "
         "(=0). 전 시나리오에서 후=전=0으로 일관 -> continuity TRAILING 결측(2026.1Q 후=0 present, "
         "2026.2Q 후=None)을 값 0으로 채움."),
    24: (0.0,
         "raw p18 '[경과조치 적용 전...]' 세부표 '1. 업권별 자본규제를 활용한 종속회사의 요구자본 "
         "환산치' 전='-'(=0), item23=24+25+26 항등식(적용후 0=0+0+0)을 위해 동반 충전 "
         "(item23 결측 티켓의 자식 셀, 별도 raw 후컬럼은 어느 표에도 없음 - 전 시나리오 0 정황증거로 채움)."),
    25: (0.0,
         "raw p18 '2. 비례성원칙을 적용한 종속회사의 요구자본 대응치' 전='-'(=0), item24와 동일 근거."),
    26: (0.0,
         "raw p18 '3. 업권별 자본규제를 활용한 관계회사의 요구자본 환산치' 전='-'(=0), item24와 동일 근거."),
    36: (0.0,
         "raw p19 ④금리위험경과조치 표: 금리위험 전=125,200백만/후='-'(공란, docling 유실 아님 - "
         "fitz 원문 직접확인). 같은 표의 시장위험액후=397,646백만=3976.46억과 부동산/외환/자산집중 "
         "불변(148,451/38,404/0)만으로 MARKET_M 역산: a=0에서 sqrt=3976.4611 (목표치와 diff "
         "+0.0011, 사실상 정확히 0). 금리위험 경과조치가 이 분기 금리위험액을 사실상 전액 이연."),
}

cells = []
for item, (post_val, reason) in sorted(NEW_POST.items()):
    row = rows.get(item)
    if row is None:
        raise SystemExit(f"ABORT: KR0005 2026.2Q item{item} row not found in live master")
    label = row["항목명"]
    cells.append({
        "항목번호": item,
        "항목명": label,
        "값": None,
        "값_적용후": post_val,
        "근거": reason,
    })
    print(f"item{item} 항목명={label!r} (byte-copied from master) -> 값_적용후={post_val}")

patch = {
    "company_code": "KR0005",
    "quarter": "2026.2Q",
    "cells": cells,
    "notes": (
        "값=null 인 셀은 '전(PRE) 컬럼은 변경하지 않음'을 뜻한다(삭제 아님) - 이번 패치는 "
        "값_적용후(post-transition) 축만 건드린다. 원인: 흥국화재는 이번 분기 IR+EQ+INT 3종 "
        "선택경과조치를 동시신청(TFI 공통 + TIR + TER + TIRR, TAC 미신청) -> raw는 각 축을 "
        "1개씩만 격리한 4개 표(공통/②IR/③EQ/④INT)만 제공, 결합후 항목별 breakdown은 어디에도 "
        "직접 인쇄돼 있지 않다(오직 헤드라인 지급여력비율/지급여력금액/지급여력기준금액=201.45%/"
        "35,693/17,718만 결합치로 인쇄됨, raw p17 도입부 + p20 4-2-3 최근3개년 표, 이중소스 일치). "
        "기존 파서는 item17·18·22를 raw p18 ②표(IR축)에서, item19·37을 raw p19 ③표(EQ축)에서 "
        "가져와 서로 다른 축의 단일표 값을 섞어썼다 -> item17·18은 IR축만 영향받아 우연히 맞았지만, "
        "item19·22는 실제로는 IR+EQ+INT 세 축이 모두 얽혀있어 한 축만 반영한 값이 틀렸다(item36도 "
        "전값 그대로 복사되어 있어 INT축이 통째로 누락돼 있었다). 이 패치는 "
        "scripts/fix_20260821_kr0005_2024q4_market_combined.py (동일회사 2024.4Q 동일유형 기수정) "
        "와 완전히 같은 방법론 - R4/MARKET_M을 kics_json_rules.py에서 import, leg 단위로 결합 "
        "후 항등식 재계산 - 을 따른다(계산 스크립트: "
        "scripts/_probes/compute_kr0005_20260831_2026q2.py). "
        "교차검증: item27후=item1/item14*100=201.4505(공시 201.45), item28후=item2/item14*100="
        "47.5958(공시 47.5957783) - item14(헤드라인,불변) 기준으로 재계산해도 공시 비율과 일치. "
        "단조성 검증: 결합item15(23297.46) <= IR단독(24131.28) <= EQ단독(29289.39) <= "
        "INT단독(29542.95) <= 전(29788) - 두 축을 동시결합하면 한 축만 적용했을 때보다 더 줄어야 "
        "한다는 물리적 요구를 만족."
    ),
    "unfixable": [],
}

out_path = ROOT / "data" / "_derived" / "_patch_2026q2_KR0005.json"
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(patch, f, indent=2, ensure_ascii=False)
    f.write("\n")

print(f"\nwrote {out_path}")
