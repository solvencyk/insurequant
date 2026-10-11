#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Final integrity check of IFRS17_BS.json: unique keys, sort order, CRLF/indent format like HEAD, no BOM, and every added/changed cell has lineage (read-only)."""
import json, subprocess, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[1]
raw = (ROOT / "IFRS17_BS.json").read_bytes()
head = subprocess.run(["git", "show", "HEAD:IFRS17_BS.json"], cwd=ROOT, capture_output=True).stdout
print("BOM:", raw[:3] == b"\xef\xbb\xbf", "| CRLF count now/HEAD:", raw.count(b"\r\n"), head.count(b"\r\n"), "| LF-only lines now/HEAD:", raw.count(b"\n") - raw.count(b"\r\n"), head.count(b"\n") - head.count(b"\r\n"))
print("tail now:", raw[-12:], "HEAD:", head[-12:])
rows = json.loads(raw.decode("utf-8"))
keys = [(r["원보험사코드"], r["항목번호"], r["공시분기"]) for r in rows]
print("rows", len(rows), "unique keys", len(set(keys)))
hrows = json.loads(head.decode("utf-8"))
hk = [(r["원보험사코드"], r["항목번호"], r["공시분기"]) for r in hrows]
print("HEAD order sorted?", hk == sorted(hk), "| now order == sorted?", keys == sorted(keys), "| same relative order of pre-existing keys:", [k for k in keys if k in set(hk)] == hk)
fields = {tuple(sorted(r.keys())) for r in rows}
print("distinct field-sets:", len(fields))
side = json.loads((ROOT / "data/_derived/bs_from_disclosure.json").read_text(encoding="utf-8"))["cells"]
ov = json.loads((ROOT / "data/dart/viz/bs_manual_overrides.json").read_text(encoding="utf-8"))["cells"]
hs = set(hk)
new = [k for k in keys if k not in hs]
no_lineage = [k for k in new if f"{k[0]}|{k[1]}|{k[2]}" not in ov]
print("added keys", len(new), "| added keys without an overlay entry:", len(no_lineage), "| without a sidecar entry:", len([k for k in new if f"{k[0]}|{k[1]}|{k[2]}" not in side]))
