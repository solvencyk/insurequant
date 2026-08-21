import io, json, sys
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
rows = json.loads((ROOT / "kics_disclosure.json").read_text(encoding="utf-8"))
PAIRS = [("KR0003","2024.3Q"),("KR0004","2024.1Q"),("KR0005","2023.2Q"),("KR0005","2024.4Q"),
         ("KR0049","2023.2Q"),("KR0049","2023.4Q"),("KR0071","2024.3Q"),("KR0071","2025.3Q"),
         ("KR0097","2023.4Q"),("KR0097","2025.1Q"),("KR0100","2023.3Q"),("KR0100","2024.2Q"),
         ("KR0104","2023.3Q"),("KR1011","2026.1Q")]
for c, q in PAIRS:
    d = {int(r["항목번호"]): r for r in rows if r["원보험사코드"] == c and r["공시분기"] == q}
    nm = next((r["원수사명"] for r in d.values()), c)
    out = []
    for n in (14, 15, 22, 23):
        r = d.get(n)
        out.append(f"i{n}: {r.get('값') if r else '-'}/{r.get('값_적용후') if r else '-'}")
    print(f"{c} {nm} {q}:  " + "   ".join(out))
