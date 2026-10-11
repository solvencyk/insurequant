# -*- coding: utf-8 -*-
"""Run ONE read-only gate (validate_data_contract.py or validate_master_tables.py --no-build) in-process while serving alternative BYTES for chosen
master files instead of the live ones.  Nothing is written to the repo (the two warn files the master-tables gate normally rewrites are skipped, an
attempt to write a served file aborts).  Purpose: compare a master BEFORE and AFTER a write under IDENTICAL gate code while another agent is editing
the gate scripts (same technique as data/_derived/bspl_apply_20261011/item4_reinsurers_lina6/gate_overlay.py, generalised to any file names).

  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe gate_overlay_csm.py <data_contract|master_tables> <out.txt> [<name>=<path> ...]

  <name> is a repo-root-relative file name (e.g. CSM_waterfall.json), <path> the file whose bytes are served in its place.  No mapping = live files.
"""
from __future__ import annotations

import builtins
import io
import pathlib
import runpy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = {"data_contract": "validate_data_contract.py", "master_tables": "validate_master_tables.py"}
ARGS = {"data_contract": [], "master_tables": ["--no-build"]}
SKIP_NAMES = {"qoq_warn.json", "pl_oci_vs_bs_aoci_warn.json"}


def main() -> int:
    which, out = sys.argv[1], Path(sys.argv[2])
    live = {}
    for spec in sys.argv[3:]:
        name, _, p = spec.partition("=")
        src = Path(p).resolve()
        if not src.exists():
            raise SystemExit(f"served file missing: {src}")
        live[(ROOT / name).resolve()] = src
    orig_write, orig_read_text, orig_read_bytes = pathlib.Path.write_text, pathlib.Path.read_text, pathlib.Path.read_bytes
    orig_write_bytes = pathlib.Path.write_bytes
    orig_path_open, orig_open = pathlib.Path.open, builtins.open
    served, skipped = [], []

    def remap(p):
        try:
            return live.get(Path(p).resolve())
        except Exception:
            return None

    def guarded_write(self, data, *a, **k):
        if self.name in SKIP_NAMES:
            skipped.append(self.name)
            return len(data)
        if self.resolve() in live:
            raise SystemExit(f"ABORT: gate tried to write {self}")
        return orig_write(self, data, *a, **k)

    def guarded_write_bytes(self, data):
        if self.name in SKIP_NAMES:
            skipped.append(self.name)
            return len(data)
        if self.resolve() in live:
            raise SystemExit(f"ABORT: gate tried to write {self}")
        return orig_write_bytes(self, data)

    def read_text(self, *a, **k):
        m = remap(self)
        if m is not None:
            served.append(self.name)
            return orig_read_text(m, *a, **k)
        return orig_read_text(self, *a, **k)

    def read_bytes(self):
        m = remap(self)
        if m is not None:
            served.append(self.name)
            return orig_read_bytes(m)
        return orig_read_bytes(self)

    def path_open(self, *a, **k):
        m = remap(self)
        if m is not None and (not a or "r" in str(a[0])) and "w" not in str(k.get("mode", "r")):
            served.append(self.name)
            return orig_path_open(m, *a, **k)
        return orig_path_open(self, *a, **k)

    def bopen(file, *a, **k):
        if isinstance(file, (str, bytes, pathlib.PurePath)):
            m = remap(file)
            mode = a[0] if a else k.get("mode", "r")
            if m is not None and "w" not in mode and "a" not in mode and "+" not in mode:
                served.append(Path(file).name)
                return orig_open(m, *a, **k)
        return orig_open(file, *a, **k)

    pathlib.Path.write_text, pathlib.Path.write_bytes = guarded_write, guarded_write_bytes
    pathlib.Path.read_text, pathlib.Path.read_bytes = read_text, read_bytes
    pathlib.Path.open = path_open
    builtins.open = bopen
    raw = io.BytesIO()
    buf = io.TextIOWrapper(raw, encoding="utf-8", newline="\n", write_through=True)
    real = sys.stdout
    sys.stdout = buf
    sys.argv = [SCRIPT[which]] + ARGS[which]
    sys.path.insert(0, str(ROOT / "scripts"))
    sys.path.insert(0, str(ROOT))
    rc = 0
    try:
        runpy.run_path(str(ROOT / "scripts" / SCRIPT[which]), run_name="__main__")
    except SystemExit as e:
        rc = e.code if isinstance(e.code, int) else (0 if e.code is None else 1)
    finally:
        sys.stdout = real
        pathlib.Path.write_text, pathlib.Path.write_bytes = orig_write, orig_write_bytes
        pathlib.Path.read_text, pathlib.Path.read_bytes = orig_read_text, orig_read_bytes
        pathlib.Path.open = orig_path_open
        builtins.open = orig_open
    buf.flush()
    txt = raw.getvalue().decode("utf-8")
    out.write_text(txt, encoding="utf-8", newline="\n")
    real.reconfigure(encoding="utf-8")
    counts = {n: served.count(n) for n in sorted(set(served))}
    print(f"[gate_overlay_csm] {which} exit={rc} lines={len(txt.splitlines())} served_reads={counts} skipped_writes={sorted(set(skipped))} -> {out.name}")
    return int(rc)


if __name__ == "__main__":
    sys.exit(main())
