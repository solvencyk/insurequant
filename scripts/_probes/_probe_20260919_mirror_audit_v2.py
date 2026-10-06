"""READ-ONLY 전수 audit of the item 4/12/13 `값_적용후` mirror.

Ground truth for the 공통적용 경과조치 two-column table is taken from the
repo's own golden-tested extractor (`scripts/fill_post_transition_to_disclosure.py`
`_scan_tables_with_context` + `_extract_post_values`) so that this audit reads
the *same* table, with the same unit/column heuristics, that produced the
master's own item1/2/3/14/27 적용후 values. No re-typing of table logic.

For every (company, quarter) bucket carrying a `값_적용후` on item 4, 12 or 13:
  * read item2(기본자본)/item3(보완자본)/item1/item14 pre & post from raw
  * decide whether the tier split actually moved
  * decide whether the mirrored 4/12/13 triple is arithmetically consistent
    with the disclosed item2 적용후 (identity item2 = item4 - item12 - item13)
  * record direction of the error

Writes data/_derived/_probe_20260919_mirror_audit_v2.json
No mutation, no build, no network.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import fill_post_transition_to_disclosure as FP  # noqa: E402

OUT = ROOT / "data" / "_derived" / "_probe_20260919_mirror_audit_v2.json"

K_CODE, K_NAME, K_ITEM, K_Q, K_V, K_VA = (
    "원보험사코드", "원수사명", "항목번호", "공시분기", "값", "값_적용후")
TARGET_ITEMS = (4, 12, 13)
TOL = 0.01
IDENTITY_TOL = 2.0  # 억원, same as R1/R2 in the rule engine

APPLIERS = frozenset({
    "KR0070", "KR0071", "KR0072", "KR0073", "KR0076", "KR0082",
    "KR0083", "KR0097", "KR0100", "KR1010", "KR1011", "KR0104",
    "KR0049", "KR0002", "KR0003", "KR0004", "KR0005", "KR0032",
})


def num(v):
    if v is None:
        return None
    s = str(v).replace(",", "").replace("△", "-").strip()
    if s in ("", "-"):
        return None
    try:
        return float(s)
    except ValueError:
        return None


def q_to_period(q):
    y, qq = q.split(".")
    return f"FY{y}_Q{qq[0]}"


def build_raw_index(master_index):
    """(code, quarter) -> {item_no: (pre, post)} straight from md_inbox."""
    raw = {}
    for pdir in sorted(FP.MD_INBOX.glob("FY*_Q?")):
        if not pdir.is_dir():
            continue
        quarter = FP._md_period_to_quarter(pdir.name)
        for md in sorted(pdir.glob("*.md")):
            code = md.stem.split("_", 1)[0]
            text = md.read_text(encoding="utf-8", errors="replace")
            tables = FP._scan_tables_with_context(text)
            existing = {}
            for it, row in master_index.get((code, quarter), {}).items():
                existing[it] = row.get(K_V)
            try:
                post_map, prov, _dbg, _uf = FP._extract_post_values(tables, code, existing)
            except Exception as exc:  # keep the audit running; record the failure
                raw[(code, quarter)] = {"_error": f"{type(exc).__name__}: {exc}",
                                        "_md": str(md.relative_to(ROOT)).replace("\\", "/")}
                continue
            d = {str(k): v for k, v in post_map.items()}
            d["_md"] = str(md.relative_to(ROOT)).replace("\\", "/")
            d["_prov"] = {str(k): v for k, v in prov.items()}
            raw[(code, quarter)] = d
    return raw


def main():
    data = json.loads((ROOT / "kics_disclosure.json").read_text(encoding="utf-8"))
    midx = {}
    for r in data:
        midx.setdefault((r.get(K_CODE), r.get(K_Q)), {})[r.get(K_ITEM)] = r

    raw = build_raw_index(midx)

    rows = []
    for (code, q), items in sorted(midx.items()):
        hit = [n for n in TARGET_ITEMS
               if items.get(n) and items[n].get(K_VA) not in (None, "")]
        if not hit:
            continue
        name = next((items[n].get(K_NAME) for n in items if items[n].get(K_NAME)), code)
        rec = {"code": code, "name": name, "q": q, "mirrored_items": sorted(hit),
               "elective_applier": code in APPLIERS}
        for n in (1, 2, 3, 4, 12, 13, 14, 27, 28):
            row = items.get(n)
            rec[f"m{n}"] = [row.get(K_V), row.get(K_VA)] if row else None

        rr = raw.get((code, q))
        if rr is None:
            rec["raw_status"] = "NO_MD_FILE"
            rows.append(rec)
            continue
        rec["md"] = rr.get("_md")
        if "_error" in rr:
            rec["raw_status"] = "EXTRACTOR_ERROR"
            rec["raw_error"] = rr["_error"]
            rows.append(rec)
            continue
        got = {int(k): v for k, v in rr.items() if k.isdigit()}
        rec["raw"] = {str(k): list(v) for k, v in sorted(got.items())}
        rec["raw_prov"] = rr.get("_prov")

        t1 = got.get(2)
        t2 = got.get(3)
        if t1 is None and t2 is None:
            rec["raw_status"] = "NO_TIER_ROWS"
            rows.append(rec)
            continue
        rec["raw_status"] = "OK"

        def delta(pair):
            if pair is None:
                return None
            a, b = num(pair[0]), num(pair[1])
            if a is None or b is None:
                return None
            return round(b - a, 4)

        d2, d3 = delta(t1), delta(t2)
        d1, d14 = delta(got.get(1)), delta(got.get(14))
        rec["raw_delta"] = {"item1": d1, "item2": d2, "item3": d3, "item14": d14}
        tier_moved = (d2 is not None and abs(d2) > TOL) or (d3 is not None and abs(d3) > TOL)
        rec["tier_moved"] = tier_moved

        # identity check on the 적용후 column: item2_post ?= item4_post - item12_post - item13_post
        def mv(n, col):
            p = rec.get(f"m{n}")
            return num(p[col]) if p else None

        i4a, i12a, i13a = mv(4, 1), mv(12, 1), mv(13, 1)
        i4b, i12b, i13b = mv(4, 0), mv(12, 0), mv(13, 0)
        i2b, i2a = mv(2, 0), mv(2, 1)
        if None not in (i4b, i12b, i13b, i2b):
            rec["identity_pre_resid"] = round(i4b - i12b - i13b - i2b, 3)
        if None not in (i4a, i12a, i13a, i2a):
            rec["identity_post_resid"] = round(i4a - i12a - i13a - i2a, 3)

        rows.append(rec)

    # ---- verdicts
    for rec in rows:
        st = rec.get("raw_status")
        if st != "OK":
            rec["verdict"] = f"UNMEASURED_{st}"
            continue
        if rec.get("tier_moved"):
            rec["verdict"] = "CONTAMINATED"
        else:
            rec["verdict"] = "BENIGN_TIER_EQUAL"

    counts, cells = {}, {}
    for rec in rows:
        counts[rec["verdict"]] = counts.get(rec["verdict"], 0) + 1
        cells[rec["verdict"]] = cells.get(rec["verdict"], 0) + len(rec["mirrored_items"])

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({
        "buckets": len(rows),
        "cells": sum(len(r["mirrored_items"]) for r in rows),
        "verdict_buckets": counts,
        "verdict_cells": cells,
        "rows": rows,
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    print("buckets:", len(rows), "cells:", sum(len(r['mirrored_items']) for r in rows))
    print("verdict buckets:", json.dumps(counts, ensure_ascii=False))
    print("verdict cells:  ", json.dumps(cells, ensure_ascii=False))
    print("wrote", OUT)


if __name__ == "__main__":
    main()
