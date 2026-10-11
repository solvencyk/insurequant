#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Run one of the two read-only gates (--no-build, no side-effect writes -- same as scripts/bspl_apply_gate.py) while serving the BASELINE bytes of
PL_breakdown.json / PL_breakdown_provenance.json from a backup directory instead of the live files.  Nothing is written to the repo; the live masters are
not touched.  Purpose: a before/after comparison under IDENTICAL gate code when another agent is editing the gate scripts concurrently.

  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe gate_overlay.py <data_contract|master_tables> <out.txt> <baseline_dir>
"""
from __future__ import annotations

import builtins
import io
import pathlib
import runpy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
SCRIPT = {"data_contract": "validate_data_contract.py", "master_tables": "validate_master_tables.py"}
SKIP_NAMES = {"qoq_warn.json", "pl_oci_vs_bs_aoci_warn.json"}
SERVE = ("PL_breakdown.json", "PL_breakdown_provenance.json")


def main() -> int:
    which, out, base = sys.argv[1], Path(sys.argv[2]), Path(sys.argv[3]).resolve()
    live = {(ROOT / n).resolve(): (base / n) for n in SERVE}
    for n in SERVE:
        if not (base / n).exists():
            raise SystemExit(f"baseline missing: {base / n}")
    orig_write, orig_read_text, orig_read_bytes = pathlib.Path.write_text, pathlib.Path.read_text, pathlib.Path.read_bytes
    orig_path_open, orig_open = pathlib.Path.open, builtins.open
    served, skipped = [], []

    def remap(p):
        try:
            rp = Path(p).resolve()
        except Exception:
            return None
        return live.get(rp)

    def guarded_write(self, data, *a, **k):
        if self.name in SKIP_NAMES:
            skipped.append(self.name)
            return len(data)
        if self.resolve() in live:
            raise SystemExit(f"ABORT: gate tried to write {self}")
        return orig_write(self, data, *a, **k)

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

    pathlib.Path.write_text, pathlib.Path.read_text, pathlib.Path.read_bytes = guarded_write, read_text, read_bytes
    pathlib.Path.open = path_open
    builtins.open = bopen
    raw = io.BytesIO()
    buf = io.TextIOWrapper(raw, encoding="utf-8", newline="\n", write_through=True)
    real = sys.stdout
    sys.stdout = buf
    sys.argv = [SCRIPT[which], "--no-build"]
    sys.path.insert(0, str(ROOT / "scripts"))
    sys.path.insert(0, str(ROOT))
    rc = 0
    try:
        runpy.run_path(str(ROOT / "scripts" / SCRIPT[which]), run_name="__main__")
    except SystemExit as e:
        rc = e.code if isinstance(e.code, int) else (0 if e.code is None else 1)
    finally:
        sys.stdout = real
        pathlib.Path.write_text, pathlib.Path.read_text, pathlib.Path.read_bytes = orig_write, orig_read_text, orig_read_bytes
        pathlib.Path.open = orig_path_open
        builtins.open = orig_open
    buf.flush()
    txt = raw.getvalue().decode("utf-8")
    out.write_text(txt, encoding="utf-8", newline="\n")
    real.reconfigure(encoding="utf-8")
    print("\n".join(txt.strip().splitlines()[-4:]))
    print(f"[gate_overlay] {which} exit={rc} lines={len(txt.splitlines())} baseline_served={sorted(set(served))} n_reads_served={len(served)} skipped_writes={sorted(set(skipped))} -> {out}")
    return int(rc)


if __name__ == "__main__":
    sys.exit(main())
