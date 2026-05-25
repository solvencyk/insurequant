"""Compute Tier-1 (basic capital) hybrid recognition-limit utilization for K-ICS insurers.

Definition (KIRI nre2024-14_2 pp. 12-13, 22):
- 신종자본증권 (hybrid perpetual) Tier-1 recognition limit:
    base = SCR (총요구자본) × 10%
    conditional-bump = SCR × 15%   # if the >10% portion is 조건부자본증권
    legacy (pre-K-ICS 기발행) common transition: SCR × 15%
  Excess above the limit is reclassified to 보완자본 (Tier-2) — appears as
  공시 항목 Ⅴ.1 "기본자본 자본증권의 인정한도를 초과한 금액".

Numerator: hybrid recognized in Tier-1.
Denominator: SCR × 15% (default reporting line — covers legacy + conditional).
            SCR × 10% also reported as `utilization_pct_strict` for the
            base-rule view.

Sources used per company:
  1. K-ICS MD `5-1) B/S상의 자기자본` table  -> 신종자본증권 issued (book equity, 억원)
  2. K-ICS MD detail Tier-2 sub-items section -> Ⅴ.1 excess (백만원)
  3. K-ICS MD 5-2-2(1) 공통적용 경과조치 table -> (기발행 신종자본증권) row (백만원)
  4. kics_disclosure.json item 14            -> SCR 지급여력기준금액 (억원)

Output:
  output/tier1_utilization/tier1_utilization_<quarter>.json + .csv

Run:
  python scripts/compute_tier1_utilization.py --quarter 2025.4Q
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
MD_DIR = REPO / "md_inbox" / "FY2025_Q4"
JSON_PATH = REPO / "kics_disclosure.json"
DEFAULT_QUARTER = "2025.4Q"
DEFAULT_OUT_DIR = REPO / "output" / "tier1_utilization"

KEY_CODE = "원보험사코드"
KEY_NAME = "원수사명"
KEY_ITEM = "항목번호"
KEY_Q = "공시분기"
KEY_VAL = "값"

NA_TOKENS = frozenset(
    {
        "-",
        "—",
        "−",
        "□",
        "■",
        "n/a",
        "na",
        "",
    }
)

LIMIT_RATIO_PRIMARY = 0.15  # KIRI common-transition / conditional-bump cap
LIMIT_RATIO_STRICT = 0.10   # KIRI base rule (non-conditional new issuance)


# ---------------------------------------------------------------------------
# Number parsing helpers
# ---------------------------------------------------------------------------

def _parse_amount(token: str | None) -> float | None:
    if token is None:
        return None
    raw = token.strip()
    if not raw:
        return None
    if raw in NA_TOKENS:
        return 0.0
    neg = False
    if raw.startswith("(") and raw.endswith(")"):
        neg = True
        raw = raw[1:-1].strip()
    raw = raw.replace(",", "").replace(" ", "")
    if raw in NA_TOKENS:
        return 0.0
    # Korean negative markers
    if raw.startswith("△") or raw.startswith("Δ") or raw.startswith("(-)"):
        neg = True
        raw = raw.lstrip("△Δ").removeprefix("(-)")
    multi = re.findall(r"-?\d+(?:\.\d+)?", raw)
    if not multi:
        return None
    val = float(multi[-1] if len(multi) > 1 else multi[0])
    return -val if neg else val


def _split_md_row(line: str) -> list[str]:
    body = line.strip()
    if not body.startswith("|"):
        return []
    return [cell.strip() for cell in body.strip("|").split("|")]


def _normalize_label(text: str) -> str:
    return re.sub(r"\s+", "", text.strip())


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class MdExtract:
    hybrid_issued_eok: float | None = None           # BS row 신종자본증권 (latest Q, 억원)
    hybrid_issued_source: str = "missing"            # bs_normal | bs_transposed | bs_split_chars | missing
    hybrid_excess_eok: float | None = None           # Ⅴ.1 row (백만원→억원)
    hybrid_excess_source: str = "missing"            # detail_v1 | transition_row | missing
    legacy_hybrid_transition_eok: float | None = None  # (기발행 신종자본증권) row 5-2-2(1), 억원
    bs_raw_cell: str | None = None                   # raw "신종자본증권" cell text (for audit)


@dataclass
class UtilizationResult:
    company: str
    code: str
    quarter: str
    scr_eok: float | None
    tier1_hybrid_limit_eok: float | None        # SCR × 15%
    tier1_hybrid_limit_strict_eok: float | None  # SCR × 10%
    tier1_hybrid_issued_eok: float | None
    tier1_hybrid_excess_eok: float | None
    tier1_hybrid_recognized_eok: float | None
    utilization_pct: float | None
    utilization_pct_strict: float | None
    data_source: str
    quality_flag: str = "ok"
    issued_source: str = "missing"
    excess_source: str = "missing"
    legacy_hybrid_transition_eok: float | None = None


# ---------------------------------------------------------------------------
# Section 5-1 BS row 신종자본증권 (3 layouts observed)
# ---------------------------------------------------------------------------

def _extract_bs_hybrid_normal(lines: list[str]) -> tuple[float | None, str | None]:
    """Standard layout: leftmost cell = label, following cells = values.

    Example: | 신종자본증권 | 8,650 | 8,650 | - |
    Returns (latest_q_value_eok, raw_cell_text).
    """
    pat = re.compile(r"^\s*신\s*종\s*자\s*본\s*증\s*권\s*$")
    for line in lines:
        cells = _split_md_row(line)
        if len(cells) < 2:
            continue
        first = _normalize_label(cells[0])
        if first != "신종자본증권":
            continue
        for val in cells[1:]:
            v = _parse_amount(val)
            if v is not None:
                return v, " | ".join(cells)
        return 0.0, " | ".join(cells)
    return None, None


def _extract_bs_hybrid_transposed(lines: list[str]) -> tuple[float | None, str | None]:
    """Transposed layout where the label appears INSIDE the rightmost cell.

    Hanwha Life style: | 30,685 | 30,685 | 신종자본증권 30,685 |
    The first cell is the current-quarter value.
    """
    for line in lines:
        cells = _split_md_row(line)
        if len(cells) < 2:
            continue
        # The 신종자본증권 label embedded somewhere in the row
        text = " ".join(cells)
        if "신종자본증권" not in text and "신종 자본증권" not in text:
            continue
        # Skip rows that already match the normal layout (handled above)
        if _normalize_label(cells[0]) == "신종자본증권":
            continue
        # First numeric cell is the latest-quarter amount
        for val in cells:
            v = _parse_amount(val)
            if v is not None:
                return v, " | ".join(cells)
        return 0.0, " | ".join(cells)
    return None, None


def _extract_bs_hybrid_split_chars(lines: list[str]) -> tuple[float | None, str | None]:
    """Shinhan Life style: | 신 | 종 | 자 본 | 증 권 | - | - | 2,995 |.

    The label is split across leading cells. Reconstruct by joining all
    non-numeric prefix cells and matching '신종자본증권'.
    """
    for line in lines:
        cells = _split_md_row(line)
        if len(cells) < 3:
            continue
        # Find boundary between text-only prefix and first numeric cell
        prefix_chars: list[str] = []
        first_num_idx: int | None = None
        for i, c in enumerate(cells):
            v = _parse_amount(c)
            if v is None and not c.strip():
                continue
            if v is None:
                prefix_chars.append(c)
                continue
            first_num_idx = i
            break
        if first_num_idx is None:
            continue
        joined = _normalize_label("".join(prefix_chars))
        if joined != "신종자본증권":
            continue
        for val in cells[first_num_idx:]:
            v = _parse_amount(val)
            if v is not None:
                return v, " | ".join(cells)
    return None, None


# ---------------------------------------------------------------------------
# Tier-2 sub-items: row "1. 기본자본 자본증권의 인정한도를 초과한 (금)액"
# ---------------------------------------------------------------------------

EXCESS_LABEL_RE = re.compile(r"기본자본자본증권의인정한도를?초과한?금?액")
UNIT_RE = re.compile(r"단위\s*[:：]?\s*(억원|백만원|천원|원)")


def _detect_unit_scale(lines: list[str], target_idx: int) -> tuple[float, str]:
    """Walk backwards from target_idx, find nearest '(단위: X)' marker.

    Returns (multiplier_to_eok, unit_label). Default = 백만원 (× 0.01).
    """
    for i in range(target_idx - 1, max(target_idx - 80, -1), -1):
        m = UNIT_RE.search(lines[i].replace(" ", ""))
        if m:
            unit = m.group(1)
            if unit == "억원":
                return 1.0, unit
            if unit == "백만원":
                return 0.01, unit
            if unit == "천원":
                return 1e-5, unit
            if unit == "원":
                return 1e-8, unit
    return 0.01, "백만원(default)"


def _extract_excess_v1(lines: list[str]) -> tuple[float | None, str | None, str]:
    """Row Ⅴ.1 in the detailed Tier-2 breakdown table.

    Example: | 1. 기본자본 자본증권의 인정한도를 초과한금액 | - |
    Returns (amount_in_eok, raw_cell_text, unit_label).

    Rejects the bundled row "Ⅲ. 보완자본으로 재분류하는 항목 (... 등)" which
    aggregates the hybrid excess with other reclassified items. Detects
    unit (억원/백만원/천원) from the nearest "(단위: ...)" marker above the row.
    """
    for idx, line in enumerate(lines):
        cells = _split_md_row(line)
        if len(cells) < 2:
            continue
        norm = _normalize_label(cells[0])
        if not EXCESS_LABEL_RE.search(norm):
            continue
        # Skip gross bucket
        if "보완자본으로재분류" in norm or norm.endswith("등)") or norm.endswith("등"):
            continue
        scale, unit_label = _detect_unit_scale(lines, idx)
        for val in cells[1:]:
            v = _parse_amount(val)
            if v is not None:
                return v * scale, " | ".join(cells), unit_label
        return 0.0, " | ".join(cells), unit_label
    return None, None, ""


# ---------------------------------------------------------------------------
# 5-2-2(1) row "(기발행 신종자본증권)"
# ---------------------------------------------------------------------------

LEGACY_HYBRID_RE = re.compile(r"^\(?기발행\s*신종자본증권\)?\s*\(\s*\)?$|^\(?기발행\s*신종자본증권\)?$")


def _extract_legacy_hybrid_transition(lines: list[str]) -> float | None:
    """5-2-2(1) row '(기발행 신종자본증권)'.

    Layout: | 구분 | 경과조치 적용 전 | 경과조치 적용 후 |
    The "전" value is the amount that, before transition, was reclassified
    from Tier-1 to Tier-2; common-transition restores it to Tier-1.
    Return the "적용 전" value (백만원).
    """
    for line in lines:
        cells = _split_md_row(line)
        if len(cells) < 2:
            continue
        norm = _normalize_label(cells[0])
        if not (norm.startswith("(기발행신종자본증권)") or norm == "(기발행신종자본증권)" or norm == "기발행신종자본증권"):
            continue
        for val in cells[1:]:
            v = _parse_amount(val)
            if v is not None:
                return v
        return 0.0
    return None


# ---------------------------------------------------------------------------
# Per-file orchestrator
# ---------------------------------------------------------------------------

def parse_md(md_path: Path) -> MdExtract:
    text = md_path.read_text(encoding="utf-8")
    lines = text.replace("\r\n", "\n").split("\n")
    extract = MdExtract()

    val, cell = _extract_bs_hybrid_normal(lines)
    if val is not None:
        extract.hybrid_issued_eok = val
        extract.hybrid_issued_source = "bs_normal"
        extract.bs_raw_cell = cell
    if extract.hybrid_issued_eok is None:
        val, cell = _extract_bs_hybrid_transposed(lines)
        if val is not None:
            extract.hybrid_issued_eok = val
            extract.hybrid_issued_source = "bs_transposed"
            extract.bs_raw_cell = cell
    if extract.hybrid_issued_eok is None:
        val, cell = _extract_bs_hybrid_split_chars(lines)
        if val is not None:
            extract.hybrid_issued_eok = val
            extract.hybrid_issued_source = "bs_split_chars"
            extract.bs_raw_cell = cell

    excess_eok, _, unit_label = _extract_excess_v1(lines)
    if excess_eok is not None:
        extract.hybrid_excess_eok = round(excess_eok, 2)
        extract.hybrid_excess_source = f"detail_v1[{unit_label}]"

    # Informational only: the (기발행 신종자본증권) row in 5-2-2(1) is the
    # legacy hybrid amount restored to Tier-1 under common transition,
    # NOT the Tier-2 excess. Reported as a separate field for reference.
    legacy_million = _extract_legacy_hybrid_transition(lines)
    if legacy_million is not None:
        extract.legacy_hybrid_transition_eok = round(legacy_million / 100.0, 2)

    return extract


# ---------------------------------------------------------------------------
# JSON SCR lookup
# ---------------------------------------------------------------------------

def load_scr_by_code(quarter: str) -> dict[str, dict[str, object]]:
    data = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    out: dict[str, dict[str, object]] = {}
    for row in data:
        if row.get(KEY_Q) != quarter:
            continue
        if row.get(KEY_ITEM) != 14:
            continue
        code = row.get(KEY_CODE)
        val = _parse_amount(str(row.get(KEY_VAL, "")))
        if code and val is not None:
            out[code] = {"scr_eok": val, "name": row.get(KEY_NAME, "")}
    return out


# ---------------------------------------------------------------------------
# Per-company computation
# ---------------------------------------------------------------------------

def _parse_company_from_filename(path: Path) -> tuple[str, str]:
    code, _, name = path.stem.partition("_")
    return code, name


def compute_one(md_path: Path, quarter: str, scr_info: dict[str, object] | None) -> UtilizationResult:
    code, company = _parse_company_from_filename(md_path)
    md = parse_md(md_path)
    scr = float(scr_info["scr_eok"]) if scr_info and scr_info.get("scr_eok") is not None else None

    limit = round(scr * LIMIT_RATIO_PRIMARY, 2) if scr is not None else None
    limit_strict = round(scr * LIMIT_RATIO_STRICT, 2) if scr is not None else None

    issued = md.hybrid_issued_eok
    excess = md.hybrid_excess_eok
    recognized: float | None = None
    if issued is not None:
        excess_val = excess if excess is not None else 0.0
        recognized = max(issued - excess_val, 0.0)

    util = None
    util_strict = None
    if recognized is not None and limit and limit > 0:
        util = round(recognized / limit * 100.0, 2)
    if recognized is not None and limit_strict and limit_strict > 0:
        util_strict = round(recognized / limit_strict * 100.0, 2)

    if issued is None and scr is None:
        data_source = "missing"
        quality = "missing"
    elif issued is None:
        data_source = "scr_only"
        quality = "no_bs_hybrid_row"
    elif scr is None:
        data_source = "bs_only"
        quality = "no_scr"
    else:
        data_source = "md+json"
        quality = "ok"

    # Quality nuance: issued > formula limit but disclosed excess is zero
    if (
        issued is not None
        and limit is not None
        and excess is not None
        and excess == 0.0
        and issued > limit
    ):
        quality = "issued_above_15pct_but_no_disclosed_excess"
    # Quality nuance: Ⅴ.1 detail row not extracted from MD; excess assumed 0
    if issued is not None and issued > 0 and excess is None:
        quality = "excess_unknown_assumed_zero"

    return UtilizationResult(
        company=company,
        code=code,
        quarter=quarter,
        scr_eok=round(scr, 2) if scr is not None else None,
        tier1_hybrid_limit_eok=limit,
        tier1_hybrid_limit_strict_eok=limit_strict,
        tier1_hybrid_issued_eok=round(issued, 2) if issued is not None else None,
        tier1_hybrid_excess_eok=round(excess, 2) if excess is not None else None,
        tier1_hybrid_recognized_eok=round(recognized, 2) if recognized is not None else None,
        utilization_pct=util,
        utilization_pct_strict=util_strict,
        data_source=data_source,
        quality_flag=quality,
        issued_source=md.hybrid_issued_source,
        excess_source=md.hybrid_excess_source,
        legacy_hybrid_transition_eok=md.legacy_hybrid_transition_eok,
    )


def run(quarter: str, md_dir: Path, out_dir: Path) -> list[UtilizationResult]:
    out_dir.mkdir(parents=True, exist_ok=True)
    scr_by_code = load_scr_by_code(quarter)
    results = [
        compute_one(md_path, quarter, scr_by_code.get(_parse_company_from_filename(md_path)[0]))
        for md_path in sorted(md_dir.glob("*.md"))
    ]
    ranked = sorted(results, key=lambda r: (r.utilization_pct is None, -(r.utilization_pct or -1)))

    stem = f"tier1_utilization_{quarter.replace('.', '')}"
    json_path = out_dir / f"{stem}.json"
    csv_path = out_dir / f"{stem}.csv"
    json_path.write_text(
        json.dumps(
            {
                "quarter": quarter,
                "count": len(ranked),
                "definition": {
                    "limit_primary": "SCR × 15%  (KIRI 2024-14 p.22 common-transition / p.12 conditional-bump)",
                    "limit_strict": "SCR × 10%  (KIRI 2024-14 p.12 base, non-conditional new issuance)",
                    "numerator": "BS 신종자본증권 issued − Ⅴ.1 excess reclassified",
                    "scr_source": "kics_disclosure.json item14 (지급여력기준금액)",
                    "source_pdf": "artifacts/kiri_study/nre2024-14_2.pdf",
                },
                "results": [asdict(r) for r in ranked],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    if ranked:
        with csv_path.open("w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(asdict(ranked[0]).keys()))
            writer.writeheader()
            writer.writerows(asdict(r) for r in ranked)
    return ranked


def _print_summary(results: list[UtilizationResult]) -> None:
    valid = [r for r in results if r.utilization_pct is not None]
    print(f"\nTotal companies: {len(results)} | Computed: {len(valid)}")
    print("\nTop 5 utilization (15% limit):")
    for r in valid[:5]:
        print(
            f"  {r.code} {r.company}: util15={r.utilization_pct}% (issued={r.tier1_hybrid_issued_eok}, "
            f"excess={r.tier1_hybrid_excess_eok}, recog={r.tier1_hybrid_recognized_eok}, "
            f"limit15={r.tier1_hybrid_limit_eok}, scr={r.scr_eok}, flag={r.quality_flag})"
        )
    print("\nBottom 5 (valid only):")
    for r in valid[-5:]:
        print(
            f"  {r.code} {r.company}: util15={r.utilization_pct}% (issued={r.tier1_hybrid_issued_eok}, "
            f"recog={r.tier1_hybrid_recognized_eok}, limit15={r.tier1_hybrid_limit_eok})"
        )
    missing = [r for r in results if r.utilization_pct is None]
    if missing:
        print(f"\nMissing/incomplete ({len(missing)}):")
        for r in missing:
            print(f"  {r.code} {r.company}: src={r.data_source}, flag={r.quality_flag}, "
                  f"issued_src={r.issued_source}, scr={r.scr_eok}")
    flagged = [r for r in results if r.quality_flag == "issued_above_15pct_but_no_disclosed_excess"]
    if flagged:
        print(f"\nFlag - issued above 15% but disclosed excess is zero ({len(flagged)}):")
        for r in flagged:
            print(f"  {r.code} {r.company}: issued={r.tier1_hybrid_issued_eok}, "
                  f"limit15={r.tier1_hybrid_limit_eok}, excess_disclosed={r.tier1_hybrid_excess_eok}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Compute Tier-1 hybrid limit utilization")
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
