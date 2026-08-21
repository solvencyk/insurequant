# -*- coding: utf-8 -*-
"""One-off: scout all 39 insurers for a 2026.06 half-year (반기보고서, A003) DART filing.

owner ticket inbox/downloader/20260814T0149Z D-1/D-2 (2026-08-14, legal deadline day).
Reuses resolve_corp + process_one_period from the proven historical-batch pipeline;
constructs the FY2026.2Q PeriodTarget locally (not added to ifrs17_batch_historical.py's
global registry, per ticket "don't touch script structure this time — just collect").
Also refreshes the FS-API cache (owner directive: FS cache ownership = downloader) for
every company confirmed filed.
"""
from __future__ import annotations

import json
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(r"C:\Users\sangwook.cho\Desktop\insurequant")
sys.path.insert(0, str(REPO))
sys.stdout.reconfigure(encoding="utf-8")

from src.ifrs17.config import settings  # noqa: E402
from src.ifrs17.opendart_client import OpenDARTClient, OpenDARTError  # noqa: E402
from scripts.ifrs17_batch_all import resolve_corp  # noqa: E402
from scripts.ifrs17_batch_historical import PeriodTarget, process_one_period  # noqa: E402
from scripts._dart_path_helpers import quarterly_raw_dir  # noqa: E402
from scripts.fetch_dart_fs import _refresh_cache  # noqa: E402

TARGET = PeriodTarget(
    label="2026.2Q", bgn_de="20260701", end_de="20260930",
    pblntf_detail_ty="A003", report_keyword="반기보고서",
)

KEYWORDS = ("보험계약마진", "보험료배분접근법", "신계약")

OUT = REPO / "data" / "_derived" / "scout_2026q2_halfyear.json"


def load_universe() -> list[tuple[str, str]]:
    data = json.loads((REPO / "kics_disclosure.json").read_text(encoding="utf-8"))
    seen: dict[str, str] = {}
    for row in data:
        kr, name = row.get("원보험사코드"), row.get("원수사명")
        if kr and name and kr not in seen:
            seen[kr] = name
    return sorted(seen.items())


def _check_keywords(zip_path: Path) -> list[str]:
    found = set()
    try:
        with zipfile.ZipFile(zip_path) as zf:
            for name in zf.namelist():
                if not name.lower().endswith(".xml"):
                    continue
                text = zf.read(name).decode("utf-8", errors="ignore")
                for kw in KEYWORDS:
                    if kw in text:
                        found.add(kw)
    except zipfile.BadZipFile:
        return ["BAD_ZIP"]
    return sorted(found)


def main() -> int:
    settings.ensure_dirs()
    client = OpenDARTClient.from_settings()
    universe = load_universe()
    print(f"universe={len(universe)}")

    results = []
    newly_confirmed = []
    for kr, name in universe:
        try:
            chosen = resolve_corp(client, name)
        except OpenDARTError as exc:
            results.append({"kr": kr, "name": name, "status": f"resolve_error:{exc}"})
            print(f"{kr} {name}: resolve_error {exc}")
            continue
        if not chosen:
            results.append({"kr": kr, "name": name, "status": "no_corp_match"})
            print(f"{kr} {name}: NO_CORP_MATCH")
            continue
        canonical, corp_code = chosen["corp_name"], chosen["corp_code"]

        pre_dir = quarterly_raw_dir(canonical_name=canonical, period_label=TARGET.label,
                                     kr_code=kr, corp_code=corp_code)
        pre_existing = (pre_dir / "document.zip").is_file()

        r = process_one_period(client, kr, canonical, corp_code, TARGET, skip_extract=True)
        status = r.get("status")
        row = {"kr": kr, "name": canonical, "corp_code": corp_code, "pre_existing": pre_existing, **r}

        if status == "fetched" and not pre_existing:
            zip_path = pre_dir / "document.zip"
            kws = _check_keywords(zip_path)
            row["keywords_found"] = kws
            row["size"] = zip_path.stat().st_size if zip_path.is_file() else 0
            fs_note = "skipped"
            try:
                _refresh_cache(corp_code, "2026")
                fs_note = "refreshed"
            except Exception as exc:  # noqa: BLE001
                fs_note = f"error:{exc}"
            row["fs_cache"] = fs_note
            newly_confirmed.append((kr, canonical, corp_code, kws, fs_note))
            print(f"{kr} {canonical} ({corp_code}): *** NEW *** rcept={r.get('rcept_no')} "
                  f"size={row['size']}B kw={kws} fs_cache={fs_note}")
        else:
            print(f"{kr} {canonical} ({corp_code}): {status} "
                  f"({'already had' if pre_existing else 'not filed'})  rcept={r.get('rcept_no')}")

        results.append(row)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({
        "scouted_at": datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"),
        "target": TARGET.label,
        "results": results,
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    total_filed = len([r for r in results if r.get("status") == "fetched"])
    print(f"\n=== total_filed={total_filed} "
          f"newly_confirmed_this_run={len(newly_confirmed)} "
          f"no_filing={len([r for r in results if r.get('status') == 'no_filing'])} "
          f"no_match={len([r for r in results if r.get('status') == 'no_corp_match'])} "
          f"other={len([r for r in results if r.get('status') not in ('fetched', 'no_filing', 'no_corp_match')])} ===")
    print("newly_confirmed_this_run:", newly_confirmed)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
