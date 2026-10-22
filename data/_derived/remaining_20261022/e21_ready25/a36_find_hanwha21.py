"""a36: where is 189,467,309,969 printed in the 한화 FY2023_Q2 original filing (READ-ONLY)"""
import sys
sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e21_ready25")
import e21_plan as PL
import e21_t2 as T
sys.stdout.reconfigure(encoding="utf-8")
path = T.main_path("KR0068", "FY2023_Q2")
for tx in ("189,467,309,969", "98,854,352,757"):
    print(tx, PL.find_printed(str(path), [tx], ""))
lines = PL.M_lines(str(path))
for i, l in enumerate(lines, 1):
    if "189,467,309,969" in l:
        print(i, l.strip()[:160])
        for k in range(i - 40, i + 3):
            s = lines[k - 1].strip()
            if s:
                print("   ", k, s[:150])
