#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Cell-level BS corrector for the 2026-10-11 round 3 (parser/ifrs17, inbox/parser/20261011T1130Z).

Applies a spec (data/_derived/bspl_apply_20261011/spec_*.json: cells with action replace | add | keep) to
  IFRS17_BS.json                                    master  (row 값 replaced / row added; nothing else touched)
  data/dart/viz/bs_manual_overrides.json            overlay the builder re-applies last (so a rebuild cannot resurrect the old value)
  data/_derived/bs_from_disclosure.json             lineage sidecar
  data/_derived/bs_from_disclosure_parts/<file>     part file that re-feeds the sidecar/overlay through merge_bs_disclosure_parts.py
Guards (abort before any write): the old value must still be in every file that holds the cell; an added key must be absent
everywhere; the files must not have changed since they were read.  Backups of every touched file go to
data/_derived/bspl_apply_backup_20261011/<round>/.  The master is written LAST (atomic replace).  After writing, every other
master row is verified byte-identical (json) and only the spec's keys may differ.

  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/bspl_apply_bs_fix.py --spec <a.json> [--spec <b.json>] --round NAME [--apply]
Dry-run is the default.  Never runs build_ifrs17_bs.py / build_root_masters.py.
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
import time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.stdout.reconfigure(encoding="utf-8")

from bspl_granularity_load_bs import (LABELS, SECTION, dumps, load_json_exact, meta_from_kics, safe_write,  # noqa: E402
                                      sha_bytes)

MASTER = ROOT / "IFRS17_BS.json"
OVERRIDES = ROOT / "data" / "dart" / "viz" / "bs_manual_overrides.json"
SIDECAR = ROOT / "data" / "_derived" / "bs_from_disclosure.json"
PARTS = ROOT / "data" / "_derived" / "bs_from_disclosure_parts"
BACKUP = ROOT / "data" / "_derived" / "bspl_apply_backup_20261011"
MANIFEST = ROOT / "data" / "_derived" / "bspl_apply_20261011" / "load_manifest_bs_apply.json"
EPS = 1e-9


def klass(stem: str) -> str:
    if "_agent_" not in stem:
        return "engine"
    if stem.endswith("_agent_note"):
        return "note"
    if stem.endswith("_agent_vision"):
        return "vision"
    return "other_agent"


def peek(name: str) -> dict:
    return json.loads((PARTS / name).read_text(encoding="utf-8"))


def detect_fmt(path: Path):
    raw = path.read_bytes()
    obj = json.loads(raw.decode("utf-8"))
    for indent in (2,):
        for nl in ("\n", "\r\n"):
            if dumps(obj, indent, nl) == raw:
                return obj, raw, indent, nl
    raise SystemExit(f"ABORT: {path.name} does not round-trip byte-exactly with indent 2 (LF or CRLF)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec", action="append", required=True)
    ap.add_argument("--round", required=True)
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    cells = []
    for sp in a.spec:
        d = json.loads(Path(sp).read_text(encoding="utf-8"))
        cells += [c for c in d["cells"] if c["action"] in ("replace", "add")]
    keys = [c["key"] for c in cells]
    if len(set(keys)) != len(keys):
        raise SystemExit("ABORT: duplicate keys in spec")

    rows, raw_master = load_json_exact(MASTER, 2, "\r\n")
    ov, raw_ov = load_json_exact(OVERRIDES, 2, "\n")
    side, raw_side = load_json_exact(SIDECAR, 2, "\r\n")
    by_key = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r for r in rows}
    meta = meta_from_kics()

    parts = {}                      # file name -> (obj, raw, indent, nl)
    def part(name):
        if name not in parts:
            p = PARTS / name
            parts[name] = detect_fmt(p) if p.exists() else ({"_readme": [], "cells": {}, "skips": {}}, None, 2, "\n")
        return parts[name]

    # ---- guards ----
    for c in cells:
        code, item_s, q = c["key"].split("|")
        item = int(item_s)
        k3 = (code, item, q)
        if c["action"] == "replace":
            if k3 not in by_key:
                raise SystemExit(f"ABORT: {c['key']} not in master")
            if abs(by_key[k3]["값"] - c["old"]) > EPS:
                raise SystemExit(f"ABORT: master {c['key']} = {by_key[k3]['값']} != guard {c['old']}")
            for name, lst in (("overlay", ov["cells"]), ("sidecar", side["cells"])):
                if c["key"] in lst and abs(lst[c["key"]]["값"] - c["old"]) > EPS:
                    raise SystemExit(f"ABORT: {name} {c['key']} = {lst[c['key']]['값']} != guard {c['old']}")
            # every non-engine part file (other_agent / note / vision: they outrank the engine files in scripts/merge_bs_disclosure_parts.py)
            # that holds the key must still hold the guard value; all of them are updated so a later re-merge cannot resurrect the old value.
            # Engine files (<KR>.json) rank below the *_agent_* files, so my <KR>_agent_apply.json overrides them and they are left untouched.
            for pname in sorted(x.name for x in PARTS.glob("*.json")):
                if klass(Path(pname).stem) == "engine":
                    continue
                pc = peek(pname).get("cells") or {}
                if c["key"] in pc and abs(pc[c["key"]]["값"] - c["old"]) > EPS:
                    raise SystemExit(f"ABORT: part {pname} {c['key']} = {pc[c['key']]['값']} != guard {c['old']}")
        else:
            if k3 in by_key:
                raise SystemExit(f"ABORT: add {c['key']} but the master already has it")
            if c["key"] in ov["cells"] or c["key"] in side["cells"]:
                raise SystemExit(f"ABORT: add {c['key']} but overlay/sidecar already has it")
            if code not in meta:
                raise SystemExit(f"ABORT: no META for {code}")
        c["_part"] = c.get("part_file") or f"{code}_agent_apply.json"
        part(c["_part"])
        c["_targets"] = {c["_part"]} | ({x.name for x in PARTS.glob("*.json") if klass(x.stem) != "engine" and c["key"] in (peek(x.name).get("cells") or {})}
                                        if c["action"] == "replace" else set())
        for tname in c["_targets"]:
            part(tname)
    n_rep = sum(1 for c in cells if c["action"] == "replace")
    n_add = sum(1 for c in cells if c["action"] == "add")
    print(f"spec cells: replace {n_rep}, add {n_add}; by company {dict(Counter(c['key'].split('|')[0] for c in cells))}")
    for c in cells:
        old = f"{c['old']:,.6f}" if c["action"] == "replace" else "(blank)"
        print(f"  {c['action']:<7} {c['key']:<20} {old:>18} -> {c['new']:,.6f}")
    if not a.apply:
        print("dry-run -- nothing written")
        return

    # ---- backups ----
    rd = BACKUP / a.round
    rd.mkdir(parents=True, exist_ok=True)
    for p in (MASTER, OVERRIDES, SIDECAR):
        shutil.copy2(p, rd / p.name)
    (rd / "parts").mkdir(exist_ok=True)
    for name in parts:
        if (PARTS / name).exists():
            shutil.copy2(PARTS / name, rd / "parts" / name)

    stamp = time.strftime("%Y-%m-%d")
    snapshot = {k: json.dumps(v, ensure_ascii=False, sort_keys=True) for k, v in by_key.items()}
    side_before = {k: json.dumps(v, ensure_ascii=False, sort_keys=True) for k, v in side["cells"].items()}
    ov_before = {k: json.dumps(v, ensure_ascii=False, sort_keys=True) for k, v in ov["cells"].items()}
    added_rows = []
    for c in cells:
        code, item_s, q = c["key"].split("|")
        item = int(item_s)
        k3 = (code, item, q)
        new = c["new"]
        rec = {"값": new, "pdf": c.get("pdf"), "page": c.get("page"), "sha256": c.get("pdf_sha256"),
               "축척": c.get("scale", "원 -> 백만원"), "앵커항목": None, "방법": c.get("method"), "근거": c["basis"]}
        if c["action"] == "replace":
            rec["정정전값"] = c["old"]
            by_key[k3]["값"] = new
        else:
            nm, tk, sb = meta[code]
            added_rows.append({"원보험사코드": code, "원수사명": nm, "티커": tk, "생손보여부": sb, "항목번호": item, "항목명": LABELS[item],
                               "섹션": SECTION[item], "레벨": 1 if item in (1, 2, 3) else 2, "공시분기": q, "값": new})
        ov["cells"][c["key"]] = {"값": new, "근거": c["basis"]}
        side["cells"][c["key"]] = rec
        for tname in sorted(c["_targets"]):
            parts[tname][0]["cells"][c["key"]] = {k: v for k, v in rec.items() if v is not None}
    ov["_readme"].append(f"[{stamp}] round3(inbox/parser/20261011T1130Z, round {a.round}) -- 정정 {n_rep}칸(옛 값 guard) + 신규 {n_add}칸, "
                         f"scripts/bspl_apply_bs_fix.py 로 셀단위. 계보: data/_derived/bs_from_disclosure.json, 근거 칸에 정정 사유.")
    out_rows = rows + added_rows
    out_rows.sort(key=lambda r: (r["원보험사코드"], r["항목번호"], r["공시분기"]))

    # ---- concurrency guard, then write (master last) ----
    for p, raw in ((MASTER, raw_master), (OVERRIDES, raw_ov), (SIDECAR, raw_side)):
        if p.read_bytes() != raw:
            raise SystemExit(f"ABORT: {p.name} changed since it was read (concurrent session?) -- nothing written")
    for name, (obj, raw, indent, nl) in parts.items():
        p = PARTS / name
        if raw is not None and p.read_bytes() != raw:
            raise SystemExit(f"ABORT: part {name} changed since it was read")
        if raw is None:
            obj["_readme"] = [f"[{stamp}] round3(inbox/parser/20261011T1130Z) 정정·신규 칸의 계보 -- scripts/bspl_apply_bs_fix.py 가 쓴다. "
                              "scripts/merge_bs_disclosure_parts.py 가 이 파일을 다른 파트와 같이 사이드카·오버레이로 합친다."]
        safe_write(p, dumps(obj, indent, nl))
    safe_write(OVERRIDES, dumps(ov, 2, "\n"))
    safe_write(SIDECAR, dumps(side, 2, "\r\n"))
    safe_write(MASTER, dumps(out_rows, 2, "\r\n"))

    # ---- verify ----
    chk = json.loads(MASTER.read_bytes().decode("utf-8"))
    chk_idx = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r for r in chk}
    rep_keys = {tuple([c["key"].split("|")[0], int(c["key"].split("|")[1]), c["key"].split("|")[2]]) for c in cells if c["action"] == "replace"}
    add_keys = {tuple([c["key"].split("|")[0], int(c["key"].split("|")[1]), c["key"].split("|")[2]]) for c in cells if c["action"] == "add"}
    changed = {k for k, s in snapshot.items() if json.dumps(chk_idx.get(k), ensure_ascii=False, sort_keys=True) != s}
    if changed != rep_keys or set(chk_idx) - set(snapshot) != add_keys or len(chk) != len(rows) + len(added_rows) or len(chk_idx) != len(chk):
        raise SystemExit(f"VERIFY FAILED master: changed {sorted(changed)[:5]} expected {sorted(rep_keys)[:5]}; rows {len(chk)}")
    ov2 = json.loads(OVERRIDES.read_bytes().decode("utf-8"))["cells"]
    sd2 = json.loads(SIDECAR.read_bytes().decode("utf-8"))["cells"]
    spec_keys = set(keys)
    bad_ov = [k for k, s in ov_before.items() if k not in spec_keys and json.dumps(ov2.get(k), ensure_ascii=False, sort_keys=True) != s]
    bad_sd = [k for k, s in side_before.items() if k not in spec_keys and json.dumps(sd2.get(k), ensure_ascii=False, sort_keys=True) != s]
    if bad_ov or bad_sd or len(ov2) != len(ov_before) + sum(1 for k in spec_keys if k not in ov_before) or set(ov2) - set(ov_before) != {k for k in spec_keys if k not in ov_before}:
        raise SystemExit(f"VERIFY FAILED lineage: overlay {bad_ov[:3]} sidecar {bad_sd[:3]}")
    prev = json.loads(MANIFEST.read_text(encoding="utf-8")).get("rounds", []) if MANIFEST.exists() else []
    prev.append({"round": a.round, "stamp": stamp,
                 "replaced": [{"key": c["key"], "old": c["old"], "new": c["new"]} for c in cells if c["action"] == "replace"],
                 "added": [{"key": c["key"], "new": c["new"]} for c in cells if c["action"] == "add"],
                 "master_rows_before": len(rows), "master_rows_after": len(chk), "master_sha256_after": sha_bytes(MASTER.read_bytes())})
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps({"rounds": prev}, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    print(f"APPLIED round {a.round}: replaced {len(rep_keys)}, added {len(add_keys)}; master rows {len(rows)} -> {len(chk)}; "
          f"all other {len(snapshot) - len(rep_keys)} pre-existing rows identical; overlay/sidecar other cells identical")


if __name__ == "__main__":
    main()
