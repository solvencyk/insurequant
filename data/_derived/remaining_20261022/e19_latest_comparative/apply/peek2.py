import json, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
E = Path("C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e19_latest_comparative")
out = []
for c in ["KR0005","KR0032","KR0070","KR0082","KR0083","KR0087","KR0104"]:
    p = json.loads((E / f"plan_{c}.json").read_text(encoding="utf-8"))
    out.append("=== " + c + " topkeys " + str(list(p.keys())))
    cell = p["cells"][0]
    out.append("CELL keys " + str(list(cell.keys())))
    out.append("CELL gold: " + json.dumps(cell.get("gold_set_entry") or cell.get("gold_note"), ensure_ascii=False)[:700])
    sc = p["seam_cells"]
    if sc:
        out.append("SEAM keys " + str(list(sc[0].keys())))
        out.append("SEAMS: " + json.dumps([{k: s.get(k) for k in ("quarter","item","proposal","proposed","value","set_value","old_dangi","old")} for s in sc], ensure_ascii=False)[:1500])
    if "apply_contract" in p:
        out.append("APPLY_CONTRACT: " + json.dumps(p["apply_contract"], ensure_ascii=False)[:3000])
    out.append("bucket0: " + json.dumps({k: v for k, v in p["buckets"][0].items() if k in ("quarter","adopt","n_cells","items","gold_overlap_with_adopted_items","owner_gold_overlap_with_adopted","gold_cells_in_block")}, ensure_ascii=False))
(Path(__file__).parent / "peek2.txt").write_text("\n".join(out), encoding="utf-8")
