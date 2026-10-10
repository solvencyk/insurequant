#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Retract BS cells that THIS backfill added (listed in load_manifest_bs.json) and later proved wrong.

Only keys present in the manifest's `added` lists (cells created by scripts/bspl_granularity_load_bs.py in this
session) can be retracted; pre-existing master cells are never touched.  Removes the key from IFRS17_BS.json,
bs_manual_overrides.json, bs_from_disclosure.json and the per-company part file, with the same byte-exact round-trip
and concurrent-change guards as the loader.  Dry-run is the default.

  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/bspl_granularity_retract_bs.py --keys KR0099|20|2026.1Q,KR0099|20|2026.2Q --reason "..." [--apply]
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.stdout.reconfigure(encoding="utf-8")

import bspl_granularity_load_bs as L  # noqa: E402  (shared helpers: exact round-trip loaders, paths)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--keys", required=True)
    ap.add_argument("--reason", required=True)
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--round", default="retract")
    a = ap.parse_args()
    keys = [k for k in a.keys.split(",") if k]
    man = json.loads(L.MANIFEST.read_text(encoding="utf-8"))
    added = set()
    for r in man["rounds"]:
        added |= set(r.get("added", []))
    unknown = [k for k in keys if k not in added]
    if unknown:
        raise SystemExit(f"ABORT: not added by this backfill (refusing to touch): {unknown}")
    rows, raw_m = L.load_json_exact(L.MASTER, 2, "\r\n")
    ov, raw_o = L.load_json_exact(L.OVERRIDES, 2, "\n")
    sd, raw_s = L.load_json_exact(L.SIDECAR, 2, "\r\n")
    ks = {tuple([k.split("|")[0], int(k.split("|")[1]), k.split("|")[2]]) for k in keys}
    keep = [r for r in rows if (r["원보험사코드"], r["항목번호"], r["공시분기"]) not in ks]
    print(f"master rows {len(rows)} -> {len(keep)} (remove {len(rows) - len(keep)}); overrides hit {sum(k in ov['cells'] for k in keys)}; sidecar hit {sum(k in sd['cells'] for k in keys)}")
    if not a.apply:
        print("dry-run -- nothing written")
        return
    rd = L.BACKUP / f"round_{a.round}"
    rd.mkdir(parents=True, exist_ok=True)
    for p in (L.MASTER, L.OVERRIDES, L.SIDECAR):
        shutil.copy2(p, rd / p.name)
    for k in keys:
        ov["cells"].pop(k, None)
        sd["cells"].pop(k, None)
        code = k.split("|")[0]
        pp = L.PARTS / f"{code}_agent_gran.json"
        if pp.exists():
            pd = json.loads(pp.read_text(encoding="utf-8"))
            pd["cells"].pop(k, None)
            pp.write_text(json.dumps(pd, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
    ov["_readme"].append(f"[{time.strftime('%Y-%m-%d')}] 경영공시 BS granularity 백필에서 넣은 {len(keys)}칸 철회(기존 값 변경 0): {a.reason}")
    for p, raw in ((L.MASTER, raw_m), (L.OVERRIDES, raw_o), (L.SIDECAR, raw_s)):
        if p.read_bytes() != raw:
            raise SystemExit(f"ABORT: {p.name} changed since it was read")
    L.safe_write(L.OVERRIDES, L.dumps(ov, 2, "\n"))
    L.safe_write(L.SIDECAR, L.dumps(sd, 2, "\r\n"))
    L.safe_write(L.MASTER, L.dumps(keep, 2, "\r\n"))
    man.setdefault("retracted", []).append({"keys": keys, "reason": a.reason, "stamp": time.strftime("%Y-%m-%d %H:%M")})
    for r in man["rounds"]:
        r["added"] = [k for k in r.get("added", []) if k not in set(keys)]
    L.MANIFEST.write_text(json.dumps(man, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    print(f"RETRACTED {len(keys)} cells; master rows now {len(keep)}")


if __name__ == "__main__":
    main()
