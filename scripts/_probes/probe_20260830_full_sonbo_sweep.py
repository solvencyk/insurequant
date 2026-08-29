# -*- coding: utf-8 -*-
"""Full SONBO x quarter sweep, reproducing main()'s exact 2-pass anchor logic, calling
waterfall_for_dir() for every (company, quarter). Read-only -- NO JSON master writes,
NO main()/build_root_masters.py execution. Dumps {kr|quarter: {vals, src}} to a JSON
file (given as argv[1]) for before/after diffing across a code change (git stash).
"""
import sys, re, json
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from scripts.build_csm_waterfall_master import waterfall_for_dir, quarter_from, SONBO, META

out_name = sys.argv[1] if len(sys.argv) > 1 else "_out_20260830_full_sonbo_sweep.json"

result = {}
errors = []
for kr in SONBO:
    name = META.get(kr, (kr, None, None))[0]
    dirs = sorted((p for p in ROOT.glob(f"data/dart/FY*_Q*/raw/{kr}_*") if p.is_dir()),
                  key=lambda rd: (lambda m: (int(m.group(1)), int(m.group(2))) if m else (0, 0))(
                      re.search(r"FY(\d{4})_Q(\d)", str(rd))))
    annual_open, annual_close = {}, {}
    for rd in dirs:
        q = quarter_from(rd)
        if q and q.endswith("4Q"):
            try:
                av, _ = waterfall_for_dir(rd, name, None)
            except Exception as e:
                errors.append(f"{kr} {q} (annual pass1): {e!r}")
                av = None
            if av:
                if av.get(1) is not None:
                    annual_open[int(q[:4])] = av[1]
                if av.get(6) is not None:
                    annual_close[int(q[:4])] = av[6]
    for rd in dirs:
        q = quarter_from(rd)
        if not q:
            continue
        y = int(q[:4])
        anchor = None if q.endswith("4Q") else (annual_open.get(y) or annual_close.get(y - 1))
        try:
            vals, src = waterfall_for_dir(rd, name, anchor)
        except Exception as e:
            errors.append(f"{kr} {q}: {e!r}")
            vals, src = None, f"ERROR:{e!r}"
        result[f"{kr}|{q}"] = {"vals": vals, "src": src}

out_path = ROOT / "scripts/_probes" / out_name
out_path.write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
print(f"wrote {out_path} ({len(result)} company-quarters, {len(errors)} errors)")
if errors:
    for e in errors[:20]:
        print("  ERROR:", e)
