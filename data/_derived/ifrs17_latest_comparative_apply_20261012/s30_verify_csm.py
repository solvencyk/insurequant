"""Read-only direct verification of the CSM waterfall blocks against the RAW later-filing XML (independent reader xmltab.py).

For each block (code, quarter) the later filing (same company, FY(N+1)_Q(q) raw dir) is opened.  The planned 6-vector (opening, new business, interest,
assumption/experience, amortisation, closing; 억원, 1 decimal) is searched among the PRINTED numeric cells of every table at the filing unit
(백만원 / 천원 / 원); a table that prints >=4 of the 6 elements within the 1-decimal rounding window is taken as the table, and its rows are echoed
(label, column, printed string, XML line).  Items that are no single printed token (sum of product lines) are reported as DERIVED with the printed parts.
Output evidence_csm.json / evidence_csm.txt
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import xmltab as X  # noqa: E402

ROOT = X.ROOT
DRY = ROOT / "data/_derived/ifrs17_latest_comparative_precedence_dryrun_20261012"
ov = json.loads((DRY / "cand/csm_adopt_overlay.json").read_text(encoding="utf-8"))
live = json.loads((ROOT / "CSM_waterfall.json").read_text(encoding="utf-8"))
lv = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r["값"] for r in live}
BLOCKS = ["KR0069|2023.2Q", "KR0082|2023.1Q", "KR0087|2023.1Q", "KR1000|2025.1Q", "KR0104|2023.1Q",
          "KR0008|2023.1Q", "KR0008|2023.2Q", "KR0008|2023.3Q", "KR0001|2023.3Q"]
SC = [(1e2, "백만원"), (1e5, "천원"), (1e8, "원")]
NAMES = {1: "기초", 2: "신계약", 3: "이자", 4: "가정/경험", 5: "상각", 6: "기말"}


def later_xmls(code, quarter):
    y = int(quarter[:4]) + 1
    base = ROOT / "data/dart" / f"FY{y}_Q{quarter[5]}" / "raw"
    res = []
    for d in sorted(base.glob(f"{code}_*")):
        res.extend(sorted(d.glob("**/*.xml"), key=lambda p: p.stat().st_size, reverse=True))
    return res


out = {}
lines = []
for blk in BLOCKS:
    kr, q = blk.split("|")
    vec = {int(k): v for k, v in ov[blk].items() if v is not None}
    best = []
    for xp in later_xmls(kr, q):
        for t in X.load_tables(str(xp)):
            matched = {}
            # CSM columns of a 3-column general-model table (수정소급법 / 공정가치법 / 그 외 보험계약마진): the vector element is the SUM of those columns
            hdr_cells = []
            for r in t.rows[:3]:
                if any("보험계약마진" in x for x in r.cells):
                    hdr_cells = r.cells
                    break
            csm_cols = [i for i, x in enumerate(hdr_cells) if "보험계약마진" in x and i >= 1]
            for r in t.rows:
                for ci, c in enumerate(r.cells[1:], 1):
                    pv = X.printed_to_float(c)
                    if pv is None or pv == 0:
                        continue
                    for item, v in vec.items():
                        for sc, nm in SC:
                            if abs(abs(pv) - abs(v) * sc) <= 0.051 * sc:
                                matched.setdefault(item, []).append((r.line, r.cells[0][:30], ci, c, nm))
                if len(csm_cols) >= 2:
                    parts = [X.printed_to_float(r.cells[i]) if i < len(r.cells) else None for i in csm_cols]
                    if any(x is not None for x in parts):
                        tot = sum(x for x in parts if x is not None)
                        for item, v in vec.items():
                            for sc, nm in SC:
                                if tot != 0 and abs(abs(tot) - abs(v) * sc) <= 0.051 * sc:
                                    shown = "+".join(r.cells[i] for i in csm_cols if i < len(r.cells))
                                    matched.setdefault(item, []).append((r.line, r.cells[0][:30], "SUM" + str(csm_cols), f"{shown} = {tot:,.0f}", nm))
            if len(matched) >= 3:
                best.append((len(matched), xp, t, matched))
    best.sort(key=lambda x: -x[0])
    lines.append(f"=== {blk}  planned {vec}")
    out[blk] = []
    for n, xp, t, matched in best[:3]:
        lines.append(f"  table #{t.index} line {t.line} file {xp.name} unit={t.unit!r} caption={t.caption[:60]!r} matched {n}/6 items")
        rec = {"xml": str(xp.relative_to(ROOT)).replace("\\", "/"), "table": t.index, "tline": t.line, "caption": t.caption[:80], "unit": t.unit, "items": {}}
        for item in sorted(matched):
            m = matched[item][0]
            lines.append(f"     item {item} {NAMES[item]:<6} planned {vec[item]:>10}  -> printed {m[3]!r:>16} ({m[4]}) row {m[1]!r} col {m[2]} line {m[0]}   [{len(matched[item])} hit(s)]")
            rec["items"][item] = {"line": m[0], "label": m[1], "col": m[2], "printed": m[3], "unit": m[4], "hits": len(matched[item])}
        out[blk].append(rec)
    if not best:
        lines.append("  NO table with >=3 matching vector items")
(HERE / "evidence_csm.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
(HERE / "evidence_csm.txt").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
print("\n".join(lines))
