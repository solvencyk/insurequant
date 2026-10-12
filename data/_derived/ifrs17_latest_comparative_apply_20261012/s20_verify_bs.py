"""Read-only direct verification of the BS year-end cells of plan_diff.json against the RAW later-filing XML (independent reader xmltab.py).

For every planned BS cell (code, quarter, item, new) the later annual filing (FY(N+1)_Q4 raw dir of the same company) is opened and every table row whose
label matches the item is scanned for a PRINTED token equal to the planned value at the filing unit (원 / 천원 / 백만원).  Only tables that are a balance sheet
(the table itself prints 자산총계 + 부채총계 + 자본총계 rows) count as evidence; a hit in any other table (business summary, text) is ignored.
The evidence keeps the XML file, table index, XML line of the row, the nearest captions, the column header text and the printed string.
No pipeline value is used for the match.
Output evidence_bs.csv
"""
from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import xmltab as X  # noqa: E402

ROOT = X.ROOT
plan = json.loads((HERE / "plan_diff.json").read_text(encoding="utf-8"))
PFX = r"^[ⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩIVX\d\.\)\s]*"
LABEL = {
    1: PFX + r"자\s*산\s*총\s*계$",
    2: PFX + r"부\s*채\s*총\s*계$",
    3: PFX + r"자\s*본\s*총\s*계$",
    4: r"기타\s*포괄\s*손익\s*누계\s*액",
    14: PFX + r"재보험\s*계약\s*자산",
    20: PFX + r"보험\s*계약\s*부채",
    21: PFX + r"재보험\s*계약\s*부채",
    31: r"이익\s*잉여\s*금|결손\s*금",
}
SCALES = [(1e6, "원"), (1e3, "천원"), (1.0, "백만원")]
RE_TA, RE_TL, RE_TE = (re.compile(LABEL[i]) for i in (1, 2, 3))
PRIOR_HINT = re.compile(r"전\s*\)?\s*기|전기|\(전\)|전기말|전년")


def later_dirs(code: str, quarter: str):
    y = int(quarter[:4]) + 1
    base = ROOT / "data/dart" / f"FY{y}_Q4" / "raw"
    return sorted(base.glob(f"{code}_*"))


def is_bs_table(t) -> bool:
    labs = [r.cells[0] for r in t.rows if r.cells]
    return any(RE_TA.search(x) for x in labs) and any(RE_TL.search(x) for x in labs) and any(RE_TE.search(x) for x in labs)


def col_header(t, ci):
    """text of the header cells at column index ci (first 3 rows that contain no numeric tokens beyond years)."""
    out = []
    for r in t.rows[:4]:
        if ci < len(r.cells):
            out.append(r.cells[ci])
        # headers with a leading label column shift by one when the row is short
    return " / ".join(x for x in out if x)[:80]


def scan(code, quarter, item, value):
    pat = re.compile(LABEL[item])
    hits = []
    for d in later_dirs(code, quarter):
        for xp in sorted(d.glob("**/*.xml"), key=lambda p: p.stat().st_size, reverse=True):
            for t in X.load_tables(str(xp)):
                if not is_bs_table(t):
                    continue
                for r in t.rows:
                    if not r.cells or not pat.search(r.cells[0]):
                        continue
                    for ci, c in enumerate(r.cells[1:], 1):
                        pv = X.printed_to_float(c)
                        if pv is None:
                            continue
                        for sc, nm in SCALES:
                            if abs(pv - value * sc) <= 0.51:
                                capt = " / ".join(t.captions[-3:])
                                hits.append({"xml": str(xp.relative_to(ROOT)).replace("\\", "/"), "table": t.index, "tline": t.line, "line": r.line,
                                             "captions": capt[:160], "unit": t.unit, "label": r.cells[0], "col": ci, "col_header": col_header(t, ci),
                                             "printed": c, "scale": nm, "hdr": " | ".join(" ".join(rr.cells) for rr in t.rows[:2])[:140],
                                             "is_consolidated": ("연결" in capt and "별도" not in capt)})
    return hits


rows_out = []
for c in plan["BS"]:
    hs = scan(c["code"], c["quarter"], c["item"], c["new"])
    hs_sep = [h for h in hs if not h["is_consolidated"]] or hs
    rec = {"block": c["block"], "item": c["item"], "old": c["old"], "new": c["new"], "n_hits": len(hs)}
    if hs_sep:
        h = hs_sep[0]
        rec.update(status="FOUND", **{k: h[k] for k in ("xml", "table", "tline", "line", "captions", "unit", "label", "col", "col_header", "printed", "scale", "is_consolidated", "hdr")})
    else:
        rec["status"] = "NOT_FOUND"
    rows_out.append(rec)
    print(rec["block"], "item", rec["item"], rec["status"], rec.get("printed"), rec.get("scale"), "| n", rec["n_hits"], "| L", rec.get("line"), "| col", rec.get("col"),
          "|", (rec.get("col_header") or "")[:50], "| consol" if rec.get("is_consolidated") else "")

cols = ["block", "item", "old", "new", "status", "n_hits", "xml", "table", "tline", "line", "captions", "unit", "label", "col", "col_header", "printed", "scale", "is_consolidated", "hdr"]
with open(HERE / "evidence_bs.csv", "w", encoding="utf-8-sig", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
    w.writeheader()
    w.writerows(rows_out)
print("FOUND", sum(1 for r in rows_out if r["status"] == "FOUND"), "NOT_FOUND", sum(1 for r in rows_out if r["status"] == "NOT_FOUND"))
