# -*- coding: utf-8 -*-
import json
from pathlib import Path
d=Path(r"C:/Users/sangwook.cho/Desktop/insurequant/artifacts/kics_validation")
rep=json.loads((d/"report_20260831T202215Z.json").read_text(encoding="utf-8"))
sec=rep.get("tier2_issuer_inconsistent_exception") or {}
print("keys:", list(sec.keys()))
for k in ("red","review"):
    v=sec.get(k)
    print(f"  {k}: {len(v) if isinstance(v,list) else v}")
    if isinstance(v,list):
        for x in v[:10]: print("     ", x)
det = sec.get("detail") or []
bad=[t for t in det if isinstance(t,(list,tuple)) and len(t)>=7 and t[6] not in (None,0,0.0)]
print(f"  detail 행 {len(det)} · delta!=0 인 행 {len(bad)}")
for t in bad[:10]: print("     DRIFT:", t)
# 전체 RED 중 면제 자체가 깨졌다는 룰
names=[f for f in rep["findings"] if f.get("status")=="RED" and str(f.get("rule")).startswith("TIER2_EXEMPTION")]
print("  TIER2_EXEMPTION_* RED findings:", len(names))
l8=rep.get("life8_issuer_inconsistent_exception")
print("\nlife8:", json.dumps(l8, ensure_ascii=False)[:400])
