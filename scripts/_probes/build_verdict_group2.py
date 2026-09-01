# -*- coding: utf-8 -*-
"""Build data/_derived/item23_children_audit/verdict_group2.json (deliverable).
Read-only w.r.t. kics_disclosure.json -- writes only to the audit output dir."""
import json
from pathlib import Path

ROOT = Path(r"C:\Users\sangwook.cho\Desktop\insurequant")
OUT = ROOT / "data" / "_derived" / "item23_children_audit" / "verdict_group2.json"

V = []

def add(code, name, quarter, item, verdict, pre, post, ev_file, ev_lines, ev_text, sandwiched, note):
    V.append({
        "code": code, "name": name, "quarter": quarter, "item": item,
        "verdict": verdict, "value_pre": pre, "value_post": post,
        "evidence_file": ev_file, "evidence_lines": ev_lines, "evidence_text": ev_text,
        "sandwiched": sandwiched, "note": note,
    })

# ---------------------------------------------------------------------------
# Hanwha Non-Life (KR0002) -- 9 quarters, item25 only. Label variant "daeyongchi"
# (substitute value) instead of canonical "daeeungchi" (corresponding value),
# consistently from 2023.4Q onward (2023.1Q-3Q used correct spelling).
# Row+value(0 or "-") present in every quarter; only the label text differs.
HANWHA_LINES = {
    "2023.4Q": ("data/disclosure/FY2023_Q4/parsed/KR0002_한화손해보험.md", "L350-353",
                "Ⅲ. 기타요구자본(1+2+3) = 0/0/0; item25 라벨 '대용치' 변형, 값 0/0/0"),
    "2024.1Q": ("data/disclosure/FY2024_Q1/parsed/KR0002_한화손해보험.md", "L307-310",
                "Ⅲ. 기타요구자본(1+2+3) = -/-/-; item25 라벨 '대용치' 변형, 값 -/-/-"),
    "2024.2Q": ("data/disclosure/FY2024_Q2/parsed/KR0002_한화손해보험.md", "L314-317",
                "Ⅲ. 기타요구자본(1+2+3) = -/-/-; item25 라벨 '대용치' 변형, 값 -/-/-"),
    "2024.4Q": ("data/disclosure/FY2024_Q4/parsed/KR0002_한화손해보험.md", "L340-343",
                "Ⅲ. 기타요구자본(1+2+3) = -/-/-; item25 라벨 '대용치' 변형, 값 -/-/-"),
    "2025.1Q": ("data/disclosure/FY2025_Q1/parsed/KR0002_한화손해보험.md", "L242-245",
                "Ⅲ. 기타요구자본(1+2+3) = -/-/-; item25 라벨 '대용치' 변형, 값 -/-/-"),
    "2025.2Q": ("data/disclosure/FY2025_Q2/parsed/KR0002_한화손해보험.md", "L253-256",
                "Ⅲ. 기타요구자본(1+2+3) = -/-/-; item25 라벨 '대용치' 변형, 값 -/-/-"),
    "2025.4Q": ("data/disclosure/FY2025_Q4/parsed/KR0002_한화손해보험.md", "L376-379",
                "Ⅲ. 기타요구자본(1+2+3) = -/-/-; item25 라벨 '대용치' 변형, 값 -/-/-"),
    "2026.1Q": ("data/disclosure/FY2026_Q1/parsed/KR0002_한화손해보험.md", "L409-412",
                "Ⅲ. 기타요구자본(1+2+3) = -/-/-; item25 라벨 '대용치' 변형, 값 -/-/-"),
    "2026.2Q": ("data/disclosure/FY2026_Q2/parsed/KR0002_한화손해보험.md", "L384-387",
                "Ⅲ. 기타요구자본(1+2+3) = -/-/-; item25 라벨 '대용치' 변형, 값 -/-/-"),
}
for q, (f, l, t) in HANWHA_LINES.items():
    screen = q in ("2026.1Q", "2026.2Q")
    note = ("라벨 변형 '대용치'(2023.4Q부터 전 분기 동일, 2023.1Q-3Q는 '대응치'로 정상 추출됨=SANDWICHED "
            "확정). item23=item24=item26=0 항등식, 값은 항상 0/-. 2026-09-01 파서 수정: "
            "src/solvency/parser/company_handlers.py LABEL_FIXES에 '대용치'->'대응치' 추가"
            "(전수 시뮬레이션 dry-run 확인: ins 123->134, upd/rem 불변=회귀 없음). "
            "이 수정으로 9개 분기 전부 자동 재추출 가능함"
            "(fill_period_to_disclosure.py --all-periods --refresh 실행 시; 마스터는 건드리지 않았음).")
    if screen:
        note += " 화면 분기."
    add("KR0002", "한화손해보험", q, 25, "EXTRACTION_GAP", 0.0, 0.0, f, l, t, True, note)

# ---------------------------------------------------------------------------
# Lotte Non-Life (KR0003) -- 2026.1Q/2026.2Q, item24+25. Root cause: the
# SOURCE PDF's own embedded font drops the "jong" glyph in "jongsokhoesa"
# (subsidiary) -> renders as a stray combining-mark prefix (confirmed via
# direct fitz PDF text extraction -- a font/encoding defect in the PDF
# itself, not a Docling artifact). 2026.1Q's Docling table structure is also
# garbled (loose "-" lines instead of a table). Values unambiguous: all-dash.
add("KR0003", "롯데손해보험", "2026.1Q", 24, "EXTRACTION_GAP", 0.0, 0.0,
    "data/disclosure/FY2026_Q1/raw/KR0003_롯데손해보험.pdf", "p.22 (fitz 텍스트 직접추출)",
    "1. 업권별 자본규제를 활용한 [종 글리프 누락]속회사의 요구자본 환산치 - - - / "
    "2. 비례성원칙을 적용한 [종 누락]속회사의 요구자본 대응치 - - - / "
    "3. 업권별 자본규제를 활용한 관계회사의 요구자본 환산치 - - - / "
    "다. 지급여력비율: 가÷나×100 = 131.93 / 126.06 / 115.33",
    False,
    "Docling MD의 이 구간은 테이블 구조 인식 실패로 깨진 상태(loose '-' 줄)라 md 대신 원문 PDF를 "
    "fitz로 직접 읽었다. PDF 자체 임베드폰트가 '종' 글리프를 누락시켜 '종속회사'가 깨져 렌더링됨"
    "(라벨 매칭 실패의 근본원인, Docling 탓이 아니라 원문 PDF 폰트 결함). item23/24/25 전부 대시=0, "
    "item26('관계회사', '종속' 의존 없음)은 이미 마스터에 값24=0 으로 로드돼 있음(레이블에 '종속' "
    "토큰이 없어 매칭이 살아남은 것으로 추정). 값_적용후: item23 후=0 이미 마스터에 있고, [경과조치 "
    "적용에 관한 사항] 표에서 지급여력비율이 131.93/131.93로 전후 동일 -> 지급여력기준금액(분모, "
    "item23 포함)도 전후 동일 -> 0. 화면 분기.")
add("KR0003", "롯데손해보험", "2026.1Q", 25, "EXTRACTION_GAP", 0.0, 0.0,
    "data/disclosure/FY2026_Q1/raw/KR0003_롯데손해보험.pdf", "p.22 (fitz 텍스트 직접추출)",
    "2. 비례성원칙을 적용한 [종 누락]속회사의 요구자본 대응치 - - -",
    False,
    "item24와 동일 근거/동일 원인(PDF 폰트 결함으로 '종' 누락). 값_적용후=0 (item24와 동일 논리). "
    "화면 분기.")
add("KR0003", "롯데손해보험", "2026.2Q", 24, "EXTRACTION_GAP", 0.0, 0.0,
    "data/disclosure/FY2026_Q2/parsed/KR0003_롯데손해보험.md", "L636-640",
    "Ⅲ.기타 요구자본(1+2+3)=- / 1.업권별...[종 누락]속회사...환산치=- / "
    "2.비례성원칙...[종 누락]속회사...대응치=- / 3.업권별...관계회사...환산치=-",
    False,
    "2026.1Q와 동일한 PDF 폰트 결함('종' 글리프 누락). 이번엔 Docling 테이블 자체는 정상 인식했으나 "
    "라벨 매칭이 '종속회사' 서브스트링에 의존해 실패. item26('관계회사', '종' 의존 없음)은 정상 "
    "추출됨(마스터 값24=0) -- item24/25만 빠진 것과 정확히 일치. 값_적용후: item23 후=0 이미 마스터. "
    "화면 분기.")
add("KR0003", "롯데손해보험", "2026.2Q", 25, "EXTRACTION_GAP", 0.0, 0.0,
    "data/disclosure/FY2026_Q2/parsed/KR0003_롯데손해보험.md", "L636-640",
    "2.비례성원칙...[종 누락]속회사...대응치=-", False,
    "item24와 동일 근거/원인. 값_적용후=0. 화면 분기.")

# ---------------------------------------------------------------------------
# AXA Non-Life (KR0049) -- 6 quarters, mixed causes.
add("KR0049", "악사손해보험", "2023.1Q", 25, "EXTRACTION_GAP", 0.0, 0.0,
    "data/disclosure/FY2023_Q1/parsed/KR0049_악사손해보험.md", "L121-125",
    "Ⅲ. 기타 요구자본(1+2+3) = 0/-/-; item25 라벨 '요구 자본'(공백삽입) 변형, 값 0/-/-",
    False,
    "라벨의 '요구 자본'(공백 삽입) 변형 -- 메리츠 2026.1Q와 동일 지문. 값=0. 2026-09-01 파서 수정: "
    "company_handlers.py LABEL_FIXES에 '요구 자본 대응치'->'요구자본 대응치' 추가(단위 테스트로 "
    "매칭 성공 확인, _label_matches()=True 재현). 단, 실제 fill_period 전체 재실행 시뮬레이션에서는 "
    "이 회사가 baseline 조회 경로상의 다른 이유로 아직 자동 반영되지 않음(직접 소스 근거로 verdict "
    "확정, 자동재추출 파이프라인 잔여 이슈는 보고서에 별도 기록).")
add("KR0049", "악사손해보험", "2023.2Q", 26, "EXTRACTION_GAP", 0.0, 0.0,
    "data/disclosure/FY2023_Q2/parsed/KR0049_악사손해보험.md", "L85-96",
    "item25 라벨 '종속회사의 요구자본'까지만 있고 값=-/-/- 인 채로 표가 이미지로 끊긴 뒤 "
    "'대응치' 접미사만 별도 미니테이블로 이어짐; item26 '3.업권별...관계회사의 요구 자본 환산치'=-/-/-",
    False,
    "페이지 경계에 이미지가 끼면서 표가 두 조각으로 쪼개짐(item25 라벨 '대응치' 접미사가 이미지 뒤 "
    "별도 미니테이블로 분리) + item26 라벨도 '요구 자본'(공백) 변형. item26 자체 행은 살아있고 "
    "값=-(=0). 값_적용후=0(item23 후=0 이미 마스터).")
add("KR0049", "악사손해보험", "2023.3Q", 25, "EXTRACTION_GAP", 0.0, 0.0,
    "data/disclosure/FY2023_Q3/parsed/KR0049_악사손해보험.md", "L201-205",
    "Ⅲ. 기타 요구자본(1+2+3) = 0/0/0; item25 라벨 '요구 자본'(공백삽입) 변형, 값 0/0/0",
    False,
    "2023.1Q와 동일('요구 자본' 공백 변형). 값=0, 값_적용후=0(item23 후=0 이미 마스터, 형제 "
    "값_적용후도 채워짐).")
add("KR0049", "악사손해보험", "2024.3Q", 25, "SOURCE_ABSENT", None, None,
    "data/disclosure/FY2024_Q3/parsed/KR0049_악사손해보험.md", "L117,L142",
    ": 지급여력비율은 2024 년 12 월말 공시 예정임 (보험업감독규정 부칙 제 3 조)",
    False,
    "이 분기는 K-ICS 지급여력비율 표 전체(item1-28)가 공시되지 않음 -- 명문 규정(보험업감독규정 "
    "부칙 제3조)에 따라 2024년 12월말(4Q)로 공시가 이연됨. 4-2절과 6-1절(비례성원칙) 둘 다 동일 "
    "문구로 명시. item23/24 등 마스터에 남은 '0' 값은 이 분기 실제 공시가 아니라 별도 경로"
    "(baseline supplement)로 채워진 것으로 보이며 본 감사 범위 밖(item25/26에 한함). 판정불가 "
    "아님 -- 원문에 결측 사유가 명시돼 있어 SOURCE_ABSENT로 확정.")
add("KR0049", "악사손해보험", "2024.3Q", 26, "SOURCE_ABSENT", None, None,
    "data/disclosure/FY2024_Q3/parsed/KR0049_악사손해보험.md", "L117,L142",
    ": 지급여력비율은 2024 년 12 월말 공시 예정임 (보험업감독규정 부칙 제 3 조)",
    False, "item25와 동일 근거(공시 자체가 이연됨).")
add("KR0049", "악사손해보험", "2024.4Q", 25, "SOURCE_ABSENT", None, None,
    "data/disclosure/FY2024_Q4/raw/KR0049_악사손해보험.pdf", "p.35-43 (fitz 전체텍스트 대조)",
    "p.42 '② 장수위험ㆍ사업비위험ㆍ해지위험 및 대재해위험 경과조치' 표: 기타요구자본 = 0 / 0 "
    "(item24/25/26 세부구분 없이 합계 한 줄만 존재)",
    False,
    "104페이지 전체를 fitz로 '비례성원칙'/'관계회사'/'종속회사' 키워드 검색한 결과 '관계회사'/"
    "'종속회사' 0건, '비례성원칙'은 6-1절 서술('회사는 비례성원칙을 적용하지 않습니다')에만 등장 "
    "-- 표에 항목 1/2/3 세부 행 자체가 없음. item15-22/23/27/28은 items1-28 3열 비교표가 아니라 "
    "p.42의 '선택적용경과조치' 2열(적용전/적용후) 표에서 온 것으로 확인(생명ㆍ장기손해보험위험액 "
    "등 세부위험 항목까지 나열되지만 기타요구자본은 세부화 없이 합계만). '기타요구자본' 합계=0/0 "
    "이지만 item24/25/26 개별 행이 원천적으로 미존재 -> SOURCE_ABSENT. fitz 키워드 0건이 이유가 "
    "아니라 104p 전체 텍스트 직접 대조로 확인한 것.")
add("KR0049", "악사손해보험", "2024.4Q", 26, "SOURCE_ABSENT", None, None,
    "data/disclosure/FY2024_Q4/raw/KR0049_악사손해보험.pdf", "p.35-43 (fitz 전체텍스트 대조)",
    "p.42 기타요구자본 = 0 / 0", False, "item25와 동일 근거.")
add("KR0049", "악사손해보험", "2025.1Q", 25, "SOURCE_ABSENT", None, None,
    "data/disclosure/FY2025_Q1/raw/KR0049_악사손해보험.pdf", "p.11-20 (fitz 전체텍스트 대조)",
    "p.19 선택적용경과조치 표: 기타요구자본 = 0 / 0",
    False,
    "2024.4Q와 동일 필링 포맷(30페이지 전체 fitz 검색, '관계회사'/'종속회사' 0건, '비례성원칙'은 "
    "6-1절 서술 1건뿐). item24/25/26 개별 행 원천 미존재 -> SOURCE_ABSENT.")
add("KR0049", "악사손해보험", "2025.1Q", 26, "SOURCE_ABSENT", None, None,
    "data/disclosure/FY2025_Q1/raw/KR0049_악사손해보험.pdf", "p.11-20 (fitz 전체텍스트 대조)",
    "p.19 기타요구자본 = 0 / 0", False, "item25와 동일 근거.")

# ---------------------------------------------------------------------------
# Hana Non-Life (KR0050)
add("KR0050", "하나손해보험", "2023.3Q", 25, "EXTRACTION_GAP", 0.0, 0.0,
    "data/disclosure/FY2023_Q3/parsed/KR0050_하나손해보험_amended.md", "L232-236",
    "Ⅲ. 기타 요구자본 (1+2+3) = 0/0/0; item25 라벨 '요구 자본'(공백삽입) 변형, 값 0/0/0",
    False,
    "'요구 자본' 공백 변형(메리츠 사례와 동일 지문). 값=0. 값_적용후=0 -- item23/item24/item26의 "
    "값_적용후가 이미 '0'으로 마스터에 채워져 있어(형제 항목 처리와 동일하게 적용) 근거 확실.")

# ---------------------------------------------------------------------------
# AIA Life (KR0080)
AIA_EV = ("data/disclosure/FY2024_Q1/raw/KR0080_에이아이에이생명보험.pdf",
          "p.13 (240dpi 렌더 육안확인 + fitz 텍스트 대조)",
          "Ⅲ.기타 요구자본(1+2+3): 당분기칸=- / 1.종속회사환산치: 당분기칸=완전공백 / "
          "2.종속회사대응치: 당분기칸=완전공백 / 3.관계회사환산치: 당분기칸=완전공백 "
          "(부모 item23 당분기 칸은 '-', 자식 3개만 완전공백. 240dpi 렌더로 시각 재확인 완료 -- "
          "OCR누락이 아니라 원본 PDF 표 자체가 이 3행의 1열만 공백)")
for item in (24, 25, 26):
    add("KR0080", "에이아이에이생명보험", "2024.1Q", item, "EXTRACTION_GAP", 0.0, 0.0,
        AIA_EV[0], AIA_EV[1], AIA_EV[2], False,
        "당분기(1열) 셀이 대시(-)조차 아닌 완전 공백 -- 240dpi 렌더로 재확인해도 동일(스캔/OCR "
        "문제 아님, AIA 자체 표 렌더링에서 이 3행만 1열이 비워짐). 부모 item23의 1열도 동일하게 "
        "공백이며 마스터엔 이미 0으로 로드돼 있어 같은 처리를 자식에도 적용. '당사는 경과조치를 "
        "적용하지 않아 경과조치 전ㆍ후 금액 및 비율이 동일함' 명시(p.13) -> 값_적용후=값=0.")

# ---------------------------------------------------------------------------
# Hana Life (KR0097)
add("KR0097", "하나생명보험", "2024.4Q", 25, "EXTRACTION_GAP", 0.0, 0.0,
    "data/disclosure/FY2024_Q4/parsed/KR0097_하나생명보험.md", "L299-303",
    "Ⅲ. 기타요구자본 = -(적용전)/-(적용후); item25 라벨 '대용치' 변형, 값 -(적용전)/-(적용후)",
    False,
    "라벨 변형 '대용치'(한화손해보험과 동일 지문). 이 표는 재무제표 주석 스타일 4열(과목|경과조치 "
    "적용전(2열)|경과조치 적용후(2열))이라 적용전/적용후 값이 원문에 나란히 명시돼 있음 -- 둘 다 "
    "'-'(=0). 열 정렬은 문서 내에서 행마다 살짝 밀리지만(item25 행은 값이 1,3열에, 부모/형제 행은 "
    "2,4열에 옴) 어느 쪽으로 읽어도 결론은 0/0으로 동일. 2026-09-01 파서 수정('대용치'->'대응치')으로 "
    "이 분기도 자동 재추출 가능함(시뮬레이션 확인).")

# ---------------------------------------------------------------------------
# KB Life (KR0099) -- word-wrap row-split corruption throughout.
add("KR0099", "KB라이프생명", "2023.3Q", 25, "EXTRACTION_GAP", 0.0, 0.0,
    "data/disclosure/FY2023_Q3/parsed/KR0099_케이비라이프생명보험.md", "L199-205",
    "Ⅲ.기타 요구자본(1+2+3)=0/0/0; item25 라벨 '2.비례성원칙을 적용한 종속회사 의'(뒷부분 절단, "
    "값 0/0/0은 이 절단행에 인쇄); item26 라벨 '3.업권별...관계'(뒷부분 절단, 값 0/0/0); 이어지는 "
    "행 '회사의 요구자본 환산치'는 값 없음",
    False,
    "Docling이 원문 셀 내 줄바꿈(긴 한글 라벨이 좁은 열에서 2줄로 인쇄)을 별도 표 행으로 잘못 "
    "분리 -- item25/26 라벨이 둘 다 앞부분만 남고 값(0/0/0)은 그 잘린 행에 그대로 붙어있음(뒷부분 "
    "'회사의 요구자본 환산치'는 값이 빈 별도 행으로 떨어져 나감). 값=0은 잘린 행 자체에 이미 "
    "인쇄돼 있어 확실. 값_적용후=0(item23 후=0 이미 마스터).")
add("KR0099", "KB라이프생명", "2023.3Q", 26, "EXTRACTION_GAP", 0.0, 0.0,
    "data/disclosure/FY2023_Q3/parsed/KR0099_케이비라이프생명보험.md", "L199-205",
    "item26 라벨 '3.업권별 자본규제를 활용한 관계'(뒷부분 절단), 값 0/0/0", False,
    "item25와 동일 원인/근거.")
add("KR0099", "KB라이프생명", "2023.4Q", 24, "EXTRACTION_GAP", 0.0, 0.0,
    "data/disclosure/FY2023_Q4/parsed/KR0099_케이비라이프생명보험_amended.md", "L185-192",
    "Ⅲ.기타 요구자본(1+2+3)=0/0/0; item24 라벨 '1.업권별...종속 회사'(절단) 값 0/0/0; 다음행 "
    "'의 요구자본 환산치 2.비례성원칙을 적용한 종속회사'(item24 접미사+item25 라벨이 한 행에 "
    "뭉침) 값 0/0/0; 그 다음 '의 요구자본 대응치'행은 값 없음; item26 '3.업권별...관계 회사의' "
    "값 0/0/0",
    False,
    "동일한 줄바꿈-행분리 오염, 이번엔 item24 라벨 뒷부분이 item25 라벨 앞부분과 한 행에 뭉쳐짐. "
    "값(0/0/0)은 뭉쳐진 행에 그대로 인쇄돼 있어 item24/25/26 셋 다 확정 가능. 값_적용후=0.")
add("KR0099", "KB라이프생명", "2023.4Q", 25, "EXTRACTION_GAP", 0.0, 0.0,
    "data/disclosure/FY2023_Q4/parsed/KR0099_케이비라이프생명보험_amended.md", "L185-192",
    "'의 요구자본 환산치 2.비례성원칙을 적용한 종속회사' 행에 값 0/0/0 (item24 접미사와 뭉침)",
    False, "item24와 동일 근거.")
add("KR0099", "KB라이프생명", "2023.4Q", 26, "EXTRACTION_GAP", 0.0, 0.0,
    "data/disclosure/FY2023_Q4/parsed/KR0099_케이비라이프생명보험_amended.md", "L185-192",
    "'3.업권별 자본규제를 활용한 관계 회사의' 행에 값 0/0/0", False, "item24와 동일 근거.")
add("KR0099", "KB라이프생명", "2024.1Q", 26, "EXTRACTION_GAP", 0.0, 0.0,
    "data/disclosure/FY2024_Q1/parsed/KR0099_케이비라이프생명보험_amended.md", "L232-238",
    "'3.업권별 자본규제를 활용한 관계회'(절단) 값 0/0/0; 다음행 '사의 요구자본 환산치'는 값 없음",
    False,
    "item24/25는 이 분기 라벨이 완전한 형태로 정상 추출됨(대응치, 공백 없음) -- item26만 "
    "줄바꿈-분리로 빠짐. 값=0(잘린 행에 인쇄), 값_적용후=0(형제 item24/25 값_적용후가 이미 '0'으로 "
    "채워져 있어 동일 처리).")
add("KR0099", "KB라이프생명", "2025.1Q", 24, "EXTRACTION_GAP", 0.0, 0.0,
    "data/disclosure/FY2025_Q1/parsed/KR0099_케이비라이프생명보험.md", "L249-253",
    "'1.업권별 자본규제를 활용한 종속회 사'(절단) 값 -/-/-; item25 '2.비례성원칙을 적용한 "
    "종속회사의 요구자본 대응치'(정상) 값 -/-/-; item26 '3.업권별...관계회 사의 요구자본 "
    "환산치'(정상) 값 -/-/-",
    False,
    "이번엔 item24만 줄바꿈으로 라벨이 잘림('의 요구자본 환산치' 접미사 소실, 그 다음 행이 빈 줄 "
    "이후라 값과 재결합 안 됨). item25/26은 정상 추출. 값=-(=0)은 잘린 행 자체에 인쇄. "
    "값_적용후=0(형제 item25/26 값_적용후 이미 '0').")
add("KR0099", "KB라이프생명", "2025.3Q", 24, "EXTRACTION_GAP", 0.0, 0.0,
    "data/disclosure/FY2025_Q3/parsed/KR0099_케이비라이프생명보험.md", "L246-250",
    "'1.업권별 자본규제를 활용한 종속회 사'(절단) 값 -/-/-", False,
    "2025.1Q와 동일 패턴/근거.")

# ---------------------------------------------------------------------------
# NongHyup Life (KR0104)
add("KR0104", "농협생명보험", "2026.2Q", 24, "EXTRACTION_GAP", 0.0, 0.0,
    "data/disclosure/FY2026_Q2/parsed/KR0104_농협생명보험.md", "L331-334",
    "Ⅲ.기타 요구자본(1+2+3)=-/-/-; item24 라벨 '1.업권별 자본규제를 활용한'(절단) 값 -/-/-; "
    "다음행 '종속회사의 요구자본 환산치 2.비례성원칙을 적용한 종속회사의 요구자본 대응치'"
    "(item24 접미사+item25 전체가 한 행에 뭉침) 값 -/-/-; item26은 정상 분리",
    False,
    "줄바꿈-행분리: item24 라벨 뒷부분이 item25 라벨 전체와 한 행에 뭉쳐짐(값 -는 그 행에 인쇄). "
    "item26은 정상 분리돼 추출됨. 값=-(=0), 값_적용후=0(item23 후=0 이미 마스터). 화면 분기.")
add("KR0104", "농협생명보험", "2026.2Q", 25, "EXTRACTION_GAP", 0.0, 0.0,
    "data/disclosure/FY2026_Q2/parsed/KR0104_농협생명보험.md", "L331-334",
    "'종속회사의 요구자본 환산치 2.비례성원칙을 적용한 종속회사의 요구자본 대응치' 행에 값 -/-/-",
    False, "item24와 동일 근거. 화면 분기.")

# ---------------------------------------------------------------------------
# Seoul Guarantee Insurance (KR0150)
add("KR0150", "서울보증보험", "2026.1Q", 25, "EXTRACTION_GAP", 0.0, 0.0,
    "data/disclosure/FY2026_Q1/parsed/KR0150_서울보증보험.md", "L495-498",
    "Ⅲ.기타 요구자본(1+2+3)=0/0/0; item25 라벨 '2.비례성원칙을 적용한 종속회사의'(절단) 값 0/0/0; "
    "다음행 '요구자본 대응치 3.업권별 자본규제를 활용한 관계회사의 요구자본 환산치'(item25 접미사"
    "+item26 전체가 한 행에 뭉침) 값 0/0/0; item24는 정상 분리",
    False,
    "줄바꿈-행분리: item25 라벨 뒷부분('요구자본 대응치')이 item26 라벨 전체와 한 행에 뭉쳐짐(값 "
    "0/0/0은 그 행에 인쇄). item24는 정상 분리돼 추출됨. 값=0, 값_적용후=0(형제 item24 값_적용후 "
    "이미 '0'으로 채워져 있어 동일 처리). 화면 분기.")
add("KR0150", "서울보증보험", "2026.1Q", 26, "EXTRACTION_GAP", 0.0, 0.0,
    "data/disclosure/FY2026_Q1/parsed/KR0150_서울보증보험.md", "L495-498",
    "'요구자본 대응치 3.업권별 자본규제를 활용한 관계회사의 요구자본 환산치' 행에 값 0/0/0",
    False, "item25와 동일 근거. 화면 분기.")

# ---------------------------------------------------------------------------
# KakaoPay Non-Life (KR1098) -- scan-only PDF (text layer ~190 chars over 61
# pages), resolved via 240dpi page render (p.29), not text search.
add("KR1098", "카카오페이손해보험", "2024.4Q", 26, "EXTRACTION_GAP", 0.0, 0.0,
    "data/disclosure/FY2024_Q4/raw/KR1098_카카오페이손해보험.pdf",
    "p.29 (240dpi 렌더, 텍스트레이어 사실상 없음)",
    "[경과조치 적용 전 지급여력비율 세부] 표, 2024년4분기 열: Ⅲ.기타 요구자본(1+2+3)=- / "
    "1.업권별...종속회사...=- / 2.비례성원칙...대응치=- / 3.업권별...관계회사...환산치=- "
    "(다.지급여력비율=409.63)",
    False,
    "이 PDF는 61페이지 전체가 사실상 스캔(fitz 텍스트 합계 190자, 페이지당 0-34자) -- 키워드검색 "
    "무의미해 240dpi로 렌더링 후 육안 확인함(p.28-33 렌더, p.29가 해당 표). item23/24/25는 이미 "
    "마스터에 0으로 로드돼 있고(다른 OCR 경로로 추정) item26만 빠짐 -- 렌더 이미지에서 3행 모두 "
    "'-'로 명확히 확인. p.30의 [경과조치 적용에 관한 사항] 표에서 지급여력비율 409.63/409.63(전후 "
    "동일) 및 '당사는...경과조치를 적용하지 않아 경과조치 전ㆍ후 금액 및 비율이 동일함' 명시 확인 "
    "-> 값_적용후=0.")

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(V, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"wrote {OUT} : {len(V)} entries")

from collections import Counter
c = Counter(v["verdict"] for v in V)
print("verdict counts:", dict(c))
companies = Counter(v["name"] for v in V)
print("per-company bucket item counts:", dict(companies))
