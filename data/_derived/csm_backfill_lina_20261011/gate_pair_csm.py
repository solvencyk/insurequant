# -*- coding: utf-8 -*-
"""Run the two gates for a PAIR of master states back to back under the same gate code and compare them.

  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe gate_pair_csm.py <label> <A> <B>
     A, B = "-" (live files) or comma separated name=path (serve those bytes instead of the live master, see gate_overlay_csm.py)
     e.g.  before/after of a write:  gate_pair_csm.py amort A "CSM_amortization.json=<backup>" -   (A = baseline bytes, B = live)

A state signature (size + mtime of the gate scripts, data/_gold, the root masters other than the served ones, data/dart/viz, the top-level
data/_derived json, the xlsx) is taken before and after the four runs; if anything moved (another agent edited code/gold/masters meanwhile) the pair
is repeated (max 3 tries) and the moved files are named.  Outputs: gate_followup/<label>_<A|B>_<gate>.txt and <label>_compare.txt.
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
W = Path(__file__).resolve().parent
OUT = W / "gate_followup"
OUT.mkdir(exist_ok=True)
OVERLAY = W / "gate_overlay_csm.py"
sys.stdout.reconfigure(encoding="utf-8")
EXCLUDE_NAMES = {"qoq_warn.json", "pl_oci_vs_bs_aoci_warn.json"}


def signature(served_names):
    sig = {}
    pats = [("", "*.json"), ("", "*.xlsx"), ("scripts", "*.py"), ("data/_gold", "*.json"), ("data/dart/viz", "*.json"), ("data/_derived", "*.json")]
    for sub, pat in pats:
        base = ROOT / sub if sub else ROOT
        for p in base.glob(pat):
            if p.name in EXCLUDE_NAMES or (sub == "" and p.name in served_names):
                continue
            try:
                st = p.stat()
            except OSError:
                continue
            sig[str(p.relative_to(ROOT)).replace("\\", "/")] = (st.st_size, st.st_mtime_ns)
    return sig


def run(label, tag, spec, gate):
    maps = [] if spec == "-" else spec.split(",")
    out = OUT / f"{label}_{tag}_{gate}.txt"
    r = subprocess.run([sys.executable, str(OVERLAY), gate, str(out), *maps], capture_output=True, cwd=str(ROOT))
    msg = r.stdout.decode("utf-8", errors="replace").strip().splitlines()
    err = r.stderr.decode("utf-8", errors="replace").strip()
    print("  ", msg[-1] if msg else "(no output)", ("| STDERR: " + err[-300:]) if err else "")
    return out, r.returncode


HEAD_RE = re.compile(r"^\s+(RED|YELLOW)\s+\[(.*?)\]\s+(\S+)\s+(.*)$")


def reds(path):
    lines = path.read_text(encoding="utf-8").splitlines()
    out = {}
    for i, ln in enumerate(lines):
        m = HEAD_RE.match(ln)
        if m and m.group(1) == "RED":
            msg = lines[i + 1].strip()[:150] if i + 1 < len(lines) else ""
            out[(m.group(2), m.group(3), m.group(4).strip())] = msg
    return out


def summary(path):
    for ln in path.read_text(encoding="utf-8").splitlines():
        if ln.startswith("SUMMARY"):
            return re.sub(r"\s+", " ", ln.strip())
    return None


def main() -> int:
    label, A, B = sys.argv[1], sys.argv[2], sys.argv[3]
    served = {s.split("=")[0] for spec in (A, B) for s in ([] if spec == "-" else spec.split(","))}
    for attempt in range(1, 4):
        sig0 = signature(served)
        print(f"== pair '{label}' attempt {attempt}: A={A} | B={B}")
        res = {}
        for gate in ("data_contract", "master_tables"):
            for tag, spec in (("A", A), ("B", B)):
                res[(tag, gate)] = run(label, tag, spec, gate)
        sig1 = signature(served)
        moved = sorted(k for k in set(sig0) | set(sig1) if sig0.get(k) != sig1.get(k))
        if not moved:
            print(f"   state signature unchanged during the pair ({len(sig0)} files: gate code, gold, masters, viz, derived json, xlsx)")
            break
        print("   STATE MOVED during the pair (another agent wrote):", moved[:12])
        if attempt == 3:
            print("   giving up identical-state comparison after 3 tries")
    lines = []
    for gate in ("data_contract", "master_tables"):
        a, b = res[("A", gate)][0], res[("B", gate)][0]
        lines.append(f"### {gate}: exit A={res[('A', gate)][1]} B={res[('B', gate)][1]}")
        lines.append("A SUMMARY: " + str(summary(a)))
        lines.append("B SUMMARY: " + str(summary(b)))
        if gate == "data_contract":
            ra, rb = reds(a), reds(b)
            only_a, only_b = sorted(set(ra) - set(rb)), sorted(set(rb) - set(ra))
            changed = sorted(k for k in set(ra) & set(rb) if ra[k] != rb[k])
            lines.append(f"RED lines: A {len(ra)} | B {len(rb)} | only in A {len(only_a)} | only in B {len(only_b)} | same RED line but message changed {len(changed)}")
            for k in only_a:
                lines.append(f"  only A: {k}  {ra[k]}")
            for k in only_b:
                lines.append(f"  only B: {k}  {rb[k]}")
            for k in changed:
                lines.append(f"  message changed: {k}\n      A: {ra[k]}\n      B: {rb[k]}")
        else:
            la = a.read_text(encoding="utf-8").splitlines()
            lb = b.read_text(encoding="utf-8").splitlines()
            import difflib
            d = [x for x in difflib.unified_diff(la, lb, lineterm="", n=0) if not x.startswith(("---", "+++", "@@"))]
            lines.append(f"master_tables output differences A->B: {len(d)} lines")
            lines.extend("  " + x[:230] for x in d[:40])
    txt = "\n".join(lines)
    (OUT / f"{label}_compare.txt").write_text(txt, encoding="utf-8", newline="\n")
    print(txt)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
