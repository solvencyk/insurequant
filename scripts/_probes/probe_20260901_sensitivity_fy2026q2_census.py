# -*- coding: utf-8 -*-
"""2026-09-01 census (inbox: 31x STALE_AS_OF on sensitivity_heatmap after 2026.2Q basis load).

Question: does ANY of the 38 companies with FY2026_Q2 raw actually disclose a genuine
가정민감도(assumption-shock ΔCSM/손익 — 사망률·장해질병·해지율·사업비 shock table) in their
반기보고서? Runs the REAL extractor (extract_sensitivity_tables) against every FY2026_Q2 raw
XML, exactly like ifrs17_batch_sensitivity_fy2025.py does for the annual round, then dumps
every table whose caption/rows mention 민감도/가정/충격 (unfiltered by score) so the answer is
based on what is actually IN the filing, not on the extractor's scoring threshold.

Dir layout differs from FY2025_Q4: `data/dart/FY2026_Q2/raw/KR####_<canonical>/` has NO rcept
suffix; meta.json carries {period, rcept_no, corp_code, canonical, report_kind, no_filing?}.

Finding (2026-09-01): 14/38 have meta.json "no_filing":true (annual-audit-only filers — see
the companion script for live-DART confirmation these never file a periodic 사업/반기/분기
report). Of the 24 that DID file, the extractor's default min_score=4 flags only 4 companies
with a table_kind=='sensitivity_analysis' hit, and full inspection shows every one of those 4
is a false positive: KR0002/KR0010/KR0011 mis-score an unrelated financial-summary/loss-ratio
table, KR0083(푸본현대) mis-scores the CSM *rollforward*'s "해지율/위험률/사업비율 가정 변경"
sub-rows (a REALIZED-this-period assumption-change breakdown inside the measurement rollforward,
not a hypothetical ±X% SHOCK table). The unfiltered caption dump below confirms the other 20
companies carry only IFRS9 fair-value Level-3 sensitivity (a different accounting topic) and/or
point-in-time "현행 추정 가정" value tables (no shock delta) in their half-year filing.
Conclusion: 가정민감도 is annual-only (사업보고서) across the whole universe — not a per-company
gap. See TODO_parser_ifrs17.md 2026-09-01 (78th pass) for the resulting gate fix.

Run: C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/_probes/probe_20260901_sensitivity_fy2026q2_census.py
Offline-safe except for reading local raw XML; no network, no writes outside stdout.
"""
from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.stdout.reconfigure(encoding="utf-8")

from src.ifrs17.csm_extractor import _iter_tables_with_context  # noqa: E402
from src.ifrs17.sensitivity_extractor import extract_sensitivity_tables, to_jsonable  # noqa: E402

RAW_ROOT = ROOT / "data" / "dart" / "FY2026_Q2" / "raw"
DIR_RE = re.compile(r"^(KR\d+)_(.+)$")


def scored_extraction_summary() -> list[dict]:
    """Mirrors ifrs17_batch_sensitivity_fy2025.py's per-company extraction, retargeted to
    FY2026_Q2's flat (no-rcept-suffix) dir layout."""
    out = []
    for d in sorted(RAW_ROOT.iterdir()):
        if not d.is_dir():
            continue
        m = DIR_RE.match(d.name)
        if not m:
            continue
        kr_code, canonical = m.group(1), m.group(2)
        meta_p = d / "meta.json"
        meta = json.loads(meta_p.read_text(encoding="utf-8")) if meta_p.exists() else {}
        if meta.get("no_filing"):
            out.append({"kr_code": kr_code, "canonical": canonical, "no_filing": True})
            continue
        all_tables = []
        for xml in sorted(d.glob("*.xml")):
            for t in extract_sensitivity_tables(xml, company_name=canonical):
                all_tables.append(to_jsonable(t))
        n_sa = sum(1 for t in all_tables if t.get("table_kind") == "sensitivity_analysis")
        out.append({"kr_code": kr_code, "canonical": canonical, "no_filing": False,
                    "report_kind": meta.get("report_kind"), "n_tables": len(all_tables),
                    "n_sensitivity_analysis": n_sa})
    return out


def unfiltered_caption_dump() -> dict[str, dict]:
    """Per filed company: every DISTINCT table caption whose caption or first-15-row-labels
    mention 민감도/가정/충격, regardless of extractor score -- ground truth independent of the
    min_score=4 threshold."""
    by_company: dict[str, dict] = {}
    for d in sorted(RAW_ROOT.iterdir()):
        if not d.is_dir():
            continue
        m = DIR_RE.match(d.name)
        if not m:
            continue
        kr_code, canonical = m.group(1), m.group(2)
        meta = json.loads((d / "meta.json").read_text(encoding="utf-8")) if (d / "meta.json").exists() else {}
        if meta.get("no_filing"):
            continue
        by_caption = defaultdict(lambda: {"n": 0, "max_rows": 0})
        for xml in sorted(d.glob("*.xml")):
            for t in _iter_tables_with_context(xml):
                cap = t.caption or ""
                row_labels = " ".join((r[0] if r else "") for r in (t.rows or [])[:15])
                hay = cap + " " + row_labels
                if ("민감도" in hay) or ("가정" in cap) or ("충격" in hay):
                    e = by_caption[cap.strip()]
                    e["n"] += 1
                    e["max_rows"] = max(e["max_rows"], len(t.rows or []))
        by_company[f"{kr_code} {canonical}"] = dict(by_caption)
    return by_company


if __name__ == "__main__":
    summary = scored_extraction_summary()
    n_nofiling = sum(1 for r in summary if r["no_filing"])
    n_filed = len(summary) - n_nofiling
    n_sa = sum(1 for r in summary if not r["no_filing"] and r.get("n_sensitivity_analysis", 0) > 0)
    print(f"[scored] {len(summary)} companies; no_filing={n_nofiling} filed={n_filed} "
          f"filed_with_extractor_SA_hit={n_sa} (verified false-positive in all 4 -- see docstring)")
    print()
    dump = unfiltered_caption_dump()
    for co, captions in dump.items():
        print(f"### {co} -- {len(captions)} distinct 민감도/가정/충격 captions")
        for cap, e in sorted(captions.items(), key=lambda kv: -kv[1]["n"]):
            print(f"  n={e['n']:3d} max_rows={e['max_rows']:3d} caption={cap[:120]!r}")
