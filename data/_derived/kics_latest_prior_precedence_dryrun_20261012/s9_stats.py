"""s9_stats.py -- step 9a (READ-ONLY).  All numbers the summary quotes, computed once and written to stats.json (so the prose never carries a hand-typed count)."""
import re
import sys
from collections import Counter, defaultdict

sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/kics_latest_prior_precedence_dryrun_20261012")
from lib_dry import *  # noqa: F401,F403,E402

utf8_stdout()
cls = read_json(OUT / "exceptions_classification.json")
verd = read_json(OUT / "block_verdicts.json")
blocks = read_json(OUT / "conflict_blocks.json")
red_map = read_json(OUT / "red56_registry_map.json")
comp = read_json(OUT / "completeness_blocks.json")

S = {}
S["gapfill_filings"] = sum(1 for f in CACHE.glob("core_*.json") if (read_json(f).get("gapfill") or 0) > 0)
dist = [r for r in cls if r["distinct_registration"]]
S["inventory_rows"] = len(cls)
S["inventory_distinct"] = len(dist)
S["domain_distinct"] = dict(Counter(r["domain"] for r in dist))
S["declared_distinct"] = dict(Counter(r["declared_type"] for r in dist))
S["final_distinct"] = dict(Counter(r["final_type"] for r in dist))
kd = [r for r in dist if r["domain"] == "K-ICS"]
S["kics_distinct"] = len(kd)
S["declared_kics"] = dict(Counter(r["declared_type"] for r in kd))
S["final_kics"] = dict(Counter(r["final_type"] for r in kd))
S["measured_kics"] = dict(Counter(r["measured"] for r in kd))
S["measured_all"] = dict(Counter(r["measured"] for r in dist))
byreg = defaultdict(lambda: {"n": 0, "declared": Counter(), "final": Counter(), "red": 0})
for r in dist:
    g = byreg[r["registry"]]
    g["n"] += 1
    g["declared"][r["declared_type"]] += 1
    g["final"][r["final_type"]] += 1
key2final = {(r["registry"], r["code"], r["quarter"]): r["final_type"] for r in dist}
red_by_final = Counter()
for x in red_map:
    ft = key2final.get((x["registry"], x["code"], x["quarter"]))
    red_by_final[ft] += 1
    byreg[x["registry"]]["red"] += 1
S["by_registry"] = {k: {"n": v["n"], "declared": dict(v["declared"]), "final": dict(v["final"]), "red": v["red"]} for k, v in sorted(byreg.items())}
S["red56_by_final_type"] = dict(red_by_final)
S["red56_by_registry"] = dict(Counter(x["registry"] for x in red_map))

# ---- population blocks
S["blocks_total"] = len(blocks)
S["blocks_status"] = dict(Counter(b["status"] for b in blocks))
S["already_adopted_clean_blocks"] = sum(1 for b in blocks if b["status"] == "CLEAN" and b.get("own_dev"))
S["already_adopted_examples"] = [f"{b['code']} {b['quarter']}" for b in blocks if b["status"] == "CLEAN" and b.get("own_dev")][:20]
_ok = [x for x in blocks if x["own_status"] in ("OK", "VISION_ONLY")]
S["own_control_blocks"] = len(_ok)
S["own_control_exact"] = sum(1 for x in _ok if not x["own_dev"])
S["own_control_deviating_already_adopted"] = sum(1 for x in _ok if x["own_dev"] and x["status"] == "CLEAN")
S["own_control_deviating_conflict"] = sum(1 for x in _ok if x["own_dev"] and x["status"] == "CONFLICT")
S["known_cases_status"] = {k: next((x["status"] for x in blocks if (x["code"], x["quarter"]) == tuple(k.split("|"))), None)
                           for k in ("KR0049|2024.3Q", "KR0073|2026.1Q", "KR1107|2025.3Q", "KR1107|2026.1Q", "KR1101|2025.4Q")}
S["conflict_by_quarter"] =dict(Counter(b["quarter"] for b in blocks if b["status"] == "CONFLICT"))
S["uncovered_reasons"] = dict(Counter(f"own={b['own_status']}|F+1={b['q1_status']}|F+2={b['q2_status']}" for b in blocks if b["status"] == "UNCOVERED"))
S["later_printings_differ_among_conflicts"] = sum(1 for b in blocks if b["status"] == "CONFLICT" and any(f.startswith("LATER_PRINTINGS_DIFFER") for f in b["flags"]))
S["later_printings_differ_all_blocks"] = sum(1 for b in blocks if b["l1_vs_l2"])

# ---- decision table
S["decision_all"] = dict(Counter(v["decision_table_outcome"] for v in verd))
S["decision_exception_blocks"] = dict(Counter(v["decision_table_outcome"] for v in verd if v["is_registered_exception"]))
S["decision_nonexception_blocks"] = dict(Counter(v["decision_table_outcome"] for v in verd if not v["is_registered_exception"]))
S["decision_by_tier"] = {t: dict(Counter(v["decision_table_outcome"] for v in verd if v["tier"] == t)) for t in ("ROUND1", "SMALL", "MATERIAL")}
S["tier_counts"] = dict(Counter(v["tier"] for v in verd))
S["category_all"] = dict(Counter(v["ticket_category"] for v in verd))
cand = [v for v in verd if v["ticket_category"] == "채택 후보"]
S["adopt_blocks"] = len(cand)
S["adopt_cells"] = {"total": sum(v["cells_total"] for v in cand), "pre": sum(v["cells_edited_pre"] for v in cand),
                    "post_mirror": sum(v["cells_edited_post_mirror"] for v in cand), "derived": sum(v["cells_derived"] for v in cand)}
S["adopt_by_tier"] = dict(Counter(v["tier"] for v in cand))
S["adopt_by_outcome"] = dict(Counter(v["decision_table_outcome"] for v in cand))
S["adopt_exception_resolved"] = [f"{v['code']} {v['quarter']}" for v in cand if v["decision_table_outcome"] == "LATEST_EXCEPTION_RESOLVED"]
S["adopt_ids_material"] = [v["id"] for v in cand if v["tier"] == "MATERIAL"]
# completeness reasons
reas = Counter()
reas_primary = Counter()
for v in verd:
    if v["ticket_category"] == "완전성 부족":
        rs = [x.strip() for x in v["category_reasons"].split("|") if x.strip()]
        kinds = set()
        for x in rs:
            if x.startswith("적용후 열"):
                kinds.add("적용후 열 대체 불가(적용사)")
            elif x.startswith("핵심표"):
                kinds.add("핵심표 일부 칸 판독 실패(추출 한계)")
            elif x.startswith("추출 의심"):
                kinds.add("추출 의심(자기 공시 대조열도 어긋남)")
            elif x.startswith("세부 위험액 직전 반기 표 미확인"):
                kinds.add("세부 위험액 직전 반기 표 미확인")
            elif x.startswith("세부 위험액 일부 값"):
                kinds.add("세부 위험액 일부 값 불일치/판독 공백")
            elif x.startswith("세부 위험액 직전 반기 열 판독 불가"):
                kinds.add("세부 위험액 열 판독 불가(스캔)")
            else:
                kinds.add(x[:30])
        for k in kinds:
            reas[k] += 1
        if len(kinds) == 1:
            reas_primary[next(iter(kinds))] += 1
S["incomplete_reasons_any"] = dict(reas)
S["incomplete_single_reason"] = dict(reas_primary)
S["incomplete_by_parity"] = dict(Counter(v["parity"] for v in verd if v["ticket_category"] == "완전성 부족"))
S["incomplete_applier"] = sum(1 for v in verd if v["ticket_category"] == "완전성 부족" and v["applier"])
S["gold_conflict"] = [f"{v['code']} {v['quarter']} {v['gold_conflict_cells']}" for v in verd if v["ticket_category"] == "gold 충돌"]
S["blind_blocks"] = [f"{v['code']} {v['quarter']}" for v in verd if v["decision_table_outcome"] == "LATEST_FIRST_BLIND_SPOT"]
S["blind_blocks_ticket_category"] = dict(Counter(v["ticket_category"] for v in verd if v["decision_table_outcome"] == "LATEST_FIRST_BLIND_SPOT"))
cov = read_json(OUT / "cell_coverage.json")
S["cells_tested_for_coverage"] = len(cov)
S["engine_blind_cells"] = sum(1 for v in cov.values() if not v["engine_covered"])
S["engine_blind_pre_cells"] = sorted({k for k, v in cov.items() if not v["engine_covered"] and k.endswith("|값")})
# cross-source (17BS) effect
S["dc_cross_new_blocks"] = [v["id"] for v in verd if v["dc_cross_source_new"]]
S["dc_cross_gone_blocks"] = [v["id"] for v in verd if v["dc_cross_source_gone"]]
S["dc_cross_new_among_adopt"] = [v["id"] for v in cand if v["dc_cross_source_new"]]
S["dc_cross_gone_among_adopt"] = [v["id"] for v in cand if v["dc_cross_source_gone"]]
S["neighbour_findings_moved_any"] = sum(1 for v in verd if v["neighbour_findings_moved"])
S["neighbour_new_red_any"] = sum(1 for v in verd if v["neighbour_new_RED"])
S["registry_actions_blocks"] = [v["id"] for v in verd if v["registry_actions"]]
# 17BS (IFRS17_BS) cross-source signal on the closure-indifferent (rule blind spot) blocks
bl = [v for v in verd if v["decision_table_outcome"] == "LATEST_FIRST_BLIND_SPOT"]
S["blind_cross_supports_latest"] = [v["id"] for v in bl if v["dc_cross_source_gone"] and not v["dc_cross_source_new"]]
S["blind_cross_supports_current"] = [v["id"] for v in bl if v["dc_cross_source_new"] and not v["dc_cross_source_gone"]]
S["blind_cross_neither"] = [v["id"] for v in bl if not v["dc_cross_source_new"] and not v["dc_cross_source_gone"]]
S["keep_current_ids"] = [f"{v['code']} {v['quarter']}" for v in verd if v["ticket_category"] == "현행 유지"]
S["dc_cross_new_by_category"] = dict(Counter(v["ticket_category"] for v in verd if v["dc_cross_source_new"]))
S["dc_cross_gone_by_category"] = dict(Counter(v["ticket_category"] for v in verd if v["dc_cross_source_gone"]))
S["post_only_split"] = dict(Counter(r["declared_type"] for r in dist if r["measured"] == "POST_COLUMN_ONLY"))
S["dc_new_red_by_category"] = dict(Counter(v["ticket_category"] for v in verd if v["dc_new_RED_n"]))
S["dc_new_red_among_adopt"] = [v["id"] for v in cand if v["dc_new_RED_n"]]
S["adopt_material_list"] = [{"id": v["id"], "diffs": v["diffs"], "outcome": v["decision_table_outcome"]} for v in cand if v["tier"] == "MATERIAL"]
# keep-current detail
keep = [v for v in verd if v["decision_table_outcome"] in ("KEEP_CURRENT_LATEST_FAILS", "KEEP_CURRENT_BOTH_FAIL")]
S["keep_current_n"] = len(keep)
S["keep_current_by_category"] = dict(Counter(v["ticket_category"] for v in keep))
S["keep_current_companies"] = dict(Counter(v["code"] for v in keep))
S["keep_current_post_axis_only"] = sum(1 for v in keep if v["new_extra_axis_RED"] and not v["latest_RED_rules"])
# completeness table
def frac(sel, key):
    return sum(1 for r in sel if r.get(key)), len(sel)
tbl = {}
for parity in ("odd", "even"):
    for label in ("next", "latest"):
        for qtype in (("1Q", "3Q") if parity == "odd" else ("2Q", "4Q")) + ("all",):
            sel = [r for r in comp if r["parity"] == parity and (qtype == "all" or r["quarter"].endswith(qtype))]
            if label == "next":
                sel = [r for r in sel if r["next_filing"]]
            read = [r for r in sel if r[f"{label}_core_readable"]]
            if parity == "even":
                scanned = [r for r in read if r.get(f"{label}_sub_complete") is not None]
                done = [r for r in scanned if r[f"{label}_complete"]]
                tbl[f"{parity}|{qtype}|{label}"] = {"blocks": len(sel), "readable": len(read), "core_complete": sum(1 for r in read if r[f"{label}_core_complete"]),
                                                   "sub_present": sum(1 for r in scanned if r[f"{label}_sub_complete"]), "scanned": len(scanned), "complete": len(done)}
            else:
                done = [r for r in read if r[f"{label}_core_complete"]]
                tbl[f"{parity}|{qtype}|{label}"] = {"blocks": len(sel), "readable": len(read), "core_complete": len(done), "complete": len(done)}
S["completeness"] = tbl
write_json_lf(OUT / "stats.json", S)
for k, v in S.items():
    if k not in ("by_registry", "completeness", "adopt_ids_material", "keep_current_companies"):
        print(k, ":", v)
