#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Resume an interrupted bspl_granularity_load_bs.py --apply (2026-10-11 round 4: the master write succeeded, the write of
bs_manual_overrides.json died with OSError 22 -- a transient Windows file lock -- leaving IFRS17_BS.json ahead of its
lineage files).

Rebuilds exactly what the loader would have written for the overlay and the sidecar from
  * the cells that are in IFRS17_BS.json but not in the round's backup master  (= the round's added keys), and
  * the per-company part files data/_derived/bs_from_disclosure_parts/<KR>_agent_gran.json (written before the master),
verifies them, writes with a retrying atomic replace, and writes the manifest entry.  Dry-run is the default.

  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/bspl_granularity_resume_bs.py --round 4 [--apply]
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.stdout.reconfigure(encoding="utf-8")

import bspl_granularity_load_bs as L  # noqa: E402


def safe_write(path: Path, data: bytes, tries: int = 8):
    last = None
    for i in range(tries):
        tmp = path.with_name(path.name + ".tmp_resume")
        try:
            tmp.write_bytes(data)
            os.replace(tmp, path)
            return
        except OSError as e:        # transient lock (antivirus / another reader)
            last = e
            time.sleep(0.75 * (i + 1))
    raise SystemExit(f"ABORT: could not write {path}: {last!r}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--round", required=True)
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    rd = L.BACKUP / f"round{a.round}"
    base_rows = json.loads((rd / "IFRS17_BS.json").read_bytes().decode("utf-8"))
    base_keys = {(r["원보험사코드"], r["항목번호"], r["공시분기"]) for r in base_rows}
    rows, raw_m = L.load_json_exact(L.MASTER, 2, "\r\n")
    ov, raw_o = L.load_json_exact(L.OVERRIDES, 2, "\n")
    sd, raw_s = L.load_json_exact(L.SIDECAR, 2, "\r\n")
    added = [r for r in rows if (r["원보험사코드"], r["항목번호"], r["공시분기"]) not in base_keys]
    print(f"master rows {len(rows)} (backup {len(base_rows)}), added keys {len(added)}")
    # every pre-existing row must be unchanged
    cur = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r for r in rows}
    base_idx = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): json.dumps(r, ensure_ascii=False, sort_keys=True) for r in base_rows}
    bad = [k for k, s in base_idx.items() if json.dumps(cur.get(k), ensure_ascii=False, sort_keys=True) != s]
    if bad:
        raise SystemExit(f"ABORT: {len(bad)} pre-existing rows changed, e.g. {bad[:3]}")

    parts = {}
    missing = []
    n_ov = n_sd = 0
    for r in added:
        k = f"{r['원보험사코드']}|{r['항목번호']}|{r['공시분기']}"
        code = r["원보험사코드"]
        if code not in parts:
            pp = L.PARTS / f"{code}_agent_gran.json"
            parts[code] = json.loads(pp.read_text(encoding="utf-8"))["cells"] if pp.exists() else {}
        cell = parts[code].get(k)
        if cell is None:
            missing.append(k)
            continue
        if abs(cell["값"] - r["값"]) > 1e-9:
            raise SystemExit(f"ABORT: part value differs from master for {k}")
        if k in ov["cells"]:
            if ov["cells"][k]["값"] != cell["값"]:
                raise SystemExit(f"ABORT: overlay holds a different value for {k}")
        else:
            ov["cells"][k] = {"값": cell["값"], "근거": cell["근거"]}
            n_ov += 1
        if k in sd["cells"]:
            if sd["cells"][k]["값"] != cell["값"]:
                raise SystemExit(f"ABORT: sidecar holds a different value for {k}")
        else:
            sd["cells"][k] = cell
            n_sd += 1
    if missing:
        raise SystemExit(f"ABORT: {len(missing)} added cells have no part-file entry, e.g. {missing[:3]}")
    stamp = time.strftime("%Y-%m-%d")
    ov["_readme"].append(f"[{stamp}] 경영공시 BS 세부(granularity) 백필 라운드 {a.round} -- {n_ov}칸 신규(기존 키 변경 0), "
                         f"scripts/bspl_granularity_load_bs.py(중단 후 scripts/bspl_granularity_resume_bs.py 로 재개). "
                         f"계보: data/_derived/bs_from_disclosure.json")
    print(f"overlay +{n_ov}, sidecar +{n_sd}")
    if not a.apply:
        print("dry-run -- nothing written")
        return
    for p, raw in ((L.MASTER, raw_m), (L.OVERRIDES, raw_o), (L.SIDECAR, raw_s)):
        if p.read_bytes() != raw:
            raise SystemExit(f"ABORT: {p.name} changed since it was read")
    safe_write(L.OVERRIDES, L.dumps(ov, 2, "\n"))
    safe_write(L.SIDECAR, L.dumps(sd, 2, "\r\n"))
    man = json.loads(L.MANIFEST.read_text(encoding="utf-8")) if L.MANIFEST.exists() else {"rounds": []}
    man["rounds"].append({"round": a.round, "stamp": stamp,
                          "added": [f"{r['원보험사코드']}|{r['항목번호']}|{r['공시분기']}" for r in added],
                          "master_rows_before": len(base_rows), "master_rows_after": len(rows),
                          "overrides_new": n_ov, "sidecar_new": n_sd, "master_sha256_after": L.sha_bytes(L.MASTER.read_bytes()),
                          "note": "resumed after OSError 22 on bs_manual_overrides.json"})
    L.MANIFEST.write_text(json.dumps(man, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    print("RESUMED: overlay and sidecar written, manifest updated")


if __name__ == "__main__":
    main()
