#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""2026-10-11 round 3 (parser/ifrs17, inbox/parser/20261011T1130Z): run one of the two read-only gates WITHOUT its side effects.

  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/bspl_apply_gate.py data_contract  <out.txt>
  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/bspl_apply_gate.py master_tables  <out.txt>

* always passes --no-build (never runs build_root_masters.py);
* validate_master_tables.py writes data/_derived/qoq_warn.json and data/_derived/pl_oci_vs_bs_aoci_warn.json as a side effect --
  those two files are outside this lane's write set, so pathlib.Path.write_text is guarded to skip exactly those two names;
* stdout (utf-8) is saved to <out.txt> and echoed (last 12 lines); the gate's exit code is returned.
"""
from __future__ import annotations

import io
import pathlib
import runpy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = {"data_contract": "validate_data_contract.py", "master_tables": "validate_master_tables.py"}
SKIP_NAMES = {"qoq_warn.json", "pl_oci_vs_bs_aoci_warn.json"}


def main() -> int:
    which, out = sys.argv[1], Path(sys.argv[2])
    orig = pathlib.Path.write_text
    skipped = []

    def guarded(self, data, *a, **k):
        if self.name in SKIP_NAMES:
            skipped.append(self.name)
            return len(data)
        return orig(self, data, *a, **k)

    pathlib.Path.write_text = guarded
    raw = io.BytesIO()
    buf = io.TextIOWrapper(raw, encoding="utf-8", newline="\n", write_through=True)   # has .reconfigure like the real stdout
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
        pathlib.Path.write_text = orig
    buf.flush()
    txt = raw.getvalue().decode("utf-8")
    out.write_text(txt, encoding="utf-8", newline="\n")
    tail = txt.strip().splitlines()[-12:]
    real.reconfigure(encoding="utf-8")
    print("\n".join(tail))
    print(f"[bspl_apply_gate] {which} exit={rc} lines={len(txt.splitlines())} skipped_writes={sorted(set(skipped))} -> {out}")
    return int(rc)


if __name__ == "__main__":
    sys.exit(main())
