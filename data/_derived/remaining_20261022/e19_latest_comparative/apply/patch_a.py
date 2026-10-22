from pathlib import Path
p = Path("e19_build_manifest.py")
s = p.read_text(encoding="utf-8")
s = s.replace('CODES = ["KR0005"', '''# cells of an adopted bucket that are NOT written: adopting them would create a masked gold cell (|gold - builder source| <= 0.05 -> SAME_AT_1DP),
# which tests/test_rule_coverage_manifest.py::test_gold_overlay_every_masked_cell_is_pinned only accepts with a gold_overlay_ledger pin (owner-level). Rounding-only difference.
EXCLUDE = {("KR0104", "2023.3Q", 32): "print-rounding refresh only: gold -3080.033747 vs builder source -3080.0 (|d| 0.0337 mn <= 0.05 -> masked gold cell, needs a ledger pin)"}
CODES = ["KR0005"''', 1)
s = s.replace('''        cells = [c for c in plan["cells"] if c["quarter"] in adopt_q]''', '''        cells = [c for c in plan["cells"] if c["quarter"] in adopt_q and (code, c["quarter"], c["item"]) not in EXCLUDE]
        for (ec, eq, ei), why in EXCLUDE.items():
            if ec == code:
                man.setdefault("excluded_cells", []).append([ec, eq, ei, why])''', 1)
p.write_text(s, encoding="utf-8", newline="\n")

p = Path("e19_apply.py")
s = p.read_text(encoding="utf-8")
s = s.replace('EXPECT = {"gold_added": 172, "null_dangi_added": 17, "set_dangi_added": 20, "census_old": (495, 29), "census_new": (667, 29)}',
              'EXPECT = {"gold_added": 171, "null_dangi_added": 17, "set_dangi_added": 20, "census_old": (495, 29), "census_new": (666, 29)}')
s = s.replace('exp_dangi = {"KR0032": 40, "KR0070": 32, "KR0087": 41, "KR0082": 8, "KR0083": 24, "KR0104": 26}',
              'exp_dangi = {"KR0032": 40, "KR0070": 32, "KR0087": 41, "KR0082": 8, "KR0083": 24, "KR0104": 21}   # KR0104: plan 22 minus 2023.4Q item 32 (item 32 of 2023.3Q is not adopted, see EXCLUDE)')
s = s.replace("(+172 set, +17 null_dangi, +20 set_dangi)", "(+171 set, +17 null_dangi, +20 set_dangi)")
s = s.replace("+172 set entries (was/note evidence)", "+171 set entries (was/note evidence)")
s = s.replace("= the 172 planned", "= the 171 planned")
# expected single-quarter values from the plans
s = s.replace('''    if not emitter_copy_is_current():
        errs.append("the sandbox emitter copy no longer matches scripts/emit_pl_provenance.py")
    sub_new''', '''    exp_bad = plan_dangi_check(new_by)
    if exp_bad:
        errs.append(f"plan single-quarter expectations differ from the build on {len(exp_bad)} cells: {exp_bad[:8]}")
    if not emitter_copy_is_current():
        errs.append("the sandbox emitter copy no longer matches scripts/emit_pl_provenance.py")
    sub_new''', 1)
s = s.replace('''def plan_all():''', '''EXPECTED_EXPLAINED = {("KR0104", 32, "2023.4Q")}   # plan assumed the item-32 refresh of 2023.3Q; that single cell is excluded (masked gold), its 2023.4Q single quarter stays as before


def plan_dangi_check(new_by):
    """Every single-quarter value a plan lists (auto_follow_cells / neighbour_effects / side_effect_single_quarters) must equal the real build with the new gold."""
    E = ROOT / "data/_derived/remaining_20261022/e19_latest_comparative"
    bad, n = [], 0
    for code in CODES:
        plan = json.loads((E / f"plan_{code}.json").read_text(encoding="utf-8"))
        for lst, key in (("auto_follow_cells", "derived_after"), ("auto_follow_cells", "derived_after_adoption"), ("neighbour_effects", "derived_after_adoption"),
                         ("side_effect_single_quarters", "new_dangi")):
            for e in plan.get(lst) or []:
                if key not in e:
                    continue
                k = (code, e["item"], e["quarter"])
                if k in EXPECTED_EXPLAINED:
                    continue
                n += 1
                got = new_by[k].get("값_당분기")
                exp = e[key]
                if not (same(got, exp)):
                    bad.append((k, exp, got))
    print(f"plan single-quarter expectations checked: {n}, differing: {len(bad)}")
    return bad


def plan_all():''', 1)
p.write_text(s, encoding="utf-8", newline="\n")
