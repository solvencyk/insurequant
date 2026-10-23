# -*- coding: utf-8 -*-
"""Make e23_plan_kdb_final.json from the planner output e23_plan_kdb.json.  Three changes, nothing else (asserted):
 1. the 4 replaced PL owner-gold entries (2023.2Q / 2023.3Q items 4 and 7) carry the previous note VERBATIM (ticket: replaced owner gold keeps `was` and `note`, with the filing line number and the owner
    2026-10-23 approval);
 2. the 5 replaced class-A CSM owner-gold entries (2023.1Q items 4/5/6, 2023.2Q items 4/5) carry the previous `why` VERBATIM plus the line numbers of the ORIGINAL print (read by the independent verifier code);
 3. the 2 chain-forced class-B CSM owner-gold entries (2023.4Q items 1 and 4) are REMOVED instead of replaced: the approved replacement values (5695.9 / -2560.0) equal the builder source values
    (CSM builder diag rows), so a replaced entry would be a MASKED gold cell and would need a ledger pin (박제) -- forbidden by the ticket (no new mask cells / no new pins).  Removing the entry lets the
    builder source flow, which is the same value; precedent: e21 removed the 3 KB라이프 2024.1Q gold cells and the ABL load of this chain removed its 2 chain-forced entries for the same reason.
Every cell value, every other note and all other contract counts stay byte-identical; the script prints the sha256 of both files."""
import copy
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.stdout.reconfigure(encoding="utf-8")
import kr0072_verify as V  # noqa: E402  (independent reader; importing does not run main)
from kdb_notes import csm_tables  # noqa: E402

src = HERE / "e23_plan_kdb.json"
plan = json.loads(src.read_text(encoding="utf-8"))
new = copy.deepcopy(plan)
C = new["apply_contract"]
TAIL_MARK = "2026-10-23 parser/ifrs17 (e23,"

# ---- original prints (independent reader): CSM current-period tables of the original FY2023 filings
o1 = V.o1_csm_cur(V.F["O1"])
o2 = csm_tables(V.F["O2"])["cur"]
o4 = csm_tables(V.F["O4"])["cur"]
ORIG = {"2023.1Q": (o1["rows"], "20230515002450", "1분기보고서"), "2023.2Q": (o2["rows"], "20230814003052", "반기보고서"), "2023.4Q": (o4["rows"], "20240401002710", "사업보고서")}
LATEST_ANNUAL = "20250331002302"

# ---- 1. PL gold replace: previous note verbatim
assert len(C["gold_replace"]) == 4
for e in C["gold_replace"]:
    k = (e["code"], e["item"], e["quarter"])
    assert k in {("KR0072", 4, "2023.2Q"), ("KR0072", 7, "2023.2Q"), ("KR0072", 4, "2023.3Q"), ("KR0072", 7, "2023.3Q")}, k
    old_note = e["old_entry"]["note"]
    assert old_note.startswith("inbox/parser/2026081") or old_note.startswith("inbox/parser/2026082"), old_note[:40]
    i0 = e["note"].index(TAIL_MARK)
    tail = e["note"][i0:]
    cls = "ⓐ 원 인쇄값(3개월 열이 아닌 누적 열)" if e["item"] == 4 else "ⓐ 파생 plug(식 3-(4+5+6))"
    e["note"] = ("owner 2026-10-23 승인, 연쇄용 gold 교체(D3 결정표 · gold_cells_replaced.csv · 분류 %s): 이전 gold 값 %s, 이전 was %s, 이전 note 원문 「%s」. " % (cls, e["old_entry"]["값"], e["old_entry"]["was"], old_note)) + tail
    if e["item"] == 4:
        assert "L40301" in e["note"] or "L46159" in e["note"]
    assert "owner 2026-10-23 승인" in e["note"] and old_note in e["note"]

# ---- 2. CSM gold replace (class A): previous why verbatim + original print line
assert len(C["csm_gold_replace"]) == 7
keep, rm = [], []
for e in C["csm_gold_replace"]:
    k = (e["code"], e["item"], e["quarter"])
    old_why = e["old_entry"]["why"]
    rows, rcept, kind = ORIG[e["quarter"]]
    r = rows[e["item"]]
    if (e["quarter"], e["item"]) in {("2023.4Q", 1), ("2023.4Q", 4)}:
        assert old_why.startswith("CSM continuity fix 2026-06-16"), old_why[:40]
        t4 = csm_tables(V.F["N4"])["prior"]["rows"][e["item"]]
        rm.append(dict(code=e["code"], item=e["item"], quarter=e["quarter"], value=e["value"], was=e["was"], old_gold_value=e["old_entry"]["값"], old_why=old_why,
                       why=("owner 2026-10-23 승인, 연쇄용 gold 제거(분류 ⓑ 연쇄: 원 인쇄값도 최신값도 아님): 이전 gold %s, 이전 was %s, 이전 why 원문 「%s」. 원 공시(FY2023 사업보고서 rcept %s)의 연간 인쇄값은 L%s %s 이고 "
                            "최신 공시(FY2024 사업보고서 rcept %s)의 전기 열도 같다(L%s %s). 같은 FY 의 1~3분기 기초가 최신 비교열로 5695.9 로 옮겨져 이 gold 의 존재 이유(1~3분기 원 기초 5239.4 에 4분기를 맞추기)가 사라졌다. "
                            "승인된 교체값 %s 은 빌더 소스 값과 같아 gold 로 남기면 마스크 칸(박제 필요)이 되므로 항목을 제거해 빌더 소스 값이 흐르게 했다."
                            % (e["old_entry"]["값"], e["old_entry"]["was"], old_why, rcept, r["line"], r["printed"], LATEST_ANNUAL, t4["line"], t4["printed"], e["value"])),
                       old_entry=e["old_entry"]))
        continue
    assert old_why.startswith("raw 재확인"), old_why[:30]
    i0 = e["why"].index(TAIL_MARK)
    tail = e["why"][i0:]
    exact = round(r["mn"] / 100.0, 2)
    e["why"] = ("owner 2026-10-23 승인, 연쇄용 gold 교체(D3 결정표 · gold_cells_replaced.csv · 분류 ⓐ 원 인쇄값): 이전 gold 값 %s, 이전 was %s, 이전 why 원문 「%s」. "
                "원 공시(FY2023 %s rcept %s) 별도 주석 L%s 인쇄값 %s = %s억원(gold 와의 차이 %+.2f, 0.05억 이내). " % (e["old_entry"]["값"], e["old_entry"]["was"], old_why, kind, rcept, r["line"], r["printed"], format(exact, "g"), e["old_entry"]["값"] - exact)) + tail
    assert old_why in e["why"] and "owner 2026-10-23 승인" in e["why"]
    keep.append(e)
C["csm_gold_replace"] = keep
C["csm_gold_remove"] = rm
assert len(keep) == 5 and len(rm) == 2

# ---- nothing else may differ
pa, pb = copy.deepcopy(plan), copy.deepcopy(new)
for P in (pa, pb):
    for e in P["apply_contract"]["gold_replace"]:
        e["note"] = ""
    P["apply_contract"]["csm_gold_replace"] = []
    P["apply_contract"].pop("csm_gold_remove", None)
assert json.dumps(pa, sort_keys=True, ensure_ascii=False) == json.dumps(pb, sort_keys=True, ensure_ascii=False), "something besides the replaced notes / whys and the two CSM gold moves changed"
assert len(C["csm_gold_new"]) == 13 and len(C["gold_new"]) == 61 and len(C["gold_replace"]) == 4 and len(C["set_dangi_add"]) == 8
new["finalized"] = ("2026-10-23 e23_plan_kdb_final.json = e23_plan_kdb.json + verbatim old notes in the 4 replaced PL gold entries + verbatim old whys (+ original print lines) in the 5 replaced class-A CSM gold entries + the 2 chain-forced "
                    "class-B CSM gold entries moved to csm_gold_remove (p03_finalize_plan.py); independent re-read kr0072_verify.py")
dst = HERE / "e23_plan_kdb_final.json"
dst.write_text(json.dumps(new, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
print("wrote", dst.name, hashlib.sha256(dst.read_bytes()).hexdigest()[:16], "| source", hashlib.sha256(src.read_bytes()).hexdigest()[:16])
print("PL replace note (item 4, 2023.2Q):", [e["note"][:420] for e in C["gold_replace"] if (e["item"], e["quarter"]) == (4, "2023.2Q")][0])
print("CSM replace why (2023.1Q item 4):", [e["why"][:700] for e in C["csm_gold_replace"] if (e["item"], e["quarter"]) == (4, "2023.1Q")][0])
print("CSM remove why:", json.dumps({k: v for k, v in rm[0].items() if k not in ("old_entry",)}, ensure_ascii=False)[:900])
