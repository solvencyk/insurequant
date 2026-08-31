# -*- coding: utf-8 -*-
"""KR0097 2024.4Q / KR0071 2024.4Q item47-52 가 과거 커밋에 있었는지."""
import json, subprocess, sys
from pathlib import Path
ROOT = Path(r"C:/Users/sangwook.cho/Desktop/insurequant")
def cells(blob, code, q):
    try: recs = json.loads(blob)
    except Exception as e: return f"(parse fail {e})"
    if isinstance(recs, dict): recs = recs.get("records") or recs.get("data") or []
    out = {}
    for r in recs:
        if r.get("원보험사코드")==code and r.get("공시분기")==q:
            try: it=int(r.get("항목번호"))
            except: continue
            if 47<=it<=54: out[it]=(r.get("값"), r.get("값_적용후"))
    return {k:out[k] for k in sorted(out)}

revs = subprocess.run(["git","log","--format=%H %ad %s","--date=short","-30","--","kics_disclosure.json"],
                      cwd=ROOT, capture_output=True, text=True, encoding="utf-8").stdout.splitlines()
print("== kics_disclosure.json 최근 커밋 ==")
for r in revs[:30]: print("  ", r[:130])
print()
for sha_line in revs:
    sha = sha_line.split()[0]
    blob = subprocess.run(["git","show",f"{sha}:kics_disclosure.json"], cwd=ROOT,
                          capture_output=True, text=True, encoding="utf-8").stdout
    if not blob: continue
    a = cells(blob,"KR0097","2024.4Q"); b = cells(blob,"KR0071","2024.4Q")
    print(f"{sha[:9]} {sha_line.split()[1]}  KR0097_2024.4Q={a}")
    print(f"{' '*20}  KR0071_2024.4Q={b}")
