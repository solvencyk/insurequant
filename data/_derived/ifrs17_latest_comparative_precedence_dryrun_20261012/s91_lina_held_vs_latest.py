"""Read-only: Lina held 2023.1Q/2Q rows (old basis, csm_backfill_lina_20261011) vs the LATEST comparative prints (FY2024_Q1 p52 / FY2024_Q2 p77) in 억원, and what the strict WFY rule would say."""
from __future__ import annotations

import json
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
held = json.loads((ROOT / "data/_derived/csm_backfill_lina_20261011/held_rows_waterfall.json").read_text(encoding="utf-8"))
probe = json.loads((HERE / "lina_csm_probe2.json").read_text(encoding="utf-8"))
latest = {"2023.1Q": probe["FY2024_Q1"]["tables"][1]["csm_eok"], "2023.2Q": probe["FY2024_Q2"]["tables"][1]["csm_eok"]}
src = {"2023.1Q": "FY2024_Q1 p52 (전분기)", "2023.2Q": "FY2024_Q2 p77 (전반기)"}
keys = ["open", "new", "fin", "adj", "amort", "close"]            # waterfall items 1..6
H = {}
for r in held["rows"]:
    H.setdefault(r["공시분기"], {})[r["항목번호"]] = r["값"]
master = {r["항목번호"]: r["값"] for r in json.loads((ROOT / "CSM_waterfall.json").read_text(encoding="utf-8")) if r["원보험사코드"] == "KR0074" and r["공시분기"] == "2023.4Q"}
out = {}
for q in ("2023.1Q", "2023.2Q"):
    h = [H.get(q, {}).get(i) for i in range(1, 7)]
    lv = [latest[q][k] for k in keys]
    same = all(a is not None and abs(a - b) <= 0.0005 for a, b in zip(h, lv))
    print(q, "held(old basis)  :", h)
    print(q, "latest comparative:", lv, "|", src[q])
    print(q, "held == latest comparative:", same)
    print(q, "opening vs master 2023.4Q opening:", lv[0], "vs", master.get(1), "-> diff", round(lv[0] - master.get(1), 4), "(WFY threshold max(0.5%*max, 2억) =", round(max(0.005 * max(lv[0], master.get(1)), 2.0), 2), ")")
    out[q] = {"held": h, "latest_comparative": lv, "source": src[q], "held_equals_latest": same,
              "opening_vs_master_2023_4Q": [lv[0], master.get(1)], "wfy_would_fire": abs(lv[0] - master.get(1)) > max(0.005 * max(lv[0], master.get(1)), 2.0)}
(HERE / "lina_feasibility.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
