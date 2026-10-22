# -*- coding: utf-8 -*-
"""Read-only. Real build_root_masters.build_pl() on a temp copy (scratchpad) with the LIVE gold: which KR0104 cells does a fresh build disagree with in the live master (pre-existing drift)?"""
import json, sys
from pathlib import Path
ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
SCR = Path("C:/Users/sangwook.cho/AppData/Local/Temp/claude/C--Users-sangwook-cho-Desktop-insurequant/429689e1-5ae3-4467-ae2a-745748238c8b/scratchpad/e19_kr0104")
SCR.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(ROOT / "data/_derived/kyobo_pl_restate_dryrun_20261021"))
import sim_pl_builder as S
sys.stdout.reconfigure(encoding="utf-8")
CODE = "KR0104"
sim, n = S.simulate(ROOT / "data/_gold/user_pl_cells.json", SCR / "tmp_baseline.json")
live = json.loads((ROOT / "PL_breakdown.json").read_text(encoding="utf-8"))
sb = {S.key(r): r for r in sim}
L, drift_other = [], 0
for r in live:
    s = sb[S.key(r)]
    if (r.get("값"), r.get("값_당분기")) != (s.get("값"), s.get("값_당분기")):
        if r["원보험사코드"] == CODE:
            L.append(f"KR0104 {r['공시분기']} i{r['항목번호']:>2} live 값={r.get('값')} 당분기={r.get('값_당분기')}   fresh-build 값={s.get('값')} 당분기={s.get('값_당분기')}")
        else:
            drift_other += 1
L.insert(0, f"rows live={len(live)} sim={len(sim)}; KR0104 cells where a fresh build_pl() != live: {len(L)}; other-company drift cells: {drift_other}")
(Path(__file__).resolve().parent / "KR0104_sim_baseline.txt").write_text("\n".join(L) + "\n", encoding="utf-8")
Path(SCR / "tmp_baseline.json").unlink(missing_ok=True)
print(L[0])
