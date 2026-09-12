# -*- coding: utf-8 -*-
"""Build the /jp/ J-ESR page data JSON from the FY2025 census + 2026Q1 sources CSVs.

Owner ticket: inbox/publishing/20260912T0446Z__owner__JP_MULTI__jesr_page_json.md

Reads
-----
J-ESR/fy2025_esr_census_20260912.csv (utf-8-sig, 79 rows) -- primary source.
    Only rows with fy2025_esr_status == "posted" are used (15 as of 2026-09-12).
J-ESR/jesr_sources_2026Q1.csv (utf-8-sig, 11 rows) -- auxiliary columns
    (ticker / total assets / target ratio / esr basis), joined onto the census
    rows by company_jp. `ticker` is joined regardless of period (a listing
    symbol does not change quarter to quarter). `total_assets_bn_jpy`,
    `target_pct` and `basis` are joined ONLY when the sources row's `as_of`
    matches the census row's `as_of` -- the sources csv still carries stale
    H1/FY2024 figures for 4 mutual companies, and attaching a stale
    balance-sheet snapshot or methodology label to a newer posted record
    would be a silent wrong-source bug, not a join. Unmatched -> null.

Writes (byte-identical)
------------------------
J-ESR/jesr_master.json  -- replaces the 2026-06 schema. This script is the
    sole producer of this path (full-replace is intentional, not a
    read-modify-write of a shared root master).
jp/jesr_esr.json        -- deploy copy for the /jp/ page fetch. `jp/` is
    created if it does not exist yet.

Schema is a fixed contract agreed with designer (see the ticket) -- key
names must not change; do not add or rename fields here without re-checking
with that ticket.
"""
from __future__ import annotations

import csv
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
CENSUS_CSV = HERE / "fy2025_esr_census_20260912.csv"
SOURCES_CSV = HERE / "jesr_sources_2026Q1.csv"
MASTER_OUT = HERE / "jesr_master.json"
DEPLOY_OUT = HERE.parent / "jp" / "jesr_esr.json"

AS_OF_TARGET = "2026-03-31"
AS_OF_LABEL_JA = "2026年3月31日"
NEXT_UPDATE = "2026-10-31"
BASIS_DEFAULT = "J-ICS"

SECTOR_MAP = {"損保": "nonlife", "生保": "life", "再保険": "reinsurance"}
PRELIM_KEYWORDS = ["속보", "잠정", "速報"]  # ticket 규칙: 속보/잠정/速報 류 표현


def _read_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def _num(s) -> float | None:
    if s is None:
        return None
    s = str(s).strip()
    if s == "":
        return None
    try:
        return float(s)
    except ValueError:
        return None


def _canon(n: float | None):
    """Whole floats -> int (so 319600.00000003 renders as 319600, not a float)."""
    if n is None:
        return None
    return int(round(n)) if abs(n - round(n)) < 1e-9 else round(n, 4)


def _extract_doc_date(doc_type: str | None) -> str | None:
    """Pull a date out of the census doc_type string, e.g.
    '決算短信/決算説明資料(2026-05-20)' -> '2026-05-20',
    '決算概要(2026年5月)' -> '2026-05'.
    Tries full ISO date, then Japanese Y/M/D, then Japanese Y/M."""
    if not doc_type:
        return None
    m = re.search(r"(\d{4})-(\d{2})-(\d{2})", doc_type)
    if m:
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    m = re.search(r"(\d{4})年(\d{1,2})月(\d{1,2})日", doc_type)
    if m:
        return f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
    m = re.search(r"(\d{4})年(\d{1,2})月", doc_type)
    if m:
        return f"{m.group(1)}-{int(m.group(2)):02d}"
    return None


def _detect_preliminary(notes: str | None, doc_type: str | None) -> tuple[bool, str | None]:
    haystack = f"{notes or ''} {doc_type or ''}"
    for kw in PRELIM_KEYWORDS:
        if kw in haystack:
            return True, kw
    return False, None


def build() -> dict:
    census_rows = _read_csv(CENSUS_CSV)
    source_rows = _read_csv(SOURCES_CSV)
    sources_by_name = {
        r["company_jp"].strip(): r for r in source_rows if (r.get("company_jp") or "").strip()
    }

    def status(r):
        return (r.get("fy2025_esr_status") or "").strip()

    total = len(census_rows)
    posted_rows = [r for r in census_rows if status(r) == "posted"]
    not_yet = sum(1 for r in census_rows if status(r) == "not_yet")
    not_found = sum(1 for r in census_rows if status(r) == "not_found")

    records = []
    for r in posted_rows:
        company_jp = (r.get("company_jp") or "").strip()
        sector_raw = (r.get("sector") or "").strip()
        as_of = (r.get("as_of") or "").strip() or None
        doc_type = (r.get("doc_type") or "").strip() or None
        notes = (r.get("notes") or "").strip() or None

        src = sources_by_name.get(company_jp)
        src_as_of_matches = bool(src) and (src.get("as_of") or "").strip() == as_of

        ticker = None
        if src:
            ticker = (src.get("ticker") or "").strip() or None

        total_assets_bn_jpy = None
        target_pct = None
        basis = BASIS_DEFAULT
        if src and src_as_of_matches:
            tn = _num(src.get("総資産_tn_jpy"))
            if tn is not None:
                total_assets_bn_jpy = _canon(tn * 1e4)  # 兆円 -> 億円 (x1e4)
            target_pct = (src.get("target_pct") or "").strip() or None
            basis = (src.get("esr_basis") or "").strip() or BASIS_DEFAULT

        preliminary, kw = _detect_preliminary(notes, doc_type)
        if preliminary:
            tag = f"(preliminary 판정: notes 내 '{kw}' 검출)"
            notes = f"{notes} {tag}" if notes else tag

        records.append({
            "company_jp": company_jp,
            "company_en": (r.get("company_en") or "").strip(),
            "ticker": ticker,
            "sector": SECTOR_MAP.get(sector_raw),
            "category": (r.get("category") or "").strip() or None,
            "scope": (r.get("esr_scope") or "").strip() or None,
            "esr_pct": _num(r.get("esr_pct")),
            "basis": basis,
            "as_of": as_of,
            "preliminary": preliminary,
            "total_assets_bn_jpy": total_assets_bn_jpy,
            "target_pct": target_pct,
            "doc_type": doc_type,
            "doc_date": _extract_doc_date(doc_type),
            "source_url": (r.get("source_url") or "").strip() or None,
            "notes": notes,
        })

    records.sort(key=lambda x: x["esr_pct"], reverse=True)

    return {
        "_meta": {
            "as_of": AS_OF_TARGET,
            "as_of_label_ja": AS_OF_LABEL_JA,
            "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "built_from": [CENSUS_CSV.name, SOURCES_CSV.name],
            "next_update": NEXT_UPDATE,
            "census": {
                "total": total,
                "posted": len(posted_rows),
                "not_yet": not_yet,
                "not_found": not_found,
            },
        },
        "records": records,
    }


def self_check(out: dict) -> list[str]:
    errors = []
    recs = out["records"]
    if len(recs) != 15:
        errors.append(f"records count = {len(recs)}, expected 15")
    seen = set()
    for rec in recs:
        name = rec["company_jp"]
        if name in seen:
            errors.append(f"duplicate company_jp: {name}")
        seen.add(name)
        e = rec["esr_pct"]
        if e is None or not isinstance(e, float) or not (100 <= e <= 1000):
            errors.append(f"esr_pct out of range or not float: {name} = {e!r}")
        if rec["scope"] not in ("group", "solo"):
            errors.append(f"bad scope: {name} = {rec['scope']!r}")
        if rec["sector"] not in ("life", "nonlife", "reinsurance"):
            errors.append(f"bad sector: {name} = {rec['sector']!r}")
        su = rec["source_url"]
        if not su or not su.startswith("https://"):
            errors.append(f"source_url not https: {name} = {su!r}")
        if rec["as_of"] != AS_OF_TARGET:
            errors.append(f"as_of != {AS_OF_TARGET}: {name} = {rec['as_of']!r}")
    c = out["_meta"]["census"]
    if c["posted"] + c["not_yet"] + c["not_found"] != c["total"]:
        errors.append(f"census does not sum to total: {c}")
    if c["posted"] != len(recs):
        errors.append(f"census.posted ({c['posted']}) != len(records) ({len(recs)})")
    return errors


def main() -> int:
    out = build()

    errors = self_check(out)
    if errors:
        for e in errors:
            print(f"SELF-CHECK FAIL: {e}", file=sys.stderr)
        return 1

    text = json.dumps(out, ensure_ascii=False, indent=2)

    MASTER_OUT.write_text(text, encoding="utf-8")
    DEPLOY_OUT.parent.mkdir(parents=True, exist_ok=True)
    DEPLOY_OUT.write_text(text, encoding="utf-8")

    a, b = MASTER_OUT.read_bytes(), DEPLOY_OUT.read_bytes()
    if a != b:
        print("SELF-CHECK FAIL: outputs are not byte-identical", file=sys.stderr)
        return 1

    print(f"wrote {MASTER_OUT} and {DEPLOY_OUT}  ({len(out['records'])} records)")
    print(f"  census: {out['_meta']['census']}")
    prelim = [r['company_en'] for r in out['records'] if r['preliminary']]
    print(f"  preliminary={len(prelim)}: {prelim}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
