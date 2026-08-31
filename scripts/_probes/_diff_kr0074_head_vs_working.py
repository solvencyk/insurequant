# -*- coding: utf-8 -*-
import io, json, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

with open(r"C:\Users\sangwook.cho\AppData\Local\Temp\claude\C--Users-sangwook-cho-Desktop-insurequant\a2eaf685-d24e-438d-8f71-52ff9b5cfb3b\scratchpad\kics_disclosure_HEAD.json", "r", encoding="utf-8") as f:
    head = json.load(f)
with open("kics_disclosure.json", "r", encoding="utf-8") as f:
    working = json.load(f)

head_kr0074 = [r for r in head if r.get("원보험사코드")=="KR0074"]
working_kr0074 = [r for r in working if r.get("원보험사코드")=="KR0074"]
print(f"HEAD KR0074 rows: {len(head_kr0074)}")
print(f"working KR0074 rows: {len(working_kr0074)}")

head_2026q2 = [r for r in head_kr0074 if r.get("공시분기")=="2026.2Q"]
working_2026q2 = [r for r in working_kr0074 if r.get("공시분기")=="2026.2Q"]
print(f"HEAD KR0074 2026.2Q rows: {len(head_2026q2)}")
print(f"working KR0074 2026.2Q rows: {len(working_2026q2)}")

# any quarter with a diff?
head_by_q = {}
for r in head_kr0074:
    head_by_q.setdefault(r["공시분기"], []).append(r)
work_by_q = {}
for r in working_kr0074:
    work_by_q.setdefault(r["공시분기"], []).append(r)

all_q = set(head_by_q) | set(work_by_q)
for q in sorted(all_q):
    h = json.dumps(sorted(head_by_q.get(q, []), key=lambda x: x["항목번호"]), ensure_ascii=False, sort_keys=True)
    w = json.dumps(sorted(work_by_q.get(q, []), key=lambda x: x["항목번호"]), ensure_ascii=False, sort_keys=True)
    if h != w:
        print(f"  DIFF at quarter {q}: HEAD {len(head_by_q.get(q,[]))} rows vs working {len(work_by_q.get(q,[]))} rows")
    else:
        print(f"  quarter {q}: IDENTICAL ({len(head_by_q.get(q,[]))} rows)")
