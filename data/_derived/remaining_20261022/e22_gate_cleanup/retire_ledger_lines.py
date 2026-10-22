"""JOB 1 registry retirements (removals only).  --check (default) verifies guards; --apply writes.

Removes:
  data/_gold/pl_bridge_baseline.json            entries: 5 keys the gate prints as FIXED?
  data/_gold/pl_csm_amort_missing_ledger.json   entries: 1 key the data-contract gate prints as ..._LEDGER_INERT
Guards: file must round-trip byte-exactly through json.loads/json.dumps(indent=2, ensure_ascii=False)
(+ original trailing newline); every key must exist; nothing else may change.  Backups in ./backup/.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
RELEASE = {
    "data/_gold/pl_bridge_baseline.json": [
        "KB라이프생명|2024.1Q|보험손익(dual)",
        "롯데손해보험|2023.2Q|보험손익(leg-coverage)",
        "메리츠화재해상보험|2023.2Q|보험손익(dual)",
        "한화생명|2023.1Q|보험손익(leg-coverage)",
        "한화생명|2023.2Q|보험손익(leg-coverage)",
    ],
    "data/_gold/pl_csm_amort_missing_ledger.json": ["롯데손해보험|2023.1Q"],
}
apply = "--apply" in sys.argv

for rel, keys in RELEASE.items():
    p = ROOT / rel
    raw = p.read_bytes()
    txt = raw.decode("utf-8")
    assert not txt.startswith("﻿"), "BOM"
    obj = json.loads(txt)
    nl = "\r\n" if "\r\n" in txt else "\n"
    tail = nl if txt.endswith("\n") else ""
    rt = json.dumps(obj, ensure_ascii=False, indent=2)
    if nl == "\r\n":
        rt = rt.replace("\n", "\r\n")
    rt += tail
    if rt != txt:
        raise SystemExit(f"ABORT: {rel} does not round-trip byte-exactly (indent/newline)")
    before = dict(obj["entries"])
    for k in keys:
        if k not in obj["entries"]:
            raise SystemExit(f"ABORT: {k!r} not in {rel}")
        del obj["entries"][k]
    after = obj["entries"]
    assert len(after) == len(before) - len(keys)
    assert all(before[k] == after[k] for k in after)
    out = json.dumps(obj, ensure_ascii=False, indent=2)
    if nl == "\r\n":
        out = out.replace("\n", "\r\n")
    out += tail
    print(f"{rel}: entries {len(before)} -> {len(after)}  (sha256 before {hashlib.sha256(raw).hexdigest()[:12]})")
    if apply:
        bk = HERE / "backup" / Path(rel).name
        bk.parent.mkdir(exist_ok=True)
        if not bk.exists():
            shutil.copyfile(p, bk)
        p.write_bytes(out.encode("utf-8"))
        print("  written")
print("applied" if apply else "check only (nothing written)")
