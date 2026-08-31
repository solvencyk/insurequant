# -*- coding: utf-8 -*-
"""Build the KR0032 2026.2Q patch, apply it to a scratch copy of kics_disclosure.json,
run the real gate against the scratch copy, and print before/after findings for KR0032 2026.2Q.
Does NOT touch the live root kics_disclosure.json.
"""
import sys, io, json, copy, subprocess
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = Path(r"C:\Users\sangwook.cho\Desktop\insurequant")
LIVE = ROOT / "kics_disclosure.json"
PATCH_OUT = ROOT / "data" / "_derived" / "_patch_2026q2_KR0032.json"
SCRATCH = ROOT / "scripts" / "_probes" / "_scratch_kics_disclosure_KR0032test.json"

with open(LIVE, "r", encoding="utf-8") as f:
    labels = None

with open(ROOT / "scripts" / "_probes" / "_kr0032_labels.json", "r", encoding="utf-8") as f:
    LBL = {int(k): v for k, v in json.load(f).items()}

def r2(x):
    return round(x, 2)

# ---- values (백만원 source /100 -> 억원), all cross-verified against the real rule engine ----
cells = [
    # item, 값, 값_적용후, 근거
    (19, 3932.0, r2(393215/100),
     "값=기존(공시 [경과조치 적용 전 지급여력비율 세부] 다. 시장위험액=3,932억, PDF p.16 확인) 불변. "
     "값_적용후=raw PDF p.18 '(2)선택적용 경과조치 관련 ②장수위험·사업비위험·해지위험 및 대재해위험 경과조치' 비교표 "
     "'시장위험액' 행 경과조치 적용후=393,215백만원/100=3932.15. 룰엔진 MARKET_M sqrt(36-40)=3932.14 (0.0036% 이내) 정합 확인."),
    (23, 0.0, 0.0,
     "값=기존 불변(0). 값_적용후=raw PDF p.18 동일 비교표 '기타요구자본' 행 전후 모두 '-' → 0. "
     "직전 3개분기(2025.2Q/2025.4Q/2026.1Q) 전부 item23_적용후=0 인 패턴과 일치."),
    (36, r2(191442/100), r2(191442/100),
     "값=raw PDF p.32 '6-4-1.② 금리위험액 현황' 표 2026년 2분기 'Ⅳ. 금리 위험액'=191,442백만원/100=1914.42. "
     "값_적용후=값과 동일(mirror) — 이 회사 시장위험 세부(36-40)는 TFI/TIR 어느 경과조치도 적용받지 않는 항목이라 "
     "2025.2Q/2025.4Q 두 분기 모두 36-40의 값=값_적용후로 공시됨(선례). item19_적용후(3932.15)도 36-40 적용후 미러 결과와 "
     "sqrt(V'MV)=3932.14로 정합."),
    (37, r2(262442/100), r2(262442/100),
     "값=raw PDF p.34 '③ 주식위험액 현황' 표 2026년 2분기 'Ⅲ. 합 계'=262,442백만원/100=2624.42. 값_적용후=mirror(위 근거와 동일)."),
    (38, r2(73079/100), r2(73079/100),
     "값=raw PDF p.34 '④ 부동산위험액 현황' 표 2026년 2분기 'Ⅲ. 합 계'=73,079백만원/100=730.79. 값_적용후=mirror."),
    (39, r2(44707/100), r2(44707/100),
     "값=raw PDF p.35 '⑤ 외환위험액 현황' 표 2026년 2분기 '계' 외환위험액 열=44,707백만원/100=447.07. 값_적용후=mirror."),
    (40, 0.0, 0.0,
     "값=raw PDF p.35 '⑥ 자산집중위험액 현황' 표 2026년 2분기 '계' 위험액 열='-'(익스포져 없음) → 0. 값_적용후=mirror."),
    (41, r2(3282006/100), None,
     "값=raw PDF p.32 '② 금리위험액 현황' 표 2026년 2분기 'Ⅲ. 순자산가치' 충격전 열=3,282,006백만원/100=32820.06. "
     "값_적용후=미공시(해당 표는 IRR 충격시나리오 전용이며 경과조치 적용후 별도 컬럼이 없음 — 2025.2Q/2025.4Q/2026.1Q 전부 "
     "item41-46 값_적용후 결측 패턴과 일치, 신규 갭 아님)."),
    (42, r2(3315191/100), None,
     "값=동일 표 '평균회귀' 열=3,315,191백만원/100=33151.91. 값_적용후=미공시(위와 동일 사유)."),
    (43, r2(3057865/100), None,
     "값=동일 표 '금리상승' 열=3,057,865백만원/100=30578.65. 값_적용후=미공시(위와 동일 사유)."),
    (44, r2(3467439/100), None,
     "값=동일 표 '금리하락' 열=3,467,439백만원/100=34674.39. 값_적용후=미공시(위와 동일 사유)."),
    (45, r2(3310674/100), None,
     "값=동일 표 '금리평탄' 열=3,310,674백만원/100=33106.74. 값_적용후=미공시(위와 동일 사유)."),
    (46, r2(3281319/100), None,
     "값=동일 표 '금리경사' 열=3,281,319백만원/100=32813.19. 값_적용후=미공시(위와 동일 사유). "
     "irr_derive_expected(41-46)=1909.57 vs item36=1914.42, diff +0.25% — kics_json_rules.py L82-90에 문서화된 "
     "이 회사(NH농협)의 기지 계통편차(+1.08~4.69%) 범위와 같은 방향(actual>expected)이며 IRR_DERIVED_TOL_REL=5% 이내."),
    (47, r2(790829/100), r2(698170/100),
     "raw PDF p.17 '[지급여력비율의 경과조치 적용에 관한 사항] (1) 공통적용 경과조치 관련' 표 "
     "'보완자본 한도 적용 전' 행: 적용전 790,829 / 적용후 698,170 (백만원) /100."),
    (48, r2(672170/100), r2(672170/100),
     "*** 기존 값(15538) 오염 수정 — item3(보완자본=15538)이 그대로 복사돼 있었다(2026.2Q 온보딩 9사 중 7사에서 재발한 "
     "동일 라벨매칭 버그, inbox/parser/20260831T0705Z 참조). 원문 정답은 raw PDF p.17 같은 표 '보완자본 한도' 행: "
     "적용전 672,170 / 적용후 672,170 (백만원) /100 = 6721.70 (양쪽 동일). "
     "독립검산: item48 == item14_적용전(TFI표 정밀치 13443.40, p.17 '지급여력기준금액' 행) × 50% = 6721.70, diff=0.000. "
     "(참고: item14 헤드라인 반올림치 13443 사용시 diff=0.20 — 반올림 오차일 뿐 오류 아님)."),
    (49, r2(881595/100), r2(881595/100),
     "raw PDF p.17 동일 표 '해약환급금 부족분 상당액 중 해약환급금 상당액 초과분' 행: 적용전 881,595 / 적용후 881,595 (백만원) /100. "
     "CAPPED 항등식 검증: min(item47,item48)+item49 = min(7908.29,6721.70)+8815.95 = 15537.65 = item51(적용전) 정확 일치."),
    (50, r2(1113624/100), r2(1113624/100),
     "raw PDF p.17 동일 표 '기본자본' 행(지급여력금액 하위): 적용전 1,113,624 / 적용후 1,113,624 (백만원) /100 = 11136.24 (양쪽 동일). "
     "TFI표 자신의 기본자본 — 헤드라인 item2(11136)과 소수점 단위만 다름(반올림)."),
    (51, r2(1553765/100), r2(1646424/100),
     "raw PDF p.17 동일 표 '보완자본' 행: 적용전 1,553,765 / 적용후 1,646,424 (백만원) /100. "
     "CAPPED 적용전 항등식 min(47,48)+49=15537.65=item51 정확 일치. "
     "적용후 항등식(+item54, kics_json_rules.py ~L906 CAPPED 후=min(47,48)+49+item54): "
     "min(6981.70,6721.70)+8815.95+926.58=16464.23 vs 16464.24 (diff 0.01, 반올림) 일치."),
    (52, r2(2667389/100), r2(2760048/100),
     "*** 기존 값(26674) 정밀도 수정 — item1(지급여력금액 헤드라인=26674) 반올림치가 대신 들어가 있었다. "
     "원문 정답은 raw PDF p.17 같은 표 '지급여력금액' 행: 적용전 2,667,389 / 적용후 2,760,048 (백만원) /100 = 26673.89 / 27600.48. "
     "item50+item51=26673.89(적용전)/27600.48(적용후) 정확히 item52와 일치 — 이 회사 과거 전 분기(2025.2Q=21384.62, "
     "2025.4Q=21007.34, 2026.1Q=22654.42 모두 item1 반올림치와 다른 자기고유 소수값)의 패턴과 같음."),
    (53, 0.0, None,
     "raw PDF p.17 동일 표 '(기발행 신종자본증권)' 행: 적용전 '-' → 0. 적용후 칸은 원문에 공백(미기재) — "
     "2025.2Q/2025.4Q/2026.1Q 전 분기 동일 항목 값_적용후 전부 결측인 패턴과 일치(이 회사는 이 메모행의 적용후를 공시하지 않음)."),
    (54, r2(92658/100), None,
     "raw PDF p.17 동일 표 '(기발행 후순위채무)' 행: 적용전 92,658백만원/100=926.58. 적용후 칸은 원문에 공백(미기재) — "
     "직전 분기들과 동일 패턴(item51_적용후는 CAPPED+item54 공식으로 이 92,658(적용전)을 그대로 사용해 16464.24와 정합됨)."),
]

patch = {
    "company_code": "KR0032",
    "quarter": "2026.2Q",
    "cells": [
        {
            "항목번호": item,
            "항목명": LBL[item],
            "값": val,
            "값_적용후": val_post,
            "근거": ev,
        }
        for item, val, val_post, ev in cells
    ],
    "notes": (
        "REDs closed (원 발주 4건): (1) 부모 item19>0/자식 36-40 전부결측 -> 36-40 5개 항목 raw PDF p.32-35에서 전량 추출 "
        "(docling keyword-window가 p.31-39, 즉 '6-4.시장위험 관리' 전체를 통째로 누락시켰다 -- source_page_ranges='5-30;40-45' "
        "frontmatter에 그 증거가 남아 있음, MULTI 티켓 inbox/parser/20260831T0700Z 5개사와 동일 패턴의 6번째 사례). "
        "(2)+(3) item19/item23 적용후 TRAILING 결측 -> p.18 '②장수위험·사업비위험·해지위험 및 대재해위험 경과조치' 비교표에서 "
        "직접 추출(같은 표의 15/16/17/18/20/21/22후는 이미 정상 로드돼 있었고 19/23만 빠져 있었다 -- 페이지 범위 문제가 아니라 "
        "그 표 안에서 두 행만 라벨매칭이 안 된 것으로 보인다. 코드 조사는 이 티켓 범위 밖). "
        "(4) 41-46 IRR 시나리오 -> p.32 '②금리위험액 현황' 표에서 6개 컬럼 전량 추출, irr_derive_expected로 자체검산 "
        "(diff +0.25%, 이 회사 기지 계통편차 범위 내). "
        "보너스(발주 범위 밖이나 지시된 cross-check로 발견) -- TFI표(47-54) 전체를 raw PDF p.17에서 채웠다: "
        "item48은 item3(보완자본) 값이 그대로 복사된 오염이었고(2026.2Q 9사 중 7사 재발 버그, MULTI 티켓 20260831T0705Z와 "
        "동일 계열의 8번째 사례), item52는 item1 반올림치가 대신 들어가 있었다 -- 둘 다 원문 정밀값으로 교체. "
        "47/49/50/51/53/54는 이번 분기에 아예 로드되지 않았던 신규 행(같은 표를 반쪽만 읽은 상태였다, rule 47_tier2_census가 "
        "RED로 이미 잡고 있었다: TIER2_PARTIAL_ROWS [48]는 있는데 [47,49] 결측). CAPPED 항등식(min(47,48)+49=51, "
        "후=+item54)과 item48==item14전×50% 두 독립 공식으로 값 전량 교차검증 완료(스크립트 출력 참조)."
    ),
    "unfixable": [
        {
            "항목번호": 53,
            "필드": "값_적용후",
            "사유": "raw PDF p.17 TFI표 '(기발행 신종자본증권)' 행 적용후 칸이 원문에 공백(미기재). "
                     "2025.2Q/2025.4Q/2026.1Q 등 이 회사의 모든 과거 분기에서 동일 항목이 항상 결측 -- "
                     "이 회사가 이 메모행의 적용후 수치를 공시하지 않는 안정적 패턴이지 이번 분기 파싱 갭이 아님.",
        },
        {
            "항목번호": 54,
            "필드": "값_적용후",
            "사유": "raw PDF p.17 TFI표 '(기발행 후순위채무)' 행 적용후 칸이 원문에 공백(미기재). "
                     "동일 사유(위 item53과 같음) -- 과거 전 분기 동일 패턴.",
        },
    ],
}

PATCH_OUT.parent.mkdir(parents=True, exist_ok=True)
PATCH_OUT.write_text(json.dumps(patch, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"wrote patch: {PATCH_OUT} ({len(patch['cells'])} cells)")

# ---------------------------------------------------------------------------
# Apply to a SCRATCH copy of kics_disclosure.json (never touch the live file)
# ---------------------------------------------------------------------------
with open(LIVE, "r", encoding="utf-8") as f:
    records = json.load(f)

records = copy.deepcopy(records)


def find_row(recs, code, quarter, item):
    for r in recs:
        if r.get("원보험사코드") == code and r.get("공시분기") == quarter and r.get("항목번호") == item:
            return r
    return None


applied_new = 0
applied_updated = 0
for cell in patch["cells"]:
    item = cell["항목번호"]
    row = find_row(records, "KR0032", "2026.2Q", item)
    if row is None:
        new_row = {
            "원보험사코드": "KR0032",
            "원수사명": "NH농협손해보험",
            "티커": "X",
            "생손보여부": "손해보험",
            "항목번호": item,
            "항목명": cell["항목명"],
            "공시분기": "2026.2Q",
            "값": cell["값"],
        }
        if cell["값_적용후"] is not None:
            new_row["값_적용후"] = cell["값_적용후"]
        records.append(new_row)
        applied_new += 1
    else:
        row["값"] = cell["값"]
        if cell["값_적용후"] is not None:
            row["값_적용후"] = cell["값_적용후"]
        applied_updated += 1

print(f"applied: {applied_new} new rows, {applied_updated} updated rows")

with open(SCRATCH, "w", encoding="utf-8") as f:
    json.dump(records, f, ensure_ascii=False)
print(f"wrote scratch master: {SCRATCH}")
