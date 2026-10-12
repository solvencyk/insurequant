# -*- coding: utf-8 -*-
"""Attribute the regenerated panel diffs: rebuild panel_compare / panel_csm_combo from the masters as committed at c76921ca
(= the parent of parser-ifrs17 b8c37fff, old NB file) in a temp tree, then compare
  A = HEAD panel on disk  vs  rebuild@c76921ca   (was the committed panel fresh before b8c37fff? any prior staleness)
  B = rebuild@c76921ca    vs  regenerated panel in the working tree (= effect of b8c37fff + the NB regeneration)
Output: z2_attribute_panels.txt"""
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
REV = "c76921ca"
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(HERE))

FILES = {
    "compare": ["kics_disclosure.json", "data/company_segment.json", "CSM_waterfall.json", "NB_CSM_multiple.json", "PL_breakdown.json",
                "IFRS17_BS.json", "data/persistency/master_persistency.json", "data/loss_ratio/master_loss_ratio.json"],
    "combo": ["insurance_liability_portfolio.json", "CSM_waterfall.json", "IFRS17_BS.json"],
}
SCRIPT = {"compare": "scripts/viz_build_compare_panel.py", "combo": "scripts/viz_build_csm_combo_panel.py"}
OUT = {"compare": "data/compare/panel_compare.json", "combo": "data/csm_combo/panel_csm_combo.json"}


def git_show(rev, path):
    r = subprocess.run(["git", "show", f"{rev}:{path}"], capture_output=True, cwd=ROOT)
    if r.returncode:
        raise SystemExit(f"git show {rev}:{path} failed")
    return r.stdout


def leaf(a, b, p, out):
    if type(a) != type(b):
        out.append(p)
    elif isinstance(a, dict):
        for k in sorted(set(a) | set(b)):
            if k not in a or k not in b:
                out.append(p + "/" + str(k))
            else:
                leaf(a[k], b[k], p + "/" + str(k), out)
    elif isinstance(a, list):
        if len(a) != len(b):
            out.append(p + "[len]")
        for i, (x, y) in enumerate(zip(a, b)):
            leaf(x, y, p + f"[{i}]", out)
    elif a != b:
        out.append(p)


lines = []
for key in ("compare", "combo"):
    tmp = Path(tempfile.mkdtemp(prefix=f"rebuild_{key}_"))
    try:
        for rel in FILES[key]:
            dst = tmp / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_bytes(git_show(REV, rel))
        # combo reads two extra sidecar paths named inside the builder: copy whatever exists at REV
        for extra in ("data/_derived/ilp_includes_lic.json", "data/_derived/ilp_restated_comparative.json"):
            try:
                (tmp / extra).parent.mkdir(parents=True, exist_ok=True)
                (tmp / extra).write_bytes(git_show(REV, extra))
            except SystemExit:
                pass
        s = tmp / SCRIPT[key]
        s.parent.mkdir(parents=True, exist_ok=True)
        s.write_bytes((ROOT / SCRIPT[key]).read_bytes())
        r = subprocess.run([sys.executable, "-X", "utf8", str(s)], capture_output=True, cwd=tmp)
        if r.returncode:
            lines.append(f"[{key}] rebuild@{REV} FAILED: {r.stderr.decode('utf-8', 'replace')[-300:]}")
            continue
        rebuilt = json.loads((tmp / OUT[key]).read_text(encoding="utf-8"))
        head_panel = json.loads(git_show("HEAD", OUT[key]).decode("utf-8"))
        work = json.loads((ROOT / OUT[key]).read_text(encoding="utf-8"))
        a, b = [], []
        leaf(head_panel, rebuilt, "", a)
        leaf(rebuilt, work, "", b)
        lines.append(f"[{key}] A: HEAD-on-disk vs rebuild@{REV}: {len(a)} differing leaves  (0 = the committed panel was fresh before b8c37fff)")
        lines.append(f"[{key}] B: rebuild@{REV} vs regenerated now: {len(b)} differing leaves  (= effect of b8c37fff + NB regeneration)")
        for p in a[:15]:
            lines.append(f"      A {p}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
(HERE / "z2_attribute_panels.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
print("\n".join(lines))
