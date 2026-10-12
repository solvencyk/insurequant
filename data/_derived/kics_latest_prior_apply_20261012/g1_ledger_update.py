"""g1_ledger_update.py [--apply] -- register the ticket's restatement-class cells in data/_gold/kics_restatement_ledger.json as
adopted_basis="as_restated" (owner 2026-10-12 'latest prior column') + record the decision in `_policy_decisions`.

Only class-R primary cells (own filing prints the old master value, the two later filings print the new one) are registered: that is
exactly the ledger's meaning (as_filed vs restated).  Class C / T cells (the master held a derived or mis-read number, the new value IS the
own filing's print / the own filing has a typo) are NOT restatements and stay out of the ledger.

Guards: the current ledger bytes must round-trip through json.dumps(indent=2)+CRLF (no trailing newline) so only the planned entries differ;
every as_filed value must equal the master's pre-change value (plan `old`) and every restated value the plan `new`; keys must not exist yet.
Write = temp file in the same folder + os.replace.  Without --apply: full verification, nothing written.
"""
import copy
import json
import sys
from pathlib import Path

sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/kics_latest_prior_apply_20261012")
from lib_apply import *  # noqa: F401,F403,E402

utf8_stdout()
LEDGER = REPO / "data" / "_gold" / "kics_restatement_ledger.json"
apply = "--apply" in sys.argv

raw = LEDGER.read_bytes()
assert not raw.startswith(b"\xef\xbb\xbf")
led = json.loads(raw.decode("utf-8"))


def dump(d) -> bytes:
    return json.dumps(d, ensure_ascii=False, indent=2).replace("\n", "\r\n").encode("utf-8")


assert dump(led) == raw, "ledger is not in the canonical byte format (indent=2, CRLF, no trailing newline) - refusing"
print(f"ledger sha {sha_bytes(raw)[:12]} entries {len(led['entries'])}")

CLOSURE = {  # hand-written 'why this is certain' notes for the blocks where an identity of the SAME printed column closes exactly
    "KR0003_2025.1Q": "같은 열의 기본자본 (2,348) = 순자산 15,657 - 불인정 8 - 재분류 17,997 로 정확히 닫힌다(자기 공시의 19,202 는 닫히지 않는다: -3,553).",
    "KR0032_2024.3Q": "같은 열의 기본자본 14,089 ~ 순자산 23,478 - 불인정 0 - 재분류 9,390 = 14,088(반올림 1). 자기 공시의 8,867 은 522 어긋났다.",
    "KR0050_2025.3Q": "같은 열의 기본자본 378 = 순자산 4,987 - 불인정 0 - 재분류 4,609 로 정확히 닫힌다(자기 공시의 4,608 은 379).",
    "KR0072_2025.2Q": "후속 공시 TFI 표의 보완자본 한도초과분(item47-48 = 327.68억)이 불인정 328 과 일치하고 같은 열의 기본자본 -5,954 = 순자산 1,542 - (328 - 327.68) - 재분류 7,496 으로 닫힌다.",
    "KR0009_2023.1Q": "재작성 열이 자기 안에서 닫힌다: 순자산 127,214 = 구성 6행 합 127,214, 지급여력금액 133,381 = 기본자본 68,456 + 보완자본 64,925 (자기 공시 열은 순자산 127,231 vs 구성 합 127,232).",
    "KR0004_2023.1Q": "지급여력금액·기본자본·보완자본·순자산 헤드라인은 두 판 모두 같고(6,774 · 4,384 · 2,390 · 5,890) 순자산 구성(보통주 · 자본증권 · 조정준비금)만 다시 인쇄됐다. 후속 공시 둘이 같은 값을 인쇄한다.",
}
DECISION = {
    "date": "2026-10-12", "by": "owner",
    "scope": "최신 공시 직전 컬럼 채택 - 드라이런(data/_derived/kics_latest_prior_precedence_dryrun_20261012) 채택 후보 26블록 중 확실 기준을 통과한 16블록(적용 65칸)에서 재작성으로 확인된 적용전 28칸(11블록)",
    "decision": "as_restated 채택 (후속 공시 둘이 같은 값을 인쇄하고 검산이 다 닫히는 칸만)",
    "quote": "생각보다 바꿀 값이 많지는 않네? 최신 공시 직전 값이 검산이 다 닫히는 게 확실한 애들만 덮어써라",
    "note": ("전면 정책 변경이 아니다. 기본값은 as_filed 그대로이고 이 결정은 건별 채택이다(앞선 교보 2026.1Q 와 같은 방식). "
             "보류한 72블록(드라이런 범주 완전성 부족 · 룰 사각 · gold 충돌 · 현행 유지 · 둘 다 실패, 채택 후보 중 후속 공시 두 곳의 인쇄가 그 칸에서 어긋난 9블록, "
             "recalc_kics_derived 가 되돌리는 1블록)은 as_filed 그대로다. 마스터 값이 자기 공시 인쇄와 이미 다른 5칸(C/T 류)은 재작성이 아니라 "
             "인쇄값 정정이라 이 장부에 올리지 않았다. 계획 · 근거 쪽 · 되돌리는 값(옛값) = data/_derived/kics_latest_prior_apply_20261012/plans/*.json, applied_blocks.csv"),
}

new_entries = {}
for bid in APPLIED:
    plan = load_plan(bid)
    code, q = plan["code"], plan["quarter"]
    prim = {e["item"]: e for e in plan["edits"] if e["kind"] == "primary"}
    n_post = sum(1 for e in plan["edits"] if e["kind"] == "post_mirror")
    n_der = sum(1 for e in plan["edits"] if e["kind"] == "derived_ratio")
    for ev in plan["evidence"]:
        if ev["class"] != "R":
            continue
        it = ev["item"]
        e = prim[it]
        old, new = float(e["old"]), float(e["new"])
        own = ev["own_src"].split(" [")[0]
        f1 = (ev["f1_src"] or "").replace(" (prev col)", " (직전분기 열)")
        f2 = (ev["f2_src"] or "").replace(" (prev2 col)", " (전전분기 열)")
        viewed = plan.get("viewed_pages") or []
        k = f"{code}|{q}|{it}"
        assert k not in led["entries"] and k not in new_entries, k
        new_entries[k] = {
            "company": code, "company_name": plan["company"], "quarter": q, "item": it,
            "as_filed": old, "restated": new, "delta": new - old,
            "as_filed_source": "data/disclosure/" + own,
            "restated_source": " · ".join("data/disclosure/" + s for s in (f1, f2) if s),
            "method": "pdf_text/pdf_text" + (" + 렌더링 육안 판독(" + ", ".join(viewed) + ")" if viewed else ""),
            "issuer_reason": ("발행사 정정 사유 미기재. 후속 공시 두 곳이 같은 값을 인쇄한다: "
                              f"자기 공시 {ev['own_print']} → 직전분기 열 {ev['f1_print']} · 전전분기 열 {ev['f2_print']}"
                              + (" . " + CLOSURE[bid] if bid in CLOSURE else "")),
            "detected_by": "parser-kics 2026-10-12 최신 공시 직전 컬럼 우선 드라이런(data/_derived/kics_latest_prior_precedence_dryrun_20261012/block_verdicts.csv)",
            "adopted_basis": "as_restated",
            "adopted_by": "owner 2026-10-12",
            "adopted_reason": ("owner 결정 2026-10-12: 「생각보다 바꿀 값이 많지는 않네? 최신 공시 직전 값이 검산이 다 닫히는 게 확실한 애들만 덮어써라」. "
                               "이 블록은 확실 기준(룰 · 이웃 분기 · 다른 게이트 축 새 RED 0 / 완전성 문제 없음 / 주의 표시 칸은 원본 PDF 직접 확인 / 후속 공시 두 곳의 인쇄가 그 칸에서 일치)을 "
                               "모두 통과했다. 적용 계획 data/_derived/kics_latest_prior_apply_20261012/plans/" + bid + ".json (옛값 = 되돌리는 값)."),
            "adopted_scope": (f"적용전(`값`) 칸. 같은 블록의 적용후 미러 {n_post}칸(전=후이던 칸) · 파생 지급여력비율/기본자본비율(item27·28) {n_der}칸은 같은 계획에서 함께 갱신했다. "
                              "경과조치 적용사의 적용후 열은 후속 공시가 싣지 않는 칸이라 독립 값이 있는 칸은 이 계획에 넣지 않았다(그런 블록은 보류)."),
        }

print("new ledger entries:", len(new_entries), "(class R primary cells)")
new_led = copy.deepcopy(led)
new_led["entries"].update(new_entries)
dec = new_led.setdefault("_policy_decisions", [])
assert not any(d.get("date") == "2026-10-12" for d in dec), "decision already recorded"
dec.append(DECISION)
new_raw = dump(new_led)

# verification: only the planned entries + one decision were added; everything else byte-for-byte equal
chk = json.loads(new_raw.decode("utf-8"))
assert {k: v for k, v in chk["entries"].items() if k not in new_entries} == led["entries"]
assert {k: v for k, v in chk.items() if k not in ("entries", "_policy_decisions")} == {k: v for k, v in led.items() if k not in ("entries", "_policy_decisions")}
assert chk["_policy_decisions"][:-1] == led.get("_policy_decisions", [])
# as_filed / restated vs plans
for k, v in new_entries.items():
    code, q, it = k.split("|")
    plan = load_plan(f"{code}_{q}")
    e = [x for x in plan["edits"] if x["kind"] == "primary" and x["item"] == int(it)][0]
    assert float(e["old"]) == v["as_filed"] and float(e["new"]) == v["restated"], k
print(f"verified; ledger bytes {len(raw)} -> {len(new_raw)}")
if not apply:
    print("dry run: nothing written")
    sys.exit(0)
assert sha_file(LEDGER) == sha_bytes(raw), "ledger changed while preparing"
tmp = LEDGER.with_name(LEDGER.name + ".latestprior.tmp")
tmp.write_bytes(new_raw)
atomic_replace(tmp, LEDGER)
assert sha_file(LEDGER) == sha_bytes(new_raw)
print("WROTE", LEDGER.relative_to(REPO), "sha", sha_file(LEDGER)[:12], "entries", len(chk["entries"]))
