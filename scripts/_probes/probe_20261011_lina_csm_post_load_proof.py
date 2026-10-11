# -*- coding: utf-8 -*-
"""Independent post-load proof for the Lina (KR0074) CSM backfill (read only; does not use the loader's code path).

 1. For CSM_waterfall.json, CSM_amortization.json and the provenance sidecar: the git HEAD version's rows/cells are an exact
    prefix of the working-tree rows (no existing row changed, was removed, or moved) and every appended row belongs to KR0074.
 2. Key diff HEAD vs working tree: keys removed 0, keys whose row changed 0, keys added = the staged keys (listed).
 3. Every other company's rows are identical to HEAD; the old KR0074 rows (2023.4Q / 2024.4Q / 2025.4Q) are identical.
 4. The appended rows equal the staged rows one for one.
 5. The loaded values satisfy open+new+interest+assumption+amortisation == close and the 당분기 convention of build_root_masters.
 6. File hygiene: no BOM, CRLF line endings only, no trailing newline.

Run:  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/_probes/probe_20261011_lina_csm_post_load_proof.py
"""
from __future__ import annotations

import json
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STAGE = ROOT / "data" / "_derived" / "csm_backfill_lina_20261011"
sys.path.insert(0, str(ROOT / "scripts"))
sys.stdout.reconfigure(encoding="utf-8")
CODE = "KR0074"

MASTERS = [
    ("CSM_waterfall.json", "rows_waterfall.json", lambda r: (r["원보험사코드"], r["공시분기"], r["항목번호"]), None),
    ("CSM_amortization.json", "rows_amortization.json", lambda r: (r["원보험사코드"], r["공시분기"], r["경과차년"]), None),
    ("CSM_waterfall_provenance.json", "sidecar_cells.json", lambda r: (r["company_code"], r["quarter"], r["item_block"]), "cells"),
]


def head_blob(name: str) -> bytes:
    return subprocess.run(["git", "show", f"HEAD:{name}"], cwd=ROOT, check=True, capture_output=True).stdout


def main() -> int:
    ok = True
    wf_now = None
    for name, staged_name, key, field in MASTERS:
        head_obj = json.loads(head_blob(name).decode("utf-8"))
        raw = (ROOT / name).read_bytes()
        now_obj = json.loads(raw.decode("utf-8"))
        head = head_obj if field is None else head_obj[field]
        now = now_obj if field is None else now_obj[field]
        staged = json.loads((STAGE / staged_name).read_text(encoding="utf-8"))
        # the amortisation staging may be filtered by --amort-quarters: compare against what is in the master for those quarters
        appended = now[len(head):]
        if name == "CSM_amortization.json":
            qs = {r["공시분기"] for r in appended}
            staged = [r for r in staged if r["공시분기"] in qs]
        prefix_ok = now[: len(head)] == head
        app_ok = appended == staged and all((r.get("원보험사코드") or r.get("company_code")) == CODE for r in appended)
        hyg = (not raw.startswith(b"\xef\xbb\xbf")) and (b"\n" not in raw.replace(b"\r\n", b"")) and (not raw.endswith(b"\n"))
        other_hdr = True if field is None else ({k: v for k, v in now_obj.items() if k != field} == {k: v for k, v in head_obj.items() if k != field})
        # key diff
        hk = {key(r): r for r in head}
        nk = {key(r): r for r in now}
        removed = [k for k in hk if k not in nk]
        changed = [k for k in hk if k in nk and nk[k] != hk[k]]
        added = [k for k in nk if k not in hk]
        dup = len(now) - len(nk)
        print(f"== {name}: HEAD {len(head)} -> now {len(now)} (+{len(appended)})")
        print(f"   HEAD rows are exact prefix: {prefix_ok} | appended == staged and KR0074-only: {app_ok} | no BOM/CRLF-only/no trailing NL: {hyg} | other top-level keys unchanged: {other_hdr}")
        print(f"   key diff vs HEAD: removed {len(removed)} | existing keys whose row changed {len(changed)} | keys added {len(added)} | duplicate keys now {dup}")
        by_q = Counter(k[1] for k in added)
        print("   added per quarter:", dict(sorted(by_q.items())))
        ok &= prefix_ok and app_ok and hyg and other_hdr and not removed and not changed and dup == 0 and len(added) == len(appended)
        if field is None:
            by_head, by_now = defaultdict(list), defaultdict(list)
            for r in head:
                by_head[r["원보험사코드"]].append(r)
            for r in now:
                by_now[r["원보험사코드"]].append(r)
            diff_codes = [c for c in by_head if by_head[c] != by_now.get(c)[: len(by_head[c])]]
            old_lina = [r for r in now if r["원보험사코드"] == CODE][: len(by_head[CODE])]
            print(f"   companies whose HEAD rows differ in the working tree: {diff_codes} | old KR0074 rows identical: {old_lina == by_head[CODE]} ({len(by_head[CODE])} rows)")
            ok &= (not diff_codes) and old_lina == by_head[CODE]
        if name == "CSM_waterfall.json":
            wf_now = now
    # value checks on the loaded waterfall rows
    import build_root_masters as BR

    ytd = defaultdict(dict)
    for r in wf_now:
        if r["원보험사코드"] == CODE:
            ytd[r["항목번호"]][r["공시분기"]] = r["값"]
    new_q = sorted({r["공시분기"] for r in wf_now[-18:]})
    for q in new_q:
        o, n, i, a, am, c = (ytd[k][q] for k in range(1, 7))
        res = o + n + i + a + am - c
        print(f"   {q}: open {o} + new {n} + interest {i} + assumption {a} + amort {am} = {round(o + n + i + a + am, 5)} vs close {c} -> residual {res:+.5f}")
        ok &= abs(res) < 1e-4
    for r in wf_now[-18:]:
        no, q, v = r["항목번호"], r["공시분기"], r["값"]
        if no == BR.CSM_CLOSE:
            d = v
        elif no == BR.CSM_OPEN:
            p = BR._prev_q(q)
            d = v if p is None else ytd[BR.CSM_CLOSE].get(p)
        else:
            d = BR._flow_dangi(ytd[no], q)
        d = round(d, 6) if isinstance(d, (int, float)) else d
        if d != r["값_당분기"]:
            print(f"   !! 값_당분기 differs from the build_csm convention: {q} item {no}: stored {r['값_당분기']} vs derived {d}")
            ok = False
    print("   값_당분기 of the loaded rows == build_root_masters.build_csm() convention: checked for", len(wf_now[-18:]), "rows")
    print("ALL PROOFS OK" if ok else "!! SOME PROOF FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
