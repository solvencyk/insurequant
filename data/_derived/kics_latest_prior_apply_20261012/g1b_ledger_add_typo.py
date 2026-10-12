"""g1b_ledger_add_typo.py [--apply] -- add the one class-T cell (KR0003 2023.4Q item 4) to the restatement ledger and correct my own 2026-10-12 decision text.

Why: the scratch rebuild (j1_repro_scratch.py) showed that an explicit fill_period refill of FY2023_Q4 writes the issuer's own typo 2,481 into that cell (neither the old
master value 24,808 nor the new 24,807).  The ledger semantics fit exactly: as_filed = what the issuer printed in its own filing (2,481), restated = what both later
filings print (24,807); a regression to 2,481 is then an immediate RED (KICS_RESTATEMENT_MASTER_REVERTED_TO_FILED).  The 4 class-C cells (own filing already prints the
new value) stay out of the ledger.

Guards: ledger bytes must round-trip in the canonical format; exactly one new key; the 28 entries written by g1_ledger_update.py are unchanged; only the `scope`
and `note` of the single 2026-10-12 decision record are rewritten.
"""
import copy
import json
import sys

sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/kics_latest_prior_apply_20261012")
from lib_apply import *  # noqa: F401,F403,E402

utf8_stdout()
LEDGER = REPO / "data" / "_gold" / "kics_restatement_ledger.json"
apply = "--apply" in sys.argv
raw = LEDGER.read_bytes()
led = json.loads(raw.decode("utf-8"))


def dump(d) -> bytes:
    return json.dumps(d, ensure_ascii=False, indent=2).replace("\n", "\r\n").encode("utf-8")


assert dump(led) == raw, "ledger is not in the canonical byte format - refusing"
plan = load_plan("KR0003_2023.4Q")
ev = [e for e in plan["evidence"] if e["item"] == 4][0]
edit = [e for e in plan["edits"] if e["kind"] == "primary" and e["item"] == 4][0]
assert ev["class"] == "T" and ev["own_print"] == 2481 and float(edit["new"]) == 24807.0 and float(edit["old"]) == 24808.0
key_ = "KR0003|2023.4Q|4"
assert key_ not in led["entries"]
n_before = len(led["entries"])
new = copy.deepcopy(led)
f1 = ev["f1_src"].replace(" (prev col)", " (직전분기 열)")
f2 = ev["f2_src"].replace(" (prev2 col)", " (전전분기 열)")
new["entries"][key_] = {
    "company": "KR0003", "company_name": plan["company"], "quarter": "2023.4Q", "item": 4,
    "as_filed": 2481.0, "restated": 24807.0, "delta": 24807.0 - 2481.0,
    "as_filed_source": "data/disclosure/FY2023_Q4/raw/KR0003_롯데손해보험_amended.pdf p41",
    "restated_source": f"data/disclosure/{f1} · data/disclosure/{f2}",
    "method": "pdf_text/pdf_text + 렌더링 육안 판독(FY2023_Q4(amended) p41)",
    "issuer_reason": ("발행사 자기 공시의 활자 오류: FY2023_Q4(amended) p41 [경과조치 적용 전 지급여력비율 세부]가 Ⅰ.순자산 23.4Q 를 2,481 로 인쇄한다(같은 표의 구성 6행 합 6,390+454+3,804+503+1,412+12,245 = 24,808, "
                      "기본자본 5,514 = 24,807 - 31 - 19,262 로 닫힘). 후속 공시 두 곳이 24,807 을 인쇄한다(직전분기 열 · 전전분기 열). 마스터는 종전에 구성행 합 24,808 을 싣고 있었다(자기 공시의 2,481 도, 후속 공시의 24,807 도 아님)."),
    "detected_by": "parser-kics 2026-10-12 최신 공시 직전 컬럼 우선 드라이런(data/_derived/kics_latest_prior_precedence_dryrun_20261012/block_verdicts.csv) + 재빌드 시뮬레이션(fill_period 재실행이 2,481 을 되살린다)",
    "adopted_basis": "as_restated",
    "adopted_by": "owner 2026-10-12",
    "adopted_reason": ("owner 결정 2026-10-12: 「생각보다 바꿀 값이 많지는 않네? 최신 공시 직전 값이 검산이 다 닫히는 게 확실한 애들만 덮어써라」. 이 블록은 확실 기준을 모두 통과했다. "
                       "적용 계획 data/_derived/kics_latest_prior_apply_20261012/plans/KR0003_2023.4Q.json (옛값 24,808 = 되돌리는 값)."),
    "adopted_scope": "적용전(`값`) 항목 4 한 칸. 이 칸의 적용후는 마스터에 없고 파생 비율(27 · 28)은 입력(항목 1 · 2 · 14)이 안 바뀌어 그대로다.",
}
dec = new["_policy_decisions"][-1]
assert dec["date"] == "2026-10-12" and dec["by"] == "owner"
dec["scope"] = ("최신 공시 직전 컬럼 채택 - 드라이런(data/_derived/kics_latest_prior_precedence_dryrun_20261012) 채택 후보 26블록 중 확실 기준을 통과한 16블록(적용 65칸)에서 "
                "재작성(R 28칸) 또는 발행사 활자 오류 정정(T 1칸)으로 확인된 적용전 29칸(12블록)")
dec["note"] = dec["note"].replace(
    "마스터 값이 자기 공시 인쇄와 이미 다른 5칸(C/T 류)은 재작성이 아니라 인쇄값 정정이라 이 장부에 올리지 않았다.",
    "마스터 값이 자기 공시 인쇄와 이미 달랐던 4칸(C 류: 악사 2025.1Q 항목 3 · 악사 2026.1Q 항목 4 · 흥국생명 2024.4Q 항목 4 · AIA 2026.1Q 항목 3, 새 값 = 자기 공시 인쇄)은 "
    "재작성이 아니라 인쇄값 정정이라 이 장부에 올리지 않았다. 롯데손해 2023.4Q 항목 4(T 류)는 자기 공시의 활자 오류 2,481 이 재빌드 때 되살아나므로 2,481 을 as_filed 로 올렸다.")
assert "C 류" in dec["note"]
new_raw = dump(new)
chk = json.loads(new_raw.decode("utf-8"))
assert len(chk["entries"]) == n_before + 1
assert {k: v for k, v in chk["entries"].items() if k != key_} == led["entries"]
assert {k: v for k, v in chk.items() if k not in ("entries", "_policy_decisions")} == {k: v for k, v in led.items() if k not in ("entries", "_policy_decisions")}
assert chk["_policy_decisions"][:-1] == led["_policy_decisions"][:-1]
print(f"verified: +1 entry ({key_}), decision text updated; entries {n_before} -> {len(chk['entries'])}; bytes {len(raw)} -> {len(new_raw)}")
if not apply:
    print("dry run: nothing written")
    sys.exit(0)
assert sha_file(LEDGER) == sha_bytes(raw)
tmp = LEDGER.with_name(LEDGER.name + ".latestprior.tmp")
tmp.write_bytes(new_raw)
atomic_replace(tmp, LEDGER)
assert sha_file(LEDGER) == sha_bytes(new_raw)
print("WROTE", LEDGER.relative_to(REPO), "sha", sha_file(LEDGER)[:12], "entries", len(chk["entries"]))
