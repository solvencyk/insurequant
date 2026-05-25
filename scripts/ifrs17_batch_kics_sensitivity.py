# -*- coding: utf-8 -*-
"""Batch: K-ICS quarterly MD -> IFRS17 contract sensitivity JSON (B5).

Outputs:
  data/ifrs17/extracted/KRxxxx_{period}_kics_sensitivity.json
  data/ifrs17/crawl_manifest.json (for --manifest-period or single --period run)
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.stdout.reconfigure(encoding="utf-8")

from src.ifrs17.kics_sensitivity_extractor import (
    extract_kics_sensitivity_from_md,
    ifrs17_measurement_ok_insurers,
    write_kics_sensitivity_json,
)

_PERIOD_DIR_RE = re.compile(r"^FY\d{4}_Q[1-4]$")


def discover_md_inbox_periods(repo_root: Path) -> list[str]:
    md = repo_root / "md_inbox"
    names = [p.name for p in md.iterdir() if p.is_dir() and _PERIOD_DIR_RE.match(p.name)]
    return sorted(names)


def build_manifest(repo_root: Path, period: str, run_summary: dict) -> dict:
    extracted_dir = repo_root / "data" / "ifrs17" / "extracted"
    measurement_rows = json.loads(
        (extracted_dir / "_batch_measurement_summary.json").read_text(encoding="utf-8")
    )
    stem_by_kics: dict[str, str | None] = {}
    for row in measurement_rows:
        if row.get("status") == "ok":
            stem_by_kics[row["kics_name"]] = f"{row['canonical']}_{row['rcept_no']}"

    pairs = ifrs17_measurement_ok_insurers(repo_root)
    insurers = []

    for code, kics_name in pairs:
        stem = stem_by_kics.get(kics_name)
        files: dict[str, str | None] = {
            "measurement": None,
            "measurement_mvp": None,
            "csm": None,
            "sensitivity_dart": None,
            "liability": None,
            "kics_sensitivity": None,
        }
        if stem:
            suffix_map = (
                ("_measurement.json", "measurement"),
                ("_measurement_mvp.json", "measurement_mvp"),
                ("_csm.json", "csm"),
                ("_sensitivity.json", "sensitivity_dart"),
                ("_liability.json", "liability"),
            )
            for sfx, fk in suffix_map:
                fp = extracted_dir / f"{stem}{sfx}"
                if fp.is_file():
                    files[fk] = fp.name
        kics_fp = extracted_dir / f"{code}_{period}_kics_sensitivity.json"
        if kics_fp.is_file():
            files["kics_sensitivity"] = kics_fp.name
        insurers.append(
            {"kics_code": code, "kics_name": kics_name, "dart_stem": stem, "files": files}
        )

    keys = insurers[0]["files"].keys() if insurers else []
    counts = {k: sum(1 for i in insurers if i["files"].get(k)) for k in keys}

    return {
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "period": period,
        "operational_insurers": len(pairs),
        "extracted_dir": str(extracted_dir.relative_to(repo_root)),
        "counts_by_artifact": counts,
        "batch_kics_run": run_summary,
        "insurers": insurers,
    }


def run_one_period(repo_root: Path, period: str, *, mvp_only: bool) -> dict:
    md_dir = repo_root / "md_inbox" / period
    if not md_dir.is_dir():
        raise FileNotFoundError(str(md_dir))

    pairs = ifrs17_measurement_ok_insurers(repo_root)
    code_to_md: dict[str, Path] = {}
    for pth in sorted(md_dir.glob("KR*.md")):
        key = pth.stem.split("_", 1)[0]
        if key.startswith("KR") and len(key) >= 6:
            code_to_md.setdefault(key, pth)

    run_summary: dict = {
        "period": period,
        "insurers_requested": len(pairs),
        "insurers_nonempty": 0,
        "tables_total": 0,
        "per_insurer": [],
    }

    nonempty = 0
    for code, name in pairs:
        md_path = code_to_md.get(code)
        if not md_path:
            run_summary["per_insurer"].append(
                {"kics_code": code, "kics_name": name, "status": "missing_md", "tables": 0}
            )
            continue
        text = md_path.read_text(encoding="utf-8")
        res = extract_kics_sensitivity_from_md(text, name, mvp_only=mvp_only)
        ntab = len(res.tables)
        run_summary["tables_total"] += ntab
        if ntab:
            nonempty += 1
        out_path = repo_root / "data" / "ifrs17" / "extracted" / f"{code}_{period}_kics_sensitivity.json"
        meta = {
            "kics_company_code": code,
            "kics_name": name,
            "fiscal_period": period,
            "source_md": str(md_path.relative_to(repo_root)),
            "source_kind": "kics_quarterly_md",
        }
        write_kics_sensitivity_json(out_path, res.tables, meta)
        run_summary["per_insurer"].append(
            {
                "kics_code": code,
                "kics_name": name,
                "status": "ok" if ntab else "empty",
                "tables": ntab,
                "md_path": str(md_path.relative_to(repo_root)),
                "json_out": str(out_path.relative_to(repo_root)),
            }
        )

    run_summary["insurers_nonempty"] = nonempty
    return run_summary


def main() -> int:
    ap = argparse.ArgumentParser(description="Extract K-ICS MD assumption sensitivity for IFRS17 B5.")
    ap.add_argument("--period", default="FY2025_Q4")
    ap.add_argument("--all-periods", action="store_true", help="Process every md_inbox/FY*_Q* directory.")
    ap.add_argument(
        "--manifest-period",
        default=None,
        help="Period label for crawl_manifest.json (default: --period, or last sorted dir with --all-periods).",
    )
    ap.add_argument("--mvp-only", action="store_true")
    args = ap.parse_args()

    man_path = REPO / "data" / "ifrs17" / "crawl_manifest.json"
    man_path.parent.mkdir(parents=True, exist_ok=True)

    if args.all_periods:
        periods = discover_md_inbox_periods(REPO)
        if not periods:
            print("No FYyyyy_Qn directories found under md_inbox", file=sys.stderr)
            return 1
        full_by_period: dict[str, dict] = {}
        grand = 0
        for period in periods:
            rs = run_one_period(REPO, period, mvp_only=args.mvp_only)
            full_by_period[period] = rs
            grand += rs["tables_total"]

        manifest_period = args.manifest_period or periods[-1]
        if manifest_period not in full_by_period:
            print(f"--manifest-period {manifest_period} was not in the run set", file=sys.stderr)
            return 1

        manifest = build_manifest(REPO, manifest_period, full_by_period[manifest_period])
        man_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

        out = {
            "manifest_period": manifest_period,
            "tables_grand_total_across_periods": grand,
            "by_period_summary": {
                p: {
                    "insurers_requested": full_by_period[p]["insurers_requested"],
                    "insurers_nonempty": full_by_period[p]["insurers_nonempty"],
                    "tables_total": full_by_period[p]["tables_total"],
                }
                for p in periods
            },
            "manifest_run_summary": full_by_period[manifest_period],
        }
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return 0

    manifest_period = args.manifest_period or args.period
    run_summary = run_one_period(REPO, manifest_period, mvp_only=args.mvp_only)
    manifest = build_manifest(REPO, manifest_period, run_summary)
    man_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(run_summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
