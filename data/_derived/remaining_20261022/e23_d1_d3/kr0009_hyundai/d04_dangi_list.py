# -*- coding: utf-8 -*-
"""read-only: the single-quarter (값_당분기) cells that changed in the 현대해상 load, grouped by quarter / kind"""
import json
import sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
BK = ROOT / "data/_derived/remaining_20261022/e23_d1_d3/backup_before_apply/kr0009_hyundai"
key = lambda r: (r["원보험사코드"], r["항목번호"], r["공시분기"])  # noqa: E731
h = {key(r): r for r in json.loads((BK / "PL_breakdown.json").read_text(encoding="utf-8"))}
l = {key(r): r for r in json.loads((ROOT / "PL_breakdown.json").read_text(encoding="utf-8"))}
val = [k for k in l if k[0] == "KR0009" and h[k]["값"] != l[k]["값"]]
dng = [k for k in l if k[0] == "KR0009" and h[k].get("값_당분기") != l[k].get("값_당분기")]
only = [k for k in dng if k not in set(val)]
print("값 changed", len(val), "| 값_당분기 changed", len(dng), "| dangi-only", len(only))
print("dangi-only by quarter:", dict(Counter(k[2] for k in only)), "items", sorted(k[1] for k in only))
print("dangi changed by quarter:", dict(Counter(k[2] for k in dng)))
blank = [k for k in dng if l[k].get("값_당분기") is None]
print("changed to blank:", sorted((k[2], k[1]) for k in blank))
filled = [k for k in dng if h[k].get("값_당분기") is None and l[k].get("값_당분기") is not None]
print("blank -> filled:", len(filled), dict(Counter(k[2] for k in filled)))
chg = [k for k in dng if h[k].get("값_당분기") is not None and l[k].get("값_당분기") is not None]
print("value -> value:", len(chg), dict(Counter(k[2] for k in chg)))
