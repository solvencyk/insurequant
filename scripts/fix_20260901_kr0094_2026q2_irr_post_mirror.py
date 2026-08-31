"""KR0094 신한라이프 2026.2Q items 41-46: fill 값_적용후 = 값 (non-applier mirror).

WHY THESE 6 CELLS WERE BLANK — structural coverage gap, not a data gap.
`scripts/fix_20260716_nonapplier_requirement_mirror.py` is the canonical
non-applier mirror for the requirement side. Its tiers are:

    TIER1_ITEMS = range(15, 27)   gated on item14
    TIER2_ITEMS = range(29, 36)   gated on item17
    TIER3_ITEMS = range(36, 41)   gated on item19   <-- stops at 40

Items 41-46 (금리위험 시나리오 순자산가치) are in **no tier at all**, so that
script has never touched them. That is why KR0094 2026.2Q carries a mirrored
값_적용후 on items 36-40 but nothing on 41-46. Repo-wide census (2026-09-01,
live master): 126 (company,quarter) pairs have 41-46 in both columns, 144 have
적용전 완비 + 적용후 전무, 0 partial. Most of the 144 are FSS elective-transition
appliers where blank post is correct; the non-applier subset is the gap.

WHY THE MIRROR IS CORRECT HERE — issuer states it, we do not infer it.
Owner's standing rule (recorded in fix_20260821_kr0097_2024q2_irr_post_denull.py):
"non-applier post may mirror pre; an applier with no post disclosed must stay
blank." KR0094 is NOT in _TRANSITION_APPLIERS, and this quarter's own filing
says so three independent ways —
  · p19 [2) 지급여력비율의 경과조치 적용에 관한 세부 사항] 적용여부 O/X 표: every row X
    (공통적용 가용자본 TFI=X · 선택적용 가용자본 TAC=X · 신규도입 TIR=X · TER=X ·
    **TIRR(금리위험 증가분 점진적 인식)=X** · K-ICS비율 적기시정조치 유예=X).
  · p21 ② 선택적용 경과조치 관련 iii): "당사는 주식위험 경과조치 또는 금리위험 경과조치를
    적용하지 않아 경과조치 전·후 금액 및 비율이 동일함" — names this exact axis.
    p21 ① 공통적용 표 also prints 적용 전 == 적용 후 on every line.
  · p22 주2: "당사는 경과조치를 적용하지 않아 경과조치 전·후 금액 및 비율이 동일함".
The 41-46 source table itself (p28 "② 금리위험액 현황") has columns
충격 전 | 충격 후(평균회귀·금리상승·금리하락·금리평탄·금리경사) — a SHOCK-SCENARIO
dimension, not a 경과조치 dimension. So the after-column is not printed there for
anyone; for a non-applier the issuer's own "전·후 동일" statement supplies it.

THIS MAKES THE GATE STRICTER, NOT LOOSER. With 41-46 post blank, the gate's
적용후 IRR axis (`_transition_irr_after`) files this bucket under
POST_SCENARIO_ABSENT(짝수Q·적용전완비) and never checks it — a silent skip.
Filling the mirror puts the bucket back under inspection, where its residual is
then pinned in IRR_DERIVE_ISSUER_INCONSISTENT (owner-approved) and re-verified every
run. No RED is erased by this script; one is exposed and then pinned.

Cell-by-cell UPSERT of exactly 6 cells. Refuses to run if the count is not 6 or
if any target already carries a 값_적용후. Full-master fingerprint before/after
proves zero out-of-scope change (row count, (code,quarter,item) combo count,
and per-row field hash).
"""
from __future__ import annotations

import hashlib
import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

REPO = Path(__file__).resolve().parent.parent
JSON_PATH = REPO / "kics_disclosure.json"

TARGET_CODE = "KR0094"
TARGET_Q = "2026.2Q"
TARGET_ITEMS = set(range(41, 47))
POST = "값_적용후"


def _fingerprint(rows) -> dict:
    """(code, quarter, item) -> hash of the whole row. Detects any field edit."""
    out = {}
    for r in rows:
        key = (r.get("원보험사코드"), r.get("공시분기"), r.get("항목번호"))
        blob = json.dumps(r, ensure_ascii=False, sort_keys=True)
        out.setdefault(key, []).append(hashlib.sha256(blob.encode("utf-8")).hexdigest())
    return {k: sorted(v) for k, v in out.items()}


def main() -> None:
    dry_run = "--dry-run" in sys.argv
    rows = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    before_rows = len(rows)
    before_fp = _fingerprint(rows)
    print(f"loaded {before_rows} rows / {len(before_fp)} (code,quarter,item) combos")

    targets = [
        r for r in rows
        if r.get("원보험사코드") == TARGET_CODE
        and r.get("공시분기") == TARGET_Q
        and r.get("항목번호") in TARGET_ITEMS
    ]
    if len(targets) != 6:
        print(f"ABORT: expected exactly 6 target rows, got {len(targets)}")
        sys.exit(1)
    already = [r["항목번호"] for r in targets if r.get(POST) not in (None, "")]
    if already:
        print(f"ABORT: {POST} already present on items {already} — never overwrite a "
              "disclosed after-value")
        sys.exit(1)

    for r in sorted(targets, key=lambda x: x["항목번호"]):
        pre = r.get("값")
        if pre in (None, ""):
            print(f"ABORT: item{r['항목번호']} has no 값 to mirror")
            sys.exit(1)
        r[POST] = pre
        print(f"  item{r['항목번호']} {r['항목명']}: {POST} = {pre!r} (mirror of 값)")

    after_fp = _fingerprint(rows)
    changed = sorted(k for k in set(before_fp) | set(after_fp)
                     if before_fp.get(k) != after_fp.get(k))
    expected = sorted((TARGET_CODE, TARGET_Q, n) for n in TARGET_ITEMS)
    print(f"\nrow count: {before_rows} -> {len(rows)}")
    print(f"combo count: {len(before_fp)} -> {len(after_fp)}")
    print(f"changed combos: {len(changed)}")
    for k in changed:
        print(f"    {k}")
    if len(rows) != before_rows or len(after_fp) != len(before_fp):
        print("ABORT: row/combo count moved — out-of-scope loss")
        sys.exit(1)
    if changed != expected:
        print(f"ABORT: out-of-scope change. unexpected={sorted(set(changed) - set(expected))} "
              f"missing={sorted(set(expected) - set(changed))}")
        sys.exit(1)

    if dry_run:
        print("\nDRY-RUN: nothing written")
        return

    JSON_PATH.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nwrote {JSON_PATH.name}: {len(rows)} rows, 6 cells filled, "
          "out-of-scope change 0")


if __name__ == "__main__":
    main()
