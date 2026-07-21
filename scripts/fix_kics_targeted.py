"""Targeted kics_disclosure.json fixes (owner 2026-06-13), run AFTER dedup_kics_disclosure.py.

1) 하나손해 KR0050 2026.1Q (scale cascade 마무리):
   - item3(보완자본) = item1 - item2 : -125617 은 item1-item2_old(132375) 로 역산된 plug.
     dedup이 item2를 1323.75로 정정했으므로 item3 = 6758-1323.75 = 5434.25 로 복구(rule 1 재정합).
   - item28 값_적용후 = 값(28.6154): dedup이 적용전만 ÷100, 적용후 2861.54 잔존 -> rule 8_post 정정.

2) 에이아이에이생명 KR0080 (owner: 경과조치 미적용사 -> 적용전=적용후 강제):
   - 모든 행 값_적용후 = 값 (frozen copy-leak 39162/75984 및 inflated 적용후 일소).
   - item27(지급여력비율) 0 또는 None -> item1/item14*100 도출(공시 헤드라인 복원, rule 7 정정).

backup: dedup_kics_disclosure.py 가 이미 kics_disclosure.json.bak 생성. 본 스크립트는 .bak2 추가 백업.
idempotent. Run: python scripts/fix_kics_targeted.py
"""
from __future__ import annotations
import json, sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "kics_disclosure.json"


def pv(v):
    s = str(v).replace(",", "").replace("%", "").replace("△", "-").strip()
    try:
        return float(s)
    except ValueError:
        return None


def fmt(x):
    return f"{x:.8f}".rstrip("0").rstrip(".") if x == x else "0"


rows = json.loads(SRC.read_text(encoding="utf-8"))
(ROOT / "kics_disclosure.json.bak2").write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")

# index helpers
val_of = {}   # (code,item,q) -> float(값)
for r in rows:
    val_of[(r["원보험사코드"], r["항목번호"], r["공시분기"])] = pv(r["값"])

log = []

# ---- 1) 하나손해 2026.1Q ----
HANA, HQ = "KR0050", "2026.1Q"
i1 = val_of.get((HANA, 1, HQ))
i2 = val_of.get((HANA, 2, HQ))
for r in rows:
    if r["원보험사코드"] != HANA or r["공시분기"] != HQ:
        continue
    it = r["항목번호"]
    if it == 3 and i1 is not None and i2 is not None:
        new3 = i1 - i2
        log.append(f"하나 2026.1Q item3 {r['값']} -> {fmt(new3)} (= item1-item2 plug 복구)")
        r["값"] = fmt(new3)
    if it == 28 and "값_적용후" in r:
        log.append(f"하나 2026.1Q item28 값_적용후 {r['값_적용후']} -> {r['값']} (적용후=적용전)")
        r["값_적용후"] = r["값"]

# ---- 2) AIA KR0080 ----
AIA = "KR0080"
# 2a) 값_적용후 = 값
post_fixed = 0
for r in rows:
    if r["원보험사코드"] != AIA:
        continue
    if "값_적용후" in r and str(r["값_적용후"]) != str(r["값"]):
        r["값_적용후"] = r["값"]
        post_fixed += 1
log.append(f"AIA 값_적용후=값 강제: {post_fixed}행 정정")
# 2b) item27 derive (0 or None)
aia_i1 = {r["공시분기"]: pv(r["값"]) for r in rows if r["원보험사코드"] == AIA and r["항목번호"] == 1}
aia_i14 = {r["공시분기"]: pv(r["값"]) for r in rows if r["원보험사코드"] == AIA and r["항목번호"] == 14}
have27 = set((r["공시분기"]) for r in rows if r["원보험사코드"] == AIA and r["항목번호"] == 27)
# 기존 27행 0/None 정정
for r in rows:
    if r["원보험사코드"] == AIA and r["항목번호"] == 27:
        cur = pv(r["값"]); q = r["공시분기"]
        if (cur is None or cur == 0) and aia_i1.get(q) and aia_i14.get(q):
            new27 = aia_i1[q] / aia_i14[q] * 100
            log.append(f"AIA {q} item27 {r['값']} -> {fmt(new27)} (= item1/item14*100 도출)")
            r["값"] = fmt(new27)
            if "값_적용후" in r:
                r["값_적용후"] = r["값"]
# 27행 자체가 없는 분기 신규 추가
meta = {r["원보험사코드"]: r for r in rows if r["원보험사코드"] == AIA}
proto = next(r for r in rows if r["원보험사코드"] == AIA)
label27 = next((r["항목명"] for r in rows if r["항목번호"] == 27), "다. 지급여력비율 : 가 ÷ 나 × 100")
for q in sorted(set(aia_i1) | set(aia_i14)):
    if q in have27:
        continue
    if aia_i1.get(q) and aia_i14.get(q):
        new27 = aia_i1[q] / aia_i14[q] * 100
        rows.append({
            "원보험사코드": AIA, "원수사명": proto["원수사명"], "티커": proto.get("티커"),
            "생손보여부": proto.get("생손보여부"), "항목번호": 27, "항목명": label27,
            "공시분기": q, "값": fmt(new27),
        })
        log.append(f"AIA {q} item27 신규추가 {fmt(new27)} (= item1/item14*100)")

SRC.write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
print(f"rows now: {len(rows)}")
for line in log:
    print("  +", line)
