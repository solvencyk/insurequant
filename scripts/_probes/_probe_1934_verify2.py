import sys
import io
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
for p in (ROOT, ROOT / "src"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from solvency.validation.kics_json_rules import irr_derive_expected  # noqa: E402


def eok(million):
    v = million / 100.0
    if abs(v - round(v)) < 1e-6:
        return float(round(v))
    return round(v, 2)


cases = {
    "KR0068 (corrected, 당기 p35 Ⅲ.순자산가치)": {
        "item36": 16266.78,
        "vals_million": [1940351, 2116952, 137244, 3197695, 1915434, 1919556],
    },
    "KR0051 (당기 p25 Ⅲ.순자산가치)": {
        "item36": 55.55,
        "vals_million": [146268, 146586, 140421, 152556, 145698, 146828],
    },
    "KR0087 (당기, OCR-verified via formula)": {
        "item36": 2578.34,
        "vals_million": [2768827, 2840658, 2468912, 3032305, 2868885, 2631973],
    },
    "KR0094 (당기 p28 Ⅲ.순자산가치)": {
        "item36": 10655.45,
        "vals_million": [6319163, 6448867, 5427499, 7105796, 6348177, 6219031],
    },
}

for name, d in cases.items():
    v = d["vals_million"]
    vals = {41: eok(v[0]), 42: eok(v[1]), 43: eok(v[2]), 44: eok(v[3]), 45: eok(v[4]), 46: eok(v[5])}
    expected = irr_derive_expected(vals)
    actual = d["item36"]
    diff = expected - actual
    rel = abs(diff) / abs(expected) * 100 if expected else float("nan")
    print(f"{name}:")
    print(f"  41-46(억원)={vals}")
    print(f"  expected={expected:.4f} actual(item36)={actual} diff={diff:+.4f} rel={rel:.4f}%")
    print()
