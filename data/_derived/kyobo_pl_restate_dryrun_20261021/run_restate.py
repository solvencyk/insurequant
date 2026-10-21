"""Read-only: restated (latest-comparative, separate basis) PL block per target quarter + harness fidelity test.

For every later filing L in LATER (parsed ONCE, one heavy parse at a time):
  prior=True   -> restated block of quarter L-1year (Tier-1 = FS-API frmtrm columns, Tier-2 = Kyobo handler on the PRIOR cumulative column)
  prior=False  -> production-mode block of quarter L (fidelity: must reproduce today's master for the quarters the master built from FS-API+notes)
Writes restated_blocks.json (+ progress log).  No repo file is touched.
"""
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import plib  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
LATER = ["2024.1Q", "2024.2Q", "2024.3Q", "2024.4Q", "2025.1Q", "2025.2Q", "2025.3Q", "2025.4Q"]


def prev_year(q):
    return f"{int(q[:4]) - 1}{q[4:]}"


def clean(d):
    return {k: (round(v, 6) if isinstance(v, float) else v) for k, v in d.items()}


out = {}
for later in LATER:
    t0 = time.time()
    tables = plib.parse_tables(plib.raw_dirs(later))
    q_prior = prev_year(later)
    vp, mp = plib.block(later, True, tables)
    vc, mc = plib.block(later, False, tables)
    out[q_prior] = {"later": later, "restated": clean(vp), "t1_src": mp["t1_src"], "t1_div": mp["t1_div"],
                    "t2": clean({k: v for k, v in (mp["t2"] or {}).items()}),
                    "t1_hidden": {k: v for k, v in (mp["t1"] or {}).items() if isinstance(k, str)}}
    out.setdefault("_production_reproduction", {})[later] = {"block": clean(vc), "t1_src": mc["t1_src"], "t2": clean(mc["t2"] or {})}
    print(f"[{time.strftime('%H:%M:%S')}] {later}: tables={len(tables)} restated {q_prior} reconciled={vp['_reconciled']} "
          f"| production-mode {later} reconciled={vc['_reconciled']} | {time.time() - t0:.0f}s", flush=True)
    del tables
    (HERE / "restated_blocks.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
print("DONE")
