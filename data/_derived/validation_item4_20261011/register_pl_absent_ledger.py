"""Add the _PL_SOURCE_ABSENT ledger record for KR1104 2025.3Q (owner 2026-10-11) to kics_exemption_provenance.json.
Entry appended at the end; refuses if present; byte round-trip of the untouched part verified."""
import json, sys
sys.stdout.reconfigure(encoding="utf-8")
P = "data/_gold/kics_exemption_provenance.json"
raw = open(P, "rb").read()
d = json.loads(raw.decode("utf-8"))
# detect formatting
for nl in ("\n", "\r\n"):
    for ind in (1, 2, 4):
        out = (json.dumps(d, ensure_ascii=False, indent=ind) + "\n").replace("\n", nl)
        if out.encode("utf-8") == raw:
            FMT = (nl, ind); break
        out2 = json.dumps(d, ensure_ascii=False, indent=ind).replace("\n", nl)
        if out2.encode("utf-8") == raw:
            FMT = (nl, ind, "nofinalnl"); break
    else:
        continue
    break
else:
    raise SystemExit("cannot reproduce file bytes by json.dumps -- refuse to rewrite")
print("format", FMT)
src = [e for e in d["entries"] if e.get("registry") == "_CENSUS_SOURCE_ABSENT" and e["company"] == "KR1104" and e["quarter"] == "2025.3Q"][0]
assert not [e for e in d["entries"] if e.get("registry") == "_PL_SOURCE_ABSENT"]
e = json.loads(json.dumps(src))
e["registry"] = "_PL_SOURCE_ABSENT"
e["claim"] = ("하노버재보험 한국지점 사이트 공시 목록에 2025년 3/4분기 항목이 없다(2025 = 1Q·2Q·4Q). 받을 문서가 없어 "
              "PL_breakdown 에도 이 분기 버킷이 없다 -- PL 의 MASTER_HOLE 은 파싱 결손이 아니라 원천 부재다.")
e["claim_kind"] = "NOT_POSTED"
e["note"] = ("K-ICS 쪽 `_CENSUS_SOURCE_ABSENT` KR1104 2025.3Q 와 같은 사실(문서 자체가 게시되지 않음)이다. 게이트는 별개라 PL 쪽에 "
             "따로 등재한다. 인용은 다운로더 매니페스트(owner 확인 2026-10-09 + downloader 2026-10-10 목록 JSON 파싱, 게시일 "
             "2025-07-02 1Q · 2025-09-01 2Q · 2026-04-08 4Q). validation 2026-10-11 재확인: data/disclosure/FY2025_Q3/raw/ 에 "
             "KR1104 파일 없음, PL_breakdown.json 에 KR1104 2025.3Q 행 0. 회사 사이트 기준의 원천 부재이며 협회 공시 시스템 "
             "직접 확인은 하지 않았다.")
e["registered_by"] = ("owner 승인 2026-10-11 (채팅: 「하노버 25.3q만 예외 승인」) -- validation 이 PL 원천부재 등재부 "
                      "`_PL_SOURCE_ABSENT`(validate_kics_disclosure.py) 로 등재. 읽는 쪽 = coverage_holes(source_absent=) "
                      "(validate_master_tables._check_coverage · validate_data_contract 1c)")
e["scope"] = "PL_breakdown KR1104 2025.3Q 의 coverage MASTER_HOLE(통째) 한 버킷. 다른 분기·회사·항목에는 적용되지 않는다."
d["entries"].append(e)
out = json.dumps(d, ensure_ascii=False, indent=FMT[1])
if len(FMT) == 2:
    out += "\n"
out = out.replace("\n", FMT[0])
assert open(P, "rb").read() == raw
open(P, "wb").write(out.encode("utf-8"))
chk = json.loads(open(P, "rb").read().decode("utf-8"))
print("entries", len(chk["entries"]), [ (x["registry"], x["company"], x["quarter"]) for x in chk["entries"][-2:]])
