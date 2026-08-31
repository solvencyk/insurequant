# -*- coding: utf-8 -*-
"""blocking 5건 정정안을 **사본**에 적용해 게이트 전/후를 비교한다. 라이브 마스터는 안 건드린다."""
import json, sys, subprocess, os, collections
from pathlib import Path
ROOT = Path(r"C:/Users/sangwook.cho/Desktop/insurequant")
SCRATCH = Path(os.environ["SCRATCH"])
src = ROOT/"kics_disclosure.json"
recs = json.loads(src.read_text(encoding="utf-8"))
assert isinstance(recs, list), type(recs)
before_rows = len(recs)
before_combo = {(r.get("원보험사코드"), r.get("공시분기"), str(r.get("항목번호"))) for r in recs}
print("before rows =", before_rows, "combos =", len(before_combo))

def find(code, q, item):
    for r in recs:
        if r.get("원보험사코드")==code and r.get("공시분기")==q and str(r.get("항목번호"))==str(item):
            return r
    return None

changed, removed, added = [], [], []

# --- 1) KR0080 2024.3Q item13: 29 -> 6327 (raw FY2024_Q3 p14 y=216 Ⅲ행) ---
r = find("KR0080","2024.3Q",13)
changed.append(("KR0080","2024.3Q",13,"값",r["값"],"6327")); r["값"]="6327"

# --- 2) KR0069 2024.4Q item29-35: 출재전(A) -> 출재후(B) (md L522-528 / L633-639 B컬럼) ---
B = {29:"18589.38", 30:"23332.41", 31:"46106.95", 32:"0", 33:"68322.65", 34:"21101.73", 35:"7142.45"}
for it, v in B.items():
    r = find("KR0069","2024.4Q",it)
    if r is None: print("  !! missing KR0069 item", it); continue
    if str(r.get("값")) != v:
        changed.append(("KR0069","2024.4Q",it,"값",r.get("값"),v)); r["값"]=v
    if r.get("값_적용후") is not None and str(r.get("값_적용후")) != v:
        changed.append(("KR0069","2024.4Q",it,"값_적용후",r.get("값_적용후"),v)); r["값_적용후"]=v

# --- 3) KR0097 2024.4Q: 47/49/50/51 추가 (2026-08-22 문서화된 raw 판독값, 천원/100000) ---
meta = {k: find("KR0097","2024.4Q",48).get(k) for k in ("원수사명","티커","생손보여부")}
LBL = {47:"보완자본 한도 적용 전", 49:"해약환급금 부족분 상당액 중 해약환급금 상당액 초과분",
       50:"기본자본(TFI표, 공통적용경과조치)", 51:"보완자본(TFI표, 공통적용경과조치)"}
VALS = {47:("3452.36301","3452.36301"), 49:("1776.2964","1776.2964"),
        50:("3526.45331","4332.17294"), 51:("3452.36301","3452.36301")}
for it,(pre,post) in VALS.items():
    if find("KR0097","2024.4Q",it) is not None: print("  (exists already)", it); continue
    row = {"원보험사코드":"KR0097", **meta, "항목번호":it, "항목명":LBL[it],
           "공시분기":"2024.4Q", "값":pre, "값_적용후":post}
    recs.append(row); added.append(("KR0097","2024.4Q",it,pre,post))

# --- 4) KR1010 2023.2Q/3Q: item48/52 제거 (원문에 TFI표 자체가 없음) ---
kill = set()
for q in ("2023.2Q","2023.3Q"):
    for it in (48,52):
        r = find("KR1010",q,it)
        if r is not None:
            kill.add(id(r)); removed.append(("KR1010",q,it,r.get("값")))
recs = [r for r in recs if id(r) not in kill]

print("\n-- 변경 --")
for c in changed: print("   CHG", c)
for a in added: print("   ADD", a)
for d in removed: print("   DEL", d)

after_combo = {(r.get("원보험사코드"), r.get("공시분기"), str(r.get("항목번호"))) for r in recs}
print(f"\nrows {before_rows} -> {len(recs)}   combos {len(before_combo)} -> {len(after_combo)}")
print("  범위밖 유실(사라진 콤보 중 의도한 것 아님):",
      sorted(before_combo - after_combo - {("KR1010","2023.2Q","48"),("KR1010","2023.2Q","52"),
                                           ("KR1010","2023.3Q","48"),("KR1010","2023.3Q","52")}))
print("  신규 콤보:", sorted(after_combo - before_combo))
dups = [k for k,v in collections.Counter((r.get("원보험사코드"), r.get("공시분기"), str(r.get("항목번호"))) for r in recs).items() if v>1]
print("  중복 콤보:", dups[:10], "총", len(dups))

out = SCRATCH/"kics_disclosure_SIM.json"
out.write_text(json.dumps(recs, ensure_ascii=False, indent=2), encoding="utf-8")
print("\nwrote", out)
