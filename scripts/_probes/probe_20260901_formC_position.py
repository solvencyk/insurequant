"""FORM_C shape: where inside source_page_ranges does the dropped page sit?

Hypotheses to separate:
  H1 tail truncation  -> dropped page is near the END of its contiguous range
  H2 page-level drop  -> dropped page sits mid-range (docling processed pages
                         after it, so the range was not truncated)
Also prints the range that contains it and its offset from both ends.
"""

from __future__ import annotations

import io
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
CENSUS = REPO / "data" / "_derived" / "_probe_docling_3forms_census.json"


def _ranges(spec: str) -> list[tuple[int, int]]:
    out = []
    for chunk in (spec or "").split(";"):
        chunk = chunk.strip()
        if not chunk:
            continue
        a, _, b = chunk.partition("-")
        try:
            out.append((int(a), int(b or a)))
        except ValueError:
            continue
    return out


def main() -> int:
    census = json.loads(CENSUS.read_text(encoding="utf-8"))
    print("\n=== FORM_C page position inside its docling range ===\n")
    print(f"{'code':<8}{'page':>5}  {'range':>10}{'len':>5}{'from_start':>11}{'from_end':>9}  anchors")
    print("-" * 100)
    rows = []
    for r in census:
        if r.get("error"):
            continue
        rngs = _ranges(r["source_page_ranges"])
        seen: dict[int, list[str]] = {}
        for key, a in r["anchors"].items():
            if a["verdict"] != "FORM_C":
                continue
            for p in a["in_selected"]:
                seen.setdefault(p, []).append(key)
        for p in sorted(seen):
            owner = next(((s, e) for s, e in rngs if s <= p <= e), None)
            if owner is None:
                continue
            s, e = owner
            rows.append(
                {
                    "company": r["company"],
                    "page": p,
                    "range": f"{s}-{e}",
                    "range_len": e - s + 1,
                    "from_start": p - s,
                    "from_end": e - p,
                    "anchors": seen[p],
                    "all_ranges": r["source_page_ranges"],
                }
            )
            print(
                f"{r['company']:<8}{p:>5}  {s}-{e:<8}{e - s + 1:>5}{p - s:>11}{e - p:>9}  {','.join(seen[p])}"
            )
    out = REPO / "data" / "_derived" / "_probe_formC_position.json"
    out.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    n_tail = sum(1 for x in rows if x["from_end"] <= 2)
    print(f"\ntotal FORM_C pages = {len(rows)}   at range tail (from_end<=2) = {n_tail}")
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
