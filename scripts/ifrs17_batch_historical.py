# -*- coding: utf-8 -*-
"""IFRS17 historical filings ingest — 23 insurers × 13 quarters (2023.1Q ~ 2026.1Q).

Per-quarter targeting (DART pblntf_detail_ty):
  1Q (Mar end)   -> 분기보고서 (A002), filing window: May ~ mid-Jun of same year
  H1 (Jun end)   -> 반기보고서 (A003), filing window: Aug ~ mid-Sep of same year
  3Q (Sep end)   -> 분기보고서 (A002), filing window: Nov ~ mid-Dec of same year
  FY (Dec end)   -> 사업보고서 (A001), filing window: Mar ~ May of next year

Output layout (canonical, post Reorg #2):
  data/dart/FY<year>_Q<q>/raw/<KR####>_<canonical>/...           (분기/반기)
  data/dart/FY<year>_Q4/raw/<KR####>_<canonical>_<rcept>/...     (사업보고서)
  data/dart/extracted_history/<canonical>__<YYYY.QQ>_csm.json    (per period)
  data/dart/extracted_history/_historical_summary.json

Usage:
  python scripts/ifrs17_batch_historical.py --pilot KR0068    # one insurer
  python scripts/ifrs17_batch_historical.py --pilot KR0068,KR0069
  python scripts/ifrs17_batch_historical.py --all             # all 23
  python scripts/ifrs17_batch_historical.py --all --periods 2025.4Q,2026.1Q  # subset
  python scripts/ifrs17_batch_historical.py --all --skip-extract              # fetch only

Reuses ``ifrs17_batch_all.resolve_corp`` + ``ifrs17.csm_table_extractor.extract_csm_tables``.
"""
from __future__ import annotations

import argparse
import json
import sys
import traceback
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.stdout.reconfigure(encoding="utf-8")

from src.ifrs17.config import settings  # noqa: E402
from src.ifrs17.opendart_client import OpenDARTClient, OpenDARTError  # noqa: E402
from src.ifrs17.csm_extractor import extract_csm_tables, to_jsonable  # noqa: E402

from scripts.ifrs17_batch_all import resolve_corp, load_company_names  # noqa: E402

# Canonical raw-path helpers (post-Reorg #2). Per-period FY<y>_Q<q>/raw/.
from scripts._dart_path_helpers import (  # noqa: E402
    annual_raw_dir,
    quarterly_raw_dir,
)

# ---------------------------------------------------------------------------
# Period targets
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class PeriodTarget:
    label: str          # "2023.1Q"
    bgn_de: str         # "20230501"
    end_de: str         # "20230630"
    pblntf_detail_ty: str   # A001=사업, A002=분기, A003=반기
    report_keyword: str     # "분기보고서" / "반기보고서" / "사업보고서"


def _make_targets() -> list[PeriodTarget]:
    """13 quarters: 2023.1Q ~ 2026.1Q."""
    targets: list[PeriodTarget] = []
    # FY 2023 ~ 2025 + 2026.1Q
    for fy in (2023, 2024, 2025):
        # 1Q
        targets.append(PeriodTarget(
            label=f"{fy}.1Q",
            bgn_de=f"{fy}0501", end_de=f"{fy}0630",
            pblntf_detail_ty="A002", report_keyword="분기보고서",
        ))
        # H1 (2Q label per user convention)
        targets.append(PeriodTarget(
            label=f"{fy}.2Q",
            bgn_de=f"{fy}0801", end_de=f"{fy}0930",
            pblntf_detail_ty="A003", report_keyword="반기보고서",
        ))
        # 3Q
        targets.append(PeriodTarget(
            label=f"{fy}.3Q",
            bgn_de=f"{fy}1101", end_de=f"{fy}1215",
            pblntf_detail_ty="A002", report_keyword="분기보고서",
        ))
        # FY (filed next year)
        targets.append(PeriodTarget(
            label=f"{fy}.4Q",
            bgn_de=f"{fy + 1}0301", end_de=f"{fy + 1}0531",
            pblntf_detail_ty="A001", report_keyword="사업보고서",
        ))
    # 2026.1Q
    targets.append(PeriodTarget(
        label="2026.1Q",
        bgn_de="20260501", end_de="20260630",
        pblntf_detail_ty="A002", report_keyword="분기보고서",
    ))
    return targets


ALL_TARGETS = _make_targets()
TARGETS_BY_LABEL = {t.label: t for t in ALL_TARGETS}


# ---------------------------------------------------------------------------
# Per-period pipeline
# ---------------------------------------------------------------------------

# Canonical layout uses per-period dirs (Reorg #2). HIST_RAW is gone — paths
# now resolved via scripts._dart_path_helpers.{quarterly,annual}_raw_dir.
HIST_EXTRACTED = settings.repo_root / "data" / "dart" / "extracted_history"


def _stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def fetch_rcept_no(
    client: OpenDARTClient,
    corp_code: str,
    target: PeriodTarget,
) -> str | None:
    filings = client.list_filings(
        corp_code=corp_code,
        bgn_de=target.bgn_de,
        end_de=target.end_de,
        pblntf_detail_ty=target.pblntf_detail_ty,
    )
    # Filter to exactly the target keyword + skip 기재정정 amended re-filings
    primary = [
        f for f in filings
        if target.report_keyword in f.get("report_nm", "")
        and "기재정정" not in f.get("report_nm", "")
    ]
    if primary:
        return primary[0]["rcept_no"]
    # Fallback: include 기재정정 if no primary
    amended = [
        f for f in filings
        if target.report_keyword in f.get("report_nm", "")
    ]
    return amended[0]["rcept_no"] if amended else None


def process_one_period(
    client: OpenDARTClient,
    insurer_code: str,
    canonical: str,
    corp_code: str,
    target: PeriodTarget,
    *,
    skip_extract: bool = False,
) -> dict:
    # Annual (사업보고서) goes into FY{Y}_Q4/raw/<KR>_<name>_<rcept>/, so we
    # need rcept_no *before* the out_dir exists. Quarterly path is
    # rcept-independent → cache meta.json in dir.
    is_annual = target.pblntf_detail_ty == "A001"
    kr_code = insurer_code if (insurer_code and insurer_code.startswith("KR")) else None

    rcept_no: str | None = None
    if is_annual:
        try:
            rcept_no = fetch_rcept_no(client, corp_code, target)
        except OpenDARTError as exc:
            return {
                "insurer_code": insurer_code, "canonical": canonical,
                "period": target.label, "status": f"list_error: {exc}",
            }
        if not rcept_no:
            return {
                "insurer_code": insurer_code, "canonical": canonical,
                "period": target.label, "status": "no_filing",
            }
        out_dir = annual_raw_dir(
            canonical_name=canonical, rcept_no=rcept_no,
            kr_code=kr_code, corp_code=corp_code,
        )
        out_dir.mkdir(parents=True, exist_ok=True)
    else:
        out_dir = quarterly_raw_dir(
            canonical_name=canonical, period_label=target.label,
            kr_code=kr_code, corp_code=corp_code,
        )
        out_dir.mkdir(parents=True, exist_ok=True)
        meta_path_q = out_dir / "meta.json"
        cached: dict = {}
        if meta_path_q.exists():
            try:
                cached = json.loads(meta_path_q.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                cached = {}
        rcept_no = cached.get("rcept_no")
        if not rcept_no:
            try:
                rcept_no = fetch_rcept_no(client, corp_code, target)
            except OpenDARTError as exc:
                return {
                    "insurer_code": insurer_code, "canonical": canonical,
                    "period": target.label, "status": f"list_error: {exc}",
                }
            if not rcept_no:
                meta_path_q.write_text(
                    json.dumps({"period": target.label, "no_filing": True}, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )
                return {
                    "insurer_code": insurer_code, "canonical": canonical,
                    "period": target.label, "status": "no_filing",
                }

    meta_path = out_dir / "meta.json"

    zip_path = out_dir / "document.zip"
    if not zip_path.is_file():
        try:
            client.fetch_document_xml(rcept_no, zip_path)
        except OpenDARTError as exc:
            return {
                "insurer_code": insurer_code, "canonical": canonical,
                "period": target.label, "rcept_no": rcept_no,
                "status": f"download_error: {exc}",
            }

    meta_path.write_text(
        json.dumps({
            "period": target.label,
            "rcept_no": rcept_no,
            "corp_code": corp_code,
            "canonical": canonical,
            "report_kind": target.report_keyword,
            "fetched_at": _stamp(),
        }, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    if skip_extract:
        return {
            "insurer_code": insurer_code, "canonical": canonical,
            "period": target.label, "rcept_no": rcept_no,
            "status": "fetched",
        }

    extract_dir = out_dir / "xml"
    if not any(extract_dir.glob("*.xml")):
        extract_dir.mkdir(exist_ok=True)
        try:
            with zipfile.ZipFile(zip_path) as zf:
                zf.extractall(extract_dir)
        except zipfile.BadZipFile as exc:
            return {
                "insurer_code": insurer_code, "canonical": canonical,
                "period": target.label, "rcept_no": rcept_no,
                "status": f"bad_zip: {exc}",
            }

    full: list[dict] = []
    parse_errors: list[dict] = []
    for xml in sorted(extract_dir.glob("*.xml")):
        try:
            tables = extract_csm_tables(xml)
        except Exception as exc:
            parse_errors.append({"xml": xml.name, "error": str(exc)})
            continue
        for t in tables:
            d = to_jsonable(t)
            d["_source_xml"] = xml.name
            full.append(d)

    HIST_EXTRACTED.mkdir(parents=True, exist_ok=True)
    out_json = HIST_EXTRACTED / f"{canonical}__{target.label}_csm.json"
    out_json.write_text(json.dumps(full, ensure_ascii=False, indent=2), encoding="utf-8")

    status = "ok" if full else "no_csm_table_found"
    return {
        "insurer_code": insurer_code, "canonical": canonical,
        "period": target.label, "rcept_no": rcept_no,
        "status": status,
        "csm_tables_found": len(full),
        "parse_errors": len(parse_errors),
        "json_out": str(out_json.relative_to(REPO)),
    }


# ---------------------------------------------------------------------------
# Universe + dispatch
# ---------------------------------------------------------------------------

def _load_kics_insurer_map() -> dict[str, str]:
    """Return {KR_code: 원수사명}. Drop entries without code."""
    data = json.loads((REPO / "kics_disclosure.json").read_text(encoding="utf-8"))
    by_name: dict[str, str | None] = {}
    for row in data:
        name = row.get("원수사명")
        code = row.get("원보험사코드") or row.get("원수사코드") or row.get("회사코드") or None
        # Update if we don't have a code yet for this name
        if name and (name not in by_name or by_name[name] is None):
            by_name[name] = code
    # Reverse so we can also look up by code
    return {code: name for name, code in by_name.items() if code}


def _load_ifrs17_universe_names() -> list[tuple[str | None, str]]:
    """Return [(KR_code or None, 원수사명)] for the 23-insurer IFRS17 universe.

    Filters out NON_LISTED_SKIP + EXCLUDED_SKIP per src.ifrs17.universe.
    """
    try:
        from src.ifrs17.universe import ALL_EXCLUDED  # type: ignore
    except Exception:
        ALL_EXCLUDED = frozenset()
    code_by_name = {v: k for k, v in _load_kics_insurer_map().items()}
    names = load_company_names()
    return [(code_by_name.get(n), n) for n in names if n not in ALL_EXCLUDED]


def main() -> int:
    ap = argparse.ArgumentParser(description="IFRS17 historical ingest 2023.1Q ~ 2026.1Q")
    ap.add_argument("--pilot", type=str, default=None,
                    help="Comma list of KR codes OR 원수사명 to run pilot")
    ap.add_argument("--all", action="store_true", help="Run all IFRS17 universe (23)")
    ap.add_argument("--periods", type=str, default=None,
                    help="Comma list of period labels (e.g. 2025.4Q,2026.1Q). Default: all 13")
    ap.add_argument("--skip-extract", action="store_true",
                    help="Fetch only, no CSM parsing")
    args = ap.parse_args()

    if not args.pilot and not args.all:
        ap.error("specify --pilot CODE or --all")

    targets = ALL_TARGETS
    if args.periods:
        wanted = {p.strip() for p in args.periods.split(",") if p.strip()}
        targets = [t for t in ALL_TARGETS if t.label in wanted]
        if not targets:
            ap.error(f"no targets match --periods (available: {sorted(TARGETS_BY_LABEL)})")

    universe = _load_ifrs17_universe_names()
    if args.pilot:
        wanted_pilot = {x.strip() for x in args.pilot.split(",") if x.strip()}
        universe = [
            (code, name) for (code, name) in universe
            if (code and code in wanted_pilot) or name in wanted_pilot
        ]
        if not universe:
            ap.error(f"no insurers match --pilot {args.pilot!r}")

    settings.ensure_dirs()
    client = OpenDARTClient.from_settings()

    print(f"[historical] insurers={len(universe)} periods={len(targets)} "
          f"total_targets={len(universe) * len(targets)}")

    summary: list[dict] = []
    for i, (code, kics_name) in enumerate(universe, 1):
        print(f"\n[{i}/{len(universe)}] === {code or '?'} {kics_name} ===")
        try:
            chosen = resolve_corp(client, kics_name)
        except OpenDARTError as exc:
            print(f"  resolve_corp failed: {exc}")
            summary.append({"insurer_code": code, "kics_name": kics_name,
                            "status": f"resolve_error: {exc}"})
            continue
        if not chosen:
            print(f"  resolve_corp -> no match")
            summary.append({"insurer_code": code, "kics_name": kics_name,
                            "status": "no_corp_match"})
            continue
        canonical = chosen["corp_name"]
        corp_code = chosen["corp_code"]
        for t in targets:
            try:
                r = process_one_period(
                    client, code or "?", canonical, corp_code, t,
                    skip_extract=args.skip_extract,
                )
            except Exception as exc:
                print(traceback.format_exc())
                r = {
                    "insurer_code": code, "canonical": canonical,
                    "period": t.label, "status": f"exception: {exc}",
                }
            print(f"  {t.label}: {r.get('status')} csm={r.get('csm_tables_found', '-')}")
            summary.append(r)

    HIST_EXTRACTED.mkdir(parents=True, exist_ok=True)
    summary_path = HIST_EXTRACTED / "_historical_summary.json"
    summary_path.write_text(
        json.dumps({"generated_at": _stamp(),
                    "insurers": len(universe),
                    "periods": [t.label for t in targets],
                    "results": summary},
                   ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    statuses: dict[str, int] = {}
    for r in summary:
        s = r.get("status", "?")
        statuses[s] = statuses.get(s, 0) + 1
    print(f"\n[summary] total={len(summary)}")
    for s, n in sorted(statuses.items(), key=lambda x: -x[1]):
        print(f"  {s}: {n}")
    print(f"[wrote] {summary_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
