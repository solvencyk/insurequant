# -*- coding: utf-8 -*-
"""Run ONE existing read-only gate in-process while serving alternative BYTES for chosen repo files.

Dry-run safety (ticket 20261012T1930Z): every write that lands under the repo root and is not under this folder is
RECORDED AND DROPPED (the master-tables gate normally rewrites data/_derived/qoq_warn.json and pl_oci_vs_bs_aoci_warn.json,
the CSM continuity / NB gates rewrite data/dart/viz/*.json).  Nothing in the repo changes.  The gate code is the live
gate code, so a candidate master is judged by exactly the rules the pre-push hook uses.

  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe gate_overlay.py <gate> <out.txt> [<name>=<path> ...]

  <gate>  data_contract | master_tables | ilp_portfolio | ilp_lic | csm_continuity | csm_waterfall | nb_csm | csm_coverage
  <name>  repo-root-relative file name (e.g. CSM_waterfall.json), <path> the file whose bytes are served in its place.
          No mapping = live files.
"""
from __future__ import annotations

import builtins
import io
import pathlib
import runpy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
OUT_DIR = Path(__file__).resolve().parent
SCRIPT = {
    "data_contract": ("validate_data_contract.py", []),
    "master_tables": ("validate_master_tables.py", ["--no-build"]),
    "ilp_portfolio": ("validate_insurance_liability_portfolio.py", []),
    "ilp_lic": ("validate_insurance_liability_lic.py", []),
    "csm_continuity": ("validate_csm_continuity.py", []),
    "csm_waterfall": ("validate_csm_waterfall.py", []),
    "nb_csm": ("validate_nb_csm_multiple.py", []),
    "csm_coverage": ("check_csm_coverage.py", []),
    "live_artifacts": ("validate_live_artifacts.py", []),
}


def _under(p: Path, base: Path) -> bool:
    try:
        p.resolve().relative_to(base.resolve())
        return True
    except Exception:
        return False


def main() -> int:
    which, out = sys.argv[1], Path(sys.argv[2])
    live: dict[Path, Path] = {}
    for spec in sys.argv[3:]:
        name, _, p = spec.partition("=")
        src = Path(p).resolve()
        if not src.exists():
            raise SystemExit(f"served file missing: {src}")
        live[(ROOT / name).resolve()] = src
    orig_write_text, orig_write_bytes = pathlib.Path.write_text, pathlib.Path.write_bytes
    orig_read_text, orig_read_bytes = pathlib.Path.read_text, pathlib.Path.read_bytes
    orig_path_open, orig_open = pathlib.Path.open, builtins.open
    served: list[str] = []
    dropped: list[str] = []

    def remap(p):
        try:
            return live.get(Path(p).resolve())
        except Exception:
            return None

    def drop_write(p) -> bool:
        """True when the write must be dropped (under repo root, outside this folder)."""
        try:
            pp = Path(p)
            if _under(pp, ROOT) and not _under(pp, OUT_DIR):
                dropped.append(str(pp.resolve().relative_to(ROOT.resolve())))
                return True
        except Exception:
            pass
        return False

    def w_text(self, data, *a, **k):
        if drop_write(self):
            return len(data)
        return orig_write_text(self, data, *a, **k)

    def w_bytes(self, data):
        if drop_write(self):
            return len(data)
        return orig_write_bytes(self, data)

    def r_text(self, *a, **k):
        m = remap(self)
        if m is not None:
            served.append(self.name)
            return orig_read_text(m, *a, **k)
        return orig_read_text(self, *a, **k)

    def r_bytes(self):
        m = remap(self)
        if m is not None:
            served.append(self.name)
            return orig_read_bytes(m)
        return orig_read_bytes(self)

    def p_open(self, *a, **k):
        mode = str(a[0]) if a else str(k.get("mode", "r"))
        if any(c in mode for c in "wax+"):
            if drop_write(self):
                return io.BytesIO() if "b" in mode else io.StringIO()
            return orig_path_open(self, *a, **k)
        m = remap(self)
        if m is not None:
            served.append(self.name)
            return orig_path_open(m, *a, **k)
        return orig_path_open(self, *a, **k)

    def b_open(file, *a, **k):
        if isinstance(file, (str, bytes, pathlib.PurePath)):
            mode = str(a[0]) if a else str(k.get("mode", "r"))
            if any(c in mode for c in "wax+"):
                if drop_write(file):
                    return io.BytesIO() if "b" in mode else io.StringIO()
            else:
                m = remap(file)
                if m is not None:
                    served.append(Path(file).name)
                    return orig_open(m, *a, **k)
        return orig_open(file, *a, **k)

    pathlib.Path.write_text, pathlib.Path.write_bytes = w_text, w_bytes
    pathlib.Path.read_text, pathlib.Path.read_bytes = r_text, r_bytes
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
        pathlib.Path.write_text, pathlib.Path.write_bytes = orig_write_text, orig_write_bytes
        pathlib.Path.read_text, pathlib.Path.read_bytes = orig_read_text, orig_read_bytes
        pathlib.Path.open = orig_path_open
        builtins.open = orig_open
    buf.flush()
    txt = raw.getvalue().decode("utf-8")
    out.write_text(txt, encoding="utf-8", newline="\n")
    real.reconfigure(encoding="utf-8")
    counts = {n: served.count(n) for n in sorted(set(served))}
    print(f"[gate_overlay] {which} exit={rc} lines={len(txt.splitlines())} served_reads={counts} "
          f"dropped_writes={sorted(set(dropped))} -> {out.name}")
    return int(rc)


if __name__ == "__main__":
    sys.exit(main())
