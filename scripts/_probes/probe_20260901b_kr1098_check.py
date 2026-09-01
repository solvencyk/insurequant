# -*- coding: utf-8 -*-
import io, json, sys
from pathlib import Path
REPO = Path(__file__).resolve().parents[2]
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, str(REPO / "scripts"))
import fill_market_subitems_to_disclosure as F

text = (REPO / "md_inbox" / "FY2026_Q2" / "KR1098_카카오페이손해보험.md").read_text(encoding="utf-8")
subs = F.extract_mkt_subs(text)
print("subs:", subs)
v5 = [float(F._to_eok(*subs.get(i, ("0","백만원")))) for i in (36,37,38,39,40)]
print("v5 (억원):", v5)
est = F.mkt_est(v5)
print("est:", est)

rows = json.loads((REPO / "kics_disclosure.json").read_text(encoding="utf-8"))
for r in rows:
    if r["원보험사코드"] == "KR1098" and r["공시분기"] == "2026.2Q" and int(r["항목번호"]) in (19,36,37,38,39,40):
        print(r["항목번호"], r["항목명"], r["값"])
