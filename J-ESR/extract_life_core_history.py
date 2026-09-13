# -*- coding: utf-8 -*-
"""layer "core_history" — 生保 基礎利益·三利源 census + values (ticket 20260913T0400Z).

Reads the FY2025 results PDFs fetched into J-ESR/raw/fy2025_samples/others/ (WebFetch binary
save; curl was blocked for every domain this session) and emits
J-ESR/raw/fy2025_samples/life_core_history.json consumed by build_jesr_detail_json.py.

Rows are read POSITIONALLY (fitz "words" grouped by y) because these 決算説明資料 slides print a
label and its values on one visual row but the text layer interleaves them. Values are stored as
disclosed (億円 unless noted). Nothing is estimated: a row that is not printed stays null, and a
derived value (費差 = 保険関係差 − 危険差) is labelled "derived".

Run: C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe J-ESR/extract_life_core_history.py
"""
from __future__ import annotations

import json
import re
import unicodedata
from datetime import date
from pathlib import Path

import fitz

ROOT = Path(__file__).resolve().parent.parent
OTHERS = ROOT / "J-ESR" / "raw" / "fy2025_samples" / "others"
OUT = ROOT / "J-ESR" / "raw" / "fy2025_samples" / "life_core_history.json"

NUM = re.compile(r"^[△▲]?(\d{1,3}(,\d{3})+|\d+)(\.\d+)?$")


def norm(s):
    return unicodedata.normalize("NFKC", s).strip()


def to_val(t):
    t = norm(t)
    neg = t.startswith("△") or t.startswith("▲")
    t = t.lstrip("△▲").replace(",", "")
    v = float(t) if "." in t else int(t)
    return -v if neg else v


def rows_of(page, ybin=3):
    rows = {}
    for x0, y0, x1, y1, w, *_ in page.get_text("words"):
        rows.setdefault(round(y0 / ybin), []).append((x0, norm(w)))
    return [[w for _, w in sorted(ws)] for _, ws in sorted(rows.items())]


def row_values(page, label_rx, n=2):
    """numbers on the first visual row whose first cell matches label_rx (left→right)."""
    for r in rows_of(page):
        if r and re.search(label_rx, r[0]):
            nums = [to_val(t) for t in r if NUM.match(t)]
            if len(nums) >= n:
                return nums[:n], " | ".join(r)
    return None, None


def line_values_after(page, label_rx, n):
    """text-layer fallback: the n numeric lines right after the label line."""
    lines = [norm(l) for l in page.get_text("text").splitlines() if l.strip()]
    for i, ln in enumerate(lines):
        if re.search(label_rx, ln):
            nums = []
            for t in lines[i + 1:i + 1 + n + 4]:
                if NUM.match(t):
                    nums.append(to_val(t))
                if len(nums) == n:
                    return nums, ln
    return None, None


def sumitomo():
    d = fitz.open(str(OTHERS / "sumitomolife_260526_results.pdf"))
    p15, p6 = d[14], d[5]
    out = dict(company_en="Sumitomo Life Insurance", company_jp="住友生命保険", scope="solo", unit_disclosed="JPY_100million",
               source_pdf="J-ESR/raw/fy2025_samples/others/sumitomolife_260526_results.pdf",
               source_url="https://www.sumitomolife.co.jp/about/pdf/company/ir/settlement/260526.pdf",
               doc_type="2025年度決算(案)説明用資料 (2026-05-26, 18p)", values={}, labels_ja={}, pages={}, notes=[])
    # solo 基礎利益 (百万円) p15
    v, raw = row_values(p15, r"^住友生命$")
    if v:
        out["values"]["hist_core_profit"] = {"FY2024": round(v[0] / 100, 1), "FY2025": round(v[1] / 100, 1)}
        out["labels_ja"]["hist_core_profit"] = "基礎利益 住友生命 (百万円→億円 ÷100)"
        out["pages"]["hist_core_profit"] = 15
        out["notes"].append(f"hist_core_profit raw 百万円 row: {raw}")
    for iid, rx, ja in (("hist_insurance_margin", r"^保険関係差$", "保険関係差"), ("hist_mortality_margin", r"^うち危険差$", "うち危険差"),
                        ("hist_interest_margin", r"^順ざや額$", "順ざや額")):
        v, raw = row_values(p15, rx)
        if v:
            out["values"][iid] = {"FY2024": v[0], "FY2025": v[1]}
            out["labels_ja"][iid], out["pages"][iid] = ja, 15
    ins, mort = out["values"].get("hist_insurance_margin"), out["values"].get("hist_mortality_margin")
    if ins and mort:
        out["values"]["hist_expense_margin"] = {fy: ins[fy] - mort[fy] for fy in ins}
        out["labels_ja"]["hist_expense_margin"] = "derived = 保険関係差 − うち危険差 (費差 단독 행 없음)"
        out["pages"]["hist_expense_margin"] = 15
    # group 5-year (p6 chart): 3971/3375/2613/3056/4081 — text layer only, labelled group
    lines = [norm(l) for l in p6.get_text("text").splitlines() if l.strip()]
    i = next((k for k, l in enumerate(lines) if l.startswith("2025年度") and "億円" in l), None)
    if i is not None:
        nums = [to_val(t) for t in lines[i + 1:i + 6] if NUM.match(t)]
        if len(nums) == 5:
            out["values"]["hist_core_profit_group"] = dict(zip(["FY2021", "FY2022", "FY2023", "FY2024", "FY2025"], nums))
            out["labels_ja"]["hist_core_profit_group"] = "グループ基礎利益 5개년 (2025年度から算出方法見直し, 2024年度遡及)"
            out["pages"]["hist_core_profit_group"] = 6
    out["three_source"] = dict(disclosed="partial", detail="利差(順ざや額)·危険差 직접, 費差 는 保険関係差−危険差 파생. 2개년(FY2024/FY2025)만.")
    return out


def nissay():
    d = fitz.open(str(OTHERS / "nissay_kessan202605_gaiyo.pdf"))
    p6 = d[5]
    out = dict(company_en="Nippon Life Insurance", company_jp="日本生命保険", scope="group", unit_disclosed="JPY_100million",
               source_pdf="J-ESR/raw/fy2025_samples/others/nissay_kessan202605_gaiyo.pdf",
               source_url="https://www.nissay.co.jp/sites/default/files/assets/news/files/kessan202605_gaiyo.pdf",
               doc_type="2025年度 業績の概要 (2026-05-26, 28p)", values={}, labels_ja={}, pages={}, notes=[])
    for iid, rx, ja, n in (("hist_core_profit_group", r"^基礎利益$", "基礎利益 (グループ)", 1), ("hist_interest_margin", r"^利差益$", "利差益 (国内生命保険の合計)", 1),
                           ("hist_insurance_margin", r"^保険関係損益$", "保険関係損益 (国内生命保険の合計)", 1), ("hist_core_profit", r"^日本生命$", "基礎利益 日本生命 (単体)", 1)):
        v, raw = line_values_after(p6, rx, n)
        if v:
            out["values"][iid] = {"FY2025": v[0]}
            out["labels_ja"][iid], out["pages"][iid] = ja, 6
    # FY2024 group 基礎利益 appears as the chart's left bar (10,109)
    lines = [norm(l) for l in p6.get_text("text").splitlines() if l.strip()]
    if "10,109" in lines and "hist_core_profit_group" in out["values"]:
        out["values"]["hist_core_profit_group"]["FY2024"] = 10109
        out["notes"].append("FY2024 group 基礎利益 10,109 read from the p6 bar chart label (24年度)")
    out["three_source"] = dict(disclosed="partial", detail="2분해(利差益 / 保険関係損益)만, 危険差·費差 분리 없음. 국내생보 합산(그룹) 기준. 5개년표 없음(FY2025 + 前年度比 만).")
    return out


def meiji():
    d = fitz.open(str(OTHERS / "meijiyasuda_life_close_2026_point.pdf"))
    p15 = d[14]
    out = dict(company_en="Meiji Yasuda Life Insurance", company_jp="明治安田生命保険", scope="solo", unit_disclosed="JPY_100million",
               source_pdf="J-ESR/raw/fy2025_samples/others/meijiyasuda_life_close_2026_point.pdf",
               source_url="https://www.meijiyasuda.co.jp/profile/corporate_info/disclosure/account/2025/pdf/close_2026_point.pdf",
               doc_type="2025年度決算(案) 説明資料 (2026-05-26, 26p)", values={}, labels_ja={}, pages={}, notes=[])
    for iid, rx, ja in (("hist_operating_profit", r"^業務利益", "業務利益 (=基礎利益 − 標準責任準備金積み増し・戻し入れの影響)"),
                        ("hist_insurance_margin", r"^保険関係損益", "保険関係損益 (注2: 2025年度から算出方法変更, 2024年度引き直し)"),
                        ("hist_investment_margin", r"^運用関係損益", "運用関係損益")):
        v, raw = line_values_after(p15, rx, 2)
        if v:
            out["values"][iid] = {"FY2024": v[0], "FY2025": v[1]}
            out["labels_ja"][iid], out["pages"][iid] = ja, 15
    out["three_source"] = dict(disclosed="partial", detail="基礎利益 자체가 아니라 業務利益(準備金 영향 제외) 2분해(保険関係/運用関係). 三利源 없음. 2개년만.")
    return out


def daiichi():
    """2026-09-13 owner upload: アニュアルレポート2026 분책 index_004(業績に関する諸資料). p7 = 5개년 主要指標(億円), p31 = 基礎利益の内訳(億円, 2개년).
    基礎利益 5개년 행은 2021年度 값 뒤에 (4,076)(2022年度 기준 소급 재계산) 괄호값이 끼어 있어 괄호 토큰을 버린다."""
    d = fitz.open(str(OTHERS / "daiichi_2026_index_004.pdf"))
    p7, p31 = d[6], d[30]
    out = dict(company_en="Dai-ichi Life Insurance", company_jp="第一生命保険", scope="solo", unit_disclosed="JPY_100million",
               source_pdf="J-ESR/raw/fy2025_samples/others/daiichi_2026_index_004.pdf",
               source_url="https://www.dai-ichi-life.co.jp/company/results/disclosure/2026/pdf/index_004.pdf",
               doc_type="アニュアルレポート2026 業績に関する諸資料 (2026-07, 86p)", values={}, labels_ja={}, pages={}, notes=[])
    fys = ["FY2021", "FY2022", "FY2023", "FY2024", "FY2025"]
    lines = [norm(l) for l in p7.get_text("text").splitlines() if l.strip()]
    for iid, rx, ja in (("hist_core_profit", r"^基礎利益", "基礎利益 5개년 (2021年度は旧基準, 括弧の再計算値 (4,076) は除外)"),
                        ("hist_ordinary_profit", r"^経常利益$", "経常利益 5개년"), ("hist_net_income", r"^当期純利益$", "当期純利益 5개년")):
        i = next((k for k, l in enumerate(lines) if re.search(rx, l)), None)
        if i is None:
            continue
        nums = []
        for t in lines[i + 1:i + 12]:
            if t.startswith("(") and t.endswith(")"):
                continue      # 소급 재계산 괄호값
            if NUM.match(t):
                nums.append(to_val(t))
            elif nums:
                break
            if len(nums) == 5:
                break
        if len(nums) == 5:
            out["values"][iid] = dict(zip(fys, nums)); out["labels_ja"][iid], out["pages"][iid] = ja, 7
    for iid, rx, ja in (("hist_interest_margin", r"^順ざや額$", "順ざや額"), ("hist_insurance_margin", r"^保険関係損益$", "保険関係損益"),
                        ("hist_mortality_margin", r"^うち危険差益$", "うち危険差益")):
        v, raw = line_values_after(p31, rx, 2)
        if v:
            out["values"][iid] = {"FY2024": v[0], "FY2025": v[1]}; out["labels_ja"][iid], out["pages"][iid] = ja, 31
    ins, mort = out["values"].get("hist_insurance_margin"), out["values"].get("hist_mortality_margin")
    if ins and mort:
        out["values"]["hist_expense_margin"] = {fy: ins[fy] - mort[fy] for fy in ins}
        out["labels_ja"]["hist_expense_margin"] = "derived = 保険関係損益 − うち危険差益 (費差 단독 행 없음)"; out["pages"]["hist_expense_margin"] = 31
    out["three_source"] = dict(disclosed="partial", detail="利差(順ざや額)·危険差 직접, 費差 는 保険関係損益−危険差益 파생(住友生命과 같은 구조). 基礎利益·経常利益·当期純利益 5개년은 p7 主要指標.")
    return out


def main():
    companies = dict(sumitomo_life=sumitomo(), nippon_life=nissay(), meijiyasuda_life=meiji())
    companies["dai_ichi_life"] = daiichi()
    companies["nnlife"] = dict(company_en="NN Life", company_jp="エヌエヌ生命保険", scope="solo", unit_disclosed="JPY_million",
                               source_pdf="J-ESR/raw/fy2025_samples/nnlife_2025disclosure_202607.pdf", source_url="https://www.nnlife.co.jp/pdf/company/results/NNLJ_2025Disclosure_202607.pdf",
                               doc_type="ディスクロージャー誌 2025 (2026-07)", values={"hist_core_profit": {"FY2024": 148.3, "FY2025": 185.2}},
                               labels_ja={"hist_core_profit": "基礎利益 (A) — profit 층 pl_core_profit 14,828/18,523 百万円 ÷100"}, pages={"hist_core_profit": 60},
                               notes=["三利源 표 없음 (profit 층 TABLE_ABSENT, §9-1). 5개년 主要な経営指標 p11 은 億円 — 基礎利益 행 유무 미확인(이번 티켓 범위 밖)."],
                               three_source=dict(disclosed="none", detail="三利源 표 없음"))
    checks = []
    s = companies["sumitomo_life"]["values"]
    if all(k in s for k in ("hist_core_profit", "hist_insurance_margin", "hist_interest_margin")):
        for fy in ("FY2024", "FY2025"):
            lhs, rhs = s["hist_core_profit"][fy], s["hist_insurance_margin"][fy] + s["hist_interest_margin"][fy]
            checks.append(dict(id=f"L01_sumitomo_core_eq_margins_{fy}", formula="基礎利益(住友生命) ≈ 保険関係差 + 順ざや額 (±2 億円)", lhs=lhs, rhs=rhs, tol=2, **{"pass": abs(lhs - rhs) <= 2}))
    m = companies["meijiyasuda_life"]["values"]
    if all(k in m for k in ("hist_operating_profit", "hist_insurance_margin", "hist_investment_margin")):
        for fy in ("FY2024", "FY2025"):
            lhs, rhs = m["hist_operating_profit"][fy], m["hist_insurance_margin"][fy] + m["hist_investment_margin"][fy]
            checks.append(dict(id=f"L02_meiji_operating_eq_margins_{fy}", formula="業務利益 == 保険関係損益 + 運用関係損益 (±1)", lhs=lhs, rhs=rhs, tol=1, **{"pass": abs(lhs - rhs) <= 1}))
    dv = companies["dai_ichi_life"]["values"]
    if all(k in dv for k in ("hist_core_profit", "hist_insurance_margin", "hist_interest_margin")):
        for fy in ("FY2024", "FY2025"):
            lhs, rhs = dv["hist_core_profit"][fy], dv["hist_insurance_margin"][fy] + dv["hist_interest_margin"][fy]
            checks.append(dict(id=f"L03_daiichi_core_eq_margins_{fy}", formula="基礎利益(第一生命) == 順ざや額 + 保険関係損益 (±1 億円)", lhs=lhs, rhs=rhs, tol=1, **{"pass": abs(lhs - rhs) <= 1}))
    out = dict(generated_at=str(date.today()), generator="J-ESR/extract_life_core_history.py", layer="core_history", unit_note="億円 unless unit_disclosed says otherwise",
               fiscal_years=["FY2021", "FY2022", "FY2023", "FY2024", "FY2025"], companies=companies, checks=checks)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({k: c["values"] for k, c in companies.items()}, ensure_ascii=False, indent=1))
    for c in checks:
        print("PASS" if c["pass"] else "FAIL", c["id"], c["lhs"], c["rhs"])
    return 0 if all(c["pass"] for c in checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
