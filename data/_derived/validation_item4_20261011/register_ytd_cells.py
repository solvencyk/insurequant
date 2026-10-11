"""Append the 3 owner-approved PL_YTD_COLLAPSE_TO_ZERO cells (owner 2026-10-11 chat) to user_pl_confirmed_cells.json.
Cell-level, guarded: refuses if any key already exists or the file bytes changed since read. CRLF preserved (round-trip verified)."""
import json, sys, hashlib
sys.stdout.reconfigure(encoding="utf-8")
P = "data/_gold/user_pl_confirmed_cells.json"
raw = open(P, "rb").read()
d = json.loads(raw.decode("utf-8"))
prop = json.load(open("data/_derived/bspl_granularity_20261011/proposed_owner_confirmed_cells_ytd_collapse.json", encoding="utf-8"))
APPROVED = "owner 2026-10-11 (채팅 승인: 「법인세는 네 제안대로 승인」, 법인세 0 은 원문에 0 으로 인쇄된 것으로 처리)"
have = {(c["master"], c["company"], c["quarter"], c["item"]) for c in d["cells"]}
new = []
for c in prop["cells"]:
    k = (c["master"], c["company"], c["quarter"], c["item"])
    assert k not in have, k
    c = dict(c)
    c["approved"] = APPROVED
    c["note"] = c["note"].replace("근거: data/disclosure/_meta/bspl_granularity_runlog.md",
        "원문(위 verify.file)을 validation 이 2026-10-11 다시 열어 인쇄값·마커 재확인(게이트가 매 실행 재확인). 등재는 이 셀(법인세 0.0)만이다 -- 값이 바뀌거나 인용 문구가 사라지면 PL_YTD_COLLAPSE_TO_ZERO RED 가 돌아온다. 근거: data/disclosure/_meta/bspl_granularity_runlog.md")
    new.append(c)
assert len(new) == 3
d["cells"] = d["cells"] + new
assert open(P, "rb").read() == raw
out = (json.dumps(d, ensure_ascii=False, indent=2) + "\n").replace("\n", "\r\n")
open(P, "wb").write(out.encode("utf-8"))
chk = json.loads(open(P, "rb").read().decode("utf-8"))
print("cells", len(chk["cells"]), "ytd-rule cells:", [(c["company"], c["quarter"], c["item"]) for c in chk["cells"] if c.get("rule") == "PL_YTD_COLLAPSE_TO_ZERO"])
