"""Round 3 of the 20260715T0801Z/20260715T0835Z thread: validation's new
`_post_transition_parent_census` continuity-break gate (inbox/parser/
20260715T0835Z) surfaced 14 (company,quarter) pairs where 값_적용후 exists
in adjacent quarters but is missing for one. Handles the "최우선"/"raw
확인 필요" tier from that ticket; the "non-display/비차단" tier (코리안리,
처브 2024.3Q, 하나손해 2023.2Q, 농협 2023.2Q-item16~21-residual, IBK
2023.2Q) is intentionally NOT touched here (see docstring notes).

- KR0069 삼성생명 2025.1Q: raw p.19 "당사는 [전부] 적용하지 않아 전후 동일함"
  x3 (zero selective-transition quarter, same pattern as round 1/2). 16-23후
  = 전 mirror.
- KR0087 동양생명 2024.2Q/2024.4Q/2025.1Q: raw confirms "공통적용 경과조치만
  적용" (all 3 selective = X) for every quarter checked. 15/16-23후 = 전
  mirror (2025.1Q's item15 was the only one the gate flagged, but the whole
  row was missing so all of 15-23 filled).
- KR0097 하나생명 2024.4Q: raw is a "지급여력 및 건전성감독기준 재무상태표"
  audit-attachment style page (data/disclosure/FY2024_Q4/raw/
  KR0097_하나생명보험.pdf p.281, 단위 천원) -- NOT the usual 정기경영공시
  prose format. item14/15후 already correctly in JSON from that same page
  (4305.31, matches this session's independent re-derivation exactly).
  item17후 already present too (1757.32) but does NOT match this page's
  value (2001.90) or reconcile with it -- provenance unclear, an earlier
  session likely sourced it from item 29-35 sub-risk partial fills instead
  (33/34 present, 30/35 still None there). Left UNTOUCHED here rather than
  guessed at; only 18/19/20/21/22/23 filled (unambiguous on this page:
  18/20/21/22/23 identical across 전/후, 19 is a real raw-sourced change).
  item16 also left unfilled since it depends on the disputed item17.
- KR0071 흥국생명 2024.4Q: **image-only PDF** (0-111p scanned, no text
  layer -- see 2026-07-07(8차) changelog). Read via vision (rendered pages
  44/47-51 to PNG, scripts/_probes/render_hkl_pages.py). Applies TIR+TER
  (life+market). item17(from p.50 ②표, market confirmed unchanged there)
  and item19(from p.51 ③표, life confirmed unchanged there) are safely
  disjoint-derivable, as are 18/20/21 (both tables agree unchanged). BUT
  item22/23 genuinely differ between the two tables (348,792/599,206 vs
  429,635/703,625 백만원) -- this company's TIR/TER both perturb the
  법인세조정/기타요구자본 lines, so they don't decompose cleanly. R4-
  computing item15 from the disjoint 17/18/19/20/21 gives 14747.27, which
  does NOT reconcile with the already-trusted headline item14=16987 (p.44
  [지급여력비율총괄], real 감사보고서-adjacent combined figure, off by
  ~2240 either way -- see scripts/_probes/verify_r4_hkl_2024q4.py) --
  genuine multi-transition combination gap, not a derivation I can trust.
  Only 17/18/19/20/21 filled; 15/16/22/23 deliberately left for owner/
  validation (`_POST_PARENT_NOT_DISCLOSED`-style residual).

UPSERT-only. Idempotent.
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

REPO = Path(__file__).resolve().parent.parent
TARGET_FILES = [REPO / "kics_disclosure.json", REPO / "templates" / "kics_disclosure.json"]


def _fmt(x: float) -> str:
    if abs(x - round(x)) < 1e-6:
        return str(int(round(x)))
    return f"{x:.2f}".rstrip("0").rstrip(".")


UPSERTS: dict[tuple[str, str, int], float] = {}

# KR0069 삼성생명 2025.1Q -- zero selective-transition, mirror 전
_ss_mirror = {16: 89321, 17: 111782, 18: 0, 19: 225562, 20: 44185, 21: 9966, 22: 72922, 23: 25834}
for n, v in _ss_mirror.items():
    UPSERTS[("KR0069", "2025.1Q", n)] = float(v)

# KR0087 동양생명 -- zero selective-transition every quarter checked, mirror 전
_dy_mirror = {
    "2024.2Q": {16: 9981, 17: 18090, 18: 0, 19: 13248, 20: 6155, 21: 1612, 22: 5474, 23: 0},
    "2024.4Q": {16: 10147, 17: 18631, 18: 0, 19: 12813, 20: 6590, 21: 1512, 22: 4480, 23: 0},
    "2025.1Q": {15: 29619, 16: 9933, 17: 19559, 18: 0, 19: 12197, 20: 6278, 21: 1516, 22: 2990, 23: 0},
}
for q, items in _dy_mirror.items():
    for n, v in items.items():
        UPSERTS[("KR0087", q, n)] = float(v)

# KR0097 하나생명 2024.4Q -- audit-report page281 (단위 천원 -> /100000 억원),
# 18/20/21/22/23 unambiguous; 16/17 skipped (see docstring)
UPSERTS[("KR0097", "2024.4Q", 18)] = 0.0
UPSERTS[("KR0097", "2024.4Q", 19)] = 200_345_315 / 100_000
UPSERTS[("KR0097", "2024.4Q", 20)] = 154_877_709 / 100_000
UPSERTS[("KR0097", "2024.4Q", 21)] = 36_485_031 / 100_000
UPSERTS[("KR0097", "2024.4Q", 22)] = 0.0
UPSERTS[("KR0097", "2024.4Q", 23)] = 0.0

# KR0071 흥국생명 2024.4Q -- vision-read scanned pages 50(②)/51(③), 단위 백만원.
# item17 from (2)표(market confirmed unchanged there), item19 from (3)표(life
# confirmed unchanged there), 18/20/21 agree across both tables.
UPSERTS[("KR0071", "2024.4Q", 17)] = 922_222 / 100
UPSERTS[("KR0071", "2024.4Q", 18)] = 0.0
UPSERTS[("KR0071", "2024.4Q", 19)] = 591_521 / 100
UPSERTS[("KR0071", "2024.4Q", 20)] = 405_758 / 100
UPSERTS[("KR0071", "2024.4Q", 21)] = 80_133 / 100


def main():
    dry_run = "--dry-run" in sys.argv
    data = json.loads(TARGET_FILES[0].read_text(encoding="utf-8"))
    index: dict[tuple[str, str, int], dict] = {}
    for r in data:
        index[(r["원보험사코드"], r["공시분기"], r["항목번호"])] = r

    written = []
    for (code, q, item_no), value in UPSERTS.items():
        row = index.get((code, q, item_no))
        if row is None:
            print(f"WARN: no row for {code} {q} item{item_no}, skip")
            continue
        if row.get("값_적용후") not in (None, ""):
            continue
        row["값_적용후"] = _fmt(value)
        written.append((code, q, item_no, _fmt(value)))

    print(f"{'DRY-RUN: ' if dry_run else ''}{len(written)} cells touched:")
    for code, q, item_no, value in written:
        print(f"  {code} {q} item{item_no}: {value}")

    if dry_run:
        return

    for path in TARGET_FILES:
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"wrote {path.relative_to(REPO)}")


if __name__ == "__main__":
    main()
