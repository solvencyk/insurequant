"""Read-only probe: can the production Tier-2 PL chain (build_pl_breakdown.parse_filing) be made to read the COMPARATIVE (prior-year) columns for the
companies whose CSM bundle needs a PL companion?  Technique (no production code changed, monkeypatches live only in this process):
  * companies._old_prior  flipped  -> the 'pre-2025.2Q 구분-rows' readers (삼성화재/DB style) keep only the comparative (전분기/전반기) tables
  * tier2._b_note_table   -> returns the SECOND matching '보험손익 상세내역' table (메리츠 Format-B prints 당분기 table first, 전분기 second)
The probe prints PL item 4 (원수CSM상각) read from the later filing's comparative columns next to the latest CSM-waterfall amortisation (prior-column read)
and the master PL.  usage: python s76_pl_prior_companions.py KR0008:2024.1Q KR0001:2024.1Q ...
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
os.chdir(ROOT)
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
import build_pl_breakdown as BP  # noqa: E402
from scripts.pl_breakdown import companies as C  # noqa: E402
from scripts.pl_breakdown import tier2 as T2  # noqa: E402

pl = {}
for r in json.loads((ROOT / "PL_breakdown.json").read_text(encoding="utf-8")):
    pl[(r["원보험사코드"], r["공시분기"], r["항목번호"])] = r["값"]
names = {}
for r in json.loads((ROOT / "CSM_waterfall.json").read_text(encoding="utf-8")):
    names[r["원보험사코드"]] = r["원수사명"]
lat = json.loads((HERE / "cand" / "csm_adopt_overlay.json").read_text(encoding="utf-8"))
LIFE = {"KR0068", "KR0069", "KR0070", "KR0071", "KR0072", "KR0073", "KR0079", "KR0082", "KR0083", "KR0087", "KR0094", "KR0099", "KR0104"}

_orig_old_prior = C._old_prior
_orig_b = T2._b_note_table


def second_b(tables):
    seen = 0
    for t in tables:
        if "보험손익" in (t.caption or "") and "상세내역" in (t.caption or ""):
            if any(T2._row_matches(r, T2.B_CSM) for r in t.rows):
                seen += 1
                if seen == 2:
                    return t
    return None


for spec in sys.argv[1:]:
    kr, later = spec.split(":")
    y = int(later[:4])
    prior_q = f"{y-1}{later[4:]}"
    fy = f"FY{later[:4]}_Q{later[5]}"
    dirs = [str(d) for d in sorted((ROOT / "data/dart" / fy / "raw").glob(f"{kr}_*"))]
    is_life = kr in LIFE
    C._old_prior = lambda tbls, i, _o=_orig_old_prior: not _o(tbls, i)
    T2._b_note_table = second_b
    try:
        t1, t2 = BP.parse_filing(dirs, is_life, kr, names.get(kr), later)
    except Exception as e:  # noqa: BLE001
        t1, t2 = None, f"ERR {type(e).__name__}: {e}"
    finally:
        C._old_prior = _orig_old_prior
        T2._b_note_table = _orig_b
    # current-column read of the same filing for orientation
    try:
        t1c, t2c = BP.parse_filing(dirs, is_life, kr, names.get(kr), later)
    except Exception as e:  # noqa: BLE001
        t2c = f"ERR {e}"
    key = f"{kr}|{prior_q}"
    wf5 = (lat.get(key) or {}).get("5")
    print("=" * 100)
    print(f"{kr} {names.get(kr)} later={later} (prior quarter {prior_q}) life={is_life}")
    pr = lambda t2_: {k: (round(t2_.get(k), 1) if isinstance(t2_.get(k), (int, float)) else None) for k in (4, 5, 6, 9, 10, 11, 13, 14)} if isinstance(t2_, dict) else t2_
    print("  current-year read :", pr(t2c))
    print("  comparative read  :", pr(t2))
    print(f"  master PL {prior_q} item4/5/6:", [pl.get((kr, prior_q, i)) for i in (4, 5, 6)], " | latest CSM wf amort (억):", wf5, "-> PL(백만원)", None if wf5 is None else abs(wf5) * 100)
