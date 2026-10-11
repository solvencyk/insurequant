#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Cell-level PL corrector for round 3 of the BS/PL work (2026-10-11, parser/ifrs17, inbox/parser/20261011T1130Z item A).

Applies a spec {"cells": [{"key": "KR0008|14|2023.2Q", "old": 354530.0, "new": 161674.0, "basis": "..."}]} to
  PL_breakdown.json              (row `값` replaced with an old-value guard; `값_당분기` of the series re-derived with build_root_masters._flow_dangi
                                  = YTD(q) - YTD(previous quarter of the same year), Q1 = YTD, None when a YTD is missing)
  PL_breakdown_provenance.json   (one `merge_note_<tag>` string; the lineage blocks themselves are unchanged -- the same source file still explains the cell)
Guards (abort before any write): the old value must be what the master holds (None = blank); every row whose `값_당분기` depends on a changed
`값` must currently satisfy the derivation rule (else the series is not rule-consistent and a human must look); the files must not change
between read and write.  Backups of both files go to data/_derived/bspl_apply_backup_20261011/<round>/.  The master is written LAST (atomic
replace).  After writing, every other row is verified identical and only the spec keys + the derived-quarter rows may differ.
`create: true` on a cell appends a missing row (meta copied from the company's other rows).

  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/bspl_apply_pl_fix.py --spec <a.json> [--spec <b.json>] --round NAME [--apply]
Dry-run is the default.  Never runs build_root_masters.py / build_pl_breakdown.py.
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
import time
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.stdout.reconfigure(encoding="utf-8")

import bspl_granularity_load_bs as L  # noqa: E402  (exact round-trip loader, safe_write, dumps)

MASTER = ROOT / "PL_breakdown.json"
SIDECAR = ROOT / "PL_breakdown_provenance.json"
BACKUP = ROOT / "data" / "_derived" / "bspl_apply_backup_20261011"
MANIFEST = ROOT / "data" / "_derived" / "bspl_apply_20261011" / "load_manifest_pl_apply.json"
EPS = 1e-9


def qkey(q):
    return int(q[:4]), int(q[5])


def prev_q(q):
    y, n = qkey(q)
    return None if n == 1 else f"{y}.{n - 1}Q"


def next_q(q):
    y, n = qkey(q)
    return None if n == 4 else f"{y}.{n + 1}Q"


def flow_dangi(ytd, q):
    cur = ytd.get(q)
    if cur is None:
        return None
    p = prev_q(q)
    if p is None:
        return cur
    prev = ytd.get(p)
    return None if prev is None else round(cur - prev, 6)


def same(a, b):
    if a is None or b is None:
        return a is None and b is None
    return abs(a - b) <= EPS


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec", action="append", required=True)
    ap.add_argument("--round", required=True)
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    cells = []
    for sp in a.spec:
        cells += json.loads(Path(sp).read_text(encoding="utf-8"))["cells"]
    keys = [c["key"] for c in cells]
    if len(set(keys)) != len(keys):
        raise SystemExit("ABORT: duplicate keys in spec")

    rows, raw_m = L.load_json_exact(MASTER, 1, "\r\n")
    side, raw_s = L.load_json_exact(SIDECAR, 1, "\r\n")
    by_key = {(r["원보험사코드"], str(r["항목번호"]), r["공시분기"]): r for r in rows}
    if len(by_key) != len(rows):
        raise SystemExit("ABORT: duplicate keys in PL master")
    series = defaultdict(dict)                       # (code, item) -> {q: 값}
    for (code, it, q), r in by_key.items():
        series[(code, it)][q] = r.get("값")

    plan = []                                        # (k3, old, new, cell)
    for c in cells:
        code, it, q = c["key"].split("|")
        k3 = (code, it, q)
        r = by_key.get(k3)
        if r is None:
            if not c.get("create"):
                raise SystemExit(f"ABORT: {c['key']} not in the PL master (use create: true to append a row)")
            if c.get("old") is not None:
                raise SystemExit(f"ABORT: {c['key']} create with a non-null old value")
        else:
            if not same(r.get("값"), c.get("old")):
                raise SystemExit(f"ABORT: master {c['key']} = {r.get('값')} != guard {c.get('old')}")
        plan.append((k3, c.get("old"), c["new"], c))

    # ---- 값_당분기 re-derivation ----
    new_ytd = {k: dict(v) for k, v in series.items()}
    for (code, it, q), _o, new, _c in plan:
        new_ytd.setdefault((code, it), {})[q] = new
    dangi_changes = {}                                # k3 -> (old_dangi, new_dangi)
    touched = set()
    for (code, it, q), _o, _n, _c in plan:
        touched.add((code, it, q))
        nq = next_q(q)
        if nq is not None and (code, it, nq) in by_key:
            touched.add((code, it, nq))
    for k3 in sorted(touched):
        code, it, q = k3
        r = by_key.get(k3)
        newd = flow_dangi(new_ytd[(code, it)], q)
        if r is None:
            dangi_changes[k3] = (None, newd)
            continue
        oldrule = flow_dangi(series[(code, it)], q)
        if not same(r.get("값_당분기"), oldrule):
            raise SystemExit(f"ABORT: {k3}: stored 값_당분기 {r.get('값_당분기')} != rule on the old YTD {oldrule} (series not rule-consistent)")
        if not same(r.get("값_당분기"), newd):
            dangi_changes[k3] = (r.get("값_당분기"), newd)

    print(f"round {a.round}: spec cells {len(plan)}; derived 값_당분기 changes {len(dangi_changes)}")
    for k3, old, new, c in plan:
        print(f"  VALUE  {'|'.join(k3):<24} {"None" if old is None else format(old, ',.3f'):>16} -> {new:>16,.3f}")
    spec_k3 = {p[0] for p in plan}
    for k3, (od, nd) in sorted(dangi_changes.items()):
        print(f"  DANGI  {'|'.join(k3):<24} {"None" if od is None else format(od, ',.3f'):>16} -> {"None" if nd is None else format(nd, ',.3f'):>16}"
              + ("" if k3 in spec_k3 else "   (next quarter of a changed YTD)"))
    if not a.apply:
        print("dry-run -- nothing written")
        return

    # ---- backups ----
    rd = BACKUP / a.round
    rd.mkdir(parents=True, exist_ok=True)
    shutil.copy2(MASTER, rd / MASTER.name)
    shutil.copy2(SIDECAR, rd / SIDECAR.name)
    snapshot = {k: json.dumps(v, ensure_ascii=False, sort_keys=True) for k, v in by_key.items()}

    # ---- apply ----
    meta_of = {}
    for r in rows:
        meta_of.setdefault(r["원보험사코드"], r)
    added = []
    for k3, old, new, c in plan:
        r = by_key.get(k3)
        if r is None:
            m = meta_of[k3[0]]
            item_val = int(k3[1]) if k3[1].isdigit() else k3[1]
            r = {"원보험사코드": k3[0], "원수사명": m["원수사명"], "티커": m["티커"], "생손보여부": m["생손보여부"], "항목번호": item_val,
                 "항목명": c.get("item_name") or "", "공시분기": k3[2], "값": new, "값_당분기": None}
            added.append(r)
            by_key[k3] = r
        else:
            r["값"] = new
    for k3, (od, nd) in dangi_changes.items():
        by_key[k3]["값_당분기"] = nd
    out_rows = rows + added
    stamp = time.strftime("%Y-%m-%d %H:%M")
    tag = a.round.replace(" ", "_")
    side[f"merge_note_20261011_{tag}"] = (
        f"round-3 PL 정정(inbox/parser/20261011T1130Z, round {a.round}, {stamp}): {len(plan)}칸 값 정정/채움 + 파생 값_당분기 {len(dangi_changes)}칸 재계산. "
        f"계보 블록의 원천 파일은 그대로(같은 파일이 같은 칸을 설명한다), 정정 전후 값·근거는 data/_derived/bspl_apply_20261011/ 의 spec·manifest. "
        f"재현: scripts/bspl_apply_pl_fix.py --spec <spec> --round {a.round} --apply")

    # ---- concurrency guard, then write (master last) ----
    for p, raw in ((MASTER, raw_m), (SIDECAR, raw_s)):
        if p.read_bytes() != raw:
            raise SystemExit(f"ABORT: {p.name} changed since it was read (concurrent session?) -- nothing written")
    L.safe_write(SIDECAR, L.dumps(side, 1, "\r\n"))
    L.safe_write(MASTER, L.dumps(out_rows, 1, "\r\n"))

    # ---- verify ----
    chk = json.loads(MASTER.read_bytes().decode("utf-8"))
    cidx = {(r["원보험사코드"], str(r["항목번호"]), r["공시분기"]): r for r in chk}
    allowed = set(spec_k3) | set(dangi_changes)
    bad = [k for k, s in snapshot.items() if k not in allowed and json.dumps(cidx.get(k), ensure_ascii=False, sort_keys=True) != s]
    if bad or len(chk) != len(rows) + len(added) or len(cidx) != len(chk):
        raise SystemExit(f"VERIFY FAILED: unexpected changes {bad[:5]}; rows {len(chk)} expected {len(rows) + len(added)}")
    for k3, old, new, c in plan:
        if not same(cidx[k3].get("값"), new):
            raise SystemExit(f"VERIFY FAILED: {k3} holds {cidx[k3].get('값')} not {new}")
    for k, s in snapshot.items():                       # fields other than 값 / 값_당분기 never change
        if k in allowed:
            o, n = json.loads(s), cidx[k]
            for f in set(o) | set(n):
                if f not in ("값", "값_당분기") and o.get(f) != n.get(f):
                    raise SystemExit(f"VERIFY FAILED: field {f} of {k} changed")
    man = json.loads(MANIFEST.read_text(encoding="utf-8")) if MANIFEST.exists() else {"rounds": []}
    man["rounds"].append({"round": a.round, "stamp": stamp,
                          "values": [{"key": "|".join(k3), "old": old, "new": new, "basis": c.get("basis")} for k3, old, new, c in plan],
                          "dangi": [{"key": "|".join(k3), "old": od, "new": nd} for k3, (od, nd) in sorted(dangi_changes.items())],
                          "rows_before": len(rows), "rows_after": len(chk), "master_sha256_after": L.sha_bytes(MASTER.read_bytes())})
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(man, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    print(f"APPLIED round {a.round}: {len(plan)} values, {len(dangi_changes)} derived 값_당분기; rows {len(rows)} -> {len(chk)}; "
          f"all other {len(snapshot) - len(allowed & set(snapshot))} pre-existing rows identical")


if __name__ == "__main__":
    main()
