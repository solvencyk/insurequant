# -*- coding: utf-8 -*-
"""Batch: fetch the latest annual report for every K-ICS insurer and
extract CSM tables.

Company list source: unique 원수사명 in ``kics_disclosure.json`` (per the
user's instruction: no permanent KR<->corp_code map, just search by name
on the fly).

Per-company artefacts (canonical layout, Reorg #2):
  data/dart/FY<year>_Q4/raw/<KR####>_<canonical>_<rcept_no>/...
  data/dart/extracted/<canonical_corp_name>_<rcept_no>_csm.json

Final summary:
  data/dart/extracted/_batch_all_summary.json
"""

from __future__ import annotations

import json
import sys
import traceback
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.stdout.reconfigure(encoding="utf-8")

from src.ifrs17.config import settings  # noqa: E402
from src.ifrs17.opendart_client import OpenDARTClient, OpenDARTError  # noqa: E402
from src.ifrs17.csm_extractor import extract_csm_tables, to_jsonable  # noqa: E402

# Canonical raw-path helper (post-Reorg #2). Path = data/dart/FY<y>_Q4/raw/...
from scripts._dart_path_helpers import annual_raw_dir  # noqa: E402


# ---------------------------------------------------------------------------
# Company list
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parents[1]
KICS_JSON = REPO_ROOT / "kics_disclosure.json"


def load_company_names() -> list[str]:
    """Return unique insurer names from kics_disclosure.json."""
    data = json.loads(KICS_JSON.read_text(encoding="utf-8"))
    names = sorted({row["원수사명"] for row in data if row.get("원수사명")})
    return names


# Manual aliases for the few cases where the DART corp_name differs from
# the K-ICS 원수사명. Keys are kics_disclosure 원수사명; values are the query
# strings to use against OpenDART corp_name (substring match). Kept short
# on purpose — per user rule we do NOT maintain a permanent corp_code map,
# this only resolves *names that OpenDART spells differently*.
NAME_ALIASES: dict[str, str] = {
    "삼성생명보험": "삼성생명",
    "IBK연금보험": "아이비케이연금보험",
    "KB라이프생명": "케이비라이프생명보험",
    "코리안리재보험": "코리안리",
}


def resolve_corp(client: OpenDARTClient, kics_name: str) -> dict | None:
    """Return one chosen corp record for ``kics_name`` or None."""
    query = NAME_ALIASES.get(kics_name, kics_name)
    matches = client.find_corp_codes_by_name(query)
    if not matches:
        # Try a shorter fallback: drop trailing "보험" if it's there.
        if kics_name.endswith("보험"):
            short = kics_name[:-2]
            matches = client.find_corp_codes_by_name(short)
            query = short
        if not matches:
            return None
    # Prefer exact match, then "full-name with 보험 suffix" match, then first.
    exact = [m for m in matches if m["corp_name"] == kics_name]
    if exact:
        return exact[0]
    exact_query = [m for m in matches if m["corp_name"] == query]
    if exact_query:
        return exact_query[0]
    # Prefer one with a stock_code (listed company) if available.
    listed = [m for m in matches if m.get("stock_code")]
    if listed:
        return listed[0]
    return matches[0]


# ---------------------------------------------------------------------------
# Per-company pipeline
# ---------------------------------------------------------------------------

def fetch_annual_rcept_no(client, corp_code, year=2024) -> str | None:
    filings = client.list_filings(
        corp_code=corp_code,
        bgn_de=f"{year + 1}0101",
        end_de=f"{year + 1}0601",
    )
    annual = [
        f for f in filings
        if "사업보고서" in f.get("report_nm", "")
        and "기재정정" not in f.get("report_nm", "")
    ]
    return annual[0]["rcept_no"] if annual else None


def run_one(client, kics_name: str, year: int = 2024) -> dict:
    chosen = resolve_corp(client, kics_name)
    if not chosen:
        return {"kics_name": kics_name, "status": "no_corp_match"}
    corp_code = chosen["corp_code"]
    canonical = chosen["corp_name"]

    rcept_no = fetch_annual_rcept_no(client, corp_code, year)
    if not rcept_no:
        return {
            "kics_name": kics_name, "canonical": canonical,
            "corp_code": corp_code, "status": "no_annual_filing",
        }

    out_dir = annual_raw_dir(
        canonical_name=canonical,
        rcept_no=rcept_no,
        kics_name=kics_name,
        corp_code=corp_code,
    )
    zip_path = out_dir / "document.zip"
    out_dir.mkdir(parents=True, exist_ok=True)
    if not zip_path.is_file():
        try:
            client.fetch_document_xml(rcept_no, zip_path)
        except OpenDARTError as exc:
            return {
                "kics_name": kics_name, "canonical": canonical,
                "corp_code": corp_code, "rcept_no": rcept_no,
                "status": f"download_error: {exc}",
            }
    try:
        with zipfile.ZipFile(zip_path) as zf:
            zf.extractall(out_dir)
    except zipfile.BadZipFile as exc:
        return {
            "kics_name": kics_name, "canonical": canonical,
            "corp_code": corp_code, "rcept_no": rcept_no,
            "status": f"bad_zip: {exc}",
        }

    summary_rows = []
    full = []
    parse_errors = []
    for xml in sorted(out_dir.glob("*.xml")):
        try:
            tables = extract_csm_tables(xml)
        except Exception as exc:
            parse_errors.append({"xml": xml.name, "error": str(exc)})
            continue
        for t in tables:
            summary_rows.append({
                "xml": xml.name,
                "caption": t.caption[:120],
                "form_type": t.form_type,
                "line_no": t.line_no,
                "score": t.score,
                "rows": len(t.rows),
                "cols": len(t.rows[0]) if t.rows else 0,
            })
            d = to_jsonable(t)
            d["_source_xml"] = xml.name
            full.append(d)

    out_json = settings.extracted_dir / f"{canonical}_{rcept_no}_csm.json"
    out_json.write_text(json.dumps(full, ensure_ascii=False, indent=2),
                        encoding="utf-8")
    status = "ok" if full else "no_csm_table_found"
    return {
        "kics_name": kics_name,
        "canonical": canonical,
        "corp_code": corp_code,
        "rcept_no": rcept_no,
        "status": status,
        "csm_tables_found": len(full),
        "form_type_counts": _count_forms(full),
        "results_preview": summary_rows[:5],
        "parse_errors": parse_errors,
        "json_out": str(out_json),
    }


def _count_forms(tables: list[dict]) -> dict[str, int]:
    out: dict[str, int] = {}
    for t in tables:
        ft = t.get("form_type") or "unknown"
        out[ft] = out.get(ft, 0) + 1
    return out


def main():
    settings.ensure_dirs()
    client = OpenDARTClient.from_settings()

    names = load_company_names()
    print(f"[start] {len(names)} companies from kics_disclosure.json")

    summary = []
    for i, name in enumerate(names, 1):
        print(f"\n[{i}/{len(names)}] === {name} ===")
        try:
            r = run_one(client, name)
        except OpenDARTError as exc:
            r = {"kics_name": name, "status": f"dart_error: {exc}"}
        except Exception:
            print(traceback.format_exc())
            r = {"kics_name": name, "status": "exception"}
        # Skinny print
        keys = ("canonical", "status", "csm_tables_found", "form_type_counts")
        print(json.dumps(
            {k: r.get(k) for k in keys if k in r},
            ensure_ascii=False,
        ))
        summary.append(r)

    out = settings.extracted_dir / "_batch_all_summary.json"
    out.write_text(json.dumps(summary, ensure_ascii=False, indent=2),
                   encoding="utf-8")

    # Headline counts
    ok = sum(1 for r in summary if r.get("status") == "ok")
    no_table = sum(1 for r in summary if r.get("status") == "no_csm_table_found")
    no_filing = sum(1 for r in summary if r.get("status") == "no_annual_filing")
    no_match = sum(1 for r in summary if r.get("status") == "no_corp_match")
    other = len(summary) - ok - no_table - no_filing - no_match
    print(f"\n[summary] total={len(summary)} ok={ok} "
          f"no_csm_table={no_table} no_filing={no_filing} "
          f"no_corp_match={no_match} other={other}")
    print(f"[wrote] {out}")


if __name__ == "__main__":
    main()
