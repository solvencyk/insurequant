"""READ-ONLY 전수 audit v3 of the item 4/12/13 `값_적용후` mirror.

Three independent axes per (company, quarter) bucket:
  A. golden extractor (scripts/fill_post_transition_to_disclosure) 공통적용 2-col table
  B. tolerant fallback scanner for docling-mangled headers ("적용 전 경과조치 | 적용 후")
  C. data/_derived/kics_transition_applicability.json TFI verdict (O/X/NA/UNKNOWN)

Verdicts:
  CONTAMINATED        tier split (item2/3) verifiably moved across the two columns
  BENIGN_TFI_NOT_APPLIED  issuer states TFI=X/NA -> 전=후 by the issuer's own words
  BENIGN_TIER_EQUAL   2-col table read and tier identical
  UNMEASURED_*        could not measure (per-cell, reported, never silently passed)

Writes data/_derived/_probe_20260919_mirror_audit_v3.json
No mutation, no build, no network.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import fill_post_transition_to_disclosure as FP  # noqa: E402

OUT = ROOT / "data" / "_derived" / "_probe_20260919_mirror_audit_v3.json"
APPLIC = ROOT / "data" / "_derived" / "kics_transition_applicability.json"

K_CODE, K_NAME, K_ITEM, K_Q, K_V, K_VA = (
    "원보험사코드", "원수사명", "항목번호", "공시분기", "값", "값_적용후")
TARGET_ITEMS = (4, 12, 13)
TOL = 0.01

APPLIERS = frozenset({
    "KR0070", "KR0071", "KR0072", "KR0073", "KR0076", "KR0082",
    "KR0083", "KR0097", "KR0100", "KR1010", "KR1011", "KR0104",
    "KR0049", "KR0002", "KR0003", "KR0004", "KR0005", "KR0032",
})

_NEG = re.compile(r"공통\s*적용\s*경과조치[^\n]{0,40}(적용하지\s*않|해당\s*사항\s*없|해당사항없)")


def num(v):
    if v is None:
        return None
    s = str(v).replace(",", "").replace("△", "-").strip()
    s = s.replace("%", "")
    if s in ("", "-", "ㅡ", "–", "—"):
        return None
    try:
        return float(s)
    except ValueError:
        return None


# ---------------- axis B: tolerant fallback scan ---------------------------
def _norm(s):
    return re.sub(r"\s+", "", s or "")


def fallback_scan(text):
    """Find the 공통적용 two-column table even when docling mangles the header.
    Returns dict axis -> (pre, post, label, lineno, unit) or None."""
    lines = text.splitlines()
    # locate the 공통적용 anchor; fall back to any 경과조치-적용-전 header
    anchors = [i for i, ln in enumerate(lines) if "공통적용" in _norm(ln)]
    cands = []
    for a in anchors:
        for j in range(a, min(len(lines), a + 30)):
            if lines[j].lstrip().startswith("|"):
                cands.append(j)
                break
    if not cands:
        for i, ln in enumerate(lines):
            if ln.lstrip().startswith("|") and "적용전" in _norm(ln) and "적용후" in _norm(ln):
                cands.append(i)
    for hdr in cands:
        cols = [c.strip() for c in lines[hdr].strip().strip("|").split("|")]
        pre_i = post_i = None
        for k, c in enumerate(cols):
            cn = _norm(c)
            if pre_i is None and cn.endswith("적용전"):
                pre_i = k
            if post_i is None and (cn.endswith("적용후") or cn == "적용후"):
                post_i = k
        if pre_i is None or post_i is None or pre_i == post_i:
            continue
        unit = ""
        for b in range(max(0, hdr - 8), hdr):
            m = re.search(r"단위\s*[:：]?\s*([^)\]]*)", lines[b])
            if m:
                unit = _norm(m.group(1))
        out = {}
        j = hdr + 1
        if j < len(lines) and set(lines[j].replace("|", "").replace(" ", "")) <= set("-:"):
            j += 1
        while j < len(lines) and lines[j].lstrip().startswith("|"):
            cells = [c.strip() for c in lines[j].strip().strip("|").split("|")]
            lbl = _norm(cells[0]) if cells else ""
            ax = None
            if lbl.startswith("기본자본"):
                ax = "tier1"
            elif lbl.startswith("보완자본") and "한도" not in lbl:
                ax = "tier2"
            elif lbl.startswith("지급여력기준금액"):
                ax = "scr"
            elif lbl.startswith("지급여력금액"):
                ax = "amount"
            elif lbl.startswith("지급여력비율"):
                ax = "ratio"
            elif lbl.startswith("보완자본한도적용전"):
                ax = "t2_prelimit"
            if ax and ax not in out and max(pre_i, post_i) < len(cells):
                pre_raw, post_raw = cells[pre_i], cells[post_i]
                # docling sometimes merges "263.14 263.14" into one cell
                if num(pre_raw) is None and len(pre_raw.split()) == 2:
                    a2, b2 = pre_raw.split()
                    pre_raw, post_raw = a2, b2
                elif post_raw == "" and len(pre_raw.split()) == 2:
                    a2, b2 = pre_raw.split()
                    pre_raw, post_raw = a2, b2
                out[ax] = (num(pre_raw), num(post_raw), cells[0], j + 1,
                           post_raw, unit)
            j += 1
        if "tier1" in out or "tier2" in out:
            out["_hdr_line"] = hdr + 1
            out["_unit"] = unit
            return out
    return None


def main():
    data = json.loads((ROOT / "kics_disclosure.json").read_text(encoding="utf-8"))
    midx = {}
    for r in data:
        midx.setdefault((r.get(K_CODE), r.get(K_Q)), {})[r.get(K_ITEM)] = r

    app = {}
    ad = json.loads(APPLIC.read_text(encoding="utf-8"))
    for rec in ad["records"]:
        app[(rec["code"], rec["quarter"])] = rec

    # md path index
    mdmap = {}
    for pdir in sorted(FP.MD_INBOX.glob("FY*_Q?")):
        if not pdir.is_dir():
            continue
        q = FP._md_period_to_quarter(pdir.name)
        for md in sorted(pdir.glob("*.md")):
            mdmap[(md.stem.split("_", 1)[0], q)] = md

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

        a = app.get((code, q))
        rec["TFI"] = a.get("TFI") if a else "NO_RECORD"
        rec["TFI_evidence"] = (a.get("evidence", {}) if a else {})

        md = mdmap.get((code, q))
        rec["md"] = str(md.relative_to(ROOT)).replace("\\", "/") if md else None
        got, fb = {}, None
        if md:
            text = md.read_text(encoding="utf-8", errors="replace")
            rec["md_lines"] = len(text.splitlines())
            rec["md_negation"] = bool(_NEG.search(_norm(text)) or
                                      "공통적용경과조치를적용하지않아" in _norm(text))
            try:
                pm, pv, _d, _u = FP._extract_post_values(
                    FP._scan_tables_with_context(text), code,
                    {it: r0.get(K_V) for it, r0 in items.items()})
                got = pm
            except Exception as exc:
                rec["extractor_error"] = f"{type(exc).__name__}: {exc}"
            fb = fallback_scan(text)

        def d_of(pair):
            if not pair:
                return None
            x, y = num(pair[0]), num(pair[1])
            return None if (x is None or y is None) else round(y - x, 4)

        rec["axisA"] = {str(k): list(v) for k, v in sorted(got.items())
                        if k in (1, 2, 3, 14, 27)}
        rec["axisA_delta"] = {"item2": d_of(got.get(2)), "item3": d_of(got.get(3)),
                              "item1": d_of(got.get(1)), "item14": d_of(got.get(14))}
        if fb:
            rec["axisB"] = {k: v for k, v in fb.items() if not k.startswith("_")}
            rec["axisB_hdr_line"] = fb.get("_hdr_line")
            rec["axisB_unit"] = fb.get("_unit")
            rec["axisB_delta"] = {}
            for ax in ("tier1", "tier2", "amount", "scr", "t2_prelimit"):
                v = fb.get(ax)
                rec["axisB_delta"][ax] = (None if not v or v[0] is None or v[1] is None
                                          else round(v[1] - v[0], 4))

        moved = None
        src = None
        da = rec["axisA_delta"]
        if da.get("item2") is not None or da.get("item3") is not None:
            moved = any(abs(x) > TOL for x in (da.get("item2"), da.get("item3")) if x is not None)
            src = "A"
        elif fb:
            db = rec.get("axisB_delta", {})
            if db.get("tier1") is not None or db.get("tier2") is not None:
                moved = any(abs(x) > TOL for x in (db.get("tier1"), db.get("tier2"))
                            if x is not None)
                src = "B"
        rec["tier_moved"] = moved
        rec["tier_src"] = src

        if moved is True:
            rec["verdict"] = "CONTAMINATED"
        elif moved is False:
            rec["verdict"] = "BENIGN_TIER_EQUAL"
        elif rec["TFI"] in ("X", "NA"):
            rec["verdict"] = "BENIGN_TFI_NOT_APPLIED"
        elif rec.get("md_negation"):
            rec["verdict"] = "BENIGN_TFI_NOT_APPLIED"
        elif rec["TFI"] == "O":
            rec["verdict"] = "UNMEASURED_TFI_O_NO_TABLE"
        else:
            rec["verdict"] = "UNMEASURED_TFI_UNKNOWN"
        rows.append(rec)

    counts, cells = {}, {}
    for r in rows:
        counts[r["verdict"]] = counts.get(r["verdict"], 0) + 1
        cells[r["verdict"]] = cells.get(r["verdict"], 0) + len(r["mirrored_items"])

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({
        "buckets": len(rows), "cells": sum(len(r["mirrored_items"]) for r in rows),
        "verdict_buckets": counts, "verdict_cells": cells, "rows": rows,
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    print("buckets:", len(rows), "cells:", sum(len(r['mirrored_items']) for r in rows))
    print("verdict buckets:", json.dumps(counts, ensure_ascii=False))
    print("verdict cells:  ", json.dumps(cells, ensure_ascii=False))
    print("wrote", OUT)


if __name__ == "__main__":
    main()
