# -*- coding: utf-8 -*-
"""Attribution test for the golden SUMMARY move: take the CURRENT masters, put the PRE-commit (3e53aef8~1) KR0073 rows
back (and the pre-commit csm_amort ledger), run validate_master_tables.main() (no build, gate-output files not written).
If the summary then equals the committed golden, every moved SUMMARY field is caused by KR0073 rows alone."""
import json, subprocess, sys, io, re, contextlib, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[3]
SC = pathlib.Path(__file__).resolve().parent / "hybrid"; SC.mkdir(exist_ok=True)
sys.path.insert(0, str(ROOT / "scripts")); sys.path.insert(0, str(ROOT))
def show(rev, f): return subprocess.run(["git", "show", f"{rev}:{f}"], capture_output=True, check=True, cwd=ROOT).stdout.decode("utf-8")
mode = sys.argv[1]   # "old_kr0073" (hybrid) or "current"
import validate_master_tables as V
if mode == "old_kr0073":
    for f, attr in (("PL_breakdown.json", "PL_PATH"), ("CSM_waterfall.json", "WF_PATH")):
        cur = json.loads((ROOT / f).read_text(encoding="utf-8")); old = json.loads(show("3e53aef8~1", f))
        key = lambda r: (r["원보험사코드"], r["공시분기"], str(r["항목번호"]))
        oldk = {key(r): r for r in old if r["원보험사코드"] == "KR0073"}
        out = []
        for r in cur:
            out.append(oldk[key(r)] if r["원보험사코드"] == "KR0073" else r)
        assert len([r for r in out if r["원보험사코드"] == "KR0073"]) == len(oldk)
        p = SC / f; p.write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8"); setattr(V, attr, str(p))
    lp = SC / "csm_amort_identity_ledger.json"; lp.write_text(show("3e53aef8~1", "data/_gold/csm_amort_identity_ledger.json"), encoding="utf-8")
    V.CSM_AMORT_LEDGER_PATH = str(lp)
_orig = pathlib.Path.write_text
def guard(self, *a, **k):
    if self.name in ("qoq_warn.json", "pl_oci_vs_bs_aoci_warn.json"): return len(a[0]) if a else 0
    return _orig(self, *a, **k)
pathlib.Path.write_text = guard
sys.argv = ["validate_master_tables.py", "--no-build"]
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    rc = V.main()
(SC / f"stdout_{mode}.txt").write_text(buf.getvalue(), encoding="utf-8")
line = next(l for l in buf.getvalue().splitlines() if l.startswith("SUMMARY"))
(SC / f"summary_{mode}.txt").write_text(f"exit={rc}\n{re.sub(chr(32)+'+', ' ', line.strip())}\n", encoding="utf-8")
print(mode, "exit", rc); print(line)
