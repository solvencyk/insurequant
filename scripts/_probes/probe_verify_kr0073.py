import io
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, "scripts")
import extract_asset_quality as aq

registry = aq.build_registry()
diag = []
rows = aq.extract_company_quarter("KR0073", "FY2026_Q2", registry, diag)
print("KR0073 rows:", len(rows))
for r in rows:
    print(f"  item{r['항목번호']:3d} lvl{r['레벨']} [{r['섹션']}] {r['항목명']}: {r['값']}")

print()
print("diag:", diag)
