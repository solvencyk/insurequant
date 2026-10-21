"""Read-only: candidate PL provenance = live sidecar with the 12 KR0073 target blocks replaced by what scripts/emit_pl_provenance.py itself emits for the post-apply
masters (tmp_emit/prov_B_cand.json, produced by emit_prov_check.py from a sandbox copy of the emitter), plus the merge note.

The emitter reproduces 26/28 live KR0073 blocks byte-for-byte (the 2 others are the 경영공시 DISCLOSURE blocks 2023.1Q/2Q that the emitter cannot know), so its output is the
reproducible form.  Writes sim/prov_pl_cand_emitter.json and prints a change summary.
"""
import copy
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
sys.stdout.reconfigure(encoding="utf-8")
QS = ["2023.1Q", "2023.2Q", "2023.3Q", "2023.4Q", "2024.1Q", "2024.2Q"]
live = json.loads((ROOT / "PL_breakdown_provenance.json").read_text(encoding="utf-8"))
emit = json.loads((HERE / "tmp_emit" / "prov_B_cand.json").read_text(encoding="utf-8"))
ek = {(c["company_code"], c["quarter"], c["item_block"]): c for c in emit["cells"]}
cand = copy.deepcopy(live)
changed = []
for i, c in enumerate(cand["cells"]):
    k = (c["company_code"], c["quarter"], c["item_block"])
    if k[0] == "KR0073" and k[1] in QS:
        new = ek[k]
        if json.dumps(new, ensure_ascii=False, sort_keys=False) != json.dumps(c, ensure_ascii=False, sort_keys=False):
            changed.append(k)
        cand["cells"][i] = new
cand["merge_note_20261022_kr0073_pl_refresh"] = (
    "KR0073 PL 2023.1Q-2024.2Q refreshed to the latest-comparative (restated) separate-basis columns via data/_gold/user_pl_cells.json (+122 cells). "
    "The 12 affected blocks are the output of scripts/emit_pl_provenance.py for the post-apply masters (touched items moved to the owner_gold_overlay entry; "
    "blocks whose published items are all gold-overlaid become OWNER_GOLD). Evidence data/_derived/kyobo_pl_restate_dryrun_20261021/")
out = HERE / "sim" / "prov_pl_cand_emitter.json"
out.write_text(json.dumps(cand, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
# invariants: nothing but the 12 blocks (and the note) differs from the live sidecar
lc = {(c["company_code"], c["quarter"], c["item_block"]): c for c in live["cells"]}
cc = {(c["company_code"], c["quarter"], c["item_block"]): c for c in cand["cells"]}
assert list(lc) == list(cc), "cell order/keys changed"
diff = [k for k in lc if lc[k] != cc[k]]
assert set(diff) <= {k for k in lc if k[0] == "KR0073" and k[1] in QS}, "a block outside the 12 target blocks changed"
assert set(live) | {"merge_note_20261022_kr0073_pl_refresh"} == set(cand), "top-level keys changed unexpectedly"
print(f"blocks replaced by emitter output: {len(changed)} ({len(diff)} differ from live); every other cell identical; top-level keys = live + merge note")
for k in sorted(diff, key=lambda x: (x[1], x[2])):
    c = cc[k]
    print(f"  {k[1]} {k[2]:15s} source_id={c['source_id']} resolution={c.get('resolution')} owner_override={c.get('owner_override')} published={c['published_items']} "
          f"files={[(e['how'], e['items']) for e in c.get('source_files', [])]}")
