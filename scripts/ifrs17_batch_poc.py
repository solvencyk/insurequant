# -*- coding: utf-8 -*-
"""Batch PoC: resolve company name -> corp_code on the fly, fetch the
annual 사업보고서, then run csm_extractor.

Per user rule: no permanent KR<->corp_code map. We re-resolve every run.
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


TARGETS = [
    # company name (substring match on OpenDART corp_name)
    "메리츠화재",
    "삼성화재해상보험",
    "DB손해보험",
    "한화생명",
    "삼성생명",
]


def fetch_annual_rcept_no(client, corp_code, year=2024):
    filings = client.list_filings(
        corp_code=corp_code,
        bgn_de=f"{year + 1}0101",
        end_de=f"{year + 1}0601",
    )
    annual = [f for f in filings
              if "사업보고서" in f.get("report_nm", "")
              and "기재정정" not in f.get("report_nm", "")]
    return annual[0]["rcept_no"] if annual else None


def run_one(client, query, year=2024):
    matches = client.find_corp_codes_by_name(query)
    # Prefer exact name match if it exists; otherwise first.
    exact = [m for m in matches if m["corp_name"] == query]
    chosen = (exact or matches)[0] if matches else None
    if not chosen:
        return {"query": query, "status": "no_match"}

    corp_code = chosen["corp_code"]
    canonical = chosen["corp_name"]
    rcept_no = fetch_annual_rcept_no(client, corp_code, year)
    if not rcept_no:
        return {"query": query, "canonical": canonical, "corp_code": corp_code,
                "status": "no_annual_filing"}

    out_dir = settings.raw_dir / f"{canonical}_{rcept_no}"
    zip_path = out_dir / "document.zip"
    out_dir.mkdir(parents=True, exist_ok=True)
    if not zip_path.is_file():
        client.fetch_document_xml(rcept_no, zip_path)
    with zipfile.ZipFile(zip_path) as zf:
        zf.extractall(out_dir)

    summary_rows = []
    full = []
    for xml in sorted(out_dir.glob("*.xml")):
        try:
            tables = extract_csm_tables(xml)
        except Exception as exc:
            summary_rows.append({"xml": xml.name, "error": str(exc)})
            continue
        for t in tables:
            summary_rows.append({
                "xml": xml.name,
                "caption": t.caption,
                "line_no": t.line_no,
                "score": t.score,
                "rows": len(t.rows),
                "cols": len(t.rows[0]) if t.rows else 0,
                "header_first_row": t.header[0] if t.header else [],
            })
            d = to_jsonable(t)
            d["_source_xml"] = xml.name
            full.append(d)

    out_json = settings.extracted_dir / f"{canonical}_{rcept_no}_csm.json"
    out_json.write_text(json.dumps(full, ensure_ascii=False, indent=2),
                        encoding="utf-8")
    return {
        "query": query,
        "canonical": canonical,
        "corp_code": corp_code,
        "rcept_no": rcept_no,
        "status": "ok",
        "csm_tables_found": len(summary_rows),
        "results": summary_rows,
        "json_out": str(out_json),
    }


def main():
    settings.ensure_dirs()
    client = OpenDARTClient.from_settings()
    summary = []
    for q in TARGETS:
        print(f"\n=== {q} ===")
        try:
            r = run_one(client, q)
        except OpenDARTError as exc:
            r = {"query": q, "status": f"dart_error: {exc}"}
        except Exception:
            print(traceback.format_exc())
            r = {"query": q, "status": "exception"}
        summary.append(r)
        print(json.dumps({k: v for k, v in r.items() if k != "results"},
                         ensure_ascii=False, indent=2))
        if "results" in r:
            for entry in r["results"]:
                print("  -", entry)

    out = settings.extracted_dir / "_batch_summary.json"
    out.write_text(json.dumps(summary, ensure_ascii=False, indent=2),
                   encoding="utf-8")
    print(f"\n[wrote] {out}")


if __name__ == "__main__":
    main()
