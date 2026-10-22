# -*- coding: utf-8 -*-
"""e21 STEP 0 (read-only): input hashes at the start + 'old' of every READY_all candidate cell vs the CURRENT live masters + working tree vs git HEAD for the files this load will write.
Ticket inbox/parser/20261023T0300Z (parser/ifrs17).  Writes input_hashes_start.txt and e21_preflight.txt next to this file.   python = venv script file only."""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
HERE = Path(__file__).resolve().parent
CRLF, LF = bytes([13, 10]), bytes([10])
MEAS = ROOT / "data/_derived/remaining_20261022/e20_held_and_remaining/measure"
sys.stdout.reconfigure(encoding="utf-8")
FILES = ["PL_breakdown.json", "CSM_waterfall.json", "PL_breakdown_provenance.json", "CSM_waterfall_provenance.json", "data/_gold/user_pl_cells.json", "data/_gold/user_csm_cells.json",
         "data/_gold/gold_overlay_ledger.json", "data/_gold/csm_amort_identity_ledger.json", "data/_gold/pl_csm_amort_missing_ledger.json", "data/_gold/pl_bridge_baseline.json",
         "data/dart/viz/pl_breakdown_master.json", "data/_derived/pl_breakdown_coverage.json", "data/_derived/pl_oci_item32_provenance.json", "data/_derived/pl_intentional_nulls.json",
         "tests/test_rule_coverage_manifest.py", "tests/fixtures/pl_breakdown_golden.json", "tests/fixtures/master_tables_golden.json", "scripts/pl_breakdown/companies.py",
         "scripts/validate_master_tables.py", "scripts/emit_pl_provenance.py", "NB_CSM_multiple.json", "data/dart/viz/csm_waterfall_master_diag.json"]


def sha(b):
    return hashlib.sha256(b).hexdigest()


def git_head_bytes(rel):
    p = subprocess.run(["git", "-C", str(ROOT), "show", f"HEAD:{rel}"], capture_output=True, stdin=subprocess.DEVNULL)
    return p.stdout if p.returncode == 0 else None


out = []
pr = out.append
head = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"], capture_output=True, text=True, stdin=subprocess.DEVNULL).stdout.strip()
br = subprocess.run(["git", "-C", str(ROOT), "branch", "--show-current"], capture_output=True, text=True, stdin=subprocess.DEVNULL).stdout.strip()
pr(f"git HEAD {head} branch {br}")
lines = []
for rel in FILES:
    p = ROOT / rel
    if not p.exists():
        pr(f"  MISSING {rel}")
        continue
    b = p.read_bytes()
    hb = git_head_bytes(rel)
    same = ("== HEAD" if hb == b else ("== HEAD (CRLF-normalised)" if hb.replace(CRLF, LF) == b.replace(CRLF, LF) else "!= HEAD")) if hb is not None else "untracked"
    lines.append(f"{sha(b)}  {len(b):>10}  {rel}  [{same}]")
(HERE / "v0_input_hashes_start.txt").write_text("git HEAD " + head + "\n" + "\n".join(lines) + "\n", encoding="utf-8", newline="\n")
pr("input hashes -> v0_input_hashes_start.txt")
pr("\n".join("  " + x for x in lines))

cand = json.loads((MEAS / "cands_READY_all.json").read_text(encoding="utf-8"))
pl = {(r["원보험사코드"], r["공시분기"], str(r["항목번호"])): r["값"] for r in json.loads((ROOT / "PL_breakdown.json").read_text(encoding="utf-8"))}
cs = {(r["원보험사코드"], r["공시분기"], str(r["항목번호"])): r["값"] for r in json.loads((ROOT / "CSM_waterfall.json").read_text(encoding="utf-8"))}
bad = 0
for kind, cells, live in (("PL", cand["pl_cells"], pl), ("CSM", cand["csm_cells"], cs)):
    n = nb = 0
    for c in cells:
        k = (c["code"], c["q"], str(c["item"]))
        lv = live.get(k, "ROW_ABSENT")
        ok = (lv is None and c["old"] is None) or (isinstance(lv, (int, float)) and c["old"] is not None and abs(lv - c["old"]) < 1e-6)
        n += 1
        if not ok:
            nb += 1
            pr(f"  DIFF {kind} {k}: candidate old={c['old']} live={lv} new={c['new']}")
    pr(f"{kind}: candidate cells {n}, old == live master: {n - nb}, differ: {nb}")
    bad += nb
pr(f"TOTAL differ {bad}")
(HERE / "v0_preflight.txt").write_text("\n".join(out) + "\n", encoding="utf-8", newline="\n")
print("\n".join(out))
