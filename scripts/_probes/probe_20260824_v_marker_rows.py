# -*- coding: utf-8 -*-
"""읽기 전용: AMBIGUOUS 숫자마커의 **행 라벨**을 원문에서 뽑는다.

fitz word 좌표로 행(y 밴드)을 복원하고, 각 마커 값이 등장하는 행들의 라벨(행 앞머리 비숫자)을 모은다.
  · 모든 등장이 **같은 라벨**의 행이면 → 컬럼 반복일 뿐 귀속은 유일 → (행,값) 쌍으로 승격 가능
  · 라벨이 둘 이상이면 → 진짜 귀속 모호 → 자동 승격 금지, 남은 것으로 보고
출력은 JSON(원장 패치 입력용)."""
import json, re, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass
import fitz

NUM = re.compile(r"^[\d,.\s()%△▲-]+$")
LEAD = re.compile(r"^[\s·ⅠⅡⅢⅣⅤ0-9().,가나다라마바-]*")


def page_rows(doc, pno, ytol=2.5):
    words = doc[pno].get_text("words")   # x0,y0,x1,y1,word,block,line,wordno
    rows = []
    for w in sorted(words, key=lambda w: (round(w[1] / ytol), w[0])):
        y = w[1]
        if rows and abs(rows[-1][0] - y) <= ytol:
            rows[-1][1].append(w)
        else:
            rows.append([y, [w]])
    out = []
    for y, ws in rows:
        ws = sorted(ws, key=lambda w: w[0])
        toks = [w[4] for w in ws]
        label_toks = []
        for t in toks:
            if NUM.match(t) and any(ch.isdigit() for ch in t):
                break
            label_toks.append(t)
        label = " ".join(label_toks).strip()
        out.append((label, [t for t in toks], "".join(toks)))
    return out


led = json.loads((ROOT / "data/_gold/kics_exemption_provenance.json").read_text(encoding="utf-8"))
patch, leftover = {}, {}
for e in led["entries"]:
    if e.get("status") == "CONTRADICTED":
        continue
    v = e.get("verify") or {}
    f, pages, pres = v.get("file"), v.get("pages"), (v.get("present_markers") or [])
    if not f or not pages or not pres:
        continue
    p = ROOT / f
    if not p.exists():
        continue
    doc = fitz.open(p)
    rows = []
    for n in pages:
        if 0 <= n - 1 < doc.page_count:
            rows += page_rows(doc, n - 1)
    doc.close()
    flat_all = "".join(r[2] for r in rows)
    key = f"{e['registry']}|{e['company']}|{e['quarter']}"
    pairs, amb = [], []
    for m in pres:
        fm = "".join(m.split())
        if not NUM.match(m) or flat_all.count(fm) <= 1:
            continue
        labels = []
        for label, toks, flatrow in rows:
            if fm in "".join(toks):
                lab = LEAD.sub("", label).strip() or label.strip()
                if lab:
                    labels.append(lab)
        uniq = sorted(set(labels))
        if len(uniq) == 1:
            pairs.append({"row": uniq[0], "value": m})
        else:
            amb.append({"value": m, "labels": uniq})
    if pairs:
        patch[key] = pairs
    if amb:
        leftover[key] = amb
    print(f"-- {key}: 승격가능 {len(pairs)} / 잔여모호 {len(amb)}")
    for pr in pairs:
        print(f"     OK  {pr['value']:>14s}  <- 행 '{pr['row']}'")
    for a in amb:
        print(f"     AMB {a['value']:>14s}  <- 라벨 {a['labels']}")

outp = ROOT / "artifacts/validation/v20260824_marker_rows.json"
outp.write_text(json.dumps({"promote": patch, "leftover": leftover},
                           ensure_ascii=False, indent=2), encoding="utf-8")
print(f"\n승격가능 총 {sum(len(v) for v in patch.values())} · 잔여모호 총 {sum(len(v) for v in leftover.values())}")
print(f"-> {outp}")
