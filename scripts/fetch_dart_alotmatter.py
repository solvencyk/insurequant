# -*- coding: utf-8 -*-
"""DART alotMatter (배당에 관한 사항) raw collector — new recurring domain.

owner ticket `inbox/downloader/20260814T0746Z` (scope confirmed 20260814T1250Z addendum, C-1~C-4).
Full kics_disclosure universe x FY2023-FY2026 x all 4 reprt_codes. Raw JSON cached verbatim
(no aggregation here -- parser's job). Reuses resolve_corp from fetch_dart_fs.py (handles the
"OO생명보험"->"OO생명" alias quirk for 삼성생명/미래에셋생명) and OpenDARTClient._get directly
(client class itself is not modified, per ticket C-2).

Two-pass by design (ticket C-1 fallback plan): pass 1 = 11011(annual)+11012(half-year), the
scope owner explicitly prioritized ("반기별 배당 전부"); pass 2 = 11013(1Q)+11014(3Q), the
stretch scope ("작업량 manageable하면 분기별까지"). If pass 2 hits trouble, pass 1 already
landed -- partial completion over total failure.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(r"C:\Users\sangwook.cho\Desktop\insurequant")
sys.path.insert(0, str(REPO))
sys.stdout.reconfigure(encoding="utf-8")

from src.ifrs17.opendart_client import OpenDARTClient  # noqa: E402
from scripts.fetch_dart_fs import resolve_corp  # noqa: E402

CACHE = REPO / "data" / "dart" / "_alotmatter_cache"
YEARS = ["2023", "2024", "2025", "2026"]
REPRT_PASS1 = ["11011", "11012"]   # annual, half-year -- owner-confirmed core scope
REPRT_PASS2 = ["11013", "11014"]   # 1Q, 3Q -- stretch scope
CENSUS_OUT = REPO / "data" / "_derived" / "alotmatter_fetch_census.json"


def load_universe() -> list[tuple[str, str]]:
    data = json.loads((REPO / "kics_disclosure.json").read_text(encoding="utf-8"))
    seen: dict[str, str] = {}
    for row in data:
        kr, name = row.get("원보험사코드"), row.get("원수사명")
        if kr and name and kr not in seen:
            seen[kr] = name
    return sorted(seen.items())


def fetch_one(client: OpenDARTClient, corp_code: str, year: str, reprt: str, force: bool = False) -> dict:
    """Cached alotMatter fetch. Only status=000 (success) responses are persisted --
    a status:013 ("no data") is returned for this call but NOT written to disk, so
    it is re-checked live next time. Fixed 2026-08-20 (inbox/downloader/20260820T1600Z):
    same negative-cache trap as fetch_dart_fs.py (fixed there 2026-08-19) -- querying
    the morning of a filing deadline, before DART had indexed the batch, baked 013
    into the cache forever for 34/39 companies. `force=True` bypasses whatever is
    currently on disk (including a stale pre-fix 013 file) and re-fetches live."""
    f = CACHE / f"{corp_code}_{year}_{reprt}.json"
    if f.exists() and not force:
        return json.loads(f.read_text(encoding="utf-8"))
    r = client._get("/api/alotMatter.json", {
        "corp_code": corp_code, "bsns_year": year, "reprt_code": reprt,
    })
    data = r.json()
    if data.get("status") == "000":
        CACHE.mkdir(parents=True, exist_ok=True)
        f.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return data


def refresh_year_reprt(client: OpenDARTClient, year: str, reprt: str) -> list[dict]:
    """Force re-fetch (universe company x year x reprt), live, for every company in
    the kics_disclosure universe. Use after a same-day-as-deadline negative-cache
    incident (see fetch_one docstring) to unstick the affected slice.

    Fixed 2026-08-20 (inbox/downloader/20260820T1810Z): also patches CENSUS_OUT's
    cells for this (year, reprt) slice in-place, so the gate's expected-grid stays
    in sync with the cache. Only this slice's cells are touched -- other slices are
    left untouched, matching --refresh's scope principle."""
    universe = load_universe()
    results = []
    for kr, name in universe:
        cc = resolve_corp(name)
        if not cc:
            continue
        f = CACHE / f"{cc}_{year}_{reprt}.json"
        before = json.loads(f.read_text(encoding="utf-8")).get("status") if f.exists() else "missing"
        data = fetch_one(client, cc, year, reprt, force=True)
        after = data.get("status", "?")
        results.append({"kr": kr, "name": name, "corp_code": cc, "before": before, "after": after})

    if CENSUS_OUT.exists():
        census = json.loads(CENSUS_OUT.read_text(encoding="utf-8"))
        by_kr = {r["kr"]: r for r in results}
        status_counts: dict[str, int] = {}
        for cell in census.get("cells", []):
            if cell.get("year") == year and cell.get("reprt") == reprt and cell.get("kr") in by_kr:
                cell["status"] = by_kr[cell["kr"]]["after"]
        for cell in census.get("cells", []):
            status_counts[cell["status"]] = status_counts.get(cell["status"], 0) + 1
        census["status_counts"] = status_counts
        census["fetched_at"] = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        CENSUS_OUT.write_text(json.dumps(census, ensure_ascii=False, indent=2), encoding="utf-8")

    return results


def main() -> int:
    client = OpenDARTClient.from_settings()
    universe = load_universe()
    print(f"universe={len(universe)}")

    resolved: dict[str, str] = {}
    unresolved: list[tuple[str, str]] = []
    for kr, name in universe:
        cc = resolve_corp(name)
        if cc:
            resolved[kr] = cc
        else:
            unresolved.append((kr, name))
    print(f"resolved={len(resolved)} unresolved={len(unresolved)}")
    for kr, name in unresolved:
        print(f"  UNRESOLVED: {kr} {name}")

    status_counts: dict[str, int] = {}
    cells: list[dict] = []

    for pass_label, reprt_list in (("pass1_core", REPRT_PASS1), ("pass2_stretch", REPRT_PASS2)):
        print(f"\n=== {pass_label}: reprt={reprt_list} ===")
        for kr, cc in resolved.items():
            for year in YEARS:
                for reprt in reprt_list:
                    try:
                        data = fetch_one(client, cc, year, reprt)
                        status = data.get("status", "?")
                    except Exception as exc:  # noqa: BLE001 -- log and keep going
                        status = f"error:{type(exc).__name__}"
                    status_counts[status] = status_counts.get(status, 0) + 1
                    cells.append({"kr": kr, "corp_code": cc, "year": year, "reprt": reprt, "status": status})
        print(f"{pass_label} done. running status_counts={status_counts}")

    CENSUS_OUT.parent.mkdir(parents=True, exist_ok=True)
    CENSUS_OUT.write_text(json.dumps({
        "fetched_at": datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"),
        "universe_total": len(universe),
        "resolved": len(resolved),
        "unresolved": [{"kr": kr, "name": name} for kr, name in unresolved],
        "status_counts": status_counts,
        "cells": cells,
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    print("\n=== FINAL status_counts:", status_counts, "===")
    print(f"census written: {CENSUS_OUT}")
    return 0


if __name__ == "__main__":
    if "--refresh" in sys.argv:
        i = sys.argv.index("--refresh")
        try:
            year, reprt = sys.argv[i + 1], sys.argv[i + 2]
        except IndexError:
            print("usage: fetch_dart_alotmatter.py --refresh <year> <reprt>", file=sys.stderr)
            raise SystemExit(2)
        client = OpenDARTClient.from_settings()
        results = refresh_year_reprt(client, year, reprt)
        counts: dict[str, int] = {}
        for r in results:
            counts[r["after"]] = counts.get(r["after"], 0) + 1
        changed = [r for r in results if r["before"] != r["after"]]
        print(f"refreshed {len(results)} cells for year={year} reprt={reprt}")
        print(f"status_counts={counts}")
        print(f"changed={len(changed)}:")
        for r in changed:
            print(f"  {r['kr']} {r['name']}: {r['before']} -> {r['after']}")
        still_013 = [r for r in results if r["after"] == "013"]
        if still_013:
            print(f"still 013 (likely structural non-filers) = {len(still_013)}:")
            for r in still_013:
                print(f"  {r['kr']} {r['name']}")
        raise SystemExit(0)

    raise SystemExit(main())
