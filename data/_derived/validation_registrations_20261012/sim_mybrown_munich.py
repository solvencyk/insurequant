# -*- coding: utf-8 -*-
"""in-memory 시뮬레이션(디스크 무변경): 마이브라운 KR1108 2025.3Q 47·48·49·53·54 = 0 을 (값·값_적용후) 싣거나,
뮌헨 KR1101 2026.2Q 50·52 = 2716.42 만 싣거나 했을 때 K-ICS 룰 엔진이 내는 finding 변화(라이브 대비).
재현: python <이 파일>   (인자 없음. 출력은 stdout)"""
import json, sys, io, copy
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, "src"); sys.path.insert(0, "scripts")
from solvency.validation.kics_json_rules import run_validation
import validate_kics_disclosure as K

recs = json.load(open("kics_disclosure.json", encoding="utf-8"))

def run(records):
    return run_validation(records,
                          source_has_breakdown=K._scan_breakdown_presence(records),
                          tfi_applicability=K._load_tfi_applicability(),
                          life_subrisk_applicability=K._load_life_subrisk_applicability(),
                          life_subrisk_source_absent=K._load_life_subrisk_source_absent())

def key(f):
    return (f.get("원보험사코드"), f.get("공시분기"), str(f.get("rule")), f.get("status"))

def add_cells(records, code, q, vals, name):
    out = list(records)
    tmpl = next(r for r in records if r["원보험사코드"] == code and r["공시분기"] == q)
    for item, v in vals.items():
        assert not any(r["원보험사코드"] == code and r["공시분기"] == q and int(r["항목번호"]) == item for r in records), item
        r = copy.deepcopy(tmpl)
        r["항목번호"] = item; r["항목명"] = name.get(item, str(item)); r["값"] = str(v); r["값_적용후"] = str(v)
        out.append(r)
    return out

base = run(recs)
bk = {}
for f in base["findings"]:
    bk.setdefault(key(f), []).append(f)
print("baseline findings", len(base["findings"]), "status", base["summary"] if "summary" in base else "")

def diff(label, new):
    nk = {}
    for f in new["findings"]:
        nk.setdefault(key(f), []).append(f)
    print("=====", label, "findings", len(new["findings"]))
    new_only = [k for k in nk if k not in bk]
    gone = [k for k in bk if k not in nk]
    print("  new (rule,status) keys:", len(new_only)); 
    for k in sorted(new_only): 
        d = nk[k][0].get("detail")
        print("   +", k, "|", str(d)[:230])
    print("  gone keys:", len(gone))
    for k in sorted(gone): print("   -", k)
    reds = [k for k in new_only if k[3] == "RED"]
    print("  NEW RED:", sorted(reds))

names = {47:"보완자본 한도 적용 전", 48:"보완자본 한도", 49:"해약환급금 부족분 상당액 중 해약환급금 상당액 초과분", 53:"(기발행 신종자본증권)", 54:"(기발행 후순위채무)", 50:"기본자본", 52:"지급여력금액"}
# 마이브라운: 형제 분기 값에서 항목명을 가져오자
sib = {int(r["항목번호"]): r["항목명"] for r in recs if r["원보험사코드"] == "KR1108" and r["공시분기"] == "2026.1Q"}
names.update({k: v for k, v in sib.items() if k in names})
diff("MyBrown 2025.3Q 47/48/49/53/54 = 0", run(add_cells(recs, "KR1108", "2025.3Q", {47: 0, 48: 0, 49: 0, 53: 0, 54: 0}, names)))
# 뮌헨
sib2 = {int(r["항목번호"]): r["항목명"] for r in recs if r["원보험사코드"] == "KR1101" and r["공시분기"] == "2026.1Q"}
names.update({k: v for k, v in sib2.items() if k in names})
diff("Munich 2026.2Q 50/52 = 2716.42 only", run(add_cells(recs, "KR1101", "2026.2Q", {50: 2716.42, 52: 2716.42}, names)))
diff("Munich 2026.2Q 50/51(0)/52", run(add_cells(recs, "KR1101", "2026.2Q", {50: 2716.42, 51: 0, 52: 2716.42}, names)))
