"""R4 diversified basic-required-capital: sqrt(V' R4 V) + operational."""
import io, sys
import numpy as np
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
R4 = np.array([[1,0,.25,.25],[0,1,.25,.25],[.25,.25,1,.25],[.25,.25,.25,1]], float)
life, nl, mkt, cred, op = (float(x) for x in sys.argv[1:6])
v = np.array([life, nl, mkt, cred], float)
base = float(np.sqrt(v @ R4 @ v))
print(f"V=({life:,.0f}, {nl:,.0f}, {mkt:,.0f}, {cred:,.0f})  op={op:,.0f}")
print(f"  sqrt(V'R4V)      = {base:,.2f}")
print(f"  + 운영 = 기본요구자본 = {base + op:,.2f}")
print(f"  분산효과 = {life+nl+mkt+cred+op - (base+op):,.2f}")
