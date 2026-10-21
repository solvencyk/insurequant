"""Read-only: do the FY2026 filings (2026.1Q / 2026.2Q) restate the 2025.1Q / 2025.2Q PL block of KR0073?  (scope check beyond the 6 target quarters)

Same harness as run_extra.py / compare_blocks.py: restated = prior-period (comparative) columns of the later filing, separate basis; production-mode block of the later filing itself is
compared with the live master too (fidelity).  Writes restated_blocks_2026.json and compare_2026.txt.  No repo file is touched.
"""
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import plib  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
ROOT = plib.ROOT
TOL = 5e-4
root = json.loads((ROOT / "PL_breakdown.json").read_text(encoding="utf-8"))
names, cur = {}, {}
for r in root:
    if r["원보험사코드"] == "KR0073":
        names[r["항목번호"]] = r["항목명"]
        cur.setdefault(r["공시분기"], {})[r["항목번호"]] = r.get("값")


def clean(d):
    return {str(k): (round(v, 6) if isinstance(v, float) else v) for k, v in d.items()}


def classify(old, new):
    if old is None and new is None:
        return "BOTH_NONE"
    if old is None:
        return "FILL"
    if new is None:
        return "LOST"
    return "SAME" if abs(old - new) <= TOL else "CHANGED"


def fmt(v):
    return "None" if v is None else f"{v:,.2f}"


lines, res = [], {}
for later in ["2026.1Q", "2026.2Q"]:
    t0 = time.time()
    tables = plib.parse_tables(plib.raw_dirs(later))
    q_prior = f"{int(later[:4]) - 1}{later[4:]}"
    vr, mr = plib.block(later, True, tables, alt_label=True)
    vc, mc = plib.block(later, False, tables, alt_label=True)
    res[q_prior] = {"later": later, "restated_alt": clean(vr), "t1_src": mr["t1_src"], "t2": clean(mr["t2"] or {})}
    res.setdefault("_prod_alt", {})[later] = clean(vc)
    del tables
    for label, q, blk in (("restated (comparative of %s)" % later, q_prior, vr), ("production-mode block of %s itself" % later, later, vc)):
        cnt = {"SAME": 0, "CHANGED": 0, "FILL": 0, "LOST": 0, "BOTH_NONE": 0}
        diffs = []
        for i in range(1, 33):
            old, new = cur.get(q, {}).get(i), blk.get(i)
            c = classify(old, new)
            cnt[c] += 1
            if c not in ("SAME", "BOTH_NONE"):
                diffs.append((i, c, old, new))
        lines.append(f"--- {q}  {label}  reconciled={blk.get('_reconciled')}  {cnt}")
        for i, c, old, new in diffs:
            d = "" if old is None or new is None else f"  delta {new - old:+,.2f}"
            lines.append(f"    item{i:2d} {str(names.get(i))[:18]:18s} {c:7s} master={fmt(old):>16s} later={fmt(new):>16s}{d}")
    print(f"[{time.strftime('%H:%M:%S')}] {later} done ({time.time() - t0:.0f}s)", flush=True)
(HERE / "restated_blocks_2026.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
(HERE / "compare_2026.txt").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
print("\n".join(lines))
print("DONE")
