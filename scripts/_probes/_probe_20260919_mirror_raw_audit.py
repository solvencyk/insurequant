"""READ-ONLY 전수 audit: items 4/12/13 값_적용후 mirror cells vs raw 공통적용 경과조치 table.

For every (company, quarter) bucket that currently carries a 값_적용후 on item 4, 12 or 13,
parse the company's own 정기경영공시 MD and read the
"(1) 공통적용 경과조치" two-column table (경과조치 적용 전 | 경과조치 적용 후).

Verdict per bucket:
  RAW_TIER_MOVED   - 기본자본/보완자본 differ across the two columns -> mirroring 4/12/13 is contamination
  RAW_TIER_EQUAL   - both columns identical -> mirror numerically harmless
  RAW_HAS_412_13   - the raw two-column table actually prints 순자산/불인정/재분류 rows (then it is not a mirror at all)
  RAW_NO_TABLE     - no common-transition 2-col table found in MD (cannot measure)
  RAW_NO_FILE      - no parsed MD on disk (cannot measure)

Writes data/_derived/_probe_20260919_mirror_raw_audit.json
No mutation of any master. No build. No network.
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
OUT = ROOT / "data" / "_derived" / "_probe_20260919_mirror_raw_audit.json"

K_CODE, K_NAME, K_ITEM, K_Q, K_V, K_VA = (
    "원보험사코드", "원수사명", "항목번호", "공시분기", "값", "값_적용후")
TARGET_ITEMS = (4, 12, 13)
TOL = 0.01

APPLIERS = frozenset({
    "KR0070", "KR0071", "KR0072", "KR0073", "KR0076", "KR0082",
    "KR0083", "KR0097", "KR0100", "KR1010", "KR1011", "KR0104",
    "KR0049", "KR0002", "KR0003", "KR0004", "KR0005", "KR0032",
})

# raw row-label -> logical axis. compare on normalised (whitespace-stripped) label.
ROW_PATTERNS = {
    "ratio": [r"^지급여력비율", r"^지급여력\s*비율"],
    "amount": [r"^지급여력금액", r"^가\.?\s*지급여력금액"],
    "tier1": [r"^기본자본$", r"^기본자본\(", r"^-?\s*기본자본$"],
    "tier2": [r"^보완자본$", r"^보완자본\(", r"^-?\s*보완자본$"],
    "scr": [r"^지급여력기준금액", r"^나\.?\s*지급여력기준금액"],
    "netasset": [r"건전성감독기준.*순자산", r"^Ⅰ\.", r"^I\.\s*건전성"],
    "nonrecog": [r"불인정하는\s*항목", r"^Ⅱ\.", r"불인정항목"],
    "reclass": [r"보완자본으로\s*재분류", r"^Ⅲ\.", r"재분류하는\s*항목"],
}


def num(v):
    if v is None:
        return None
    s = str(v).replace(",", "").replace("△", "-").replace("Δ", "-").strip()
    s = s.replace("(", "-").replace(")", "")
    if s in ("", "-", "--"):
        return None
    try:
        return float(s)
    except ValueError:
        return None


def q_to_dir(q):
    y, qq = q.split(".")
    return f"FY{y}_Q{qq[0]}"


def find_md(code, q):
    d = ROOT / "data" / "disclosure" / q_to_dir(q) / "parsed"
    if not d.is_dir():
        return None
    cands = sorted(d.glob(f"{code}_*.md"))
    if not cands:
        return None
    # prefer the most-amended variant (same convention as the parser lane)
    cands.sort(key=lambda p: (p.name.count("amended"), len(p.name)))
    return cands[-1]


HDR_RE = re.compile(r"경과조치\s*적용\s*전")


def extract_common_tables(text):
    """Return list of dicts: {header:str, unit:str, rows:[(label, colvals[])], line:int}
    for every markdown table whose header row mentions '경과조치 적용 전'."""
    lines = text.splitlines()
    tables = []
    i = 0
    while i < len(lines):
        ln = lines[i]
        if ln.lstrip().startswith("|") and HDR_RE.search(ln):
            # header found; find the unit hint above
            unit = ""
            for back in range(max(0, i - 8), i):
                m = re.search(r"단위\s*[:：]\s*([^)\]]*)", lines[back])
                if m:
                    unit = m.group(1).strip()
            header = ln
            cols = [c.strip() for c in ln.strip().strip("|").split("|")]
            rows = []
            j = i + 1
            if j < len(lines) and set(lines[j].replace("|", "").replace(" ", "")) <= set("-:"):
                j += 1
            while j < len(lines) and lines[j].lstrip().startswith("|"):
                cells = [c.strip() for c in lines[j].strip().strip("|").split("|")]
                if cells:
                    rows.append((cells[0], cells[1:], j + 1))
                j += 1
            tables.append({"header_cols": cols, "unit": unit, "rows": rows, "line": i + 1})
            i = j
        else:
            i += 1
    return tables


def norm(lbl):
    return re.sub(r"\s+", "", lbl or "")


def classify_row(label):
    n = norm(label)
    for axis, pats in ROW_PATTERNS.items():
        for p in pats:
            if re.search(p.replace(r"\s*", ""), n):
                return axis
    return None


def pick_pre_post(table):
    """Given a table whose header mentions 경과조치 적용 전, return (pre_idx, post_idx)
    as indexes into the row's value list (header_cols[1:])."""
    cols = table["header_cols"]
    pre_i = post_i = None
    for k, c in enumerate(cols):
        cn = norm(c)
        if "경과조치적용전" in cn or cn.endswith("적용전"):
            pre_i = k
        if "경과조치적용후" in cn or cn.endswith("적용후"):
            post_i = k
    if pre_i is None or post_i is None:
        return None, None
    # row cells were split with cells[0] as label, cells[1:] as values
    return pre_i - 1, post_i - 1


def main():
    data = json.loads((ROOT / "kics_disclosure.json").read_text(encoding="utf-8"))
    idx = {}
    for r in data:
        idx.setdefault((r.get(K_CODE), r.get(K_Q)), {})[r.get(K_ITEM)] = r

    buckets = {}
    for (code, q), items in idx.items():
        hit = [n for n in TARGET_ITEMS
               if items.get(n) and items[n].get(K_VA) not in (None, "")]
        if hit:
            buckets[(code, q)] = hit

    results = []
    for (code, q), hit in sorted(buckets.items()):
        items = idx[(code, q)]
        name = next((items[n].get(K_NAME) for n in items if items[n].get(K_NAME)), code)
        rec = {"code": code, "name": name, "q": q, "items_with_post": sorted(hit),
               "applier": code in APPLIERS}
        # master-internal view of 1/2/3/14/27/28
        for n in (1, 2, 3, 14, 27, 28):
            row = items.get(n)
            if row:
                rec[f"m{n}_pre"] = row.get(K_V)
                rec[f"m{n}_post"] = row.get(K_VA)
        for n in TARGET_ITEMS:
            row = items.get(n)
            if row:
                rec[f"m{n}_pre"] = row.get(K_V)
                rec[f"m{n}_post"] = row.get(K_VA)

        md = find_md(code, q)
        if md is None:
            rec["verdict"] = "RAW_NO_FILE"
            results.append(rec)
            continue
        rec["md"] = str(md.relative_to(ROOT)).replace("\\", "/")
        text = md.read_text(encoding="utf-8", errors="replace")
        tables = extract_common_tables(text)
        best = None
        for t in tables:
            pi, qi = pick_pre_post(t)
            if pi is None:
                continue
            axes = {}
            for lbl, vals, lineno in t["rows"]:
                ax = classify_row(lbl)
                if ax is None or ax in axes:
                    continue
                if pi < len(vals) and qi < len(vals):
                    axes[ax] = (num(vals[pi]), num(vals[qi]), lbl, lineno)
            if "tier1" in axes or "tier2" in axes:
                if best is None or len(axes) > len(best[1]):
                    best = (t, axes)
        if best is None:
            rec["verdict"] = "RAW_NO_TABLE"
            rec["n_two_col_tables"] = len(tables)
            results.append(rec)
            continue

        t, axes = best
        rec["raw_line"] = t["line"]
        rec["raw_unit"] = t["unit"]
        rec["raw"] = {k: {"pre": v[0], "post": v[1], "label": v[2], "line": v[3]}
                      for k, v in axes.items()}
        has_412 = [k for k in ("netasset", "nonrecog", "reclass") if k in axes]
        rec["raw_has_412_13_rows"] = has_412

        moved = {}
        for ax in ("amount", "tier1", "tier2", "scr", "ratio"):
            if ax in axes:
                p, s = axes[ax][0], axes[ax][1]
                if p is None or s is None:
                    moved[ax] = None
                else:
                    moved[ax] = round(s - p, 4)
        rec["raw_delta"] = moved

        t1d = moved.get("tier1")
        t2d = moved.get("tier2")
        tier_moved = (t1d is not None and abs(t1d) > TOL) or (t2d is not None and abs(t2d) > TOL)
        if has_412:
            rec["verdict"] = "RAW_HAS_412_13"
        elif tier_moved:
            rec["verdict"] = "RAW_TIER_MOVED"
        elif t1d is None and t2d is None:
            rec["verdict"] = "RAW_TIER_UNREADABLE"
        else:
            rec["verdict"] = "RAW_TIER_EQUAL"
        results.append(rec)

    counts = {}
    for r in results:
        counts[r["verdict"]] = counts.get(r["verdict"], 0) + 1
    cell_counts = {}
    for r in results:
        cell_counts[r["verdict"]] = cell_counts.get(r["verdict"], 0) + len(r["items_with_post"])

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({
        "bucket_total": len(results),
        "cell_total": sum(len(r["items_with_post"]) for r in results),
        "verdict_buckets": counts,
        "verdict_cells": cell_counts,
        "rows": results,
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    print("buckets:", len(results), "cells:", sum(len(r['items_with_post']) for r in results))
    print("by verdict (buckets):", json.dumps(counts, ensure_ascii=False))
    print("by verdict (cells):", json.dumps(cell_counts, ensure_ascii=False))
    print("wrote", OUT)


if __name__ == "__main__":
    main()
