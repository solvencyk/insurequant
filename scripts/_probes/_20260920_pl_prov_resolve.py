#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Back-trace every PL_breakdown master cell to the file it actually came from.

Fully offline.  Replicates the builder's own source precedence:

  income_statement (items not in {4,5,6,9,10,11,13,14})
      Tier-1 = DART FS-API, cached at data/dart/_fs_api_cache/{cc}_{year}_{reprt}_{fs_div}.json
      (scripts/fetch_dart_fs.py::tier1_for -> _fetch_raw).  fs_div order = OFS then CFS
      (BASIS_CFS is empty).  We PARSE the cached JSON with the production _parse() and
      CONFIRM the lineage by matching values against the master; we never label by guess.
      No cache hit / no value agreement -> HTML fallback = the raw rcept dir.

  contract_notes (items 4,5,6,9,10,11,13,14)
      Tier-2 only ever reads the raw filing XML under data/dart/FY*/raw/KR*_*/.

Writes data/_derived/_probe_20260920_pl_prov_resolve.json.  Touches no master, no sidecar.
"""
import glob
import io
import json
import os
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

from scripts.fetch_dart_fs import ALIAS, BASIS_CFS, REPRT, _parse  # noqa: E402

PL_CONTRACT_NOTES = {4, 5, 6, 9, 10, 11, 13, 14}
# Items that arrive verbatim from the FS-API Tier-1 dict (no derivation in assemble()).
T1_DIRECT = (1, 16, 17, 20, 22, 23, 24)
CACHE = "data/dart/_fs_api_cache"


def _block(it):
    return "contract_notes" if it in PL_CONTRACT_NOTES else "income_statement"


# --------------------------------------------------------------------------- #
# corp_code resolution, offline clone of fetch_dart_fs.resolve_corp
# --------------------------------------------------------------------------- #
def _load_corpcode():
    from lxml import etree
    tree = etree.parse(str(ROOT / "data/dart/raw/CORPCODE.xml"))
    recs = []
    for el in tree.iter("list"):
        recs.append({
            "corp_code": (el.findtext("corp_code") or "").strip(),
            "corp_name": (el.findtext("corp_name") or "").strip(),
            "stock_code": (el.findtext("stock_code") or "").strip(),
        })
    return recs


def _make_resolver(recs):
    cache = {}

    def resolve(name):
        if name in cache:
            return cache[name]
        queries = [ALIAS.get(name, name), name]
        if name.endswith("생명보험"):
            queries.append(name[:-2])
        if name.endswith("재보험"):
            queries.append(name[:-3])
        cc = None
        for q in queries:
            hits = [h for h in recs if q in h["corp_name"]]
            if not hits:
                continue
            exact = [h for h in hits if h["corp_name"] in (q, name)]
            listed = [h for h in hits if h["stock_code"]]
            cc = (exact or listed or hits)[0]["corp_code"]
            break
        cache[name] = cc
        return cc
    return resolve


def main():
    rows = json.loads((ROOT / "PL_breakdown.json").read_text(encoding="utf-8"))
    names, vals = {}, defaultdict(dict)
    for r in rows:
        code, q = r.get("원보험사코드"), r.get("공시분기")
        try:
            it = int(r.get("항목번호"))
        except (TypeError, ValueError):
            continue
        if not (code and q):
            continue
        names[code] = r.get("원수사명")
        vals[(code, q)][it] = r.get("값")

    # ---- raw filing index -------------------------------------------------- #
    raw = defaultdict(list)
    for base in sorted(glob.glob("data/dart/FY*/raw")):
        m = re.search(r"FY(\d{4})_Q(\d)", base.replace("\\", "/"))
        if not m:
            continue
        q = f"{m.group(1)}.{m.group(2)}Q"
        for d in sorted(glob.glob(base + "/KR*")):
            b = os.path.basename(d)
            mm = re.match(r"(KR\d+)_", b)
            if not mm:
                continue
            xmls = sorted(set(glob.glob(d + "/*.xml") + glob.glob(d + "/xml/*.xml")
                              + glob.glob(d + "/extracted*/*.xml")))
            raw[(mm.group(1), q)].append((d.replace("\\", "/"),
                                          [x.replace("\\", "/") for x in xmls]))

    resolve = _make_resolver(_load_corpcode())

    # ---- per (code, quarter): resolve the Tier-1 FS-API cache file ---------- #
    t1_cache = {}
    for (code, q) in sorted(vals):
        cc = resolve(names[code])
        reprt = REPRT.get(q[5:])
        year = q[:4]
        annual = q[5:] == "4Q"
        picked, tried = None, []
        if cc and reprt:
            primary = "CFS" if code in BASIS_CFS else "OFS"
            for fs_div in (primary, "CFS" if primary == "OFS" else "OFS"):
                p = f"{CACHE}/{cc}_{year}_{reprt}_{fs_div}.json"
                tried.append(p)
                if not os.path.exists(p):
                    continue
                try:
                    t1 = _parse(json.loads(Path(p).read_text(encoding="utf-8")), annual)
                except Exception:
                    t1 = None
                if t1:
                    picked = (p, t1)
                    break
        t1_cache[(code, q)] = {"corp_code": cc, "tried": tried, "picked": picked}

    # ---- resolve each master cell ----------------------------------------- #
    out, stat = [], Counter()
    for (code, q) in sorted(vals):
        v = vals[(code, q)]
        for blk in ("income_statement", "contract_notes"):
            items = sorted(i for i in v if _block(i) == blk)
            if not items:
                continue
            nonnull = [i for i in items if v[i] is not None]
            entry = {"company_code": code, "quarter": q, "item_block": blk,
                     "n_items": len(items), "n_nonnull": len(nonnull)}
            rawdirs = raw.get((code, q), [])
            rawdirs_xml = [(d, xs) for d, xs in rawdirs if xs]

            if blk == "income_statement":
                info = t1_cache[(code, q)]
                pick = info["picked"]
                if pick:
                    path, t1 = pick
                    hit = miss = 0
                    for i in T1_DIRECT:
                        mv, av = v.get(i), t1.get(i)
                        if mv is None or av is None:
                            continue
                        if abs(mv - av) <= max(1.0, abs(mv) * 1e-4):
                            hit += 1
                        else:
                            miss += 1
                    entry.update(fs_api_file=path, fs_hit=hit, fs_miss=miss)
                    if hit:
                        entry.update(source_file=path, resolution="FS_API_CONFIRMED")
                    elif rawdirs_xml:
                        entry.update(source_file=rawdirs_xml[0][0],
                                     resolution="RAW_HTML_FS_API_NO_VALUE_MATCH")
                    else:
                        entry.update(source_file=None,
                                     unresolved_reason="FS_API_CACHE_PARSES_BUT_NO_VALUE_MATCH_AND_NO_RAW_XML")
                elif rawdirs_xml:
                    entry.update(source_file=rawdirs_xml[0][0], resolution="RAW_HTML_NO_FS_CACHE",
                                 fs_api_tried=info["tried"])
                else:
                    entry.update(source_file=None, fs_api_tried=info["tried"],
                                 unresolved_reason="NO_FS_API_CACHE_AND_NO_RAW_XML")
            else:
                if rawdirs_xml:
                    entry.update(source_file=rawdirs_xml[0][0], resolution="RAW_XML")
                else:
                    entry.update(source_file=None,
                                 unresolved_reason="NO_RAW_XML_IN_FILING_DIR")
            entry["raw_dirs"] = [d for d, _ in rawdirs]
            entry["raw_dirs_with_xml"] = [d for d, _ in rawdirs_xml]
            stat[entry.get("resolution") or ("UNRESOLVED:" + entry["unresolved_reason"])] += 1
            out.append(entry)

    print(f"cells = {len(out)}")
    for k, n in stat.most_common():
        print(f"  {k}: {n}")

    unres = [e for e in out if e["source_file"] is None]
    print(f"\nunresolved = {len(unres)}")
    print(f"  with non-null 값 = {sum(1 for e in unres if e['n_nonnull'])}")
    for e in unres:
        print(f"   {e['company_code']} {e['quarter']} {e['item_block']} "
              f"nonnull={e['n_nonnull']} {e['unresolved_reason']}")

    nomatch = [e for e in out if e.get("resolution") == "RAW_HTML_FS_API_NO_VALUE_MATCH"]
    print(f"\nFS-API cache parsed but no value agreement = {len(nomatch)}")
    for e in nomatch[:40]:
        print(f"   {e['company_code']} {e['quarter']} hit={e['fs_hit']} miss={e['fs_miss']} "
              f"nonnull={e['n_nonnull']}")

    nofs = [e for e in out if e.get("resolution") == "RAW_HTML_NO_FS_CACHE"]
    print(f"\nno FS-API cache at all (income_statement) = {len(nofs)}")
    print("  by company:", dict(Counter(e["company_code"] for e in nofs)))

    dst = ROOT / "data/_derived/_probe_20260920_pl_prov_resolve.json"
    dst.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nwrote {dst.relative_to(ROOT)}")


main()
