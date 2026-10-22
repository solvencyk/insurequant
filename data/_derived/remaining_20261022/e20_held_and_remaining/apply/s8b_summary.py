#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""e20 step 8b: compact summary of s8_validate_reader.txt: per bucket which items differ master/orig, master/later, plus identity residuals"""
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
HERE = Path(__file__).resolve().parent
cur = None
out = []
buf = {}
for ln in (HERE / "s8_validate_reader.txt").read_text(encoding="utf-8").split("\n"):
    if ln.startswith("====="):
        if cur:
            out.append(cur)
        cur = {"head": ln, "units": "", "orig_ne": [], "later_ne": [], "fsapi_ne": [], "ids": []}
    elif cur is not None:
        if "orig:" in ln and "fmt=" in ln:
            m = re.findall(r"fmt=(\w+) unit=(\S+)", ln)
            cur["units"] = str(m)
        m = re.match(r"\s+i\s*(\d+) master=\s*(\S+)\s+orig=\s*(\S+)\s+later=\s*(\S+)\s+d\(later-master\)=\s*(\S+)\s+(.*)$", ln)
        if m:
            it = int(m.group(1))
            flags = m.group(6)
            if "master==orig N" in flags:
                cur["orig_ne"].append(it)
            if "master==later N" in flags:
                cur["later_ne"].append(it)
            fm = re.search(r"fsapi_prior_diff (\S+)", flags)
            if fm and abs(float(fm.group(1))) > 1.01:
                cur["fsapi_ne"].append((it, fm.group(1)))
        if "identities" in ln:
            cur["ids"].append(ln.strip())
out.append(cur)
for c in out:
    print(c["head"][:90], c["units"])
    print("    master!=orig :", c["orig_ne"], "| master!=later :", c["later_ne"], "| later vs FS-API prior |diff|>1:", c["fsapi_ne"])
    for i in c["ids"]:
        print("    ", i[:260])
