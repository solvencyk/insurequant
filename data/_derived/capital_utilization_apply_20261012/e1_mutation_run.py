"""e1: mutation run - temporarily break scripts/capital_utilization_rules.py in two ways, run the unit test file,
and restore the original byte-for-byte (sha256 checked). Proves the tests actually fire.

  M1  R1 disabled (gross printing never detected)          -> expect failures
  M2  registry ignored (no supplementary-type exclusion)   -> expect failures
  M3  R4 branch removed (falls through to R5)              -> expect failures

Run (repo root):
  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe data/_derived/capital_utilization_apply_20261012/e1_mutation_run.py
Output: e1_mutation_run.txt (same folder)
"""
from __future__ import annotations

import hashlib
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
TARGET = REPO / "scripts" / "capital_utilization_rules.py"
PY = sys.executable
MUTATIONS = [
    ("M1 R1 disabled", "gross = l49 is not None and l49 > TOL and close(p0, i3)", "gross = False"),
    ("M2 registry ignored", 't2_amt = sum(((s.get("amount_eok") or 0.0) for s in secs if s.get("type") == "tier2"), 0.0)',
     "t2_amt = 0.0"),
    ("M3 R4 removed", "elif s54 > TOL and close(p1, p0 - h53):", "elif False:"),
]


def main() -> int:
    original = TARGET.read_bytes()
    h0 = hashlib.sha256(original).hexdigest()
    out = [f"target sha256 before: {h0}"]
    try:
        for name, old, new in MUTATIONS:
            src = original.decode("utf-8")
            assert src.count(old) == 1, (name, src.count(old))
            TARGET.write_bytes(src.replace(old, new).encode("utf-8"))
            p = subprocess.run([PY, "-m", "pytest", "-q", "-p", "no:cacheprovider",
                                "tests/unit/test_capital_utilization_rules.py"],
                               cwd=REPO, capture_output=True, text=True, encoding="utf-8", errors="replace")
            last = [ln for ln in p.stdout.splitlines() if "passed" in ln or "failed" in ln][-1:]
            failed = [ln.split(" - ")[0] for ln in p.stdout.splitlines() if ln.startswith("FAILED")]
            out.append(f"{name}: exit={p.returncode} {last} -> killed={p.returncode != 0}")
            out.extend(f"    {f}" for f in failed[:12])
    finally:
        TARGET.write_bytes(original)
    h1 = hashlib.sha256(TARGET.read_bytes()).hexdigest()
    out.append(f"target sha256 after restore: {h1} (identical={h0 == h1})")
    txt = "\n".join(out) + "\n"
    (HERE / "e1_mutation_run.txt").write_text(txt, encoding="utf-8")
    print(txt)
    return 0 if h0 == h1 else 1


if __name__ == "__main__":
    raise SystemExit(main())
