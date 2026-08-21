"""흥국생명(KR0071) 기타요구자본(관계회사 환산치) vs 흥국화재(KR0005) 요구자본 — 비율 안정성."""
import io, json, sys
from collections import defaultdict
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
REPO = Path(__file__).resolve().parents[2]
rows = json.loads((REPO / "kics_disclosure.json").read_text(encoding="utf-8"))
def num(v):
    try: return float(str(v).replace(",", ""))
    except (TypeError, ValueError): return None
m = defaultdict(dict)
for r in rows:
    try: m[(r["원보험사코드"], r["공시분기"])][int(r["항목번호"])] = (num(r.get("값")), num(r.get("값_적용후")))
    except (TypeError, ValueError, KeyError): pass
def g(c, q, it, p): return m.get((c, q), {}).get(it, (None, None))[1 if p else 0]
qs = sorted({q for (c, q) in m if c == "KR0071"}, key=lambda x: (x.split(".")[0], x.split(".")[1]))
print(f"{'분기':<9}{'생명 기타요구전':>13}{'화재 item14전':>13}{'비율':>9} | "
      f"{'생명 기타요구후':>13}{'화재 item14후':>13}{'비율':>9} | {'화재 15전':>10}{'비율(15전)':>11}")
for q in qs:
    o_pre, o_post = g("KR0071", q, 23, 0), g("KR0071", q, 23, 1)
    f14p, f14a = g("KR0005", q, 14, 0), g("KR0005", q, 14, 1)
    f15p = g("KR0005", q, 15, 0)
    r1 = f"{o_pre/f14p:.5f}" if o_pre and f14p else ""
    r2 = f"{o_post/f14a:.5f}" if o_post and f14a else ""
    r3 = f"{o_pre/f15p:.5f}" if o_pre and f15p else ""
    print(f"{q:<9}{o_pre!s:>13}{f14p!s:>13}{r1:>9} | {o_post!s:>13}{f14a!s:>13}{r2:>9} | {f15p!s:>10}{r3:>11}")
