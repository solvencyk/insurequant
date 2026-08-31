import sys
import io
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
for p in (ROOT, ROOT / "src"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from solvency.validation.kics_json_rules import MARKET_M, _diversified_sqrt, irr_derive_expected  # noqa: E402
import numpy as np  # noqa: E402


def eok(million):
    """convert 백만원 value to 억원 (2 decimal), matching _to_eok in fill_market_subitems."""
    v = million / 100.0
    if abs(v - round(v)) < 1e-6:
        return float(round(v))
    return round(v, 2)


# All values captured directly from raw PDF (fitz/pdfplumber render + vision read), 백만원 unless noted.
# item19 disclosed values are already 억원 (from kics_disclosure.json, item19 "값" field).
DATA_19MKT = {
    "KR0004": {"item19": 2299, "36": 110218, "37": 176466, "38": 0, "39": 27883, "40": 0},
    "KR0011": {"item19": 44370, "36_eok_existing": 15626.6, "37": 3314863, "38": 688360, "39": 1280861, "40": 744764},
    "KR0029": {"item19": 384, "36_eok_existing": 304.44, "37": 2245, "38": 0, "39": 1243, "40": 22085},
    "KR0051": {"item19": 71, "36": 5555, "37": 0, "38": 0, "39": 0, "40": 5061},
    "KR0068": {"item19": 82108, "36_eok_existing": 5572.26, "37": 6806022, "38": 1940109, "39": 2084802, "40": 0},
    "KR0080": {"item19": 8058, "36_eok_existing": 4459.78, "37": 435062, "38": 121250, "39": 277734, "40": 24378},
    "KR0087": {"item19": 6497, "36": 257834, "37": 372219, "38": 134420, "39": 324658, "40": 0},
    "KR0094": {"item19": 27807, "36": 1065545, "37": 2289463, "38": 114574, "39": 362457, "40": 0},
    "KR0099": {"item19": 14226, "36_eok_existing": 2135.01, "37": 1297763, "38": 178617, "39": 425948, "40": 0},
    "KR0100": {"item19": 295, "36_eok_existing": 203.31, "37": 6397, "38": 0, "39": 15503, "40": 0},
    "KR0104": {"item19": 19272, "36_eok_existing": 13866.27, "37": 771289, "38": 281893, "39": 348739, "40": 0},
    "KR1098": {"item19": 64, "36_eok_existing": 1.78, "37": 0, "38": 0, "39": 0, "40": 6369},
}

print("=== 19_market reconciliation (using real MARKET_M + _diversified_sqrt import) ===")
for code, d in DATA_19MKT.items():
    v36 = d.get("36_eok_existing")
    if v36 is None:
        v36 = eok(d["36"])
    v37 = eok(d["37"])
    v38 = eok(d["38"])
    v39 = eok(d["39"])
    v40 = eok(d["40"])
    v = np.array([v36, v37, v38, v39, v40], dtype=float)
    expected = _diversified_sqrt(v, MARKET_M)
    actual = d["item19"]
    diff = expected - actual
    rel = abs(diff) / abs(expected) * 100 if expected else float("nan")
    print(f"{code}: v=[36:{v36}, 37:{v37}, 38:{v38}, 39:{v39}, 40:{v40}]  "
          f"expected={expected:.2f} actual={actual} diff={diff:+.2f} rel={rel:.3f}%")

print()
print("=== 36_irr reconciliation (using real irr_derive_expected import) ===")
DATA_IRR = {
    "KR0072": {"item36_existing": 2885.22, "41": -35338, "42": 12500, "43": -355175, "44": 160546, "45": -139464, "46": -3642},
    "KR1010": {"item36_existing": 110.98, "41": 137243, "42": 137779, "43": 136908, "44": 133929, "45": 126091, "46": 147575},
}
for code, d in DATA_IRR.items():
    vals = {41: eok(d["41"]), 42: eok(d["42"]), 43: eok(d["43"]), 44: eok(d["44"]), 45: eok(d["45"]), 46: eok(d["46"])}
    expected = irr_derive_expected(vals)
    actual = d["item36_existing"]
    diff = expected - actual
    rel = abs(diff) / abs(expected) * 100 if expected else float("nan")
    print(f"{code}: 41-46(억원)={vals}  expected={expected:.4f} actual(item36)={actual} diff={diff:+.4f} rel={rel:.4f}%")
