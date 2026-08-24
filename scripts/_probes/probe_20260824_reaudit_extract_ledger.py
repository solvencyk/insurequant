# -*- coding: utf-8 -*-
"""Read-only: dump the exemption ledger records for the re-audit buckets."""
import json, sys, io
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[2]
led = json.loads((ROOT / "data/_gold/kics_exemption_provenance.json").read_text(encoding="utf-8"))

TARGETS = {("KR0075", "2024.3Q"), ("KR0075", "2024.4Q"), ("KR0075", "2025.1Q"),
           ("KR0087", "2025.2Q"), ("KR0073", "2025.2Q")}

def walk(node, path=""):
    if isinstance(node, dict):
        c = node.get("company") or node.get("code")
        p = node.get("period") or node.get("quarter")
        if c and p and (c, p) in TARGETS:
            print("=" * 100)
            print("PATH:", path)
            print(json.dumps(node, ensure_ascii=False, indent=2))
        for k, v in node.items():
            walk(v, f"{path}.{k}")
    elif isinstance(node, list):
        for i, v in enumerate(node):
            walk(v, f"{path}[{i}]")

print("TOP KEYS:", list(led.keys()))
walk(led)
