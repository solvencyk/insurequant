"""Per-(company,quarter) detail: items 14-23 + 29-40 전/후 with R4/R7/M reconciliation."""
import io, json, sys
from pathlib import Path
import numpy as np
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO)); sys.path.insert(0, str(REPO / "src"))
from solvency.validation.kics_json_rules import R4, R7, MARKET_M

rows = json.loads((REPO / "kics_disclosure.json").read_text(encoding="utf-8"))
def num(v):
    try: return float(str(v).replace(",", ""))
    except (TypeError, ValueError): return None

for arg in sys.argv[1:]:
    code, q = arg.split(":")
    d = {}
    nm = code
    for r in rows:
        if r["원보험사코드"] == code and r["공시분기"] == q:
            d[int(r["항목번호"])] = (num(r.get("값")), num(r.get("값_적용후")), r.get("항목명"))
            nm = r.get("원수사명", code)
    print(f"\n===== {code} {nm} {q} =====")
    for it in list(range(14, 24)) + list(range(29, 41)):
        if it in d:
            pre, post, label = d[it]
            print(f"  {it:>2} {str(label)[:30]:<30} 전={pre!s:>12}  후={post!s:>12}")
    def rec(label, parent, subs, mat, addend=None):
        for post in (0, 1):
            p = d.get(parent, (None, None, ""))[post]
            vs = [d.get(s, (None, None, ""))[post] for s in subs]
            add = d.get(addend, (None, None, ""))[post] if addend else 0.0
            tag = "후" if post else "전"
            if p is None or any(v is None for v in vs) or (addend and add is None):
                miss = [s for s in subs if d.get(s, (None, None, ""))[post] is None]
                print(f"  {label}{tag}: 계산불가 (부모={p}, 결측={miss})")
                continue
            v = np.array(vs, float)
            exp = float(np.sqrt(v @ mat @ v)) + (add or 0.0)
            flag = "OK " if abs(p - exp) <= 2.0 else "FAIL"
            print(f"  {label}{tag}: 공시={p:>12,.2f} 계산={exp:>12,.2f} 차={p - exp:>10,.2f}  {flag}")
    rec("A item17=R7(29-35) ", 17, list(range(29, 36)), R7)
    rec("B item19=M(36-40)  ", 19, list(range(36, 41)), MARKET_M)
    rec("C item15=R4(17-20)+21", 15, [17, 18, 19, 20], R4, 21)
