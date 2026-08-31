import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

LABELS = {
    47: "보완자본 한도 적용 전",
    48: "보완자본 한도",
    49: "해약환급금 부족분 상당액 중 해약환급금 상당액 초과분",
    51: "보완자본(TFI표, 공통적용경과조치)",
    53: "(기발행 신종자본증권)(TFI표, 공통적용경과조치)",
    54: "(기발행 후순위채무)(TFI표, 공통적용경과조치)",
}

QUARTER = "2026.2Q"
DERIVED = Path("data/_derived")

# (code, item, 값, 값_적용후_or_None, 근거)
CELLS = [
    ("KR0001", 47, 17484.88, 62.08,
     "raw PDF data/disclosure/FY2026_Q2/pdf/KR0001_메리츠화재해상보험.pdf p.18 [지급여력비율의 경과조치 적용에 관한 사항](1)공통적용경과조치: '보완자본 한도 적용 전 1,748,488 / 6,208'(백만원)/100=17484.88/62.08. 기존 라이브값(19627.2/없음)은 2026.1Q 값의 재활용(같은 페이지의 item1/2/3 분기밀림 오염과 동일 패턴, KR0001 기존 패치 파일이 이미 확정한 사실) -- 28892.4/2=... 아님, item14(2026.1Q)x50%=57784.81x0.5=28892.405와 정확 일치해 TIER2_LIMIT_STALE 확정. correction(overwrite), not a blank-fill."),
    ("KR0001", 48, 31553.53, 31553.53,
     "raw PDF p.18 '보완자본 한도 3,155,353 / 3,155,353'(백만원, 양쪽 동일)/100=31553.53. 기존 라이브값(28892.4)은 2026.1Q의 item14x50%와 정확 일치(=stale). correction(overwrite)."),
    ("KR0001", 49, 75409.56, 75409.56,
     "raw PDF p.18 '해약환급금 부족분 상당액 중 해약환급금 상당액 초과분 7,540,956 / 7,540,956'(백만원)/100=75409.56. 신규(행 없었음)."),
    ("KR0001", 53, 1791.95, None,
     "raw PDF p.18 '(기발행 신종자본증권) 179,195'(백만원, 적용후 칸은 빈칸)/100=1791.95. 신규."),
    ("KR0001", 54, 15630.85, None,
     "raw PDF p.18 '(기발행 후순위채무) 1,563,085'(백만원, 적용후 칸은 빈칸)/100=15630.85. 신규."),

    ("KR0003", 48, None, 10555.50,
     "md_inbox/FY2026_Q2/KR0003_롯데손해보험.md L630 '보완자본 한도 1,055,550 1,055,550'(백만원, 양쪽 동일)/100=10555.50. 기존 값(적용전=28741)은 item3/item51과 다른 값이라 재검토 대상이나 이미 존재하는 값이라 안 건드림(다른 축 소관) -- 값_적용후만 신규 추가."),
    ("KR0003", 53, 453.70, None,
     "md_inbox/FY2026_Q2/KR0003_롯데손해보험.md L632 '(기발행 신〮자본증권) 45,370'(백만원, U+302E 결합문자 혼입으로 자동 라벨매처가 '신종'과 불일치해 미추출)/100=453.70. 신규."),

    ("KR0004", 47, 0.49, None,
     "raw PDF data/disclosure/FY2026_Q2/pdf/KR0004_MG_예별손해보험.pdf p.18 [지급여력비율의 경과조치 적용에 관한 사항](1)공통적용경과조치: '보완자본 한도 적용 전 49 / 49'(백만원)/100=0.49. 오늘자 TODO의 'KR0004 2026.2Q는 (1)공통적용경과조치 표 자체가 필링에 없다'는 기존 판단은 MD 기준 판단이었고, docling이 이 페이지(raw PDF p18)를 MD 변환에서 누락시킨 것으로 확인(파서 갭, 소스 부재 아님) -- raw PDF 직접 확인으로 정정. 신규."),
    ("KR0004", 49, 0, None,
     "raw PDF p.18 '해약환급금 부족분 상당액 중 해약환급금 상당액 초과분 0 / 0'(명시적 0, 대시 아님). 신규."),
    ("KR0004", 53, 0, None,
     "raw PDF p.18 '(기발행 신종자본증권) 0'(명시적 0). 신규."),
    ("KR0004", 54, 0, None,
     "raw PDF p.18 '(기발행 후순위채무) 0'(명시적 0). 신규."),

    ("KR0011", 48, None, 57549.42,
     "md_inbox/FY2026_Q2/KR0011_DB손해보험.md L376 '보완자본 한도 5,754,942 5,754,942'(백만원, 양쪽 동일)/100=57549.42. 기존 값(적용전=124792)은 item3와 동일한 오염값이라 재검토 대상이나 다른 축 소관이라 안 건드림 -- 값_적용후만 신규 추가."),
    ("KR0011", 53, 0, None,
     "md_inbox/FY2026_Q2/KR0011_DB손해보험.md L378 '(기발행 신종자본증권) -'(대시=0, 적용후 칸은 빈칸). 신규."),
    ("KR0011", 54, 0, None,
     "md_inbox/FY2026_Q2/KR0011_DB손해보험.md L379 '(기발행 후순위채무) -'(대시=0). 신규."),

    ("KR0029", 48, None, 1389.83,
     "md_inbox/FY2026_Q2/KR0029_AIG손해보험.md L520 '보완자본 한도 138,983 138,983'(백만원, 양쪽 동일)/100=1389.83. 기존 값(적용전=754)은 item3와 동일한 오염값이라 재검토 대상이나 다른 축 소관 -- 값_적용후만 신규 추가."),

    ("KR0051", 53, 0, None,
     "md_inbox/FY2026_Q2/KR0051_신한이지손해보험.md L386 '(기발행신종자본증권) -'(대시=0, 단위=억원 표기라 환산 불요). 신규."),
    ("KR0051", 54, 0, None,
     "md_inbox/FY2026_Q2/KR0051_신한이지손해보험.md L387 '(기발행후순위채무) -'(대시=0). 신규."),

    ("KR0070", 53, 0, None,
     "md_inbox/FY2026_Q2/KR0070_에이비엘생명보험.md L462 '(기발행 신종자본증권) -'(대시=0, item54=632.85는 기존 적재값과 일치 확인). 신규."),

    ("KR0072", 53, 0, None,
     "md_inbox/FY2026_Q2/KR0072_케이디비생명보험.md L335 '기발행 신종자본증권 ( ) -'(대시=0). 신규."),
    ("KR0072", 54, 0, None,
     "md_inbox/FY2026_Q2/KR0072_케이디비생명보험.md L336 '기발행 후순위채무 ( ) -'(대시=0). 신규."),

    ("KR0080", 53, 0, None,
     "md_inbox/FY2026_Q2/KR0080_에이아이에이생명보험.md L380 '( 기발행신종자본증권 ) -'(대시=0). 신규."),
    ("KR0080", 54, 0, None,
     "md_inbox/FY2026_Q2/KR0080_에이아이에이생명보험.md L381 '( 기발행후순위채무 ) -'(대시=0). 신규."),

    ("KR0082", 53, 0, None,
     "md_inbox/FY2026_Q2/KR0082_DB생명보험.md L565 '(기발행 신종자본증권) -'(대시=0, item54=3135.91은 기존 적재값과 일치 확인). 신규."),

    ("KR0083", 49, 0, 0,
     "md_inbox/FY2026_Q2/KR0083_푸본현대생명보험.md L414 '해약환급금 부족분 상당액 중 해약환급금 상당액 초과분 - -'(양쪽 모두 대시=0). 신규(양쪽 컬럼)."),

    ("KR0087", 47, 12478.17, None,
     "raw PDF data/disclosure/FY2026_Q2/pdf/KR0087_동양생명.pdf p.17(fitz 240dpi 렌더링 시각확인, MD는 이 페이지 스캔전용이라 fitz 텍스트층 0 -- 결측/OCR 재확인 필요 케이스): '보완자본 한도 적용 전 1,247,817 / 1,247,817'(백만원)/100=12478.17. 신규."),
    ("KR0087", 49, 16910.13, None,
     "raw PDF p.17(시각확인) '해약환급금 부족분 상당액 중 해약환급금 상당액 초과분 1,691,013 / 1,691,013'(양쪽 컬럼 모두 동일값 인쇄 -- docling OCR MD는 이를 적용후 칸에만 잘못 배치했었음, 원본 이미지 직접 대조로 정정). 신규."),
    ("KR0087", 53, 0, None,
     "raw PDF p.17(시각확인) '(기발행 신종자본증권) - / [대각선 취소선, 값 없음]'. 적용전=0(대시), 적용후는 취소선(TFI_MEMO_COLUMN_VARIANT 패턴과 동일, 값 없음이 원문 그대로). 신규."),
    ("KR0087", 54, 0, None,
     "raw PDF p.17(시각확인) '(기발행 후순위채무) - / [대각선 취소선]'. 적용전=0(대시). 신규."),

    ("KR0094", 47, 8907.55, None,
     "raw PDF data/disclosure/FY2026_Q2/pdf/KR0094_신한라이프생명보험.pdf p.21(docling이 이 페이지를 MD 변환에서 누락 -- fitz 직접추출로 복구, TFI=X 이지만 표는 인쇄됨) '보완자본 한도 적용 전 890,755 / 890,755'(백만원)/100=8907.55. 신규."),
    ("KR0094", 49, 50459.24, None,
     "raw PDF p.21 '해약환급금 부족분 상당액 중 해약환급금준비금 상당액 초과분 5,045,924 / 5,045,924'(백만원)/100=50459.24. 신규."),
    ("KR0094", 53, 0, None,
     "raw PDF p.21 '(기발행 신종자본증권) - / -'(양쪽 대시=0). 신규."),
    ("KR0094", 54, 0, None,
     "raw PDF p.21 '(기발행 후순위채무) - / -'(양쪽 대시=0). 신규."),

    ("KR0097", 53, 0, None,
     "md_inbox/FY2026_Q2/KR0097_하나생명보험.md L344 '기발행 신종자본증권 ( ) -'(대시=0). 신규."),
    ("KR0097", 54, 0, None,
     "md_inbox/FY2026_Q2/KR0097_하나생명보험.md L345 '기발행 후순위채무 ( ) -'(대시=0). 신규."),

    ("KR0100", 53, 0, None,
     "md_inbox/FY2026_Q2/KR0100_처브라이프생명보험.md L620 '(기발행 신종자본증권) -'(대시=0). 신규."),
    ("KR0100", 54, 0, None,
     "md_inbox/FY2026_Q2/KR0100_처브라이프생명보험.md L621 '(기발행 후순위채무) -'(대시=0). 신규."),

    ("KR1011", 47, 4346.77, None,
     "raw PDF data/disclosure/FY2026_Q2/pdf/KR1011_IBK연금보험.pdf p.18(docling이 이 페이지를 MD 변환에서 누락 -- fitz 직접추출로 복구) '보완자본 한도 적용 전 434,677 / 274,469'(백만원)/100=4346.77(적용전만 필요분). 신규."),
    ("KR1011", 48, 3610.46, None,
     "raw PDF p.18 '보완자본 한도 361,046 / 361,046'(백만원)/100=3610.46. 기존값(7168)은 item3(보완자본 헤드라인, 7168=raw p17 확인상 정확)의 복사 오염 -- correction(overwrite). 정정 후 3_tier2_composition 항등식(min(47,48)+49=min(4346.77,3610.46)+3557.89=7168.35 ~= item3=7168, diff 0.35)이 닫힘을 게이트로 확인."),
    ("KR1011", 49, 3557.89, None,
     "raw PDF p.18 '해약환급금 부족분 상당액 중 해약환급금 상당액 초과분 355,789 / 355,789'(백만원)/100=3557.89(적용전만 필요분). 신규."),
    ("KR1011", 53, 0, None,
     "raw PDF p.18 '(기발행 신종자본증권) 0'(명시적 0). 신규."),
    ("KR1011", 54, 1602.09, None,
     "raw PDF p.18 '(기발행 후순위채무) 160,209'(백만원)/100=1602.09. 신규."),

    ("KR1098", 47, 0, 0,
     "md_inbox/FY2026_Q2/KR1098_카카오페이손해보험.md L439 '보완자본 한도 적용 전 - -'(양쪽 모두 대시=0). 신규(양쪽 컬럼)."),
    ("KR1098", 49, 0, 0,
     "md_inbox/FY2026_Q2/KR1098_카카오페이손해보험.md L441 '해약환급금 부족분 상당액 중 해약환급금 상당액 초과분 - -'(양쪽 대시=0). 신규(양쪽 컬럼)."),
    ("KR1098", 51, 0, 0,
     "md_inbox/FY2026_Q2/KR1098_카카오페이손해보험.md L438 '보완자본 - -'(양쪽 대시=0, 이 행이 TFI표 자신의 item51). 신규(양쪽 컬럼)."),
    ("KR1098", 53, 0, None,
     "md_inbox/FY2026_Q2/KR1098_카카오페이손해보험.md L442 '기발행 신종자본증권 ( ) -'(대시=0). 신규."),
    ("KR1098", 54, 0, None,
     "md_inbox/FY2026_Q2/KR1098_카카오페이손해보험.md L443 '기발행 후순위채무 ( ) -'(대시=0). 신규."),
]

OVERRIDES = {("KR0001", 47), ("KR0001", 48), ("KR1011", 48)}

by_code = {}
for code, item, val, val_post, note in CELLS:
    by_code.setdefault(code, []).append((item, val, val_post, note))

written = []
for code, cells in by_code.items():
    path = DERIVED / f"_patch_2026q2_{code}.json"
    if path.exists():
        doc = json.loads(path.read_text(encoding="utf-8"))
        assert doc.get("company_code") == code
        assert doc.get("quarter") == QUARTER
    else:
        doc = {"company_code": code, "quarter": QUARTER, "cells": []}
    existing_items = {c.get("항목번호") for c in doc["cells"]}
    for item, val, val_post, note in cells:
        if item in existing_items:
            print(f"SKIP {code} item{item}: already in patch file (unexpected overlap)")
            continue
        entry = {
            "항목번호": item,
            "항목명": LABELS[item],
        }
        if val is not None:
            entry["값"] = val
        if val_post is not None:
            entry["값_적용후"] = val_post
        if (code, item) in OVERRIDES:
            entry["_override_verified"] = True
        entry["근거"] = note
        doc["cells"].append(entry)
    path.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
    written.append(str(path))

print(f"\nwrote/updated {len(written)} patch files:")
for w in written:
    print(" ", w)
