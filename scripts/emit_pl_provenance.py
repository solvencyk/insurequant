#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Re-issue PL_breakdown_provenance.json WITH a per-cell `source_file`
(inbox/parser/20260918T0700Z §E — 경영공시 PL 백필 병합 순서 ①).

The 2026-06-20 emission (scripts/emit_ifrs17_provenance.py) declared `source_file` as
"pending downloader" and shipped 638 cells with none, so the sidecar could not be used to
split the coverage grid by source.  This script fills it by BACK-TRACING each cell to the
file the builder actually read, and refuses to guess: a cell whose lineage cannot be
established keeps `source_file: null` plus an `unresolved_reason`.

Resolution follows the builder's own precedence, which is (last wins):
    scripts/build_pl_breakdown.py : assemble(t1, t2)  ->  _GOLD_CELL_OVERRIDE
    scripts/build_root_masters.py : build_pl()        ->  _apply_pl_overrides()
so a published value can only have come from one of four files:

  A  data/dart/_fs_api_cache/{corp}_{year}_{reprt}_{fs_div}.json
        Tier-1 포괄손익계산서 via the DART FS API (fetch_dart_fs.tier1_for).  We re-resolve
        the exact cache path offline (CORPCODE.xml + REPRT + fs_div order) and CONFIRM it by
        re-parsing the cached JSON with the production _parse() and matching values against
        the master.  No value agreement -> not claimed.
  B  data/dart/FY<Y>_Q<n>/raw/KR####_<name>[_<rcept>]/
        the raw filing.  Tier-2 (계약유형별/재보험 notes -> items 4,5,6,9,10,11,13,14) can
        ONLY come from here, and Tier-1 falls back to the HTML extractor here whenever the
        FS-API has no data (FY2023 1Q/2Q void + the non-listed insurers with no XBRL).  The
        Tier-1 fallback is likewise confirmed by re-running extract_tier1() over the dir.
  C  data/_gold/user_pl_cells.json          owner gold overlay (UPSERT, wins over everything)
  D  scripts/build_pl_breakdown.py          _GOLD_CELL_OVERRIDE literals

The sidecar key is (company_code, quarter, item_block), so a block can mix sources.  Every
contributing file is listed in `source_files` with the items it explains; `source_file` is
the one explaining the most published items (ties -> the DART path).

Usage:
    python scripts/emit_pl_provenance.py --dry-run     # report only, writes nothing
    python scripts/emit_pl_provenance.py               # re-issue the sidecar
"""
import argparse
import glob
import io
import json
import os
import re
import sys
from collections import Counter, OrderedDict, defaultdict
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

from src.ifrs17.csm_extractor import _iter_tables_with_context  # noqa: E402
from scripts.fetch_dart_fs import ALIAS, BASIS_CFS, REPRT, _parse  # noqa: E402
from scripts.pl_breakdown.common import _iter_tables_by_basis, _tag_basis  # noqa: E402
from scripts.pl_breakdown.tier1 import extract_tier1  # noqa: E402
from scripts.build_pl_breakdown import _GOLD_CELL_OVERRIDE  # noqa: E402

PL_SRC = ROOT / "PL_breakdown.json"
PL_OVR = ROOT / "data" / "_gold" / "user_pl_cells.json"
PL_OUT = ROOT / "PL_breakdown_provenance.json"
BUILDER = "scripts/build_pl_breakdown.py"
GOLD_FILE = "data/_gold/user_pl_cells.json"
CACHE = "data/dart/_fs_api_cache"
CORPCODE = ROOT / "data" / "dart" / "raw" / "CORPCODE.xml"

# Same split the 2026-06-20 emitter used — do not change without re-agreeing the contract.
PL_CONTRACT_NOTES = {4, 5, 6, 9, 10, 11, 13, 14}
# Items the FS-API Tier-1 dict carries verbatim (assemble() does not derive them).
T1_DIRECT = (1, 15, 16, 17, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32)


def _block(it):
    return "contract_notes" if it in PL_CONTRACT_NOTES else "income_statement"


def _eq(a, b):
    if a is None or b is None:
        return False
    try:
        return abs(a - b) <= max(1.0, abs(a) * 1e-4)
    except TypeError:
        return False


def _rel(p):
    return os.path.relpath(p, ROOT).replace("\\", "/")


# --------------------------------------------------------------------------- #
# offline clone of fetch_dart_fs.resolve_corp (CORPCODE.xml is committed)
# --------------------------------------------------------------------------- #
def _make_resolver():
    from lxml import etree
    tree = etree.parse(str(CORPCODE))
    recs = [{"corp_code": (el.findtext("corp_code") or "").strip(),
             "corp_name": (el.findtext("corp_name") or "").strip(),
             "stock_code": (el.findtext("stock_code") or "").strip()}
            for el in tree.iter("list")]
    memo = {}

    def resolve(name):
        if name in memo:
            return memo[name]
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
        memo[name] = cc
        return cc
    return resolve


def _xmls_in(d):
    xs = glob.glob(d + "/*.xml") + glob.glob(d + "/xml/*.xml") + glob.glob(d + "/extracted*/*.xml")
    return sorted(set(xs), key=os.path.getsize, reverse=True)


def _raw_index():
    raw = defaultdict(list)
    for base in sorted(glob.glob("data/dart/FY*/raw")):
        m = re.search(r"FY(\d{4})_Q(\d)", base.replace("\\", "/"))
        if not m:
            continue
        q = f"{m.group(1)}.{m.group(2)}Q"
        for d in sorted(glob.glob(base + "/KR*")):
            mm = re.match(r"(KR\d+)_", os.path.basename(d))
            if mm:
                xs = _xmls_in(d)
                if xs:
                    raw[(mm.group(1), q)].append(
                        (d.replace("\\", "/"), sum(os.path.getsize(x) for x in xs)))
    return raw


def _raw_tier1(d, code):
    tables = []
    for x in _xmls_in(d):
        try:
            tables.extend(_tag_basis(
                list(_iter_tables_by_basis(Path(x), _iter_tables_with_context)), x))
        except Exception:
            pass
    if not tables:
        return None
    try:
        return extract_tier1(tables, code=code)
    except Exception:
        return None


# --------------------------------------------------------------------------- #
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    rows = json.loads(PL_SRC.read_text(encoding="utf-8"))
    names, is_life, vals, order = {}, {}, defaultdict(dict), []
    skipped = 0
    for r in rows:
        code, q = r.get("원보험사코드"), r.get("공시분기")
        try:
            it = int(r.get("항목번호"))
        except (TypeError, ValueError):
            skipped += 1          # 코리안리 2-1…12-1 sub-items: outside the integer schema
            continue
        if not (code and q):
            skipped += 1
            continue
        names[code] = r.get("원수사명")
        is_life[code] = r.get("생손보여부") == "생명보험"
        vals[(code, q)][it] = r.get("값")
        key = (code, q, _block(it))
        if key not in order:
            order.append(key)

    # owner gold overlay (UPSERT, applied last by build_root_masters.build_pl)
    gold = json.loads(PL_OVR.read_text(encoding="utf-8")) if PL_OVR.exists() else {}
    goldset, gold_est = {}, set()
    for s in gold.get("set", []):
        try:
            it = int(s["항목번호"])
        except (TypeError, ValueError, KeyError):
            continue
        k = (s.get("원보험사코드"), s.get("공시분기"), it)
        goldset[k] = s.get("값")
        if s.get("estimate"):
            gold_est.add(k)

    raw = _raw_index()
    resolve = _make_resolver()

    cells, stat, unres_reason, stat_items = [], Counter(), Counter(), Counter()
    fs_memo, rawt1_memo = {}, {}

    for (code, q, blk) in order:
        v = vals[(code, q)]
        items = sorted(i for i in v if _block(i) == blk)
        pub = [i for i in items if v[i] is not None]
        cell = OrderedDict([("company_code", code), ("quarter", q),
                            ("item_block", blk), ("source_id", "DART")])
        ovr_items = [i for i in pub if (code, q, i) in goldset and _eq(v[i], goldset[(code, q, i)])]
        cov = _GOLD_CELL_OVERRIDE.get((code, q), {})
        bld_items = [i for i in pub if i not in ovr_items and i in cov and _eq(v[i], cov[i])]
        # assemble(): `if is_life: v[13] = 0.0; v[14] = 0.0`.  Unconditional — a 생보 자동차/
        # 일반 LOB zero has NO data path from any filing, so it must not be attributed to one.
        # (item6/item11 zeros are NOT included here: the 2026-08-30 two-pass zero_fill_ok rule
        # means some of those are genuinely extracted, and telling them apart needs Tier-2 —
        # they stay attributed to the filing and the residual ambiguity is reported, not hidden.)
        conv_items = ([i for i in pub if i in (13, 14) and v[i] == 0.0
                       and i not in ovr_items and i not in bld_items]
                      if is_life.get(code) else [])
        rest = [i for i in pub
                if i not in ovr_items and i not in bld_items and i not in conv_items]

        rawdirs = raw.get((code, q), [])
        api_file, api_items, raw_pick, raw_items = None, [], None, []

        if blk == "income_statement":
            if (code, q) not in fs_memo:
                cc, reprt, year = resolve(names[code]), REPRT.get(q[5:]), q[:4]
                annual, got = q[5:] == "4Q", None
                if cc and reprt:
                    primary = "CFS" if code in BASIS_CFS else "OFS"
                    for fs_div in (primary, "CFS" if primary == "OFS" else "OFS"):
                        p = f"{CACHE}/{cc}_{year}_{reprt}_{fs_div}.json"
                        if not os.path.exists(p):
                            continue
                        try:
                            t1 = _parse(json.loads(Path(p).read_text(encoding="utf-8")), annual)
                        except Exception:
                            t1 = None
                        if t1:
                            got = (p, t1)
                            break
                fs_memo[(code, q)] = got
            got = fs_memo[(code, q)]
            if got:
                api_file, t1 = got
                api_items = [i for i in rest if i in T1_DIRECT and _eq(v[i], t1.get(i))]
            if len(api_items) < len([i for i in rest if i in T1_DIRECT]):
                best = None
                for d, size in rawdirs:
                    if (d, code) not in rawt1_memo:
                        rawt1_memo[(d, code)] = _raw_tier1(d, code)
                    t1r = rawt1_memo[(d, code)] or {}
                    hits = [i for i in rest
                            if i in T1_DIRECT and i not in api_items and _eq(v[i], t1r.get(i))]
                    if best is None or len(hits) > len(best[1]):
                        best = (d, hits, size)
                if best and best[1]:
                    raw_pick, raw_items = best[0], best[1]
        else:
            # Tier-2 note items have exactly one code path: the raw filing XML.
            if rawdirs and rest:
                raw_pick = max(rawdirs, key=lambda t: t[1])[0]
                raw_items = list(rest)

        # items still unexplained: assemble() derivations (2,3,7,8,12 and 18/20/22/24 when the
        # statement omits them).  Their inputs are Tier-2 notes / Tier-1 hidden keys, i.e. the
        # same filing — attribute them to it, but only when that filing is on disk.
        derived = [i for i in rest if i not in api_items and i not in raw_items]
        if derived and raw_pick is None and rawdirs:
            raw_pick = max(rawdirs, key=lambda t: t[1])[0]
        derived_here = derived if (derived and raw_pick) else []

        buckets = []
        if api_items:
            buckets.append((api_file, api_items, "fs_api_tier1"))
        if raw_items or derived_here:
            buckets.append((raw_pick, sorted(raw_items + derived_here),
                            "raw_filing" if raw_items else "raw_filing_derived"))
        if ovr_items:
            buckets.append((GOLD_FILE, ovr_items, "owner_gold_overlay"))
        if bld_items:
            buckets.append((BUILDER, bld_items, "gold_cell_override"))
        buckets.sort(key=lambda b: (-len(b[1]), 0 if str(b[0]).startswith("data/dart/") else 1,
                                    str(b[0])))
        # Builder-fabricated values never carry a filing path — listed with file: null so the
        # item lists above stay truthful about what the filing actually contains.
        if conv_items:
            buckets.append((None, conv_items, "life_lob_zero_builder_rule"))

        if not buckets:
            cell["source_file"] = None
            reason = ("NO_PUBLISHED_VALUE_IN_BLOCK" if not pub
                      else "NO_SOURCE_FILE_ON_DISK_FOR_PUBLISHED_VALUES")
            cell["unresolved_reason"] = reason
            unres_reason[reason] += 1
            stat["UNRESOLVED"] += 1
        elif buckets[0][0] is None:
            # every published value in this block is builder-fabricated
            cell["source_id"] = "DERIVED"
            cell["source_file"] = None
            cell["unresolved_reason"] = "LIFE_LOB_ZERO_BUILDER_RULE_NOT_FROM_A_FILING"
            cell["source_files"] = [{"file": f, "how": how, "items": its}
                                    for f, its, how in buckets]
            unres_reason["LIFE_LOB_ZERO_BUILDER_RULE_NOT_FROM_A_FILING"] += 1
            stat["DERIVED_ONLY"] += 1
        else:
            cell["source_file"] = buckets[0][0]
            cell["source_files"] = [
                {"file": f, "how": how, "items": its} for f, its, how in buckets]
            cell["resolution"] = buckets[0][2]
            if not buckets[0][0].startswith("data/dart/"):
                cell["source_id"] = "OWNER_GOLD"
            stat[buckets[0][2]] += 1
        cell["published_items"] = len(pub)
        cell["schema_items"] = len(items)
        if conv_items:
            cell["builder_derived_items"] = conv_items
        if ovr_items:
            cell["owner_override"] = True
            if any((code, q, i) in gold_est for i in ovr_items):
                cell["estimate"] = True
        cells.append(cell)
        stat_items["builder_derived"] += len(conv_items)

    filled = sum(1 for c in cells if c["source_file"])
    n_conv_cells = sum(1 for c in cells if c.get("builder_derived_items"))
    print(f"master rows={len(rows)} skipped={skipped} cells={len(cells)}")
    print(f"source_file filled = {filled}/{len(cells)}   null = {len(cells)-filled}")
    print("by resolution:", dict(stat.most_common()))
    print("unresolved reasons:", dict(unres_reason))
    print("source_id:", dict(Counter(c["source_id"] for c in cells)))
    print("blocks:", dict(Counter(c["item_block"] for c in cells)))
    print(f"builder-fabricated (생보 13/14=0.0) values = {stat_items['builder_derived']} "
          f"in {n_conv_cells} cells; cells made source_id=DERIVED by them = "
          f"{stat['DERIVED_ONLY']}")
    missing_disk = [c for c in cells if c["source_file"] and not (ROOT / c["source_file"]).exists()]
    print(f"source_file not found on disk = {len(missing_disk)}")
    for c in cells:
        if not c["source_file"]:
            print(f"  NULL  {c['company_code']} {c['quarter']} {c['item_block']} "
                  f"published={c['published_items']} {c['unresolved_reason']}")

    doc = OrderedDict([
        ("master", "PL_breakdown"),
        ("generated_at", "20260920T0000Z"),
        ("emitter", "parser"),
        ("emitted_by", "scripts/emit_pl_provenance.py"),
        ("fields_owned", ["source_id", "item_block", "source_file"]),
        ("fields_pending_downloader", ["as_of_date", "effective_filtered"]),
        ("key", ["company_code", "quarter", "item_block"]),
        ("source_id_values", {
            "DART": "source_file under data/dart/ — DART filing XML or the DART FS-API cache",
            "OWNER_GOLD": ("owner-verified cell literal; source_file is where the literal "
                           "lives (data/_gold/user_pl_cells.json or "
                           "scripts/build_pl_breakdown.py::_GOLD_CELL_OVERRIDE). NOT registered "
                           "in validate_data_contract._SOURCE_LINEAGE — register before wiring "
                           "source_id_for_lineage() for this master."),
            "DERIVED": ("every published value in the block is fabricated by the builder with "
                        "no data path from any filing (assemble()'s unconditional 생보 "
                        "자동차/일반 LOB zero). source_file stays null — pointing at the filing "
                        "would be a false lineage. New label, introduced 2026-09-20; also NOT "
                        "in _SOURCE_LINEAGE."),
        }),
        ("builder_derived_items", ("per-cell list of item numbers whose value the builder "
                                   "fabricated (생보 item13/14 = 0.0). They are excluded from "
                                   "every filing bucket in source_files.")),
        ("note", "source_file = the file explaining the most published items of the block; "
                 "source_files lists every contributing file with the items it explains "
                 "(the (company,quarter,item_block) key can mix Tier-1 and Tier-2 sources). "
                 "FS-API and raw-HTML Tier-1 attributions are value-confirmed against the "
                 "master; Tier-2 note items are attributed structurally (the raw filing XML "
                 "is their only code path in build_pl_breakdown). Unresolved cells keep "
                 "source_file: null + unresolved_reason — never a guessed path."),
        ("cells", cells),
    ])
    if args.dry_run:
        print("\n--dry-run: nothing written")
        return
    # newline="\n": the committed sidecars are LF; Path.write_text would emit CRLF on Windows.
    with open(PL_OUT, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(doc, ensure_ascii=False, indent=2))
    print(f"\nwrote {PL_OUT.name}")


main()
