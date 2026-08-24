# -*- coding: utf-8 -*-
"""parser-kics 발주(2026-08-25) -- item52(TFI표 자신의 지급여력금액 행) 잔여 30버킷 갭 중
텍스트로 직접 읽히는 12버킷을 INSERT한다 (나머지 18버킷은 NO_MATCHED_PAGE -- 별도 vision 세션).

## 근거 문서
artifacts/validation/reaudit_20260824_KR0003_KR0004.md F1 -- item50/51은 있는데 item52만
없는 버킷이 전사 30개. 이 스크립트는 그중 raw가 텍스트로 직접 읽히는 12개를 처리한다
(fix_20260824_tfi_capital_memo_rows.py --dry-run 재실행 확인: 나머지 18개는 페이지 자체가
NO_MATCHED_PAGE -- 폰트매핑/스캔 의심이라 vision 이 필요해 이 스크립트 범위 밖).

## 왜 원 스크립트(fix_20260824_tfi_capital_memo_rows.py)가 이 12개를 놓쳤나 -- 근본원인 3종

read-only 진단(scripts/_probes/probe_20260825_item52_rowdump.py,
probe_20260825_item52_more.py, probe_20260825_kr0004_rest.py)으로 전부 재현:

1. 세모(음수) 값이 라벨에 섞여 들어간다 (KR0004 4분기 전부). _label_norm()이 쓰는
   T2.NUMRE(정규식 ^\\(?-?[\\d,]+(\\.\\d+)?\\)?%?$)는 세모165,099 같은 토큰을 숫자로 인식하지
   못해 라벨 텍스트로 흡수한다 -- "지급여력금액" 단독매칭이 "지급여력금액세모165,099세모165,099"가
   되어 실패한다. (원 스크립트의 _num()은 세모를 처리하지만 NUMRE는 안 한다 -- 게이트 함수와
   토큰분류 함수가 다른 정규식을 쓰는 불일치.)
2. 동일 라벨 토큰이 좌표만 미세하게(약 0.2pt) 어긋난 채 중복 렌더링된다 (KR0068 3분기 전부,
   기존 dedup 주석이 "동일좌표 완전중복"만 잡는다고 명시함 -- 이 필링은 그보다 미세하게
   어긋나 dedup을 통과, "지급여력금액"이 4번 이어붙는다).
3. 라벨행과 값행이 ROW_TOL(3.0pt)보다 살짝 더 벌어져 별도 클러스터로 쪼개진다
   (KR0009 2025.1Q: 라벨 y=196.3, 값 y=192.5, 갭 3.8pt). KR0087 3분기는 다른 변형 --
   라벨+값 행 자체는 멀쩡한데 그 페이지엔 idx48(보완자본한도)이 없고(다음 페이지로 표가
   이어짐), 원 스크립트가 "첫 매치 페이지에서 무엇이든 하나라도 찾으면 그 페이지에서
   멈추는" 구조라 item53/54만 있는(item52는 없는) 다음 페이지에서 멈춰버린다. KR0100
   2023.1Q는 그 페이지 자체가 좌우 2단 레이아웃(별개 표 2개가 y좌표만으로 한 행에
   섞임)이라 라벨/값이 또 분리되는데, 다행히 같은 정보가 바로 다음 캔디데이트 페이지에
   깨끗하게(라벨+값 한 행) 다시 인쇄되어 있다.

## 왜 재-일반화(원 스크립트 패치)가 아니라 하드코딩 INSERT인가

12버킷 전부 fitz 좌표로 원문 직접 재확인 + item50+item51(이미 적재·검증된 마스터 값)과
교차검산까지 마쳤다(아래 CROSSCHECK 딕셔너리 각 라인이 그 결과). 일반화된 재추출 로직을
새로 짜면 이미 로드된 428버킷을 건드릴 위험(같은 이름의 shared 함수를 고치면 재실행 시
회귀 여지)이 생긴다 -- 이 스크립트는 원 스크립트를 import조차 하지 않고 정독한 값만
cell 단위로 INSERT한다(idempotent, 이미 있으면 skip).

## 교차검산 (item50 + item51 == 직접 읽은 raw52/100, 전부 차이 0.01억 이내)

  KR0004 2025.1Q: -1650.99+0.00=-1650.99 vs -1650.99 (diff 0.00)
  KR0004 2025.2Q: -2775.57+803.90=-1971.67 vs -1971.66 (diff 0.01, 반올림)
  KR0004 2025.4Q: -715.47+1.84=-713.63 vs -713.63 (diff 0.00)
  KR0004 2026.1Q: -1091.76+1.62=-1090.14 vs -1090.14 (diff 0.00)
  KR0068 2023.4Q(적용후): 115853.43+93939.23=209792.66 vs 209792.66 (diff 0.00)
  KR0068 2024.2Q: 100426.25+97968.65=198394.90 vs 198394.90 (diff 0.00)
  KR0068 2024.3Q: 99229.30+105880.73=205110.03 vs 205110.03 (diff 0.00)
  KR0087 2023.2Q(적용후): 28963.31+15548.84=44512.15 vs 44512.15 (diff 0.00)
  KR0087 2025.1Q(적용후): 15294.11+18567.46=33861.57 vs 33861.57 (diff 0.00, item1_적용후도 33861.57로 일치)
  KR0087 2025.4Q: 13700.70+26894.26=40594.96 vs 40594.96 (diff 0.00)
  KR0100 2023.1Q: 2216.60+704.65=2921.25 vs 2921.25 (diff 0.00)
  KR0009 2025.1Q: 38394.77+92631.42=131026.19 vs 131026.19 (diff 0.00)

전부 item50/item51 둘 다 이미 있는(=이미 검증된) 버킷만 대상이라 이 교차검산 자체가
비순환은 아니지만(같은 표에서 온 값), item52는 로더가 스케일/배율 선택에 쓰지 않는
독립 행이라 50_tfi_tier_split의 comparand로는 여전히 유효하다(validation 설계 의도).

Usage:
  ...python scripts/fix_20260825_item52_gap_group2_textread.py --dry-run
  ...python scripts/fix_20260825_item52_gap_group2_textread.py
"""
from __future__ import annotations

import json
import sys
import os
from pathlib import Path

sys.stdout = os.fdopen(1, "w", encoding="utf-8", closefd=False)

REPO = Path(__file__).resolve().parents[1]
TARGET = REPO / "kics_disclosure.json"

LABEL52 = "지급여력금액(TFI표, 공통적용경과조치)"


def _fmt(x: float) -> str:
    return str(int(round(x))) if abs(x - round(x)) < 1e-6 else f"{x:.2f}".rstrip("0").rstrip(".")


# (code, quarter, raw_pre_백만원, raw_post_백만원) -- fitz 좌표로 직접 재확인한 원문 그대로,
# 스케일은 /100(백만원->억원, 마스터 관례 -- item50/51과 동일 스케일로 교차검산 완료)
RAW = [
    ("KR0004", "2025.1Q", -165099, -165099),
    ("KR0004", "2025.2Q", -197166, -197166),
    ("KR0004", "2025.4Q", -71363, -71363),
    ("KR0004", "2026.1Q", -109014, -109014),
    ("KR0068", "2023.4Q", 20979266, 20979266),
    ("KR0068", "2024.2Q", 19839490, 19839490),
    ("KR0068", "2024.3Q", 20511003, 20511003),
    ("KR0087", "2023.2Q", 4451215, 4451215),
    ("KR0087", "2025.1Q", 3386157, 3386157),
    ("KR0087", "2025.4Q", 4059496, 4059496),
    ("KR0100", "2023.1Q", 292125, 292125),
    ("KR0009", "2025.1Q", 13102619, 13102619),
]


def find_row(data, code, q, item_no):
    hits = [r for r in data if r.get("원보험사코드") == code and r.get("공시분기") == q
            and int(r.get("항목번호", -1)) == item_no]
    if len(hits) > 1:
        raise SystemExit(f"FATAL: 중복행 {code} {q} item{item_no}: {len(hits)}건")
    return hits[0] if hits else None


def find_company_meta(data, code):
    for r in data:
        if r.get("원보험사코드") == code:
            return {"원수사명": r.get("원수사명"), "티커": r.get("티커"),
                    "생손보여부": r.get("생손보여부")}
    raise SystemExit(f"FATAL: {code} 메타를 찾을 수 없음")


def _num(r, field):
    v = r.get(field) if r else None
    if v is None or v == "":
        return None
    return float(v)


def main() -> int:
    dry = "--dry-run" in sys.argv
    data = json.loads(TARGET.read_text(encoding="utf-8"))
    n0 = len(data)
    print(f"로드 전 row_count = {n0:,}")

    log = []
    warn = []

    for code, q, raw_pre, raw_post in RAW:
        # 1. idempotent: 이미 있으면 skip
        existing = find_row(data, code, q, 52)
        if existing is not None:
            log.append(("SKIP(이미존재)", code, q, existing))
            continue

        # 2. 50/51 present guard -- 이 스크립트의 스코프 전제(CAT A: 50&51 있고 52만 없음)
        r50 = find_row(data, code, q, 50)
        r51 = find_row(data, code, q, 51)
        if r50 is None or r51 is None:
            raise SystemExit(f"FATAL: {code} {q} item50/51 이 없음 -- 이 스크립트 스코프 밖")

        pre = round(raw_pre / 100.0, 2)
        post = round(raw_post / 100.0, 2)

        # 3. 교차검산: item50+item51 (같은 컬럼) vs 이번에 적재하려는 값, 차이 0.05 이내
        sum_pre = None
        sum_post = None
        p50, p51 = _num(r50, "값"), _num(r51, "값")
        if p50 is not None and p51 is not None:
            sum_pre = p50 + p51
        p50p, p51p = _num(r50, "값_적용후"), _num(r51, "값_적용후")
        if p50p is not None and p51p is not None:
            sum_post = p50p + p51p

        if sum_pre is not None and abs(sum_pre - pre) > 0.05:
            warn.append(f"{code} {q}: PRE 교차검산 어긋남 item50+51={sum_pre:.2f} vs 신규 item52={pre:.2f}")
        if sum_post is not None and abs(sum_post - post) > 0.05:
            warn.append(f"{code} {q}: POST 교차검산 어긋남 item50+51={sum_post:.2f} vs 신규 item52={post:.2f}")

        meta = find_company_meta(data, code)
        row = {
            "원보험사코드": code, "원수사명": meta["원수사명"],
            "티커": meta["티커"], "생손보여부": meta["생손보여부"],
            "항목번호": 52, "항목명": LABEL52, "공시분기": q,
            "값": _fmt(pre), "값_적용후": _fmt(post),
        }
        data.append(row)
        log.append(("INSERT", code, q, row))

    print(f"\n=== 변경 로그 ({len(log)}건) ===")
    for entry in log:
        op = entry[0]
        if op == "INSERT":
            _, code, q, row = entry
            print(f"  INSERT  {code} {q} item52 값={row['값']} 값_적용후={row['값_적용후']}")
        else:
            _, code, q, existing = entry
            print(f"  {op}  {code} {q} item52 (현재 값={existing.get('값')} 값_적용후={existing.get('값_적용후')})")

    if warn:
        print(f"\n=== 교차검산 경고 ({len(warn)}건) ===")
        for w in warn:
            print(f"  !! {w}")

    n_insert = sum(1 for e in log if e[0] == "INSERT")
    n_skip = sum(1 for e in log if e[0].startswith("SKIP"))
    print(f"\nINSERT={n_insert} SKIP={n_skip}")

    if warn:
        print("\n교차검산 경고가 있어 안전을 위해 파일을 쓰지 않는다 -- 원인 규명 후 재실행할 것.")
        return 1

    if dry:
        print("\n(dry-run; 파일 안 씀)")
        return 0
    if n_insert == 0:
        print("쓸 셀 없음")
        return 0

    TARGET.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n{n_insert}행 INSERT, wrote {TARGET.name} (row_count {n0:,} -> {len(data):,})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
