"""Read-only: candidate PL gold (user_pl_cells.json + 122 KR0073 cells), candidate provenance and the gold-overlay census/pin effect.

Writes (all under sim/): gold_pl_cand.json, prov_pl_cand.json, ledger_pl_pins_cand.json (live pin ledger + PL pins for masked new gold cells).
Provenance convention = scripts/apply_latest_comparative_20261012.py (touched items move into the `owner_gold_overlay` entry of the (code, quarter, block) record;
other entries lose those items; owner_override=True; published_items = non-null count of the block after the change).
"""
import copy
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
SIM = HERE / "sim"
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT))
sys.stdout.reconfigure(encoding="utf-8")
GOLD_PL_PATH = "data/_gold/user_pl_cells.json"
CONTRACT_NOTE_ITEMS = {4, 5, 6, 9, 10, 11, 13, 14}
LATER = {"2023.1Q": ("FY2024_Q1", "20240516001553"), "2023.2Q": ("FY2024_Q2", "20240814004365"), "2023.3Q": ("FY2024_Q3", "20241114003039"),
         "2023.4Q": ("FY2024_Q4", "20250331004015"), "2024.1Q": ("FY2025_Q1", "20250515002967"), "2024.2Q": ("FY2025_Q2", "20250814004112")}
plan = json.loads((HERE / "pl_plan.json").read_text(encoding="utf-8"))["plan"]
gold = json.loads((ROOT / GOLD_PL_PATH).read_text(encoding="utf-8"))
prov = json.loads((ROOT / "PL_breakdown_provenance.json").read_text(encoding="utf-8"))
pins = json.loads((ROOT / "data/_gold/gold_overlay_ledger.json").read_text(encoding="utf-8"))
pl_master = json.loads((ROOT / "data/dart/viz/pl_breakdown_master.json").read_text(encoding="utf-8"))
root = json.loads((ROOT / "PL_breakdown.json").read_text(encoding="utf-8"))

# ---- 1. gold ----
existing = {(e["원보험사코드"], e["항목번호"], e["공시분기"]) for e in gold["set"]}
new_gold = copy.deepcopy(gold)
for c in plan:
    k = ("KR0073", c["item"], c["quarter"])
    if k in existing:
        raise SystemExit(f"ABORT: gold already has {k}")
    fy, rc = LATER[c["quarter"]]
    note = (f"2026-10-22 parser/ifrs17 (KR0073 PL refresh, coordinator instruction 2026-10-21 after owner rejected the amortization pins): latest-comparative, 별도 기준. "
            f"{fy} rcept {rc} 의 전기(누적) 열 = 재작성 값. 값 근거·원문 줄 번호 data/_derived/kyobo_pl_restate_dryrun_20261021/pl_cell_changes.csv"
            + (" (item 6/7: 같은 행이 이 필링에서 '발생한 보험서비스수익' 로 인쇄돼 생산 판독기가 못 읽는다 — 같은 행을 같은 산식으로 읽음)" if "ALT_LABEL_ITEM6" in c["flags"] else ""))
    new_gold["set"].append({"원보험사코드": "KR0073", "항목번호": c["item"], "공시분기": c["quarter"], "값": c["new"], "was": c["old"], "note": note})
(SIM / "gold_pl_cand.json").write_text(json.dumps(new_gold, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
print(f"PL gold: {len(gold['set'])} -> {len(new_gold['set'])} entries (+{len(new_gold['set']) - len(gold['set'])})")

# ---- 2. census / pins ----
import validate_data_contract as G  # noqa: E402

rows_old = G.gold_overlay_census("PL", gold["set"], pl_master)
rows_new = G.gold_overlay_census("PL", new_gold["set"], pl_master)
mk = lambda rows: [r for r in rows if r["verdict"] in G._GOLD_MASKED]
print(f"PL census (gold cells, masked): {(len(rows_old), len(mk(rows_old)))} -> {(len(rows_new), len(mk(rows_new)))}")
new_rows = [r for r in rows_new if r["company"] == "KR0073" and r["quarter"] in LATER]
verdicts = {}
for r in new_rows:
    verdicts[r["verdict"]] = verdicts.get(r["verdict"], 0) + 1
print("verdicts of the 122 new gold cells vs builder source:", verdicts)
masked_new = [r for r in new_rows if r["verdict"] in G._GOLD_MASKED]
new_pins = copy.deepcopy(pins)
for r in masked_new:
    new_pins["entries"][r["key"]] = {"overlay": "PL", "verdict": r["verdict"], "gold": r["gold"], "src": r["src"], "source_file": "data/dart/viz/pl_breakdown_master.json",
                                     "note": "2026-10-22 KR0073 PL refresh: masked gold cell pinned (gold equals the builder source)"}
print("masked new gold cells needing a pin:", [(r["quarter"], r["item"], r["gold"], r["src"]) for r in masked_new])
(SIM / "ledger_pl_pins_cand.json").write_text(json.dumps(new_pins, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")

# ---- 3. provenance ----
new_prov = copy.deepcopy(prov)
recs = {(c["company_code"], c["quarter"], c["item_block"]): c for c in new_prov["cells"]}
vec_new = {}
for r in root:
    if r["원보험사코드"] == "KR0073":
        vec_new.setdefault(r["공시분기"], {})[r["항목번호"]] = r.get("값")
for c in plan:
    vec_new[c["quarter"]][c["item"]] = c["new"]
touched = {}
for c in plan:
    blk = "contract_notes" if c["item"] in CONTRACT_NOTE_ITEMS else "income_statement"
    touched.setdefault(("KR0073", c["quarter"], blk), set()).add(c["item"])
summary = []
for key, items in sorted(touched.items()):
    rec = recs[key]
    sfs = rec.setdefault("source_files", [])
    g = next((e for e in sfs if e.get("file") == GOLD_PL_PATH and e.get("how") == "owner_gold_overlay"), None)
    if g is None:
        g = {"file": GOLD_PL_PATH, "how": "owner_gold_overlay", "items": []}
        sfs.append(g)
    for e in list(sfs):
        if e is g:
            continue
        e["items"] = [i for i in e.get("items", []) if i not in items]
        if not e["items"] and e.get("file") != rec.get("source_file"):
            sfs.remove(e)
    g["items"] = sorted(set(g.get("items", [])) | items)
    rec["owner_override"] = True
    # every non-builder item of the block now lives in the gold overlay -> the block's lineage IS the gold entry (same convention as
    # KR0008 2023.1Q / KR0002 2023.1Q contract_notes); keeping source_id=DISCLOSURE would make the lineage guard treat all items as 경영공시 계보.
    others = [e for e in sfs if e is not g and e.get("file") is not None and e.get("items")]
    if not others:
        rec["source_id"] = "OWNER_GOLD"
        rec["source_file"] = GOLD_PL_PATH
        rec["resolution"] = "owner_gold_overlay"
        for e in list(sfs):
            if e is not g and e.get("file") is not None and not e.get("items"):
                sfs.remove(e)
    nonnull = {i for i, v in vec_new[key[1]].items() if v is not None and ((i in CONTRACT_NOTE_ITEMS) == (key[2] == "contract_notes"))}
    rec["published_items"] = len(nonnull)
    summary.append((key[1], key[2], len(items), rec["published_items"], [(e["how"], e["items"]) for e in sfs]))
new_prov["merge_note_20261022_kr0073_pl_refresh"] = ("KR0073 PL 2023.1Q-2024.2Q refreshed to the latest-comparative (restated) separate-basis columns via data/_gold/user_pl_cells.json "
                                                    "(+122 cells); touched items moved to the owner_gold_overlay entry. Evidence data/_derived/kyobo_pl_restate_dryrun_20261021/")
(SIM / "prov_pl_cand.json").write_text(json.dumps(new_prov, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
print("provenance blocks touched:", len(touched))
for s in summary:
    print("  ", s[0], s[1], "touched", s[2], "published_items", s[3], "entries", s[4])
