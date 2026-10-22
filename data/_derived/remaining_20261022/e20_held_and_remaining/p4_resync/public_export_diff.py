# -*- coding: utf-8 -*-
import json, subprocess
from collections import Counter
for s in ["손익분해PL"]:
    p = f"public_exports/{s}.json"
    old = json.loads(subprocess.check_output(["git", "show", f"HEAD:{p}"]).decode("utf-8"))
    new = json.load(open(p, encoding="utf-8"))
    assert len(old) == len(new), (s, len(old), len(new))
    rows = Counter(); cols = Counter(); cells = 0; q = Counter()
    for a, b in zip(old, new):
        d = [k for k in set(a) | set(b) if a.get(k) != b.get(k)]
        if d:
            rows[b.get("원수사명")] += 1; q[b.get("공시분기")] += 1; cells += len(d)
            for k in d: cols[k] += 1
    print(s, "rows", len(new), "changed rows by company", dict(rows), "quarters", dict(q), "columns", dict(cols), "cells", cells)
m_old = json.loads(subprocess.check_output(["git", "show", "HEAD:public_exports/manifest.json"]).decode("utf-8"))
m_new = json.load(open("public_exports/manifest.json", encoding="utf-8"))
for k in sorted(set(m_old) | set(m_new)):
    if m_old.get(k) != m_new.get(k): print("manifest diff:", k, m_old.get(k), "->", m_new.get(k))
