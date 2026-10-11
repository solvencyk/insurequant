# -*- coding: utf-8 -*-
"""Step 96 (in memory only): what the gates would say if the two held old-basis quarters (2023.1Q, 2023.2Q) were loaded.
Uses validate_csm_continuity.check_company on KR0074's rows (master + held rows); nothing is written."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
W = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.stdout.reconfigure(encoding="utf-8")
import validate_csm_continuity as V  # noqa: E402

wf = json.loads((ROOT / "CSM_waterfall.json").read_text(encoding="utf-8"))
held = json.loads((W / "held_rows_waterfall.json").read_text(encoding="utf-8"))["rows"]


def co_data(rows):
    d = {}
    for r in rows:
        if r["원보험사코드"] == "KR0074":
            d.setdefault(r["공시분기"], {})[r["항목번호"]] = r.get("값")
    return d


now = V.check_company(co_data(wf), "라이나생명보험")
sim = V.check_company(co_data(wf + held), "라이나생명보험")
print("continuity findings now (without the held quarters):", now)
print("continuity findings if the held old-basis quarters were loaded:")
for f in sim:
    print("  ", f["severity"], f["rule"], f["detail"])
