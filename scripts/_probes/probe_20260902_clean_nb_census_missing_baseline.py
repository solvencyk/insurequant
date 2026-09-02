# -*- coding: utf-8 -*-
"""One-off: remove the 31 NB_CSM_multiple.json|NB_CENSUS_MISSING baseline entries that
validate_live_artifacts.py reported as BASELINE STALE after the 2026.2Q(202606) KIDI
premium ingest + NB_CSM_multiple.json rebuild (2026-09-02). Surgical edit — touches only
those 31 keys + their _counts line; every other artifact's baseline entries (including
kics_tier1/2_utilization, which belongs to the parallel kics-lane session) are untouched.

Preserves the file's existing CRLF line endings and no-BOM UTF-8 encoding.
"""
from __future__ import annotations
import json
from pathlib import Path

PATH = Path(__file__).resolve().parents[2] / "data" / "_gold" / "live_artifact_baseline.json"

STALE_KEYS = [
    "NB_CSM_multiple.json|NB_CENSUS_MISSING|KR0001|2026.2Q",
    "NB_CSM_multiple.json|NB_CENSUS_MISSING|KR0002|2026.2Q",
    "NB_CSM_multiple.json|NB_CENSUS_MISSING|KR0003|2026.2Q",
    "NB_CSM_multiple.json|NB_CENSUS_MISSING|KR0005|2026.2Q",
    "NB_CSM_multiple.json|NB_CENSUS_MISSING|KR0008|2026.2Q",
    "NB_CSM_multiple.json|NB_CENSUS_MISSING|KR0009|2026.2Q",
    "NB_CSM_multiple.json|NB_CENSUS_MISSING|KR0010|2026.2Q",
    "NB_CSM_multiple.json|NB_CENSUS_MISSING|KR0011|2026.2Q",
    "NB_CSM_multiple.json|NB_CENSUS_MISSING|KR0032|2026.2Q",
    "NB_CSM_multiple.json|NB_CENSUS_MISSING|KR0068|2026.2Q",
    "NB_CSM_multiple.json|NB_CENSUS_MISSING|KR0069|2026.2Q",
    "NB_CSM_multiple.json|NB_CENSUS_MISSING|KR0070|2026.2Q",
    "NB_CSM_multiple.json|NB_CENSUS_MISSING|KR0071|2026.2Q",
    "NB_CSM_multiple.json|NB_CENSUS_MISSING|KR0072|2026.2Q",
    "NB_CSM_multiple.json|NB_CENSUS_MISSING|KR0073|2026.2Q",
    "NB_CSM_multiple.json|NB_CENSUS_MISSING|KR0074|2023.4Q",
    "NB_CSM_multiple.json|NB_CENSUS_MISSING|KR0079|2026.2Q",
    "NB_CSM_multiple.json|NB_CENSUS_MISSING|KR0080|2023.4Q",
    "NB_CSM_multiple.json|NB_CENSUS_MISSING|KR0080|2024.4Q",
    "NB_CSM_multiple.json|NB_CENSUS_MISSING|KR0080|2025.4Q",
    "NB_CSM_multiple.json|NB_CENSUS_MISSING|KR0082|2026.2Q",
    "NB_CSM_multiple.json|NB_CENSUS_MISSING|KR0083|2026.2Q",
    "NB_CSM_multiple.json|NB_CENSUS_MISSING|KR0087|2026.2Q",
    "NB_CSM_multiple.json|NB_CENSUS_MISSING|KR0094|2026.2Q",
    "NB_CSM_multiple.json|NB_CENSUS_MISSING|KR0095|2023.4Q",
    "NB_CSM_multiple.json|NB_CENSUS_MISSING|KR0097|2023.4Q",
    "NB_CSM_multiple.json|NB_CENSUS_MISSING|KR0097|2025.4Q",
    "NB_CSM_multiple.json|NB_CENSUS_MISSING|KR0099|2026.2Q",
    "NB_CSM_multiple.json|NB_CENSUS_MISSING|KR0100|2023.4Q",
    "NB_CSM_multiple.json|NB_CENSUS_MISSING|KR0104|2026.2Q",
    "NB_CSM_multiple.json|NB_CENSUS_MISSING|KR1000|2026.2Q",
]


def main() -> int:
    raw = PATH.read_bytes()
    assert b"\r\n" in raw, "expected CRLF line endings in source file"
    data = json.loads(raw.decode("utf-8"))

    before = len(data["entries"])
    missing = [k for k in STALE_KEYS if k not in data["entries"]]
    if missing:
        raise SystemExit(f"ABORT: {len(missing)} expected keys not present: {missing}")
    if len(set(STALE_KEYS)) != len(STALE_KEYS):
        raise SystemExit("ABORT: duplicate keys in STALE_KEYS")

    for k in STALE_KEYS:
        del data["entries"][k]
    after = len(data["entries"])

    rule_key = "NB_CSM_multiple.json|NB_CENSUS_MISSING"
    if rule_key in data.get("_counts", {}):
        if data["_counts"][rule_key] != len(STALE_KEYS):
            raise SystemExit(
                f"ABORT: _counts[{rule_key}]={data['_counts'][rule_key]} != "
                f"{len(STALE_KEYS)} removed"
            )
        del data["_counts"][rule_key]

    text = json.dumps(data, ensure_ascii=False, indent=2)
    text = text.replace("\n", "\r\n") + "\r\n"
    PATH.write_bytes(text.encode("utf-8"))

    print(f"entries: {before} -> {after} (removed {before - after})")
    print(f"removed _counts[{rule_key!r}]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
