"""Compute Tier-2 (supplementary capital) recognition-limit utilization for K-ICS insurers."""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
MD_DIR = REPO / "md_inbox" / "FY2025_Q4"
JSON_PATH = REPO / "kics_disclosure.json"
DEFAULT_QUARTER = "2025.4Q"
DEFAULT_OUT_DIR = REPO / "output" / "tier2_utilization"

KEY_CODE = "\uc6d0\ubcf4\ud5d8\uc0ac\ucf54\ub4dc"
KEY_NAME = "\uc6d0\uc218\uc0ac\uba85"
KEY_ITEM = "\ud56d\ubaa9\ubc88\ud638"
KEY_Q = "\uacf5\uc2dc\ubd84\uae30"
KEY_VAL = "\uac12"

ROW_PATTERNS: dict[str, re.Pattern[str]] = {
    "tier2": re.compile(r"^\s*(\uBCF4\s*\uC644\s*\uC790\s*\uBCF8)\s*$"),
    "pre_limit": re.compile(
        r"^\s*(\uBCF4\s*\uC644\s*\uC790\s*\uBCF8\s*\uD55C\s*\uB3C4\s*\uC801\s*\uC6A9\s*\uC804)\s*$"
    ),
    "limit": re.compile(r"^\s*(\uBCF4\s*\uC644\s*\uC790\s*\uBCF8\s*\uD55C\s*\uB3C4)\s*$"),
    "lapse_excess": re.compile(
        r"^\s*(\uD574\s*\uC57D\s*\uD658\s*\uAE09\s*\uAE08\s*\uBD80\s*\uC871\s*\uBD84).*"
    ),
    # Allow either label-wrapping parens "(\uAE30\uBC1C\uD589 \uC2E0\uC885\uC790\uBCF8\uC99D\uAD8C)" or trailing
    # "\uAE30\uBC1C\uD589 \uC2E0\uC885\uC790\uBCF8\uC99D\uAD8C ( )" cosmetic empty-paren markers seen in some MD outputs.
    "hybrid": re.compile(
        r"^\s*\(?\s*\uAE30\s*\uBC1C\s*\uD589\s*\uC2E0\s*\uC885\s*\uC790\s*\uBCF8\s*\uC99D\s*\uAD8C\s*(?:\(\s*\)|\))?\s*$"
    ),
    "subordinated": re.compile(
        r"^\s*\(?\s*\uAE30\s*\uBC1C\s*\uD589\s*\uD6C4\s*\uC21C\s*\uC704\s*\uCC44\s*\uBB34\s*(?:\(\s*\)|\))?\s*$"
    ),
    "scr": re.compile(r"^\s*(\uC9C0\s*\uAE09\s*\uC5EC\s*\uB825\s*\uAE30\s*\uC900\s*\uAE08\s*\uC561)\s*$"),
}

NA_TOKENS = frozenset(
    {
        "-",
        "\u2014",
        "\u2212",
        "\u25a1",
        "\u25a0",
        "n/a",
        "na",
        "",
    }
)

# Million-KRW tolerance for pre_limit vs tier2 reconciliation (avoid double-subtract).
_NUM_TOL_ABS_M = 100.0
_NUM_TOL_REL = 0.02


@dataclass
class TableValues:
    tier2: float | None = None
    pre_limit: float | None = None
    limit: float | None = None
    lapse_excess: float | None = None
    hybrid: float | None = None
    subordinated: float | None = None
    hybrid_post: float | None = None
    subordinated_post: float | None = None
    scr: float | None = None
    raw: dict[str, list[str]] = field(default_factory=dict)


@dataclass
class UtilizationResult:
    company: str
    code: str
    quarter: str
    tier2_limit_eok: float | None
    numerator_eok: float | None
    utilization_pct: float | None
    data_source: str
    tier2_eok: float | None = None
    pre_limit_eok: float | None = None
    lapse_excess_eok: float | None = None
    hybrid_eok: float | None = None
    subordinated_eok: float | None = None
    proxy_utilization_pct: float | None = None
    quality_flag: str = "ok"


def _normalize_label(text: str) -> str:
    return re.sub(r"\s+", "", text.strip())


def _parse_amount(token: str | None) -> float | None:
    if token is None:
        return None
    raw = token.strip()
    if not raw:
        return None
    if re.fullmatch(r"\uD574\uB2F9.*", raw):
        return None
    if raw in NA_TOKENS:
        return 0.0
    neg = False
    if raw.startswith("(") and raw.endswith(")"):
        neg = True
        raw = raw[1:-1].strip()
    if raw.startswith("\u25b3") or raw.startswith("\u0394"):
        neg = True
        raw = raw[1:].strip()
    raw = raw.replace(",", "").replace(" ", "")
    if raw in NA_TOKENS:
        return 0.0
    multi = re.findall(r"-?\d+(?:\.\d+)?", raw)
    if len(multi) > 1:
        raw = multi[-1]
    try:
        val = float(raw)
    except ValueError:
        return None
    return -val if neg else val


def _split_md_row(line: str) -> list[str]:
    body = line.strip()
    if not body.startswith("|"):
        return []
    return [cell.strip() for cell in body.strip("|").split("|")]


def _match_row_key(label: str) -> str | None:
    norm = _normalize_label(label)
    for key, pattern in ROW_PATTERNS.items():
        if pattern.match(norm) or pattern.match(label.strip()):
            return key
    return None


def _pick_column(values: list[str | None]) -> float | None:
    """Pick the last numeric cell — represents post-transition (경과조치 적용 후)."""
    parsed = [_parse_amount(v) for v in values]
    numeric_indices = [i for i, v in enumerate(parsed) if v is not None]
    if not numeric_indices:
        return None
    return parsed[numeric_indices[-1]]


def _pick_grandfathered_column(values: list[str | None]) -> float | None:
    """Pick the first numeric cell — for 기발행 자본증권 rows, the 경과조치
    적용 전 column carries the face / exempted amount (post column is often 0
    or empty after phase-out). PDF [그림 3] footnote 2 explicitly asks for the
    2022-까지-발행 amount, not the post-transition residual."""
    parsed = [_parse_amount(v) for v in values]
    numeric_indices = [i for i, v in enumerate(parsed) if v is not None]
    if not numeric_indices:
        return None
    return parsed[numeric_indices[0]]


def _parse_table_block(lines: list[str]) -> TableValues | None:
    tv = TableValues()
    for line in lines:
        cells = _split_md_row(line)
        if len(cells) < 2:
            continue
        key = _match_row_key(cells[0])
        if key is None:
            continue
        data_cells = cells[1:]
        tv.raw[key] = data_cells
        if key in ("hybrid", "subordinated"):
            setattr(tv, key, _pick_grandfathered_column(data_cells))
            setattr(tv, f"{key}_post", _pick_column(data_cells))
        else:
            setattr(tv, key, _pick_column(data_cells))
    if tv.limit is None and tv.pre_limit is None and tv.tier2 is None:
        return None
    return tv


def _score_table(tv: TableValues) -> int:
    score = 0
    if tv.limit is not None and tv.limit > 0:
        score += 10
    if tv.pre_limit is not None:
        score += 5
    if tv.tier2 is not None and tv.tier2 > 0:
        score += 2
    if tv.lapse_excess is not None:
        score += 1
    return score


def _extract_common_table(text: str) -> TableValues | None:
    norm_text = text.replace("\r\n", "\n")
    lines = norm_text.split("\n")
    blocks: list[list[str]] = []
    current: list[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("<!--") and current:
            continue
        if stripped.startswith("|"):
            current.append(line)
        else:
            if current:
                blocks.append(current)
                current = []
    if current:
        blocks.append(current)

    merged: list[list[str]] = []
    for block in blocks:
        if not merged:
            merged.append(block)
            continue
        prev = merged[-1]
        prev_tv = _parse_table_block(prev)
        cur_tv = _parse_table_block(block)
        if prev_tv and cur_tv and prev_tv.limit is None and cur_tv.limit is not None:
            merged[-1] = prev + block
        elif prev_tv and cur_tv and prev_tv.pre_limit is not None and cur_tv.pre_limit is None and cur_tv.limit is not None:
            merged[-1] = prev + block
        else:
            merged.append(block)
    blocks = merged

    best: TableValues | None = None
    best_score = -1
    for block in blocks:
        has_limit_row = False
        for row in block:
            cells = _split_md_row(row)
            if cells and "\uD55C\uB3C4" in _normalize_label(cells[0]):
                has_limit_row = True
                break
        if not has_limit_row:
            continue
        tv = _parse_table_block(block)
        if tv is None:
            continue
        score = _score_table(tv)
        if score > best_score:
            best_score = score
            best = tv
    return best


def _million_to_eok(v: float | None) -> float | None:
    if v is None:
        return None
    return round(v / 100.0, 2)


def _approx_equal(a: float, b: float) -> bool:
    return abs(a - b) <= max(_NUM_TOL_ABS_M, _NUM_TOL_REL * max(abs(a), abs(b), 1.0))


def _exemption_parts(tv: TableValues, *, lapse_netted: bool = False) -> tuple[float, float, float]:
    lapse = tv.lapse_excess or 0.0
    if lapse_netted:
        hybrid = tv.hybrid_post if tv.hybrid_post is not None else (tv.hybrid or 0.0)
        sub = tv.subordinated_post if tv.subordinated_post is not None else (tv.subordinated or 0.0)
    else:
        hybrid = tv.hybrid or 0.0
        sub = tv.subordinated or 0.0
    return lapse, hybrid, sub


def _compute_numerator(tv: TableValues) -> tuple[float | None, str]:
    """Numerator per PDF [그림 3] footnote 2:
        (경과조치 후 보완자본) − 해약환급금부족분상당액 중 해약환급금준비금초과분
                                − 2022년까지 발행한 자본성증권 (기발행 신종/후순위)

    Insurers disagree on whether `보완자본 한도 적용 전` is gross (≈ tier2) or
    already nets lapse / hybrid / subordinated. Reconcile against tier2 before
    subtracting so we never double-count exemptions.
    """
    pre = tv.pre_limit
    tier2 = tv.tier2

    if pre is not None and tier2 is not None:
        if _approx_equal(pre, tier2):
            lapse, hybrid, sub = _exemption_parts(tv, lapse_netted=False)
            return pre - lapse - hybrid - sub, "pre_limit_gross_minus_exemptions"
        if _approx_equal(pre, tier2 - (tv.lapse_excess or 0.0)):
            lapse, hybrid, sub = _exemption_parts(tv, lapse_netted=True)
            net = pre - hybrid - sub
            if net < 0:
                return pre, "pre_limit_lapse_netted"
            return net, "pre_limit_minus_hybrid_sub"
        lapse, hybrid, sub = _exemption_parts(tv, lapse_netted=False)
        expected = tier2 - lapse - hybrid - sub
        if _approx_equal(pre, expected):
            return max(0.0, pre), "pre_limit_already_netted"
        if pre >= 0 and pre < tier2 * 0.25:
            return pre, "pre_limit_residual"

    lapse, hybrid, sub = _exemption_parts(tv, lapse_netted=False)
    if pre is not None:
        net = pre - lapse - hybrid - sub
        if net < 0 and pre > 0:
            return pre, "pre_limit_only"
        return net, "pre_limit_minus_exemptions"

    if tier2 is not None:
        return tier2 - lapse - hybrid - sub, "tier2_minus_exemptions"

    return None, "missing"


def _compute_proxy_numerator(
    proxy: dict[str, float],
    tv: TableValues | None,
) -> tuple[float | None, str]:
    """JSON fallback: item3 (보완자본) minus exemptions when MD table has them."""
    item3 = proxy.get("item3")
    if item3 is None:
        return None, "missing"
    base = item3 * 100.0  # 억원 → 백만원
    if tv is None:
        return base, "proxy_item3_gross"
    if tv.pre_limit is not None and tv.tier2 is not None:
        if not _approx_equal(tv.pre_limit, tv.tier2):
            if _approx_equal(tv.pre_limit, tv.tier2 - (tv.lapse_excess or 0.0)) or (
                tv.pre_limit >= 0 and tv.pre_limit < tv.tier2 * 0.25
            ):
                return tv.pre_limit, "proxy_pre_limit"
    lapse, hybrid, sub = _exemption_parts(tv, lapse_netted=False)
    if lapse or hybrid or sub:
        net = base - lapse - hybrid - sub
        if net >= 0:
            return net, "proxy_item3_minus_exemptions"
        return max(0.0, base - lapse), "proxy_item3_minus_lapse"
    return base, "proxy_item3_gross"


def _load_json_proxy(quarter: str) -> dict[str, dict[str, float]]:
    data = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    out: dict[str, dict[str, float]] = {}
    for row in data:
        if row.get(KEY_Q) != quarter:
            continue
        code = row[KEY_CODE]
        item = row[KEY_ITEM]
        if item not in (3, 14):
            continue
        val = _parse_amount(str(row.get(KEY_VAL, "")))
        if val is None:
            continue
        out.setdefault(code, {})[f"item{item}"] = val
        if KEY_NAME in row:
            out[code]["name"] = row[KEY_NAME]
    return out


def _parse_company_from_filename(path: Path) -> tuple[str, str]:
    code, _, name = path.stem.partition("_")
    return code, name


def compute_one(
    md_path: Path,
    quarter: str,
    proxy: dict[str, float] | None,
) -> UtilizationResult:
    code, company = _parse_company_from_filename(md_path)
    tv = _extract_common_table(md_path.read_text(encoding="utf-8"))

    proxy_item3 = proxy.get("item3") if proxy else None
    proxy_item14 = proxy.get("item14") if proxy else None
    proxy_limit = proxy_item14 * 0.5 if proxy_item14 is not None else None
    proxy_num_m, proxy_num_method = (
        _compute_proxy_numerator(proxy, tv) if proxy else (None, "missing")
    )
    proxy_util = (
        proxy_num_m / (proxy_limit * 100.0) * 100.0
        if proxy_num_m is not None and proxy_limit and proxy_limit > 0
        else (
            proxy_item3 / proxy_limit * 100.0
            if proxy_item3 is not None and proxy_limit and proxy_limit > 0
            else None
        )
    )

    if tv is None:
        if proxy_util is not None:
            num_eok = round(proxy_num_m / 100.0, 2) if proxy_num_m is not None else (
                round(proxy_item3, 2) if proxy_item3 is not None else None
            )
            flag = "no_table"
            if proxy_util < 0:
                flag = "util_negative"
            elif proxy_util > 100:
                flag = "util_over_100"
            return UtilizationResult(
                company=company,
                code=code,
                quarter=quarter,
                tier2_limit_eok=round(proxy_limit, 2) if proxy_limit else None,
                numerator_eok=num_eok,
                utilization_pct=round(proxy_util, 2),
                data_source="proxy",
                tier2_eok=round(proxy_item3, 2) if proxy_item3 is not None else None,
                proxy_utilization_pct=round(proxy_util, 2),
                quality_flag=flag,
            )
        return UtilizationResult(
            company=company,
            code=code,
            quarter=quarter,
            tier2_limit_eok=None,
            numerator_eok=None,
            utilization_pct=None,
            data_source="missing",
            quality_flag="missing",
        )

    limit_m = tv.limit
    if limit_m is None and tv.scr is not None:
        limit_m = tv.scr * 0.5
    if limit_m is None and proxy_limit is not None:
        limit_m = proxy_limit * 100.0

    numerator_m, num_method = _compute_numerator(tv)
    util = (
        numerator_m / limit_m * 100.0
        if numerator_m is not None and limit_m and limit_m > 0
        else None
    )

    result = UtilizationResult(
        company=company,
        code=code,
        quarter=quarter,
        tier2_limit_eok=_million_to_eok(limit_m),
        numerator_eok=_million_to_eok(numerator_m),
        utilization_pct=round(util, 2) if util is not None else None,
        data_source="table",
        tier2_eok=_million_to_eok(tv.tier2),
        pre_limit_eok=_million_to_eok(tv.pre_limit),
        lapse_excess_eok=_million_to_eok(tv.lapse_excess),
        hybrid_eok=_million_to_eok(tv.hybrid),
        subordinated_eok=_million_to_eok(tv.subordinated),
        proxy_utilization_pct=round(proxy_util, 2) if proxy_util is not None else None,
    )

    if util is None:
        if proxy_util is not None:
            result.utilization_pct = round(proxy_util, 2)
            result.numerator_eok = (
                round(proxy_num_m / 100.0, 2) if proxy_num_m is not None else (
                    round(proxy_item3, 2) if proxy_item3 is not None else None
                )
            )
            result.tier2_limit_eok = round(proxy_limit, 2) if proxy_limit else result.tier2_limit_eok
            result.data_source = "proxy"
            result.quality_flag = "table_incomplete"
        else:
            result.data_source = "missing"
            result.quality_flag = "missing"
    else:
        if util < 0:
            result.quality_flag = "util_negative"
        elif util > 100:
            result.quality_flag = "util_over_100"
        elif proxy_util is not None and abs(util - proxy_util) > max(5.0, 0.05 * proxy_util):
            result.quality_flag = "table_proxy_diverge"
        elif num_method != "pre_limit_gross_minus_exemptions":
            result.quality_flag = num_method

    return result


_OUTLIER_INTERPRETATIONS: dict[str, str] = {
    "util_over_100": "Numerator exceeds SCRx50% limit — may reflect pre-clamp disclosure or proxy without exemption rows.",
    "util_negative": "Negative numerator after reconciliation — check MD table row semantics.",
    "no_table": "No 5-2-2 transitional table in MD; proxy uses gross item3/item14.",
    "missing": "No MD table and no JSON proxy items 3/14.",
    "table_incomplete": "Table missing limit or numerator rows; fell back to proxy.",
}


def _interpret_outlier(r: UtilizationResult) -> str:
    if r.quality_flag in _OUTLIER_INTERPRETATIONS:
        return _OUTLIER_INTERPRETATIONS[r.quality_flag]
    if r.data_source == "proxy":
        return "Proxy-only (image-only MD or missing transitional table); gross tier2/item14 ratio."
    if r.quality_flag == "table_proxy_diverge":
        return "Table formula differs from gross item3 proxy — table uses PDF numerator logic."
    return f"quality_flag={r.quality_flag}"


def write_outlier_report(results: list[UtilizationResult], quarter: str, out_dir: Path) -> Path:
    """Write markdown report of utilization outliers (<0, >100, null)."""
    import statistics

    stem = quarter.replace(".", "")
    path = out_dir / f"outlier_report_{stem}.md"
    in_range = [r for r in results if r.utilization_pct is not None and 0 <= r.utilization_pct <= 100]
    outliers = [r for r in results if r.utilization_pct is None or r.utilization_pct < 0 or r.utilization_pct > 100]
    missing = [r for r in results if r.utilization_pct is None]

    lines = [
        f"# Tier-2 utilization outlier report ({quarter})",
        "",
        "## Summary",
        "",
        "| Metric | Count |",
        "|--------|------:|",
        f"| Total companies | {len(results)} |",
        f"| In range 0-100% | {len(in_range)} |",
        f"| Outliers (<0, >100, null) | {len(outliers)} |",
        f"| Missing (null) | {len(missing)} |",
        "",
    ]
    if in_range:
        vals = sorted(r.utilization_pct for r in in_range)
        med = statistics.median(vals)
        lines += [
            f"Valid 0-100% distribution: min={vals[0]:.2f}%, median={med:.2f}%, max={vals[-1]:.2f}%",
            "",
        ]

    spot_codes = (
        ("KR0068", "Hanwha Life", 73.07),
        ("KR0008", "Samsung Fire", -169.59),
        ("KR0001", "Meritz Fire", -321.70),
    )
    spot_notes = {
        "KR0068": "Unchanged (gross pre_limit)",
        "KR0008": "pre_limit already netted lapse",
        "KR0001": "post-transition residual pre_limit",
    }
    lines += [
        "## Spot-check (formula fix before/after)",
        "",
        "| Code | Company | Before | After | Notes |",
        "|------|---------|-------:|------:|-------|",
    ]
    by_code = {r.code: r for r in results}
    for code, label, before in spot_codes:
        r = by_code.get(code)
        after_s = f"{r.utilization_pct:.2f}%" if r and r.utilization_pct is not None else "null"
        lines.append(
            f"| {code} | {label} | {before:.2f}% | {after_s} | {spot_notes.get(code, '')} |"
        )
    lines += ["", "## Outliers", ""]
    if not outliers:
        lines.append("None.")
    else:
        for r in sorted(outliers, key=lambda x: (x.utilization_pct is None, -(x.utilization_pct or -999))):
            util_s = "null" if r.utilization_pct is None else f"{r.utilization_pct:.2f}%"
            lines += [
                f"### {r.code} {r.company}",
                "",
                f"- **utilization_pct**: {util_s}",
                f"- **numerator_eok**: {r.numerator_eok}",
                f"- **tier2_limit_eok**: {r.tier2_limit_eok}",
                f"- **data_source**: {r.data_source}",
                f"- **quality_flag**: {r.quality_flag}",
                f"- **lapse_excess_eok**: {r.lapse_excess_eok}",
                f"- **hybrid_eok**: {r.hybrid_eok}",
                f"- **subordinated_eok**: {r.subordinated_eok}",
                f"- **tier2_eok / pre_limit_eok**: {r.tier2_eok} / {r.pre_limit_eok}",
                f"- **proxy_utilization_pct**: {r.proxy_utilization_pct}",
                f"- **Interpretation**: {_interpret_outlier(r)}",
                "",
            ]

    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def run(quarter: str, md_dir: Path, out_dir: Path) -> list[UtilizationResult]:
    out_dir.mkdir(parents=True, exist_ok=True)
    proxy_by_code = _load_json_proxy(quarter)
    results = [
        compute_one(md_path, quarter, proxy_by_code.get(_parse_company_from_filename(md_path)[0]))
        for md_path in sorted(md_dir.glob("*.md"))
    ]
    ranked = sorted(results, key=lambda r: (r.utilization_pct is None, -(r.utilization_pct or -1)))

    stem = f"tier2_utilization_{quarter.replace('.', '')}"
    json_path = out_dir / f"{stem}.json"
    csv_path = out_dir / f"{stem}.csv"
    json_path.write_text(
        json.dumps({"quarter": quarter, "count": len(ranked), "results": [asdict(r) for r in ranked]}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    if ranked:
        with csv_path.open("w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(asdict(ranked[0]).keys()))
            writer.writeheader()
            writer.writerows(asdict(r) for r in ranked)
    write_outlier_report(ranked, quarter, out_dir)
    return ranked


def _print_summary(results: list[UtilizationResult]) -> None:
    valid = [r for r in results if r.utilization_pct is not None]
    print(f"\nTotal companies: {len(results)} | Computed: {len(valid)}")
    if not valid:
        return
    print("\nTop 5 (highest utilization):")
    for r in valid[:5]:
        print(f"  {r.code} {r.company}: {r.utilization_pct:.2f}% (limit={r.tier2_limit_eok}, num={r.numerator_eok}, src={r.data_source})")
    print("\nBottom 5 (lowest utilization):")
    for r in valid[-5:]:
        print(f"  {r.code} {r.company}: {r.utilization_pct:.2f}% (limit={r.tier2_limit_eok}, num={r.numerator_eok}, src={r.data_source})")
    for code in ("KR0068", "KR0008", "KR0001"):
        hit = next((r for r in results if r.code == code), None)
        if hit:
            print(
                f"\nSpot-check {code} {hit.company}: util={hit.utilization_pct}% "
                f"limit={hit.tier2_limit_eok} num={hit.numerator_eok} tier2={hit.tier2_eok} "
                f"pre={hit.pre_limit_eok} lapse={hit.lapse_excess_eok} hybrid={hit.hybrid_eok} "
                f"sub={hit.subordinated_eok} src={hit.data_source} flag={hit.quality_flag} proxy={hit.proxy_utilization_pct}"
            )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Compute Tier-2 limit utilization")
    parser.add_argument("--quarter", default=DEFAULT_QUARTER)
    parser.add_argument("--md-dir", type=Path, default=MD_DIR)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    args = parser.parse_args(argv)
    if not args.md_dir.is_dir():
        print(f"MD directory not found: {args.md_dir}", file=sys.stderr)
        return 1
    if not JSON_PATH.is_file():
        print(f"JSON not found: {JSON_PATH}", file=sys.stderr)
        return 1
    results = run(args.quarter, args.md_dir, args.out_dir)
    _print_summary(results)
    print(f"\nWrote: {args.out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
