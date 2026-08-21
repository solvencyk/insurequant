import io, json, sys
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
rows = json.loads((ROOT / "kics_disclosure.json").read_text(encoding="utf-8"))
PAIRS = [("KR0003","2024.4Q"),("KR0005","2023.3Q"),("KR0097","2024.1Q"),
         ("KR0097","2025.2Q"),("KR0100","2023.4Q"),("KR0104","2023.4Q")]
def num(v):
    try: return float(str(v).replace(",", ""))
    except (TypeError, ValueError): return None
for c, q in PAIRS:
    d = {int(r["항목번호"]): r for r in rows if r["원보험사코드"] == c and r["공시분기"] == q}
    nm = next((r["원수사명"] for r in d.values()), c)
    g = lambda n, k: (d.get(n) or {}).get(k)
    v14, v15, v22, v23 = (num(g(n, "값_적용후")) for n in (14, 15, 22, 23))
    v22 = 0.0 if v22 is None else v22
    exp = None if v15 is None else v15 - v22 + 0.0
    ok = "" if exp is None or v14 is None else (" OK" if abs(exp - v14) <= max(2.0, 0.005*abs(exp)) else "  <<< R5 FAIL")
    print(f"{c} {nm} {q}: i14후={g(14,'값_적용후')} i15후={g(15,'값_적용후')} "
          f"i22후={g(22,'값_적용후')} i23후={g(23,'값_적용후')} | i15-i22+0={exp}{ok}")
