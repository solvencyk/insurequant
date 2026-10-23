# -*- coding: utf-8 -*-
import json, sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e25_followups/pass3/verify_independent/val")
from vte import tagged_rows, period_of
from vtab import num
ROOT = "C:/Users/sangwook.cho/Desktop/insurequant"
F = ROOT + "/data/dart/FY2025_Q2/raw/KR0087_동양생명/xml/20250814002600.xml"
rows = tagged_rows(F, 155690, 156420)
vals = {}   # (label_key, period) -> float
for r in rows:
    lab = " / ".join(l for l in r["labels"] if l.strip())
    for c, code, t in r["cells"]:
        vals[(lab.split(" / ")[-1], period_of(c))] = num(t)
pl = json.load(open(ROOT + "/PL_breakdown.json", encoding="utf-8"))
M = {(r["공시분기"], str(r["항목번호"])): (r.get("값"), r.get("값_당분기")) for r in pl if r["원보험사코드"] == "KR0087"}
def g(lab, per): return vals[(lab, per)]
for tag, cq, per_cum, per_3m in (("CURRENT 2025.2Q", "2025.2Q", "C2025dHYA", "C2025dHYQ"), ("PRIOR 2024.2Q", "2024.2Q", "P2024dHYA", "P2024dHYQ")):
    print("====", tag)
    out = {}
    for nm, per in (("cum", per_cum), ("3M", per_3m)):
        act = g("재보험수익, 발생한 보험금", per); act_s = g("재보험수익, 발생한 손해조사비", per)
        fut = g("재보험수익, 미래 서비스와 관련된 변동분에 관련된 금액", per); past = g("재보험수익, 과거 서비스와 관련된 금액", per)
        revtot = g("재보험자에게서 회수한 금액에서 생기는 수익", per)
        exp = g("재보험비용, 예상 보험금 (기초 예상 측정치)", per); expo = g("재보험비용, 예상 기타 보험서비스비용 (기초 예상 측정치)", per)
        ra = g("재보험비용, 비금융위험에 대한 위험조정의 변동분", per); csm = g("재보험비용, 서비스의 이전으로 당기손익에 인식한 보험계약마진", per)
        oth = g("재보험비용, 그 밖의 금액", per); costtot = g("재보험자에게 지급된 보험료 배분액에서 생기는 비용", per)
        print(f" [{nm}] rev rows sum {act+act_s+fut+past} vs total {revtot} (rows inverted: {-(act+act_s+fut+past)==revtot}); cost rows sum {exp+expo+ra+csm+oth} vs total {costtot} (inverted: {-(exp+expo+ra+csm+oth)==costtot})")
        item11 = abs(act) + abs(act_s) - abs(exp) - abs(expo)   # mirrors master defn: actual recovered - expected
        # signed (sign-aware, rows are printed inverted => value = -row)
        item11s = (-act - act_s) - (-exp - expo)
        # other-rows item12 : revenue-type other (-fut-past) - cost-type other(-oth)
        item12_rows = (-fut - past) - (-oth)
        print(f"     item11 = {item11}  (signed {item11s}); CSM printed row {csm}; RA printed row {ra}; item12(other rows rev-other minus cost-other) = {item12_rows}")
        out[nm] = dict(csm=csm, ra=ra, i11=item11, i12rows=item12_rows)
    mv = {k: M.get((cq, k)) for k in ("8", "9", "10", "11", "12")}
    print("  master", cq, mv)
    c = out["cum"]
    for cand in ("as-printed row (9=csm,10=ra)", "-|v|"):
        if cand.startswith("as"): i9, i10 = c["csm"], c["ra"]
        else: i9, i10 = -abs(c["csm"]), -abs(c["ra"])
        i8 = M[(cq, "8")][0]
        i12 = i8 - i9 - i10 - c["i11"]
        print(f"   candidate {cand}: 9={i9} 10={i10} 11={c['i11']} -> 12 = 8-9-10-11 = {i12:.6f}  vs other-rows {c['i12rows']}  diff {i12-c['i12rows']:+.3f}")
