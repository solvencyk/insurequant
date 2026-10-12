"""Step 4: per-company hybrid (신종자본증권) vintage from the bond-level master vs disclosure item6/item53 (read-only).

Vintage buckets (regulation + public record, see definition_memo.md):
  legacy  : issued before 2023-01-01 (K-ICS 시행 전, TFI VI.1.가.(1) -> tier1 up to SCR x 15% until 2032)
  kics_t2 : 2023-01-01 .. 2025-08-31 (K-ICS-era 일반 신종자본증권, step-up -> 보완자본 자본증권, III.2.다.(2))
  kics_t1?: 2025-09-01 or later (업계 최초 '기본자본 신종자본증권' = DB손보 2025-09; other issues need per-bond terms)
Output: s4_hybrid_vintage.json / .txt

Run (repo root):
  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe data/_derived/capital_utilization_definition_20261012/s4_hybrid_vintage.py
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]


def main() -> int:
    cs = json.loads((REPO / "kics_capital_securities.json").read_text(encoding="utf-8"))
    rec = json.loads((HERE / "recompute_47.json").read_text(encoding="utf-8"))
    byc = {r["code"]: r for r in rec["rows"]}
    agg: dict[str, dict] = {}
    for r in cs["rows"]:
        code = r["원보험사코드"]
        e = agg.setdefault(code, {"name": r.get("회사명"), "hyb_legacy": 0.0, "hyb_2023_2508": 0.0, "hyb_2509p": 0.0,
                                  "sub_legacy": 0.0, "sub_2023p": 0.0, "bonds": []})
        d = r.get("발행일") or ""
        bal = r.get("잔액_억") or 0.0
        if r.get("종류") == "신종자본증권":
            key = "hyb_legacy" if d < "2023-01-01" else ("hyb_2023_2508" if d < "2025-09-01" else "hyb_2509p")
        else:
            key = "sub_legacy" if d < "2023-01-01" else "sub_2023p"
        e[key] += bal
        e["bonds"].append({"종류": r.get("종류"), "발행일": d, "잔액_억": bal, "구분": r.get("구분"),
                           "잔액기준일": r.get("잔액기준일")})
    lines = ["code name | item6 item53 item54 | hyb legacy / 23-25.8 / 25.9+ | sub legacy / 23+ | bal_asof"]
    for code in sorted(set(agg) | {c for c, r in byc.items() if (r.get("item6_nonCET_securities") or 0) > 0}):
        e = agg.get(code, {"name": byc.get(code, {}).get("name"), "hyb_legacy": 0, "hyb_2023_2508": 0, "hyb_2509p": 0,
                           "sub_legacy": 0, "sub_2023p": 0, "bonds": []})
        r = byc.get(code, {})
        asof = sorted({b["잔액기준일"] for b in e["bonds"] if b.get("잔액기준일")})
        lines.append(f"{code} {str(e['name'])[:10]} | {r.get('item6_nonCET_securities')} {r.get('item53_legacy_hybrid')} "
                     f"{r.get('item54_legacy_sub')} | {e['hyb_legacy']:.0f} / {e['hyb_2023_2508']:.0f} / {e['hyb_2509p']:.0f} | "
                     f"{e['sub_legacy']:.0f} / {e['sub_2023p']:.0f} | {asof}")
        for b in sorted(e["bonds"], key=lambda x: x["발행일"]):
            if b["종류"] == "신종자본증권" and b["발행일"] >= "2025-01-01":
                lines.append(f"      {b['발행일']} {b['잔액_억']:.0f} {b['구분']}")
    (HERE / "s4_hybrid_vintage.json").write_text(json.dumps(agg, ensure_ascii=False, indent=1), encoding="utf-8")
    (HERE / "s4_hybrid_vintage.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
