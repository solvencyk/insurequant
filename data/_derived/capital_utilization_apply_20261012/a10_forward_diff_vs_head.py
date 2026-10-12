"""a10: field-level diff of kics_forward_capital.json (working tree) vs HEAD - proves the forward re-run changed
nothing but the `confidence` blocks (read-only). Also checks templates/forward_capital_latest.json == root content.

Run (repo root):
  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe data/_derived/capital_utilization_apply_20261012/a10_forward_diff_vs_head.py
Output: a10_forward_diff_vs_head.txt (same folder)
"""
from __future__ import annotations

import io
import json
import subprocess
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]


def walk(a, b, path, out):
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b)):
            walk(a.get(k, "<absent>"), b.get(k, "<absent>"), f"{path}.{k}", out)
    elif isinstance(a, list) and isinstance(b, list) and len(a) == len(b) and not all(isinstance(x, str) for x in a + b):
        for i, (x, y) in enumerate(zip(a, b)):
            walk(x, y, f"{path}[{i}]", out)
    elif a != b:
        out.append((path, a, b))


def main() -> int:
    head = json.loads(subprocess.run(["git", "show", "HEAD:kics_forward_capital.json"], cwd=REPO,
                                     capture_output=True, check=True).stdout.decode("utf-8"))
    new = json.loads((REPO / "kics_forward_capital.json").read_text(encoding="utf-8"))
    tmpl = json.loads((REPO / "templates" / "forward_capital_latest.json").read_text(encoding="utf-8"))
    hk = {r.get("insurer_code"): r for r in head}
    nk = {r.get("insurer_code"): r for r in new}
    out = [f"rows HEAD={len(head)} new={len(new)} · same codes={set(hk) == set(nk)} · same order="
           f"{[r.get('insurer_code') for r in head] == [r.get('insurer_code') for r in new]} · templates==root: {tmpl == new}"]
    diffs = []
    for code in sorted(set(hk) | set(nk)):
        walk(hk.get(code), nk.get(code), code, diffs)
    outside = [d for d in diffs if ".confidence." not in d[0] and not d[0].endswith(".confidence")]
    out.append(f"differing leaf fields: {len(diffs)} · outside `confidence`: {len(outside)}")
    for p, a, b in outside:
        out.append(f"  OUTSIDE {p}: {a!r} -> {b!r}")
    levels = [(p, a, b) for p, a, b in diffs if p.endswith(".confidence.level")]
    out.append(f"confidence.level changes: {len(levels)}")
    for p, a, b in levels:
        out.append(f"  {p}: {a} -> {b}")
    txt = "\n".join(out) + "\n"
    (HERE / "a10_forward_diff_vs_head.txt").write_text(txt, encoding="utf-8")
    print(txt)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
