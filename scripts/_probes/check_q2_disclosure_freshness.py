#!/usr/bin/env python3
"""One-off probe: compare FY2026_Q2 nonlife disclosure downloads against the
existing FY2026_Q1 files (same KR code) to catch a 'latest-row' XPath that
silently re-resolved to the still-current 1Q file instead of a genuine 2Q
posting. Read-only; writes nothing.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
Q1_DIR = ROOT / "data" / "disclosure" / "FY2026_Q1" / "raw"  # canonical layout (pdf/ is a stale pre-reorg leftover)
Q2_DIR = ROOT / "data" / "disclosure" / "FY2026_Q2" / "pdf"
MANIFEST = ROOT / "data" / "disclosure" / "_meta" / "FY2026_Q2" / "manifest.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    q1_by_kr = {}
    for p in Q1_DIR.glob("*"):
        kr = p.name.split("_", 1)[0]
        q1_by_kr[kr] = p

    print(f"{'KR':<12} {'status':<6} {'verdict':<18} detail")
    for r in manifest["results"]:
        kr = r["kr"]
        if r["status"] != "ok":
            print(f"{kr:<12} {'FAIL':<6} {'honest_gap':<18} {r.get('error','')}")
            continue
        q2_path = ROOT / r["path"]
        q2_hash = sha256(q2_path)
        q1_path = q1_by_kr.get(kr)
        if q1_path is None:
            print(f"{kr:<12} {'OK':<6} {'new_no_q1_baseline':<18} {q2_path.name} ({r['bytes']:,}B)")
            continue
        q1_hash = sha256(q1_path)
        if q1_hash == q2_hash:
            print(f"{kr:<12} {'OK*':<6} {'STALE_DUPLICATE':<18} identical to {q1_path.name} -- NOT a real 2Q file")
        else:
            print(f"{kr:<12} {'OK':<6} {'genuine_new_2Q':<18} {q2_path.name} ({r['bytes']:,}B, differs from Q1)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
