# -*- coding: utf-8 -*-
"""Build management_indicators rows for the reinsurer branches KR1101~KR1108 from the parsed 1-1 / 1-2 / 5-1 tables.

READ ONLY on masters. Input  : data/_derived/reinsurer_ifrs17_csm_20261011/mi_tables.json (extract_reinsurer_mi_20261011.py)
                  Output : data/_derived/reinsurer_ifrs17_csm_20261011/mi_rows.json   (rows in the master's schema, sorted)
                           data/_derived/reinsurer_ifrs17_csm_20261011/mi_build_report.json (decisions, conflicts, checks)

Rules (owner, handoff_20261008_reinsurer_pipeline §7, same as the K-ICS reinsurer load and the CSM masters):
  1. a (company, quarter, item) that really differs between filings takes the value of the MOST RECENT filing's prior-year
     column (the filing four quarters later); no agent judgement of "typo";
  2. a pure rounding difference (one print has decimals, the other is its integer rounding) is no conflict: the more precise
     value is kept;
  3. a 0 / '-' print never overwrites a non-zero value;
  6. (2026-10-10) when the later column breaks an identity that the filing's own column keeps, the filing's own set stands
     (here: 자산 = 부채 + 자본 is judged per (company, quarter) over the three cells together).
No back-fill of unpublished values: every value is a printed number of some filing. Values of 2022 quarters are not loaded
(the master starts at 2023.1Q; 2022 is RBC). "0" prints in 1-2 rows of reinsurers (신계약률, 유지율 ... = 해당없음) are not loaded.

Units: amounts are 억원 in the master. A table printed in 백만원 is divided by 100 (decimals kept). The 5-1 amounts of some
docs carry a "억원" header but 백만원 magnitudes (KR1106); the unit is fixed by comparing 경과운용자산 with 자산 (flagged).

Run:  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/build_reinsurer_mi_rows_20261011.py
"""
from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STAGE = ROOT / "data" / "_derived" / "reinsurer_ifrs17_csm_20261011"
sys.stdout.reconfigure(encoding="utf-8")
CODES = [f"KR11{n:02d}" for n in range(1, 9)]

# label -> (item_no, name, section, level, is_amount)
ITEMS = {
    "assets": (1, "자산", "1-1", 1, True),
    "liabilities": (2, "부채", "1-1", 1, True),
    "equity": (3, "자본", "1-1", 1, True),
    "net_income": (4, "당기순이익", "1-1", 1, True),
    "solv_pre": (5, "지급여력비율_경과조치전", "1-1", 1, False),
    "solv_post": (6, "지급여력비율_경과조치후", "1-1", 1, False),
    "inv_yield": (7, "운용자산이익률", "1-1", 1, False),
    "op_margin": (8, "영업이익률", "1-1", 1, False),
    "roa": (9, "총자산수익률ROA", "1-1", 1, False),
    "roe": (10, "자기자본수익률ROE", "1-1", 1, False),
    "new_contract_rate": (11, "신계약률", "1-2", 1, False),
    "lapse_rate": (12, "효력상실및해약률", "1-2", 1, False),
    "claims_paid_rate": (13, "보험금지급률", "1-2", 1, False),
    "asset_mgmt_rate": (14, "자산운용률", "1-2", 1, False),
    "persist_13": (15, "계약유지율_13회차", "1-2", 2, False),
    "persist_25": (16, "계약유지율_25회차", "1-2", 2, False),
    "persist_37": (17, "계약유지율_37회차", "1-2", 2, False),
    "persist_49": (18, "계약유지율_49회차", "1-2", 2, False),
    "persist_61": (19, "계약유지율_61회차", "1-2", 2, False),
    "persist_73": (20, "계약유지율_73회차", "1-2", 2, False),
    "persist_85": (21, "계약유지율_85회차", "1-2", 2, False),
    "inv_profit_A": (22, "투자이익A", "5-1", 1, True),
    "avg_inv_assets_B": (23, "경과운용자산B", "5-1", 1, True),
}
SRC_KIND = {"assets": "t11", "liabilities": "t11", "equity": "t11", "net_income": "t11", "solv_pre": "t11", "solv_post": "t11",
            "inv_yield": "t11", "op_margin": "t11", "roa": "t11", "roe": "t11",
            "new_contract_rate": "t12", "lapse_rate": "t12", "claims_paid_rate": "t12", "asset_mgmt_rate": "t12",
            "inv_profit_A": "t51", "avg_inv_assets_B": "t51"}
for k in ITEMS:
    if k.startswith("persist_"):
        SRC_KIND[k] = "t12"
RATIO_FALLBACK = {"inv_yield", "op_margin", "roa", "roe"}          # also printed in the 5-1 block
UNIT_FACTOR = {"억원": 1.0, "백만원": 0.01, "천원": 1e-5, "원": 1e-8, None: 1.0}


def decimals(raw: str) -> int:
    t = re.sub(r"[^\d.]", "", raw or "")
    return len(t.split(".")[1]) if "." in t else 0


# (company, quarter) whose 지급여력비율 keeps the quarter's own filing value (owner 2026-10-10, handoff §7-6; kics_disclosure agrees)
OWNER_KEEP_OWN_SOLVENCY = {("KR1101", "2023.2Q"), ("KR1103", "2024.1Q")}


def eff_dec(v: float) -> int:
    """decimals that carry information: a trailing zero of the print ('0.70') is padding, not precision"""
    t = f"{v:.6f}".rstrip("0").rstrip(".")
    return len(t.split(".")[1]) if "." in t else 0


def qlabel(period: str) -> str:
    m = re.fullmatch(r"FY(\d{4})_Q([1-4])", period)
    return f"{m.group(1)}.{m.group(2)}Q"


def prev_year(q: str) -> str:
    return f"{int(q[:4]) - 1}.{q[5]}Q"


def next_year(q: str) -> str:
    return f"{int(q[:4]) + 1}.{q[5]}Q"


def load_meta():
    reg = {}
    for r in json.loads((ROOT / "kics_disclosure.json").read_text(encoding="utf-8")):
        c = r.get("원보험사코드")
        if c in CODES and c not in reg:
            reg[c] = (r["원수사명"], r["티커"], r["생손보여부"])
    return reg


def tol_delta(label, a_cur, a_pri, raw_cur, raw_pri, raw_delta=""):
    if ITEMS[label][4]:
        return 1.01
    # a ratio whose 증감 is printed as a rounded integer (some filings do) or whose columns are integers
    if decimals(raw_cur) == 0 or decimals(raw_pri) == 0 or decimals(raw_delta) == 0:
        return 1.01
    return 0.021


def table_candidates(doc, kind, label_filter=None):
    """-> {label: {'cur': v, 'pri': v, 'raw': (c, p, d), 'flags': [...], 'page': n, 'unit': u}} from the first table of `kind`"""
    ents = doc["tables"].get(kind) or []
    out = {}
    for ent in ents:
        for r in ent["rows"]:
            lab = r["label"]
            if lab in out:
                continue
            vals, cells, flags = r["vals"], r["cells"], []
            cur = vals[0] if len(vals) >= 1 else None
            pri = vals[1] if len(vals) >= 2 else None
            dl = vals[2] if len(vals) >= 3 else None
            rc = cells[0] if len(cells) >= 1 else ""
            rp = cells[1] if len(cells) >= 2 else ""
            rd = cells[2] if len(cells) >= 3 else ""
            if r.get("col_mode") == "x_clash":
                flags.append("column_clash")
            if cur is not None and pri is not None and dl is not None and lab in ITEMS:
                if abs((cur - pri) - dl) > tol_delta(lab, cur, pri, rc, rp, rd):
                    flags.append(f"delta_mismatch(cur-prior={cur - pri:.2f}, printed {dl})")
            out[lab] = {"cur": cur, "pri": pri, "raw": (list(cells) + ["", "", ""])[:3], "flags": flags, "page": ent["page"], "unit": ent["unit"],
                        "via": ent.get("via", "find_tables"), "dec_cur": decimals(rc), "dec_pri": decimals(rp),
                        "flag_cells": r["flags"][:3]}
        break          # first table of the kind only
    return out


def header_check(doc, kind, q):
    ents = doc["tables"].get(kind) or []
    if not ents:
        return None
    h = ents[0]["header"]
    qs, ys = h.get("quarters") or [], h.get("years") or []
    yy = q[2:4]
    if qs:
        return "ok" if qs[:2] == [f"{yy}.{q[5]}Q", f"{int(yy) - 1:02d}.{q[5]}Q"] else f"header quarters {qs}"
    if ys:
        return "ok" if ys[:2] == [q[:4], str(int(q[:4]) - 1)] else f"header years {ys}"
    return "no_header_label"


def main() -> int:
    meta = load_meta()
    docs = json.loads((STAGE / "mi_tables.json").read_text(encoding="utf-8"))["docs"]
    report = {"header_flags": [], "cand_flags": [], "unit_fixes": [], "conflicts": [], "rounding": [], "skipped": defaultdict(list),
              "identity": [], "yield_check": [], "ratio_dup_diff": []}

    # ---- 1. candidates: (code, quarter, label) -> list of {src_q, value, raw, decimals, col, ...}
    cands = defaultdict(list)
    doc_unit = {}                     # (code, filing quarter) -> factor of the t11 amounts
    for key, doc in sorted(docs.items()):
        code, period = key.split("|")
        fq = qlabel(period)
        t11 = table_candidates(doc, "t11")
        t12 = table_candidates(doc, "t12")
        t51 = table_candidates(doc, "t51")
        for kind in ("t11", "t12", "t51"):
            hc = header_check(doc, kind, fq)
            if hc not in (None, "ok", "no_header_label"):
                report["header_flags"].append({"doc": key, "kind": kind, "check": hc})
        # unit of the amounts per table (+ sanity: 경과운용자산B must not exceed total assets by a wide margin)
        u11 = (doc["tables"].get("t11") or [{}])[0].get("unit")
        f11 = UNIT_FACTOR.get(u11, 1.0)
        a_cur = t11.get("assets", {}).get("cur")
        u51 = (doc["tables"].get("t51") or [{}])[0].get("unit")
        f51 = UNIT_FACTOR.get(u51, 1.0)
        b = t51.get("avg_inv_assets_B", {}).get("cur")
        if b is not None and a_cur is not None:
            assets_eok = a_cur * f11
            if b * f51 > 1.6 * assets_eok and b * f51 * 0.01 <= 1.6 * assets_eok:
                report["unit_fixes"].append({"doc": key, "table": "t51", "header_unit": u51, "applied": "백만원",
                                             "B_as_printed": b, "assets_eok": assets_eok})
                f51 = 0.01
        for kind, tab, f in (("t11", t11, f11), ("t12", t12, 1.0), ("t51", t51, f51)):
            for lab, c in tab.items():
                if lab not in ITEMS:
                    continue
                if SRC_KIND.get(lab) != kind and not (kind == "t51" and lab in RATIO_FALLBACK):
                    continue
                is_amt = ITEMS[lab][4]
                fac = f if is_amt else 1.0
                for col, val, dec in (("cur", c["cur"], c["dec_cur"]), ("pri", c["pri"], c["dec_pri"])):
                    if val is None:
                        continue
                    srcq = fq if col == "cur" else prev_year(fq)
                    tq = fq if col == "cur" else prev_year(fq)
                    value = round(val * fac, 6)
                    cands[(code, tq, lab)].append({
                        "filing": fq, "col": col, "kind": kind, "value": value, "printed": c["raw"][0 if col == "cur" else 1],
                        "decimals": eff_dec(value), "page": c["page"], "unit": u11 if kind == "t11" else (u51 if kind == "t51" else None),
                        "flags": c["flags"], "via": c["via"]})
                if c["flags"]:
                    report["cand_flags"].append({"doc": key, "kind": kind, "label": lab, "flags": c["flags"], "raw": c["raw"]})

    # ---- 1b. a ratio printed in 1-1 AND repeated in 5-1 of the SAME filing/column must agree (up to the rounding of the
    # coarser print); when they really differ the filing contradicts itself: both prints are set aside (owner rule:
    # "문서 안에서 쪽마다 값이 어긋나면 임의 선택하지 말고 둘 다 기록하고 비운다") and the quarter is decided by the other filing.
    def compatible(a, b, da, db):
        if abs(a - b) < 1e-9:
            return True
        return da != db and abs(a - b) <= 0.5 * 10 ** (-min(da, db)) + 1e-9

    report["disputed"] = []
    for key in list(cands):
        code, q, lab = key
        if lab not in RATIO_FALLBACK:
            continue
        cs = cands[key]
        drop = set()
        for filing in {c["filing"] for c in cs}:
            for col in ("cur", "pri"):
                a = [c for c in cs if c["filing"] == filing and c["col"] == col and c["kind"] == "t11"]
                b = [c for c in cs if c["filing"] == filing and c["col"] == col and c["kind"] == "t51"]
                if a and b and not compatible(a[0]["value"], b[0]["value"], a[0]["decimals"], b[0]["decimals"]):
                    drop.add((filing, col))
                    report["disputed"].append({"code": code, "q": q, "label": lab, "filing": filing, "col": col,
                                               "t11": a[0]["value"], "t51": b[0]["value"]})
        if drop:
            cands[key] = [c for c in cs if (c["filing"], c["col"]) not in drop]

    # ---- 2. adjudicate
    def pick(code, q, lab):
        cs = cands.get((code, q, lab), [])
        # kind priority: the canonical table first; the repeated ratio of t51 only as the fallback / cross-check
        canon = [c for c in cs if c["kind"] == SRC_KIND[lab]]
        alt = [c for c in cs if c["kind"] != SRC_KIND[lab]]
        use = canon if canon else alt
        if not use:
            return None
        own = [c for c in use if c["col"] == "cur"]
        later = [c for c in use if c["col"] == "pri"]
        o = own[0] if own else None
        l = later[0] if later else None
        note = None
        if o and l and lab in ("solv_pre", "solv_post") and (code, q) in OWNER_KEEP_OWN_SOLVENCY:
            # owner decision 2026-10-10 (handoff §7-6): the latest filing's prior column breaks the K-ICS identity of these
            # quarters, so the quarter's own filing value stays (same cells as in kics_disclosure.json)
            ch, note = o, f"owner 2026-10-10(§7-6): 최신 공시({l['filing']}) 전기 칸 {l['value']} 대신 해당 분기 공시 값 유지(K-ICS 항등식)"
        elif o and l:
            a, b = o["value"], l["value"]
            if abs(a - b) < 1e-9:
                ch, note = o, None
            elif abs(a) < 1e-12 and abs(b) > 0:        # own is a 0 print: take the non-zero
                ch, note = l, "0 인쇄(당기 칸)보다 비영(전기 칸) 채택"
            elif abs(b) < 1e-12 and abs(a) > 0:        # rule 3
                ch, note = o, "후속 공시 전기 칸 0 인쇄는 비영값을 덮지 않음(owner 규칙 3)"
            elif (o["decimals"] != l["decimals"]) and abs(a - b) <= 0.5 * 10 ** (-min(o["decimals"], l["decimals"])) + 1e-9:
                ch = o if o["decimals"] > l["decimals"] else l
                note = "반올림 차이(상충 아님): 더 정밀한 값 채택"
                report["rounding"].append({"code": code, "q": q, "label": lab, "own": a, "later": b, "chosen": ch["value"]})
            else:
                ch = l
                note = f"공시 간 상충: 최신 공시({l['filing']}) 전기 칸 채택(옛 값 {a} from {o['filing']})"
                report["conflicts"].append({"code": code, "q": q, "label": lab, "own": a, "own_filing": o["filing"], "later": b,
                                            "later_filing": l["filing"], "chosen": b})
        else:
            ch = o or l
            if ch and ch["col"] == "pri":
                note = f"{ch['filing']} 공시 전년동기(전기) 칸만 있음(해당 분기 공시 없음/판독 불가)"
        return {"value": ch["value"], "src": ch, "note": note, "own": o, "later": l}

    chosen = {}
    for (code, q, lab) in sorted(cands):
        if q < "2023.1Q":
            continue
        p = pick(code, q, lab)
        if p:
            chosen[(code, q, lab)] = p

    # ---- 3. identity 자산 = 부채 + 자본 per (company, quarter): later set only when it closes (owner rule 6)
    for code in CODES:
        for q in sorted({k[1] for k in chosen if k[0] == code}):
            trio = [chosen.get((code, q, l)) for l in ("assets", "liabilities", "equity")]
            if any(t is None for t in trio):
                continue
            a, l_, e = (t["value"] for t in trio)
            if abs(a - l_ - e) <= 1.6:
                continue
            # try the filing's own column set
            own = [t["own"] for t in trio]
            later = [t["later"] for t in trio]
            res = {"code": code, "q": q, "chosen": [a, l_, e], "resid": round(a - l_ - e, 2)}
            for name, st in (("own", own), ("later", later)):
                if all(x is not None for x in st):
                    ra = st[0]["value"] - st[1]["value"] - st[2]["value"]
                    res[f"{name}_resid"] = round(ra, 2)
            if all(x is not None for x in own) and abs(res.get("own_resid", 9e9)) <= 1.6:
                for lab, st in zip(("assets", "liabilities", "equity"), own):
                    old = chosen[(code, q, lab)]
                    chosen[(code, q, lab)] = {"value": st["value"], "src": st, "note": "최신 공시 전기 칸 세트가 항등식(자산=부채+자본)을 깨 해당 분기 공시 세트 유지(owner 규칙 6)",
                                              "own": old["own"], "later": old["later"]}
                res["action"] = "reverted to filing's own set"
            elif all(x is not None for x in later) and abs(res.get("later_resid", 9e9)) <= 1.6:
                res["action"] = "later set closes (kept)"
            else:
                res["action"] = "no set closes: loaded as chosen, flagged"
            report["identity"].append(res)

    # ---- 4. 운용자산이익률 vs 투자이익A / 경과운용자산B (same filing, same column)
    percol = defaultdict(dict)
    for (code, q, lab), cs in cands.items():
        for c in cs:
            percol[(code, c["filing"], c["col"])].setdefault(lab, c)
    for (code, filing, col), labs in sorted(percol.items()):
        y, A, B = labs.get("inv_yield"), labs.get("inv_profit_A"), labs.get("avg_inv_assets_B")
        if y and A and B and B["value"]:
            calc = A["value"] / B["value"] * 100
            rel = 0.5 / abs(B["value"]) * (1 + abs(calc) / 100 * 0) * 100  # B rounding in % of B
            allowed = 100 * (0.5 / abs(B["value"]) + abs(A["value"]) * 0.5 / B["value"] ** 2) if B["decimals"] == 0 else 0.03
            ok = abs(calc - y["value"]) <= max(allowed, 0.02) + 0.011
            report["yield_check"].append({"code": code, "filing": filing, "col": col, "printed": y["value"], "A/B": round(calc, 3), "ok": ok})


    # ---- 6. rows (skip placeholders)
    rows, prov = [], []
    for (code, q, lab), p in sorted(chosen.items(), key=lambda kv: (kv[0][0], kv[0][1], ITEMS[kv[0][2]][0])):
        item_no, name, sec, lvl, is_amt = ITEMS[lab]
        v = p["value"]
        if lab in ("solv_post", "new_contract_rate", "lapse_rate", "claims_paid_rate", "asset_mgmt_rate") or lab.startswith("persist_"):
            if abs(v) < 1e-12:
                report["skipped"][f"{lab}=0 print (해당없음)"].append(f"{code} {q}")
                continue
        nm, tk, kind = meta[code]
        rows.append({"원보험사코드": code, "원수사명": nm, "티커": tk, "생손보여부": kind, "항목번호": item_no, "항목명": name,
                     "섹션": sec, "레벨": lvl, "공시분기": q, "값": float(v)})
        prov.append({"code": code, "quarter": q, "item": item_no, "label": lab, "value": v, "filing": p["src"]["filing"],
                     "col": p["src"]["col"], "kind": p["src"]["kind"], "page": p["src"]["page"], "printed": p["src"]["printed"],
                     "unit": p["src"]["unit"], "note": p["note"],
                     "other": {"own": p["own"]["value"] if p["own"] else None, "later": p["later"]["value"] if p["later"] else None}})
    (STAGE / "mi_rows.json").write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    report["skipped"] = dict(report["skipped"])
    report["n_rows"] = len(rows)
    report["provenance"] = prov
    (STAGE / "mi_build_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    cnt = defaultdict(int)
    for r in rows:
        cnt[r["항목번호"]] += 1
    print("rows", len(rows), "by item", dict(sorted(cnt.items())))
    print("conflicts", len(report["conflicts"]), "| rounding", len(report["rounding"]), "| header flags", len(report["header_flags"]),
          "| cand flags", len(report["cand_flags"]), "| unit fixes", len(report["unit_fixes"]), "| identity issues", len(report["identity"]),
          "| yield check fails", sum(1 for x in report["yield_check"] if not x["ok"]), "/", len(report["yield_check"]),
          "| disputed 1-1/5-1 ratio prints", len(report["disputed"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
