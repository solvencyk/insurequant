#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Run one of the two read-only gates (--no-build, no side-effect writes) while serving either the BASELINE bytes (pre-apply backup) or the LIVE bytes of the four masters this
ticket writes (PL_breakdown.json, PL_breakdown_provenance.json, IFRS17_BS.json, data/_derived/bs_from_disclosure.json).  Nothing is written to the repo.  Purpose: a before/after comparison
under IDENTICAL gate code while another agent may be editing the gate scripts.

  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe gate_overlay.py <data_contract|master_tables> <out.txt> <baseline|live>
"""
from __future__ import annotations

import builtins
import hashlib
import io
import pathlib
import runpy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BASE = ROOT / "data/_derived/reinsurer_resweep_backup_20261012"
SCRIPT = {"data_contract": "validate_data_contract.py", "master_tables": "validate_master_tables.py"}
SKIP_NAMES = {"qoq_warn.json", "pl_oci_vs_bs_aoci_warn.json"}
SERVE = {"PL_breakdown.json": "PL_breakdown.json", "PL_breakdown_provenance.json": "PL_breakdown_provenance.json", "IFRS17_BS.json": "IFRS17_BS.json",
         "data/_derived/bs_from_disclosure.json": "bs_from_disclosure.json"}


def main() -> int:
    which, out, mode = sys.argv[1], Path(sys.argv[2]), sys.argv[3]
    live = {}
    if mode == "baseline":
        for rel, bn in SERVE.items():
            if not (BASE / bn).exists():
                raise SystemExit(f"baseline missing: {BASE / bn}")
            live[(ROOT / rel).resolve()] = BASE / bn
    orig_write, orig_read_text, orig_read_bytes = pathlib.Path.write_text, pathlib.Path.read_text, pathlib.Path.read_bytes
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
        raise SystemExit(f"ABORT: gate tried to write {self}") if self.resolve() in {(ROOT / r).resolve() for r in SERVE} else None
        return orig_write(self, data, *a, **k)

    def safe_guarded_write(self, data, *a, **k):
        if self.name in SKIP_NAMES:
            skipped.append(self.name)
            return len(data)
        if self.resolve() in {(ROOT / r).resolve() for r in SERVE}:
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

    pathlib.Path.write_text, pathlib.Path.read_text, pathlib.Path.read_bytes = safe_guarded_write, read_text, read_bytes
    pathlib.Path.open = path_open
    builtins.open = bopen
    raw = io.BytesIO()
    buf = io.TextIOWrapper(raw, encoding="utf-8", newline="\n", write_through=True)
    real = sys.stdout
    sys.stdout = buf
    sys.argv = [SCRIPT[which], "--no-build"]
    sys.path.insert(0, str(ROOT / "scripts"))
    sys.path.insert(0, str(ROOT))
    gate_hashes = {n: hashlib.sha256((ROOT / "scripts" / n).read_bytes()).hexdigest()[:12] for n in ("validate_data_contract.py", "validate_master_tables.py", "validate_kics_disclosure.py", "_data_contract_selftest.py")
                   if (ROOT / "scripts" / n).exists()}
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
    print(f"[gate_overlay] {which} {mode} exit={rc} lines={len(txt.splitlines())} gate_script_hashes={gate_hashes} baseline_served={sorted(set(served))} n_reads_served={len(served)} skipped_writes={sorted(set(skipped))} -> {out}")
    return int(rc)


if __name__ == "__main__":
    sys.exit(main())
