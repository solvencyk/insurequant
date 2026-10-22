"""a35: locate the printed text of each gold value in the ORIGINAL filing (READ-ONLY)"""
import sys
sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e21_ready25")
import e21_plan as PL
import e21_plan_lib as P
import e21_t2 as T
sys.stdout.reconfigure(encoding="utf-8")
CASES = [("KR0010", "2023.1Q", ["92,565"], "기타사업비용"), ("KR0010", "2023.2Q", ["190,719"], "기타사업비용"), ("KR0010", "2024.2Q", ["192,135"], "기타사업비용"),
         ("KR0003", "2023.2Q", ["71,316,307,049"], ""), ("KR0001", "2023.1Q", ["12,370,224,177"], "기타사업비"), ("KR0001", "2023.2Q", ["71,546,566,619"], "기타사업비"),
         ("KR0068", "2023.1Q", ["375,708,317,423"], "영업이익"), ("KR0068", "2023.2Q", ["189,467,309,969"], "영업외")]
for code, q, texts, lab in CASES:
    fy = P.orig_fy(q)
    path = T.main_path(code, fy)
    hits = PL.find_printed(str(path), texts, lab)
    print(f"{code} {q} {texts} label~{lab!r} in {path.name}: {hits[:8]}")
