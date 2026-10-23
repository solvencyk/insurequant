# -*- coding: utf-8 -*-
"""Make e23_plan_hd_final.json from the planner output e23_plan_hd.json.  Changes (asserted), nothing else:
 1. the 6 IR-leg PL gold notes (items 2 / 13 / 14 of 2023.1Q and 2023.2Q) are rewritten so that the IR factsheet lineage (file, sheet, cell, label cell, block cell, header cell, printed value, sum identity with the
    DART statement 보험손익, owner D3 permission) is stated in full; `plan["ir_lineage"]` lists the same facts for the provenance sidecar;
 2. the 4 owner CSM chain-forced gold entries (2023.3Q items 1 / 4, 2023.4Q items 1 / 4, class B): the 3 whose approved replacement value EQUALS the CSM builder source value are REMOVED instead of replaced
    (a replaced entry would be a MASKED gold cell and would need a ledger pin -- forbidden by the ticket: no new mask cells / no new pins); the 1 whose approved value differs from the builder source
    (2023.4Q item 4: -2715.9 vs builder -2714.9, the latest comparative prints the restated adjustment) is REPLACED in place with the previous `why` verbatim, `was` kept, the owner approval and the line numbers
    of the original annual print and of the latest comparative; precedent: ABL / KDB load of this chain, e21 KB라이프;
 3. the 11 null_dangi additions keep their reasons in a doc key of the gold file (written by the applier).
Every cell value, every other note and all other contract counts stay byte-identical; the script prints the sha256 of both files."""
import copy
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.stdout.reconfigure(encoding="utf-8")
import kr0009_verify as V  # noqa: E402  (independent reader; importing does not run main)

src = HERE / "e23_plan_hd.json"
plan = json.loads(src.read_text(encoding="utf-8"))
new = copy.deepcopy(plan)
C = new["apply_contract"]
TAIL_MARK = "2026-10-23 parser/ifrs17 (e23,"

# ---------------------------------------------------------------- 1. IR notes + lineage
IR_NAME = {2: "장기", 13: "자동차", 14: "일반"}
IR_FY = {"2023.1Q": "FY2024 1분기 IR 자료", "2023.2Q": "FY2024 반기 IR 자료"}
bucket_by_q = {b["quarter"]: b for b in new["buckets"]}
lineage = []
n_ir = 0
for e in C["gold_new"]:
    if e["item"] not in IR_NAME or e["quarter"] not in IR_FY:
        continue
    q, it = e["quarter"], e["item"]
    cell = next(c for c in bucket_by_q[q]["cells"] if c["item"] == it)
    p = cell["parts"][0]
    assert p.get("xlsx") and p["sheet"] == "(3) UW Income" and p["cell"] and p["label_cell"] and p["header_cell"] == "L6"
    stm = next(c for c in bucket_by_q[q]["cells"] if c["item"] == 1)["parts"][0]            # DART separate statement 보험손익 (prior-year cumulative)
    sibling = {k: next(c for c in bucket_by_q[q]["cells"] if c["item"] == k) for k in (2, 13, 14)}
    legs_sum = sum(sibling[k]["new"] for k in (2, 13, 14))
    assert abs(legs_sum - stm["contribution_mn"]) < 2e-6, (legs_sum, stm["contribution_mn"])
    ir = V.ir_legs(q)
    irc = ir["cells"][IR_NAME[it]]
    assert irc["cell"] == p["cell"] and irc["label_cell"] == p["label_cell"] and abs(irc["value_mn"] - e["value"]) < 2e-6
    hdr = str(ir["header_text"]).replace("\n", " ")
    lin = dict(code=e["code"], quarter=q, item=it, file=ir["file"], sheet=ir["sheet"], cell=irc["cell"], label_cell=irc["label_cell"], label=irc["label"],
               block=IR_NAME[it], block_cell=irc["block_cell"], header_cell=ir["header_cell"], header=hdr, unit="백만원", printed=p["printed"], value_mn=e["value"],
               total_cell=ir["cells"]["합계"]["cell"], total_mn=ir["cells"]["합계"]["value_mn"])
    lineage.append(lin)
    old_note = e["note"]
    assert old_note.startswith(TAIL_MARK)
    e["note"] = (f"{TAIL_MARK} ticket 20261023T0900Z D3: 현대해상 KR0009 FY2023 2023.1Q~4Q 최신 비교열 채택, owner 결정 2026-10-23: DART 에 전분기 LOB 분해 표가 없어 IR 팩트시트를 LOB 레그 원천으로 허용): "
                 f"LOB 레그 항목 {it}({IR_NAME[it]} 보험손익) = 현대해상 {IR_FY[q]} 팩트시트 {ir['file']} 시트 '{ir['sheet']}' 셀 {irc['cell']} "
                 f"(행 라벨 셀 {irc['label_cell']} 「보 험 손 익」, 종목 블록 셀 {irc['block_cell']} 「{IR_NAME[it]}」, 열 머리글 셀 {ir['header_cell']} 「{hdr}」 = 전년동기({q[:4]}.{q[5]}Q) 누계 열, 단위 L4 「(단위:백만원)」), "
                 f"인쇄값 {p['printed']} 백만원 → 저장 {e['value']} 백만원. 일반 {sibling[14]['parts'][0]['cell']} + 장기 {sibling[2]['parts'][0]['cell']} + 자동차 {sibling[13]['parts'][0]['cell']} = {legs_sum:.6f} 백만원 = "
                 f"합계 셀 {ir['cells']['합계']['cell']} {ir['cells']['합계']['value_mn']:.6f} = 같은 분기보고서 DART 별도 포괄손익계산서 전년동기 누적 보험손익 {stm['printed']}원 (L{stm['line']}, 항목 1)과 원 단위까지 일치. "
                 f"변경 전 마스터값 {e['was']} (원 공시 보험종목별 수지 인쇄값, 비재작성 판). 2023.4Q 레그 13/14 도 IR 유래 owner gold 라 같은 방식의 선례가 있다. 변동 {e['value'] - e['was']:+.6f}. "
                 f"증거 data/_derived/remaining_20261022/e23_d1_d3/kr0009_hyundai/e23_plan_hd.json, kr0009_verify.txt")
    n_ir += 1
assert n_ir == 6, n_ir
new["ir_lineage"] = lineage

# ---------------------------------------------------------------- 2. CSM chain-forced gold: remove the three masked, replace the one load-bearing
o4 = V.csm_cur_table("O4", "2023.4Q")["rows"]                  # ORIGINAL FY2023 annual (rcept 20240314001515) CSM roll-forward, current period
ORIG_ANNUAL = {1: o4[1], 4: o4[4]}
LATEST = {("2023.3Q", 1): ("20241114003026", "FY2024 3분기보고서"), ("2023.3Q", 4): ("20241114003026", "FY2024 3분기보고서"),
          ("2023.4Q", 1): ("20250313001346", "FY2024 사업보고서"), ("2023.4Q", 4): ("20250313001346", "FY2024 사업보고서")}
rm, keep = [], []
assert len(C["csm_gold_replace"]) == 4
for e in C["csm_gold_replace"]:
    k = (e["quarter"], e["item"])
    old_why = e["old_entry"]["why"]
    assert old_why.startswith("CSM continuity fix 2026-06-16"), old_why[:40]
    cell = next(c for cb in new["csm_buckets"] for c in cb["cells"] if cb["quarter"] == e["quarter"] and c["item"] == e["item"])
    ln = cell["parts"][0]["line"]
    printed = cell["parts"][0]["printed"]
    rcept, kind = LATEST[k]
    tail_i = e["why"].index(TAIL_MARK)
    tail = e["why"][tail_i:]
    orig_txt = ""
    if e["quarter"] == "2023.4Q":
        r = ORIG_ANNUAL[e["item"]]
        orig_txt = f"원 공시(FY2023 사업보고서 rcept 20240314001515) 별도 주석 CSM 롤포워드 당기 열 L{r['line']} {r['printed']} 천원 = {r['mn'] / 100.0:.5f}억원 (빌더 소스 값 {e['old_entry']['was']}), "
    else:
        orig_txt = f"원 공시(FY2023 3분기보고서 rcept 20231114002737)의 빌더 소스 값은 {e['old_entry']['was']}억원이고 ({kind} 전기 열 인쇄값과 같다), "
    approved_same_as_builder = abs(e["value"] - e["old_entry"]["was"]) < 0.05
    if approved_same_as_builder:
        rm.append(dict(code=e["code"], item=e["item"], quarter=e["quarter"], value=e["value"], was=e["was"], old_gold_value=e["old_entry"]["값"], old_why=old_why,
                       why=(f"owner 2026-10-23 승인, 연쇄용 gold 제거(분류 ⓑ 연쇄: 원 인쇄값도 최신값도 아님): 이전 gold {e['old_entry']['값']}, 이전 was {e['old_entry']['was']}, 이전 why 원문 「{old_why}」. "
                            f"{orig_txt}최신 공시({kind} rcept {rcept})의 전기 열은 L{ln} {printed} 천원 = {cell['exact']}억원(저장값 {e['value']})이다. 같은 FY 의 1~3분기 기초가 최신 비교열 83515.4 로 옮겨져 "
                            f"이 gold 의 존재 이유(1~3분기 원 기초 88281.1 에 3·4분기를 맞추기)가 사라졌다. 승인된 교체값 {e['value']} 은 빌더 소스 값과 같아 gold 로 남기면 마스크 칸(박제 필요)이 되므로 "
                            f"항목을 제거해 빌더 소스 값이 흐르게 했다(선례: 이 체인의 ABL · e21 KB라이프)."),
                       old_entry=e["old_entry"]))
    else:
        assert k == ("2023.4Q", 4), k
        e["why"] = (f"owner 2026-10-23 승인, 연쇄용 gold 교체(D3 결정표 · gold_cells_replaced.csv · 분류 ⓑ 연쇄: 원 인쇄값도 최신값도 아님): 이전 gold 값 {e['old_entry']['값']}, 이전 was {e['old_entry']['was']}, "
                    f"이전 why 원문 「{old_why}」. {orig_txt}최신 공시({kind} rcept {rcept})의 전기 열은 L{ln} {printed} 천원 = {cell['exact']}억원(저장값 {e['value']})이라 "
                    f"교체값은 빌더 소스 값({e['old_entry']['was']})과 달라 마스크 칸이 아니다(적재 후에도 gold 필요). ") + tail
        assert old_why in e["why"] and "owner 2026-10-23 승인" in e["why"] and f"L{ln}" in e["why"]
        keep.append(e)
C["csm_gold_replace"] = keep
C["csm_gold_remove"] = rm
assert len(keep) == 1 and len(rm) == 3 and {(x["quarter"], x["item"]) for x in rm} == {("2023.3Q", 1), ("2023.3Q", 4), ("2023.4Q", 1)}

# ---------------------------------------------------------------- nothing else may differ
pa, pb = copy.deepcopy(plan), copy.deepcopy(new)
for Pn in (pa, pb):
    for e in Pn["apply_contract"]["gold_new"]:
        if (e["quarter"], e["item"]) in {(q, i) for q in IR_FY for i in IR_NAME}:
            e["note"] = ""
    Pn["apply_contract"]["csm_gold_replace"] = []
    Pn["apply_contract"].pop("csm_gold_remove", None)
    Pn.pop("ir_lineage", None)
assert json.dumps(pa, sort_keys=True, ensure_ascii=False) == json.dumps(pb, sort_keys=True, ensure_ascii=False), "something besides the IR notes and the CSM gold split changed"
assert len(C["csm_gold_new"]) == 14 and len(C["gold_new"]) == 57 and len(C["gold_replace"]) == 0 and len(C["null_dangi_add"]) == 11
new["finalized"] = ("2026-10-23 e23_plan_hd_final.json = e23_plan_hd.json + IR-lineage notes of the 6 IR leg gold cells (+ plan['ir_lineage']) + the 3 chain-forced CSM gold entries whose approved value equals the builder source "
                    "moved to csm_gold_remove + the 1 load-bearing chain-forced entry (2023.4Q item 4) replaced with the previous why verbatim (p03_finalize_plan.py); independent re-read kr0009_verify.py")
dst = HERE / "e23_plan_hd_final.json"
dst.write_text(json.dumps(new, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
print("wrote", dst.name, hashlib.sha256(dst.read_bytes()).hexdigest()[:16], "| source", hashlib.sha256(src.read_bytes()).hexdigest()[:16])
print("IR note (2023.1Q item 2):", [e["note"] for e in C["gold_new"] if (e["quarter"], e["item"]) == ("2023.1Q", 2)][0])
print("CSM replace why (2023.4Q item 4):", C["csm_gold_replace"][0]["why"][:1200])
print("CSM remove why (2023.4Q item 1):", [x["why"] for x in rm if (x["quarter"], x["item"]) == ("2023.4Q", 1)][0][:1200])
print("lineage:", json.dumps(lineage[0], ensure_ascii=False))
