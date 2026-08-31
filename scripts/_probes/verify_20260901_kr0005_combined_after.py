# -*- coding: utf-8 -*-
"""Independent re-verification (2026-09-01) of KR0005 흥국화재 2025.3Q/2026.2Q combined
경과조치 적용후 item15/16/22 (+ item14/27/28 sanity) via the canonical
scripts/rebuild_combined_transition_after.py pipeline.

This does NOT reimplement the methodology -- it imports the canonical script as a module and
calls its own functions (_pdf, scan_occurrences, resolve_leaf, R4/R7/MARKET_M) so the numbers
are a genuine independent re-derivation from raw PDF, not a copy of a prior session's output.
Read-only: does not write kics_disclosure.json. Prints every guard value the task asked for.
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))

import numpy as np  # noqa: E402
import rebuild_combined_transition_after as M  # noqa: E402

TARGET = ROOT / "kics_disclosure.json"
CODE = "KR0005"
QUARTERS = ["2025.3Q", "2026.2Q"]


def main():
    data = json.loads(TARGET.read_text(encoding="utf-8"))
    by_cq = {}
    for r in data:
        c, q = r["원보험사코드"], r["공시분기"]
        by_cq.setdefault((c, q), {})[int(r["항목번호"])] = r

    def val(items, n, post):
        r = items.get(n)
        if r is None:
            return None
        return M._num(r.get("값_적용후" if post else "값"))

    for q in QUARTERS:
        items = by_cq[(CODE, q)]
        print(f"\n================ {CODE} {q} ================")
        print("--- CURRENT MASTER (before this session's edit) ---")
        for it in (1, 2, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 27, 28, 36, 37, 38, 39, 40):
            r = items.get(it)
            if r is None:
                continue
            print(f"  item{it:<2} {r.get('항목명',''):<14} 전={r.get('값')!r:>12} "
                  f"후={r.get('값_적용후')!r:>12}")

        pdf = M._pdf(M.q2p(q), CODE)
        print(f"pdf = {pdf}")
        occ, headline = M.scan_occurrences(pdf)
        print(f"headline(경과조치후 지급여력비율, raw) = {headline}")

        # --- guard 1: 적용전 재현 ---
        sp = np.array([(occ[k][0][0] if occ.get(k) else 0.0) for k in M.LIFE7], float)
        life_pre = float(np.sqrt(sp @ M.R7 @ sp))
        vp = np.array([(occ[k][0][0] if occ.get(k) else 0.0) for k in M.MARKET5], float)
        mkt_pre = float(np.sqrt(vp @ M.MARKET_M @ vp))
        nl_pre = occ["일반손해"][0][0] if occ.get("일반손해") else 0.0
        cr_pre = occ["신용"][0][0] if occ.get("신용") else 0.0
        op_pre = occ["운영"][0][0] if occ.get("운영") else 0.0
        wp = np.array([life_pre, nl_pre, mkt_pre, cr_pre], float)
        base_pre_calc = float(np.sqrt(wp @ M.R4 @ wp)) + op_pre
        cands = [a for a, _b in occ["기본요구자본"]
                 if base_pre_calc and abs(a - base_pre_calc) <= max(2.0, 0.005 * base_pre_calc)]
        base_pre = cands[0] if cands else None
        print(f"\n[GUARD1 적용전 재현] base_pre_calc(R4 from raw leaves) = {base_pre_calc:,.2f}백만  "
              f"raw 표 기본요구자본전 candidates = {sorted({a for a,_ in occ['기본요구자본']})}  "
              f"matched={base_pre}  PASS={base_pre is not None}")

        # --- resolve combined leaves (each leaf from whichever table moved it) ---
        leaves = {}
        for k in M.LIFE7 + M.MARKET5 + ["신용", "운영", "일반손해"]:
            v, note = M.resolve_leaf(occ.get(k, []))
            if v is None and k in ("자산집중", "장기재물", "장수"):
                v = 0.0
            leaves[k] = v
        s = np.array([leaves[k] for k in M.LIFE7], float)
        life_after = float(np.sqrt(s @ M.R7 @ s))
        v = np.array([leaves[k] for k in M.MARKET5], float)
        mkt_after = float(np.sqrt(v @ M.MARKET_M @ v))
        w = np.array([life_after, leaves["일반손해"], mkt_after, leaves["신용"]], float)
        base_after = float(np.sqrt(w @ M.R4 @ w)) + leaves["운영"]

        # --- guard 2: 표가 직접 공시한 생명장기후/시장후를 R7/MARKET_M이 재현하는가 ---
        disc_life = {round(b, 1) for a, b in occ.get("생명장기", []) if b is not None and abs(a - b) > 0.5}
        disc_mkt = {round(b, 1) for a, b in occ.get("시장", []) if b is not None and abs(a - b) > 0.5}
        life_ok = (not disc_life) or any(abs(life_after - d) <= max(2.0, 0.002 * d) for d in disc_life)
        mkt_ok = (not disc_mkt) or any(abs(mkt_after - d) <= max(2.0, 0.002 * d) for d in disc_mkt)
        print(f"[GUARD2 R7 재현] life_after(calc)={life_after:,.2f}백만  표 생명장기후 후보={sorted(disc_life)}  PASS={life_ok}")
        print(f"[GUARD2 MARKET_M 재현] mkt_after(calc)={mkt_after:,.2f}백만  표 시장후 후보={sorted(disc_mkt)}  PASS={mkt_ok}")

        # --- scale (억원 vs 백만원) ---
        scale = (val(items, 15, False) or 0) / base_pre if base_pre else 0
        scale = 0.01 if scale < 0.5 else 1.0

        # --- tax residual + monotonicity candidates (identical to canonical script) ---
        tax_cands = [a for a, _b in occ.get("법인세", []) if 0 <= a <= base_pre]
        tax_pre = max(tax_cands) if tax_cands else 0.0
        avail_after = val(items, 1, True)
        scr_after = avail_after / headline * 100 / scale
        tax_after = base_after + 0.0 - scr_after  # other_after=0 for KR0005 (no affiliate link)
        disc_base = [b for a, b in occ["기본요구자본"]
                     if b is not None and a == base_pre and abs(a - b) > 0.5]
        disc_scr = [b for a, b in occ.get("기준금액", [])
                    if b is not None and b > 0.1 * base_pre and abs(a - b) > 0.5]
        mono_base_ok = (not disc_base) or (base_after <= min(disc_base) + 2.0)
        mono_scr_ok = (not disc_scr) or (scr_after <= min(disc_scr) + 2.0)
        tax_range_ok = -0.5 <= tax_after <= max(1.0, tax_pre * 1.2 + 2)
        print(f"\n[GUARD3 단조성] 결합 기본요구자본후(calc)={base_after:,.2f}백만  "
              f"단일표 후보(②③④ 각자)={sorted(disc_base)}  min={min(disc_base) if disc_base else None}  "
              f"PASS(결합<=단일 최소)={mono_base_ok}")
        print(f"[GUARD3 단조성] 결합 기준금액후(calc)={scr_after:,.2f}백만  "
              f"단일표 후보={sorted(disc_scr)}  PASS={mono_scr_ok}")
        print(f"[GUARD4 잔차범위] 법인세조정액후(calc)={tax_after:,.2f}백만  "
              f"법인세조정액전={tax_pre:,.2f}백만  범위=[-0.5, {max(1.0, tax_pre*1.2+2):,.2f}]  "
              f"PASS={tax_range_ok}")

        # --- final combined values (억원, scaled) ---
        item15_new = base_after * scale
        item16_new = (life_after + leaves["일반손해"] + mkt_after + leaves["신용"] + leaves["운영"]
                      - base_after) * scale
        item17_new = life_after * scale
        item19_new = mkt_after * scale
        item14_new = scr_after * scale
        item22_new = tax_after * scale

        print(f"\n[FINAL 계산값, 억원] item14후={item14_new:.2f}  item15후={item15_new:.2f}  "
              f"item16후={item16_new:.2f}  item17후={item17_new:.2f}  item19후={item19_new:.2f}  "
              f"item22후={item22_new:.2f}")

        print("[MASTER 현재값, 억원] item14후=%r  item15후=%r  item16후=%r  item17후=%r  "
              "item19후=%r  item22후=%r" % (
                  items[14].get("값_적용후"), items[15].get("값_적용후"), items[16].get("값_적용후"),
                  items[17].get("값_적용후"), items[19].get("값_적용후"), items[22].get("값_적용후")))

        # sanity: item17/19 in master should already equal the freshly-recomputed leaves
        cur17 = val(items, 17, True)
        cur19 = val(items, 19, True)
        print(f"[sanity] item17후 master={cur17} vs recompute={item17_new:.2f}  diff={cur17-item17_new:+.4f}")
        print(f"[sanity] item19후 master={cur19} vs recompute={item19_new:.2f}  diff={cur19-item19_new:+.4f}")

        # item14/27/28 should be UNCHANGED (anchor); print cross-check only
        cur14 = val(items, 14, True)
        v1 = val(items, 1, True)
        v2 = val(items, 2, True)
        print(f"[anchor unchanged check] item14후 master={cur14}  item27후 recompute={v1/cur14*100:.4f} "
              f"(master={items[27].get('값_적용후')})  item28후 recompute={ (v2/cur14*100) if v2 else None} "
              f"(master={items[28].get('값_적용후')})")


if __name__ == "__main__":
    main()
