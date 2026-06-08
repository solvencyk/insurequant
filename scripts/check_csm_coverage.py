# -*- coding: utf-8 -*-
"""CSM COMPLETENESS gate — the blind spot the consistency gates (closing/crosscheck/
plausibility) miss: a company-quarter that is simply ABSENT trips no arithmetic check.

For every (company, quarter) in 2023.1Q..2026.1Q whose 기말 CSM is missing from
CSM_waterfall.json, decide:
  • RED  — the DART raw XML EXISTS for that quarter → the filing was made but the
           parser failed to extract it (a real gap, e.g. 메리츠 2025.3Q 'caption 변형').
  • ok   — no raw (the insurer did not file a quarterly CSM disclosure: small/foreign/
           digital insurers file annual-only). A legitimate absence, NOT a bug.

Exit 1 if any RED. This is what should have been run BEFORE ever claiming "complete".
"""
from __future__ import annotations
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[1]
CSM = ROOT / "CSM_waterfall.json"

ALLQ = [f"{y}.{q}Q" for y in range(2023, 2027) for q in range(1, 5)
        if not (y == 2026 and q > 1)]
QDIR = {f"{y}.{q}Q": f"FY{y}_Q{q}" for y in range(2023, 2027) for q in range(1, 5)}


def _has_raw(code: str, q: str) -> bool:
    for rd in ROOT.glob(f"data/dart/{QDIR[q]}/raw/{code}_*"):
        if any(rd.glob("*.xml")) or any(rd.glob("xml/*.xml")) or any(rd.glob("extracted/*.xml")):
            return True
    return False


def main() -> int:
    rows = json.loads(CSM.read_text(encoding="utf-8"))
    have: dict[str, set] = defaultdict(set)
    code_of: dict[str, str] = {}
    for r in rows:
        code_of[r["원수사명"]] = r["원보험사코드"]
        if r["항목번호"] == 6 and r.get("값") is not None:
            have[r["원수사명"]].add(r["공시분기"])

    red: list[tuple[str, str, str]] = []   # (name, code, quarter) raw exists but cell missing
    absent = 0
    for nm in sorted(have):
        code = code_of[nm]
        for q in ALLQ:
            if q in have[nm]:
                continue
            if _has_raw(code, q):
                red.append((nm, code, q))
            else:
                absent += 1

    n_co = len(have)
    print(f"CSM COMPLETENESS  companies={n_co}  quarters={len(ALLQ)}")
    print(f"  legitimate-absence (no raw filed): {absent} cells")
    print(f"  RED (raw exists, cell MISSING = parser gap): {len(red)}")
    for nm, code, q in red:
        print(f"    RED  {code}  {nm}  {q}")
    print("\n" + ("CSM COVERAGE OK (no raw-but-missing)" if not red else "CSM COVERAGE GAPS PRESENT"))
    return 1 if red else 0


if __name__ == "__main__":
    sys.exit(main())
