# -*- coding: utf-8 -*-
"""layer "bs" — J-GAAP 貸借対照表 요약 (ticket 20260913T1300Z, T자형 BS 패널용).

Reads the FY2025 PDFs already under J-ESR/raw/fy2025_samples/ (+others/) — never downloads — and
emits J-ESR/raw/fy2025_samples/extracted_bs_values.json consumed by build_jesr_detail_json.py
(build_bs_block). Page/text helpers (page_lines / merge_vertical / unwrap_paren_lines / grab /
GidDoc) are imported from extract_esr_template_samples.py so the known traps (MSI one-glyph-per-line
labels, Sompo Japan glyph-id fonts) are not re-solved here.

Row ids/labels follow the ticket table; rows not printed are omitted, the three totals are required.
Residual rows (bs_other_assets / bs_other_liabilities / bs_other_equity) are derived = total − Σ listed.
Values are stored in JPY_million; a source printed in 億円 is multiplied by 100 and its checks use
tolerance 100 (= ±1 in the disclosed unit). Nothing is estimated: a column the source does not print
(前期末 on the 5月 決算説明資料 slides, or on the EBS financial-accounting column) stays null.

Run: C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe J-ESR/extract_bs.py
"""
from __future__ import annotations

import json
import re
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fitz  # noqa: E402

from extract_esr_template_samples import (  # noqa: E402
    COMPANIES, SAMPLES, GidDoc, grab, is_val, merge_vertical, page_lines, to_val, unwrap_paren_lines,
)

OUT = SAMPLES / "extracted_bs_values.json"
OTHERS = SAMPLES / "others"

# ---- row spec (ticket table). section: a=資産の部 l=負債の部 n=純資産の部 ----
ROWS = [
    ("bs_assets_total", "資産合計", 0, "=", None, "a", [r"^資産の部合計$", r"^資産合計$", r"^総資産$", r"^うち総資産$"]),
    ("bs_cash", "現金及び預貯金", 1, "+", "bs_assets_total", "a", [r"^現金及び預貯金$", r"^うち現預金・コールローン$"]),
    ("bs_securities", "有価証券", 1, "+", "bs_assets_total", "a", [r"^有価証券$", r"^うち有価証券$"]),
    ("bs_loans", "貸付金", 1, "+", "bs_assets_total", "a", [r"^貸付金$", r"^うち貸付金$"]),
    ("bs_tangible", "有形固定資産", 1, "+", "bs_assets_total", "a", [r"^有形固定資産$", r"^うち有形固定資産$"]),
    ("bs_liabilities_total", "負債合計", 0, "=", None, "l", [r"^負債の部合計$", r"^負債合計$", r"^総負債$", r"^負債$"]),
    ("bs_policy_reserves_total", "保険契約準備金", 1, "+", "bs_liabilities_total", "l",
     [r"^保険契約準備金$", r"^うち保険契約準備金$", r"^保険負債\(保険契約準備金\)合計$"]),
    ("bs_outstanding_claims", "支払備金", 2, "+", "bs_policy_reserves_total", "l", [r"^支払備金$", r"^うち支払備金$"]),
    ("bs_policy_reserves", "責任準備金", 2, "+", "bs_policy_reserves_total", "l", [r"^責任準備金$", r"^うち責任準備金$"]),
    ("bs_policyholder_dividend_reserve", "契約者配当準備金", 2, "+", "bs_policy_reserves_total", "l",
     [r"^契約者配当準備金$", r"^社員配当準備金$", r"^うち契約者配当準備金$", r"^うち社員配当準備金$"]),
    ("bs_bonds", "社債", 1, "+", "bs_liabilities_total", "l", [r"^社\s?債$", r"^うち社債$"]),
    ("bs_net_assets_total", "純資産合計", 0, "=", None, "n", [r"^純資産の部合計$", r"^純資産合計$", r"^純資産$"]),
    # capital_and_surplus is assembled from the private parts below (stock: 資本金+資本剰余金 / mutual: 基金+基金償却積立金)
    ("_capital_stock", "資本金", None, None, None, "n", [r"^(純資産の部)?資本金$"]),
    ("_capital_surplus", "資本剰余金", None, None, None, "n", [r"^資本剰余金合計$", r"^資本剰余金$"]),
    ("_fund", "基金", None, None, None, "n", [r"^基金$"]),
    ("_fund_redemption", "基金償却積立金", None, None, None, "n", [r"^基金償却積立金$"]),
    ("_fund_combined", "基金・基金償却積立金", None, None, None, "n", [r"^うち基金・基金償却積立金$", r"^基金・基金償却積立金$"]),
    ("bs_retained_earnings", "利益剰余金", 1, "+", "bs_net_assets_total", "n",
     [r"^利益剰余金合計$", r"^利益剰余金$", r"^剰余金$", r"^うち連結剰余金$", r"^うち剰余金$"]),
    ("bs_valuation_diff", "その他有価証券評価差額金", 1, "+", "bs_net_assets_total", "n",
     [r"^その他有価証券評価差額金$", r"^うちその他有価証券評価差額金$"]),
]
SECTION_RX = {
    "a": r"^[（(]?資産の部[）)]?$",
    "l": r"^[（(]?負債の部[）)]?$",
    "n": r"^[（(]?純資産の部",
}
MUTUAL = {"nippon_life", "meijiyasuda_life", "sumitomo_life"}

# layout: prev_cur = [prev, cur(, diff)] / pct = [prev, %, cur, %(, diff)] on top rows / cur_only = [cur(, diff)] /
#         ebs_first = EBS column イ(財務会計ベース) = J-GAAP current only
BS_COMPANIES = [
    dict(key="au_nonlife", company_en="au Non-Life", pdf="au_nonlife_disclo_260730_4of5.pdf", pages=[14], layout="pct",
         mv=True, unit="JPY_million", scope="solo", doc="ディスクロージャー誌 業績データ 貸借対照表"),
    # 2026-09-13 orchestrator: 본편(owner 업로드 60p) p39~40 貸借対照表 — 3개년을 「열 우선」으로 찍은 세로글리프 표
    # (라벨 열 전체 → 2023 금액열 → 구성비 → 2024 → … → 合計 행만 행 우선). 라벨은 글리프 병합이 안 돼 고정 목록으로 index 매핑.
    dict(key="meijiyasuda_nonlife", company_en="Meiji Yasuda Non-Life", pdf="meijiyasuda_nonlife_20260729_main.pdf",
         pages=[39, 40], layout="col_major_3yr", unit="JPY_million", scope="solo", doc="ディスクロージャー誌 本編 計算書類等 貸借対照表"),
    dict(key="tokiomarine_nichido", company_en="Tokio Marine & Nichido Fire", pdf="others/tmnf_2026_full.pdf", pages=[98, 99],
         layout="prev_cur", unit="JPY_million", scope="solo", doc="ディスクロージャー誌 本編 計算書類 貸借対照表"),
    dict(key="mitsui_sumitomo", company_en="Mitsui Sumitomo Insurance", pdf="others/msi_2026_full.pdf", pages=[106], layout="prev_cur",
         mv=True, up=True, unit="JPY_million", scope="solo", doc="ディスクロージャー誌 本編 業績データ 貸借対照表"),
    dict(key="sompo_japan", company_en="Sompo Japan Insurance", pdf="others/sompojapan_2026_full.pdf", pages=[130, 131], layout="prev_cur",
         gid=True, unit="JPY_million", scope="solo", doc="ディスクロージャー誌 本編 業績データ 貸借対照表"),
    dict(key="nnlife", company_en="NN Life", pdf="nnlife_2025disclosure_202607.pdf", pages=[43, 44], layout="pct",
         unit="JPY_million", scope="solo", doc="ディスクロージャー誌 財産の状況 貸借対照表"),
    dict(key="nippon_life", company_en="Nippon Life", pdf="others/nissay_kessan202605_gaiyo.pdf", pages=[9], layout="cur_only",
         unit="JPY_100million", scope="group", doc="決算説明資料(5月) 連結貸借対照表 要約",
         notes=["連結・億円・当期末のみの要約スライド(純資産内訳なし)。前期末は前年度末比(%)しか無いので null。"]),
    dict(key="meijiyasuda_life", company_en="Meiji Yasuda Life", pdf="others/meijiyasuda_life_close_2026_point.pdf", pages=[10], layout="cur_only",
         unit="JPY_100million", scope="group", doc="決算説明資料(5月) 連結貸借対照表 要約",
         notes=["連結・億円・当期末のみの要約スライド。前年度末差(増減額)は印字されるが前期末を逆算しない(推定禁止)。"]),
    # 2026-09-13 orchestrator: 7월 資料編(REPORT SUMISEI 2026 資料編, 162p) 확보 → 単体 貸借対照表 p58(2개년, 百万円). 社債 라벨은 「社　債」(전각 공백).
    dict(key="sumitomo_life", company_en="Sumitomo Life", pdf="others/sumitomolife_2026_repodata.pdf", pages=[58], layout="prev_cur",
         unit="JPY_million", scope="solo", doc="ディスクロージャー誌 資料編 計算書類 貸借対照表"),
    # 2026-09-13 owner 업로드: アニュアルレポート2026 분책 index_004(業績に関する諸資料, 86p). 単体 貸借対照表 = 책 p73~74 = 분책 p23~24(2개년, 百万円).
    dict(key="dai_ichi_life", company_en="Dai-ichi Life", pdf="others/daiichi_2026_index_004.pdf", pages=[23, 24], layout="prev_cur",
         unit="JPY_million", scope="solo", doc="アニュアルレポート2026 経理の状況 貸借対照表"),
]


def open_doc(comp):
    path = SAMPLES / comp["pdf"]
    doc = fitz.open(str(path))
    return (GidDoc(doc) if comp.get("gid") else doc), path


def split_sections(lines):
    """{'a'|'l'|'n': [(p, line), ...]} — a marker not found ⇒ that section = all lines."""
    idx = {}
    for i, (_p, ln) in enumerate(lines):
        for k, rx in SECTION_RX.items():
            if k not in idx and re.match(rx, ln):
                idx[k] = i
    order = sorted(idx.items(), key=lambda kv: kv[1])
    out = {}
    for n, (k, start) in enumerate(order):
        end = order[n + 1][1] if n + 1 < len(order) else len(lines)
        out[k] = lines[start:end]
    for k in SECTION_RX:
        out.setdefault(k, lines)
    return out


def pick_pair(toks, layout):
    n = len(toks)
    if layout == "prev_cur":
        return (to_val(toks[0]), to_val(toks[1])) if n >= 2 else (None, None)
    if layout == "pct":
        if n >= 4:
            return to_val(toks[0]), to_val(toks[2])
        return (to_val(toks[0]), to_val(toks[1])) if n >= 2 else (None, None)
    if layout in ("cur_only", "ebs_first"):
        return None, to_val(toks[0])
    raise ValueError(layout)


# ---- Meiji Yasuda Non-Life: column-major 3-year layout (main volume p39 資産 / p40 負債·純資産) ----
# 각 섹션: (섹션 헤더) → 라벨 글리프들 → [연도별: 금액 N개 → 구성비 K개] × 3 → 合計 라벨 → 合計 행(금액·구성비 × 3, 행 우선).
# 라벨 목록은 FY2025 본편의 인쇄 순서(법정 양식, 회사 고정). N 이 안 맞으면 not_obtained 로 떨어뜨린다(추정 금지).
COLMAJOR_ROWS = {
    "a": ["現金及び預貯金", "預貯金", "金銭の信託", "有価証券", "国債", "株式", "その他の証券", "有形固定資産", "土地", "建物", "建設仮勘定",
          "その他の有形固定資産", "無形固定資産", "ソフトウェア", "その他の無形固定資産", "その他資産", "未収保険料", "代理店貸", "共同保険貸",
          "再保険貸", "外国再保険貸", "未収金", "未収収益", "預託金", "地震保険預託金", "仮払金", "繰延税金資産", "貸倒引当金"],
    "l": ["保険契約準備金", "支払備金", "責任準備金", "その他負債", "共同保険借", "再保険借", "外国再保険借", "債券貸借取引受入担保金",
          "未払法人税等", "預り金", "前受収益", "未払金", "仮受金", "賞与引当金", "特別法上の準備金", "価格変動準備金"],
    "n": ["資本金", "資本剰余金", "資本準備金", "その他資本剰余金", "利益剰余金", "利益準備金", "その他利益剰余金", "繰越利益剰余金",
          "株主資本合計", "その他有価証券評価差額金", "評価・換算差額等合計"],
}
COLMAJOR_TOTAL_LABEL = {"a": "資産の部合計", "l": "負債の部合計", "n": "純資産の部合計"}
COLMAJOR_MAP = {  # ROWS id -> (section, label)   (貸付金·社債 없음, 契約者配当準備金 없음)
    "bs_cash": ("a", "現金及び預貯金"), "bs_securities": ("a", "有価証券"), "bs_tangible": ("a", "有形固定資産"),
    "bs_policy_reserves_total": ("l", "保険契約準備金"), "bs_outstanding_claims": ("l", "支払備金"), "bs_policy_reserves": ("l", "責任準備金"),
    "_capital_stock": ("n", "資本金"), "_capital_surplus": ("n", "資本剰余金"), "bs_retained_earnings": ("n", "利益剰余金"),
    "bs_valuation_diff": ("n", "その他有価証券評価差額金"),
}


def _is_amount(tok):
    return bool(re.match(r"^[△▲-]?[\d,]*\d?$", tok)) and "." not in tok and tok not in ("",)


def _is_pct(tok):
    return bool(re.match(r"^[△▲-]?\d+\.\d+$", tok))


def _colmajor_section(lines, sec):
    """lines: [(p, ln)] of one page. Returns ({label: (prev, cur)}, (total_prev, total_cur)) or (None, None)."""
    hdr = {"a": "(資産の部)", "l": "(負債の部)", "n": "(純資産の部)"}[sec]
    toks = [ln for _p, ln in lines]
    try:
        start = next(i for i, t in enumerate(toks) if t == hdr)
    except StopIteration:
        return None, None
    # merged label of the 合計 row (glyph-per-line) — find where the total label starts: first run of single glyphs after the numbers
    labels = COLMAJOR_ROWS[sec]
    n = len(labels)
    # numeric stream after the header until the total label glyph run
    nums, k = [], start + 1
    seen_numbers = False
    while k < len(toks):
        t = toks[k]
        if _is_amount(t) or _is_pct(t):
            nums.append(t); seen_numbers = True
        elif seen_numbers and len(t) == 1:
            break   # 合計 라벨 글리프 시작
        k += 1
    # split into runs: amounts / pct alternating
    runs, cur_run, cur_kind = [], [], None
    for t in nums:
        kind = "p" if _is_pct(t) else "a"
        if cur_kind is None or kind == cur_kind:
            cur_run.append(t); cur_kind = kind
        else:
            runs.append((cur_kind, cur_run)); cur_run, cur_kind = [t], kind
    if cur_run:
        runs.append((cur_kind, cur_run))
    amt_runs = [r for kd, r in runs if kd == "a"]
    if len(amt_runs) < 3 or any(len(r) != n for r in amt_runs[:3]):
        return None, None
    prev_run, cur_run3 = amt_runs[1], amt_runs[2]
    vals = {lab: (to_val(prev_run[i]), to_val(cur_run3[i])) for i, lab in enumerate(labels)}
    # total row: after the glyph label run, 6 tokens (amt pct) × 3 → prev = 3rd, cur = 5th
    while k < len(toks) and not (_is_amount(toks[k]) and toks[k] not in ("-",)):
        k += 1
    tot = toks[k:k + 6]
    if len(tot) == 6 and _is_amount(tot[2]) and _is_amount(tot[4]):
        total = (to_val(tot[2]), to_val(tot[4]))
    else:
        total = (None, None)
    return vals, total


def extract_colmajor(comp, doc, path):
    values, pages, raw = {}, {}, {}
    by_page = {}
    for pg in comp["pages"]:
        by_page[pg] = page_lines(doc, [pg])
    sec_vals, sec_tot, sec_page = {}, {}, {}
    for sec in ("a", "l", "n"):
        for pg, lines in by_page.items():
            v, t = _colmajor_section(lines, sec)
            if v:
                sec_vals[sec], sec_tot[sec], sec_page[sec] = v, t, pg
                break
    for rid, (sec, lab) in COLMAJOR_MAP.items():
        v = (sec_vals.get(sec) or {}).get(lab)
        if v and not (v[0] is None and v[1] is None):
            values[rid] = {"prev": v[0], "cur": v[1]}; pages[rid] = sec_page[sec]; raw[rid] = f"colmajor {lab} {v}"
    for rid, sec in (("bs_assets_total", "a"), ("bs_liabilities_total", "l"), ("bs_net_assets_total", "n")):
        t = sec_tot.get(sec)
        if t and not (t[0] is None and t[1] is None):
            values[rid] = {"prev": t[0], "cur": t[1]}; pages[rid] = sec_page[sec]; raw[rid] = f"colmajor total {t}"
    return values, pages, raw, str(path.relative_to(SAMPLES.parent.parent)).replace("\\", "/")


def extract(comp):
    doc, path = open_doc(comp)
    if comp["layout"] == "col_major_3yr":
        return extract_colmajor(comp, doc, path)
    lines = page_lines(doc, comp["pages"])
    if comp.get("mv"):
        lines = merge_vertical(lines)
    if comp.get("up"):
        lines = unwrap_paren_lines(lines)
    # NN Life prints negatives as "△ 7,608" (space after the sign) → is_val() would drop the row
    lines = [(p, re.sub(r"^([△▲])\s+", r"\1", ln)) for p, ln in lines]
    secs = split_sections(lines)
    values, pages, raw = {}, {}, {}
    for rid, _ja, _d, _s, _parent, sec, aliases in ROWS:
        for rx in aliases:
            r = grab(secs[sec], 0, [rx], skip_limit=0)
            if r and r[0]:
                toks, p, _j = r
                prev, cur = pick_pair(toks, comp["layout"])
                if cur is None and prev is None:
                    continue
                values[rid] = {"prev": prev, "cur": cur}
                pages[rid] = p
                raw[rid] = " | ".join(toks)
                break
    return values, pages, raw, str(path.relative_to(SAMPLES.parent.parent)).replace("\\", "/")


def build_tree(values, comp):
    scale = 100 if comp["unit"] == "JPY_100million" else 1

    def v(rid, col):
        x = (values.get(rid) or {}).get(col)
        return None if x is None else x * scale

    def sub(total, parts, col):
        t = v(total, col)
        if t is None:
            return None
        s = sum(v(p, col) or 0 for p in parts)
        return t - s

    mutual = comp["key"] in MUTUAL
    cap = {}
    for col in ("prev", "cur"):
        if mutual:
            if values.get("_fund_combined"):
                cap[col] = v("_fund_combined", col)
            else:
                parts = [v("_fund", col), v("_fund_redemption", col)]
                cap[col] = None if all(x is None for x in parts) else sum(x or 0 for x in parts)
        else:
            parts = [v("_capital_stock", col), v("_capital_surplus", col)]
            cap[col] = None if all(x is None for x in parts) else sum(x or 0 for x in parts)
    cap_label = "基金・基金償却積立金" if mutual else "資本金・資本剰余金"

    rows = []

    def add(rid, ja, depth, sign, parent, prev, cur, derived=False):
        if prev is None and cur is None:
            return
        rows.append({"id": rid, "label_ja": ja, "depth": depth, "sign": sign, "cur": cur, "prev": prev,
                     "parent": parent, "derived": derived})

    for rid, ja, depth, sign, parent, _sec, _al in ROWS:
        if rid.startswith("_"):
            continue
        if rid == "bs_policyholder_dividend_reserve" and mutual:
            ja = "社員配当準備金"   # 相互会社 표기(住友生命·日本生命·明治安田生命)
        add(rid, ja, depth, sign, parent, v(rid, "prev"), v(rid, "cur"))
        if rid == "bs_tangible":
            add("bs_other_assets", "その他資産", 1, "+", "bs_assets_total",
                sub("bs_assets_total", ["bs_cash", "bs_securities", "bs_loans", "bs_tangible"], "prev"),
                sub("bs_assets_total", ["bs_cash", "bs_securities", "bs_loans", "bs_tangible"], "cur"), derived=True)
        if rid == "bs_bonds":
            add("bs_other_liabilities", "その他負債", 1, "+", "bs_liabilities_total",
                sub("bs_liabilities_total", ["bs_policy_reserves_total", "bs_bonds"], "prev"),
                sub("bs_liabilities_total", ["bs_policy_reserves_total", "bs_bonds"], "cur"), derived=True)
        if rid == "bs_net_assets_total":
            add("bs_capital_and_surplus", cap_label, 1, "+", "bs_net_assets_total", cap["prev"], cap["cur"])
    # residual equity after retained/valuation rows
    ret = {c: v("bs_retained_earnings", c) for c in ("prev", "cur")}
    val = {c: v("bs_valuation_diff", c) for c in ("prev", "cur")}
    oe = {}
    for c in ("prev", "cur"):
        t = v("bs_net_assets_total", c)
        oe[c] = None if t is None else t - sum(x or 0 for x in (cap[c], ret[c], val[c]))
    add("bs_other_equity", "その他(純資産)", 1, "+", "bs_net_assets_total", oe["prev"], oe["cur"], derived=True)
    # order: fixed ticket order
    order = ["bs_assets_total", "bs_cash", "bs_securities", "bs_loans", "bs_tangible", "bs_other_assets",
             "bs_liabilities_total", "bs_policy_reserves_total", "bs_outstanding_claims", "bs_policy_reserves",
             "bs_policyholder_dividend_reserve", "bs_bonds", "bs_other_liabilities",
             "bs_net_assets_total", "bs_capital_and_surplus", "bs_retained_earnings", "bs_valuation_diff", "bs_other_equity"]
    rows.sort(key=lambda r: order.index(r["id"]))
    return rows, scale


def run_checks(rows, tol):
    by = {r["id"]: r for r in rows}

    def g(rid, col):
        return (by.get(rid) or {}).get(col)

    out = {}
    res = []
    for col in ("prev", "cur"):
        a, l, n = g("bs_assets_total", col), g("bs_liabilities_total", col), g("bs_net_assets_total", col)
        if None not in (a, l, n):
            res.append(abs(a - (l + n)) <= tol)
    out["assets_eq_liab_plus_equity"] = all(res) if res else None
    res = []
    for col in ("prev", "cur"):
        t = g("bs_policy_reserves_total", col)
        parts = [g(k, col) for k in ("bs_outstanding_claims", "bs_policy_reserves", "bs_policyholder_dividend_reserve")]
        parts = [p for p in parts if p is not None]
        # closable only when both 支払備金 and 責任準備金 are printed (5月 slides print 責任準備金 alone → None)
        if t is not None and len(parts) >= 2:
            # 항 개수만큼 百万円 절사 허용(住友生命·第一生命 3항 합이 합계와 1~2 차이 실측, by_line B01 과 같은 규칙)
            res.append(abs(t - sum(parts)) <= max(tol, len(parts)))
    out["policy_reserves_sum_ok"] = all(res) if res else None
    res = []
    for rid in ("bs_other_assets", "bs_other_liabilities"):
        for col in ("prev", "cur"):
            x = g(rid, col)
            if x is not None:
                res.append(x >= 0)
    out["no_negative_residual"] = all(res) if res else None
    return out


def main():
    companies = {}
    for comp in BS_COMPANIES:
        key = comp["key"]
        if comp.get("not_obtained"):
            companies[key] = {"company_en": comp["company_en"], "status": "not_obtained", "scope": comp["scope"],
                              "source_doc": comp["doc"], "notes": [comp["not_obtained"]]}
            print(f"{key}: not_obtained — {comp['not_obtained']}")
            continue
        values, pages, raw, rel = extract(comp)
        rows, scale = build_tree(values, comp)
        ids = {r["id"] for r in rows}
        missing_totals = [t for t in ("bs_assets_total", "bs_liabilities_total", "bs_net_assets_total") if t not in ids]
        if missing_totals:
            companies[key] = {"company_en": comp["company_en"], "status": "not_obtained", "scope": comp["scope"],
                              "source_doc": rel, "notes": [f"totals missing: {missing_totals}"] + comp.get("notes", [])}
            print(f"{key}: not_obtained — totals missing {missing_totals}")
            continue
        checks = run_checks(rows, tol=1 * scale)
        companies[key] = {
            "company_en": comp["company_en"], "status": "extracted", "scope": comp["scope"], "as_of": "2026-03-31",
            "unit": "JPY_million", "unit_disclosed": comp["unit"], "source_doc": rel, "doc_type": comp["doc"],
            "pages": {"assets": pages.get("bs_assets_total"), "liabilities": pages.get("bs_liabilities_total"),
                      "net_assets": pages.get("bs_net_assets_total")},
            "layout": comp["layout"], "tree": rows, "checks": checks, "raw": raw, "notes": comp.get("notes", []),
        }
        print(f"{key}: rows={len(rows)} checks={checks} assets_cur={[r['cur'] for r in rows if r['id']=='bs_assets_total']}")
        with open(OUT, "w", encoding="utf-8", newline="\n") as f:  # save as we go
            json.dump({"generated": date.today().isoformat(), "companies": companies}, f, ensure_ascii=False, indent=2)
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        json.dump({"generated": date.today().isoformat(), "companies": companies}, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
