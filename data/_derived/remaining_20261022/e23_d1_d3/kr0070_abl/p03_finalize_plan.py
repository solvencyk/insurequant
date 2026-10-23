# -*- coding: utf-8 -*-
"""Make e23_plan_abl_final.json from the planner output e23_plan_abl.json.  Two changes, nothing else (asserted):
 1. the replaced PL owner-gold entry (2023.1Q item 4) carries the previous note VERBATIM (ticket: replaced owner gold keeps `was` and `note`, with the filing line number and the owner 2026-10-23 approval);
 2. the two CSM chain-forced owner-gold entries (2023.4Q items 1 and 4) are REMOVED instead of replaced in place: the approved replacement values (the printed 7,585.3 and -1,716.3) equal the builder source
    values (CSM builder diag rows), so a replaced entry would be a MASKED gold cell and would need a ledger pin (박제) -- forbidden by the ticket (no new mask cells / no new pins).  Removing the entry lets the builder
    source flow, which is the same value; precedent: e21 removed the 3 KB라이프 2024.1Q gold cells for the same reason.  The old entry (value, was, why verbatim) moves to the contract list `csm_gold_remove`.
Every cell value, every other note and all other contract counts stay byte-identical; the script prints the sha256 of both files."""
import copy
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.stdout.reconfigure(encoding="utf-8")
src = HERE / "e23_plan_abl.json"
plan = json.loads(src.read_text(encoding="utf-8"))
new = copy.deepcopy(plan)
C = new["apply_contract"]

# ---- 1. PL gold replace (2023.1Q item 4): previous note verbatim
assert len(C["gold_replace"]) == 1
e = C["gold_replace"][0]
assert (e["code"], e["item"], e["quarter"]) == ("KR0070", 4, "2023.1Q")
old_note = e["old_entry"]["note"]
assert old_note.startswith("inbox/parser/20260815T1400Z")
i0 = e["note"].index("2026-10-23 parser/ifrs17 (e23,")
tail = e["note"][i0:]
e["note"] = ("owner 2026-10-23 승인, 연쇄용 gold 교체(D3 결정표 · gold_cells_replaced.csv · 분류 ⓐ 원 인쇄값): 이전 gold 값 %s, 이전 was %s, 이전 note 원문 「%s」. " % (e["old_entry"]["값"], e["old_entry"]["was"], old_note)) + tail
assert "L26968" in e["note"] and "L41498" in e["note"]

# ---- 2. CSM chain-forced gold: remove (value = the builder value = the printed value)
CITE = {1: ("L53731", "758,530", "L50551"), 4: ("L53763", "(171,628)", "L50583")}
rm = []
for e in C["csm_gold_replace"]:
    assert e["code"] == "KR0070" and e["quarter"] == "2023.4Q" and e["item"] in (1, 4)
    old_why = e["old_entry"]["why"]
    assert old_why.startswith("CSM continuity fix 2026-06-16")
    ln_o, pr, ln_n = CITE[e["item"]]
    rm.append(dict(code=e["code"], item=e["item"], quarter=e["quarter"], value=e["value"], was=e["was"], old_gold_value=e["old_entry"]["값"], old_why=old_why,
                   why=("owner 2026-10-23 승인, 연쇄용 gold 제거(분류 ⓑ 연쇄: 원 인쇄값도 최신값도 아님): 이전 gold %s, 이전 was %s, 이전 why 원문 「%s」. 원 공시(FY2023 사업보고서 rcept 20240329001518)의 연간 인쇄값은 %s %s 이고 "
                        "최신 공시(FY2024 사업보고서 rcept 20250331001358)의 전기 열도 같다(%s %s). 같은 FY 의 1~3분기 기초가 최신 비교열로 7585.3 으로 옮겨져 이 gold 의 존재 이유(1~3분기 원 기초 7017.8 에 4분기를 맞추기)가 사라졌다. "
                        "승인된 교체값 %s 은 빌더 소스 값과 같아 gold 로 남기면 마스크 칸(박제 필요)이 되므로 항목을 제거해 빌더 소스 값이 흐르게 했다."
                        % (e["old_entry"]["값"], e["old_entry"]["was"], old_why, ln_o, pr, ln_n, pr, e["value"])),
                   old_entry=e["old_entry"]))
C["csm_gold_remove"] = rm
C["csm_gold_replace"] = []

# ---- nothing else may differ
pa, pb = copy.deepcopy(plan), copy.deepcopy(new)
for P in (pa, pb):
    P["apply_contract"]["gold_replace"][0]["note"] = ""
    P["apply_contract"]["csm_gold_replace"] = []
    P["apply_contract"].pop("csm_gold_remove", None)
assert json.dumps(pa, sort_keys=True, ensure_ascii=False) == json.dumps(pb, sort_keys=True, ensure_ascii=False), "something besides the replaced PL note and the two CSM gold moves changed"
assert len(C["csm_gold_new"]) == 18 and len(C["gold_new"]) == 73 and len(C["csm_gold_remove"]) == 2
new["finalized"] = ("2026-10-23 e23_plan_abl_final.json = e23_plan_abl.json + verbatim old note in the replaced PL gold entry + the 2 chain-forced CSM gold entries moved to csm_gold_remove "
                    "(p03_finalize_plan.py); independent re-read kr0070_verify.py")
dst = HERE / "e23_plan_abl_final.json"
dst.write_text(json.dumps(new, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
print("wrote", dst.name, hashlib.sha256(dst.read_bytes()).hexdigest()[:16], "| source", hashlib.sha256(src.read_bytes()).hexdigest()[:16])
print("PL replace note:", C["gold_replace"][0]["note"][:300])
print("CSM remove:", json.dumps({k: v for k, v in rm[0].items() if k not in ("old_entry",)}, ensure_ascii=False)[:900])
