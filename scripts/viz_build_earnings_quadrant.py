"""Build Earnings Quality Quadrant JSON for templates/index.html."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from viz_build_csm_waterfall import (
    deduplicate,
    detect_unit_scale,
    extract_stages,
    parse_num,
    pick_main_block,
)

SRC_DIR = ROOT / "data" / "ifrs17" / "extracted"
OUT_DIR = ROOT / "data" / "ifrs17" / "viz"
OUT_DIR.mkdir(parents=True, exist_ok=True)

ISR_LABELS = (
    "\ucd1d \ubcf4\ud5d8\uc11c\ube44\uc2a4\uacb0\uacfc",
    "\ubcf4\ud5d8\uc11c\ube44\uc2a4\uacb0\uacfc \ud569\uacc4",
    "\ucd1d \ubcf4\ud5d8\uc190\uc775",
    "\ubcf4\ud5d8\uc11c\ube44\uc2a4\uacb0\uacfc",
)
IFIE_LABELS = ("\ubcf4\ud5d8\uae08\uc735\uc190\uc775", "\ubcf4\ud5d8\uae08\uc735\uc190\uc775 \uc18c\uacc4")
INVEST_LABELS = ("\ud22c\uc790\uc218\uc775", "\uae08\uc735\uc218\uc775", "\ub2f9\uae30\uc190\uc775\uc778\uc2dd \uae08\uc735\uc190\uc775")


def _norm(s: str) -> str:
    return s.replace(" ", "").strip()


def _slice_rank(policy: str | None) -> int:
    if policy == "whole_company_life":
        return 3
    if policy == "long_term":
        return 2
    return 1


def _data_col_index(header: list[list[str]]) -> int:
    if not header:
        return 0
    top = header[0]
    for i, cell in enumerate(top):
        if isinstance(cell, str) and "\ud569\uacc4" in cell:
            return max(0, i - 1) if i > 0 else max(0, len(top) - 2)
    for i, cell in enumerate(top):
        if isinstance(cell, str) and _norm(cell) in ("\ub2f9\uae30", "\ub2f9\uae30\uae08\uc561"):
            return max(0, i - 1) if i > 0 else 0
    if len(top) > 2:
        return len(top) - 2
    return 0


def _row_value(row: list, col_idx: int, label: str = "") -> float | None:
    if not row or not isinstance(row[0], str):
        return None
    data = row[1:]
    stub = _norm(row[0])
    use_last = stub.startswith("\ucd1d") or stub in {_norm(l) for l in ISR_LABELS}
    if use_last:
        for cell in reversed(data):
            v = parse_num(cell)
            if v is not None:
                return v
    if col_idx < len(data):
        v = parse_num(data[col_idx])
        if v is not None:
            return v
    for cell in reversed(data):
        v = parse_num(cell)
        if v is not None:
            return v
    return None


def _find_row_value(blocks: list[dict], labels: tuple[str, ...]) -> float | None:
    best: tuple[int, float] | None = None
    for blk in blocks:
        rows = blk.get("rows") or []
        header = blk.get("header") or []
        col = _data_col_index(header)
        cap = blk.get("caption") or ""
        rank = _slice_rank(blk.get("slice_policy"))
        for row in rows:
            if not row or not isinstance(row[0], str):
                continue
            stub = _norm(row[0])
            if not any(_norm(l) in stub or stub == _norm(l) for l in labels):
                continue
            val = _row_value(row, col, labels[0])
            if val is None:
                continue
            score = rank * 10
            if "\ubcf4\ud5d8\uc11c\ube44\uc2a4\uacb0\uacfc" in cap or "\ubcf4\ud5d8\uc190\uc775" in cap:
                score += 8
            if any(l in cap for l in labels):
                score += 5
            if labels == ISR_LABELS and _norm(row[0]) == "\ubcf4\ud5d8\uc11c\ube44\uc2a4\uacb0\uacfc":
                score -= 3
            if blk.get("mvp_candidate"):
                score += 1
            if best is None or score > best[0]:
                best = (score, val)
    return best[1] if best else None


def _measurement_kpis(path: Path) -> dict:
    blocks = deduplicate(json.loads(path.read_text(encoding="utf-8")))
    main = pick_main_block(blocks)
    if main is None:
        return {"csm_amort_pl": None, "closing_total_csm": None}
    stages = extract_stages(main)
    unit_div = detect_unit_scale(blocks)
    if unit_div != 1.0:
        for s in stages.values():
            s["value_mn_krw"] = s["value_mn_krw"] / unit_div
    amort = stages.get("amortization", {}).get("value_mn_krw")
    closing = stages.get("closing", {}).get("value_mn_krw")
    return {
        "csm_amort_pl": abs(amort) if amort is not None else None,
        "closing_total_csm": closing,
    }


def _pl_kpis(company: str) -> dict:
    pl_path = next(SRC_DIR.glob(f"{company}_*_insurance_pl_mvp.json"), None)
    bs_path = next(SRC_DIR.glob(f"{company}_*_bs_snapshot_mvp.json"), None)
    blocks: list[dict] = []
    if pl_path:
        blocks.extend(deduplicate(json.loads(pl_path.read_text(encoding="utf-8"))))
    if bs_path:
        blocks.extend(deduplicate(json.loads(bs_path.read_text(encoding="utf-8"))))
    return {
        "insurance_service_result": _find_row_value(blocks, ISR_LABELS),
        "ifie_pl": _find_row_value(blocks, IFIE_LABELS),
        "investment_income": _find_row_value(blocks, INVEST_LABELS),
    }


def build_company(path: Path) -> dict:
    company = path.stem.split("_")[0]
    rcept = path.stem.split("_")[1] if len(path.stem.split("_")) >= 2 else ""
    m = _measurement_kpis(path)
    pl = _pl_kpis(company)

    amort = m.get("csm_amort_pl")
    closing = m.get("closing_total_csm")
    isr = pl.get("insurance_service_result")
    ifie = pl.get("ifie_pl")
    invest = pl.get("investment_income")

    runway = None
    if closing is not None and amort and amort > 0:
        runway = closing / amort

    denom_parts = []
    if isr is not None:
        denom_parts.append(abs(isr))
    if ifie is not None:
        denom_parts.append(abs(ifie))
    if invest is not None:
        denom_parts.append(abs(invest))
    earnings_base = sum(denom_parts) if denom_parts else None

    dependency = None
    if amort and amort > 0 and earnings_base and earnings_base > 0:
        dependency = amort / earnings_base

    missing = []
    if dependency is None:
        if not amort:
            missing.append("csm_amort_pl")
        if earnings_base is None or earnings_base <= 0:
            missing.append("earnings_base")
    if runway is None:
        if not closing:
            missing.append("closing_total_csm")
        if not amort:
            missing.append("csm_amort_pl")

    status = "ok"
    if dependency is None and runway is None:
        status = "missing"
    elif dependency is None or runway is None:
        status = "partial"

    return {
        "company": company,
        "rcept_no": rcept,
        "status": status,
        "csm_dependency": round(dependency, 4) if dependency is not None else None,
        "csm_runway_years": round(runway, 2) if runway is not None else None,
        "components": {
            "csm_amort_pl_mn": amort,
            "closing_total_csm_mn": closing,
            "insurance_service_result_mn": isr,
            "ifie_pl_mn": ifie,
            "investment_income_mn": invest,
            "earnings_base_mn": earnings_base,
        },
        "missing": missing,
    }


def main() -> None:
    files = sorted(SRC_DIR.glob("*_measurement_mvp.json"))
    results = []
    for f in files:
        try:
            results.append(build_company(f))
        except Exception as e:
            results.append({"company": f.stem.split("_")[0], "status": "error", "error": str(e)})

    both = [
        r
        for r in results
        if r.get("csm_dependency") is not None and r.get("csm_runway_years") is not None
    ]
    payload = {
        "unit": "million KRW (components); ratios dimensionless / years",
        "period": "annual (fiscal 2024 reporting)",
        "source": "IFRS17 A1 measurement_mvp + A3 insurance_pl_mvp",
        "formulas": {
            "csm_dependency": "abs(csm_amort_pl) / earnings_base",
            "csm_runway_years": "closing_total_csm / abs(csm_amort_pl)",
        },
        "coverage": {
            "total": len(results),
            "both_kpis": len(both),
            "partial_or_missing": len(results) - len(both),
        },
        "companies": results,
    }
    out = OUT_DIR / "earnings_quadrant.json"
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {out}")
    print(f"coverage: {len(both)}/{len(results)} companies with both KPIs")


if __name__ == "__main__":
    main()