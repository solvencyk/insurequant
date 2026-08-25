import json, sys, io
sys.stdout.reconfigure(encoding="utf-8")
d = json.load(open("PL_breakdown.json", encoding="utf-8"))
out = io.open("scripts/_probes/out_20260826f_kyobo_check.txt", "w", encoding="utf-8")
for code in ("KR0073", "KR1010", "KR0008", "KR0009", "KR0011", "KR0010", "KR1000"):
    for r in d:
        if r.get("원보험사코드") == code and r.get("공시분기") in ("2025.4Q", "2024.4Q") \
                and r.get("항목번호") in (17, 22, 23, 24):
            out.write(f"{code}\t{r['공시분기']}\titem{r['항목번호']}({r['항목명']})\t"
                      f"값={r['값']}\t당분기={r.get('값_당분기')}\n")
out.close()
print("done")
