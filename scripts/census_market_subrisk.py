# -*- coding: utf-8 -*-
"""Full census of 시장위험액 하위(36-40) coverage vs disclosure.

For every (company, quarter) that has item19(시장위험액) but NOT all of 36-40,
classify what the source MD discloses:
  ALL5_RECON   - extract_mkt_subs finds 5 and sqrt(V'MV) reconciles item19 <2%
                 (should already be stored; if not, extractor/fill gap)
  PARTIAL_FOUND- finds 2-4 sub-risk labels but doesn't reconcile (layout variant
                 or genuine partial — needs eyeball)
  G36_ONLY     - only 금리위험액 found (IRR table; 37-40 not in a breakdown table)
  NONE_FOUND   - no bare sub-risk labels in the MD at all (aggregate-only;
                 candidate for documented MARKET_BREAKDOWN_EXEMPT, evidence=MD)
  NO_MD        - md_inbox file missing for that period

Output: artifacts/kics_validation/market_subrisk_census_<stamp>.md (+ stdout).
"""
from __future__ import annotations
import glob
import json
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
sys.stdout.reconfigure(encoding="utf-8")
import fill_market_subitems_to_disclosure as F  # noqa: E402

JSON_PATH = REPO / "kics_disclosure.json"
MD_INBOX = REPO / "md_inbox"


def md_for(code, quarter):
    y, q = quarter.split(".")
    period = f"FY{y}_Q{q.rstrip('Q')}"
    g = glob.glob(str(MD_INBOX / period / f"{code}_*.md"))
    return Path(g[0]) if g else None


def main():
    rows = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    item19 = {}
    have = defaultdict(set)
    name = {}
    for r in rows:
        it = int(r["항목번호"])
        key = (r["원보험사코드"], r["공시분기"])
        name[r["원보험사코드"]] = r["원수사명"]
        if it == 19:
            v = F._parse_value(str(r["값"]))
            if v is not None:
                item19[key] = float(v)
        if 36 <= it <= 40 and F._parse_value(str(r["값"])) is not None:
            have[key].add(it)

    buckets = defaultdict(list)
    for key, v19 in sorted(item19.items()):
        if len(have[key]) >= 5 or v19 <= 0:
            continue
        code, quarter = key
        md = md_for(code, quarter)
        if md is None:
            buckets["NO_MD"].append((key, None))
            continue
        subs = F.extract_mkt_subs(md.read_text(encoding="utf-8"))
        found = sorted(subs)
        if found:
            v5 = [float(F._to_eok(subs.get(i, 0), "백만원")) for i in (36, 37, 38, 39, 40)]
            est = F.mkt_est(v5)
            rel = abs(est - v19) / v19 * 100 if v19 else 999
            if len(found) >= 4 and rel < 2:
                buckets["ALL5_RECON"].append((key, (found, round(rel, 1))))
            elif found == [36]:
                buckets["G36_ONLY"].append((key, None))
            else:
                buckets["PARTIAL_FOUND"].append((key, (found, round(rel, 1))))
        else:
            buckets["NONE_FOUND"].append((key, None))

    total = sum(len(v) for v in buckets.values())
    lines = [f"# 시장위험 하위(36-40) census — {total} (co,q) with item19 but <5 subs", ""]
    for b in ("ALL5_RECON", "PARTIAL_FOUND", "G36_ONLY", "NONE_FOUND", "NO_MD"):
        items = buckets.get(b, [])
        lines.append(f"## {b}: {len(items)}")
        for key, extra in items:
            tag = f"  ({extra})" if extra else ""
            lines.append(f"- {key[0]} {name.get(key[0],'?')} {key[1]}{tag}")
        lines.append("")
    out = REPO / "artifacts" / "kics_validation" / "market_subrisk_census.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines[:4]))
    for b in ("ALL5_RECON", "PARTIAL_FOUND", "G36_ONLY", "NONE_FOUND", "NO_MD"):
        print(f"  {b}: {len(buckets.get(b, []))}")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
