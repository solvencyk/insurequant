# -*- coding: utf-8 -*-
"""손계산 검산: 한화생명·DB손해·하나손해·하나생명·교보·메리츠의 기본자본 경로를 시뮬레이터 코드를 쓰지 않고 다시 계산해
kics_forward_capital.json 과 대조한다. 규칙(여기서 직접 적은 산수):
  SCR_y = SCR_post + (SCR_pre - SCR_post) x (y-2026)/6
  기준 기여 = min(기발행 잔액, 15% x SCR_post) + min(기본자본형 잔액, 10% x SCR_post)        (보완자본형 = 0)
  연말 기여 = 같은 식을 그 해 12-31 에 콜이 안 온 잔액과 SCR_y 로
  기본자본_y = 기본자본(항목2, 적용후) + 연말 기여 - 기준 기여
  계층 = 발행사 처리(issuer_type 있으면 그것, 없으면 type)   [하나생명·교보만 issuer_type=tier1]
"""
import json, sys
from datetime import date
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
Q = "2026.2Q"
recs = json.loads(Path("kics_disclosure.json").read_text(encoding="utf-8"))
reg = json.loads(Path("data/bonds/capital_tier_registry.json").read_text(encoding="utf-8"))["companies"]
src = json.loads(Path("data/bonds/capital_securities_fy2026h1.json").read_text(encoding="utf-8"))["companies"]
fwd = {r["insurer_code"]: r for r in json.loads(Path("kics_forward_capital.json").read_text(encoding="utf-8"))}
def item(code, no):
    for r in recs:
        if r["원보험사코드"] == code and r["공시분기"] == Q and r["항목번호"] == no:
            pre = float(str(r["값"]).replace(",", "")); post = r.get("값_적용후")
            return pre, (float(str(post).replace(",", "")) if post not in (None, "", "None") else pre)
bad = 0
for code in ("KR0068", "KR0011", "KR0050", "KR0097", "KR0073", "KR0001"):
    scr_pre, scr_post = item(code, 14)[0], item(code, 14)[1]
    basic0 = item(code, 2)[1]
    bonds = [b for c in src if c["code"] == code for b in c["bonds"] if b["tier"] == "hybrid" and b.get("outstanding_mn")]
    def ty(b):
        hit = [s for s in reg[code]["securities"] if s["issue_date"] == b["issue_date"]]
        return hit[0].get("issuer_type") or hit[0]["type"]
    def contrib(at, scr):
        leg = sum(b["outstanding_mn"] / 100 for b in bonds if ty(b) == "legacy_tfi" and date.fromisoformat(b["call_date"]) > at)
        t1 = sum(b["outstanding_mn"] / 100 for b in bonds if ty(b) == "tier1" and date.fromisoformat(b["call_date"]) > at)
        return min(leg, 0.15 * scr) + min(t1, 0.10 * scr)
    base = contrib(date(2026, 6, 30), scr_post)
    print(f"== {code} {fwd[code]['insurer_name']}  SCR post/pre {scr_post:,.0f}/{scr_pre:,.0f}  기본자본 {basic0:,.0f}  기준기여 {base:,.1f}")
    for p in fwd[code]["projections"]:
        y = p["year"]
        scr_y = scr_post + (scr_pre - scr_post) * (y - 2026) / 6
        basic_y = basic0 + contrib(date(y, 12, 31), scr_y) - base
        ratio = max(basic_y, 0) / scr_y * 100
        ok = abs(ratio - p["basic_ratio_pct"]) < 0.011 and abs(basic_y - p["basic_capital_eok"]) < 0.11
        bad += 0 if ok else 1
        print(f"   {y}: 손계산 기본자본 {basic_y:,.1f} 비율 {ratio:.2f}%  | JSON {p['basic_capital_eok']:,.1f} {p['basic_ratio_pct']}%  {'OK' if ok else 'MISMATCH'}")
print("불일치", bad)
