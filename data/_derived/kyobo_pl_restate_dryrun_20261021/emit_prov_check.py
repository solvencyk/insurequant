"""Read-only: is the KR0073 PL provenance reproducible by scripts/emit_pl_provenance.py, and what would the emitter write for the post-apply files?

Uses the sandbox copy (make_emit_copy.py) run as a subprocess with EMIT_PL_SRC / EMIT_PL_OVR / EMIT_PL_OUT pointing at temp files in tmp_emit/.
  A  live KR0073 rows + live gold      -> compare with the LIVE PL_breakdown_provenance.json   (does the emitter reproduce today's sidecar for this company?)
  B  candidate KR0073 rows + cand gold -> compare with the hand-edited candidate sim/prov_pl_cand.json (what the emitter itself would emit after the apply)
"""
import json
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
TMP = HERE / "tmp_emit"
TMP.mkdir(exist_ok=True)
PY = "C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe"
sys.stdout.reconfigure(encoding="utf-8")
CODE = "KR0073"


def kr_rows(path):
    rows = json.loads(Path(path).read_text(encoding="utf-8"))
    return [r for r in rows if r["원보험사코드"] == CODE]


def run(tag, rows, gold_path):
    src = TMP / f"src_{tag}.json"
    src.write_text(json.dumps(rows, ensure_ascii=False), encoding="utf-8", newline="\n")
    out = TMP / f"prov_{tag}.json"
    env = dict(os.environ, EMIT_PL_SRC=str(src), EMIT_PL_OVR=str(gold_path), EMIT_PL_OUT=str(out), PYTHONIOENCODING="utf-8")
    p = subprocess.run([PY, str(HERE / "emit_pl_provenance_sandbox_copy.py")], cwd=str(ROOT), env=env, capture_output=True, text=True, encoding="utf-8", errors="replace")
    (TMP / f"emit_{tag}.log").write_text((p.stdout or "") + "\n--- stderr ---\n" + (p.stderr or ""), encoding="utf-8", newline="\n")
    print(f"[{tag}] rc={p.returncode} -> {out.name}")
    return json.loads(out.read_text(encoding="utf-8")) if out.exists() else None


def cells_of(doc, quarters=None):
    return {(c["company_code"], c["quarter"], c["item_block"]): c for c in doc["cells"]
            if c["company_code"] == CODE and (quarters is None or c["quarter"] in quarters)}


def norm(c):
    d = dict(c)
    d["source_files"] = [dict(e) for e in c.get("source_files", [])]
    return d


def diff(a, b, label_a, label_b):
    out = []
    for k in sorted(set(a) | set(b), key=lambda x: (x[1], x[2])):
        if k not in a or k not in b:
            out.append(f"  {k}: only in {label_a if k in a else label_b}")
            continue
        ca, cb = norm(a[k]), norm(b[k])
        if ca == cb:
            continue
        keys = sorted(set(ca) | set(cb))
        parts = []
        for f in keys:
            if ca.get(f) != cb.get(f):
                parts.append(f"{f}: {label_a}={ca.get(f)!r} | {label_b}={cb.get(f)!r}")
        out.append(f"  {k[1]} {k[2]}:\n      " + "\n      ".join(parts))
    return out


live_prov = json.loads((ROOT / "PL_breakdown_provenance.json").read_text(encoding="utf-8"))
cand_prov = json.loads((HERE / "sim" / "prov_pl_cand.json").read_text(encoding="utf-8"))
QS = {"2023.1Q", "2023.2Q", "2023.3Q", "2023.4Q", "2024.1Q", "2024.2Q"}

docA = run("A_live", kr_rows(ROOT / "PL_breakdown.json"), ROOT / "data" / "_gold" / "user_pl_cells.json")
docB = run("B_cand", kr_rows(HERE / "sim" / "cand_pl.json"), HERE / "sim" / "gold_pl_cand.json")
lines = []
a_all, l_all = cells_of(docA), cells_of(live_prov)
d = diff(l_all, a_all, "live", "emitter")
lines.append(f"A. emitter(live KR0073 rows + live gold) vs LIVE sidecar: {len(l_all)} live KR0073 blocks, {len(a_all)} emitted, differing blocks = {len(d)}")
lines += d[:60]
b6, c6 = cells_of(docB, QS), cells_of(cand_prov, QS)
d2 = diff(c6, b6, "handedit", "emitter")
lines.append("")
lines.append(f"B. emitter(candidate KR0073 rows + candidate gold) vs hand-edited candidate sidecar, 6 target quarters x 2 blocks: {len(c6)} vs {len(b6)}, differing blocks = {len(d2)}")
lines += d2[:60]
b_all = cells_of(docB)
l_rest = {k: v for k, v in l_all.items() if k[1] not in QS}
b_rest = {k: v for k, v in b_all.items() if k[1] not in QS}
d3 = diff(l_rest, b_rest, "live", "emitter")
lines.append("")
lines.append(f"C. KR0073 blocks OUTSIDE the 6 target quarters: live sidecar vs emitter(candidate) -> differing blocks = {len(d3)} (must equal the A-differences, i.e. nothing new)")
(HERE / "emit_prov_check.txt").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
print("\n".join(lines))
