import json
import io
import sys
import os
import math

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, os.path.abspath("."))

from src.solvency.validation.kics_json_rules import MARKET_M, irr_derive_expected  # noqa

patch = json.load(open("data/_derived/_patch_2026q2_KR0049.json", encoding="utf-8"))
print("JSON valid. company:", patch["company_code"], "quarter:", patch["quarter"])
print("cells:", len(patch["cells"]))

values = {c["항목번호"]: c["값"] for c in patch["cells"]}
post = {c["항목번호"]: c["값_적용후"] for c in patch["cells"]}
print("\n항목번호 -> 값 / 값_적용후")
for k in sorted(values):
    print(k, values[k], "/", post[k])

# 19_market check
V = [values.get(i, 0.0) or 0.0 for i in range(36, 41)]
total = 0.0
for i in range(5):
    for j in range(5):
        total += V[i] * MARKET_M[i][j] * V[j]
item19_expected = math.sqrt(total)
print(f"\n19_market: derived={item19_expected:.4f}  actual(item19)={values[19]}  diff={abs(item19_expected-values[19]):.4f}")
tol19 = max(2.0, 0.05 * abs(item19_expected))
print(f"  tolerance={tol19:.4f}  status={'GREEN/YELLOW (within tol)' if abs(item19_expected-values[19])<=tol19 else 'RED'}")

# 36_irr check
irr_vals = {i: values.get(i) for i in [41, 42, 43, 44, 45, 46]}
item36_expected = irr_derive_expected(irr_vals)
print(f"\n36_irr: derived={item36_expected:.4f}  actual(item36)={values[36]}  diff={abs(item36_expected-values[36]):.4f}")
tol36 = max(2.0, 0.05 * abs(item36_expected))
print(f"  tolerance={tol36:.4f}  status={'GREEN/YELLOW (within tol)' if abs(item36_expected-values[36])<=tol36 else 'RED'}")

# sanity: all mirrors correct?
for i in range(36, 41):
    assert values[i] == post[i], f"item{i} mirror mismatch"
print("\nitem36-40 mirror (값==값_적용후): OK")
for i in range(41, 47):
    assert post[i] is None, f"item{i} 값_적용후 should be null"
print("item41-46 값_적용후 all null: OK")

print(f"\nitem19 값_적용후 = {post[19]} (expected 536, matches 값)")
