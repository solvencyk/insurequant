# -*- coding: utf-8 -*-
"""rescan.json 상세 인쇄 — 재작성 후보 셀 + 컨트롤 실패 셀 + unmatched 라벨."""
import json
import sys
from pathlib import Path


def main():
    rep = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    only = sys.argv[2:] or None
    for code, r in rep.items():
        if only and code not in only:
            continue
        if r.get("status") != "OK":
            print(f"### {code} {r['company']}  {r['status']}")
            continue
        cells = r["cells"]
        re1 = [c for c in cells if c["restated_prev"]]
        re2 = [c for c in cells if c["restated_prev2"]]
        bad = [c for c in cells if c["d_cur"] is not None and not c["control_ok"]]
        nocmp = [c for c in cells if c["d_cur"] is None]
        if not (re1 or re2 or bad or r["unmatched"] or nocmp):
            continue
        print("=" * 100)
        print(f"### {code} {r['company']}  src={r['source']}  rows={r['rows']} "
              f"mapped={r['mapped']} ctlOK={r['control_ok']} ctlBAD={r['control_bad']}")
        if r["unmatched"]:
            print("  UNMATCHED labels:", r["unmatched"])
        if nocmp:
            print("  NO-CONTROL (printed or master missing):",
                  [(c["item"], c["label"][:28], c["printed_cur"], c["master_cur"]) for c in nocmp])
        for c in bad:
            print(f"  CTLBAD it{c['item']:<3d} {c['label'][:36]:36s} "
                  f"2Q인쇄={c['printed_cur']} 마스터2Q={c['master_cur']} Δ={c['d_cur']}")
        for c in re1:
            print(f"  RE-1Q  it{c['item']:<3d} {c['label'][:36]:36s} "
                  f"마스터1Q={c['master_prev']} 2Q본직전칸={c['printed_prev']} Δ={c['d_prev']:+}")
        for c in re2:
            print(f"  RE-4Q  it{c['item']:<3d} {c['label'][:36]:36s} "
                  f"마스터4Q={c['master_prev2']} 2Q본전전칸={c['printed_prev2']} Δ={c['d_prev2']:+}")


if __name__ == "__main__":
    sys.exit(main())
