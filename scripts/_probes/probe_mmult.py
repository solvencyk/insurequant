"""R7 (life sub-risks 29-35) / MARKET_M (36-40) diversified aggregation check."""
import io, sys
import numpy as np
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[2]))
from src.solvency.validation.kics_json_rules import R7, MARKET_M

kind = sys.argv[1]
vals = [float(x) for x in sys.argv[2:]]
M = R7 if kind == "r7" else MARKET_M
v = np.array(vals, float)
print(f"{kind}  V={vals}")
print(f"  sqrt(V'MV) = {float(np.sqrt(v @ M @ v)):,.4f}   (sum={sum(vals):,.2f})")
