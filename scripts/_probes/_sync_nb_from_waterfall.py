#!/usr/bin/env python3
"""NB_CSM_multiple.json 의 신계약CSM 셀만 CSM_waterfall 항목2 에 맞춘다 (배수 재계산 포함).

전체 재생성(`build_nb_csm_multiple.py`)은 하지 않는다 — 그 빌더의 분모 소스
`data/kidi/premium_summary.json` 이 디스크에 없어서(owner 가 재수집 보류) 지금 돌리면
월납월초·배수가 전부 null 이 되고 라이브 Panel 5 와 버블맵 Y축이 빈다.
"""
import sys, json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.stdout.reconfigure(encoding="utf-8")
DRY = "--dry-run" in sys.argv

wf = {}
for r in json.loads((ROOT / "CSM_waterfall.json").read_text(encoding="utf-8")):
    if r.get("항목번호") == 2:
        wf[(r["원보험사코드"], r["공시분기"])] = (r.get("값"), r.get("값_당분기"))

P = ROOT / "NB_CSM_multiple.json"
rows = json.loads(P.read_text(encoding="utf-8"))
PAIRS = [("신계약CSM_연누계", "월납월초보험료_연누계", "신계약CSM배수_연누계", 0),
         ("신계약CSM_당분기", "월납월초보험료_당분기", "신계약CSM배수_당분기", 1)]
n_val = n_mult = 0
for r in rows:
    k = (r["원보험사코드"], r["공시분기"])
    if k not in wf:
        continue
    for csm_f, prem_f, mult_f, idx in PAIRS:
        new = wf[k][idx]
        cur = r.get(csm_f)
        if cur is None and new is None:
            continue
        if isinstance(cur, (int, float)) and isinstance(new, (int, float)) and abs(cur - new) < 0.005:
            continue
        print(f"  {r['원수사명'][:14]:14s} {k[1]:8s} {csm_f:14s} {cur} -> {new}")
        r[csm_f] = new
        n_val += 1
        prem = r.get(prem_f)
        # 배수 = 신계약CSM / 월납월초. 분모 없거나 0, 또는 분자 음수(4Q 재서술 artifact)면 null.
        old_m = r.get(mult_f)
        if isinstance(new, (int, float)) and isinstance(prem, (int, float)) and prem and new >= 0:
            r[mult_f] = round(new / prem, 4)
        else:
            r[mult_f] = None
        if r.get(mult_f) != old_m:
            print(f"  {'':14s} {'':8s} {mult_f:14s} {old_m} -> {r[mult_f]}")
            n_mult += 1
print(f"\n신계약CSM 셀 {n_val} · 배수 셀 {n_mult} 갱신" + ("  (dry-run, 파일 안 씀)" if DRY else ""))
if not DRY:
    P.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    print("wrote", P)
