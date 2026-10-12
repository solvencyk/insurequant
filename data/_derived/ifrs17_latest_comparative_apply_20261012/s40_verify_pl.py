"""Read-only direct verification (token level) of the planned PL cells against the RAW later-filing XML (independent reader xmltab.py).

Every planned PL cell (company, quarter, item, new value in 백만원) is searched among the PRINTED numeric cells of all tables of the later filing
(same company, FY(N+1)_Q(q) raw dir; abs values compared at 원 / 천원 / 백만원 scale, +-0.51 of the printed unit).  A hit records table index, XML line, row label,
column and the printed string.  Cells that are not a single printed token (sums / residuals of the builder) are reported as NO_TOKEN and are checked
by the identity script instead.  Output evidence_pl_tokens.json / .txt
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import xmltab as X  # noqa: E402

ROOT = X.ROOT
plan = json.loads((HERE / "plan_diff.json").read_text(encoding="utf-8"))
SC = [(1e6, "원"), (1e3, "천원"), (1.0, "백만원")]
STMT_HINT = ("손익계산서", "포괄손익")


def later_xmls(code, quarter):
    y = int(quarter[:4]) + 1
    base = ROOT / "data/dart" / f"FY{y}_Q{quarter[5]}" / "raw"
    res = []
    for d in sorted(base.glob(f"{code}_*")):
        res.extend(sorted(d.glob("**/*.xml"), key=lambda p: p.stat().st_size, reverse=True))
    return res


# index printed tokens per later filing once: list of (abs value, scale name, record)
cache = {}


def tokens(code, quarter):
    k = (code, quarter)
    if k in cache:
        return cache[k]
    toks = []
    for xp in later_xmls(code, quarter):
        for t in X.load_tables(str(xp)):
            for r in t.rows:
                for ci, c in enumerate(r.cells[1:], 1):
                    pv = X.printed_to_float(c)
                    if pv is None or pv == 0:
                        continue
                    toks.append((abs(pv), c, r.line, r.cells[0][:40], ci, t.index, t.caption[:50], xp.name, " | ".join(" ".join(rr.cells) for rr in t.rows[:2])[:90]))
    cache[k] = toks
    return toks


by_block = defaultdict(list)
for c in plan["PL"]:
    by_block[c["block"]].append(c)

res = {}
lines = []
for blk, cells in by_block.items():
    kr, q = blk.split("|")
    tk = tokens(kr, q)
    lines.append(f"=== {blk}  later filing tokens {len(tk)}")
    res[blk] = []
    for c in sorted(cells, key=lambda x: x["item"]):
        v = abs(c["new"])
        hits = []
        for (pv, raw, line, lab, ci, tidx, cap, xname, hdr) in tk:
            for sc, nm in SC:
                if abs(pv - v * sc) <= 0.51:
                    hits.append((raw, nm, line, lab, ci, tidx, cap, hdr))
                    break
        rec = {"item": c["item"], "old": c["old"], "new": c["new"], "n_hits": len(hits)}
        if hits:
            rec["hits"] = [{"printed": h[0], "unit": h[1], "line": h[2], "label": h[3], "col": h[4], "table": h[5], "caption": h[6], "hdr": h[7]} for h in hits[:6]]
        res[blk].append(rec)
        first = hits[0] if hits else None
        lines.append(f"  item {c['item']:>2} old {c['old']!s:>16} new {c['new']:>16.6f} -> " +
                     (f"{len(hits):>3} hit(s) first: {first[0]!r} {first[1]} L{first[2]} row {first[3]!r} col {first[4]} tbl#{first[5]} cap {first[6]!r}" if first else "NO_TOKEN"))
(HERE / "evidence_pl_tokens.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
(HERE / "evidence_pl_tokens.txt").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
print("\n".join(lines))
