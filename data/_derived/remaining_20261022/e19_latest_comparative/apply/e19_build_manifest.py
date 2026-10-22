# -*- coding: utf-8 -*-
"""Normalise the 7 plan_KR*.json files into ONE manifest (e19_manifest.json): gold set entries, null_dangi cells, set_dangi cells, expected dangi-change counts.
Read-only w.r.t. the repo."""
import json
import sys
from pathlib import Path

ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
E = ROOT / "data/_derived/remaining_20261022/e19_latest_comparative"
OUT = Path(__file__).resolve().parent
sys.stdout.reconfigure(encoding="utf-8")
# cells of an adopted bucket that are NOT written: adopting them would create a masked gold cell (|gold - builder source| <= 0.05 -> SAME_AT_1DP),
# which tests/test_rule_coverage_manifest.py::test_gold_overlay_every_masked_cell_is_pinned only accepts with a gold_overlay_ledger pin (owner-level). Rounding-only difference.
EXCLUDE = {("KR0104", "2023.3Q", 32): "print-rounding refresh only: gold -3080.033747 vs builder source -3080.0 (|d| 0.0337 mn <= 0.05 -> masked gold cell, needs a ledger pin)"}
CODES = ["KR0005", "KR0032", "KR0070", "KR0082", "KR0083", "KR0087", "KR0104"]


def main():
    man = {"companies": {}, "gold_set": [], "null_dangi": [], "set_dangi": [], "held_buckets": [], "adopted_buckets": []}
    lines = []
    for code in CODES:
        plan = json.loads((E / f"plan_{code}.json").read_text(encoding="utf-8"))
        adopt_q = [b["quarter"] for b in plan["buckets"] if b.get("adopt")]
        held = [(b["quarter"], b.get("reason", "")[:200]) for b in plan["buckets"] if not b.get("adopt")]
        for q in adopt_q:
            man["adopted_buckets"].append([code, q])
        for q, why in held:
            man["held_buckets"].append([code, q, why])
        cells = [c for c in plan["cells"] if c["quarter"] in adopt_q and (code, c["quarter"], c["item"]) not in EXCLUDE]
        for (ec, eq, ei), why in EXCLUDE.items():
            if ec == code:
                man.setdefault("excluded_cells", []).append([ec, eq, ei, why])
        ac = plan.get("apply_contract")
        for c in cells:
            if "gold_set_entry" in c:
                note = c["gold_set_entry"]["note"]
            elif c.get("gold_note"):
                note = c["gold_note"]
            else:
                note = ac["gold_set_notes"][f"{c['quarter']}|{c['item']}"]
            man["gold_set"].append({"원보험사코드": code, "항목번호": c["item"], "공시분기": c["quarter"], "값": c["new"], "was": c["old"], "note": note})
        nd, sd = [], []
        if ac:
            nd = [list(x) for x in ac.get("null_dangi_cells", [])]
            sd = [list(x) for x in ac.get("set_dangi_cells", [])]
        else:
            for s in plan["seam_cells"]:
                if s["proposal"] == "set_dangi":
                    src = f"{s['xml_file']}:L{s['xml_line']} [{s['xml_label']}] 3-month column printed in the later filing; {s['second_source']}"
                    sd.append([code, s["quarter"], s["item"], s["value"], src])
                elif s["proposal"] == "null_dangi":
                    nd.append([code, s["quarter"], s["item"]])
        man["null_dangi"] += nd
        man["set_dangi"] += sd
        man["companies"][code] = {"adopt_quarters": adopt_q, "held": held, "n_gold": len(cells), "n_null_dangi": len(nd), "n_set_dangi": len(sd),
                                  "expected": (ac or {}).get("expected_master_changes")}
        lines.append(f"{code}: adopt {adopt_q}; held {held}; gold {len(cells)}; null_dangi {len(nd)}; set_dangi {len(sd)}; expected {(ac or {}).get('expected_master_changes')}")
        if ac:
            gs = {(x[1], x[2]): (x[3], x[4]) for x in ac["gold_set_cells"]}
            mine = {(c["item"], c["quarter"]): (c["new"], c["old"]) for c in cells}
            lines.append(f"   apply_contract gold cells == cells: {gs == mine} ({len(gs)} vs {len(mine)})")
        for x in sd:
            lines.append("   set_dangi " + json.dumps(x, ensure_ascii=False)[:420])
    (OUT / "e19_manifest.json").write_text(json.dumps(man, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    lines.append(f"TOTAL gold {len(man['gold_set'])} null_dangi {len(man['null_dangi'])} set_dangi {len(man['set_dangi'])} adopted buckets {len(man['adopted_buckets'])} held {len(man['held_buckets'])}")
    (OUT / "e19_manifest.txt").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


main()
