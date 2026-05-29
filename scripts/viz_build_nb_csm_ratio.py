#!/usr/bin/env python3
"""Build data/ir/nb_csm_ratio.json from IR text artifacts.

Definition (TODO Decision #3): NB CSM ratio = New-business CSM / Monthly initial premium (wol-nap wol-cho).
Ratios are taken directly from IR PDF body text extracts in artifacts/ir_research/.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts" / "ir_research"
OUT_PATH = ROOT / "data" / "ir" / "nb_csm_ratio.json"
OUT_EMBED_JS = ROOT / "data" / "ir" / "nb_csm_ratio.embed.js"
TEMPLATES_OUT = ROOT / "templates" / "data" / "ir" / "nb_csm_ratio.json"
TEMPLATES_EMBED_OUT = ROOT / "templates" / "data" / "ir" / "nb_csm_ratio.embed.js"

FY24_QS = ["FY24.1Q", "FY24.2Q", "FY24.3Q", "FY24.4Q", "FY25.1Q"]

# Data-integrity gate. A real NB CSM multiple (신계약 CSM ÷ 월납환산 초회보험료)
# tops out around 30-50x in practice; anything above this (or non-positive) is a
# parse error — typically an absolute CSM amount (십억원) misread as a ratio.
# (Caught the Samsung Life 사망 series reading 459/471/520 instead of ~5-10.)
MAX_PLAUSIBLE_MULTIPLE = 60.0

# Chronological buckets used across non-life IR extracts (Samsung Fire + Hyundai M&F).
_NONLIFE_AXIS_ORDER = [
    "2024.1H",
    "2024.2Q",
    "2025.1Q",
    "2025.2Q",
    "2025.1H",
    "2025.3Q",
]

# Text extracts consumed by build_payload (not every file in artifacts/ir_research/).
SOURCE_TXT_USED = (
    "samsungfire_2025_3q.txt",
    "hyundai_mar_2025_1h.txt",
    "db_2025_results.txt",
    "kbfg_2025_4q.txt",
    "samsung_life_2025_1q.txt",
    "hanwha_life_2025_1q.txt",
)


def _read(name: str) -> str:
    path = ARTIFACTS / name
    raw = path.read_bytes()
    for enc in ("utf-8", "cp949", "utf-16"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def _points(periods: list[str], values: list[float]) -> list[dict]:
    if len(periods) != len(values):
        raise ValueError(f"period/value length mismatch: {len(periods)} vs {len(values)}")
    return [{"period": p, "value": v} for p, v in zip(periods, values)]


def extract_samsung_life(text: str) -> dict:
    """Samsung Life FY25 1Q IR deck, slide '신계약 CSM' (p.8)."""
    anchor = text.find("1) 신계약 CSM ÷ 월납월초")
    if anchor < 0:
        raise ValueError("Samsung Life: missing '신계약 CSM ÷ 월납월초' anchor")

    chunk = text[max(0, anchor - 1200) : anchor + 80]

    total_m = re.search(
        r"([\d\.]+)\s+([\d\.]+)\s+([\d\.]+)\s+([\d\.]+)\s+([\d\.]+)배",
        chunk,
    )
    if not total_m:
        raise ValueError("Samsung Life: total ratio row not found")
    total_vals = [float(total_m.group(i)) for i in range(1, 6)]

    health_m = re.search(
        r"([\d\.]+)\s+([\d\.]+)\s+([\d\.]+)\s+([\d\.]+)\s+([\d\.]+)배\s*건강",
        chunk,
    )
    if not health_m:
        # first health point may sit on the previous line in PDF extract
        health_m = re.search(
            r"([\d\.]+)\s*\n\s*([\d\.]+)\s+([\d\.]+)\s+([\d\.]+)\s+([\d\.]+)배\s*건강",
            chunk,
        )
    if not health_m:
        raise ValueError("Samsung Life: health ratio row not found")
    health_vals = [float(health_m.group(i)) for i in range(1, 6)]

    # Death (사망/종신) multiples. The PDF extract interleaves the death
    # multiples (single digits) with absolute CSM amounts (십억원, hundreds) on
    # adjacent lines, so a positional 5-number regex grabbed the amounts
    # (459/435/520/471/488) — the 400x+ parse bug. Instead scan the region
    # between the health row (건강) and the 사망 label and keep only the
    # plausible-multiple values (< cap); the amounts are filtered out.
    # rfind: the first 사망 is the column header (건강 사망 금융); we want the
    # data-row 사망 at the bottom of the chart block.
    death_anchor = chunk.rfind("사망")
    if death_anchor < 0:
        raise ValueError("Samsung Life: 사망 label not found")
    region = chunk[:death_anchor]
    h_pos = region.rfind("건강")
    death_region = region[h_pos:] if h_pos >= 0 else region
    death_floats = [float(x) for x in re.findall(r"\d+\.\d+", death_region)]
    death_vals = [v for v in death_floats if 0 < v < MAX_PLAUSIBLE_MULTIPLE]
    if len(death_vals) != 5:
        raise ValueError(
            f"Samsung Life: expected 5 plausible death multiples, got {death_vals} "
            f"(region floats: {death_floats})"
        )

    # Financial ratios are often wrapped across lines (3.4 / 3.0 / … / 금융 / trailing 3.0).
    fin_main = re.search(
        r"([\d\.]+)\s*\n\s*([\d\.]+)\s*\n\s*([\d\.]+)\s+([\d\.]+)[^\n]*금융",
        chunk,
    )
    if fin_main:
        fin_vals = [float(fin_main.group(i)) for i in range(1, 5)]
        tail = chunk[fin_main.end() : fin_main.end() + 120]
        m5 = re.search(r"\n\s*([\d\.]+)", tail)
        if not m5:
            raise ValueError("Samsung Life: financial ratio trailing value not found")
        fin_vals.append(float(m5.group(1)))
    else:
        fin_block = re.search(
            r"([\d\.]+)\s+([\d\.]+)\s+([\d\.]+)\s+([\d\.]+)\s+([\d\.]+)\s*\n\s*\n\s*1Q FY24",
            chunk,
        )
        if not fin_block:
            fin_block = re.search(
                r"([\d\.]+)\s*\n\s*([\d\.]+)\s+([\d\.]+)\s+([\d\.]+)\s+([\d\.]+)\s*\n\s*\n\s*1Q FY24",
                chunk,
            )
        if not fin_block:
            raise ValueError("Samsung Life: financial ratio row not found")
        fin_vals = [float(fin_block.group(i)) for i in range(1, 6)]

    return {
        "label": "Samsung Life",
        "source_pdf": "samsung_life_2025_1q.pdf",
        "source_citation": "FY25 1Q IR slide '신계약 CSM', footnote 1) 신계약 CSM ÷ 월납월초",
        "series": {
            "total": {
                "label": "Total (all products)",
                "points": _points(FY24_QS, total_vals),
            },
            "health": {
                "label": "Health",
                "points": _points(FY24_QS, health_vals),
            },
            "death": {
                "label": "Death",
                "points": _points(FY24_QS, death_vals),
            },
            "financial": {
                "label": "Financial",
                "points": _points(FY24_QS, fin_vals),
            },
        },
    }


def extract_samsung_fire(text: str) -> dict:
    """Samsung F&MI 3Q25 IR — protection-type quarterly CSM multiplier."""
    m = re.search(r"\*월납환산\s+([\d\.]+)\s+([\d\.]+)\s+([\d\.]+)", text)
    if not m:
        raise ValueError("Samsung Fire: protection quarterly ratios not found")
    vals = [float(m.group(i)) for i in range(1, 4)]
    return {
        "label": "Samsung F&MI",
        "source_pdf": "samsungfire_2025_3q.pdf",
        "source_citation": "3Q25 IR '장기보험 - 신계약 CSM', 보장성 환산배수 (월납환산) 1Q25-3Q25",
        "series": {
            "protection_only": {
                "label": "Protection-type only",
                "points": _points(["2025.1Q", "2025.2Q", "2025.3Q"], vals),
            }
        },
        "single_point": {
            "ytd_2024_1_3Q_total": 13.5,
            "ytd_2025_1_3Q_total": 14.1,
        },
        "notes": "Total (all products) only available as YTD comparison; only protection-type is broken out quarterly.",
    }


def extract_hyundai_marine(text: str) -> dict:
    """Hyundai M&F 1H25 IR — CSM multiplier by product line."""
    anchor = text.find("신계약(월납환산) CSM 배수")
    if anchor < 0:
        raise ValueError("Hyundai Marine: CSM multiplier section not found")
    chunk = text[anchor : anchor + 1200]

    block_m = re.search(
        r"([\d\.]+)\s+([\d\.]+)\s+([\d\.]+)\s+([\d\.]+)\s*\n"
        r"\s*([\d\.]+)\s+([\d\.]+)\s+([\d\.]+)\s+([\d\.]+)",
        chunk,
    )
    if not block_m:
        raise ValueError("Hyundai Marine: CSM multiplier rows not found")

    g = block_m.groups()
    personal = [float(g[0]), float(g[4]), float(g[1]), float(g[5])]
    total = [float(g[6]), float(g[2]), float(g[7]), float(g[3])]

    prop_m = re.search(
        r"([\d\.]+)\s+([\d\.]+)\s+([\d\.]+)\s+([\d\.]+)\s*\n\s*\n\s+'24\.1H",
        chunk,
    )
    if not prop_m:
        raise ValueError("Hyundai Marine: property/savings ratios not found")
    prop = [float(prop_m.group(i)) for i in range(1, 5)]

    periods = ["2024.1H", "2024.2Q", "2025.1H", "2025.2Q"]
    return {
        "label": "Hyundai M&F",
        "source_pdf": "hyundai_mar_2025_1h.pdf",
        "source_citation": "1H25 IR slide 5, 신계약(월납환산) CSM 배수 (원수기준)",
        "series": {
            "total": {"label": "Total (all products)", "points": _points(periods, total)},
            "personal_insurance": {"label": "Personal insurance", "points": _points(periods, personal)},
            "property_savings": {"label": "Property/savings", "points": _points(periods, prop)},
        },
        "notes": "Hyundai uses 1H rather than 1Q; 2025.2H is forward guidance — excluded.",
    }


def extract_db_insurance(text: str) -> dict:
    return {
        "label": "DB Insurance",
        "source_pdf": "db_2025_results.pdf",
        "source_citation": "2025 results IR slide 4, 신계약CSM 배수 annual snapshot",
        "series": {},
        "single_point": {
            "2024_total": 14.3,
            "2025_total_via_4Q_avg": 16.3,
            "protection_2024": 14.3,
            "protection_2025": 16.9,
            "savings_2024": 0.7,
            "savings_2025": 5.1,
        },
        "notes": "Only annual/4Q snapshot in IR deck; no quarterly time series. Excluded from line chart.",
    }


def extract_kb_insurance(_text: str) -> dict:
    return {
        "label": "KB Insurance",
        "source_pdf": "kbfg_2025_4q.pdf",
        "source_citation": "KB Financial Group 4Q25 IR — company-level NB CSM ratio not disclosed",
        "series": {},
        "notes": "KB shares only group-level summary; quarterly NB CSM ratio not disclosed. Excluded from line chart.",
    }


def extract_hanwha_life(text: str) -> dict:
    """Hanwha Life 1Q25 IR — YoY CSM profitability (total / general protection)."""
    block = re.search(
        r"신계약 CSM 수익성 1\)[\s\S]{0,500}?"
        r"([\d\.]+)배[\s\S]{0,120}?([\d\.]+)배[\s\S]{0,120}?"
        r"([\d\.]+)배[\s\S]{0,120}?([\d\.]+)배",
        text,
    )
    if not block:
        raise ValueError("Hanwha Life: CSM profitability block not found")

    # Deck order text: YoY totals; normalized to FY24.1Q / FY25.1Q so same x-axis as Samsung Life.
    q25_gen, q25_tot, q24_gen, q24_tot = [float(block.group(i)) for i in range(1, 5)]
    return {
        "label": "Hanwha Life",
        "source_pdf": "hanwha_life_2025_1q.pdf",
        "source_citation": "1Q25 IR slide 4, footnote 1) 신계약 CSM 수익성 = 신계약 CSM ÷ 월초",
        "series": {
            "total": {
                "label": "Total",
                "points": _points(["FY24.1Q", "FY25.1Q"], [q24_tot, q25_tot]),
            },
            "general_protection": {
                "label": "General protection",
                "points": _points(["FY24.1Q", "FY25.1Q"], [q24_gen, q25_gen]),
            },
        },
        "notes": "Only YoY comparison disclosed in 1Q25 deck; FY24.1Q/FY25.1Q aligns with Samsung Life axis.",
        "presentation": {"deck_period_labels": ["1Q24", "1Q25"]},
    }


def _nonlife_chart_periods(non_life: dict) -> list[str]:
    found: set[str] = set()
    for corp in non_life.values():
        if not isinstance(corp, dict):
            continue
        for ser in corp.get("series") or {}:
            for pt in corp["series"][ser].get("points") or []:
                if isinstance(pt, dict) and "period" in pt:
                    found.add(str(pt["period"]))
    ordered = [p for p in _NONLIFE_AXIS_ORDER if p in found]
    tail = sorted(p for p in found if p not in _NONLIFE_AXIS_ORDER)
    return ordered + tail


def _partial_disclosure_rows(non_life: dict) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    db = non_life.get("db_insurance") or {}
    sp_db = db.get("single_point") or {}
    pdf_db = db.get("source_pdf", "db_2025_results.pdf")
    rows.append(
        {
            "company": "DB Insurance",
            "disclosed_point": "2024 total → 2025 total (4Q avg)",
            "values": f"{sp_db.get('2024_total', '?')} → {sp_db.get('2025_total_via_4Q_avg', '?')}",
            "source": f"{pdf_db} p.4",
        },
    )
    rows.append(
        {
            "company": "DB Insurance",
            "disclosed_point": "Protection 2024 → 2025",
            "values": f"{sp_db.get('protection_2024', '?')} → {sp_db.get('protection_2025', '?')}",
            "source": "same",
        },
    )
    rows.append(
        {
            "company": "DB Insurance",
            "disclosed_point": "Savings 2024 → 2025",
            "values": f"{sp_db.get('savings_2024', '?')} → {sp_db.get('savings_2025', '?')}",
            "source": "same",
        },
    )

    kb = non_life.get("kb_insurance") or {}
    rows.append(
        {
            "company": "KB Insurance",
            "disclosed_point": "None at company level",
            "values": "—",
            "source": kb.get("source_pdf", "kbfg_2025_4q.pdf") + " (group-only)",
        },
    )

    sf = non_life.get("samsung_fire") or {}
    sp_sf = sf.get("single_point") or {}
    rows.append(
        {
            "company": "Samsung F&MI",
            "disclosed_point": "Total YTD 24.1-3Q → 25.1-3Q",
            "values": f"{sp_sf.get('ytd_2024_1_3Q_total', '')} → {sp_sf.get('ytd_2025_1_3Q_total', '')}",
            "source": "samsungfire_2025_3q.pdf (YTD supplemental)",
        },
    )
    return rows


def _augment_coverage_meta(payload: dict) -> None:
    """Attach chart axes, coverage counters, partial table payload to _meta."""

    non_life = payload["non_life"]
    life = payload["life"]

    nl_axis = _nonlife_chart_periods(non_life)
    life_axis = [str(p["period"]) for p in life["samsung_life"]["series"]["total"]["points"]]

    def _series_line_count(corps: dict) -> int:
        return sum(len((v.get("series") or {})) for v in corps.values() if isinstance(v, dict))

    partial_rows = _partial_disclosure_rows(non_life)

    cov: dict[str, object] = {
        "insurers_total": len(non_life) + len(life),
        "non_life_insurers": len(non_life),
        "life_insurers": len(life),
        "non_life_chart_line_series": _series_line_count(non_life),
        "life_chart_line_series": _series_line_count(life),
        "non_life_with_quarterly_lines": sum(
            1
            for v in non_life.values()
            if isinstance(v, dict) and any(len(s.get("points") or []) >= 3 for s in (v.get("series") or {}).values())
        ),
        "non_life_annual_snapshot_only": 1,
        "non_life_group_only_nb_ratio": 1,
        "partial_disclosure_rows": len(partial_rows),
        "distinct_periods_non_life_axis": len(nl_axis),
        "distinct_periods_life_axis": len(life_axis),
        "deck_source_files": list(SOURCE_TXT_USED),
        "coverage_summary_line": "",
    }

    cov["coverage_summary_line"] = (
        f"Universe {cov['non_life_insurers']} non-life + {cov['life_insurers']} life "
        f"({cov['insurers_total']} insurers). Charts: {cov['non_life_chart_line_series']} "
        f"non-life line series + {cov['life_chart_line_series']} life series. Non-life insurers "
        f"with ≥3 quarterly points disclosed: {cov['non_life_with_quarterly_lines']}/{cov['non_life_insurers']} "
        "(Samsung Fire: protection quarterly + total YTD; Hyundai M&F: 4 half/quarter anchors). "
        "See partial-disclosure rows for DB annual-only, KB group-only NB ratio, Samsung Fire total YTD."
    )

    m = payload["_meta"]
    m["extracted_at"] = "2026-05-25"
    m["notes"] = (
        "Quarterly NB CSM ratio coverage varies by company. "
        "`partial_disclosure` lists annual-only / undisclosed ratios; prototype loads `embed.js` for file-safe viewing."
    )
    m["chart_axes"] = {"non_life": nl_axis, "life": life_axis}
    m["coverage"] = cov
    m["partial_disclosure"] = partial_rows


def validate_plausible(payload: dict) -> None:
    """Build-time data-integrity gate on NB CSM multiples.

    Every chart series point must satisfy 0 < value <= MAX_PLAUSIBLE_MULTIPLE.
    A violation means an absolute CSM amount was misread as a ratio (or a sign
    error), so we fail the build loudly rather than ship a bogus 400x line.
    """
    bad: list[str] = []
    for section in ("life", "non_life"):
        for key, entry in (payload.get(section) or {}).items():
            if not isinstance(entry, dict):
                continue
            for sname, series in (entry.get("series") or {}).items():
                for pt in series.get("points") or []:
                    v = pt.get("value")
                    if v is None:
                        continue
                    if not (0 < float(v) <= MAX_PLAUSIBLE_MULTIPLE):
                        bad.append(f"{section}.{key}.{sname}.{pt.get('period')}={v}")
    if bad:
        raise ValueError(
            f"implausible NB CSM multiple(s) (expect 0 < x <= {MAX_PLAUSIBLE_MULTIPLE}); "
            "likely an absolute CSM amount misread as a ratio: " + "; ".join(bad)
        )


def build_payload() -> dict:
    payload: dict = {
        "_meta": {
            "definition": "NB CSM ratio = New-business CSM / Monthly-initial-premium (wol-nap wol-cho)",
            "source": "Company IR PDFs (artifacts/ir_research/)",
            "decision_ref": "TODO.md Decision #3 (2026-05-24)",
            "unit": "times (x)",
            "build_script": "scripts/viz_build_nb_csm_ratio.py",
            "embed_asset": "data/ir/nb_csm_ratio.embed.js",
            "artifacts_encoding": "Text extracts: UTF-8 preferred; KB deck falls back to cp949 in _read()",
            "prototype_html": "prototype_nb_csm_ratio.html",
            "extracted_at": "",
            "notes": "",
        },
        "non_life": {
            "samsung_fire": extract_samsung_fire(_read("samsungfire_2025_3q.txt")),
            "hyundai_marine": extract_hyundai_marine(_read("hyundai_mar_2025_1h.txt")),
            "db_insurance": extract_db_insurance(_read("db_2025_results.txt")),
            "kb_insurance": extract_kb_insurance(_read("kbfg_2025_4q.txt")),
        },
        "life": {
            "samsung_life": extract_samsung_life(_read("samsung_life_2025_1q.txt")),
            "hanwha_life": extract_hanwha_life(_read("hanwha_life_2025_1q.txt")),
        },
    }
    _augment_coverage_meta(payload)
    validate_plausible(payload)
    return payload


def write_json(payload: dict) -> None:
    text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(text, encoding="utf-8")
    embed = (
        "// Auto-built by scripts/viz_build_nb_csm_ratio.py\n"
        f"window.NB_CSM_RATIO_DATA = {json.dumps(payload, ensure_ascii=False)};\n"
    )
    OUT_EMBED_JS.write_text(embed, encoding="utf-8")
    TEMPLATES_OUT.parent.mkdir(parents=True, exist_ok=True)
    TEMPLATES_OUT.write_text(text, encoding="utf-8")
    TEMPLATES_EMBED_OUT.parent.mkdir(parents=True, exist_ok=True)
    TEMPLATES_EMBED_OUT.write_text(embed, encoding="utf-8")
    print(f"Wrote {OUT_PATH}")
    print(f"Wrote {OUT_EMBED_JS}")
    print(f"Wrote {TEMPLATES_OUT}")
    print(f"Wrote {TEMPLATES_EMBED_OUT}")


def main() -> int:
    try:
        payload = build_payload()
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    write_json(payload)
    sl = payload["life"]["samsung_life"]["series"]["total"]["points"]
    print("Samsung Life total:", ", ".join(f"{p['period']}={p['value']}x" for p in sl))
    cov = payload["_meta"].get("coverage") or {}
    print(
        "Coverage:",
        f"{cov.get('non_life_chart_line_series')} non-life series,",
        f"{cov.get('life_chart_line_series')} life series,",
        f"{cov.get('partial_disclosure_rows')} partial rows;",
        f"deck files {len(cov.get('deck_source_files') or [])}.",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
