# -*- coding: utf-8 -*-
"""읽기 전용: 면제 레지스트리 전수 + 축 제거형 여부 + KR0097 마스터 셀 실측."""
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
import importlib.util
spec = importlib.util.spec_from_file_location("vkd", ROOT / "scripts" / "validate_kics_disclosure.py")
vkd = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vkd)

print("=== 면제 레지스트리 census ===")
for k, v in vkd._exemption_registries().items():
    print(f"  {k:38s} n={len(v):3d}  {sorted(v) if len(v) <= 8 else '...'}")

print("\n=== 마스터 KR0097 2024.4Q / KR0049 2024.3Q 셀 ===")
recs = json.loads((ROOT / "kics_disclosure.json").read_text(encoding="utf-8"))
if isinstance(recs, dict):
    recs = recs.get("records", recs)
for (c, q) in (("KR0097", "2024.4Q"), ("KR0049", "2024.3Q")):
    m = {}
    for r in recs:
        if r.get("회사코드") == c and r.get("분기") == q:
            m[int(r["항목번호"])] = (r.get("값"), r.get("값_적용후"))
    print(f"-- {c} {q}: 항목수 {len(m)}")
    for i in sorted(m):
        if i in (2, 15, 16, 17, 18, 19, 20, 21, 22, 23) or 29 <= i <= 40:
            print(f"     item{i:<3d} 전={m[i][0]!s:<12s} 후={m[i][1]!s:<12s}")
