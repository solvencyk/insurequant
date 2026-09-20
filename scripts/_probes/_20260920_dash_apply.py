#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Record the PRINTED_DASH adjudication in the backfill staging file.

Does NOT change any 값: the 27 in-scope dashes were already promoted to 0 by the extractor
on the strength of E6 alone.  This re-states the evidence on the three axes actually
measured (scripts/_probes/_20260920_dash_adjudicate.py) so the promotion is auditable, and
pins the 2 out-of-scope KR0004 cells as not-merged.  Content is built in full and written
once at the end (never open("w") before the content exists)."""
import io
import json
import sys
from collections import Counter
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "data/_derived/pl_backfill_disclosure_20260918.json"
ADJ = ROOT / "data/_derived/_probe_20260920_dash_adjudication.json"

stg = json.loads(SRC.read_text(encoding="utf-8"))
adj = {(a["code"], a["quarter"], a["item"]): a
       for a in json.loads(ADJ.read_text(encoding="utf-8"))}
BF = set(stg["backfill_item_numbers"])

touched, stat, before_vals = 0, Counter(), {}
for c in stg["cells"]:
    code, q = c.get("원보험사코드"), c.get("공시분기")
    for k, it in (c.get("items") or {}).items():
        n = int(k)
        if it.get("dash_state") != "PRINTED_DASH" or n not in BF:
            continue
        a = adj.get((code, q, n))
        if not a:
            print(f"  !! no adjudication row for {code} {q} #{n}")
            continue
        before_vals[(code, q, n)] = it.get("값")
        axes = []
        if a["A_self_closure"]:
            axes.append(f"A 자기폐쇄: 같은 표의 세전이익({a['세전_억']:g}억)과 "
                        f"당기순이익({a['순이익_억']:g}억)이 동일 → 발행사 표 자체가 법인세=0 을 "
                        f"진술. E6 diff=0.0억(허용 2.5억), 이 표의 유일한 대시")
        dart = a["B_dart_4Q_tax_백만원"]
        if dart:
            zs = [k2 for k2, v in sorted(dart.items()) if abs(v) < 1e-9]
            nz = [f"{k2}={v:g}" for k2, v in sorted(dart.items()) if abs(v) >= 1e-9]
            axes.append("B 독립원천(DART 연간 마스터 #23): " +
                        (f"0인 연도 {', '.join(zs)}" if zs else "0인 연도 없음") +
                        (f" / 0이 아닌 연도 {', '.join(nz)} (연말 일괄인식분)" if nz else ""))
        if a["C_lossmaker"]:
            axes.append(f"C 결손: 당기순이익 {a['순이익_억']:g}억 (적자) — 당기 법인세 부담 없음이 "
                        f"구조적으로 성립. 같은 회사 대시 연속 {len([1 for kk in adj if kk[0]==code])}분기")
        if a["backfill_excluded"]:
            it["dash_promotion"] = {
                "promoted": False,
                "merged": False,
                "evidence": ("KR0004 는 경영공시↔DART 범위 불일치 규명 전까지 백필 제외"
                             "(validation 20260918T0700Z §B). 증거축은 충족하나 이 라운드에서 "
                             "병합하지 않는다: " + " | ".join(axes)),
                "adjudicated": "20260920 parser-ifrs17",
            }
            stat["out_of_scope_KR0004"] += 1
        else:
            verdict = "0" if a["A_self_closure"] and len(axes) >= 2 else None
            it["dash_promotion"] = {
                "promoted": verdict == "0",
                "promoted_to": 0.0 if verdict == "0" else None,
                "evidence": " | ".join(axes),
                "adjudicated": "20260920 parser-ifrs17",
            }
            if verdict != "0":
                it["값"], it["값_억원"] = None, None
                stat["demoted_to_null"] += 1
            else:
                stat["promoted_zero"] += 1
        touched += 1

stg["dash_adjudication"] = {
    "date": "20260920",
    "by": "parser-ifrs17",
    "scope": "backfill_item_numbers 5개 항목의 dash_state=PRINTED_DASH 전건",
    "policy": ("기본값 null. 승격은 A(자기폐쇄: 세전=순이익) + 최소 1개 독립축(B DART 연간 0 / "
               "C 결손사) 을 모두 만족할 때만. 근거는 셀의 dash_promotion.evidence 에 박제."),
    "result": dict(stat),
    "note": ("전건이 item23 법인세였다. 값은 이번 판정으로 바뀌지 않았다 — 추출기가 이미 E6 "
             "단독 근거로 0 승격해 둔 것을 3축으로 재검증하고 근거를 교체했다. "
             "KR0004 2칸은 회사 단위 보류(§B)라 병합대상이 아니다."),
    "probe": "scripts/_probes/_20260920_dash_adjudicate.py",
}

after = json.dumps(stg, ensure_ascii=False, indent=1)
with open(SRC, "w", encoding="utf-8", newline="\n") as fh:
    fh.write(after)
print(f"touched dash items = {touched}   {dict(stat)}")
print("값 changed =", sum(1 for c in stg["cells"] for k, it in (c.get('items') or {}).items()
                        if (c.get('원보험사코드'), c.get('공시분기'), int(k)) in before_vals
                        and it.get('값') != before_vals[(c.get('원보험사코드'),
                                                        c.get('공시분기'), int(k))]))
print(f"wrote {SRC.relative_to(ROOT)}")
