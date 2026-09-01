# -*- coding: utf-8 -*-
"""Build verdict_group1.json for 현대해상(KR0009)/KB손해보험(KR0010)/신한이지손해보험(KR0051)."""
from __future__ import annotations
import json, io, sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "data" / "_derived" / "item23_children_audit" / "verdict_group1.json"

records = []

def add(code, name, q, item, verdict, value, evidence_file, evidence_lines, evidence_text,
        sandwiched, note):
    records.append({
        "code": code, "name": name, "quarter": q, "item": item,
        "verdict": verdict,
        "value_pre": value, "value_post": value,  # 기타요구자본은 경과조치 비대상, 후=전
        "evidence_file": evidence_file,
        "evidence_lines": evidence_lines,
        "evidence_text": evidence_text,
        "sandwiched": sandwiched,
        "note": note,
    })

# ============================================================
# 현대해상 (KR0009) -- 12분기, item25/26 EXTRACTION_GAP value=0
# 원인: kics_disclosure_parser.py extract_kics_detail_rows()가 '값 셀이 진짜
# 공백(대시조차 아님)'인 행을 통째로 pairs에서 제외 -- item24는 179 등 실값이라
# 살아남지만 25/26은 매 분기 공백이라 계속 탈락. 라벨 자체는 원문에 정상 인쇄.
# 수정: extract_kics_detail_rows()에서 공백 셀을 "-"로 치환(기존 대시 처리 경로
# 재사용) -- 전체 데이터셋 시뮬레이션 0 regression, 64 신규 fill 확인.
# ============================================================
HD_MD = "md_inbox/{period}/KR0009_현대해상.md (동일 내용이 data/disclosure/{period}/parsed/KR0009_현대해상{amend}.md 에도 있음)"
HD_ROWS = [
    ("2023.1Q", "FY2023_Q1", "", 179.0),
    ("2023.2Q", "FY2023_Q2", "", 176.0),
    ("2023.3Q", "FY2023_Q3", "_amended", 176.0),
    ("2023.4Q", "FY2023_Q4", "_amended", 168.0),
    ("2024.1Q", "FY2024_Q1", "_amended", 168.0),
    ("2024.2Q", "FY2024_Q2", "_amended", 174.0),
    ("2024.3Q", "FY2024_Q3", "_amended", 189.0),
    ("2024.4Q", "FY2024_Q4", "", 192.0),
    ("2025.1Q", "FY2025_Q1", "", 201.0),
    ("2025.2Q", "FY2025_Q2", "_amended", 203.0),
    ("2025.3Q", "FY2025_Q3", "", 222.0),
    ("2025.4Q", "FY2025_Q4", "", 208.0),
]
for q, period, amend, item23 in HD_ROWS:
    ev_file = HD_MD.format(period=period, amend=amend)
    ev_text = (
        f"| Ⅲ. 기타 요구자본(1+2+3) | {item23:.0f} | ... |\n"
        f"| 1. 업권별 자본규제를 활용한 종속회사의 요구자본 환산치 | {item23:.0f} | ... |\n"
        "| 2. 비례성원칙을 적용한 종속회사의 요구자본 대응치 |  (공백) | -  | - |\n"
        "| 3. 업권별 자본규제를 활용한 관계회사의 요구자본 환산치 |  (공백) | -  | - |"
    )
    note = (
        "item24=item23 항상 정확히 일치(12분기 연속) - 값이 전부 item24 한 곳에만 실렸고 "
        "25/26 셀은 당분기 컬럼이 대시(-)조차 아닌 완전 공백(원문 PDF 텍스트 레이어 직접 확인, "
        "fitz get_text 재현: 라벨 다음 값 위치가 공백 문자 하나뿐). 같은 회사 부속 서술 섹션 "
        "'○ 비례성원칙 적용현황에 관한 사항' 이 '해당사항 없음' 이라고 명시(2023.1Q 확인, 매 "
        "분기 동일 문구 반복) -- item25=0 이 원문상 사실. 12분기 전부 동일 패턴(SANDWICHED: "
        "전후 분기 전부 같은 공백 구조, 회사 자체가 이 두 항목을 쓴 적이 없음을 뜻하되, 그 자체가 "
        "표의 '행'은 인쇄돼 있으므로 회사가 이 서식을 안 쓰는 게 아니라 값이 0인 것 -- SOURCE_ABSENT "
        "아닌 EXTRACTION_GAP). 파서 수정: src/solvency/parser/kics_disclosure_parser.py "
        "extract_kics_detail_rows() 의 'if not label or not value or label in seen: continue' 를 "
        "'값이 공백이면 -로 치환 후 계속 진행'으로 변경 -- 전체 데이터셋 재시뮬레이션(회사무관 "
        "546개 md_inbox 파일 전수, match_baseline_value_or_zero 재실행) 결과 lost_keys=0, "
        "changed_keys=0(기존에 이미 맞던 셀은 전부 그대로), new_keys=64(전부 신규 0채움, 그 중 24개가 "
        "이 회사 item25/26 12분기×2)."
    )
    add("KR0009", "현대해상", q, 25, "EXTRACTION_GAP", 0.0, ev_file, "표 'Ⅲ.기타 요구자본' 블록",
        ev_text, True, note)
    add("KR0009", "현대해상", q, 26, "EXTRACTION_GAP", 0.0, ev_file, "표 'Ⅲ.기타 요구자본' 블록",
        ev_text, True, note)

# ============================================================
# 신한이지손해보험 (KR0051)
# ============================================================
SH_MD = "md_inbox/{period}/KR0051_신한이지손해보험.md"
# 2023.1Q-2024.4Q: raw PDF 자체는 label에 mid-word 공백 오염("요 구자본"/"요구자 본")
# -- labels_compatible()의 "요구자본" 부분일치 가드가 원문 그대로 문자열 비교라 이 공백에
# 걸려 매칭 실패 -> match_baseline_value_or_zero가 행이 table_pairs에 있어도(대시 값) None
# 반환. normalise_label()은 이미 공백을 지우므로 1차 정확매칭엔 문제 없었지만 그 결과를
# labels_compatible()에 넘길 때 원본(raw) 문자열을 쓰는 게 문제.
SH_8Q = ["2023.1Q", "2023.2Q", "2023.3Q", "2023.4Q", "2024.1Q", "2024.2Q", "2024.3Q", "2024.4Q"]
SH_PERIOD = {
    "2023.1Q": "FY2023_Q1", "2023.2Q": "FY2023_Q2", "2023.3Q": "FY2023_Q3", "2023.4Q": "FY2023_Q4",
    "2024.1Q": "FY2024_Q1", "2024.2Q": "FY2024_Q2", "2024.3Q": "FY2024_Q3", "2024.4Q": "FY2024_Q4",
}
for q in SH_8Q:
    period = SH_PERIOD[q]
    ev_file = SH_MD.format(period=period)
    if q != "2024.4Q":
        ev_text = (
            "| Ⅲ. 기타 요구자본(1+2+3) | - | - | - |\n"
            "| 1. 업권별 자본규제를 활용한 종속회사의 요 구자본 환산치 | - | - | - |\n"
            "| 2. 비례성원칙을 적용한 종속회사의 요구자 본 대응치 | - | - | - |\n"
            "| 3. 업권별 자본규제를 활용한 관계회사의 요 구자본 환산치 | - | - | - |"
        )
        note = (
            "item23=item24=0 은 이미 마스터에 정상 존재(대시->0 매핑 성공). item25/26 은 라벨에 "
            "'요 구자본'/'요구자 본' 처럼 Docling 줄바꿈 과정에서 단어 중간에 공백이 끼어 "
            "labels_compatible() 의 원문(raw) 문자열 대상 '요구자본' 포함여부 검사가 실패 -- "
            "normalise_label() 자체는 공백을 지우므로 1차 사전 매칭은 이미 성공하는데, 그 결과를 "
            "검증하는 labels_compatible() 이 원문 그대로를 받아 재차 걸러버림(Meritz(KR0001) "
            "2026.1Q 의 '요구 자본' 사고와 동일 계열, 이번엔 회사·위치가 다름). 값 자체는 원문에 "
            "'-'(대시)로 인쇄돼 있어 0 이 맞음(같은 회사 item23/24 이 이미 0 인 것과 정합). 파서 "
            "수정: labels_compatible() 이 baseline_name/table_label 을 공백 제거한 사본(bn/tl)으로 "
            "비교하도록 변경 -- 결합 시뮬레이션에서 이 회사 item24/25/26 8분기 전부(2023.1Q-2024.3Q) "
            "None->0 으로 해소, 다른 회사 값 변경 0건."
        )
    else:
        ev_text = (
            "fitz get_text() 읽기순서 뒤섞임(2단 레이아웃 의심) -- 'Ⅲ.기타요구자본(1+2+3)' 및 "
            "'1.업권별...' 행은 정상 위치에 보이나 '2.비례성원칙...'/'3.업권별...관계회사...' 행은 "
            "페이지 후반부(159-178번째 줄, '다.지급여력비율' 행보다도 뒤)에 뒤섞여 등장. 값은 "
            "3열(당기/전기/전전기) 전부 '-'(대시). md_inbox 의 Docling 변환 결과에는 "
            "'기타 요구자본'/'업권별'/'비례성원칙'/'관계회사' 키워드가 단 하나도 없음(grep 0건) "
            "-- Docling 이 이 2단 레이아웃 블록 자체를 표로 인식하지 못하고 통째로 누락시킨 것으로 "
            "판단(라벨매칭 이전 단계, 내 파서 수정 2건이 닿지 않는 지점)."
        )
        note = (
            "item23=item24=0 은 이미 마스터에 정상 존재. item25/26 은 Docling 의 표 추출 자체가 "
            "이 분기만 통째로 실패(원문 raw PDF fitz 텍스트에는 4행 전부 존재, 값은 3열 전부 대시 "
            "-> 0). 내가 고친 두 파서 버그(공백값 처리/라벨공백 무시) 모두 '행이 table_pairs 후보에 "
            "있다'는 전제 위에서 동작하는데 이 분기는 그 전제 자체(extract_kics_detail_section의 "
            "표 인식)가 깨져 있어 자동 재추출로 닿지 않음 -- 수동 패치 필요. SANDWICHED: 바로 앞뒤 "
            "8개 분기가 전부 확인됨(같은 회사, 같은 대시=0 패턴)이 강한 방증."
        )
    add("KR0051", "신한이지손해보험", q, 25, "EXTRACTION_GAP", 0.0, ev_file, "표 'Ⅲ.기타 요구자본' 블록",
        ev_text, True, note)
    add("KR0051", "신한이지손해보험", q, 26, "EXTRACTION_GAP", 0.0, ev_file, "표 'Ⅲ.기타 요구자본' 블록",
        ev_text, True, note)

# 2026.1Q: 24/25/26 모두 결측(item23=0 만 존재)
q = "2026.1Q"
ev_file = SH_MD.format(period="FY2026_Q1")
ev_text = (
    "| Ⅲ. 기타 요구자본(1+2+3) | - | - | - |\n"
    "| 1. 업권별 자본규제를 활용한 종속회사의 요\\n구자본 환산치 | - | - | - |\n"
    "| 2. 비례성원칙을 적용한 종속회사의 요구자본\\n대응치 | - | - | - |\n"
    "| 3. 업권별 자본규제를 활용한 관계회사의 요\\n구자본 환산치 | - | - | - |"
)
note = (
    "8개 선행분기(2023.1Q-2024.4Q)와 동일 패턴: 라벨 줄바꿈 공백 오염 + 값은 전부 대시. "
    "labels_compatible() 공백무시 수정으로 item24/25/26 세 칸 전부 None->0 해소 확인"
    "(전체 시뮬레이션 실측: 'item24 KR0051 2026.1Q -> 0', 'item25 KR0051 2026.1Q -> 0', "
    "'item26 KR0051 2026.1Q -> 0')."
)
add("KR0051", "신한이지손해보험", q, 24, "EXTRACTION_GAP", 0.0, ev_file, "표 'Ⅲ.기타 요구자본' 블록", ev_text, True, note)
add("KR0051", "신한이지손해보험", q, 25, "EXTRACTION_GAP", 0.0, ev_file, "표 'Ⅲ.기타 요구자본' 블록", ev_text, True, note)
add("KR0051", "신한이지손해보험", q, 26, "EXTRACTION_GAP", 0.0, ev_file, "표 'Ⅲ.기타 요구자본' 블록", ev_text, True, note)

print(f"현대해상+신한이지 records so far: {len(records)}")

# ============================================================
# KB손해보험 (KR0010) -- 이미지 전용(스캔) PDF. 원문 렌더링(fitz get_pixmap
# 200-240dpi) 육안 확인으로 [경과조치 적용 전 지급여력비율 세부] 표를 직접 읽음.
# item24/26 은 매 분기 원문에 대시(간혹 비교열에서 '0' 숫자로 인쇄), item25 는
# 실값 -- KB 는 모든 '기타요구자본'을 '비례성원칙(간편법)' 하나로만 신고하고
# 있어 item24(업권별자본규제)/item26(관계회사) 개념 자체가 이 회사에 해당사항
# 없음. TFI(가용자본 경과조치)만 O, 그 외(TAC/TIR/TER/TIRR) 전부 X이고 그 중
# 어느 것도 기타요구자본(item23-26)에 적용되는 항목이 아니므로 값_적용후=값_적용전.
# ============================================================
KB_NOTE_HEAD = (
    "KB손해보험(KR0010)은 텍스트 레이어가 없는 스캔 PDF(주로 1Q/3Q 간이공시 25-27p, 일부 "
    "2Q/4Q 는 부분적으로 텍스트 있음) -- fitz get_pixmap(dpi 200-240)로 직접 렌더링해 "
    "[경과조치 적용 전 지급여력비율 세부] 표를 육안 확인. 이 표는 매 분기 3열(당분기/-1분기/-2분기) "
    "비교 형식이라 인접 분기 교차검증까지 됨. 항목24(업권별자본규제 활용 종속회사)/26(관계회사)은 "
    "모든 확인된 분기에서 예외 없이 대시(또는 비교열에서 숫자 '0')이고, 항목25(비례성원칙/간편법)만 "
    "실값을 가짐 -- '6-1-5) 비례성원칙 적용에 관한 사항' 서술 섹션의 해외종속회사(LIG재산보험(중국)/"
    "PT.KB Insurance Indonesia, 2024.4Q 이후 KBFG Insurance(China)로 사명변경) 총자산의 8%(간편법) "
    "합계가 [세부]표의 item25 값과 정확히 일치함을 별도 확인(예: 2024.2Q 11,929+3,777=15,706백만원"
    "=157.06->157). TFI(가용자본 경과조치)만 O(적용여부표 확인), TAC/TIR/TER/TIRR 전부 X이며 "
    "어느 것도 기타요구자본 항목에 적용되지 않음(TFI는 보완자본한도 계산에만 영향) -- 값_적용후=값."
)

KB_ROWS = [
    # quarter, item23(=item25), evidence(pdf path, pages, table snippet source)
    ("2023.4Q", 152.0, "data/disclosure/FY2023_Q4/raw/KR0010_KB손해보험.pdf",
     "p54(0-idx, 인쇄쪽 '53')",
     "회사명 LIG재산보험(중국)유한공사 총자산143,427 요구자본(8%)11,474 / PT.KB Insurance Indonesia "
     "총자산46,508 요구자본(8%)3,721 (단위:백만원) -> 11,474+3,721=15,195백만원=151.95->152",
     "6-1-5) 비례성원칙 적용에 관한 사항 ④적용대상 및 산출결과('23.12월말 기준) 서술표(fitz 텍스트, "
     "정상 순서로 읽힘 - 이 분기는 이 페이지 자체가 텍스트 레이어 있음)"),
    ("2024.1Q", 151.0, "data/disclosure/FY2024_Q1/raw/KR0010_KB손해보험_amended.pdf",
     "p13(0-idx, 인쇄쪽 '12')",
     "[경과조치 적용 전 지급여력비율 세부] 당분기(24.1Q) 열: Ⅲ.기타 요구자본(1+2+3)=151 / "
     "1.업권별...=- / 2.비례성원칙...=151 / 3.업권별...관계회사...=- "
     "(같은 표 비교열 당분기-1분기(23.4Q)=152, 당분기-2분기(23.3Q)=145 도 동시 확인)",
     "렌더링 이미지(get_pixmap dpi200) 육안 판독 -- [경과조치 적용 전 지급여력비율 세부] 표 전체가 "
     "이 한 페이지에 있고 item23-26 4행이 그대로 인쇄돼 있음(long-form 회사들과 동일 표 서식, 이 "
     "회사는 스캔 이미지로만 존재)"),
    ("2024.2Q", 157.0, "data/disclosure/FY2024_Q2/raw/KR0010_KB손해보험_amended.pdf",
     "p20(0-idx, 인쇄쪽 '19')",
     "회사명 KBFG Insurance(China)... (2024.2Q 시점엔 여전히 이전 사명 다수) 총자산149,106 "
     "요구자본(8%)11,929 / PT.KB Insurance Indonesia 총자산47,209 요구자본(8%)3,777 -> "
     "11,929+3,777=15,706백만원=157.06->157 (owner gold data/_gold/kr0010_user_cells.json 과 정확 일치)",
     "6-1-5) 비례성원칙 적용에 관한 사항 서술표(이 분기는 텍스트 레이어 있음, fitz 직접 판독)"),
    ("2024.3Q", 148.0, "data/disclosure/FY2024_Q3/raw/KR0010_KB손해보험_amended.pdf",
     "p13(0-idx, 인쇄쪽 '12')",
     "[경과조치 적용 전 지급여력비율 세부] 당분기(24.3Q) 열: Ⅲ.기타 요구자본(1+2+3)=148 / "
     "1.업권별...=- / 2.비례성원칙...=148 / 3.업권별...관계회사...=- "
     "(비교열 당분기-1분기(24.2Q)=157, 당분기-2분기(24.1Q)=151 도 동시 재확인 - 151/157 모두 "
     "위 두 분기 값과 정확 일치)",
     "렌더링 이미지(get_pixmap dpi200) 육안 판독"),
    ("2024.4Q", 154.0, "data/disclosure/FY2024_Q4/raw/KR0010_KB손해보험.pdf",
     "p62(0-idx, 인쇄쪽 '61')",
     "회사명 KBFG Insurance(China) Co., Ltd 총자산129,011 요구자본(8%)10,321 / "
     "PT.KB Insurance Indonesia 총자산62,951 요구자본(8%)5,036 -> 10,321+5,036=15,357백만원"
     "=153.57->154",
     "6-1-5) 비례성원칙 적용에 관한 사항 서술표(텍스트 레이어 있음) + 2025.1Q 자체 [세부]표의 "
     "비교열(당분기-1분기=24.4Q)에서도 154 로 재확인(교차검증 2건)"),
    ("2025.1Q", 154.0, "data/disclosure/FY2025_Q1/raw/KR0010_KB손해보험.pdf",
     "p16(0-idx, 인쇄쪽 '15')",
     "[경과조치 적용 전 지급여력비율 세부] 당분기(25.1Q)=154 / 1.업권별...=- / 2.비례성원칙...=154 / "
     "3.업권별...관계회사...=- (비교열 24.4Q=154,항목24/26='0'으로 인쇄, 24.3Q=148,항목24/26='0')",
     "렌더링 이미지(get_pixmap dpi200) 육안 판독 -- owner gold(item25=154)와 정확 일치"),
    ("2025.2Q", 136.0, "data/disclosure/FY2025_Q2/raw/KR0010_KB손해보험.pdf",
     "p21(0-idx, 인쇄쪽 '20')",
     "회사명 KBFG Insurance(China) 총자산113,063 요구자본(8%)9,045 / PT.KB Insurance Indonesia "
     "총자산56,401 요구자본(8%)4,512 -> 9,045+4,512=13,557백만원=135.57->136",
     "6-1. 비례성원칙 적용에 관한 사항(이 분기부터 소제목 번호가 6-1-5에서 6-1로 단순화됨) "
     "서술표(텍스트 레이어 있음) -- census 상 item25=136 이 이미 마스터에 정상 존재해 일치 확인만"),
    ("2025.3Q", 128.0, "data/disclosure/FY2026_Q1/raw/KR0010_KB손해보험.pdf",
     "p17(0-idx, 인쇄쪽 '16')",
     "[경과조치 적용 전 지급여력비율 세부] 당분기-2분기(25.3Q)=128 / 1.업권별...=- / "
     "2.비례성원칙...=128 / 3.업권별...관계회사...=-",
     "2026.1Q 자체 신고서의 비교열(당분기-2분기=25.3Q)로 교차확인(렌더링 이미지 육안 판독) -- "
     "census 상 item25=128 이미 마스터 정상, item24/26 만 결측"),
    ("2025.4Q", 123.0, "data/disclosure/FY2026_Q1/raw/KR0010_KB손해보험.pdf",
     "p17(0-idx, 인쇄쪽 '16')",
     "[경과조치 적용 전 지급여력비율 세부] 당분기-1분기(25.4Q)=123 / 1.업권별...=- / "
     "2.비례성원칙...=123 / 3.업권별...관계회사...=-",
     "2026.1Q 자체 신고서의 비교열(당분기-1분기=25.4Q)로 교차확인(렌더링 이미지 육안 판독) -- "
     "owner gold(item25=123)와 정확 일치, item24/26 만 결측"),
    ("2026.1Q", 131.0, "data/disclosure/FY2026_Q1/raw/KR0010_KB손해보험.pdf",
     "p17(0-idx, 인쇄쪽 '16')",
     "[경과조치 적용 전 지급여력비율 세부] 당분기(26.1Q)=131 / 1.업권별...=- / 2.비례성원칙...=131 / "
     "3.업권별...관계회사...=-",
     "렌더링 이미지(get_pixmap dpi200) 육안 판독 -- owner gold(item25=131)와 정확 일치, "
     "item24/26 만 결측"),
    ("2026.2Q", 133.0, "(직전 세션 патch, 미검증 재확인은 못함 -- 근거는 owner gold 아님)",
     "-", "-",
     "이 분기는 내가 직접 렌더링/재확인하지 못했다. 근거는 직전 세션(2026-08-31)의 "
     "scripts/_probes/_kr0010_write_final_patch.py 가 raw PDF p.21 '[경과조치 적용 전 지급여력비율 "
     "세부]' 표를 fitz get_pixmap 220dpi로 직접 판독해 item25=133, item24/26=대시(0, 미기재)로 "
     "확정한 결과이며 이 값은 census 파일(data/_derived/item23_children_audit/B_item24_26_row_absent.json) "
     "의 현재 라이브 마스터 상태(item25=133 이미 존재, item24/26 결측)와 일치한다. 나머지 10개 "
     "분기와 동일한 패턴(item24/26=대시, item25=간편법 종속회사 합계)이라 UNMEASURED 로 미루지 않고 "
     "EXTRACTION_GAP·값0 으로 판정하되, 내가 직접 원문을 본 게 아니라는 점을 명시한다."),
]

for q, item23, pdf_path, page_ref, subsid_calc, table_text in KB_ROWS:
    ev_text = f"{table_text}\n계산: {subsid_calc}" if subsid_calc != "-" else table_text
    if q in ("2023.4Q", "2024.1Q", "2024.3Q", "2024.4Q"):
        mislabel_note = (
            f" **중요: 현재 마스터는 이 값({item23:.0f})을 item24(업권별자본규제) 필드에 잘못 "
            "적재하고 있다(census: children_pre.24={0:.0f}, 25/26 null). 원문은 이 값이 item25"
            "(비례성원칙)이고 item24는 대시(0)다 -- 이건 '행 결측'이 아니라 '기존 셀 오분류'이므로 "
            "패치 시 item24를 0으로 정정하고 item25에 이 값을 새로 적재해야 항등식(23=24+25+26)이 "
            "닫힌다. item24 자체는 이번 32버킷 입력에 absent로 잡히지 않았음(값이 있어서) -- 이 "
            "verdict는 item25/26 두 칸만 formal 하되 이 정정 필요성을 별도로 강조한다.".format(item23)
        )
    else:
        mislabel_note = ""
    note = KB_NOTE_HEAD + " " + mislabel_note
    add("KR0010", "KB손해보험", q, 25, "EXTRACTION_GAP", item23, pdf_path, page_ref, ev_text, True, note)
    # item26: always a gap in every one of the 11 buckets
    add("KR0010", "KB손해보험", q, 26, "EXTRACTION_GAP", 0.0, pdf_path, page_ref, ev_text, True,
        KB_NOTE_HEAD)
    # item24: only a *formal* gap-verdict for the 7 quarters where census lists it absent
    # (the other 4 quarters have it present-but-mislabeled, handled via the note above)
    if q not in ("2023.4Q", "2024.1Q", "2024.3Q", "2024.4Q"):
        add("KR0010", "KB손해보험", q, 24, "EXTRACTION_GAP", 0.0, pdf_path, page_ref, ev_text, True,
            KB_NOTE_HEAD)

print(f"total records: {len(records)}")

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
print("wrote", OUT)

# quick tally
from collections import Counter
by_company_verdict = Counter((r["code"], r["verdict"]) for r in records)
for k, v in sorted(by_company_verdict.items()):
    print(k, v)
buckets = {(r["code"], r["quarter"]) for r in records}
print("unique buckets:", len(buckets))
