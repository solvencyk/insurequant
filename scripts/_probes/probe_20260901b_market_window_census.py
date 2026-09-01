# -*- coding: utf-8 -*-
"""2026.2Q 39-company census: does the CURRENT md_inbox MD reproduce items
36-40 (extract_mkt_subs) vs what's already stored in kics_disclosure.json?

This is independent of what's already in the master -- it measures whether
today's MD is a *reproducible source* for the master's 36-40 values, which is
the "landmine" class the inbox ticket 20260831T0700Z's validation memo found
for KR0069 (master right, MD can no longer reproduce it because the MD was
parsed before the keyword-list fix landed).

Classifies each of the 39 companies' 2026.2Q filing into:
  MD_FULL       - MD reproduces >=4 of 36-40 AND sqrt(V'MV) reconciles item19 <2%
  MD_PARTIAL    - MD reproduces 1-3, or >=4 but doesn't reconcile
  MD_NONE       - MD reproduces 0 of 36-40 (whole breakdown table missing from MD)
  and separately reports whether the MASTER already has all 5 of 36-40 for
  that (company, quarter), so we can tell "still a real gap" apart from
  "master fine, MD is a landmine".
"""
from __future__ import annotations
import glob
import io
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import fill_market_subitems_to_disclosure as F  # noqa: E402

JSON_PATH = REPO / "kics_disclosure.json"
MD_DIR = REPO / "md_inbox" / "FY2026_Q2"
QUARTER = "2026.2Q"


def read_front_matter(text: str) -> dict:
    if not text.startswith("---"):
        return {}
    _, _, rest = text.partition("---\n")
    front, _, _ = rest.partition("\n---\n")
    meta = {}
    for raw in front.splitlines():
        if ":" not in raw:
            continue
        k, _, v = raw.partition(":")
        meta[k.strip()] = v.strip().strip('"')
    return meta


def main():
    rows = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    master36_40 = {}  # code -> set(item_no) present in master for QUARTER
    item19 = {}
    name = {}
    for r in rows:
        if r.get("공시분기") != QUARTER:
            continue
        code = r["원보험사코드"]
        name[code] = r["원수사명"]
        it = int(r["항목번호"])
        val = F._parse_value(str(r.get("값", "")))
        if it == 19 and val is not None:
            item19[code] = float(val)
        if 36 <= it <= 40 and val is not None:
            master36_40.setdefault(code, set()).add(it)

    codes = sorted(name.keys())
    print(f"39-company roster from master @ {QUARTER}: {len(codes)} companies\n")

    results = []
    for code in codes:
        g = sorted(glob.glob(str(MD_DIR / f"{code}_*.md")))
        if not g:
            results.append((code, name[code], "NO_MD", None, None, {}, {}))
            continue
        md_path = Path(g[0])
        text = md_path.read_text(encoding="utf-8")
        meta = read_front_matter(text)
        subs = F.extract_mkt_subs(text)
        found = sorted(subs)
        master_have = master36_40.get(code, set())
        v19 = item19.get(code)

        if len(found) >= 4:
            v5 = [float(F._to_eok(*subs.get(i, ("0", "백만원")))) for i in (36, 37, 38, 39, 40)]
            est = F.mkt_est(v5)
            rel = abs(est - v19) / v19 * 100 if v19 else None
            md_status = "MD_FULL" if (v19 and rel is not None and rel < 2) else "MD_PARTIAL"
        elif len(found) == 0:
            md_status = "MD_NONE"
        else:
            md_status = "MD_PARTIAL"

        master_status = "MASTER_FULL" if len(master_have) >= 5 else f"MASTER_MISSING({sorted(set(range(36,41))-master_have)})"
        results.append((code, name[code], md_status, master_status, meta, found, subs))

    # Summary counts
    from collections import Counter
    md_counts = Counter(r[2] for r in results)
    print("MD reproducibility (current md_inbox, extract_mkt_subs):")
    for k, v in md_counts.items():
        print(f"  {k}: {v}")
    print()

    landmine = [r for r in results if r[2] != "MD_FULL" and r[3] == "MASTER_FULL"]
    real_gap = [r for r in results if r[2] != "MD_FULL" and r[3] != "MASTER_FULL"]
    print(f"LANDMINE (master already complete, but current MD would NOT reproduce it): {len(landmine)}")
    for code, nm, md_status, master_status, meta, found, subs in landmine:
        spr = meta.get("source_page_ranges", "?")
        khp = meta.get("keyword_hit_pages", "?")
        psh = meta.get("parse_spec_hash", "?")
        print(f"  {code} {nm}: md={md_status} found={found} spr={spr} khp={khp} spec_hash={psh}")
    print()
    print(f"REAL GAP (master itself incomplete for 36-40): {len(real_gap)}")
    for code, nm, md_status, master_status, meta, found, subs in real_gap:
        spr = meta.get("source_page_ranges", "?") if meta else "NO_MD"
        print(f"  {code} {nm}: md={md_status} master={master_status} found={found} spr={spr}")

    out_path = REPO / "artifacts" / "kics_validation" / "market_window_census_20260901b.md"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [f"# 2026.2Q market-subrisk MD-reproducibility census ({len(codes)} companies)", ""]
    lines.append("## LANDMINE (master full, MD would not reproduce if re-parsed today)")
    for code, nm, md_status, master_status, meta, found, subs in landmine:
        lines.append(f"- {code} {nm}: md={md_status} found={found} spr={meta.get('source_page_ranges','?')} spec_hash={meta.get('parse_spec_hash','?')}")
    lines.append("")
    lines.append("## REAL GAP (master incomplete)")
    for code, nm, md_status, master_status, meta, found, subs in real_gap:
        lines.append(f"- {code} {nm}: md={md_status} master={master_status} found={found}")
    lines.append("")
    lines.append("## ALL (full detail)")
    for code, nm, md_status, master_status, meta, found, subs in results:
        lines.append(f"- {code} {nm}: md={md_status} master={master_status} found={found}")
    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nwrote {out_path}")


if __name__ == "__main__":
    main()
