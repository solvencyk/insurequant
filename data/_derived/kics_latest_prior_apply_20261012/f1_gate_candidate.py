"""f1_gate_candidate.py CANDIDATE_MASTER [--release] [--tag NAME] -- run the REAL K-ICS gate (scripts/validate_kics_disclosure.py main())
on a temporary candidate master, in-process, WITHOUT touching the live master or registry files.

--release : monkeypatch (in memory only) the two owner-approved releases out of `_TIER2_ISSUER_INCONSISTENT`
            (KR0003 2025.1Q and KR0032 2024.3Q) so the candidate is judged as it will be after the registry edit is committed.
Writes: gates/<tag>_slim.json (findings + extra-axis RED lists, same shape as the dry-run baseline) and gates/<tag>_stdout.txt.
Restores artifacts/kics_validation/report_latest.json (pointer) and deletes the timestamped report this run created.
"""
import contextlib
import io
import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/kics_latest_prior_apply_20261012")
sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/kics_latest_prior_precedence_dryrun_20261012")
sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/scripts")
sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/src")
from lib_apply import *  # noqa: F401,F403,E402

utf8_stdout()
import harness as dryh  # noqa: E402

cand = Path(sys.argv[1])
release = "--release" in sys.argv
tag = sys.argv[sys.argv.index("--tag") + 1] if "--tag" in sys.argv else "cand"
os.chdir(str(REPO))

import validate_kics_disclosure as vkd  # noqa: E402

if release:
    for k in (("KR0003", "2025.1Q"), ("KR0032", "2024.3Q")):
        assert k in vkd._TIER2_ISSUER_INCONSISTENT, k
        vkd._TIER2_ISSUER_INCONSISTENT.pop(k)

ART = REPO / "artifacts" / "kics_validation"
latest = ART / "report_latest.json"
blob = latest.read_bytes() if latest.exists() else None
before = set(ART.glob("report_2*.json"))
sys.argv = ["validate_kics_disclosure.py", "--master", str(cand)]
buf = io.StringIO()
t0 = time.time()
with contextlib.redirect_stdout(buf):
    rc = vkd.main()
text = buf.getvalue()
first = text.splitlines()[0] if text else ""
rp = Path(first.split("report:", 1)[1].strip())
rep = json.loads(rp.read_text(encoding="utf-8"))
slim = dryh.slim_report(rep)
slim["_rc"] = rc
slim["_release_patch"] = release
slim["_master"] = str(cand)
slim["_master_sha"] = sha_file(cand)
(OUT / "gates").mkdir(exist_ok=True)
write_json_lf(OUT / "gates" / f"{tag}_slim.json", slim, indent=None)
(OUT / "gates" / f"{tag}_stdout.txt").write_text(text, encoding="utf-8", newline="\n")
for p in set(ART.glob("report_2*.json")) - before:
    try:
        p.unlink()
    except OSError:
        pass
if blob is not None:
    latest.write_bytes(blob)
keep = [ln.strip()[:260] for ln in text.splitlines() if ln.startswith("Status counts") or "blocking RED" in ln]
print(f"[{tag}] rc={rc} {time.time()-t0:.0f}s release_patch={release}")
for ln in keep:
    print("  ", ln)
