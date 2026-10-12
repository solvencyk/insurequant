#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Run ONE read-only gate with the BASELINE bytes of the masters I changed served from backups (map.json) or with the live files ('live').
Writes into the repository are suppressed (names logged), so nothing in the tree changes; gate code and every other file are whatever is on disk at the moment
-> run 'before' and 'after' back to back for an identical-code comparison.  (Same technique as data/_derived/reinsurer_csm_resweep_20261012/gate_overlay_csm.py,
with an explicit target -> baseline map.)

  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe gate_overlay.py <data_contract|master_tables|continuity|ilp_portfolio|ilp_lic|live_artifacts> <out.txt> <baseline_map.json|live>
"""
from __future__ import annotations

import builtins
import io
import json
import pathlib
import runpy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = {"data_contract": ("validate_data_contract.py", []), "master_tables": ("validate_master_tables.py", ["--no-build"]), "continuity": ("validate_csm_continuity.py", []),
          "ilp_portfolio": ("validate_insurance_liability_portfolio.py", []), "ilp_lic": ("validate_insurance_liability_lic.py", []),
          "live_artifacts": ("validate_live_artifacts.py", [])}


def main() -> int:
    which, out, base = sys.argv[1], Path(sys.argv[2]), sys.argv[3]
    live = {}
    if base != "live":
        mp = json.loads(Path(base).read_text(encoding="utf-8"))
        for target, bfile in mp.items():
            b = (ROOT / bfile).resolve()
            if not b.exists():
                raise SystemExit(f"baseline missing: {b}")
            live[(ROOT / target).resolve()] = b
    orig = dict(write_text=pathlib.Path.write_text, write_bytes=pathlib.Path.write_bytes, read_text=pathlib.Path.read_text, read_bytes=pathlib.Path.read_bytes,
                path_open=pathlib.Path.open, open=builtins.open)
    served, suppressed = [], []

    def remap(p):
        try:
            return live.get(Path(p).resolve())
        except Exception:
            return None

    def inside_repo(p):
        try:
            Path(p).resolve().relative_to(ROOT)
            return True
        except Exception:
            return False

    def w_text(self, data, *a, **k):
        if inside_repo(self):
            suppressed.append(self.name)
            return len(data)
        return orig["write_text"](self, data, *a, **k)

    def w_bytes(self, data, *a, **k):
        if inside_repo(self):
            suppressed.append(self.name)
            return len(data)
        return orig["write_bytes"](self, data, *a, **k)

    def r_text(self, *a, **k):
        m = remap(self)
        if m is not None:
            served.append(self.name)
            return orig["read_text"](m, *a, **k)
        return orig["read_text"](self, *a, **k)

    def r_bytes(self):
        m = remap(self)
        if m is not None:
            served.append(self.name)
            return orig["read_bytes"](m)
        return orig["read_bytes"](self)

    def p_open(self, mode="r", *a, **k):
        if any(c in mode for c in "wax+") and inside_repo(self):
            suppressed.append(self.name)
            return io.StringIO() if "b" not in mode else io.BytesIO()
        m = remap(self)
        if m is not None and not any(c in mode for c in "wax+"):
            served.append(self.name)
            return orig["path_open"](m, mode, *a, **k)
        return orig["path_open"](self, mode, *a, **k)

    def b_open(file, mode="r", *a, **k):
        if isinstance(file, (str, bytes, pathlib.PurePath)):
            if any(c in mode for c in "wax+") and inside_repo(file):
                suppressed.append(Path(file).name)
                return io.StringIO() if "b" not in mode else io.BytesIO()
            m = remap(file)
            if m is not None and not any(c in mode for c in "wax+"):
                served.append(Path(file).name)
                return orig["open"](m, mode, *a, **k)
        return orig["open"](file, mode, *a, **k)

    pathlib.Path.write_text, pathlib.Path.write_bytes, pathlib.Path.read_text, pathlib.Path.read_bytes = w_text, w_bytes, r_text, r_bytes
    pathlib.Path.open = p_open
    builtins.open = b_open
    raw = io.BytesIO()
    buf = io.TextIOWrapper(raw, encoding="utf-8", newline="\n", write_through=True)
    real = sys.stdout
    sys.stdout = buf
    script, args = SCRIPT[which]
    sys.argv = [script] + args
    sys.path.insert(0, str(ROOT / "scripts"))
    sys.path.insert(0, str(ROOT))
    rc = 0
    try:
        runpy.run_path(str(ROOT / "scripts" / script), run_name="__main__")
    except SystemExit as e:
        rc = e.code if isinstance(e.code, int) else (0 if e.code is None else 1)
    finally:
        sys.stdout = real
        pathlib.Path.write_text, pathlib.Path.write_bytes, pathlib.Path.read_text, pathlib.Path.read_bytes = orig["write_text"], orig["write_bytes"], orig["read_text"], orig["read_bytes"]
        pathlib.Path.open = orig["path_open"]
        builtins.open = orig["open"]
    buf.flush()
    txt = raw.getvalue().decode("utf-8")
    out.write_text(txt, encoding="utf-8", newline="\n")
    real.reconfigure(encoding="utf-8")
    print("\n".join(txt.strip().splitlines()[-4:]))
    print(f"[gate_overlay] {which} base={base} exit={rc} lines={len(txt.splitlines())} served={sorted(set(served))} n_served={len(served)} suppressed_writes={sorted(set(suppressed))} -> {out}")
    return int(rc)


if __name__ == "__main__":
    sys.exit(main())
