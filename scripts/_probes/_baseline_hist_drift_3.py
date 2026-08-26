#!/usr/bin/env python3
"""csm_waterfall_history 정적 스냅샷 drift 3건 등재 (기존 919건과 같은 class)."""
import sys, json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.stdout.reconfigure(encoding="utf-8")
P = ROOT / "data/_gold/live_artifact_baseline.json"
d = json.loads(P.read_text(encoding="utf-8"))
ent = d["entries"]
REASON = ("정적 스냅샷 drift. 이 파일의 선언 빌더(scripts/ifrs17_batch_historical.py, 파일 source "
          "필드)는 2026-06 에 아카이브돼 아무도 재생성하지 않는다 — 마스터가 백필·정정될 때마다 "
          "벌어진다(같은 class 919건 기등재). IFRS17.html:1523 이 이 파일을 stale 로 폐기했고 "
          "배포 HTML 어느 것도 fetch 하지 않는다. 이번 3건의 원인: 2026-08-26 별도기준 정정 "
          "(inbox/parser/20260826T0500Z·0730Z) — 2023.2Q/3Q interest 는 환율변동효과 가산이 "
          "diag 재생성으로 산출에 실린 몫, 2023.4Q amortization 은 연결→별도 정정분(−13,842.8 "
          "= 연결 _00761 값, −13,676.7 = 별도 _00760 값). 마스터 쪽이 옳다.")
NEW = {
    "csm_waterfall_history.json|HIST_MASTER_DRIFT|삼성생명보험|2023.2Q|interest":
        "snapshot=878.7 vs master=900.2 (Δ=-21.5 억원)",
    "csm_waterfall_history.json|HIST_MASTER_DRIFT|삼성생명보험|2023.3Q|interest":
        "snapshot=2,934.3 vs master=2,969.2 (Δ=-34.9 억원)",
    "csm_waterfall_history.json|HIST_MASTER_DRIFT|삼성생명보험|2023.4Q|amortization":
        "snapshot=-13,842.8 vs master=-13,676.7 (Δ=-166.0 억원)",
}
n = 0
for k, detail in NEW.items():
    if k in ent:
        print("  이미 등재:", k); continue
    ent[k] = {"detail": detail, "reason": REASON, "first_seen": "2026-08-26",
              "route": "owner (파일 거취 미결: 아카이브 유지 vs 삭제)"}
    n += 1
    print("  + ", k)
if isinstance(d.get("_counts"), dict):
    d["_counts"]["entries"] = len([k for k in ent if not k.startswith("_")])
P.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"{n}건 등재, 총 {len([k for k in ent if not k.startswith('_')])}건")
