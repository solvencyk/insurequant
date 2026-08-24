# -*- coding: utf-8 -*-
"""inbox 20260821T1425Z (validation, iter-5 sender 재확인 section) 후속 -- tier2 잔여
blocking RED 53건 중 parser 몫 "데이터 결함 17건" 처리.

전부 raw PDF를 word-좌표(get_text("words"))로 직접 재확인한 값이다(validation이 준
정답 후보를 그대로 베끼지 않고 재검증). 상세 재현 로그는 이 세션의 답변(inbox
`## 답변 (parser-kics, iter-8)`) 참조.

## 처리 내역

1. 신한이지(KR0051) 2023.1Q~2023.3Q -- census PARTIAL_ROWS 6건.
   raw는 word-좌표로 읽으면 라벨 행과 값 행이 y로 1.1pt 어긋나 있을 뿐 완전분리
   블록이 아니다(이전 라운드 "라벨/값 완전분리"라며 저신뢰 revert한 진단이 틀렸다
   -- 재현: dump_words3.py로 y 반올림 없이 정렬하면 라벨-값 페어가 명확).
   - 2023.1Q/2023.2Q: item47은 "보완자본 한도 적용 전" 행 자신의 값(원문 "-"=0)이
     아니라 item49(해약환급금 초과분)의 값이 잘못 들어가 있었다(예: 1Q는 5.03).
     47을 0/0으로 정정, 48/49 신규 INSERT.
   - 2023.3Q: 47은 이미 0/0으로 맞다. 48 신규 INSERT(0/0). 49는 현재 0/0인데
     원문은 145백만원(=1.45억)이 명확히 인쇄돼 있어 1.45/1.45로 정정.
   자체검산: min(47,48)+49 == item51 스코프 항등식이 3분기 전부 소수점까지 닫힌다.

2. 교보생명(KR0073) 2023.3Q·2024.1Q·2024.3Q·2025.3Q -- `50_tfi_tier_split_post` 4건.
   교보 PDF는 fitz 텍스트 스트림 순서 자체가 뒤섞이는 회사라(기존 결함A/버그4/5와
   동일 계열) word 좌표로 재구성해야 한다. **validation이 이미 정답 후보를
   줬지만 그대로 쓰지 않고 raw를 직접 열어 재확인**했고 4개 분기 전부 word-좌표
   재구성값이 정확히 일치했다(1원 단위까지). item47_후·50_후·51_후 세 항목 모두
   "적용전" 값이 그대로 미러링돼 있거나(47,50) 쓰레기값(51)이었다 -- 적용후만
   교체, 적용전/48/49는 이미 정확해 손대지 않는다.
   자체검산: 50후+51후 == 지급여력금액(TFI표 자기 항목), min(47후,48후)+49후
   == 51후. 4분기 전부 반올림 오차 1 이내로 닫힌다.

3. 미래에셋생명(KR0079) 2023.3Q -- census(+-post) 2건, TFI=O인데 표 부재로
   판정된 유일한 진짜 RED. 전 페이지가 스캔(텍스트 30~230자, 이미지 100+개/p)
   이라 fitz 텍스트로는 안 잡히는데, get_pixmap(dpi=240) 렌더링하면
   [지급여력비율의 경과조치 적용에 관한 사항] 표가 실제로 있다(p12). 47/48/49
   신규 INSERT(이 회사는 "업무보고서 보고·공시기한 연장만 적용"이라 전후 동일).

4. 하나생명(KR0097) 2024.4Q -- **false-green, 최우선.** raw가 347p 번들
   "2024년 하나생명보험회사의 현황"(보험업법 124조/보험업감독규정 7-44조 근거
   연간 종합공시, 정기경영공시 아님) 문서라 표준 TFI 표
   ("보완자본 한도 적용 전" 정확 문구 0회)가 아예 없다. 그런데 마스터엔
   item47=item48=item51=item3=3452.36 로 헤드라인 item3가 그대로 복사돼 있어
   `3_tier2_composition`이 UNCAPPED로 오판, GREEN이 됐다. item49=1776.3도 이
   문서 어디에도 근거가 없다(해약환급금 관련 언급 32회 중 어느 것도 47-51
   테이블 형태가 아님). 47/48/49/50/51 DELETE -- 결측으로 되돌린다.
   (item1/2/3/14 핵심항목은 이 문서의 다른 표 "Ⅳ.기본자본/Ⅴ.보완자본/Ⅵ.자본
   감소분경과조치"(p280)에서 이미 올바르게 파생돼 있어 손대지 않았다 -- 단
   item2_적용후=4332.17이 Ⅵ.자본감소분경과조치 80,571,963천원 전액을 기본자본
   에 귀속시킨 값인데, 원문 자체는 Ⅳ.기본자본을 pre=post로 명시해서 이 귀속이
   맞는지는 별도 확인이 필요하다 -- 이번 스코프(47-51) 밖이라 안 건드림, 보고서에만 기록)

## 안 건드린 것 (raw 대조 결과 이미 정확 또는 owner 승인 필요)

- 롯데손해(KR0003) 2026.1Q: 발행사가 2025.4Q TFI표를 재게시(비율만 갱신) --
  기확정 사실을 이번 세션도 재확인(raw p22 vs p77 word-좌표 대조). 마스터는
  원문과 이미 정확히 일치. 데이터 변경 없음, 면제 초안만 답변에 기록.
- 예별손해(KR0004) 2025.1Q: raw는 47=49=0을 명시적으로 인쇄한다(p17, "-"
  기호, 결측 아님). 헤드라인 item3(997)과 TFI표 보완자본(0)의 괴리는 두 표의
  스코프 차이(코리안리 등과 동일 패턴) -- 이미 정확, 데이터 변경 없음.

Usage:
  ...python scripts/fix_20260822_tier2_dataquality17.py --dry-run
  ...python scripts/fix_20260822_tier2_dataquality17.py
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

TARGET = REPO / "kics_disclosure.json"

ITEM_LABELS = {
    47: "보완자본 한도 적용 전",
    48: "보완자본 한도",
    49: "해약환급금 부족분 상당액 중 해약환급금 상당액 초과분",
    50: "기본자본(TFI표, 공통적용경과조치)",
    51: "보완자본(TFI표, 공통적용경과조치)",
}


def _fmt(x):
    if x is None:
        return None
    return str(int(round(x))) if abs(x - round(x)) < 1e-6 else f"{x:.2f}".rstrip("0").rstrip(".")


# (원보험사코드, 공시분기, 항목번호) -> {"값": ..., "값_적용후": ...}  (None이면 그 컬럼 미기재)
EDITS = {
    # --- 1. 신한이지(KR0051) ---
    ("KR0051", "2023.1Q", 47): {"값": 0, "값_적용후": 0},          # 정정(기존 5.03/0 -- item49값 오염)
    ("KR0051", "2023.1Q", 48): {"값": 0, "값_적용후": 0},          # 신규
    ("KR0051", "2023.1Q", 49): {"값": 5.03, "값_적용후": 5.03},    # 신규
    ("KR0051", "2023.2Q", 47): {"값": 0, "값_적용후": 0},          # 정정(기존 2.31/0)
    ("KR0051", "2023.2Q", 48): {"값": 0, "값_적용후": 0},          # 신규
    ("KR0051", "2023.2Q", 49): {"값": 2.31, "값_적용후": 2.31},    # 신규
    ("KR0051", "2023.3Q", 48): {"값": 0, "값_적용후": 0},          # 신규 (47은 이미 정확, 불변)
    ("KR0051", "2023.3Q", 49): {"값": 1.45, "값_적용후": 1.45},    # 정정(기존 0/0)

    # --- 2. 교보생명(KR0073) -- 적용후(값_적용후)만 정정, 적용전은 불변이라 미기재 ---
    ("KR0073", "2023.3Q", 47): {"값_적용후": 16534.08},
    ("KR0073", "2023.3Q", 50): {"값_적용후": 117087.85},
    ("KR0073", "2023.3Q", 51): {"값_적용후": 30826.05},
    ("KR0073", "2024.1Q", 47): {"값_적용후": 12562.41},
    ("KR0073", "2024.1Q", 50): {"값_적용후": 107699.03},
    ("KR0073", "2024.1Q", 51): {"값_적용후": 30789.57},
    ("KR0073", "2024.3Q", 47): {"값_적용후": 20275.62},
    ("KR0073", "2024.3Q", 50): {"값_적용후": 98063.85},
    ("KR0073", "2024.3Q", 51): {"값_적용후": 43247.84},
    ("KR0073", "2025.3Q", 47): {"값_적용후": 27573.27},
    ("KR0073", "2025.3Q", 50): {"값_적용후": 82822.11},
    ("KR0073", "2025.3Q", 51): {"값_적용후": 56770.12},

    # --- 3. 미래에셋생명(KR0079) 2023.3Q -- 전량 신규(스캔본 vision 판독) ---
    ("KR0079", "2023.3Q", 47): {"값": 8153.24, "값_적용후": 8153.24},
    ("KR0079", "2023.3Q", 48): {"값": 9993.36, "값_적용후": 9993.36},
    ("KR0079", "2023.3Q", 49): {"값": 3207.02, "값_적용후": 3207.02},
}

# --- 4. 하나생명(KR0097) 2024.4Q -- false-green 원인, 5개 항목 통째 DELETE ---
DELETES = {
    ("KR0097", "2024.4Q", 47),
    ("KR0097", "2024.4Q", 48),
    ("KR0097", "2024.4Q", 49),
    ("KR0097", "2024.4Q", 50),
    ("KR0097", "2024.4Q", 51),
}

# 회사 메타(신규 INSERT 행 구성용) -- 마스터에서 그대로 가져온 값
META = {
    "KR0051": {"원수사명": "신한이지손해보험", "티커": "X", "생손보여부": "손해보험"},
    "KR0073": {"원수사명": "교보생명보험", "티커": "X", "생손보여부": "생명보험"},
    "KR0079": {"원수사명": "미래에셋생명보험", "티커": "085620", "생손보여부": "생명보험"},
}


def main() -> int:
    dry = "--dry-run" in sys.argv
    data = json.loads(TARGET.read_text(encoding="utf-8"))
    print(f"로드: {len(data):,}행")

    by_key = {}
    for idx, r in enumerate(data):
        key = (r["원보험사코드"], r["공시분기"], int(r["항목번호"]))
        by_key[key] = idx

    n_edit = 0
    n_insert = 0
    new_rows = []
    edit_log = []
    insert_log = []
    missing_targets = []

    for key, changes in EDITS.items():
        co, q, item = key
        if key in by_key:
            row = data[by_key[key]]
            before = {"값": row.get("값"), "값_적용후": row.get("값_적용후")}
            for col, val in changes.items():
                row[col] = _fmt(val)
            edit_log.append((key, before, changes))
            n_edit += 1
        else:
            meta = META[co]
            row = {
                "원보험사코드": co,
                "원수사명": meta["원수사명"],
                "티커": meta["티커"],
                "생손보여부": meta["생손보여부"],
                "항목번호": item,
                "항목명": ITEM_LABELS[item],
                "공시분기": q,
            }
            if "값" in changes and changes["값"] is not None:
                row["값"] = _fmt(changes["값"])
            if "값_적용후" in changes and changes["값_적용후"] is not None:
                row["값_적용후"] = _fmt(changes["값_적용후"])
            new_rows.append(row)
            insert_log.append((key, changes))
            n_insert += 1

    # DELETE (하나생명) -- 인덱스가 밀리므로 마지막에 일괄 처리
    delete_log = []
    keep = []
    for r in data:
        key = (r["원보험사코드"], r["공시분기"], int(r["항목번호"]))
        if key in DELETES:
            delete_log.append((key, {"값": r.get("값"), "값_적용후": r.get("값_적용후")}))
            continue
        keep.append(r)
    n_delete = len(delete_log)

    print(f"\nEDIT {n_edit}건:")
    for key, before, changes in edit_log:
        print(f"  {key}  {before} -> {changes}")

    print(f"\nINSERT {n_insert}건:")
    for key, changes in insert_log:
        print(f"  {key}  {changes}")

    print(f"\nDELETE {n_delete}건 (기대 {len(DELETES)}):")
    for key, before in sorted(delete_log):
        print(f"  {key}  {before}")
    if n_delete != len(DELETES):
        print("경고: DELETE 기대 건수와 다르다 -- 중단")
        return 1

    if n_edit + n_insert != len(EDITS):
        print(f"경고: EDIT+INSERT 합계가 EDITS 딕셔너리 크기({len(EDITS)})와 다르다"
              f"(edit={n_edit} insert={n_insert}) -- 중단")
        return 1

    final = keep + new_rows
    print(f"\n요약: EDIT={n_edit}  INSERT={n_insert}  DELETE={n_delete}")
    print(f"row_count {len(data):,} -> {len(final):,}  (delta {len(final)-len(data):+d})")

    if dry:
        print("\n(dry-run; 파일 안 씀)")
        return 0

    TARGET.write_text(json.dumps(final, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nwrote {TARGET.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
