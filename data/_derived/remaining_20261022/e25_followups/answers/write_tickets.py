# -*- coding: utf-8 -*-
"""Insert the answers into the five ticket files (UTF-8, LF, no BOM) and set status: answered.  Each ticket must still be in its original state (status: open)."""
from pathlib import Path
R = Path("C:/Users/sangwook.cho/Desktop/insurequant/inbox/parser")
A = Path("C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e25_followups/answers")
HEAD = "## 답변 (recipient 작성 — 처리 후)"
jobs = [
    ("20261023T1130Z__validation__KR0099__2023.1Q__kblife_reinsurance_subitems_9_11_12_stale.md", "kr0099_kblife.md"),
    ("20261023T1210Z__validation__KR0070__2023.1Q-2023.4Q__abl_items_5_9_10_old_vintage_and_wrong_leg.md", "kr0070_abl.md"),
    ("20261023T0600Z__validation__KR0104__2024.1Q-2024.3Q__nh_life_17_20_21_vintage_gap.md", "kr0104_nhlife.md"),
    ("20261024T0100Z__orchestrator__KR0010__2024.4Q-2025.4Q__kbsonbo_item16_cumulative_impossible.md", "kr0010_kbsonbo.md"),
    ("20261023T1215Z__validation__KR0099-KR0003__2023.4Q__single_quarter_vintage_seam_not_blanked.md", "kr0003_lotte_csm.md"),
]
for tname, aname in jobs:
    p = R / tname
    raw = p.read_bytes()
    assert not raw.startswith(b"\xef\xbb\xbf") and b"\r\n" not in raw
    s = raw.decode("utf-8")
    ans = (A / aname).read_text(encoding="utf-8").strip("\n")
    assert s.count("\nstatus: open\n") == 1, tname
    s = s.replace("\nstatus: open\n", "\nstatus: answered\n", 1)
    if HEAD in s:
        i = s.index(HEAD) + len(HEAD)
        rest = s[i:]
        if rest.strip() in ("", "(처리 전)"):
            s = s[:i] + "\n\n" + ans + "\n"
        elif rest.lstrip().startswith("(처리 전)"):          # 1215Z: keep the orchestrator memo that follows
            k = rest.index("(처리 전)") + len("(처리 전)")
            s = s[:i] + "\n\n" + ans + "\n" + rest[k:]
        else:
            raise SystemExit(f"unexpected answer section content in {tname}: {rest[:80]!r}")
    else:
        s = s.rstrip("\n") + "\n\n" + HEAD + "\n\n" + ans + "\n"
    p.write_bytes(s.encode("utf-8"))
    print("updated", tname, len(s))
