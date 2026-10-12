"""Step 5 (final): regulation-based tier1/tier2 utilization for all 47 companies, 2026.2Q (read-only).

Definitions (definition_memo.md has the regulation citations):
  tier2  numerator N2 = 보완자본 한도 적용 대상 = 보완자본 - III.2.다.(3) 해약환급금 초과분 - VI.1.가.(2) 기발행 자본증권
         (= TFI 표 「보완자본 한도 적용 전」 경과조치 적용 후 열, 발행사 인쇄 관행 차이를 아래 규칙으로 정규화)
         denominator = 총요구자본(경과조치 적용 전, item14 값) x 50%   [III.2.마, VI.1.라]
  tier1  binding test = max( item53 / (SCR x 15%) ,  (item6 - item53) / (SCR x 10%) )
         [VI.1.가.(1) 기발행분 15% ; III.2.다.(1)② 10% (보험업법 조건부자본증권이면 15%, 보험사 발행 사례 없음)]
         item6 은 순자산 계상액(한도 전)이라 상한값이다 (K-ICS 이후 일반 신종 = 보완자본 자본증권 III.2.다.(2) 포함 가능).

Normalisation rules for item47 (issuer printing conventions, all measured in s3_tfi_tables.txt):
  R0  보완자본(item3) == 0                     -> N2 = 0
  R1  gross printing: |47 - item3| <= tol and item49 > tol  -> subtract item49 (gate scope INCL, kics_json_rules)
  R2  legacy netted by issuer in 적용후 열 (47후 == 47전 - 53 - 54)        -> use 47후
  R3  legacy not netted (47후 == 47전, 53+54 > 0)                          -> max(0, 47 - 53 - 54)
  R4  hybrid-only netted (47후 == 47전 - 53, 54 > 0)                       -> max(0, 47후 - 54)
  R5  other issuer-specific netting                                          -> 47후 as printed
Inputs: kics_disclosure.json, kics_tier1/2_utilization.json, s3_tfi_tables.json, s4_hybrid_vintage.json
Outputs: recompute_47.json / recompute_47.csv (utf-8-sig) / s5_summary.txt

Run (repo root, after s2..s4):
  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe data/_derived/capital_utilization_definition_20261012/s5_final_recompute.py
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
sys.path.insert(0, str(REPO / "src"))
from solvency.validation.kics_json_rules import (  # noqa: E402  (import, do not retype)
    TIER2_LIMIT_RATIO,
    _group_records,
    _tier2_i47_scope_map,
)

Q = "2026.2Q"
TOL = 2.0  # 억원, same absolute tolerance as kics_json_rules.evaluate default


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


def close(a, b, tol=TOL):
    return a is not None and b is not None and abs(a - b) <= tol


def pct(n, d):
    return None if n is None or not d or d <= 0 else round(n / d * 100.0, 1)


def main() -> int:
    records = json.loads((REPO / "kics_disclosure.json").read_text(encoding="utf-8"))
    scope_map = _tier2_i47_scope_map(_group_records(records), TOL)
    m: dict[str, dict] = {}
    for r in records:
        if r.get("공시분기") != Q:
            continue
        e = m.setdefault(r["원보험사코드"], {"name": r.get("원수사명"), "pre": {}, "post": {}})
        e["pre"][r["항목번호"]] = f(r.get("값"))
        if "값_적용후" in r:
            e["post"][r["항목번호"]] = f(r.get("값_적용후"))
    t1 = {r["code"]: r for r in json.loads((REPO / "kics_tier1_utilization.json").read_text(encoding="utf-8"))["results"]}
    t2 = {r["code"]: r for r in json.loads((REPO / "kics_tier2_utilization.json").read_text(encoding="utf-8"))["results"]}
    vint = json.loads((HERE / "s4_hybrid_vintage.json").read_text(encoding="utf-8"))

    rows = []
    for code in sorted(set(m) | set(t1) | set(t2)):
        e = m.get(code, {"name": None, "pre": {}, "post": {}})
        pre, post = e["pre"], e["post"]
        scr = pre.get(14)
        i3, i6, i13 = pre.get(3), pre.get(6), pre.get(13)
        p0, p1 = pre.get(47), post.get(47)
        if p1 is None:
            p1 = p0
        l49, h53, s54_printed = pre.get(49), pre.get(53) or 0.0, pre.get(54) or 0.0
        lim2 = scr * TIER2_LIMIT_RATIO if scr else None
        v = vint.get(code, {})
        bond_leg_sub = v.get("sub_legacy", 0.0)
        flags = []
        # '(기발행 후순위채무)' row vs bond ledger: if the ledger has no pre-2023 subordinated debt, the printed row is
        # post-2023 debt mislabelled by the issuer (DB생명: row appears 2025.1Q = 2025-02-14 issue; 미래에셋: row jumps
        # +2,998 in 2025.4Q = 2025-10-24 issue and old one called by 2026.2Q) -> it is NOT exempt (VI.1.가.(2)).
        s54 = s54_printed
        if s54_printed > TOL and bond_leg_sub <= TOL:
            s54 = 0.0
            flags.append(f"기발행 후순위 행 {s54_printed:g}억 = 2023년 이후 신규채(채권원장·시계열) -> 차감 안 함")
        legacy = h53 + s54

        # ---------------- tier2 ----------------
        rule = None
        n2 = None          # TFI 적용 후 (현행 규정) 한도 적용 대상
        n2_pre = None      # TFI 적용 전 (경과조치 종료 시 관점)
        if i3 is not None and abs(i3) <= TOL:
            rule, n2, n2_pre = "R0", 0.0, 0.0
        elif p0 is None:
            rule = "NA"
            flags.append("47~54 원문 미공시 -> 산출 불가")
        else:
            gross = l49 is not None and l49 > TOL and close(p0, i3)
            d0 = p0 - l49 if gross else p0
            d1 = (p1 - l49) if (gross and close(p1, i3) or (gross and close(p1, p0))) else p1
            if gross:
                flags.append("R1 발행사가 한도적용전 행에 보완자본 총액 인쇄(해약환급금 초과분 포함) -> item49 차감")
            n2_pre = max(0.0, d0)
            if legacy <= TOL:
                rule, n2 = ("R1" if gross else "R-none"), max(0.0, d1 if s54_printed <= TOL else d0)
            elif close(p1, p0 - legacy):
                rule, n2 = "R2", max(0.0, d1)
            elif close(p1, p0):
                rule, n2 = "R3", max(0.0, d0 - legacy)
                flags.append("R3 발행사가 적용후 열에서 기발행분을 안 뺌 -> 53+54 차감([별표22] VI.1.가.(3))")
                if d0 - legacy < -TOL:
                    flags.append("53+54 > 한도적용전: 기발행 행이 인정액이 아님(액면·오기 가능)")
            elif s54 > TOL and close(p1, p0 - h53):
                rule, n2 = "R4", max(0.0, d1 - s54)
                flags.append("R4 발행사가 기발행 신종만 뺌 -> 기발행 후순위 추가 차감")
            else:
                rule, n2 = "R5", max(0.0, d1)
                flags.append("R5 발행사 고유 차감 방식(적용후 열 인쇄값 사용)")
        # alternative: what the number would be if the printed '(기발행 후순위채무)' row WERE subtracted
        # (only differs for the two mislabelled-row companies) -> kept for the owner decision table
        n2_alt_no_legacy_sub = None
        if s54_printed > TOL and s54 == 0.0 and n2_pre is not None:
            n2_alt_no_legacy_sub = round(max(0.0, n2_pre - h53 - s54_printed), 2)

        # ---------------- tier1 ----------------
        t1num = max(i6, 0.0) if i6 is not None else None
        t1_15 = pct(t1num, scr * 0.15 if scr else None)
        t1_10 = pct(t1num, scr * 0.10 if scr else None)
        t1_bind = None
        if t1num is not None and scr:
            leg = min(h53, t1num)
            new = max(0.0, t1num - leg)
            t1_bind = round(max(leg / (scr * 0.15), new / (scr * 0.10)) * 100.0, 1)
        if v.get("hyb_2023_2508", 0.0) > TOL:
            flags.append(f"T1 상한값: 2023-01~2025-08 발행 일반 신종 {v['hyb_2023_2508']:.0f}억(스텝업이면 보완자본 자본증권 III.2.다.(2)) 포함")
        if t1num and t1num > TOL and not v:
            flags.append("T1: 채권원장에 신종 없음(item6 = 우선주 등 다른 증권일 수 있음)")

        d1r, d2r = t1.get(code, {}), t2.get(code, {})
        rows.append({
            "code": code, "name": e["name"] or d1r.get("company"),
            "scr_item14_pre": scr, "tier2_limit_scr50": None if lim2 is None else round(lim2, 2),
            "item3": i3, "item13": i13, "item6": i6,
            "item47_pre": p0, "item47_post": post.get(47), "item49": l49, "item53": pre.get(53), "item54": pre.get(54),
            "gate_item47_scope": scope_map.get(code, "EXCL"),
            "bond_hyb_legacy": v.get("hyb_legacy"), "bond_hyb_2023_2508": v.get("hyb_2023_2508"),
            "bond_hyb_2509p": v.get("hyb_2509p"), "bond_sub_legacy": v.get("sub_legacy"), "bond_sub_2023p": v.get("sub_2023p"),
            "t2_rule": rule,
            "t2_num_reg": None if n2 is None else round(n2, 2),
            "t2_pct_reg": pct(n2, lim2),
            "t2_num_tfi_off": None if n2_pre is None else round(n2_pre, 2),
            "t2_pct_tfi_off": pct(n2_pre, lim2),
            "t2_num_alt_if_printed_legacy_row_subtracted": n2_alt_no_legacy_sub,
            "t2_pct_alt_if_printed_legacy_row_subtracted": pct(n2_alt_no_legacy_sub, lim2),
            "t2_deployed_pct": d2r.get("utilization_pct"), "t2_deployed_num": d2r.get("numerator_eok"),
            "t2_deployed_flag": d2r.get("quality_flag"),
            "t2_diff_pp": (None if pct(n2, lim2) is None or d2r.get("utilization_pct") is None
                           else round(pct(n2, lim2) - d2r["utilization_pct"], 1)),
            "t1_pct_deployed_15": d1r.get("utilization_pct"), "t1_pct_item6_15": t1_15, "t1_pct_item6_10": t1_10,
            "t1_pct_binding": t1_bind,
            "flags": " | ".join(flags),
        })

    (HERE / "recompute_47.json").write_text(json.dumps({
        "quarter": Q, "count": len(rows),
        "definition_tier2": "N2 = 보완자본 - 해약환급금 부족분 초과분(III.2.다.(3)) - 기발행 자본증권(VI.1.가.(2)); 분모 = 총요구자본(적용 전) x 50%",
        "definition_tier1_binding": "max(기발행 신종 / (SCR x 15%), (보통주 이외 자본증권 - 기발행 신종) / (SCR x 10%))",
        "rows": rows}, ensure_ascii=False, indent=1), encoding="utf-8")
    with (HERE / "recompute_47.csv").open("w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    out = [f"{Q} n={len(rows)}  (tier2: reg / tfi_off / deployed ; tier1: binding / item6-10% / deployed-15%)"]
    for r in rows:
        out.append(f"{r['code']} {str(r['name'])[:9]:9s} T2 {r['t2_pct_reg']}/{r['t2_pct_tfi_off']}/{r['t2_deployed_pct']} "
                   f"[{r['t2_rule']}] alt={r['t2_pct_alt_if_printed_legacy_row_subtracted']} | T1 {r['t1_pct_binding']}/{r['t1_pct_item6_10']}/{r['t1_pct_deployed_15']} "
                   f"| scope={r['gate_item47_scope']} | {r['flags']}")
    (HERE / "s5_summary.txt").write_text("\n".join(out) + "\n", encoding="utf-8")
    print("\n".join(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
