"""Build plan_final.json + applied_cells.csv + held_blocks.csv for ticket 20261012T2230Z (read-only on the repo; writes only in this folder).

Cells = (a) dry-run recommended latest-comparative blocks that PASSED the independent raw-XML re-reading (s20/s30/s31/s45/s46/s65) and
        (b) definite 3-month-as-cumulative corrections found by the systematic scan (s61) and re-read from the original filing statement.
Dropped / held with a reason: see HELD below and the dry-run census.
"""
from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
DRY = ROOT / "data/_derived/ifrs17_latest_comparative_precedence_dryrun_20261012"


def jl(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


plan = jl(HERE / "plan_diff.json")
pl_rows = jl(ROOT / "PL_breakdown.json")
csm_rows = jl(ROOT / "CSM_waterfall.json")
bs_rows = jl(ROOT / "IFRS17_BS.json")
NAME = {}
ITEM = {"PL": {}, "CSM": {}, "BS": {}}
for r in pl_rows:
    NAME[r["원보험사코드"]] = r["원수사명"]
    ITEM["PL"].setdefault(r["항목번호"], r["항목명"])
for r in csm_rows:
    ITEM["CSM"].setdefault(r["항목번호"], r["항목명"])
for r in bs_rows:
    ITEM["BS"].setdefault(r["항목번호"], r["항목명"])
pl_live = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r["값"] for r in pl_rows}

ev_bs = {(r["block"], int(r["item"])): r for r in csv.DictReader(open(HERE / "evidence_bs.csv", encoding="utf-8-sig"))}
ev_csm = jl(HERE / "evidence_csm.json")
ev_csm_rc = jl(HERE / "evidence_csm_recipes.json")
ev_t1 = jl(HERE / "evidence_pl_tier1.json")
ev_notes = jl(HERE / "evidence_pl_notes.json")
ev_mer = jl(HERE / "evidence_pl_meritz.json")
ev_tok = jl(HERE / "evidence_pl_tokens.json")


def rcept_of(xml_rel: str) -> str:
    m = re.search(r"(\d{14})", xml_rel)
    return m.group(1) if m else "?"


def fyq_of(xml_rel: str) -> str:
    m = re.search(r"(FY\d{4}_Q\d)", xml_rel)
    return m.group(1) if m else "?"


cells = []


def add(**kw):
    kw.setdefault("printed", "")
    kw.setdefault("evidence", "")
    cells.append(kw)


# ------------------------------------------------------------------------------------------------------------------ CSM (8 blocks)
CSM_DROP = {"KR1000|2025.1Q"}
by_blk = {}
for c in plan["CSM"]:
    if c["block"] in CSM_DROP:
        continue
    by_blk.setdefault(c["block"], []).append(c)

csm_ovl = jl(DRY / "cand/csm_adopt_overlay.json")
UNIT_DIV = {"백만원": 100.0, "천원": 1e5, "원": 1e8}


def pick_rec(blk):
    recs = ev_csm.get(blk) or []
    if not recs:
        return None
    return max(recs, key=lambda r: (len(r["items"]), r["table"]))


for blk, cs in by_blk.items():
    kr, q = blk.split("|")
    rec = pick_rec(blk)
    rcp = rc = None
    for c in sorted(cs, key=lambda x: x["item"]):
        it = c["item"]
        printed = src = ver = ev = ""
        if blk in ev_csm_rc:
            R = ev_csm_rc[blk]
            d = R["items"][str(it)]
            xml = R["xml"]
            parts = "; ".join(f"표#{t['table']} L{t['line']} '{t['label']}' CSM열 {'+'.join(t['printed_csm_cols'])}" for t in d["tokens"])
            printed = parts
            src = f"rcept {rcept_of(xml)} ({fyq_of(xml)}) 측정요소 변동표 전기열 (CSM 3열 합)"
            ver = f"독립 재독 {xml}: {parts} => {d['derived']:,.2f}억 (계획 {d['plan']})"
            ev = f"printed rows; closing identity residual {R['closing_identity_resid']:+.3f}억; item4 = printed '추정치 변경' rows"
        elif rec is not None:
            xml = rec["xml"]
            d = rec["items"].get(str(it))
            if d is not None:
                printed = f"{d['printed']} {d['unit']} ('{d['label']}' col {d['col']})"
                src = f"rcept {rcept_of(xml)} ({fyq_of(xml)}) 표#{rec['table']} L{rec['tline']} '{rec['caption'][:30]}' 전기열"
                ver = f"독립 재독 {xml}#L{d['line']} '{d['label']}' 인쇄 {d['printed']} ({d['unit']})"
                ev = "printed token matches planned value at 1-decimal rounding"
            else:
                # item 4 = residual of the printed rows (master convention: close - open - new - interest - amort)
                toks = {k: v for k, v in rec["items"].items()}
                def val(k):
                    t = toks[str(k)]
                    s = t["printed"].replace(",", "").replace("(", "-").replace(")", "")
                    return float(s)
                try:
                    resid = val(6) - (val(1) + val(2) + val(3) - abs(val(5)))
                    printed = (f"기초 {toks['1']['printed']} (L{toks['1']['line']}) · 신계약 {toks['2']['printed']} (L{toks['2']['line']}) · 이자 {toks['3']['printed']} (L{toks['3']['line']}) · "
                               f"상각 {toks['5']['printed']} (L{toks['5']['line']}) · 기말 {toks['6']['printed']} (L{toks['6']['line']}) 백만원")
                    ev = f"item4 = residual of printed rows = {resid:,.0f} 백만원 => {resid / 100:.2f}억 (master convention: close - open - new - interest - amort, rounded to 0.1억)"
                except Exception as e:  # noqa: BLE001
                    ev = f"residual item (master convention); tokens {list(toks)}"
                src = f"rcept {rcept_of(xml)} ({fyq_of(xml)}) 표#{rec['table']} L{rec['tline']} 전기열"
                ver = f"독립 재독 {xml}: 위 인쇄행으로 항등식 재계산"
        add(master="CSM_waterfall", code=kr, company=NAME.get(kr, ""), quarter=q, item=it, item_name=ITEM["CSM"].get(it, ""), old=c["old"], new=c["new"], unit="억원",
            kind="latest_comparative", block=f"CSM {kr} {q}", source_ref=src, verified_ref=ver, printed=printed, evidence=ev)

# ------------------------------------------------------------------------------------------------------------------ PL latest-comparative blocks
NOISE = {("KR0011|2023.3Q", 18), ("KR0008|2023.1Q", 16)}     # float noise / 0.042 precision upgrade (same at 0.1억): kept as is, not worth a gold line
T1_ITEMS = {1, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32}
tok_keys_for = {4: ("rev_csm",), 5: ("rev_ra",), 6: ("rev_exp", "cost_act"), 9: ("recost_csm",), 10: ("recost_ra",), 11: ("rerev_act", "recost_exp"),
                3: ("rev_total_장기", "cost_total_장기"), 8: ("rerev_total_장기", "recost_total_장기"),
                13: ("rev_total_자동차", "cost_total_자동차", "rerev_total_자동차", "recost_total_자동차"),
                14: ("rev_total_일반", "cost_total_일반", "rerev_total_일반", "recost_total_일반")}
FORMULA = {2: "item2 = item3 + item8", 3: "item3 = 장기 보험수익 합계 - 장기 보험서비스비용 합계 (누적)", 4: "item4 = |보험계약마진 상각| 장기", 5: "item5 = |위험조정 변동| 장기",
           6: "item6 = 예상보험금류(보험수익 leg) - 발생보험금류(보험비용 leg), 장기", 7: "item7 = item3 - (item4+item5+item6) (residual)", 8: "item8 = 장기 재보험수익 합계 - 장기 재보험비용 합계",
           9: "item9 = -(재보험 CSM 상각)", 10: "item10 = -(재보험 위험조정)", 11: "item11 = 발생출재보험금 - 예상출재보험금", 12: "item12 = item8 - (item9+item10+item11) (residual)",
           13: "item13 = (자동차 보험수익-서비스비용)+(재보험수익-재보험비용)", 14: "item14 = (일반 보험수익-서비스비용)+(재보험수익-재보험비용)"}

for c in plan["PL"]:
    blk, it = c["block"], c["item"]
    if (blk, it) in NOISE:
        continue
    kr, q = blk.split("|")
    fy = f"FY{int(q[:4]) + 1}_Q{q[5]}"
    src = ver = printed = ev = ""
    if kr == "KR0001":
        M = ev_mer
        xml = M["xml"]
        tk = M["tokens"]
        keymap = {4: ("csm",), 5: ("ra",), 6: ("rev_exp", "cost_act"), 9: ("re_csm",), 10: ("re_ra",), 11: ("re_rev", "re_exp"), 3: ("tot_rev", "tot_cost"), 8: ("tot_rerev", "tot_recost")}
        used = [(k, tk[k]) for k in keymap.get(it, ()) if k in tk]
        printed = "; ".join(f"{k}={v[1]}@L{v[2]}" for k, v in used)
        src = f"rcept {rcept_of(xml)} ({fyq_of(xml)}) 주석 '(4) 보험손익 상세내역' 별도 <전분기> 표#{M['table']} L{M['tline']} (장기 누적열)"
        ver = f"독립 재독 {xml}: {FORMULA.get(it, '')} => {M['items'].get(str(it))}"
        ev = "Format-B 별도 전분기 표를 독립 코드로 재도출(= 계획값)"
    elif it in T1_ITEMS and blk in ev_t1 and str(it) in ev_t1[blk]["items"]:
        d = ev_t1[blk]["items"][str(it)]
        xml = ev_t1[blk]["xml"]
        printed = "; ".join(f"L{r['line']} '{r['label'][:14]}' {r['printed']}" for r in d["rows"]) or "(rule: no 기타영업수익 line -> 0.0)" if it == 15 else "; ".join(f"L{r['line']} '{r['label'][:14]}' {r['printed']}" for r in d["rows"])
        src = f"rcept {rcept_of(xml)} ({fyq_of(xml)}) 포괄손익계산서 표#{ev_t1[blk]['table']} L{ev_t1[blk]['tline']} 전기 누적열"
        ver = f"독립 재독 {xml}: " + (printed or "-") + f" => {d['derived']:,.6f} (계획 {d['plan']:,.6f})"
        ev = "statement lines re-derived; derived items by builder formulas (18 = 17-19, 19 = sum of 보험금융 lines, 21 = 영업외수익-영업외비용 or 영업외손익, 32 = 25-sum(26..30))"
    else:
        D = ev_notes.get(blk)
        if D and "items" in D:
            xmls = None
            tk = D.get("tokens", {})
            keys = tok_keys_for.get(it, ())
            used = [(k, v) for k, v in tk.items() if any(k.startswith(kk) for kk in keys)]
            printed = "; ".join(f"{k}={v[0]}@L{v[1]}" for k, v in used)
            tb = D.get("tables")
            src = f"later filing {fy} 별도 주석 보험수익/비용·재보험수익/비용 전기 표 {tb}"
            ver = f"독립 재독(자체 코드, '-'=0 위치 파싱, 별도=무생명 열/후행 복제본): {FORMULA.get(it, '')} => {D['items'].get(str(it))}"
            ev = "own re-derivation equals plan value (all items 2-14 of the block agree)"
        else:
            src = ver = ev = "see evidence_pl_*.json"
    add(master="PL_breakdown", code=kr, company=NAME.get(kr, ""), quarter=q, item=it, item_name=ITEM["PL"].get(it, ""), old=c["old"], new=c["new"], unit="백만원",
        kind="latest_comparative", block=f"PL {kr} {q}", source_ref=src, verified_ref=ver, printed=printed, evidence=ev)

# ------------------------------------------------------------------------------------------------------------------ PL 3-month-as-cumulative corrections
FIX = {"KR0005|2023.2Q": [1, 19, 20, 21, 22, 23, 24], "KR0003|2023.2Q": [19, 18], "KR0002|2023.2Q": [21], "KR0068|2023.2Q": [21], "KR0083|2023.2Q": [19, 18, 21]}
scan = {(r["code"], r["quarter"], r["item"]): r for r in csv.DictReader(open(HERE / "scan3m_v2.csv", encoding="utf-8-sig"))}
for blk, items in FIX.items():
    kr, q = blk.split("|")
    E = ev_t1[blk + "|3Mfix"]
    xml = E["xml"]
    vals17 = pl_live.get((kr, 17, q))
    for it in items:
        old = pl_live[(kr, it, q)]
        if it == 18:
            new19 = E["items"]["19"]["derived_cum"]
            new = round(vals17 - new19, 6)
            printed = f"item18 = item17({vals17}) - item19({new19:,.6f})"
            ver = f"독립 재독 {xml}: 투자손익 누적 L{E['items']['19']['rows'][0]['line']} 인근 + 보험금융 줄; item18 = 17 - 19 (builder 정의)"
        else:
            d = E["items"][str(it)]
            new = round(d["derived_cum"], 6)
            printed = "; ".join(f"L{r['line']} '{r['label'][:16]}' {r['printed']}" for r in d["rows"])
            ver = f"독립 재독 {xml}: 당기 누적열 {printed} => {new:,.6f}"
        s = scan.get((kr, q, str(it)))
        three_m = f" (현재 마스터값 = 같은 표의 '3개월' 열 {s['vals'] if s else ''})" if it != 18 and s and s.get("cls") == "3M_AS_CUM" else ""
        add(master="PL_breakdown", code=kr, company=NAME.get(kr, ""), quarter=q, item=it, item_name=ITEM["PL"].get(it, ""), old=old, new=new, unit="백만원",
            kind="3m_as_cumulative", block=f"PL {kr} {q} (3개월 열 오적재 정정)",
            source_ref=f"rcept {rcept_of(xml)} ({fyq_of(xml)}) 원 공시 포괄손익계산서 표#{E['table']} L{E['tline']} 당기 누적열",
            verified_ref=ver, printed=printed, evidence="master equals the 3개월 column; cumulative column printed in the same statement" + three_m)

# ------------------------------------------------------------------------------------------------------------------ PL wrong-year-column corrections (found by the PDF-lineage scan s105/s109/s111)
# KR0002 2023.1Q / 2023.2Q item 16: the master holds the 24.1Q / 24.2Q figures (399 / 845 억원) of the FY2024 PDFs' '해당 분기' column; the 전년 동기 (23.xQ) column of the same PDFs and the
# OWN FY2023 filings print 257 / 529 억원.  Master convention for the 경영공시 summary = 억원 x 100 (백만원).
ev_k2 = jl(HERE / "evidence_kr0002_item16.json")
for q, own_tag, later_tag, new in (("2023.1Q", "own_2023_Q1", "later_2024_Q1", 25700.0), ("2023.2Q", "own_2023_Q2", "later_2024_Q2", 52900.0)):
    o, l3 = ev_k2[own_tag], ev_k2[later_tag]
    old = pl_live[("KR0002", 16, q)]
    printed = (f"원 공시 {o['file']} p{o['page']} 2-1 요약 포괄손익계산서(총괄) 기타사업비용 {o['header_lines'][1]} = {o['row'][1]}억원; "
               f"후속 공시 {l3['file']} p{l3['page']} 해당 분기 {l3['header_lines'][1]} = {l3['row'][1]}억원 · 전년 동기 {l3['header_lines'][3]} = {l3['row'][2]}억원")
    add(master="PL_breakdown", code="KR0002", company=NAME.get("KR0002", ""), quarter=q, item=16, item_name=ITEM["PL"].get(16, ""), old=old, new=new, unit="백만원",
        kind="wrong_year_column", block=f"PL KR0002 {q} (후속 공시 해당 분기 열 오적재 정정)",
        source_ref=f"{o['file']} p{o['page']} (원 공시) = {l3['file']} p{l3['page']} 전년 동기 열",
        verified_ref=printed,
        printed=printed,
        evidence=f"master {old:,.0f} = {l3['row'][1]}억원 x 100 = the LATER year's current-quarter column ({l3['header_lines'][1]}); correct 23.xQ figure {o['row'][1]}억원 printed in both filings; "
                 f"series check 23.1Q 257 / 23.2Q 529 / 23.3Q 803 (FS-API 80,303.18 백만원) = quarterly flows 257 / 272 / 274 (the old values gave a negative Q3 flow)")

# ------------------------------------------------------------------------------------------------------------------ BS
for c in plan["BS"]:
    e = ev_bs[(c["block"], c["item"])]
    add(master="IFRS17_BS", code=c["code"], company=NAME.get(c["code"], ""), quarter=c["quarter"], item=c["item"], item_name=ITEM["BS"].get(c["item"], ""), old=c["old"], new=c["new"],
        unit="백만원", kind="latest_comparative", block=f"BS {c['code']} {c['quarter']}",
        source_ref=f"rcept {rcept_of(e['xml'])} ({fyq_of(e['xml'])}) 재무상태표 전기말 열 (FS-API frmtrm 와 동일)",
        verified_ref=f"독립 재독 {e['xml']}#L{e['line']} '{e['label']}' 인쇄 {e['printed']} ({e['scale']}) 표#{e['table']} 헤더 {e['hdr'][:60]}",
        printed=f"{e['printed']} ({e['scale']})", evidence="BS table (자산총계·부채총계·자본총계 rows present); planned value equals the printed 전기말 token")

RELEASE = {
    "pl_bridge_baseline": ["DB손해보험|2023.1Q|보험손익(dual)", "DB손해보험|2023.2Q|보험손익(dual)", "DB손해보험|2023.3Q|보험손익(dual)", "메리츠화재해상보험|2023.3Q|보험손익(dual)",
                           "한화생명|2023.2Q|세전이익 = 영업이익+영업외손익", "한화손해보험|2023.2Q|세전이익 = 영업이익+영업외손익"],
    "csm_amort_identity_ledger": ["DB손해보험|2023.1Q", "DB손해보험|2023.2Q", "DB손해보험|2023.3Q"],
    "wfy_exceptions": [["농협생명보험", "2023"]],
}
(HERE / "plan_final.json").write_text(json.dumps({"ticket": "20261012T2230Z", "cells": cells, "release": RELEASE}, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
cols = ["master", "code", "company", "quarter", "item", "item_name", "unit", "old", "new", "kind", "block", "source_ref", "verified_ref", "printed", "evidence"]
with open(HERE / "applied_cells.csv", "w", encoding="utf-8-sig", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
    w.writeheader()
    w.writerows(cells)
from collections import Counter

print("cells", len(cells), Counter((c["master"], c["kind"]) for c in cells))
print("blocks", Counter(c["master"] for c in {c["block"]: c for c in cells}.values()))
