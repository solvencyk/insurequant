"""Build consolidated IFRS17 dashboard panel JSON from extracted MVP files."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "data" / "ifrs17" / "extracted"
OUT = ROOT / "data" / "ifrs17" / "viz"

_FILENAME_RE = re.compile(r"^(.+?)_(\d{14})")
_YEAR_CELL_RE = re.compile(r"^(\d{1,2})\uB144$")


def parse_num(value: object, *, dash_means_zero: bool = True) -> float | None:
    """Parse Korean accounting-style numerics; commas and parentheses negatives."""
    if value is None:
        return None
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    if not isinstance(value, str):
        return None
    s = value.strip().replace(",", "").replace(" ", "").replace("\u00a0", "")
    if s == "":
        return None
    if s in ("-", "\u2014", "\uff0d"):
        return 0.0 if dash_means_zero else None
    neg = False
    if s.startswith("(") and s.endswith(")"):
        neg = True
        s = s[1:-1]
    try:
        v = float(s)
        return -v if neg else v
    except ValueError:
        return None


def pick_best_block(blocks: list[dict], prefer_kind: str | None = None) -> dict | None:
    if not blocks:
        return None
    return max(
        blocks,
        key=lambda b: (
            1 if prefer_kind and b.get("table_kind") == prefer_kind else 0,
            b.get("score", 0),
            len(b.get("rows") or []),
            b.get("line_no", 0),
        ),
    )


def header_has_year_buckets(header: list[list[str]]) -> bool:
    flat = " ".join(c for row in header for c in row if isinstance(c, str))
    keys = ("\u0031\uB144", "\u0032\uB144", "\u0035\uB144", "\uD569\uACC4")
    return any(k in flat for k in keys)


def _flatten_header(header: list[list[str]]) -> list[str]:
    out: list[str] = []
    for row in header:
        for c in row:
            if isinstance(c, str):
                out.append(c.strip())
    return out


def _align_row_to_flat_header(flat_hdr: list[str], row: list[object]) -> list[str]:
    cells = [("" if v is None else str(v)).strip() for v in row]
    L = len(flat_hdr)
    while len(cells) < L:
        cells.insert(0, "")
    if len(cells) > L:
        cells = cells[len(cells) - L :]
    return cells


def _bucket_indices(flat_hdr: list[str]) -> dict[str, list[int]]:
    singles: dict[int, int] = {}
    range_idxs: list[int] = []
    total_idx: int | None = None
    over30_idxs: list[int] = []

    for i, cell in enumerate(flat_hdr):
        t = cell.strip().replace(" ", "").replace("\u00a0", "")
        m = _YEAR_CELL_RE.fullmatch(t)
        if m:
            singles[int(m.group(1))] = i
            continue

        plain = cell.strip()
        if "\uD569\uACC4" in plain or plain == "\uACC4":
            total_idx = i
            continue

        if "~" in plain and "\uB144" in plain:
            range_idxs.append(i)

        if "\u0033\u0030" in t and "\uB144" in t and "\uCD08\uACFC" in t:
            over30_idxs.append(i)

    def pick_years(lo: int, hi: int) -> list[int]:
        out = [singles[y] for y in range(lo, hi + 1) if y in singles]
        out.sort()
        return out

    y5_plus: set[int] = set(pick_years(6, 10))
    y5_plus.update(range_idxs)
    y5_plus.update(over30_idxs)

    return {
        "y1": pick_years(1, 1),
        "y1_y3": pick_years(2, 3),
        "y3_y5": pick_years(4, 5),
        "y5_plus": sorted(y5_plus),
        "total": [total_idx] if total_idx is not None else [],
    }


def extract_amort_schedule(blocks: list[dict]) -> dict | None:
    kw = ("\uC0C1\uAC01", "\uC778\uC2DD", "\uC608\uC0C1", "\uAE30\uB300", "CSM")
    candidates = [
        b
        for b in blocks
        if header_has_year_buckets(b.get("header") or [])
        and any(k in str(b.get("caption") or "") for k in kw)
    ]
    blk = pick_best_block(candidates) or pick_best_block(blocks)
    if not blk:
        return None

    header = blk.get("header") or []
    flat_hdr = _flatten_header(header)
    buckets_map = _bucket_indices(flat_hdr)
    rows = blk.get("rows") or []

    total_row: list[str] | None = None
    hit_labels = (
        "\uB2F9\uAE30\uC190\uC775\uC778\uC2DD",
        "\uD569\uACC4",
        "\uC18C\uACC4",
    )
    for row in rows:
        if not row:
            continue
        stub = str(row[0]).strip()
        if any(k in stub for k in hit_labels) and len(row) >= 4:
            total_row = [str(v) for v in row]
            break

    if total_row is None:
        best: list[str] | None = None
        best_n = 0
        for row in rows:
            if not row:
                continue
            aligned_try = _align_row_to_flat_header(flat_hdr, row)
            nums = sum(1 for c in aligned_try[2:] if parse_num(c) is not None)
            if nums > best_n:
                best_n = nums
                best = aligned_try
        total_row = best

    if not total_row:
        return {"status": "no_rows", "caption": blk.get("caption")}

    aligned = (
        total_row if len(total_row) == len(flat_hdr) else _align_row_to_flat_header(flat_hdr, total_row)
    )

    bucket_vals: dict[str, float] = {}
    seen_bucket = False

    for bucket, idxs in buckets_map.items():
        if bucket == "total":
            continue
        usable = [i for i in idxs if 0 <= i < len(aligned)]
        if not usable:
            continue
        parts = []
        for i in usable:
            v = parse_num(aligned[i])
            if v is not None:
                parts.append(float(v))
        if not parts:
            continue
        bucket_vals[bucket] = sum(parts)
        seen_bucket = True

    tidx = (buckets_map.get("total") or [])
    if tidx:
        ti = tidx[0]
        if ti is not None and 0 <= ti < len(aligned):
            tv = parse_num(aligned[ti])
            if tv is not None:
                bucket_vals["total"] = float(tv)

    if not seen_bucket:
        numeric_tail = [float(v) for v in (parse_num(c) for c in aligned) if v is not None]
        if len(numeric_tail) >= 5:
            tail = numeric_tail[-5:]
            keys = ["y1", "y1_y3", "y3_y5", "y5_plus", "total"]
            bucket_vals = {k: tail[i] for i, k in enumerate(keys)}

    status = "ok" if bucket_vals else "partial"
    return {
        "status": status if bucket_vals else "partial",
        "caption": blk.get("caption"),
        "buckets": bucket_vals,
        "header": header,
        "row_label": aligned[0] if aligned else "",
    }


def extract_pl_breakdown(blocks: list[dict]) -> dict | None:
    kw_caption = (
        "\uBCF4\uD5D8\uC11C\uBE44\uC2A4",
        "\uBCF4\uD5D8\uC218\uC775",
        "\uBCF4\uD5D8\uC190\uC775",
    )
    candidates = [
        b
        for b in blocks
        if any(k in str(b.get("caption") or "") for k in kw_caption) or int(b.get("score", 0)) >= 6
    ]
    blk = pick_best_block(candidates) or pick_best_block(blocks)
    if not blk:
        return None

    rows_out: list[list[str]] = []
    for row in blk.get("rows") or []:
        if not row or not isinstance(row[0], str):
            continue
        label = row[0].strip()
        if not label:
            continue
        if label.startswith("\uACC4\uC57D"):
            continue
        if sum(1 for c in row[1:] if parse_num(c) is not None) == 0:
            continue
        rows_out.append([str(c).strip() for c in row])
        if len(rows_out) >= 12:
            break

    if not rows_out:
        return {"status": "no_rows", "caption": blk.get("caption")}

    return {
        "status": "ok",
        "caption": blk.get("caption"),
        "header": blk.get("header") or [],
        "table": rows_out,
    }


def extract_bs_snapshot(blocks: list[dict]) -> dict | None:
    kw = ("\uC790\uC0B0\uBD80\uCC44", "\uD604\uD669", "\uC0C1\uC138\uB0B4\uC5ED")
    candidates = [b for b in blocks if any(k in str(b.get("caption") or "") for k in kw)]
    blk = pick_best_block(candidates) or pick_best_block(blocks)
    if not blk:
        return None

    header = blk.get("header") or []
    hdr_flat = _flatten_header(header)
    rows_out: list[list[str]] = []

    for row in blk.get("rows") or []:
        if not row:
            continue
        aligned = _align_row_to_flat_header(hdr_flat, row) if hdr_flat else [str(v).strip() for v in row]
        rows_out.append(aligned)
        if len(rows_out) >= 80:
            break

    if not rows_out:
        return {"status": "no_rows", "caption": blk.get("caption")}

    return {
        "status": "ok",
        "caption": blk.get("caption"),
        "header": header,
        "table": rows_out,
    }


def _is_rollforward_sensitivity_caption(caption: str) -> bool:
    cap = caption or ""
    rollforward_cues = (
        "\uCE21\uC815\uC694\uC18C",
        "\uBCC0\uB3D9 \uC138\uBD80",
        "\uBCC0\uB3D9\uB0B4\uC5ED",
        "\uBBF8\uB798\uC11C\uBE44\uC2A4 \uAD00\uB828",
        "\uC0C1\uC138\uBCC0\uB3D9",
    )
    return any(k in cap for k in rollforward_cues)


def _sensitivity_caption_score(caption: str) -> int:
    cap = caption or ""
    score = 0
    if any(k in cap for k in ("\uBBFC\uAC10\uB3C4", "\uAC00\uC815\uBBFC\uAC10")):
        score += 10
    if "\uBBFC\uAC10\uB3C4\uBD84\uC11D" in cap:
        score += 5
    if any(k in cap for k in ("\uB2F9\uAE30", "\uAE30\uB9D0", "2024", "2023")):
        score += 1
    if _is_rollforward_sensitivity_caption(cap):
        score -= 20
    return score


def _header_has_product_lines(header: list[list[str]]) -> bool:
    flat = " ".join(c for row in header for c in row if isinstance(c, str))
    return "\uC0C1\uD488\uB77C\uC778" in flat or "\uC0C1\uD488 \uB77C\uC778" in flat


def _is_shock_label(text: str) -> bool:
    t = text.strip()
    if not t:
        return False
    return "%" in t or "\uC99D\uAC00" in t or "\uAC10\uC18C" in t or t.startswith("(-)")


def _is_risk_label(text: str, skip_stub: tuple[str, ...]) -> bool:
    t = text.strip()
    if not t or t in skip_stub:
        return False
    risk_cues = (
        "\uC704\uD5C8",
        "\uD574\uC57D",
        "\uD574\uC9C0",
        "\uC0AC\uB9DD",
        "\uC7A5\uD574",
        "\uC0AC\uC5C5\uBE44",
        "\uC190\uD574",
    )
    return any(k in t for k in risk_cues)


def _parse_sensitivity_deltas(row: list[object], *, product_line_layout: bool) -> tuple[float | None, float | None]:
    cells = [("" if v is None else str(v)).strip() for v in row]
    if product_line_layout and cells and cells[0] == "\uC21C\uC561":
        if len(cells) >= 6:
            return parse_num(cells[4], dash_means_zero=False), parse_num(cells[5], dash_means_zero=False)
        return None, None
    if len(cells) >= 6:
        return parse_num(cells[4], dash_means_zero=False), parse_num(cells[5], dash_means_zero=False)
    return None, None


def _pick_sensitivity_block(sens_blocks: list[dict]) -> dict | None:
    eligible = [b for b in sens_blocks if not _is_rollforward_sensitivity_caption(str(b.get("caption") or ""))]
    pool = eligible or sens_blocks
    return max(
        pool,
        key=lambda b: (
            _sensitivity_caption_score(str(b.get("caption") or "")),
            b.get("score", 0),
            len(b.get("rows") or []),
            -int(b.get("line_no") or 0),
        ),
    )


def extract_sensitivity(blocks: list[dict]) -> dict | None:
    sa_kind = "sensitivity_analysis"
    sens_blocks = [b for b in blocks if str(b.get("table_kind")) == sa_kind]
    if not sens_blocks:
        return {"status": "unavailable", "note": "No sensitivity_analysis block in MVP extract"}

    blk = _pick_sensitivity_block(sens_blocks)

    skip_stub = (
        "\uAE30\uC900\uAE08\uC561",
        "\uC18C\uACC4",
        "\uC21C\uC704",
        "\uC77C\uBC18 \uBCF4\uD5D8",
        "\uCD9C\uC7AC \uBCF4\uD5D8",
    )
    product_line_layout = _header_has_product_lines(blk.get("header") or [])

    scenarios: list[dict[str, object]] = []
    current_risk = ""
    current_shock = ""

    for row in blk.get("rows") or []:
        if not row:
            continue
        if not isinstance(row[0], str):
            continue

        label = row[0].strip()
        if not label or label in skip_stub:
            continue

        if product_line_layout:
            col1 = row[1].strip() if len(row) > 1 and isinstance(row[1], str) else ""
            if label == "\uC21C\uC561":
                csm_delta, pl_impact = _parse_sensitivity_deltas(row, product_line_layout=True)
                if (csm_delta is not None or pl_impact is not None) and current_risk:
                    scenarios.append(
                        {
                            "risk": current_risk,
                            "shock": current_shock,
                            "csm_delta": csm_delta,
                            "pl_impact": pl_impact,
                        },
                    )
                continue
            if _is_shock_label(label) and not _is_risk_label(label, skip_stub):
                current_shock = label
                continue
            if _is_risk_label(label, skip_stub) and _is_shock_label(col1):
                current_risk = label
                current_shock = col1
                continue
            continue

        if len(row) < 6:
            continue

        risk = label
        shock = row[1].strip() if len(row) > 1 and isinstance(row[1], str) else ""
        if shock in skip_stub:
            continue

        csm_delta, pl_impact = _parse_sensitivity_deltas(row, product_line_layout=False)
        if csm_delta is None and pl_impact is None:
            continue

        scenarios.append(
            {
                "risk": risk,
                "shock": shock,
                "csm_delta": csm_delta,
                "pl_impact": pl_impact,
            },
        )
        if len(scenarios) >= 12:
            break

    if not scenarios:
        return {
            "status": "partial",
            "caption": blk.get("caption"),
            "table_kind": sa_kind,
            "note": "sensitivity_analysis found but scenarios not parsed",
        }

    return {
        "status": "ok",
        "caption": blk.get("caption"),
        "table_kind": sa_kind,
        "header": blk.get("header") or [],
        "scenarios": scenarios,
    }


def build_panel(glob_pat: str, extractor) -> dict:
    companies: list[dict[str, object]] = []
    for path in sorted(SRC.glob(glob_pat)):
        m = _FILENAME_RE.match(path.stem)
        company = m.group(1) if m else path.stem
        rcept = m.group(2) if m else ""

        try:
            blocks_raw = json.loads(path.read_text(encoding="utf-8"))
            blocks: list = blocks_raw if isinstance(blocks_raw, list) else [blocks_raw]
            panel = extractor(blocks)
            if isinstance(panel, dict):
                companies.append({"company": company, "rcept_no": rcept, **panel})
            else:
                companies.append({"company": company, "rcept_no": rcept, "status": "empty"})
        except Exception as exc:  # noqa: BLE001
            companies.append(
                {"company": company, "rcept_no": rcept, "status": "error", "error": str(exc)},
            )

    return {"period": "annual (filings skim)", "companies": companies}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    outputs = {
        "csm_amort_schedule.json": ("*_csm.json", extract_amort_schedule),
        "insurance_pl_breakdown.json": ("*_insurance_pl_mvp.json", extract_pl_breakdown),
        "bs_snapshot.json": ("*_bs_snapshot_mvp.json", extract_bs_snapshot),
        "sensitivity_heatmap.json": ("*_sensitivity_mvp.json", extract_sensitivity),
    }

    for fname, (pat, fn) in outputs.items():
        payload = build_panel(pat, fn)
        out_path = OUT / fname
        out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

        ok_count = sum(1 for item in payload["companies"] if str(item.get("status")) == "ok")
        total_count = len(payload["companies"])

        rel = str(out_path.relative_to(ROOT)).replace("\\", "/")
        print("Wrote " + rel + " (" + str(ok_count) + "/" + str(total_count) + " ok)")


if __name__ == "__main__":
    main()