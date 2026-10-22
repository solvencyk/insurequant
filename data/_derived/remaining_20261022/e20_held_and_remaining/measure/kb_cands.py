"""kb_cands: candidate PL cells (latest comparative) for KB손해보험 (KR0010) = FS-API prior Tier-1 + production Tier-2 handler run on the LATER filing
(item1-steered table pick).  Writes kb_cands.json/.txt with filing line numbers of the 전기/전분기 LOB note table.  READ-ONLY."""
import json
import sys

sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e20_held_and_remaining/measure")
import cand as K  # noqa: E402
import fsapi as F  # noqa: E402
import mlib as M  # noqa: E402
import plan_lib as PL  # noqa: E402
import prod as P  # noqa: E402
import stmtlib as S  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
CODE = "KR0010"
pl, names, inames = M.load_pl()
gold = M.jload(M.SNAP / "user_pl_cells.json")
gold_cells = {(c["원보험사코드"], c["공시분기"], c["항목번호"]): c for c in gold["set"]}
qs = sys.argv[1].split(",") if len(sys.argv) > 1 else ["2023.4Q", "2024.1Q", "2024.2Q", "2024.3Q"]
res, txt = {}, []
for q in qs:
    m = pl[(CODE, q)]
    t1p, _ = F.prior(CODE, q)
    fy = M.later_fy(q)
    tabs = P.tables_for(CODE, fy)
    t2 = P.C.extract_tier2_kb(tabs, item1=t1p.get(1))
    del tabs
    zf = None if m.get(6) is not None else frozenset()
    v = P.C.__dict__  # noqa: F841  (keep production module referenced)
    from build_pl_breakdown import assemble  # noqa: E402
    vv = assemble(dict(t1p), dict(t2), False, zero_fill_ok=zf)
    ch = PL.changed(CODE, q, vv, pl)
    clo = PL.closure(vv, nonlife=True)
    # --- locate the chosen LOB note table in the later filing (my line reader): '총 보험서비스결과' whose last number == later item 1
    path = [p for p in M.main_xmls(CODE, fy) if not p.name.endswith(("_00760.xml", "_00761.xml"))][0]
    lines = M.read_lines(path)
    s, e = S.sep_section(lines)
    note_from = None
    import re
    for ln, tt in S.titles(lines):
        if re.match(r"^\d+\.재무제표주석$", re.sub(r"\s+", "", tt)):
            note_from = ln
    hit = None
    for t in M.iter_tables(lines):
        if note_from and t["start"] < note_from:
            continue
        for r in t["rows"]:
            if r["cells"] and M.norm_label(r["cells"][0]["text"]) == "총보험서비스결과":
                nums = [c for c in r["cells"][1:] if c["val"] is not None]
                if nums and abs(nums[-1]["val"] - t1p.get(1)) < 1.5:
                    hit = (t, r, nums)
    cite = None
    if hit:
        t, r, nums = hit
        cite = {"table": [t["start"], t["end"]], "caption": t["caption"][:70], "row_tr": r["tr_line"], "cells": [(c["text"], c["line"]) for c in r["cells"][1:]]}
        # CSM/RA rows used for items 4/5/9/10 (first numeric cell)
        rows_used = {}
        for rr in t["rows"]:
            lab = M.norm_label(rr["cells"][0]["text"]) if rr["cells"] else ""
            if any(x in lab for x in ("보험계약마진상각", "제공된서비스의보험계약마진", "위험해제", "제공받은서비스의재보험계약마진", "예상보험금", "회수예상", "회수가능", "보험금및보험서비스비용")):
                rows_used.setdefault(lab, []).append((rr["tr_line"], [(c["text"], c["line"]) for c in rr["cells"][1:4]]))
        cite["rows_used"] = rows_used
    gold_hit = {it: gold_cells[(CODE, q, it)].get("값") for it, _o, _n in ch if (CODE, q, it) in gold_cells}
    res[q] = {"later_filing": M.rel(path), "tier2_prior": {str(k): (round(x, 6) if isinstance(x, (int, float)) else x) for k, x in t2.items()}, "cells": [(it, old, new) for it, old, new in ch],
              "closure": clo, "screen_eok": PL.screen_eok(CODE, q, vv, pl), "gold_hit": gold_hit, "lob_note": cite, "vector": {str(k): vv.get(k) for k in range(1, 33)}}
    txt.append(f"=== {CODE} {q}: later {M.rel(path)}  cells changed={len(ch)}  gold overlap={gold_hit}")
    txt.append("   closure: " + "; ".join(f"{k}={('%.3f' % x) if x is not None else None}" for k, x in clo.items()))
    txt.append("   screen(억원 old,new,delta): " + json.dumps(res[q]["screen_eok"], ensure_ascii=False))
    txt.append("   LOB note: " + json.dumps({k: v2 for k, v2 in (cite or {}).items() if k != "rows_used"}, ensure_ascii=False)[:900])
    for it, old, new in ch:
        txt.append(f"   item {it:>2} {inames.get(it, '')[:22]:<22} old={old!s:>14} new={new:>16,.3f}")
M.MEASURE.joinpath("kb_cands.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
M.MEASURE.joinpath("kb_cands.txt").write_text("\n".join(txt), encoding="utf-8")
print("\n".join(txt)[:9000])
