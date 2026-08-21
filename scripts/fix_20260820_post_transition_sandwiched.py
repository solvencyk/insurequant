"""Inbox 20260706T0502Z iter-2 (validation): the 5 (company, quarter) pairs whose
경과조치 '적용후' 요구자본 table was SANDWICHED-missing (34 cells) plus the 4 가용자본
적용후 cells listed in the same ticket.

Every value below was read out of the raw PDF with fitz (the Docling MD had either
dropped the 경과조치 section entirely or landed its rows in the wrong column) and then
cross-checked against the K-ICS aggregation formulas before being written:

  KR0050 하나손해보험 2023.2Q  — DATA CORRUPTION, not a gap.
      raw p9/p10 (FY2023_Q2/KR0050_하나손해보험_amended.pdf): "경과조치를 적용하고 있는
      사항이 없습니다", and every 경과조치 표 (공통·(1)·(2)·(3)) carries the note "적용 전·후
      금액 및 비율이 동일함" with a blank 적용후 column.
      The stored 값_적용후 (item1=3507·3=1228·14=2160·27=162.36) is the **전분기(2023.1Q)
      column** of the 3-quarter [경과조치 적용 전 지급여력비율 세부] table — a column-picker
      shift. scripts/_probes/probe_prevq_contamination.py sweeps the whole grid for this
      signature: 하나손해 2023.2Q is the only occurrence. → mirror 전 into 후 (overwrite).

  KR0097 하나생명보험 2023.2Q  — (2)TIR + (3)TER 결합, raw p12-15.
      (2) moves only 생명장기(141,860→43,425), (3) moves only 시장(263,192→209,043); each
      table re-states the other's item unchanged, so the two are non-overlapping and
      combine. R4 recomputation of the combined vector reproduces the disclosed headline
      exactly: sqrt(V'R4V)+운영 = 360,712.71백만 vs 지급여력기준금액후 3,607억 (item14후,
      already stored). The same recomputation reproduces (2) alone (407,783) and (3) alone
      (415,049) to the 백만원, so the match is not a coincidence. R7(29-35후)=434.25 and
      MARKET_M(36-40후)=2,090.42 likewise close exactly.

  KR1011 IBK연금보험 2023.2Q  — (2)+(3) 결합, raw p12-15 (+ p10 headline 5,179억 / 176.95%).
      Same non-overlapping structure. R4 on the combined vector = 517,910.57백만 vs the
      disclosed 5,179억. 29-40후 were already loaded and reconcile (R7→557.41,
      MARKET_M→2,812.35), only 16/17/19후 were missing. This supersedes the 2026-07-12
      round-5 verdict "다중경과조치 결합공식 불명" for this cell.

  KR0049 악사손해보험 2024.3Q  — 가용자본만 채움; 요구자본 적용후는 raw 자체가 없음.
      The 2024.3Q filing has no 지급여력비율 section at all ("지급여력비율은 2024년 12월말
      공시 예정임 (보험업감독규정 부칙 제3조)", raw p3/p9/p11). The stored 2024.3Q figures
      come from the FY2024_Q4 filing's 당분기-1분기 columns, and there the 경과조치 적용에
      관한 사항 tables are **current-quarter only** (p41-43) — only [지급여력비율 총괄]
      (p36) carries 경과조치후 for prior quarters, and it carries just 비율/금액/기준금액.
      AXA applies TIR only (p39 table: TAC=X, TER=X, TIRR=X), and the 4Q filing states
      "지급여력금액 증감은 경과조치 전과 동일" → 가용자본 전=후, so item3후 = item1후 −
      item2후 = 5,554 − 3,228 = 2,326 is exact. items 15-23후 = documented exception.

  KR0100 처브라이프생명보험 2024.3Q  — (2) 단독, raw p15-16.
      The old "(2)표 값이 행별로 다른 컬럼 착지" verdict was a Docling artifact; fitz reads
      the table cleanly. R4 on (45,312·0·64,131·31,102)+5,563 = 106,993.75백만 = the
      disclosed 지급여력기준금액후 106,994. R7 on the 적용후 subs = 45,312 exactly.

  KR0071 흥국생명보험 2023.1Q  — 가용자본 적용후 2셀, raw p9 (공통TFI) + p12 (headline).
      공통 TFI reclassifies 50,000백만 of 기발행 신종자본증권 from 보완자본 to 기본자본:
      기본자본 826,183→876,183 (item2후=8,761.83, already stored) and 보완자본
      1,823,726→1,773,726 → item3후 = 17,737.26. 지급여력금액 is unchanged at 2,649,910
      → item1후 = 26,499 (p12 헤드라인 '경과조치 후 지급여력금액 26,499' 와 일치).
      R1 closes: 8,761.83 + 17,737.26 = 26,499.09.

UPSERT by default; the KR0050 row set is the only one marked overwrite (it is repairing
known-wrong values, and re-running just re-writes the same 전 value). Idempotent.
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

REPO = Path(__file__).resolve().parent.parent
TARGET = REPO / "kics_disclosure.json"

# (code, quarter) -> items whose 값_적용후 must be mirrored from 값 (raw states 전 == 후).
MIRROR = {
    ("KR0050", "2023.2Q"): (
        [1, 2, 3]                      # 공통표가 직접 공시(적용후 blank + '전·후 동일' 주석)
        + list(range(14, 29))          # 14-26 요구자본 + 27/28 비율
        + list(range(29, 36))          # 생명장기 subs (2Q = full-form)
        + list(range(36, 41))          # 시장 subs
    ),
}

# (code, quarter) -> {item: 값_적용후} in 억원, straight from the raw 경과조치 적용후 column.
EXPLICIT: dict[tuple[str, str], dict[int, float]] = {
    ("KR0097", "2023.2Q"): {
        15: 3607.13, 16: 1006.74, 17: 434.25, 18: 0.0, 19: 2090.43,
        20: 1527.02, 21: 562.17, 22: 0.0, 23: 0.0, 24: 0.0, 25: 0.0, 26: 0.0,
        29: 52.90, 30: 0.0, 31: 238.60, 33: 350.05, 34: 0.0, 35: 0.0,
        36: 467.45, 37: 1636.78, 38: 624.12, 39: 33.75, 40: 227.26,
    },
    ("KR1011", "2023.2Q"): {16: 1352.93, 17: 557.41, 19: 2812.35},
    ("KR0049", "2024.3Q"): {3: 2326.0},
    ("KR0100", "2024.3Q"): {
        16: 391.14, 18: 0.0, 19: 641.31, 21: 55.63, 22: 0.0, 23: 0.0,
        24: 0.0, 25: 0.0, 26: 0.0, 29: 161.01, 31: 364.61, 33: 0.0,
    },
    ("KR0071", "2023.1Q"): {1: 26499.0, 3: 17737.26},
    # 예별손해보험(구MG) 2023.1Q/2Q/3Q — 같은 티켓의 '적용후 하위 census 결측 3건'.
    # raw p10-12 / p12-14 / p12-14: ②(생명장기+일반손해) + ③(시장) 비중첩 결합.
    # R4(결합) vs 공통표 지급여력기준금액후: 820,515.73 vs 820,516 · 785,931.40 vs 785,937 ·
    # 767,461.88 vs 767,462. R7(29-35후)·MARKET_M(36-40후)도 세 분기 전부 정확히 닫힌다.
    # item16후 = Σ(17~21 raw 백만) − 공시 기본요구자본후 (저장된 item15후에 앵커).
    ("KR0004", "2023.1Q"): {16: 2125.17, 17: 6629.02, 18: 308.96, 19: 2237.07, 40: 0.0},
    ("KR0004", "2023.2Q"): {16: 1930.25, 17: 6448.19, 18: 329.21, 19: 2025.92},
    ("KR0004", "2023.3Q"): {16: 1774.45, 17: 6415.20, 18: 397.63, 19: 1841.32, 40: 0.0},
    # 조정항목(22 법인세조정액 · 23 기타요구자본) 적용후 단독 continuity break — 게이트 review
    # (비차단)로 오래 남아 있던 19셀. raw ②/③표를 전수 확인한 결과 아래 (회사,분기)는 두 항목이
    # 전·후 모두 "-"(=0)로 명시돼 있어 결측이 아니라 추출 누락이었다. 채우면 R5 적용후 항등식
    # (item14후 = item15후 − item22후 + item23후)이 전부 tol 안에서 닫히는 것까지 확인했다.
    #   미처리 3셀: KR0071 2024.3Q·2025.3Q item23후(기타요구자본이 ②표 625,404 / ③표 721,634로
    #   갈려 다중경과조치 결합값 불명) · KR0005 2024.4Q item23후(image-only PDF, 기존 예외).
    ("KR0003", "2024.3Q"): {23: 0.0},          # 롯데손해 raw p14/p15: 기타요구자본 - / -
    ("KR0004", "2024.1Q"): {22: 0.0, 23: 0.0},  # 예별손해 raw p11/p13/p14: 둘 다 - / -
    ("KR0005", "2023.2Q"): {23: 0.0},          # 흥국화재 raw p12/p13
    ("KR0049", "2023.2Q"): {23: 0.0},          # 악사손해 raw p13/p14
    ("KR0049", "2023.4Q"): {23: 0.0},          # 악사손해 raw p34
    ("KR0097", "2023.4Q"): {22: 0.0, 23: 0.0},  # 하나생명 raw p30/p32/p33
    ("KR0097", "2025.1Q"): {22: 0.0, 23: 0.0},  # 하나생명 raw p18/p21/p22
    ("KR0100", "2023.3Q"): {22: 0.0, 23: 0.0, 24: 0.0, 25: 0.0, 26: 0.0},  # 처브 raw p6
    ("KR0100", "2024.2Q"): {22: 0.0, 23: 0.0, 24: 0.0, 25: 0.0, 26: 0.0},  # 처브 raw p16
    ("KR0104", "2023.3Q"): {23: 0.0},          # 농협생명 raw p14/p15 (법인세후 4,602는 이미 present)
    ("KR1011", "2026.1Q"): {22: 0.0, 23: 0.0},  # IBK연금 raw p16/p19/p20
}

# (code, quarter) -> {item: (지금 저장된 값(가드), 올바른 값)}. 값이 이미 present 인데 틀린 셀.
REPAIR: dict[tuple[str, str], dict[int, tuple[str, float]]] = {
    # 예별손해 2023.1Q·3Q 시장 세부 적용후가 ②표(시장 불변) 기준으로 채워져 ③표(주식·금리
    # 경과조치)가 반영 안 됨 — item19후가 결측이라 mmult 검사가 영구 skip 되면서 숨어 있었다
    # (scripts/_probes/probe_after_subs_blindspot.py). raw ③표 적용후 컬럼으로 교체.
    ("KR0004", "2023.1Q"): {36: ("2698.84", 1619.31), 37: ("1892.03", 1135.22)},
    ("KR0004", "2023.3Q"): {36: ("1937.85", 858.32), 37: ("2168.89", 1412.08)},
}

# Rows the extractor dropped entirely because the raw cell was 0. Without item32 the
# 적용후 mmult check for parent item17 can never run (it needs all of 29-35), so filling
# 29-35후 above would silently buy a review-level skip instead of a verified R7 close.
# KR0097 2023.2Q raw p14 ②표: 장기재물·기타위험 0 (전) / 0 (후).
ADD_ROWS = [
    {
        "원보험사코드": "KR0097", "원수사명": "하나생명보험", "티커": "X",
        "생손보여부": "생명보험", "항목번호": 32, "항목명": "1-4. 장기재물·기타위험액",
        "공시분기": "2023.2Q", "값": "0", "값_적용후": "0",
    },
]

# Cells being repaired, with the wrong value we expect to find (guard against silently
# rewriting something a later round already corrected differently).
OVERWRITE_GUARD = {
    ("KR0050", "2023.2Q", 1): "3507",
    ("KR0050", "2023.2Q", 3): "1228",
    ("KR0050", "2023.2Q", 14): "2160",
    ("KR0050", "2023.2Q", 27): "162.36111111",
    ("KR0050", "2023.2Q", 28): "101.71296296",
}


def _fmt(x: float) -> str:
    if abs(x - round(x)) < 1e-6:
        return str(int(round(x)))
    return f"{x:.2f}".rstrip("0").rstrip(".")


def main() -> int:
    dry = "--dry-run" in sys.argv
    data = json.loads(TARGET.read_text(encoding="utf-8"))

    by_cq: dict[tuple[str, str], dict[int, dict]] = {}
    for r in data:
        by_cq.setdefault((r["원보험사코드"], r["공시분기"]), {})[int(r["항목번호"])] = r

    filled: list[tuple] = []
    repaired: list[tuple] = []
    skipped: list[tuple] = []

    for key, items in MIRROR.items():
        rows = by_cq.get(key, {})
        for n in items:
            row = rows.get(n)
            if row is None:
                skipped.append((*key, n, "row absent"))
                continue
            pre = row.get("값")
            if pre in (None, "", "-"):
                skipped.append((*key, n, "값 없음"))
                continue
            cur = row.get("값_적용후")
            if cur == pre:
                continue
            guard = OVERWRITE_GUARD.get((key[0], key[1], n))
            if cur not in (None, ""):
                if guard is None or cur != guard:
                    skipped.append((*key, n, f"unexpected 후={cur!r} (guard={guard!r})"))
                    continue
                repaired.append((*key, n, cur, pre))
            else:
                filled.append((*key, n, pre))
            row["값_적용후"] = pre

    for key, vals in EXPLICIT.items():
        rows = by_cq.get(key, {})
        for n, v in sorted(vals.items()):
            row = rows.get(n)
            if row is None:
                skipped.append((*key, n, "row absent"))
                continue
            cur = row.get("값_적용후")
            if cur not in (None, ""):
                skipped.append((*key, n, f"이미 present ({cur})"))
                continue
            row["값_적용후"] = _fmt(v)
            filled.append((*key, n, _fmt(v)))

    for key, vals in REPAIR.items():
        rows = by_cq.get(key, {})
        for n, (guard, v) in sorted(vals.items()):
            row = rows.get(n)
            if row is None:
                skipped.append((*key, n, "row absent"))
                continue
            cur = row.get("값_적용후")
            new = _fmt(v)
            if cur == new:
                continue
            if cur != guard:
                skipped.append((*key, n, f"unexpected 후={cur!r} (guard={guard!r})"))
                continue
            row["값_적용후"] = new
            repaired.append((*key, n, cur, new))

    added: list[tuple] = []
    for spec in ADD_ROWS:
        key = (spec["원보험사코드"], spec["공시분기"])
        n = int(spec["항목번호"])
        if n in by_cq.get(key, {}):
            skipped.append((*key, n, "row 이미 존재"))
            continue
        siblings = [i for i, r in enumerate(data)
                    if r["원보험사코드"] == key[0] and r["공시분기"] == key[1]]
        at = max(siblings) + 1 if siblings else len(data)
        for i in siblings:  # keep 항목번호 order inside the (company, quarter) block
            if int(data[i]["항목번호"]) > n:
                at = i
                break
        data.insert(at, dict(spec))
        added.append((*key, n))

    print(f"{'DRY-RUN ' if dry else ''}filled={len(filled)}  repaired={len(repaired)}  "
          f"added={len(added)}  skipped={len(skipped)}")
    for c, q, n in sorted(added):
        print(f"  ADD    {c} {q} item{n:>2} (row 신설)")
    for c, q, n, v in sorted(filled):
        print(f"  FILL   {c} {q} item{n:>2} -> {v}")
    for c, q, n, old, new in sorted(repaired):
        print(f"  REPAIR {c} {q} item{n:>2}  {old} -> {new}")
    for c, q, n, why in sorted(skipped):
        print(f"  skip   {c} {q} item{n:>2}  ({why})")

    if not dry:
        TARGET.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"wrote {TARGET}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
