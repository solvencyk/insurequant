"""s6_verdicts.py -- step 6 (READ-ONLY).  Decision-table verdicts per (company, quarter) block + final exception classification.

Decision table (coordinator message, owner clarification 2026-10-12) -- both candidates (current master value vs latest prior-column value)
are evaluated with the SAME rule set (the real gate, run on a temporary candidate master):
    latest closes + current closes -> LATEST if the values differ (true restatement); no change if equal
    latest closes + current fails  -> LATEST (the exception is resolved)
    latest fails  + current closes -> KEEP CURRENT (owner principle)
    both fail                      -> KEEP CURRENT and list
    cells no rule covers           -> LATEST FIRST, flagged as rule blind spot
"closes" = no RED finding in the block (raw findings; a documented exception does NOT count as closing), no new RED in the neighbouring
quarters (cross-period checks), no new RED on any other gate axis.  Exemption-machinery signals (pin drift / inert registration) are NOT rule
failures: they are reported as "registry action".
Ticket categories on top: gold conflict / completeness insufficient / rule blind spot / adoption candidate / keep current (+ list).
"""
import csv
import re
import sys
from collections import Counter, defaultdict

sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/kics_latest_prior_precedence_dryrun_20261012")
from lib_dry import *  # noqa: F401,F403,E402
import validate_kics_disclosure as vkd  # noqa: E402

utf8_stdout()
APPLIERS = set(vkd._TRANSITION_APPLIERS)

blocks = {(b["code"], b["quarter"]): b for b in read_json(OUT / "conflict_blocks.json")}
evals = {}
for ln in (OUT / "block_eval.jsonl").read_text(encoding="utf-8").splitlines():
    if ln.strip():
        r = json.loads(ln)
        evals[r["id"]] = r                     # last record per id wins
cov = read_json(OUT / "cell_coverage.json")
sub_path = OUT / "subitem_match_pdf.json"
sub = {(r["code"], r["quarter"]): r for r in read_json(sub_path)} if sub_path.exists() else {}
ccomp = {(r["code"], r["quarter"]): r for r in read_json(OUT / "core_completeness.json")}
dc_path = OUT / "datacontract_eval.jsonl"
dcev = {}
if dc_path.exists():
    for ln in dc_path.read_text(encoding="utf-8").splitlines():
        if ln.strip():
            r = json.loads(ln)
            dcev[r["id"]] = r
inv = read_json(OUT / "exceptions_inventory_base.json")

# ------------------------------------------------------------------ owner gold
gold_cells = set()
g1 = read_json(REPO / "data" / "_gold" / "user_kics_cells.json")["cells"]
for code, byq in g1.items():
    for q, byitem in byq.items():
        for it, flds in byitem.items():
            for fld in flds:
                gold_cells.add((code, q, int(it), fld))
g2 = read_json(REPO / "data" / "_gold" / "kr0010_user_cells.json")
for q, byitem in g2.items():
    if re.match(r"\d{4}\.\dQ$", q):
        for it in byitem:
            gold_cells.add(("KR0010", q, int(it), "값"))

# ------------------------------------------------------------------ items an exception is about
RULE_ITEMS = {
    "2_tier1_bridge": {2, 4, 12, 13, 47, 48, 49}, "3_tier2_composition": {3, 47, 48, 49, 13}, "47_tier2_census": {47, 48, 49},
    "50_tfi_tier_split": {50, 51, 52, 1}, "51_tfi_tier2_composition": {51, 47, 48, 49}, "룰2": {4, 5, 6, 7, 8, 9, 10, 11},
    "룰4": {15, 17, 18, 19, 20, 21}, "룰5": {14, 15, 22, 23}, "룰6": {16, 15, 17, 18, 19, 20, 21},
    "8_life": {17, 29, 30, 31, 32, 33, 34, 35}, "19_market": {19, 36, 37, 38, 39, 40}, "36_irr": {36, 41, 42, 43, 44, 45, 46},
}
CORE = set(range(1, 27))


def involved_items(row):
    s = set()
    try:
        s |= {int(x) for x in str(row.get("items_involved", "")).split(";") if x.strip().isdigit()}
    except ValueError:
        pass
    for rule in str(row.get("rules", "")).split(";"):
        base = rule.replace("_post", "").replace("룰", "룰")
        for k, v in RULE_ITEMS.items():
            if base.startswith(k) or base == k:
                s |= v
    return s


# ------------------------------------------------------------------ decision per conflict block
def rule_of(key):
    return key.split("|", 2)[2]


def decide(ev, blk):
    cur_red = sorted({rule_of(k) for k in ev["base_bucket_red"]})
    lat_red = sorted({rule_of(k) for k in ev["cand_bucket_red"]})
    near_new = [c for c in ev["neighbour_changes"] if c[2] and c[2][0] == "RED" and not (c[1] and c[1][0] == "RED")]
    other_new = [c for c in ev["other_changes"] if c[2] and c[2][0] == "RED" and not (c[1] and c[1][0] == "RED")]
    new_extra = ev["new_extra_red"]
    lat_closes = (not lat_red) and not near_new and not other_new and not new_extra
    cur_closes = not cur_red
    resolved = sorted(set(cur_red) - set(lat_red))
    introduced = sorted(set(lat_red) - set(cur_red))
    differs = bool(blk["diffs"])
    # blind spot: every changed 전(값) cell is engine-blind AND no finding of the bucket/neighbours moved
    val_cells = [k for k in cov if k.startswith(f"{blk['code']}|{blk['quarter']}|") and k.endswith("|값")]
    changed_items = {d["item"] for d in blk["diffs"]}
    pre_cells = [f"{blk['code']}|{blk['quarter']}|{it}|값" for it in changed_items]
    blind_cells = [k for k in pre_cells if k in cov and not cov[k]["engine_covered"]]
    all_blind = bool(pre_cells) and len(blind_cells) == len(pre_cells) and not ev["bucket_changes"] and not ev["neighbour_changes"]
    # closure-indifferent: NOT ONE finding moved (not even a residual) although cells changed -> either no rule reads the cells or the change is
    # residual-neutral (a sum-preserving shuffle between net-asset rows).  The rule set cannot tell the two candidates apart = rule blind spot.
    indifferent = (not ev["bucket_changes"] and not ev["neighbour_changes"] and not ev["other_changes"]
                   and not new_extra and not ev["new_registry_red"])
    if (all_blind or indifferent) and cur_closes:
        out = "LATEST_FIRST_BLIND_SPOT"
    elif lat_closes and cur_closes:
        out = "LATEST_TRUE_RESTATEMENT" if differs else "NO_CHANGE"
    elif lat_closes and not cur_closes:
        out = "LATEST_EXCEPTION_RESOLVED"
    elif (not lat_closes) and cur_closes:
        out = "KEEP_CURRENT_LATEST_FAILS"
    else:
        out = "KEEP_CURRENT_BOTH_FAIL"
    sub = ""
    if out == "KEEP_CURRENT_BOTH_FAIL":
        if resolved and not introduced:
            sub = "latest strictly improves (fewer RED) but does not close"
        elif introduced and not resolved:
            sub = "latest adds RED"
        elif resolved and introduced:
            sub = "mixed (resolves some, adds others)"
        else:
            sub = "same RED either way"
    return {"outcome": out, "sub": sub, "cur_red": cur_red, "lat_red": lat_red, "resolved": resolved, "introduced": introduced,
            "near_new_red": [c[0] for c in near_new], "other_new_red": [c[0] for c in other_new], "new_extra": list(new_extra),
            "blind_cells": blind_cells, "lat_closes": lat_closes, "cur_closes": cur_closes}


def exc_rows_for(code, q):
    return [r for r in inv if r["code"] == code and r["quarter"] == q and r["domain"] == "K-ICS"]


verdicts = []
for pid, ev in sorted(evals.items()):
    if "error" in ev:
        continue
    code, q = ev["code"], ev["quarter"]
    blk = blocks.get((code, q))
    if blk is None or blk["status"] != "CONFLICT":
        continue
    d = decide(ev, blk)
    plan = read_json(OUT / "plans" / f"{pid}.json")
    gold_hit = [(e["item"], e["field"]) for e in plan["edits"] if (code, q, e["item"], e["field"]) in gold_cells]
    n_pre = sum(1 for e in plan["edits"] if e["field"] == "값")
    n_post = sum(1 for e in plan["edits"] if e["field"] == "값_적용후")
    n_der = ev["n_derived"]
    cc = ccomp.get((code, q))
    latest_core = (cc or {}).get("latest") or {}
    core_complete = bool(latest_core.get("complete"))
    post_flag = any(f.startswith("POST_COLUMN_NOT_REPLACEABLE") for f in blk["flags"])
    sus = any(f.startswith("EXTRACTION_SUSPECT") for f in blk["flags"])
    sm = sub.get((code, q))
    sub_status = sm["status"] if sm else ("NA_ODD" if not blk["even"] else "NO_SUB_RECORD")
    reasons = []
    if not core_complete:
        reasons.append("핵심표 일부 칸 판독 실패" + str(latest_core.get("missing_items")))
    if post_flag:
        reasons.append("적용후 열 대체 불가(선택경과조치 적용사: 후 세부는 직전 칸에 인쇄되지 않음)")
    if sus:
        reasons.append("추출 의심(자기 공시 대조열도 같은 항목에서 마스터와 어긋남)")
    if blk["even"]:
        if sub_status not in ("ALL_MATCH", "NO_SUBITEMS_IN_MASTER"):
            if sm and sm["status"] == "SOME_UNMATCHED":
                miss_fam = sorted({u["family"] for u in sm["unmatched"] if not u["family_page_found"]})
                if miss_fam:
                    reasons.append("세부 위험액 직전 반기 표 미확인(family %s)" % miss_fam)
                else:
                    reasons.append("세부 위험액 일부 값이 직전 반기 열에서 안 찾아짐(재작성 또는 판독 공백) " + str([u["item"] for u in sm["unmatched"]][:8]))
            else:
                reasons.append("세부 위험액 직전 반기 열 판독 불가(%s)" % sub_status)
    if gold_hit:
        cat = "gold 충돌"
    elif reasons:
        cat = "완전성 부족"
    elif d["outcome"] == "LATEST_FIRST_BLIND_SPOT":
        cat = "룰 사각"
    elif d["outcome"] in ("LATEST_TRUE_RESTATEMENT", "LATEST_EXCEPTION_RESOLVED"):
        cat = "채택 후보"
    elif d["outcome"] == "KEEP_CURRENT_LATEST_FAILS":
        cat = "현행 유지"
    else:
        cat = "현행 유지 + 목록"
    excs = exc_rows_for(code, q)
    verdicts.append({
        "id": pid, "code": code, "company": blk["name"], "quarter": q, "parity": "짝수(2Q/4Q)" if blk["even"] else "홀수(1Q/3Q)",
        "applier": code in APPLIERS, "tier": blk.get("tier"), "n_items_differ": len(blk["diffs"]),
        "diffs": "; ".join(f"{x['item']}:{x['master']:g}->{x['latest']:g}" for x in blk["diffs"]),
        "max_abs_delta": blk.get("max_abs_delta"),
        "latest_source": f"{blk['latest_label']} ; {blk['latest_src']}", "own_source": blk.get("own_src"),
        "flags": "; ".join(blk["flags"]),
        "cur_RED_rules": ",".join(d["cur_red"]), "latest_RED_rules": ",".join(d["lat_red"]),
        "resolved_RED": ",".join(d["resolved"]), "introduced_RED": ",".join(d["introduced"]),
        "neighbour_new_RED": ",".join(d["near_new_red"]), "other_new_RED": ",".join(d["other_new_red"]), "new_extra_axis_RED": ",".join(d["new_extra"]),
        "bucket_findings_moved": len(ev["bucket_changes"]), "neighbour_findings_moved": len(ev["neighbour_changes"]),
        "registry_actions": "; ".join(sorted({(json.loads(x).get("rule") if x.startswith("{") else x) for v in ev["new_registry_red"].values() for x in v})),
        "decision_table_outcome": d["outcome"], "outcome_note": d["sub"],
        "ticket_category": cat, "category_reasons": " | ".join(reasons),
        "gold_conflict_cells": str(gold_hit), "blind_spot_cells": ",".join(d["blind_cells"]),
        "sub_item_check": sub_status, "core_complete": core_complete,
        "cells_edited_pre": n_pre, "cells_edited_post_mirror": n_post, "cells_derived": n_der, "cells_total": n_pre + n_post + n_der,
        "is_registered_exception": bool(excs), "exception_registries": ",".join(sorted({r["registry"] for r in excs})),
        "exception_declared_types": ",".join(sorted({r["declared_type"] for r in excs})),
        "dc_cross_source_new": " ; ".join(n[5][:90] for n in dcev.get(pid, {}).get("new", []) if n[0] == "cross_source"),
        "dc_cross_source_gone": " ; ".join(g[5][:90] for g in dcev.get(pid, {}).get("gone", []) if g[0] == "cross_source"),
        "dc_new_RED_n": sum(1 for n in dcev.get(pid, {}).get("new", []) if n[1] == "RED"),
        "gate_status_counts_candidate": json.dumps(ev["cand_status"], ensure_ascii=False),
    })

write_json_lf(OUT / "block_verdicts.json", verdicts)
cols = list(verdicts[0].keys())
with open(OUT / "block_verdicts.csv", "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=cols)
    w.writeheader()
    for v in sorted(verdicts, key=lambda v: (v["code"], v["quarter"])):
        w.writerow(v)

print("conflict blocks evaluated:", len(verdicts))
print("decision-table outcome:", dict(Counter(v["decision_table_outcome"] for v in verdicts)))
print("ticket category      :", dict(Counter(v["ticket_category"] for v in verdicts)))
print("by tier x outcome:")
for t in ("ROUND1", "SMALL", "MATERIAL"):
    print("  ", t, dict(Counter(v["decision_table_outcome"] for v in verdicts if v["tier"] == t)))
print("registered-exception blocks:", sum(1 for v in verdicts if v["is_registered_exception"]),
      dict(Counter(v["decision_table_outcome"] for v in verdicts if v["is_registered_exception"])))
