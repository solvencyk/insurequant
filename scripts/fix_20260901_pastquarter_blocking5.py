# -*- coding: utf-8 -*-
"""과거분기 blocking RED 5건 정정 (validation 2026-09-01 전수검증).

셀 단위만 건드린다. 통째 read-modify-write 금지 원칙에 따라 대상 (회사,분기,항목) 밖은
한 글자도 바꾸지 않고, 실행 직전에 마스터를 다시 읽는다(동시 세션 lost-update 방지).

## 1) KR0080 에이아이에이생명 2024.3Q — item13 [값] 29 -> 6327  (우리 추출 오류)
raw data/disclosure/FY2024_Q3/raw/KR0080_에이아이에이생명보험.pdf p14 를 fitz word 좌표로 판독:
    y=172/180  Ⅱ.지급여력금액으로 불인정하는 항목 ...   29 / 27 / 29
    y=208/216  Ⅲ.보완자본으로 재분류하는 항목 ...    6,327 / 6,348 / 5,518
docling MD(md_inbox/FY2024_Q3/...md L213)가 Ⅱ·Ⅲ 두 행의 **라벨을 한 셀로 병합**하고 Ⅲ의
값 3개조를 통째로 흘렸다. 그 결과 item13 에 item12 의 값(29)이 들어갔다.
대조군: 같은 회사 나머지 13개 분기는 전부 item13 == item3 이고 다리 잔차 0~+1.
정정 후 2_tier1_bridge: 35,814 − 29 − 6,327 = 29,458 vs item2 29,459 (잔차 +1, 반올림) -> YELLOW.

## 2) KR0069 삼성생명 2024.4Q — item29~35 를 출재전(A) -> 출재후(B) 로  (우리 추출 오류)
md_inbox/FY2024_Q4/KR0069_삼성생명.md L629-639 는 **재보험 위험경감** 표다:
    생명ㆍ장기손해보험위험액   출재전(A) 11,431,746   출재후(B) 11,223,289  (백만원)
마스터의 29~35 는 **A(출재전) 컬럼**을 담고 있었다. 그런데 부모 item17 = 112,233 은
**B(출재후)** 다. 같은 필링 L522-528 의 하위항목표가 B 값을 그대로 인쇄한다.
검산(룰엔진 R7 import, _diversified_sqrt):
    A -> expected 114,317.4633  vs item17 112,233  잔차 −2,084.46  (tol 1,143.17) FAIL
    B -> expected 112,232.8877  vs item17 112,233  잔차 **+0.1123**            PASS
대조군: 삼성생명 나머지 6개 짝수분기는 전부 잔차 ±0.5 이내. 2024.4Q 만 틀렸다.
※ 이 오류는 2026-07 이전부터 있었는데 **item32 가 결측이라 8_life 룰이 SKIP** 하고 있었다
   (`if all(bucket.get(i) is not None for i in range(29,36))`). 2026-09-01 커밋이 item32=0 을
   넣자 비로소 룰이 돌면서 드러났다 — SKIP-on-missing 이 두 달간 가린 진짜 오류다.

## 3) KR1010 교보라이프플래닛 2023.2Q·2023.3Q — item48/52 제거  (근거 없는 값)
## 4) KR0097 하나생명 2024.4Q          — item48/52 제거  (근거 없는 값)
세 버킷 모두 지문이 같다: **item48 == item3, item52 == item1, 값_적용후 없음.**
  · item48 은 '보완자본 한도'(= item14전 x 50%)인데 실제로는 '보완자본'(item3) 복사다.
      KR1010 2023.2Q  item14 679 x50% = 339.5   vs item48 795  (= item3)
      KR1010 2023.3Q  item14 660 x50% = 330.0   vs item48 800  (= item3)
      KR0097 2024.4Q  item14 5,321.43 x50% = 2,660.72 vs item48 3,452.36 (= item3)
    대조군: KR0097 나머지 13개 분기 전부 item48 == item14전x50% (진짜 한도).
            KR1010 은 표가 실재하는 2023.1Q 만 item48 305.43 == 611x50%.
  · 원문에 TFI 표 자체가 없다:
      KR1010 — 2026-08-22 12개 분기 전수 재조사 결론 "원문이 표를 안 그린다"
               (scripts/fix_20260822_kr1010_investigation.py). raw 재확인도 동일.
               fill_tfi_table_to_disclosure.py dry-run 도 `NO_SIGNATURE_TABLE` 로 후보를 안 낸다.
      KR0097 — 연간 전체공시라 재무제표 주석 형식이고 표준 TFI 표가 없다. 게다가
               apply_transition_vision_overrides.py L73 이 raw p48 O/X 그리드 판독으로
               **TFI = "X"**(미적용)를 등재해 뒀다 — TFI 스코프 슬롯이 있을 이유가 없다.
"틀린 값을 싣느니 빈 칸" — 0 으로도, 다른 값으로도 채우지 않고 지운다. 지우면 47/48/49 가
전부 결측이 되어 47_tier2_census 는 RED 가 아니라 SKIP 이 된다(원문 부재의 정직한 표현).

## 시뮬레이션 실측 (라이브 마스터 스냅샷 대비, --master 로 사본 게이트 실행)
    RED 44 -> 39 · blocking 7 -> 2 (남는 2건은 AIG KR0029, 다른 에이전트 담당)
    닫힘 5건 = 위 5건 전부 · **새로 생긴 RED 0건** · 범위 밖 콤보 변화 0 · 중복 콤보 0
"""
from __future__ import annotations
import argparse, collections, json, sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
TARGET = REPO / "kics_disclosure.json"

SET_VALUES: dict[tuple[str, str, int], dict[str, str]] = {
    ("KR0080", "2024.3Q", 13): {"값": "6327"},
    ("KR0069", "2024.4Q", 29): {"값": "18589.38", "값_적용후": "18589.38"},
    ("KR0069", "2024.4Q", 30): {"값": "23332.41", "값_적용후": "23332.41"},
    ("KR0069", "2024.4Q", 31): {"값": "46106.95", "값_적용후": "46106.95"},
    ("KR0069", "2024.4Q", 33): {"값": "68322.65", "값_적용후": "68322.65"},
    ("KR0069", "2024.4Q", 34): {"값": "21101.73", "값_적용후": "21101.73"},
    ("KR0069", "2024.4Q", 35): {"값": "7142.45",  "값_적용후": "7142.45"},
}
# item32 는 원문이 "-" 라 0 이 맞다(이미 0) — 건드리지 않는다.

DELETE_CELLS: set[tuple[str, str, int]] = {
    ("KR1010", "2023.2Q", 48), ("KR1010", "2023.2Q", 52),
    ("KR1010", "2023.3Q", 48), ("KR1010", "2023.3Q", 52),
    ("KR0097", "2024.4Q", 48), ("KR0097", "2024.4Q", 52),
}
# 지우기 전 반드시 만족해야 하는 지문(아니면 중단): item48==item3 이고 item52==item1.
DELETE_GUARD = {("KR1010", "2023.2Q"): ("795", "1190"),
                ("KR1010", "2023.3Q"): ("800", "1206"),
                ("KR0097", "2024.4Q"): ("3452.36301", "6978.81632")}


def key(r):
    try:
        return (r.get("원보험사코드"), r.get("공시분기"), int(r.get("항목번호")))
    except (TypeError, ValueError):
        return (r.get("원보험사코드"), r.get("공시분기"), None)


def main(argv) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="write (default: dry-run)")
    a = ap.parse_args(argv)

    rows = json.loads(TARGET.read_text(encoding="utf-8"))
    assert isinstance(rows, list), type(rows)
    before_n = len(rows)
    before_combo = collections.Counter(key(r) for r in rows)

    by = {key(r): r for r in rows}
    # --- guard: 지우려는 셀이 정말 그 지문인가 ---
    for (c, q), (v48, v52) in DELETE_GUARD.items():
        r48, r52 = by.get((c, q, 48)), by.get((c, q, 52))
        i3, i1 = by.get((c, q, 3)), by.get((c, q, 1))
        for r, want, sib, nm in ((r48, v48, i3, "item48~item3"), (r52, v52, i1, "item52~item1")):
            if r is None:
                print(f"  SKIP(이미 없음) {c} {q} {nm}")
                continue
            if str(r.get("값")) != want:
                print(f"  ABORT {c} {q} {nm}: 값이 {r.get('값')} 로 바뀌었다(기대 {want}) — 전제 변경")
                return 2
            if sib is None or str(sib.get("값")) != want:
                print(f"  ABORT {c} {q} {nm}: 형제 셀이 더는 같은 값이 아니다 — 지문 소멸")
                return 2

    changed, deleted, missing = [], [], []
    for (c, q, it), cols in SET_VALUES.items():
        r = by.get((c, q, it))
        if r is None:
            missing.append((c, q, it)); continue
        for col, new in cols.items():
            old = r.get(col)
            if old is None and col == "값_적용후":
                continue  # 없던 적용후를 새로 만들지 않는다
            if str(old) != new:
                changed.append((c, q, it, col, old, new))
                if a.apply:
                    r[col] = new

    kill = {k for k in DELETE_CELLS if k in by}
    for k in sorted(kill):
        deleted.append((k, by[k].get("값")))
    if a.apply:
        rows = [r for r in rows if key(r) not in kill]

    print(f"변경 {len(changed)} · 삭제 {len(deleted)} · 대상없음 {len(missing)}")
    for x in changed: print("   CHG", x)
    for x in deleted: print("   DEL", x)
    for x in missing: print("   !! MISSING", x)

    if not a.apply:
        print("\n(dry-run; --apply 로 기록)")
        return 0

    after_combo = collections.Counter(key(r) for r in rows)
    lost = {k: (before_combo[k], after_combo.get(k, 0)) for k in before_combo
            if after_combo.get(k, 0) != before_combo[k] and k not in kill}
    gained = {k: after_combo[k] for k in after_combo if k not in before_combo}
    dups = [k for k, v in after_combo.items() if v > 1]
    print(f"\nrows {before_n} -> {len(rows)} (기대 -{len(kill)})")
    print(f"  범위 밖 콤보 변화: {lost or '없음'}")
    print(f"  신규 콤보: {gained or '없음'}")
    print(f"  중복 콤보: {dups or '없음'}")
    if lost or gained or dups or len(rows) != before_n - len(kill):
        print("  !! 예상 밖 변화 — 기록하지 않는다"); return 2

    TARGET.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nwrote {TARGET}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
