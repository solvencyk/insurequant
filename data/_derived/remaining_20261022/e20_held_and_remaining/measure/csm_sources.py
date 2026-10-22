"""csm_sources: for the later filings that supply a CSM latest vector, list the PRIOR-period blocks the dry-run reader (prior_csm.prior_blocks, production block extractor + labeller) finds:
source file, table line_no (lxml sourceline), caption.  These are the candidate source tables for the CSM vector (the apply step re-reads them).  READ-ONLY.
usage: csm_sources.py CODE:Q,CODE:Q,...  -> csm_sources.json/.txt"""
import json
import sys
from pathlib import Path

sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e20_held_and_remaining/measure")
sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/ifrs17_latest_comparative_precedence_dryrun_20261012")
import prod as P  # noqa: E402  (chdir repo root, sys.path)
import mlib as M  # noqa: E402
import prior_csm as PC  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
res, txt = {}, []
pl, names, inames = M.load_pl()
for sp in sys.argv[1].split(","):
    code, q = sp.split(":")
    fy = M.later_fy(q)
    dirs = M.filing_dirs(code, fy)
    if not dirs:
        txt.append(f"{code} {q}: no raw dir for {fy}")
        continue
    rd = dirs[0]
    try:
        pri, cur, blocks, lab = PC.prior_blocks(rd, names.get(code))
    except Exception as e:  # noqa: BLE001
        txt.append(f"{code} {q}: prior_blocks failed: {e}")
        continue
    rows = [{"src": b.get("_src"), "line_no": b.get("line_no"), "caption": (b.get("caption") or "")[:60]} for b in pri]
    res[f"{code}|{q}"] = {"later_dir": M.rel(rd), "n_prior_blocks": len(pri), "prior_blocks": rows}
    txt.append(f"{code} {q} later {M.rel(rd)}: {len(pri)} prior blocks: " + "; ".join(f"{r['src']}:L{r['line_no']}" for r in rows[:14]))
M.MEASURE.joinpath("csm_sources.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
M.MEASURE.joinpath("csm_sources.txt").write_text("\n".join(txt), encoding="utf-8")
print("\n".join(txt)[:6000])
