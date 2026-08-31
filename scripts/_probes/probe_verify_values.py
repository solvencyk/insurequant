import io
import json
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, "scripts")
import extract_asset_quality as aq

registry = aq.build_registry()
diag = []
rows = aq.extract_company_quarter("KR0011", "FY2026_Q2", registry, diag)
print("KR0011 rows:", len(rows))
for r in rows:
    print(f"  item{r['항목번호']:3d} [{r['섹션']}] {r['항목명']}: {r['값']}")
