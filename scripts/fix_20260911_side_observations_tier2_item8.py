# -*- coding: utf-8 -*-
"""티켓 `inbox/parser/20260901T0420Z__validation__MULTI__scanned_section_needs_ocr_not_refetch.md`
"부수 관찰" 3건 중 2건 처리 (2026-09-11) -- 전부 raw PDF fitz 190dpi 렌더 직접 판독으로 재확인
(스캔 구간이라 텍스트 추출 불가, `scripts/_probes/probe_20260911_side_obs_render.py` 로 렌더).

## (2) KR0010 2025.4Q item8(자본조정): 원문 "0" vs 마스터 "" -- 0-vs-결측 표기 통일
raw p68([경과조치 적용 전 지급여력비율 세부], 당분기=25.4Q 열) "4. 자본조정 | 0 | 0 | 0"
(25.4Q/25.3Q/25.2Q 세 분기 다 0) -- 이웃 항목(7=이익잉여금, 9=기타포괄손익누계액)이 이미
값=값_적용후 로 미러링돼 있는 것과 동일 패턴(이 회사는 자본감소분(TAC) 미적용, p68 표 자체가
경과조치 적용전 전용이라 적용후는 항상 적용전과 동일). 값/값_적용후 둘 다 "0" 으로 정정.

## (3) item53/54(TFI 메모행) 마스터 부재 2건 x 2사 = 4셀 신규 UPSERT
- KR0071 2024.4Q raw p49(0-idx 48, 1)공통적용경과조치 TFI표): "(기발행 신종자본증권) 49,650"
  · "(기발행 후순위채무) 123,407" -> 496.50 / 1,234.07 억(적용후 컬럼은 해당 표에서 빗금 처리
  -- 47/48/49/50/51/52 와 동일 관례로 값_적용후 미기재).
- KR0010 2025.4Q raw p69(0-idx, 1)공통적용경과조치 TFI표): "(기발행 신종자본증권) -"
  · "(기발행 후순위채무) 672,249" -> 0.00(대시=0, 이 저장소 관례) / 6,722.49 억(적용후 빗금).
  같은 표의 47/48/49 (14138.32/7415.83, 31823.16/31823.16, 57670.39/57670.39) 가 이미
  마스터와 소수점까지 일치 -- 판독 방법론 자체의 교차검증.

둘 다 스캔 구간(kics_source_textlayer.json 상 SCANNED_SECTION 6칸에 포함)이라 fitz get_text()
는 0자를 반환한다(확인됨) -- 렌더링 후 Claude 육안판독만이 유일한 경로, 이 스크립트는 그
판독 결과를 셀 단위로 적재만 한다.

## 실행
    C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/fix_20260911_side_observations_tier2_item8.py [--apply]
"""
from __future__ import annotations

import json
import shutil
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.stdout.reconfigure(encoding="utf-8")
MASTER = ROOT / "kics_disclosure.json"

ITEM_LABELS = {
    53: "(기발행 신종자본증권)(TFI표, 공통적용경과조치)",
    54: "(기발행 후순위채무)(TFI표, 공통적용경과조치)",
}

NEW_ROWS = [
    # code, quarter, item, value(억원)
    ("KR0071", "2024.4Q", 53, "496.5"),
    ("KR0071", "2024.4Q", 54, "1234.07"),
    ("KR0010", "2025.4Q", 53, "0"),
    ("KR0010", "2025.4Q", 54, "6722.49"),
]

ITEM8_FIX = ("KR0010", "2025.4Q", 8)  # 값/값_적용후 "" -> "0"


def census(rows):
    combos = {(r["원보험사코드"], r["공시분기"], str(r["항목번호"])) for r in rows}
    filled = sum(1 for r in rows for f in ("값", "값_적용후") if r.get(f) not in (None, ""))
    return len(rows), len(combos), filled


def main() -> int:
    apply = "--apply" in sys.argv
    rows = json.loads(MASTER.read_text(encoding="utf-8"))
    b = census(rows)
    print(f"before: rows={b[0]} combos={b[1]} filled(non-empty)={b[2]}")

    idx = {(r["원보험사코드"], r["공시분기"], str(r["항목번호"])): r for r in rows}
    meta_by_code: dict[str, tuple] = {}
    for r in rows:
        meta_by_code.setdefault(r["원보험사코드"], (r["원수사명"], r.get("티커"), r["생손보여부"]))

    # --- item8 fix ---
    code, q, item = ITEM8_FIX
    r8 = idx.get((code, q, str(item)))
    if r8 is None:
        print(f"ABORT: {code} {q} item{item} 행이 없다"); return 2
    if r8.get("값") not in ("", None) or r8.get("값_적용후") not in ("", None):
        print(f"ABORT: {code} {q} item{item} 이 이미 빈칸이 아니다 (값={r8.get('값')!r} "
              f"값_적용후={r8.get('값_적용후')!r}) -- 다른 세션이 손댔을 수 있다, 정지")
        return 2
    print(f"FIX  {code} {q} item{item}({r8['항목명']}): 값/값_적용후 '' -> '0'")

    # --- item53/54 new rows ---
    to_insert = []
    for code, q, item, val in NEW_ROWS:
        key = (code, q, str(item))
        if key in idx:
            print(f"ABORT: {code} {q} item{item} 이 이미 마스터에 있다 -- 다른 세션이 이미 채웠을 수 있다, 정지")
            return 2
        if code not in meta_by_code:
            print(f"ABORT: {code} 의 메타(원수사명/티커/생손보여부)를 마스터에서 못 찾음"); return 2
        nm, tk, seg = meta_by_code[code]
        to_insert.append({
            "원보험사코드": code, "원수사명": nm, "티커": tk, "생손보여부": seg,
            "항목번호": item, "항목명": ITEM_LABELS[item], "공시분기": q, "값": val,
        })
        print(f"NEW  {code} {q} item{item}({ITEM_LABELS[item]}): 값={val}")

    if not apply:
        print("\n(dry-run) 반영하려면 --apply")
        return 0

    bak = MASTER.with_suffix(f".json.bak_{datetime.now():%Y%m%d_%H%M%S}_sideobs")
    shutil.copy2(MASTER, bak)

    r8["값"] = "0"
    r8["값_적용후"] = "0"

    for code, q, item, val in NEW_ROWS:
        anchor = idx.get((code, q, "49"))  # insert right after item49 if present
        pos = rows.index(anchor) + 1 if anchor is not None else len(rows)
        row = next(nr for nr in to_insert if nr["원보험사코드"] == code
                   and nr["공시분기"] == q and nr["항목번호"] == item)
        rows.insert(pos, row)
        idx[(code, q, str(item))] = row

    MASTER.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    a = census(rows)
    print(f"\nafter : rows={a[0]} combos={a[1]} filled(non-empty)={a[2]}  "
          f"(+{a[0]-b[0]}행 기대 +{len(NEW_ROWS)})")
    print(f"저장 완료. 백업: {bak.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
