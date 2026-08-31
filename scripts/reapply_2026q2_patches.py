#!/usr/bin/env python3
"""Re-apply every 2026.2Q patch and assert zero drift. Run after EVERY fill-chain run.

Why this must be a step, not a habit: `fill_post_transition_to_disclosure.py` re-derives
값_적용후 from the MD each time it runs. For a company whose MD came from OCR, that
re-derivation puts the OCR's misread digits back. Observed twice on 미래에셋(KR0079)
2026.2Q, where EasyOCR reads '1' as '7':

    item1 값_적용후  37207 -> 97207.33
    item3 값_적용후  13473 -> 73472.53

Both times the gate caught it (`R7_지급여력비율 공시후=155.28 계산후=405.67`), but the gate
is the last line of defence, not the first. Applying every patch again after a fill is
cheap and idempotent, so do it unconditionally.

Exits non-zero if any patch cell still disagrees with the master afterwards.
"""

from __future__ import annotations

import glob
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PY = sys.executable
APPLY = ROOT / "scripts" / "apply_2026q2_patches.py"
MASTER = ROOT / "kics_disclosure.json"


def patches() -> list[str]:
    return sorted(glob.glob(str(ROOT / "data/_derived/_patch*_2026q2_KR*.json")))


def drift() -> list[tuple]:
    rows = json.loads(MASTER.read_text(encoding="utf-8"))
    rows = rows if isinstance(rows, list) else rows.get("records", rows)
    idx = {}
    for r in rows:
        kr = r.get("회사코드") or r.get("원보험사코드")
        idx[(kr, r.get("공시분기"), r.get("항목번호"))] = r

    out = []
    for p in patches():
        patch = json.loads(Path(p).read_text(encoding="utf-8"))
        kr, q = patch["company_code"], patch["quarter"]
        for c in patch["cells"]:
            hit = idx.get((kr, q, c["항목번호"]))
            if hit is None:
                out.append((kr, c["항목번호"], "행 없음", None, None))
                continue
            for f in ("값", "값_적용후"):
                want = c.get(f)
                if want is None:
                    continue
                got = hit.get(f)
                try:
                    ok = got is not None and abs(float(got) - float(want)) <= max(
                        abs(float(want)) * 0.001, 0.02)
                except (TypeError, ValueError):
                    ok = str(got) == str(want)
                if not ok:
                    out.append((kr, c["항목번호"], f, want, got))
    return out


def main() -> int:
    ps = patches()
    if not ps:
        print("적용할 패치가 없다.")
        return 0

    before = drift()
    print(f"패치 {len(ps)}개 · 재적용 전 drift {len(before)}건")
    for kr, item, f, want, got in before:
        print(f"  {kr} item{item} {f}: 패치={want} → 마스터={got}")

    if not before:
        print("drift 없음 — 재적용 생략")
        return 0

    r = subprocess.run([PY, str(APPLY)] + ps, cwd=ROOT)
    if r.returncode != 0:
        print("재적용 실패")
        return r.returncode

    after = drift()
    print(f"\n재적용 후 drift {len(after)}건")
    for kr, item, f, want, got in after:
        print(f"  {kr} item{item} {f}: 패치={want} → 마스터={got}")
    return 0 if not after else 2


if __name__ == "__main__":
    raise SystemExit(main())
