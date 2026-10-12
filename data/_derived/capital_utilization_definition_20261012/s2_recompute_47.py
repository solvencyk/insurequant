"""Step 2: independent re-computation of tier1/tier2 capital-utilization for all companies (read-only).

Regulation anchors (see definition_memo.md):
  tier1: [별표22] III.2.다.(1)② 기본자본 자본증권 인정한도 = 총요구자본 x 10% (보험업법 조건부자본증권 15%),
         VI.1.가.(1) TFI: 시행일 이전 발행·종전 기본자본 증권은 총요구자본 15% 까지 기본자본.
  tier2: III.2.마 보완자본 한도 = 총요구자본 x 50%, 다.(3) 해약환급금 초과분 제외;
         VI.1.가.(3) TFI: (2)의 기발행 자본증권도 제외하고 한도초과 여부 계산.
  denominator: VI.1.라 -> 총요구자본은 경과조치 적용 전(= item14 '값').

Inputs (read only): kics_disclosure.json, kics_tier1_utilization.json, kics_tier2_utilization.json.
Outputs: recompute_47.json, recompute_47.csv (utf-8-sig for Excel), s2_summary.txt

Run (repo root):
  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe data/_derived/capital_utilization_definition_20261012/s2_recompute_47.py
"""
from __future__ import annotations

import csv
import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
Q = "2026.2Q"
TOL_EOK = 2.0  # absolute tolerance (억원) for identity checks (rounding in issuer tables)


def f(v):
    if v is None:
        return None
    s = str(v).replace(",", "").replace("△", "-").strip()
    if s in ("", "-", "None", "nan"):
        return None
    try:
        return float(s)
    except ValueError:
        return None


def load_master():
    out: dict[str, dict] = {}
    for r in json.loads((REPO / "kics_disclosure.json").read_text(encoding="utf-8")):
        if r.get("공시분기") != Q:
            continue
        e = out.setdefault(r["원보험사코드"], {"name": r.get("원수사명"), "kind": r.get("생손보여부"), "pre": {}, "post": {}})
        it = r["항목번호"]
        e["pre"][it] = f(r.get("값"))
        if "값_적용후" in r:
            e["post"][it] = f(r.get("값_적용후"))
    return out


def load_util(name):
    doc = json.loads((REPO / name).read_text(encoding="utf-8"))
    return {r["code"]: r for r in doc["results"]}, doc.get("definition", {})


def pct(n, d):
    if n is None or d is None or d <= 0:
        return None
    return round(n / d * 100.0, 1)


def close(a, b, tol=TOL_EOK):
    return a is not None and b is not None and abs(a - b) <= max(tol, 0.001 * max(abs(a), abs(b)))


def main() -> int:
    m = load_master()
    t1, t1def = load_util("kics_tier1_utilization.json")
    t2, t2def = load_util("kics_tier2_utilization.json")
    codes = sorted(set(m) | set(t1) | set(t2))
    rows = []
    for code in codes:
        e = m.get(code, {"name": None, "kind": None, "pre": {}, "post": {}})
        pre, post = e["pre"], e["post"]
        g = lambda it: pre.get(it)  # noqa: E731
        gp = lambda it: post.get(it) if post.get(it) is not None else pre.get(it)  # noqa: E731
        scr = g(14)  # 총요구자본, 경과조치 적용 전 (VI.1.라)
        i3, i3p = g(3), post.get(3)
        i6, i6p = g(6), post.get(6)
        i13, i49, i49p = g(13), g(49), post.get(49)
        i47, i47p = g(47), post.get(47)
        i48 = g(48)
        i51, i51p = g(51), post.get(51)
        i53, i54 = g(53), g(54)
        i53p, i54p = post.get(53), post.get(54)
        legacy = (i53 or 0.0) + (i54 or 0.0)

        # ---- tier1 ----
        t1num = max(i6, 0.0) if i6 is not None else None
        t1_10 = pct(t1num, scr * 0.10 if scr else None)
        t1_15 = pct(t1num, scr * 0.15 if scr else None)
        # regulatory limit rate: 15% only for TFI legacy tier1 securities (VI.1.가.(1)) or
        # 보험업법 conditional securities (III.2.다.(1)②, not identifiable from disclosure) -> 10% otherwise
        legacy_t1 = (i53 or 0.0) > 0
        t1_rate_reg = 0.15 if legacy_t1 else 0.10
        t1_reg = pct(t1num, scr * t1_rate_reg if scr else None)

        # ---- tier2 ----
        # issuer-printed limit-subject amount, TFI-applied column (VI.1.가.(3)); fallback to 값 when no 적용후 cell
        n2_post = i47p if i47p is not None else i47
        # component reconstruction (한기평 p4 주2 formula): 보완자본 - 해약환급금 초과분 - 기발행 자본증권
        n2_comp = None
        if i3 is not None and i49 is not None:
            n2_comp = i3 - i49 - legacy
        # issuer convention classification for item 47
        conv = []
        if i47 is not None and i3 is not None and i49 is not None:
            conv.append("47pre=3-49" if close(i47, i3 - i49) else "47pre!=3-49")
        if i47p is not None and i47 is not None:
            if legacy > 0:
                if close(i47p, i47 - legacy):
                    conv.append("47post=47pre-53-54(nets_legacy)")
                elif close(i47p, i47):
                    conv.append("47post=47pre(no_netting)")
                else:
                    conv.append("47post_other")
            else:
                conv.append("47post=47pre" if close(i47p, i47) else "47post!=47pre(no_legacy)")
        elif i47 is not None:
            conv.append("47post_missing")
        lim_scr = scr * 0.5 if scr else None
        lim_ok = close(i48, lim_scr) if i48 is not None and lim_scr is not None else None

        # regulatory tier2 numerator choice:
        #   no legacy -> 47 (pre==post)
        #   legacy & issuer nets in post column -> 47 post
        #   legacy & issuer did NOT net -> max(0, 47pre - 53 - 54)  (VI.1.가.(3)); flag
        #   47 inconsistent with 3-49 (e.g. RGA prints 기본자본 in 47) -> use max(0, 3-49-53-54); flag
        flag = []
        n2_reg = None
        if i47 is None and i3 is not None and i49 is not None:
            n2_reg = max(0.0, n2_comp)
            flag.append("47_missing->components")
        elif i47 is not None:
            if i3 is not None and i49 is not None and not close(i47, i3 - i49) and i47 > (i3 or 0) + TOL_EOK:
                n2_reg = max(0.0, n2_comp) if n2_comp is not None else None
                flag.append("47_gt_tier2(issuer_misprint)->components")
            elif legacy > 0 and i47p is not None and close(i47p, i47 - legacy):
                n2_reg = max(0.0, i47p)
            elif legacy > 0:
                n2_reg = max(0.0, i47 - legacy)
                flag.append("legacy_not_netted_by_issuer->47-53-54")
                if i47 - legacy < -TOL_EOK:
                    flag.append("53+54>47(legacy_row_likely_face_value)")
            else:
                n2_reg = max(0.0, n2_post)
        t2_reg = pct(n2_reg, lim_scr)
        t2_post = pct(n2_post, lim_scr)
        t2_pre = pct(i47, lim_scr)
        t2_gross3 = pct(i3, lim_scr)

        d1 = t1.get(code, {})
        d2 = t2.get(code, {})
        row = {
            "code": code,
            "name": e["name"] or d1.get("company") or d2.get("company"),
            "kind": e["kind"],
            "scr_item14_pre": scr,
            "item3_tier2": i3,
            "item6_nonCET_securities": i6,
            "item13_reclass": i13,
            "item47_pre": i47,
            "item47_post": i47p,
            "item48_limit_printed": i48,
            "item48_eq_scr50": lim_ok,
            "item49_lapse_excess": i49,
            "item51_tier2_tfi": i51,
            "item53_legacy_hybrid": i53,
            "item54_legacy_sub": i54,
            "t1_numerator": t1num,
            "t1_pct_10": t1_10,
            "t1_pct_15": t1_15,
            "t1_rate_reg": t1_rate_reg,
            "t1_pct_reg": t1_reg,
            "t1_deployed_pct": d1.get("utilization_pct"),
            "t1_deployed_num": d1.get("tier1_hybrid_issued_eok"),
            "t1_deployed_flag": d1.get("quality_flag"),
            "t1_diff_15_vs_deployed": (None if t1_15 is None or d1.get("utilization_pct") is None
                                       else round(t1_15 - d1["utilization_pct"], 1)),
            "t2_num_reg": None if n2_reg is None else round(n2_reg, 2),
            "t2_num_components": None if n2_comp is None else round(n2_comp, 2),
            "t2_pct_reg": t2_reg,
            "t2_pct_47post": t2_post,
            "t2_pct_47pre": t2_pre,
            "t2_pct_gross_item3": t2_gross3,
            "t2_deployed_pct": d2.get("utilization_pct"),
            "t2_deployed_num": d2.get("numerator_eok"),
            "t2_deployed_flag": d2.get("quality_flag"),
            "t2_diff_reg_vs_deployed": (None if t2_reg is None or d2.get("utilization_pct") is None
                                        else round(t2_reg - d2["utilization_pct"], 1)),
            "item47_convention": ";".join(conv),
            "t2_reg_flags": ";".join(flag),
            "in_t1_json": code in t1,
            "in_t2_json": code in t2,
            "in_master": code in m,
        }
        rows.append(row)

    (HERE / "recompute_47.json").write_text(json.dumps(
        {"quarter": Q, "count": len(rows), "deployed_t1_definition": t1def, "deployed_t2_definition": t2def,
         "rows": rows}, ensure_ascii=False, indent=1), encoding="utf-8")
    with (HERE / "recompute_47.csv").open("w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    lines = [f"quarter={Q} companies={len(rows)} (master {len(m)}, t1 {len(t1)}, t2 {len(t2)})"]
    lines.append("code name | SCR | i6 | t1 15%/10%/reg dep | i3 i49 i47pre i47post i53 i54 | t2 reg/post/pre dep | conv | flags")
    for r in rows:
        lines.append(
            f"{r['code']} {str(r['name'])[:10]} | {r['scr_item14_pre']} | {r['item6_nonCET_securities']} | "
            f"{r['t1_pct_15']}/{r['t1_pct_10']}/{r['t1_pct_reg']} dep {r['t1_deployed_pct']} | "
            f"{r['item3_tier2']} {r['item49_lapse_excess']} {r['item47_pre']} {r['item47_post']} {r['item53_legacy_hybrid']} {r['item54_legacy_sub']} | "
            f"{r['t2_pct_reg']}/{r['t2_pct_47post']}/{r['t2_pct_47pre']} dep {r['t2_deployed_pct']} | {r['item47_convention']} | {r['t2_reg_flags']}")
    (HERE / "s2_summary.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
