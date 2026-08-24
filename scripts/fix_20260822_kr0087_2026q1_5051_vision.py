# -*- coding: utf-8 -*-
"""KR0087(동양생명) 2026.1Q item50/51 -- vision 판독 신규 적재.

완전 스캔본(fitz 텍스트 2~4자/p, `probe_20260822_tier2_backlog_lists.py` 의
TFI_TIER_ROWS_ABSENT_BACKLOG 목록에 있던 마지막 1버킷). `get_pixmap(dpi=220)` 로 raw
0-idx p16(=인쇄쪽수17) 렌더링, `[지급여력비율의 경과조치 적용에 관한 사항] 1) 공통적용
경과조치 관련` 표(단위 백만원, 전=후 전부 동일 인쇄) 육안 판독:

  지급여력금액 4,345,726 / 4,345,726
  기본자본     1,592,006 / 1,592,006   <- item50
  보완자본     2,753,720 / 2,753,720   <- item51
  보완자본 한도 적용 전 1,240,578 / 1,240,578  (기존 item47=12405.78 와 정확히 일치 재확인)
  보완자본 한도         1,146,316 / 1,146,316  (기존 item48=11463.16 와 일치 재확인)
  해약환급금 부족분 상당액 중 초과분 1,607,404 / 1,607,404  (기존 item49=16074.04 와 일치)
  지급여력기준금액 2,292,632 / 2,292,632

자체검산: item50(15920.06)+item51(27537.20)=43457.26 ≈ 마스터 item1(43457) diff 0.26 정확.
item2(마스터 기존, 헤드라인)=15920 · item3=27537 과도 정확히 일치(diff<0.3) -- 이 회사는
선택경과조치를 전부 미신청(같은 페이지 "당사는 ~ 적용하지 않아 ~ 동일함" 각주 3개)이라
헤드라인표와 TFI표가 같은 스코프라 정합이 당연하다.

Usage:
  ...python scripts/fix_20260822_kr0087_2026q1_5051_vision.py --dry-run
  ...python scripts/fix_20260822_kr0087_2026q1_5051_vision.py
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

TARGET = REPO / "kics_disclosure.json"

VALUES = {
    50: {"label": "기본자본(TFI표, 공통적용경과조치)", "pre_raw": 1592006.0, "post_raw": 1592006.0},
    51: {"label": "보완자본(TFI표, 공통적용경과조치)", "pre_raw": 2753720.0, "post_raw": 2753720.0},
}


def _fmt(x: float) -> str:
    return str(int(round(x))) if abs(x - round(x)) < 1e-6 else f"{x:.2f}".rstrip("0").rstrip(".")


def main() -> int:
    dry = "--dry-run" in sys.argv
    data = json.loads(TARGET.read_text(encoding="utf-8"))
    print(f"로드 전 row_count = {len(data):,}")

    meta = next((r for r in data if r["원보험사코드"] == "KR0087"), None)
    if meta is None:
        print("[WARN] KR0087 행 자체가 마스터에 없음 -- 중단")
        return 1
    existing = {(r["원보험사코드"], r["공시분기"], int(r["항목번호"])) for r in data}

    new_rows = []
    for item, v in VALUES.items():
        if ("KR0087", "2026.1Q", item) in existing:
            print(f"  [SKIP] KR0087 2026.1Q item{item} 이미 존재 -- 덮어쓰지 않음")
            continue
        pre = round(v["pre_raw"] / 100.0, 2)
        post = round(v["post_raw"] / 100.0, 2)
        row = {
            "원보험사코드": "KR0087", "원수사명": meta.get("원수사명"),
            "티커": meta.get("티커"), "생손보여부": meta.get("생손보여부"),
            "항목번호": item, "항목명": v["label"], "공시분기": "2026.1Q",
            "값": _fmt(pre), "값_적용후": _fmt(post),
        }
        new_rows.append(row)
        print(f"  INSERT KR0087 2026.1Q item{item}({v['label']}) 값={row['값']} "
              f"값_적용후={row['값_적용후']}")

    print(f"\n합계: INSERT {len(new_rows)}건")
    if dry:
        print("(dry-run; 파일 안 씀)")
        return 0
    if not new_rows:
        print("쓸 변경 없음")
        return 0

    data.extend(new_rows)
    TARGET.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {TARGET.name} (row_count {len(data)-len(new_rows):,} -> {len(data):,})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
