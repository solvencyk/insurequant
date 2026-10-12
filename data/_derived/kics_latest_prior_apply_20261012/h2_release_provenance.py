"""h2_release_provenance.py [--apply] -- mark the two released pins' records in data/_gold/kics_exemption_provenance.json as CONTRADICTED
(the repository's release convention: keep the record so a re-registration of the same (registry, company, quarter) is an immediate RED).

Only status + refuted_by + resolved_note of exactly two entries change.  Canonical byte format is asserted first (indent=2, CRLF, trailing CRLF).
"""
import copy
import json
import sys

sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/kics_latest_prior_apply_20261012")
from lib_apply import *  # noqa: F401,F403,E402

utf8_stdout()
P = REPO / "data" / "_gold" / "kics_exemption_provenance.json"
apply = "--apply" in sys.argv
raw = P.read_bytes()
d = json.loads(raw.decode("utf-8"))


def dump(x) -> bytes:
    return (json.dumps(x, ensure_ascii=False, indent=2).replace("\n", "\r\n") + "\r\n").encode("utf-8")


assert dump(d) == raw, "provenance ledger is not in the canonical byte format - refusing (would rewrite every line)"
print(f"provenance ledger sha {sha_bytes(raw)[:12]} entries {len(d['entries'])}")

REFUTED = ("owner 2026-10-12 (티켓 inbox/parser/20261012T2200Z, parser-kics 최신 공시 직전 컬럼 채택 적용). 후속 공시 두 곳이 같은 칸을 같은 값으로 인쇄해 "
           "룰이 닫힌다 - 발행사 자기모순이 아니라 이후 공시의 정정이었다. 근거 쪽 · 직접 확인 기록 = data/_derived/kics_latest_prior_apply_20261012/applied_blocks.csv.")
NOTES = {
    ("KR0003", "2025.1Q"): ("2026-10-12 해제. 등재 전제('헤드라인표의 Ⅲ.재분류항목 19,202 만 나머지 행과 1,205억 어긋난다')는 마스터가 자기 공시 인쇄를 옮긴 상태에서만 참이었다. "
                            "FY2025_Q2 p20(당분기-1분기 열)과 FY2025_Q3 p20(당분기-2분기 열)이 같은 칸을 17,997 로 인쇄하고 15,657 - 8 - 17,997 = -2,348 = 같은 열의 기본자본으로 "
                            "정확히 닫힌다. owner 규칙 '최신 공시 직전 컬럼 채택' 으로 마스터 항목 13 을 19,202 → 17,997 로 바꿨고(`kics_restatement_ledger.json` KR0003|2025.1Q|13 as_restated) "
                            "박제 셀(항목 13)이 움직여 TIER2_EXEMPTION_INPUT_DRIFT · INERT 가 발화하므로 등재를 풀었다. 기록을 지우지 않는 이유: 같은 (회사,분기)가 다시 등재되면 "
                            "status=CONTRADICTED 가 즉시 RED 를 띄운다. owner 판단이 틀렸다는 뜻이 아니다 - 당시에는 그 공시본이 마스터의 as-filed 기준이었다."),
    ("KR0032", "2024.3Q"): ("2026-10-12 해제. 이 항목의 release_condition 이 충족됐다: owner 가 as-restated(FY2024_Q4 p43 의 9,390) 채택을 결정했고(최신 공시 직전 컬럼 채택, 2026-10-12) "
                            "parser 가 항목 13 을 8,867 → 9,390 으로 갈아끼웠다. 후속 공시 둘(FY2024_Q4 p43 직전분기 열 · FY2025_Q1 v20261011 p15 전전분기 열)이 모두 9,390 을 인쇄하고 "
                            "23,478 - 0 - 9,390 = 14,088 ~ 기본자본 14,089(잔차 +1, 반올림)로 닫힌다(`kics_restatement_ledger.json` KR0032|2024.3Q|13 as_restated). "
                            "박제 셀이 움직여 TIER2_EXEMPTION_INPUT_DRIFT · INERT 가 발화하므로 등재를 풀었다. 기록은 재등재 방지용으로 남긴다."),
}
nd = copy.deepcopy(d)
n = 0
for e in nd["entries"]:
    k = (e.get("company"), e.get("quarter"))
    if e.get("registry") == "_TIER2_ISSUER_INCONSISTENT" and k in NOTES:
        assert e.get("status") == "VERIFIED", (k, e.get("status"))
        e["status"] = "CONTRADICTED"
        e["refuted_by"] = REFUTED
        e["resolved_note"] = NOTES[k]
        n += 1
assert n == 2, n
new_raw = dump(nd)
chk = json.loads(new_raw.decode("utf-8"))
changed = [(i, k) for i, (a, b) in enumerate(zip(d["entries"], chk["entries"])) for k in set(a) | set(b) if a.get(k) != b.get(k)]
assert sorted({k for _i, k in changed}) == ["refuted_by", "resolved_note", "status"], changed
assert len({i for i, _k in changed}) == 2 and {k: v for k, v in d.items() if k != "entries"} == {k: v for k, v in chk.items() if k != "entries"}
print(f"verified: 2 entries changed (status, refuted_by, resolved_note); bytes {len(raw)} -> {len(new_raw)}")
if not apply:
    print("dry run: nothing written")
    sys.exit(0)
assert sha_file(P) == sha_bytes(raw), "ledger changed while preparing"
tmp = P.with_name(P.name + ".latestprior.tmp")
tmp.write_bytes(new_raw)
atomic_replace(tmp, P)
assert sha_file(P) == sha_bytes(new_raw)
print("WROTE", P.relative_to(REPO), "sha", sha_file(P)[:12])
