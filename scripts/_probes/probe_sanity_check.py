import io
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, "scripts")
import extract_asset_quality as aq

registry = aq.build_registry()
diag = []
codes = sys.argv[1:] if len(sys.argv) > 1 else ["KR0068", "KR0080", "KR0008"]
for code in codes:
    rows = aq.extract_company_quarter(code, "FY2026_Q2", registry, diag)
    by_item = {r["항목번호"]: r["값"] for r in rows}
    i1, i2, i3 = by_item.get(1), by_item.get(2), by_item.get(3)
    print(f"{code}: item1={i1} item2={i2} item3={i3}", end="  ")
    if i1 is not None and i2 is not None and i2:
        implied = i1 / i2 * 100
        print(f"implied_ratio={implied:.4f} vs disclosed={i3} diff={abs(implied - i3):.4f}")
    else:
        print()
    fv120 = by_item.get(120)
    fv127 = by_item.get(127)
    fv128 = by_item.get(128)
    print(f"  fv: 일반계정소계={fv120} 특별계정소계={fv127} 합계={fv128} sum={None if fv120 is None or fv127 is None else fv120+fv127} diff_from_128={None if fv120 is None or fv127 is None or fv128 is None else (fv120+fv127)-fv128}")
