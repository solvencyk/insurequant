"""Summarize K-ICS validation RED findings with per-rule samples."""
from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

CODE = "\uc6d0\ubcf4\ud5d8\uc0ac\ucf54\ub4dc"
NAME = "\uc6d0\uc218\uc0ac\uba85"
QUARTER = "\uacf5\uc2dc\ubd84\uae30"


def norm(row: dict) -> dict:
    return {
        "rule": row.get("rule"),
        "code": row.get(CODE),
        "name": row.get(NAME),
        "quarter": row.get(QUARTER),
        "expected": row.get("expected"),
        "actual": row.get("actual"),
        "diff": row.get("diff"),
        "detail": row.get("detail") or "",
    }


def bucket(row: dict) -> str:
    detail = (row.get("detail") or "").lower()
    if "missing" in detail:
        return "missing_data"
    if row.get("expected") is None or row.get("actual") is None:
        return "missing_data"
    diff = row.get("diff")
    if diff is None:
        return "unknown"
    ad = abs(float(diff))
    if ad > 1000:
        return "large_numeric"
    if ad > 10:
        return "medium_numeric"
    return "small_numeric"


def summarize(report_path: Path) -> dict:
    data = json.loads(report_path.read_text(encoding="utf-8"))
    findings = data.get("findings") or data.get("results") or []
    reds = [r for r in findings if r.get("status") == "RED"]
    by_rule: dict[str, list[dict]] = defaultdict(list)
    for row in reds:
        by_rule[str(row.get("rule"))].append(norm(row))
    out = {"source": str(report_path), "total_red": len(reds), "by_rule": {}}
    for rule in sorted(by_rule, key=lambda r: (-len(by_rule[r]), r)):
        items = by_rule[rule]
        buckets = Counter(bucket(r) for r in items)
        picks: list[dict] = []
        seen: set[str] = set()
        for btype in ("missing_data", "large_numeric", "medium_numeric", "small_numeric"):
            ranked = sorted(items, key=lambda r: abs(float(r["diff"])) if r["diff"] is not None else 0.0, reverse=True)
            for row in ranked:
                if bucket(row) == btype and btype not in seen:
                    picks.append(row)
                    seen.add(btype)
                    break
        if not picks:
            picks = items[:2]
        out["by_rule"][rule] = {"count": len(items), "buckets": dict(buckets), "samples": picks[:3]}
    co_counts = Counter(r.get(CODE) for r in reds)
    out["top_companies"] = []
    for code, count in co_counts.most_common(12):
        nm = next(r.get(NAME) for r in reds if r.get(CODE) == code)
        rules = Counter(str(r.get("rule")) for r in reds if r.get(CODE) == code)
        out["top_companies"].append({"code": code, "name": nm, "red": count, "by_rule": dict(rules)})
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path, default=Path("artifacts/kics_validation/report_20260524T151923Z.json"))
    parser.add_argument("--out", type=Path, default=Path("artifacts/kics_validation/red_samples_311.json"))
    args = parser.parse_args()
    result = summarize(args.report)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
