import sys
from pathlib import Path
import json

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))
import fix_20260822_tfi_tier_full_scan as F  # noqa: E402
import fix_20260821_tier2_limit_lines as T2  # noqa: E402

data = json.loads((REPO / "kics_disclosure.json").read_text(encoding="utf-8"))
quarters = sorted({r["공시분기"] for r in data if r["원보험사코드"] == "KR1000"})
existing = {(r["원보험사코드"], r["공시분기"], int(r["항목번호"])) for r in data}
for q in quarters:
    pdf = T2._pdf(T2.q2p(q), "KR1000")
    found, anchor, reason = F.extract_tfi_full(pdf)
    have5051 = ("KR1000", q, 50) in existing
    print(q, "found_items=", sorted(found.keys()), "anchor=", anchor, "reason=", reason,
          "already_has_50=", have5051)
