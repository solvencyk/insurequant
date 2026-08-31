# -*- coding: utf-8 -*-
"""문제 셀들이 언제 마스터에 나타났나 — 최근 6커밋 추적."""
import json, subprocess
from pathlib import Path
ROOT = Path(r"C:/Users/sangwook.cho/Desktop/insurequant")
TARGETS = [("KR0097","2024.4Q"),("KR1010","2023.2Q"),("KR1010","2023.3Q"),
           ("KR0080","2024.3Q"),("KR0069","2024.4Q")]
revs = subprocess.run(["git","log","--format=%H|%ad|%s","--date=short","-8","--","kics_disclosure.json"],
                      cwd=ROOT, capture_output=True, text=True, encoding="utf-8").stdout.splitlines()
def grab(blob, code, q, items):
    recs = json.loads(blob)
    if isinstance(recs, dict): recs = recs.get("records") or recs.get("data") or []
    out={}
    for r in recs:
        if r.get("원보험사코드")==code and r.get("공시분기")==q:
            try: it=int(r.get("항목번호"))
            except: continue
            if it in items: out[it]=(r.get("값"), r.get("값_적용후"))
    return {k:out[k] for k in sorted(out)}
WANT = {("KR0097","2024.4Q"):{47,48,49,50,51,52},
        ("KR1010","2023.2Q"):{47,48,49,50,51,52},
        ("KR1010","2023.3Q"):{47,48,49,50,51,52},
        ("KR0080","2024.3Q"):{12,13},
        ("KR0069","2024.4Q"):{17,29,30,31,32,33,34,35}}
for line in revs:
    sha,date,subj = line.split("|",2)
    blob = subprocess.run(["git","show",f"{sha}:kics_disclosure.json"], cwd=ROOT,
                          capture_output=True, text=True, encoding="utf-8").stdout
    if not blob: continue
    print(f"\n### {sha[:9]} {date} {subj[:70]}")
    for t in TARGETS:
        print(f"    {t[0]} {t[1]}: {grab(blob, t[0], t[1], WANT[t])}")
