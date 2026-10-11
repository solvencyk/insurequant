#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""2026-10-12 follow-up to the reinsurer PL/BS re-sweep (orchestrator decisions).  Two cell-level operations on PL_breakdown.json / PL_breakdown_provenance.json:

  --withhold7 | --restore7   withhold (or put back, once the owner approves) the 7 printed-zero cells that trigger PL_YTD_COLLAPSE_TO_ZERO
                             (KR1101 2023.4Q item 17; KR1105 2023.2Q·2025.3Q, KR1103 2024.3Q·2025.3Q, KR1107 2023.3Q·2025.3Q item 21).
                             State of the removal is stored in data/_derived/reinsurer_resweep_20261012/collapse7_state.json so that restore is exact.
  --r1                       owner R1 rule (2026-10-09, covers reinsurers): adopt the latest filing's prior-year column for the 11 EXISTING cells whose own-filing value
                             differs from it (+ the 3 new 17/20 cells of the same buckets, so the bucket stays consistent).  Provenance how=latest_prior_column_R1.

  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/reinsurer_resweep_pl_followup.py <--withhold7|--restore7|--r1> [--apply]

NOTE: after `--r1 --apply` run scripts/reinsurer_resweep_pl_r1_fixhow.py once (moves the 3 NEW cells' sidecar items from the R1 entry to the disclosure_summary_pl_reinsurer entry).
값_당분기 of the following quarter is re-derived with the builder rule (Q1 = YTD; Q2/Q3 = YTD - previous YTD, None if the previous quarter is missing; Q4 row = None) ONLY when the row
currently equals that derivation (a row that does not is left alone and reported).
"""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.stdout.reconfigure(encoding="utf-8")
import bspl_granularity_load_bs as L  # noqa: E402

MASTER = ROOT / "PL_breakdown.json"
SIDECAR = ROOT / "PL_breakdown_provenance.json"
D = ROOT / "data/_derived/reinsurer_resweep_20261012"
BACKUP = ROOT / "data/_derived/reinsurer_resweep_backup_20261012"
STATE = D / "collapse7_state.json"
SEVEN = [("KR1101", "17", "2023.4Q"), ("KR1105", "21", "2023.2Q"), ("KR1105", "21", "2025.3Q"), ("KR1103", "21", "2024.3Q"),
         ("KR1103", "21", "2025.3Q"), ("KR1107", "21", "2023.3Q"), ("KR1107", "21", "2025.3Q")]
HOW_NEW = "disclosure_summary_pl_reinsurer"
HOW_R1 = "latest_prior_column_R1"
K2 = {"1": "ins_pl", "16": "other_biz", "22": "pretax", "23": "tax", "24": "net", "17": "inv_pl", "20": "op_inc", "21": "nonop_pl"}
PURE = {"KR1101", "KR1102", "KR1103", "KR1104", "KR1105", "KR1106", "KR1107", "KR1108"}


def prev_q(q):
    y, n = int(q[:4]), int(q[5])
    return None if n == 1 else f"{y}.{n - 1}Q"


def next_q(q):
    y, n = int(q[:4]), int(q[5])
    return None if n == 4 else f"{y}.{n + 1}Q"


def derived(ytd: dict, q):
    cur = ytd.get(q)
    if cur is None or q.endswith("4Q"):
        return None
    p = prev_q(q)
    if p is None:
        return cur
    pv = ytd.get(p)
    return None if pv is None else round(cur - pv, 6)


def chain(by, co, item):
    return {q: r["값"] for (c, it, q), r in by.items() if c == co and it == item and r.get("값") is not None}


def rederive(by, co, item, old_ytd, new_ytd, report):
    """for the rows of (co,item): if the row's 값_당분기 equals derived(old) set it to derived(new); else leave + report"""
    n = 0
    for q in sorted(set(old_ytd) | set(new_ytd)):
        r = by.get((co, item, q))
        if r is None:
            continue
        cur = r.get("값_당분기")
        d_old, d_new = derived(old_ytd, q), derived(new_ytd, q)
        if d_old == d_new:
            continue
        if (cur is None and d_old is None) or (cur is not None and d_old is not None and abs(cur - d_old) < 1e-6):
            r["값_당분기"] = d_new
            n += 1
            report.append(f"{co} item {item} {q}: 값_당분기 {cur} -> {d_new}")
        else:
            report.append(f"{co} item {item} {q}: 값_당분기 {cur} is not the derivation of the old values ({d_old}); left alone")
    return n


def snap(o):
    return json.dumps(o, ensure_ascii=False, sort_keys=True)


def write_back(rows, side, raw_m, raw_s):
    for p, raw in ((MASTER, raw_m), (SIDECAR, raw_s)):
        if p.read_bytes() != raw:
            raise SystemExit(f"ABORT: {p.name} changed since read -- nothing written")
    L.safe_write(SIDECAR, L.dumps(side, 1, "\r\n"))
    L.safe_write(MASTER, L.dumps(rows, 1, "\r\n"))


def backup(tag):
    d = BACKUP / tag
    d.mkdir(parents=True, exist_ok=True)
    for p in (MASTER, SIDECAR):
        if (d / p.name).exists():
            raise SystemExit(f"ABORT: backup {d / p.name} exists already")
        shutil.copy2(p, d / p.name)


def blocks_of(side):
    return {(b["company_code"], b["quarter"], b["item_block"]): b for b in side["cells"]}


# ---------------------------------------------------------------------------------------------------------------------------------- withhold / restore
def withhold7(apply):
    rows, raw_m = L.load_json_exact(MASTER, 1, "\r\n")
    side, raw_s = L.load_json_exact(SIDECAR, 1, "\r\n")
    by = {(r["원보험사코드"], str(r["항목번호"]), r["공시분기"]): r for r in rows}
    blocks = blocks_of(side)
    if STATE.exists():
        raise SystemExit("ABORT: collapse7_state.json exists (already withheld?)")
    plan = {(p["co"], p["item"], p["q"]): p for p in json.loads((D / "fill_plan.json").read_text(encoding="utf-8"))["plan"]}
    state = {"rows": [], "next_rows": [], "blocks_before": {}, "blocks_after": {}}
    for k in SEVEN:
        co, it, q = k
        r = by.get(k)
        if r is None or r["값"] != 0.0 or k not in plan:
            raise SystemExit(f"ABORT: {k} is not the loaded printed-zero cell ({r})")
        state["rows"].append(r)
    removed_keys = set(SEVEN)
    new_rows = [r for r in rows if (r["원보험사코드"], str(r["항목번호"]), r["공시분기"]) not in removed_keys]
    by2 = {(r["원보험사코드"], str(r["항목번호"]), r["공시분기"]): r for r in new_rows}
    report = []
    for co, it in sorted({(c, i) for c, i, _ in SEVEN}):
        old = chain(by, co, it)
        for r in new_rows:
            pass
        new = {q: v for q, v in old.items() if (co, it, q) not in removed_keys}
        before = {q: snap(by2[(co, it, q)]) for q in new if (co, it, q) in by2}
        rederive(by2, co, it, old, new, report)
        for q in new:
            r = by2[(co, it, q)]
            if snap(r) != before[q]:
                state["next_rows"].append({"key": [co, it, q], "before": json.loads(before[q]), "after": r})
    # sidecar: drop the item from its entry
    for co, it, q in SEVEN:
        b = blocks[(co, q, "income_statement")]
        key = f"{co}|{q}"
        if key not in state["blocks_before"]:
            state["blocks_before"][key] = json.loads(snap(b))
        for e in list(b["source_files"]):
            if e.get("how") == HOW_NEW and int(it) in e["items"]:
                e["items"] = [i for i in e["items"] if i != int(it)]
                if isinstance(e.get("printed"), dict):
                    e["printed"].pop(it, None)
                if not e["items"]:
                    b["source_files"].remove(e)
        b["published_items"] -= 1
        state["blocks_after"][key] = json.loads(snap(b))
    print(f"withhold: remove {len(SEVEN)} rows; {len(state['next_rows'])} following rows re-derived; sidecar blocks touched {len(state['blocks_before'])}")
    for ln in report:
        print("  ", ln)
    if not apply:
        print("dry-run")
        return
    backup("withhold7")
    side["merge_note_20261012_withhold7"] = ("재보사 인쇄된 0 7칸(PL_YTD_COLLAPSE_TO_ZERO) 보류 -- owner 등재 전까지 마스터에서 뺐다(조정자 결정 2026-10-12). 복원: "
                                             "scripts/reinsurer_resweep_pl_followup.py --restore7 --apply (상태 data/_derived/reinsurer_resweep_20261012/collapse7_state.json).")
    write_back(new_rows, side, raw_m, raw_s)
    STATE.write_text(json.dumps(state, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    chk = json.loads(MASTER.read_bytes().decode("utf-8"))
    ci = {(r["원보험사코드"], str(r["항목번호"]), r["공시분기"]) for r in chk}
    if any(k in ci for k in SEVEN) or len(chk) != len(rows) - 7:
        raise SystemExit("VERIFY FAILED")
    print(f"APPLIED withhold: rows {len(rows)} -> {len(chk)}")


def restore7(apply):
    state = json.loads(STATE.read_text(encoding="utf-8"))
    rows, raw_m = L.load_json_exact(MASTER, 1, "\r\n")
    side, raw_s = L.load_json_exact(SIDECAR, 1, "\r\n")
    by = {(r["원보험사코드"], str(r["항목번호"]), r["공시분기"]): r for r in rows}
    blocks = blocks_of(side)
    for r in state["rows"]:
        if (r["원보험사코드"], str(r["항목번호"]), r["공시분기"]) in by:
            raise SystemExit("ABORT: a withheld row is already back")
    for n in state["next_rows"]:
        cur = by.get(tuple(n["key"]))
        if cur is None or snap(cur) != snap(n["after"]):
            raise SystemExit(f"ABORT: following row {n['key']} changed since the withhold")
    for key, after in state["blocks_after"].items():
        co, q = key.split("|")
        if snap(blocks[(co, q, "income_statement")]) != snap(after):
            raise SystemExit(f"ABORT: sidecar block {key} changed since the withhold")
    print(f"restore: +{len(state['rows'])} rows, {len(state['next_rows'])} following rows back, {len(state['blocks_before'])} sidecar blocks back")
    if not apply:
        print("dry-run")
        return
    backup("restore7")
    for n in state["next_rows"]:
        by[tuple(n["key"])].update(n["before"])
    for key, before in state["blocks_before"].items():
        co, q = key.split("|")
        b = blocks[(co, q, "income_statement")]
        b.clear()
        b.update(before)
    side.pop("merge_note_20261012_withhold7", None)
    write_back(rows + state["rows"], side, raw_m, raw_s)
    STATE.rename(STATE.with_name("collapse7_state.restored.json"))
    print("APPLIED restore")


# ---------------------------------------------------------------------------------------------------------------------------------- R1
def r1(apply):
    rows, raw_m = L.load_json_exact(MASTER, 1, "\r\n")
    side, raw_s = L.load_json_exact(SIDECAR, 1, "\r\n")
    by = {(r["원보험사코드"], str(r["항목번호"]), r["공시분기"]): r for r in rows}
    blocks = blocks_of(side)
    dec = json.loads((D / "pl_decided.json").read_text(encoding="utf-8"))
    cl = json.loads((D / "r1_conflict_lists.json").read_text(encoding="utf-8"))
    existing = [c for c in cl["r1_conflicts_on_existing_master_cells"] if c["side"] == "master==own"]
    new_items = []
    buckets = {(c["co"], c["q"]) for c in existing}
    for c in cl["conflicts_on_new_cells_resolved_by_anchor_rule"]:
        if (c["co"], c["q"]) in buckets:
            new_items.append(c)
    skipped = [c for c in existing if c["co"] not in PURE]
    existing = [c for c in existing if c["co"] in PURE]
    if len(existing) != 11:
        raise SystemExit(f"ABORT: expected 11 existing cells, got {len(existing)}")
    for c in existing:
        for k in (("KR1102", "23"),):
            pass
    plan_old = {(p["co"], p["item"], p["q"]): p for p in json.loads((D / "fill_plan.json").read_text(encoding="utf-8"))["plan"]}
    changes = []     # (co, item, q, old, new, later_info, kind)
    def later_info(co, q, item):
        nq = f"{int(q[:4]) + 1}.{q[5]}Q"
        d = dec[f"{co}|{nq}"]
        k = K2[item]
        v = d["chosen"][k][1]
        raw = d["raw"][k][1]
        pdf = None
        inv = json.loads((D / "inventory.json").read_text(encoding="utf-8"))
        pdf = inv[f"{co}|{nq}"]["pdf"][0].replace("\\", "/")
        pdf = pdf[pdf.index("data/disclosure/"):]
        return {"val": round(v * d["scale"], 6), "raw": raw, "page": d["page"], "unit": "억원" if d["scale"] == 100.0 else "백만원", "file": pdf, "later_q": nq}
    for c in existing:
        k = (c["co"], c["item"], c["q"])
        li = later_info(c["co"], c["q"], c["item"])
        if abs(li["val"] - c["later"]) > 1e-6:
            raise SystemExit(f"ABORT: later value mismatch {k}: {li['val']} vs {c['later']}")
        if abs(by[k]["값"] - c["master"]) > 1e-6:
            raise SystemExit(f"ABORT: master guard {k}: {by[k]['값']} vs {c['master']}")
        changes.append((k, by[k]["값"], li["val"], li, "existing"))
    for c in new_items:
        k = (c["co"], c["item"], c["q"])
        li = later_info(c["co"], c["q"], c["item"])
        if abs(li["val"] - c["later"]) > 1e-6 or abs(by[k]["값"] - c["own"]) > 1e-6:
            raise SystemExit(f"ABORT: new-cell guard {k}")
        changes.append((k, by[k]["값"], li["val"], li, "new"))
    print(f"R1: existing {len([x for x in changes if x[4]=='existing'])} (skipped non-reinsurer: {len(skipped)}) + new-in-bucket {len([x for x in changes if x[4]=='new'])}")
    for k, o, n, li, kind in changes:
        print(f"   {kind:8s} {k} {o} -> {n}  (later filing {li['later_q']} p{li['page']} printed {li['raw']} {li['unit']})")
    # apply to a copy
    snap_rows = {k: snap(v) for k, v in by.items()}
    old_ytd = {}
    for (co, it) in {(k[0], k[1]) for k, *_ in changes}:
        old_ytd[(co, it)] = chain(by, co, it)
    for k, o, n, li, kind in changes:
        by[k]["값"] = n
    report = []
    for (co, it), old in old_ytd.items():
        rederive(by, co, it, old, chain(by, co, it), report)
    for ln in report:
        print("   ", ln)
    # sidecar
    for k, o, n, li, kind in changes:
        co, it, q = k
        b = blocks[(co, q, "income_statement")]
        for e in list(b["source_files"]):
            if int(it) in e["items"] and e.get("how") in ("disclosure_summary_pl", HOW_NEW):
                e["items"] = [i for i in e["items"] if i != int(it)]
                if isinstance(e.get("printed"), dict):
                    e["printed"].pop(it, None)
                if not e["items"]:
                    b["source_files"].remove(e)
        ent = next((e for e in b["source_files"] if e.get("how") == HOW_R1 and e["file"] == li["file"]), None)
        if ent is None:
            ent = {"file": li["file"], "how": HOW_R1, "items": [], "page": li["page"], "printed": {}, "unit": li["unit"], "column": "prior_year_column_of_later_filing",
                   "later_filing_quarter": li["later_q"], "replaced_values": {}}
            b["source_files"].append(ent)
        ent["items"] = sorted(ent["items"] + [int(it)])
        ent["printed"][it] = li["raw"]
        ent["replaced_values"][it] = o
    changed_rows = [k for k, v in by.items() if snap(v) != snap_rows[k]]
    print(f"rows changed in total: {len(changed_rows)} (primary {len(changes)}; re-derived 값_당분기 on {len(changed_rows) - len(changes)} other rows/fields)")
    if not apply:
        print("dry-run")
        return
    backup("r1")
    side["merge_note_20261012_r1"] = ("owner R1(2026-10-09, 재보사 포함): 최신 공시의 전기 칸 채택 -- 기존 11칸(스위스리 2023.2Q 22·24 · 2025.1Q·2Q 16 · 제네럴 2023.2Q 22·24 · 2023.3Q 24 · RGA 2023.3Q 1·22·23·24) + "
                                      "같은 버킷의 새 17·20 3칸(제네럴 2023.3Q 17, RGA 2023.3Q 17·20)을 이듬해 같은 분기 공시의 전년동기 열로 교체. how=latest_prior_column_R1, 옛 값은 replaced_values. "
                                      "재현 scripts/reinsurer_resweep_pl_followup.py --r1")
    write_back(rows, side, raw_m, raw_s)
    chk = json.loads(MASTER.read_bytes().decode("utf-8"))
    ci = {(r["원보험사코드"], str(r["항목번호"]), r["공시분기"]): r for r in chk}
    now_changed = [k for k, s in snap_rows.items() if snap(ci[k]) != s]
    if set(now_changed) != set(changed_rows) or len(chk) != len(rows):
        raise SystemExit("VERIFY FAILED")
    print(f"APPLIED R1: {len(changes)} primary cells, {len(now_changed)} rows changed in total")


if __name__ == "__main__":
    apply = "--apply" in sys.argv
    if "--withhold7" in sys.argv:
        withhold7(apply)
    elif "--restore7" in sys.argv:
        restore7(apply)
    elif "--r1" in sys.argv:
        r1(apply)
    else:
        raise SystemExit(__doc__)
