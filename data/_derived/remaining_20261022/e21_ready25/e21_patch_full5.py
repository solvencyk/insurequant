"""one-off patcher #5 for e21_plan_full.py: drop NEW gold cells that would be masked (value == builder source) -- they would need a new ledger pin (ticket: no new mask cells / no new pins)"""
H = "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e21_ready25/"
s = open(H + "e21_plan_full.py", encoding="utf-8").read()
old = '''    # ------------------------------------------------------------------------------------------------ 1. value differences against the measure-phase candidates
    OUT.append("== A. adopted cells whose value differs from the measure-phase candidate")'''
new = '''    # ------------------------------------------------------------------------------------------------ 0. masked-gold guard
    sys.path.insert(0, str(PL.ROOT / "scripts"))
    import validate_data_contract as GV
    src_pl = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r for r in json.loads((PL.ROOT / "data/dart/viz/pl_breakdown_master.json").read_text(encoding="utf-8"))}
    OUT.append("== 0. new gold cells that would be MASKED (value == builder source within the census tolerance) -> dropped (a masked cell needs a ledger pin; ticket: no new mask cells / no new pins)")
    plan.setdefault("findings", [])
    for b in plan["buckets"]:
        keep = []
        for c in b["cells"]:
            k = (c["code"], c["item"], c["quarter"])
            if k not in GOLD and GV.gold_overlay_verdict(c["new"], src_pl.get(k)) in GV._GOLD_MASKED:
                OUT.append(f"   dropped {k}: new {c['new']} vs builder source {src_pl.get(k, {}).get('값')} -> masked")
                b["dropped"].append(dict(item=c["item"], old=c["old"], new=c["new"], cls="masked", reason="would be a masked gold cell (== builder source); a new ledger pin is forbidden by the ticket", in_cand=c["cand_new"] is not None))
                plan["findings"].append(dict(code=c["code"], quarter=c["quarter"], item=c["item"], kind="masked new gold cell not loaded",
                                             text=f"latest comparative {c['new']} equals the builder source value; master stays {c['old']} (the _zero_other_expense heuristic blanks it); loading it needs a new ledger pin"))
                cells_all.pop((c["code"], c["quarter"], c["item"]), None)
                continue
            keep.append(c)
        b["cells"] = keep
    # ------------------------------------------------------------------------------------------------ 1. value differences against the measure-phase candidates
    OUT.append("== A. adopted cells whose value differs from the measure-phase candidate")'''
assert s.count(old) == 1
s = s.replace(old, new)
open(H + "e21_plan_full.py", "w", encoding="utf-8", newline="\n").write(s)
print("patched full5")
