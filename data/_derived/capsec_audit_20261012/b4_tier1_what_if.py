# -*- coding: utf-8 -*-
"""b4: how much does the displayed 기본자본 소진율 move if the classification of the securities the X test could NOT settle (or contradicts) is flipped?
Independent arithmetic from the master (item 6 / 14 / 53) and the pinned registry; no repo code imported.
tier1 = max( legacy53 / (15% SCR) , new_basic / (10% SCR) ),  new_basic = item6 - legacy - (tier2-typed amounts).
Output b4_tier1_what_if_<rev>.txt
"""
import json
import sys

ROOT = "C:/Users/sangwook.cho/Desktop/insurequant"
HERE = ROOT + "/data/_derived/capsec_audit_20261012/"
sys.path.insert(0, HERE)
import audit_io  # noqa: E402

SUF = "_" + audit_io.resolved_rev()
inp = json.load(open(HERE + "a2_inputs_2026_2Q.json", encoding="utf-8"))
reg = audit_io.load_json("data/bonds/capital_tier_registry.json")["companies"]
pub1 = {r["code"]: r for r in audit_io.load_json("kics_tier1_utilization.json")["results"]}


def t1(code, flip_to_tier2=(), flip_to_tier1=()):
    r = inp[code]
    scr, i6, l53 = r["i14_pre"], r["i6_pre"], r.get("i53_pre") or 0.0
    leg = min(l53, max(i6, 0.0))
    excl = 0.0
    for s in reg[code]["securities"]:
        ty = s["type"]
        key = s.get("issue_date")
        if key in flip_to_tier2:
            ty = "tier2"
        if key in flip_to_tier1:
            ty = "tier1"
        if ty == "tier2":
            excl += s["amount_eok"]
    new = max(0.0, i6 - leg - excl)
    p_leg, p_new = leg / (0.15 * scr) * 100, new / (0.10 * scr) * 100
    return max(p_leg, p_new), p_leg, p_new


CASES = [
    ("KR0011", "DB손해보험", "제3·4·5회 -> 보완자본형 (X 검정 쪽, 집계 잔차 113 대 2,973)", dict(flip_to_tier2=("2026-02-11", "2026-06-09", "2026-06-29"))),
    ("KR0011", "DB손해보험", "제2~5회 -> 보완자본형 (제2회 사모 1,200억도 보완자본형이면)", dict(flip_to_tier2=("2025-09-25", "2026-02-11", "2026-06-09", "2026-06-29"))),
    ("KR1000", "코리안리", "제5·6회 -> 기본자본형 (발행사가 기본자본으로 처리한 경우)", dict(flip_to_tier1=("2023-03-16", "2024-10-11"))),
    ("KR1000", "코리안리", "제6회만 -> 기본자본형", dict(flip_to_tier1=("2024-10-11",))),
    ("KR0104", "농협생명", "제5회 -> 기본자본형", dict(flip_to_tier1=("2023-01-31",))),
    ("KR0083", "푸본현대", "2023-02 600억 -> 기본자본형", dict(flip_to_tier1=("2023-02-28",))),
    ("KR0097", "하나생명", "제1회 -> 보완자본형 (이전 분류)", dict(flip_to_tier2=("2023-03-31",))),
    ("KR0073", "교보", "2024-11 -> 보완자본형 (이전 분류)", dict(flip_to_tier2=("2024-11-12",))),
]
L = ["PIN rev=%s registry=%s" % (audit_io.resolved_rev(), audit_io.sha12("data/bonds/capital_tier_registry.json"))]
for code, nm, label, kw in CASES:
    cur = t1(code)
    alt = t1(code, **kw)
    L.append("%s %s | %s | displayed %.1f%% (mine %.1f%%: legacy %.1f / new %.1f) -> alternative %.1f%% (legacy %.1f / new %.1f)  [%+.1f%%p]" % (
        code, nm, label, pub1[code]["utilization_pct"], cur[0], cur[1], cur[2], alt[0], alt[1], alt[2], alt[0] - cur[0]))
open(HERE + "b4_tier1_what_if" + SUF + ".txt", "w", encoding="utf-8", newline="\n").write("\n".join(L) + "\n")
print("\n".join(L))
