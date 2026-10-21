# -*- coding: utf-8 -*-
import json, subprocess
from collections import Counter
for s in ["CSM워터폴", "손익분해PL", "신계약CSM배수"]:
    p = f"public_exports/{s}.json"
    old = json.loads(subprocess.check_output(["git", "show", f"HEAD:{p}"]).decode("utf-8"))
    new = json.load(open(p, encoding="utf-8"))
    ch = Counter(); cells = 0
    assert len(old) == len(new), (s, len(old), len(new))
    for a, b in zip(old, new):
        keys = set(a) | set(b)
        d = [k for k in keys if a.get(k) != b.get(k)]
        if d:
            cells += len(d); ch[b.get("원수사명")] += 1
        else:
            pass
        # row identity unchanged
        assert all(a.get(k) == b.get(k) for k in ("원수사명", "공시분기") if k in a)
    print(s, "rows", len(new), "changed rows by company", dict(ch), "changed cells", cells)
m_old = json.loads(subprocess.check_output(["git", "show", "HEAD:public_exports/manifest.json"]).decode("utf-8"))
m_new = json.load(open("public_exports/manifest.json", encoding="utf-8"))
for k in sorted(set(m_old) | set(m_new)):
    if m_old.get(k) != m_new.get(k): print("manifest diff:", k, m_old.get(k), "->", m_new.get(k))
