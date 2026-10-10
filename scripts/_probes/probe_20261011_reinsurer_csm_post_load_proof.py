# -*- coding: utf-8 -*-
"""Independent post-load proof for the reinsurer CSM load (read only, does not use the loader's own code path).

 1. For every master (+ provenance sidecar): the git HEAD version's rows are an exact prefix of the working-tree rows
    (so no existing row changed, was removed, or moved) and every appended row belongs to a reinsurer (KR1101~KR1108).
 2. The appended rows equal the staged rows (rows_*.json) one for one.
 3. Per-company-quarter counts of what was loaded.
 4. File hygiene: no BOM, CRLF line endings only, no trailing newline (same as before).

Run:  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/_probes/probe_20261011_reinsurer_csm_post_load_proof.py
"""
from __future__ import annotations

import json
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STAGE = ROOT / "data" / "_derived" / "reinsurer_ifrs17_csm_20261011"
sys.stdout.reconfigure(encoding="utf-8")
CODES = {f"KR11{n:02d}" for n in range(1, 9)}

MASTERS = [
    ("CSM_amortization.json", "rows_amortization.json", "경과차년"),
    ("CSM_sensitivity.json", "rows_sensitivity.json", "순번"),
    ("CSM_waterfall.json", "rows_waterfall.json", "항목번호"),
    ("management_indicators.json", "mi_rows.json", "항목번호"),
]


def head_blob(name: str) -> bytes:
    return subprocess.run(["git", "show", f"HEAD:{name}"], cwd=ROOT, check=True, capture_output=True).stdout


def main() -> int:
    ok = True
    for name, staged_name, unit in MASTERS:
        head = json.loads(head_blob(name).decode("utf-8"))
        raw = (ROOT / name).read_bytes()
        now = json.loads(raw.decode("utf-8"))
        staged = json.loads((STAGE / staged_name).read_text(encoding="utf-8"))
        prefix_ok = now[: len(head)] == head
        appended = now[len(head):]
        app_codes = {r["원보험사코드"] for r in appended}
        app_ok = appended == staged and app_codes <= CODES
        hyg = (not raw.startswith(b"\xef\xbb\xbf")) and (b"\n" not in raw.replace(b"\r\n", b"")) and (not raw.endswith(b"\n"))
        print(f"== {name}: HEAD {len(head)} -> now {len(now)} (+{len(appended)}) | HEAD rows are exact prefix: {prefix_ok} | "
              f"appended == staged and reinsurer-only: {app_ok} | no BOM/CRLF-only/no trailing NL: {hyg}")
        ok &= prefix_ok and app_ok and hyg
        # existing companies per code: unchanged
        by_head, by_now = defaultdict(list), defaultdict(list)
        for r in head:
            by_head[r["원보험사코드"]].append(r)
        for r in now:
            by_now[r["원보험사코드"]].append(r)
        diff_codes = [c for c in by_head if by_head[c] != by_now.get(c)]
        print(f"   companies present before: {len(by_head)}; companies whose rows differ now: {diff_codes}")
        ok &= not diff_codes
        # counts per company-quarter
        cnt = Counter((r["원보험사코드"], r["원수사명"], r["공시분기"]) for r in appended)
        for (c, nm, q), n in sorted(cnt.items()):
            print(f"   {c} {nm} {q}: {n} rows")
    # sidecar
    head_s = json.loads(head_blob("CSM_waterfall_provenance.json").decode("utf-8"))
    raw_s = (ROOT / "CSM_waterfall_provenance.json").read_bytes()
    now_s = json.loads(raw_s.decode("utf-8"))
    added = now_s["cells"][len(head_s["cells"]):]
    side_ok = now_s["cells"][: len(head_s["cells"])] == head_s["cells"] and all(c["company_code"] in CODES for c in added)
    other_keys_same = {k: v for k, v in now_s.items() if k != "cells"} == {k: v for k, v in head_s.items() if k != "cells"}
    print(f"== CSM_waterfall_provenance.json: cells {len(head_s['cells'])} -> {len(now_s['cells'])} (+{len(added)}); "
          f"HEAD cells exact prefix: {side_ok}; other top-level keys unchanged: {other_keys_same}")
    ok &= side_ok and other_keys_same
    print(f"   added cell sample: {added[0]}")
    print("ALL PROOFS OK" if ok else "!! SOME PROOF FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
