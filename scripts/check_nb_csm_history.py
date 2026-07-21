#!/usr/bin/env python3
"""NB CSM time-series cross-source check: DART CSM waterfall vs IR factsheets.

Compares, per (company, quarter), the new-business CSM derived two ways:
  - DART side: data/dart/viz/csm_waterfall_history.json `new_business` stage
    (million KRW -> 억원), YTD -> per-Q delta (Q1 of each year = raw, no prior to subtract).
  - IR side:   data/ir/series/<KR>_*.json, convention-aware per company:
       * has `nb_csm_singleQ_eok`            -> use it directly (single-quarter).
       * units.nb_csm_eok contains "YTD"     -> ytd_delta (subtract prior quarter).
       * else                                -> per-quarter value as disclosed.
Flag: OK (<=5% or <=100억), MINOR (<=10%), OVER (dart>ir), UNDER (dart<ir).

Conventions are DERIVED from each series' own metadata (no external table), so the
tool is self-contained. Rebuilt 2026-06-16 after the file went missing (was ad-hoc);
faithful to the persisted data/_derived/nb_csm_history_check.json schema.

Off-by-one provenance: a 2026-06-01 history rebuild shifted quarter<->year by one
year; the current series carry correct YTD-reset-at-Q1 alignment (삼성화재 witness).
"""
from __future__ import annotations

import glob
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DART_PATH = ROOT / "data" / "dart" / "viz" / "csm_waterfall_history.json"
SERIES_DIR = ROOT / "data" / "ir" / "series"
OUT_PATH = ROOT / "data" / "_derived" / "nb_csm_history_check.json"

REL_OK_PCT = 5.0
REL_MINOR_PCT = 10.0
ABS_TOL_EOK = 100.0


def _is_q1(period: str) -> bool:
    return period.endswith(".1Q")


def _num(v):
    return float(v) if isinstance(v, (int, float)) and not isinstance(v, bool) else None


def dart_per_q(dart: dict, periods: list[str]) -> dict[str, dict[str, float | None]]:
    """new_business stage (mn KRW) -> 억원, YTD -> per-Q delta (Q1 raw)."""
    out: dict[str, dict[str, float | None]] = {}
    for entry in dart.get("companies", []):
        co = entry.get("company")
        pers = entry.get("periods", {})
        ytd: dict[str, float | None] = {}
        for p in periods:
            nb = (pers.get(p, {}).get("stages", {}) or {}).get("new_business", {})
            v = _num(nb.get("value_mn_krw"))
            ytd[p] = v / 100.0 if v is not None else None  # mn KRW -> 억원
        perq: dict[str, float | None] = {}
        for i, p in enumerate(periods):
            if ytd[p] is None:
                perq[p] = None
            elif _is_q1(p):
                perq[p] = ytd[p]
            else:
                prev = ytd.get(periods[i - 1])
                perq[p] = (ytd[p] - prev) if prev is not None else None
        out[co] = perq
    return out


def _series_convention(meta: dict) -> str:
    units = (meta.get("units") or {}).get("nb_csm_eok", "") or ""
    return "ytd_delta" if "YTD" in units else "per_q_delta"


def ir_per_q(series: dict, periods: list[str]) -> tuple[dict[str, float | None], str]:
    ser = series.get("series", {})
    conv = _series_convention(series)
    has_single = any(
        isinstance(r, dict) and r.get("nb_csm_singleQ_eok") is not None for r in ser.values()
    )
    if has_single:
        conv = "singleQ"
    out: dict[str, float | None] = {}
    for i, p in enumerate(periods):
        rec = ser.get(p)
        if not isinstance(rec, dict):
            out[p] = None
            continue
        if conv == "singleQ":
            out[p] = _num(rec.get("nb_csm_singleQ_eok"))
        elif conv == "ytd_delta" and not _is_q1(p):
            cur = _num(rec.get("nb_csm_eok"))
            prev = ser.get(periods[i - 1], {})
            pv = _num(prev.get("nb_csm_eok")) if isinstance(prev, dict) else None
            out[p] = (cur - pv) if (cur is not None and pv is not None) else cur
        else:
            out[p] = _num(rec.get("nb_csm_eok"))
    return out, conv


def _flag(d: float | None, ir: float | None) -> str:
    if d is None or ir is None:
        return "MISSING"
    ad = abs(d - ir)
    rel = (ad / abs(ir) * 100.0) if ir else float("inf")
    if ad <= ABS_TOL_EOK or rel <= REL_OK_PCT:
        return "OK"
    if rel <= REL_MINOR_PCT:
        return "MINOR"
    return "OVER" if d > ir else "UNDER"


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    dart = json.loads(DART_PATH.read_text(encoding="utf-8"))
    periods = dart["periods"]
    dnb = dart_per_q(dart, periods)

    matrix: dict[str, dict] = {}
    skipped: dict[str, str] = {}
    flags = ("OK", "MINOR", "OVER", "UNDER", "MISSING")
    per_company = {}
    per_quarter = {p: {f: 0 for f in flags} for p in periods}

    for path in sorted(SERIES_DIR.glob("*.json")):
        s = json.loads(path.read_text(encoding="utf-8"))
        co = s.get("company")
        ser = s.get("series", {})
        if not ser:
            skipped[co or path.stem] = "empty IR series"
            continue
        if not any(isinstance(r, dict) and r.get("nb_csm_eok") is not None for r in ser.values()):
            skipped[co or path.stem] = "no nb_csm_eok values (incompatible schema?)"
            continue
        irq, conv = ir_per_q(s, periods)
        rows = []
        counts = {f: 0 for f in flags}
        for p in periods:
            d, ir = dnb.get(co, {}).get(p), irq.get(p)
            fl = _flag(d, ir)
            counts[fl] += 1
            per_quarter[p][fl] += 1
            rows.append({
                "period": p,
                "dart_eok": round(d, 2) if d is not None else None,
                "ir_eok": round(ir, 2) if ir is not None else None,
                "abs_diff_eok": round(abs(d - ir), 2) if (d is not None and ir is not None) else None,
                "rel_diff": round(abs(d - ir) / abs(ir), 4) if (d is not None and ir) else None,
                "flag": fl,
            })
        matrix[co] = {"kr": s.get("kr"), "sector": s.get("sector"),
                      "ir_convention": conv, "rows": rows}
        per_company[co] = counts

    report = {
        "_meta": {
            "cohort_size": len(matrix),
            "skipped": skipped,
            "periods": periods,
            "tolerance": {"rel_ok_pct": REL_OK_PCT, "rel_minor_pct": REL_MINOR_PCT, "abs_tol_eok": ABS_TOL_EOK},
            "per_quarter_flag_counts": per_quarter,
            "per_company_flag_counts": per_company,
            "notes": "DART side: csm_waterfall_history.json NB stage YTD->per-Q delta. "
                     "IR side: convention-aware (singleQ field / YTD units / per-Q default). "
                     "Q1 of each year uses raw value (no prior YTD to subtract).",
        },
        "matrix": matrix,
    }
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    over_under = sum(c["OVER"] + c["UNDER"] for c in per_company.values())
    print(f"NB CSM history check -> {OUT_PATH}")
    print(f"cohort={len(matrix)} skipped={list(skipped)} OVER+UNDER={over_under}")
    for co, c in per_company.items():
        tag = " <-- flags" if (c["OVER"] or c["UNDER"]) else ""
        print(f"  {co}: OK={c['OK']} MINOR={c['MINOR']} OVER={c['OVER']} UNDER={c['UNDER']} MISSING={c['MISSING']}{tag}")
    return 2 if over_under else 0


if __name__ == "__main__":
    raise SystemExit(main())
