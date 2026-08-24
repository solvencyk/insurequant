# -*- coding: utf-8 -*-
"""읽기 전용: verify present_marker 를 등급별로 센다 + 다중출현 마커의 행 라벨 후보를 뽑는다.

등급  LABELLED   숫자 아닌 라벨을 포함 → 행 귀속을 검사할 수 있다
      UNIQUE     숫자만이지만 인용 페이지에서 정확히 1회 → 귀속이 유일성으로 함의된다
      AMBIGUOUS  숫자만인데 2회 이상 → '이 페이지 어딘가 V 가 있다' 만 확인 = 검사처럼 보이는 무검사
"""
import json, re, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass
import fitz

led = json.loads((ROOT / "data/_gold/kics_exemption_provenance.json").read_text(encoding="utf-8"))
NUM = re.compile(r"^[\d,.\s()%△▲-]+$")

tot = {"LABELLED": 0, "UNIQUE": 0, "AMBIGUOUS": 0}
rows = []
for e in led["entries"]:
    if e.get("status") == "CONTRADICTED":
        continue
    v = e.get("verify") or {}
    f, pages, pres = v.get("file"), v.get("pages"), (v.get("present_markers") or [])
    if not f or not pres:
        continue
    p = ROOT / f
    if not p.exists():
        continue
    doc = fitz.open(p)
    idx = [n - 1 for n in pages] if pages else range(doc.page_count)
    text = "".join(doc[n].get_text() for n in idx if 0 <= n < doc.page_count)
    doc.close()
    flat = "".join(text.split())
    g = {"LABELLED": [], "UNIQUE": [], "AMBIGUOUS": []}
    for m in pres:
        fm = "".join(m.split())
        n = flat.count(fm)
        if not NUM.match(m):
            g["LABELLED"].append((m, n))
        elif n <= 1:
            g["UNIQUE"].append((m, n))
        else:
            g["AMBIGUOUS"].append((m, n))
    for k in tot:
        tot[k] += len(g[k])
    rows.append((e["registry"], e["company"], e["quarter"], f, pages, g))

print(f"present_marker 등급 합계: {tot}  총 {sum(tot.values())}")
print(f"AMBIGUOUS 를 가진 엔트리: {sum(1 for *_x, g in rows if g['AMBIGUOUS'])} / {len(rows)}")
print(f"LABELLED 가 하나도 없는 엔트리: {sum(1 for *_x, g in rows if not g['LABELLED'])} / {len(rows)}")
print()
for reg, c, q, f, pages, g in rows:
    print(f"-- {c} {q} [{reg.replace('_ISSUER_INCONSISTENT','')}] p{pages}  "
          f"L={len(g['LABELLED'])} U={len(g['UNIQUE'])} A={len(g['AMBIGUOUS'])}")
    if g["AMBIGUOUS"]:
        print(f"     AMBIGUOUS: {[(m, n) for m, n in g['AMBIGUOUS']]}")
