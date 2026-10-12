# -*- coding: utf-8 -*-
"""x1: per-company panel of the K-ICS items needed for the per-security issuer-treatment (X) test.
Read-only on kics_disclosure.json. Output: x1_panel.txt / x1_panel.json
Items (억원): 2 기본자본, 3 보완자본, 6 보통주 이외 자본증권, 13 보완자본으로 재분류(Ⅲ), 14 지급여력기준금액,
47 보완자본 한도 적용 전, 48 한도, 49 해약환급금 부족분 초과분, 53 기발행 신종, 54 기발행 후순위. 값=적용전, 값_적용후=경과조치 후.
Run (repo root): C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe data/_derived/capsec_reinstate_20261012/x1_panel_dump.py
"""
import json, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
sys.stdout.reconfigure(encoding="utf-8")
CODES = ["KR0005","KR0032","KR0050","KR0068","KR0072","KR0073","KR0083","KR0097","KR0104","KR1000"]
ITEMS = [1,2,3,6,13,14,47,48,49,53,54]

def f(v):
    try: return float(str(v).replace(",", ""))
    except (TypeError, ValueError): return None

def qkey(q):
    y, p = q.split("."); return int(y), int(p[0])

def main():
    d = json.loads((REPO/"kics_disclosure.json").read_text(encoding="utf-8"))
    pan = {}; names = {}
    for r in d:
        c = r["원보험사코드"]
        if c in CODES and r["항목번호"] in ITEMS:
            names[c] = r.get("원수사명")
            pan.setdefault(c, {}).setdefault(r["공시분기"], {})[r["항목번호"]] = (f(r.get("값")), f(r.get("값_적용후")))
    out = {}
    lines = []
    for c in CODES:
        lines.append(f"== {c} {names.get(c)}  (pre = 값, post = 값_적용후; X = 13 - 49)")
        lines.append("  q      | i2 pre/post | i3 pre/post | i6 | i13 | i49 | X | i14 | cap10 | i47 pre/post | i48 | i53 | i54")
        out[c] = {}
        for q in sorted(pan[c], key=qkey):
            v = pan[c][q]
            g = lambda i, k=0: (v.get(i) or (None, None))[k]
            i13, i49 = g(13), g(49)
            x = None if i13 is None or i49 is None else round(i13 - i49, 2)
            cap10 = None if g(14) is None else round(g(14) * 0.10, 1)
            out[c][q] = {"i2": g(2), "i2p": g(2,1), "i3": g(3), "i3p": g(3,1), "i6": g(6), "i13": i13, "i49": i49, "X": x,
                         "i14": g(14), "cap10": cap10, "i47": g(47), "i47p": g(47,1), "i48": g(48), "i53": g(53), "i54": g(54)}
            lines.append(f"  {q} | {g(2)}/{g(2,1)} | {g(3)}/{g(3,1)} | {g(6)} | {i13} | {i49} | {x} | {g(14)} | {cap10} | {g(47)}/{g(47,1)} | {g(48)} | {g(53)} | {g(54)}")
    (HERE/"x1_panel.txt").write_text("\n".join(lines)+"\n", encoding="utf-8")
    (HERE/"x1_panel.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print("\n".join(lines))

if __name__ == "__main__":
    main()
