# -*- coding: utf-8 -*-
"""Read-only simulation (validation, 2026-10-23): item-23 constructive coverage before / after the planned KDB load,
over EVERY company x quarter bucket of the live PL master.  Nothing in the repo is written.

States
  pre  = live PL_breakdown.json / CSM_waterfall.json (the tree as it is now: KDB not loaded)
  post = pre + the 65 PL (값) and 20 CSM cells of kr0072_kdb/e23_plan_kdb_final.json applied in memory

For each state and each manifest item (BLIND | GUARDED) the test's own CONSTRUCTIVE mutation and blocking signature are
used (imported from tests/test_rule_coverage_manifest.py), and the NEW findings are listed per axis.
For item 23 it also enumerates the bucket universe in which the mutation can change anything at all:
master item23 != round(22 - 24, 6) (an override cell; elsewhere the mutation is a no-op by construction).
"""
from __future__ import annotations

import contextlib
import copy
import io
import json
import sys
from pathlib import Path

ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
HERE = Path(__file__).resolve().parent
PLAN = ROOT / "data/_derived/remaining_20261022/e23_d1_d3/kr0072_kdb/e23_plan_kdb_final.json"
sys.path.insert(0, str(ROOT / "tests"))
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

import test_rule_coverage_manifest as M  # noqa: E402

V = M._vmt()
ITEMS = sorted(set(M.PL_CONSTRUCTIVE_BLIND) | set(M.PL_CONSTRUCTIVE_GUARDED))
ONLY = [int(a) for a in sys.argv[1:]]
if ONLY:
    ITEMS = [i for i in ITEMS if i in ONLY]

out = open(HERE / ("s01_sim_item23.txt" if not ONLY else f"s01_sim_items_{'_'.join(map(str, ONLY))}.txt"),
           "w", encoding="utf-8")


def W(*a):
    s = " ".join(str(x) for x in a)
    out.write(s + "\n")
    out.flush()


pl_rows = json.loads((ROOT / "PL_breakdown.json").read_text(encoding="utf-8"))
wf_rows = json.loads((ROOT / "CSM_waterfall.json").read_text(encoding="utf-8"))
plan = json.loads(PLAN.read_text(encoding="utf-8"))


def apply_plan(pl_rows, wf_rows):
    pl2, wf2 = copy.deepcopy(pl_rows), copy.deepcopy(wf_rows)
    ipl = {(r["원보험사코드"], r["공시분기"], r["항목번호"]): r for r in pl2}
    iwf = {(r["원보험사코드"], r["공시분기"], r["항목번호"]): r for r in wf2}
    n_pl = n_wf = 0
    bad = []
    for b in plan["buckets"]:
        for c in b["cells"]:
            r = ipl.get((c["code"], c["quarter"], c["item"]))
            if r is None:
                bad.append(("PL missing row", c["quarter"], c["item"]))
                continue
            old = r.get("값")
            if not ((old is None and c["old"] is None) or (old is not None and c["old"] is not None
                                                            and abs(old - c["old"]) < 1e-9)):
                bad.append(("PL old != live", c["quarter"], c["item"], old, c["old"]))
            r["값"] = c["new"]
            n_pl += 1
    for b in plan["csm_buckets"]:
        for c in b["cells"]:
            r = iwf.get((c["code"], c["quarter"], c["item"]))
            if r is None:
                bad.append(("CSM missing row", c["quarter"], c["item"]))
                continue
            old = r.get("값")
            if not ((old is None and c["old"] is None) or (old is not None and c["old"] is not None
                                                            and abs(old - c["old"]) < 1e-9)):
                bad.append(("CSM old != live", c["quarter"], c["item"], old, c["old"]))
            r["값"] = c["new"]
            n_wf += 1
    return pl2, wf2, n_pl, n_wf, bad


def wf_index(rows):
    idx = {}
    for r in rows:
        idx.setdefault((r["원수사명"], r["공시분기"]), {})[V.norm(r["항목명"])] = r["값"]
    return idx


def tax_universe(rows, tag):
    """Buckets where the item-23 mutation can move anything: master 23 != round(22 - 24, 6)."""
    by = {}
    for r in rows:
        by.setdefault((r["원보험사코드"], r["원수사명"], r["공시분기"]), {})[r["항목번호"]] = r.get("값")
    n_all = n_23 = 0
    moved, eq2224 = [], []
    for k, m in sorted(by.items()):
        n_all += 1
        v22, v23, v24 = m.get(22), m.get(23), m.get(24)
        if None in (v22, v24) or v23 is None:
            continue
        n_23 += 1
        rec = round(v22 - v24, 6)
        if abs(rec - v23) > 1e-6:
            moved.append((k[0], k[2], v22, v24, v23, rec))
        if v22 == v24:
            eq2224.append((k[0], k[2], v22, v23))
    W(f"[{tag}] buckets={n_all} with 22/23/24 present={n_23}")
    W(f"[{tag}] buckets where master item23 != round(22-24,6) (the ONLY cells the item-23 mutation changes): "
      f"{len(moved)}")
    for x in moved:
        W(f"    {x[0]} {x[1]}: 22={x[2]} 24={x[3]} master23={x[4]} recomputed={x[5]}")
    W(f"[{tag}] buckets with 22 == 24 exactly: {len(eq2224)} {eq2224}")


def run_state(tag, rows, wf_rows_state):
    wf = wf_index(wf_rows_state)
    # validate_data_contract.Env reads CSM_waterfall.json with its own load_long (only "pl" is injected by the
    # test signature) -> serve the state's waterfall to it as well, so pre/post differ only by the plan.
    import validate_data_contract as G
    _orig = G.load_long
    G.load_long = lambda p, _o=_orig, _wf=wf: _wf if str(p).endswith("CSM_waterfall.json") else _o(p)
    extra_lob, unknown_hyphen = V.load_pl_extra_lob(V.PL_PATH)
    with contextlib.redirect_stdout(io.StringIO()):
        base = M._pl_blocking_signature(rows, wf, extra_lob, unknown_hyphen)
    res = {}
    for item in ITEMS:
        mutated, n = M._pl_mutate_constructive(rows, item)
        with contextlib.redirect_stdout(io.StringIO()):
            after = M._pl_blocking_signature(mutated, wf, extra_lob, unknown_hyphen)
        new = {ax: sorted(after[ax] - base[ax]) for ax in base}
        det = {ax: v for ax, v in new.items() if v}
        res[item] = det
        decl = "BLIND" if item in M.PL_CONSTRUCTIVE_BLIND else "GUARDED"
        ok = (not det) if decl == "BLIND" else bool(det)
        W(f"[{tag}] item{item:>2} ({M.PL_ITEM_NAME[item]}) declared={decl} injected={n} "
          f"detected_axes={ {k: len(v) for k, v in det.items()} } -> {'OK' if ok else 'MISMATCH'}")
        if item == 23:
            for ax, v in det.items():
                for f in v:
                    W(f"      new {ax}: {f}")
    G.load_long = _orig
    return res


W("== plan apply (in memory) ==")
pl_post, wf_post, n_pl, n_wf, bad = apply_plan(pl_rows, wf_rows)
W(f"PL cells applied={n_pl} CSM cells applied={n_wf} old-value mismatches={bad}")
tax_universe(pl_rows, "pre")
tax_universe(pl_post, "post")
W("== constructive mutation, pre (live tree) ==")
pre = run_state("pre", pl_rows, wf_rows)
W("== constructive mutation, post (live + KDB plan) ==")
post = run_state("post", pl_post, wf_post)
W("== items whose detected set differs pre vs post ==")
for it in ITEMS:
    if pre[it] != post[it]:
        W(f"item{it}: pre={ {k: len(v) for k, v in pre[it].items()} } post={ {k: len(v) for k, v in post[it].items()} }")
        for ax in sorted(set(pre[it]) | set(post[it])):
            a, b = set(map(tuple, pre[it].get(ax, []))), set(map(tuple, post[it].get(ax, [])))
            if a - b:
                W(f"    lost  {ax}: {sorted(a - b)}")
            if b - a:
                W(f"    gained {ax}: {sorted(b - a)}")
W("DONE")
out.close()
print("done")
