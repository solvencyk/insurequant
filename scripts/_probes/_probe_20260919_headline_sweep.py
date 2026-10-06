"""READ-ONLY sweep: does the master's item1/2/3/14/27 `값_적용후` agree with the
company's own 공통적용 경과조치 table (golden extractor) for EVERY (company, quarter)?

This is the wider version of the item 4/12/13 mirror audit: the same blind spot
('적용후' column never re-anchored to raw) applied to the headline tier pair that
the site actually renders and that R1/R8_post consume.

Writes data/_derived/_probe_20260919_headline_sweep.json
No mutation, no build, no network.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import fill_post_transition_to_disclosure as FP  # noqa: E402

OUT = ROOT / "data" / "_derived" / "_probe_20260919_headline_sweep.json"
K_CODE, K_NAME, K_ITEM, K_Q, K_V, K_VA = (
    "원보험사코드", "원수사명", "항목번호", "공시분기", "값", "값_적용후")
ITEMS = (1, 2, 3, 14, 27)
TOL = {1: 2.0, 2: 2.0, 3: 2.0, 14: 2.0, 27: 0.5}


def num(v):
    if v is None:
        return None
    s = str(v).replace(",", "").replace("△", "-").replace("%", "").strip()
    if s in ("", "-", "ㅡ"):
        return None
    try:
        return float(s)
    except ValueError:
        return None


def main():
    data = json.loads((ROOT / "kics_disclosure.json").read_text(encoding="utf-8"))
    midx = {}
    for r in data:
        midx.setdefault((r.get(K_CODE), r.get(K_Q)), {})[r.get(K_ITEM)] = r

    findings = []
    stats = {"buckets_with_raw_table": 0, "buckets_total": 0}
    for pdir in sorted(FP.MD_INBOX.glob("FY*_Q?")):
        if not pdir.is_dir():
            continue
        q = FP._md_period_to_quarter(pdir.name)
        for md in sorted(pdir.glob("*.md")):
            code = md.stem.split("_", 1)[0]
            items = midx.get((code, q))
            if not items:
                continue
            stats["buckets_total"] += 1
            text = md.read_text(encoding="utf-8", errors="replace")
            try:
                got, prov, _d, _u = FP._extract_post_values(
                    FP._scan_tables_with_context(text), code,
                    {it: r0.get(K_V) for it, r0 in items.items()})
            except Exception:
                continue
            if not any(k in got for k in ITEMS):
                continue
            stats["buckets_with_raw_table"] += 1
            name = next((r0.get(K_NAME) for r0 in items.values() if r0.get(K_NAME)), code)
            for it in ITEMS:
                pair = got.get(it)
                if not pair:
                    continue
                rpre, rpost = num(pair[0]), num(pair[1])
                if rpre is None or rpost is None:
                    continue
                row = items.get(it)
                if row is None:
                    continue
                mpre, mpost = num(row.get(K_V)), num(row.get(K_VA))
                raw_moved = abs(rpost - rpre) > 0.01
                if mpost is None:
                    kind = "MASTER_POST_MISSING" if raw_moved else None
                elif mpre is not None and abs(mpost - mpre) <= 0.01 and raw_moved:
                    kind = "MASTER_POST_STALE(=pre, raw moved)"
                elif abs(mpost - rpost) > TOL[it]:
                    kind = "MASTER_POST_NE_RAW"
                else:
                    kind = None
                if kind:
                    findings.append({
                        "code": code, "name": name, "q": q, "item": it, "kind": kind,
                        "raw_pre": pair[0], "raw_post": pair[1],
                        "master_pre": row.get(K_V), "master_post": row.get(K_VA),
                        "raw_delta": round(rpost - rpre, 4),
                        "src_table": prov.get(it),
                        "md": str(md.relative_to(ROOT)).replace("\\", "/"),
                    })

    from collections import Counter
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({
        "stats": stats,
        "by_kind": dict(Counter(f["kind"] for f in findings)),
        "by_item": dict(Counter(f["item"] for f in findings)),
        "by_company": dict(Counter(f"{f['code']} {f['name']}" for f in findings)),
        "findings": findings,
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    print("stats:", stats)
    print("by kind:", dict(Counter(f["kind"] for f in findings)))
    print("by item:", dict(Counter(f["item"] for f in findings)))
    print("total findings:", len(findings))
    print("wrote", OUT)


if __name__ == "__main__":
    main()
