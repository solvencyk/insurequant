# -*- coding: utf-8 -*-
"""Build p3_plan.json (apply contract) for ticket 20261024T0600Z (neighbor stale cells sweep pass 3).  PL only: no CSM cell is touched.
Inputs (all read-only, produced by the reader scripts of this folder, each cell with its physical xml line):
  kr0070_abl/r10_abl_cur_read.json        ABL 2025.3Q-2026.2Q note legs (CURRENT-period column of the quarter's own filing = the latest; no FY2026 Q3 filing exists yet)
  kr0087_dongyang/r11_dy_reins_read.json  동양생명 FY2025_Q2 prior-period (전반기) 재보험수익 / 재보험비용 분석 tables = 2024.2Q cumulative
  kr0032_nhfire/n02_is_read.json          NH농협손해보험 FY2024_Q1 / FY2024_Q2 separate income statement prior cumulative column (2023.1Q / 2023.2Q) incl. OCI vectors
  live PL_breakdown.json + data/_gold/user_pl_cells.json
Nothing here writes the repo: the plan is written next to this script (p3_plan.json)."""
import json
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = "C:/Users/sangwook.cho/Desktop/insurequant"
EV = f"{ROOT}/data/_derived/remaining_20261022/e25_followups/pass3"
EVREL = "data/_derived/remaining_20261022/e25_followups/pass3"
TICKET = "20261024T0600Z"
live = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r for r in json.load(open(f"{ROOT}/PL_breakdown.json", encoding="utf-8"))}
gold = json.load(open(f"{ROOT}/data/_gold/user_pl_cells.json", encoding="utf-8"))
gold_by = {(e["원보험사코드"], e["항목번호"], e["공시분기"]): e for e in gold["set"]}
NAMES = {1: "보험손익", 3: "생명장기 원수손익", 4: "원수 CSM상각", 5: "원수 위험조정 변동", 6: "원수 예실차", 7: "기타 생명장기 원수손익", 8: "생명장기 재보험손익", 9: "재보험 CSM상각", 10: "재보험 위험조정 변동",
         11: "재보험 예실차", 12: "기타 생명장기 재보험손익", 20: "영업이익", 21: "영업외손익", 22: "세전이익", 23: "법인세", 24: "당기순이익", 25: "기타포괄손익", 26: "FVOCI 채무증권 평가손익", 27: "보험계약금융손익(OCI)",
         28: "위험회피 파생상품 평가손익", 29: "FVOCI 지분증권 평가손익", 30: "재보험금융손익(OCI)", 31: "총포괄손익", 32: "기타 포괄손익(미분류)"}


def r6(x):
    return round(float(x), 6)


def lv(code, item, q):
    r = live.get((code, item, q))
    return None if r is None else r.get("값")


def ls(code, item, q):
    r = live.get((code, item, q))
    return None if r is None else r.get("값_당분기")


gold_new, gold_replace, buckets, seams, null_dangi_add, null_dangi_remove, set_dangi_add, not_loaded = [], [], {}, [], [], [], [], []


def add_cell(code, q, item, value, was, note, kind="new", old_entry=None):
    ent = dict(code=code, item=item, quarter=q, value=r6(value), was=(None if was is None else r6(was)), note=note)
    if kind == "replace":
        ent["old_entry"] = old_entry
        gold_replace.append(ent)
    else:
        gold_new.append(ent)
    b = buckets.setdefault((code, q), dict(code=code, quarter=q, kind="pass3_neighbor", cells=[]))
    b["cells"].append(dict(item=item, item_name=NAMES.get(item, str(item)), old=lv(code, item, q), new=r6(value), delta=(None if lv(code, item, q) is None else r6(value - lv(code, item, q)))))


def stale_prefix(code, q, item, old_g, why):
    return (f"2026-10-24 parser/ifrs17 (pass3, ticket {TICKET}): 정적 파생 gold(항목 {item} = 잔차)가 낡아 제자리 교체 — 이전 gold 값 {old_g['값']}, 이전 was {old_g.get('was')}, 이전 note 원문 「{old_g.get('note')}」. {why} ")


def put_derived(code, q, item, value, note_core, why):
    old_g = gold_by.get((code, item, q))
    if old_g is not None:
        add_cell(code, q, item, value, old_g["값"], stale_prefix(code, q, item, old_g, why) + note_core, kind="replace", old_entry=old_g)
    else:
        add_cell(code, q, item, value, lv(code, item, q), note_core)


def seam(code, q, item, derived_after, printed, file, line, text, tol=1.0, extra=None):
    d = r6(derived_after - printed)
    e = dict(code=code, quarter=q, item=item, derived_after=r6(derived_after), printed_3m=dict(value=r6(printed), file=file, line=line, printed=text), diff_vs_printed_3m=d,
             cls="consistent" if abs(d) <= tol + 1e-9 else "mismatch", proposal="none" if abs(d) <= tol + 1e-9 else "null_dangi")
    if extra:
        e.update(extra)
    seams.append(e)
    return e


# ====================================================================================================== 1. ABL KR0070 (items 5 / 10 (+ 9 of 2026.2Q) and derived 7 / 12, 2025.3Q-2026.2Q)
abl = json.load(open(f"{EV}/kr0070_abl/r10_abl_cur_read.json", encoding="utf-8"))
EVJ_ABL = f"{EVREL}/kr0070_abl/r10_abl_cur_read.json"
HEAD_ABL = (f"2026-10-24 parser/ifrs17 (pass3, ticket {TICKET} 항목 1: ABL 2025.3Q-2026.2Q 항목 5·10 은 재보험 위험조정(또는 구성내역 표의 다른 열)을 잘못 집은 값 — FY2026 3Q 공시가 아직 없어 각 분기 자기 공시의 "
            "당기 열이 최신 비교열이다; 박제·잔차 끼움·게이트 예외 없음): 별도(OFS) 기준 life_note 경로, ")
SRC_ABL = {"2025.3Q": "FY2025_Q3 분기보고서 당기 누적 열(4열 표의 2번째)", "2025.4Q": "FY2025_Q4 사업보고서 당기 열", "2026.1Q": "FY2026_Q1 분기보고서 당기 열", "2026.2Q": "FY2026_Q2 반기보고서 당반기 누적 열(4열 표의 2번째)"}
PREV = {"2025.3Q": "2025.2Q", "2026.2Q": "2026.1Q"}
for q in ("2025.3Q", "2025.4Q", "2026.1Q", "2026.2Q"):
    rec = abl[q]
    f = rec["file"]
    cc = rec["cur_cum"]
    rfx = rec["rollforward_cur"]
    m = {int(k): x for k, x in rec["master"].items()}
    base = f"{SRC_ABL[q]} → "
    c5 = cc["rev"]["위험조정변동"]
    c10 = cc["re_cost"]["위험조정변동"]
    v5 = c5["v"]
    v10 = -abs(c10["v"])
    rf5 = f"; 같은 파일의 당기 측정요소 롤포워드 RA 해제 {rfx['ins_ra_release']['text']}@L{rfx['ins_ra_release']['line']} 와 일치" if "ins_ra_release" in rfx else "(당기 롤포워드 표는 이 분기 서식에서 못 찾아 대조 생략; 노트 표 소계=행 합으로 검산)"
    rf10 = f"; 롤포워드 재보험 RA 해제 {rfx['rein_ra_release']['text']}@L{rfx['rein_ra_release']['line']} 와 일치" if "rein_ra_release" in rfx else ""
    add_cell("KR0070", q, 5, v5, lv("KR0070", 5, q),
             HEAD_ABL + base + f"{v5:.0f} 백만원. 원문 {f} L{c5['line']} (보험수익 구간 위험조정변동 {c5['text']}{rf5}). 변경 전 마스터값 {lv('KR0070', 5, q)}. 변동 {r6(v5 - lv('KR0070', 5, q))}. "
             f"산식: 보험수익 구간 위험조정변동 [당기 누적]. 검산: 보험수익 구간 행 합 = 소계 {rec['subtotal_check_cur_cum']['보험수익'][1]:.0f}. 증거 {EVJ_ABL}")
    add_cell("KR0070", q, 10, v10, lv("KR0070", 10, q),
             HEAD_ABL + base + f"{v10:.0f} 백만원. 원문 {f} L{c10['line']} (재보험비용 구간 위험조정변동 {c10['text']}{rf10}). 변경 전 마스터값 {lv('KR0070', 10, q)}. 변동 {r6(v10 - lv('KR0070', 10, q))}. "
             f"산식: -|재보험비용 구간 위험조정변동| [당기 누적]. 검산: 재보험비용 구간 행 합 = 소계 {rec['subtotal_check_cur_cum']['재보험비용'][1]:.0f}. 증거 {EVJ_ABL}")
    v9 = m[9]
    if q == "2026.2Q":
        c9 = cc["re_cost"]["보험계약마진상각"]
        v9 = -abs(c9["v"])
        c3m9 = rec["cur_3m"]["re_cost"]["보험계약마진상각"]
        add_cell("KR0070", q, 9, v9, lv("KR0070", 9, q),
                 HEAD_ABL + base + f"{v9:.0f} 백만원 (블록 닫기용 한 단위 정정). 원문 {f} L{c9['line']} (재보험비용 구간 보험계약마진상각 {c9['text']}); 같은 파일의 CSM 롤포워드는 (6,876) 으로 한 단위 다르게 인쇄된다(L15622 등) — "
                 f"손익 노트(항목 9 의 원천 표)가 최신 인쇄 기준이고 이 표의 3개월 열 {c3m9['text']}@L{c3m9['line']} + 1분기 -3,072 = {-abs(c3m9['v']) - 3072:.0f} 로 닫힌다. 변경 전 마스터값 {lv('KR0070', 9, q)}. "
                 f"이 칸을 안 옮기면 파생 12 의 단일분기가 인쇄 3개월 열에서 2.0 벗어난다(항목 9 단일분기 -3,804 대 인쇄 -3,803). 증거 {EVJ_ABL}")
    # derived 7 = 3 - (4 + 5 + 6) and 12 = 8 - (9 + 10 + 11), master operands + the new 5 / 9 / 10
    i7 = m[3] - (m[4] + v5 + m[6])
    i12 = m[8] - (v9 + v10 + m[11])
    cl7, cl12 = rec["closure7"], rec["closure12"]
    core7 = (HEAD_ABL + base + f"항목들로 유도 → {r6(i7)} 백만원. 산식: 3 - (4+5+6). 피연산자: 3번={m[3]}(마스터), 4번={m[4]}(마스터), 5번={v5:.0f}(위 줄), 6번={m[6]}(마스터; 노트의 예상4종-발생4종 {rec['items']['6']:.0f} 와 같음). "
             f"같은 표의 나머지 행(보험취득현금흐름상각·손실요소배분액·기타보험수익 - 손실부담계약관련비용·발생사고요소조정·보험취득현금흐름상각·손실요소배분액·기타보험서비스비용)의 합 {cl7['value']:.0f} 과 {r6(i7 - cl7['value']):+} 차이(반올림). "
             f"변경 전 마스터값 {lv('KR0070', 7, q)}. 증거 {EVJ_ABL}")
    put_derived("KR0070", q, 7, i7, core7, f"항목 5 가 {lv('KR0070', 5, q)} → {v5:.0f} 로 최신 인쇄값으로 바뀌어 잔차가 달라진다.")
    core12 = (HEAD_ABL + base + f"항목들로 유도 → {r6(i12)} 백만원. 산식: 8 - (9+10+11). 피연산자: 8번={m[8]}(마스터), 9번={v9:.0f}({'위 줄' if q == '2026.2Q' else '마스터'}), 10번={v10:.0f}(위 줄), 11번={m[11]}(마스터; 노트 {rec['items']['11']:.0f} 와 같음). "
              f"같은 표의 나머지 재보험 행(손실회수요소관련수익·발생사고요소조정·손실회수요소배분액·기타재보험수익 - 손실회수요소배분액·기타재보험비용)의 합 {cl12['value']:.0f} 과 {r6(i12 - cl12['value']):+} 차이(반올림). "
              f"변경 전 마스터값 {lv('KR0070', 12, q)}. 증거 {EVJ_ABL}")
    put_derived("KR0070", q, 12, i12, core12, "재보험 항목 " + ("9·10" if q == "2026.2Q" else "10") + " 이 최신 인쇄값으로 바뀌어 잔차가 달라진다.")
    rec["_plan"] = dict(v5=v5, v10=v10, v9=v9, i7=i7, i12=i12)

# seams (single quarter = new cumulative - previous cumulative vs the printed 3-month column of the same filing; 2025.3Q and 2026.2Q filings print it)
for q in ("2025.3Q", "2026.2Q"):
    rec, pq = abl[q], PREV[q]
    f = rec["file"]
    v3 = rec["cur_3m"]
    p = rec["_plan"]

    def prevv(it):
        # the previous quarter's cumulative AFTER this load (2025.2Q / 2026.1Q: 2026.1Q items 5/10/7/12 are loaded above, 2025.2Q items are the pass-2 gold)
        if pq == "2026.1Q":
            pl = abl["2026.1Q"]["_plan"]
            return {5: pl["v5"], 10: pl["v10"], 9: lv("KR0070", 9, pq), 7: pl["i7"], 12: pl["i12"]}.get(it, lv("KR0070", it, pq))
        return lv("KR0070", it, pq)
    sg = {4: v3["rev"]["보험계약마진상각"], 5: v3["rev"]["위험조정변동"], 9: v3["re_cost"]["보험계약마진상각"], 10: v3["re_cost"]["위험조정변동"]}
    printed = {4: sg[4]["v"], 5: sg[5]["v"], 9: -sg[9]["v"], 10: -sg[10]["v"]}
    cur = {4: lv("KR0070", 4, q), 5: p["v5"], 9: p["v9"], 10: p["v10"]}
    for it in (4, 5, 9, 10):
        c = sg[it]
        seam("KR0070", q, it, cur[it] - prevv(it), printed[it], f, c["line"], c["text"])
    # item 6 / 11 (unchanged, shown for the 3M block)
    exp3 = sum(x["v"] for x in (v3["rev"].get(k) for k in ("예상보험금", "예상손해조사비", "예상계약유지비", "예상투자관리비")) if x)
    inc3 = sum(x["v"] for x in (v3["cost"].get(k) for k in ("발생보험금", "발생손해조사비", "발생계약유지비", "발생투자관리비")) if x)
    seam("KR0070", q, 6, lv("KR0070", 6, q) - lv("KR0070", 6, pq), exp3 - inc3, f, v3["rev"]["예상보험금"]["line"], f"예상4종 {exp3:.0f} - 발생4종 {inc3:.0f}")
    ract3 = sum(x["v"] for x in (v3["re_rev"].get(k) for k in ("발생재보험금", "발생손해조사비")) if x)
    rexp3 = sum(x["v"] for x in (v3["re_cost"].get(k) for k in ("예상재보험금", "예상손해조사비")) if x)
    seam("KR0070", q, 11, lv("KR0070", 11, q) - lv("KR0070", 11, pq), ract3 - rexp3, f, v3["re_rev"]["발생재보험금"]["line"], f"발생재보험금 {ract3:.0f} - 예상재보험금 {rexp3:.0f}")
    # derived 7 / 12: single (cumulative difference) vs the value implied by the printed 3-month cells AND vs the 3-month other-rows sum
    m3s = lv("KR0070", 3, q) - lv("KR0070", 3, pq)
    m8s = lv("KR0070", 8, q) - lv("KR0070", 8, pq)
    p7 = m3s - (printed[4] + printed[5] + (exp3 - inc3))
    p12 = m8s - (printed[9] + printed[10] + (ract3 - rexp3))
    seam("KR0070", q, 7, p["i7"] - prevv(7), p7, f, None, f"3 단일분기 {r6(m3s)} - (4 {printed[4]:.0f} + 5 {printed[5]:.0f} + 6 {exp3 - inc3:.0f}) 인쇄 3개월; 3개월 나머지 행 합 {rec['other7_3m']:.0f}",
         extra=dict(vs_other_rows_3m=r6(p["i7"] - prevv(7) - rec["other7_3m"])))
    seam("KR0070", q, 12, p["i12"] - prevv(12), p12, f, None, f"8 단일분기 {r6(m8s)} - (9 {printed[9]:.0f} + 10 {printed[10]:.0f} + 11 {ract3 - rexp3:.0f}) 인쇄 3개월; 3개월 나머지 행 합 {rec['other12_3m']:.0f}",
         extra=dict(vs_other_rows_3m=r6(p["i12"] - prevv(12) - rec["other12_3m"])))
# the 2025.3Q item 5 single now equals the printed 3M column -> release its null_dangi; item 7 does not (2.0 off, inherited from the item 6 single) -> keeps its null_dangi
s5 = [s for s in seams if (s["quarter"], s["item"]) == ("2025.3Q", 5)][0]
s7 = [s for s in seams if (s["quarter"], s["item"]) == ("2025.3Q", 7)][0]
assert s5["cls"] == "consistent" and s7["cls"] == "mismatch", (s5, s7)
null_dangi_remove.append(["KR0070", "2025.3Q", 5])
for s in seams:
    if s["code"] == "KR0070" and s["cls"] == "mismatch" and (s["quarter"], s["item"]) not in (("2025.3Q", 7), ("2025.3Q", 6)):
        raise SystemExit(f"unexpected ABL seam mismatch {s}")
    if s["code"] == "KR0070" and (s["quarter"], s["item"]) == ("2025.3Q", 6):
        s["proposal"] = "none (item 6 is not loaded in this ticket; the 2.0 difference is the inherited rounding noise of the eight-row item 6 between the FY2026_Q2 comparative and the FY2025_Q3 report)"

# ====================================================================================================== 2. 동양생명 KR0087 2024.2Q reinsurance items 9 / 10 / 11 / 12
dy = json.load(open(f"{EV}/kr0087_dongyang/r11_dy_reins_read.json", encoding="utf-8"))
EVJ_DY = f"{EVREL}/kr0087_dongyang/r11_dy_reins_read.json"
v = dy["q2024_2Q"]
d = dy["prior"]
f = dy["file"]
HEAD_DY = (f"2026-10-24 parser/ifrs17 (pass3, ticket {TICKET} 항목 2: 동양생명 2024.2Q 재보험 항목 9·10·11·12 — 원 공시(FY2024_Q2)의 재보험 표는 합계(재보험수익·재보험비용·재보험계약의 보험서비스결과)만 인쇄해 "
           "9·10·12 가 공란이었고 항목 11(523)에는 3개월 열의 재보험계약 보험서비스결과 합계가 들어 있었다; FY2025 반기보고서의 전반기 재보험수익·재보험비용 분석 표(최신 비교열)는 구성 행을 인쇄한다; 박제·잔차 끼움·게이트 예외 없음): "
           "별도(OFS) 기준, FY2025_Q2 전반기 누적 열 → ")
SIGN_DY = ("부호는 생산 정의(extract_tier2_dongyang · docs/domains/csm-pl-basis-methodology.md '출재 CSM, 음수') -|값| 를 쓴다; 인쇄 부호(재보험비용 표의 구성 행은 기여 부호)로는 CSM 이 +2,528(이익), RA 가 (824) 라 "
           f"9 = +2,528 / 10 = -824 / 12 = {r6(v['i12_printed_sign_convention'])} 이 되고 8 = 9+10+11+12 합은 같다 (owner 손입력 2024.4Q·2025.1Q gold 는 인쇄 부호를 썼다).")
note9 = (HEAD_DY + f"{v['i9']:,.0f} 백만원. 원문 {f} L{d['csm']['cum']['line']} (재보험비용, 서비스의 이전으로 당기손익에 인식한 보험계약마진 누적 {d['csm']['cum']['text']}; 3개월 {d['csm']['m3']['text']}@L{d['csm']['m3']['line']}). "
         f"변경 전 마스터값 {lv('KR0087', 9, '2024.2Q')}(공란). 산식: -|CSM|. {SIGN_DY} 증거 {EVJ_DY}")
note10 = (HEAD_DY + f"{v['i10']:,.0f} 백만원. 원문 {f} L{d['ra']['cum']['line']} (재보험비용, 비금융위험에 대한 위험조정의 변동분 누적 {d['ra']['cum']['text']}; 3개월 {d['ra']['m3']['text']}@L{d['ra']['m3']['line']}). "
          f"변경 전 마스터값 {lv('KR0087', 10, '2024.2Q')}(공란). 산식: -|RA|. 인쇄 부호와 같다. 증거 {EVJ_DY}")
note11 = (HEAD_DY + f"{v['i11']:,.0f} 백만원. 원문 {f} 재보험수익, 발생한 보험금 누적 {d['act']['cum']['text']} L{d['act']['cum']['line']} (+ 발생한 손해조사비 {d['act_survey']['cum']['text']} L{d['act_survey']['cum']['line']}) "
          f"- 재보험비용, 예상 보험금(기초 예상 측정치) 누적 {d['exp']['cum']['text']} L{d['exp']['cum']['line']} (+ 예상 기타 보험서비스비용 {d['exp_other']['cum']['text']} L{d['exp_other']['cum']['line']}). 변경 전 마스터값 {lv('KR0087', 11, '2024.2Q')} "
          f"(= 3개월 열 재보험계약의 보험서비스결과 523, FY2024_Q2 L44621). 산식: |실제 재보험금| - |예상 재보험금|, 2025.2Q 마스터 7,026 = 18,774 - 11,748 과 같은 정의(같은 보고서의 당반기 표로 대조: 9/10/11 이 마스터 2025.2Q 와 일치). 증거 {EVJ_DY}")
core12 = (HEAD_DY + f"항목들로 유도 → {r6(v['i12'])} 백만원. 산식: 8 - (9+10+11). 피연산자: 8번={v['i8']}(마스터), 9번={v['i9']:.0f}, 10번={v['i10']:.0f}, 11번={v['i11']:.0f}(위 줄). "
          f"검산: 재보험수익 구성 행 합 {-dy['prior_closure']['rev_components_sum']:,.0f} = 인쇄 합계 {dy['prior_closure']['rev_total']:,.0f}, 재보험비용 구성 행 합 {-dy['prior_closure']['cost_components_sum']:,.0f} = 인쇄 합계 {dy['prior_closure']['cost_total']:,.0f}; "
          f"노트 표 결과 {dy['prior_closure']['note_result']:,.0f} 대 마스터 8번 {v['i8']:.3f} 은 {v['i8'] - dy['prior_closure']['note_result']:+.3f}(원 공시 FY2024_Q2 는 재보험비용 26,158 로 인쇄해 노트 결과 4,327), "
          f"나머지 행(미래·과거 서비스 -> 기여 부호 {v['other_rows_printed_sign']:,.0f}) 대 인쇄부호 기준 12번 {v['i12_printed_sign_convention']:.3f} 은 {v['diff_i12_vs_other_rows_printed_sign']:+.3f}(구성 7개 행의 반올림). {SIGN_DY} "
          f"변경 전 마스터값 {lv('KR0087', 12, '2024.2Q')}(공란). 증거 {EVJ_DY}")
add_cell("KR0087", "2024.2Q", 9, v["i9"], lv("KR0087", 9, "2024.2Q"), note9)
add_cell("KR0087", "2024.2Q", 10, v["i10"], lv("KR0087", 10, "2024.2Q"), note10)
add_cell("KR0087", "2024.2Q", 11, v["i11"], lv("KR0087", 11, "2024.2Q"), note11)
add_cell("KR0087", "2024.2Q", 12, v["i12"], lv("KR0087", 12, "2024.2Q"), core12)
# single quarters: 2024.1Q item 11 (3,805) is the Q1 reinsurance service RESULT (= item 8), not the 예실차, so 2Q - 1Q would be garbage (10,468); 2024.3Q item 11 (-479) is the 3-month result total -> (3Q - 2Q) garbage
null_dangi_add.append(["KR0087", "2024.2Q", 11])
null_dangi_add.append(["KR0087", "2024.3Q", 11])
# printed 3-month column of the 2Q tables vs nothing (Q1 has no detail) -> shown for the record
for it, key in ((9, "csm"), (10, "ra")):
    c = d[key]["m3"]
    seams.append(dict(code="KR0087", quarter="2024.2Q", item=it, derived_after=None, printed_3m=dict(value=r6(-abs(c["v"])), file=f, line=c["line"], printed=c["text"]), diff_vs_printed_3m=None, cls="no_q1_detail",
                      proposal="single quarter stays blank: 2024.1Q items 9/10/12 are blank (the original FY2025_Q1 filing prints no reinsurance detail), the cumulative is not split"))

# ====================================================================================================== 3. NH농협손해보험 KR0032 2023.1Q + 2023.2Q
nh = json.load(open(f"{EV}/kr0032_nhfire/n02_is_read.json", encoding="utf-8"))
EVJ_NH = f"{EVREL}/kr0032_nhfire/n02_is_read.json"
HEAD_NH = (f"2026-10-24 parser/ifrs17 (pass3, ticket {TICKET} 항목 3: NH농협손해보험 2023.1Q·2Q 손익 말단(영업이익·영업외손익·세전이익·법인세·당기순이익)을 후속 공시(FY2024 1분기·반기) 별도 손익계산서의 전기 누적 열 원 단위 인쇄값으로 "
           "맞춘다 — 마스터는 정수 백만원/억원으로 반올림된 옛 값이었고(2Q 법인세 38,600 대 인쇄 38,631.288, 순이익 141,300 대 141,267.568), 2Q 기타포괄손익 25~32 는 공란이었다; 박제·잔차 끼움·게이트 예외 없음): 별도(OFS) 기준, ")
FYN = {"2023.1Q": "FY2024_Q1 분기보고서", "2023.2Q": "FY2024_Q2 반기보고서"}
LABN = {20: ("i20", "III.영업이익", "영업이익"), 22: ("i22", "VI.법인세차감전순이익", "법인세차감전순이익"), 23: ("i23", "VII.법인세비용", "법인세비용"), 24: ("i24", "VIII.순이익", "순이익")}
CHAIN = "검산(원 단위 정확): 22 - 23 - 24 = {a:,.0f}, 20 + 영업외수익 - 영업외비용 - 22 = {b:,.0f}, 24 + 기타포괄손익 - 총포괄손익 = {c:,.0f}; 단일분기(2Q-1Q)는 FY2024_Q2 인쇄 3개월 열과 소수 6자리까지 일치."
for q in ("2023.1Q", "2023.2Q"):
    rec = nh[q]
    f = rec["file"]
    vals = rec["vals_mn"]
    items = (20, 21, 22, 23, 24) if q == "2023.1Q" else (22, 23, 24)
    for it in items:
        if it == 21:
            a, b = rec["i21a"], rec["i21b"]
            cite = f"IV.영업외수익 {a['text']}@L{a['line']} - V.영업외비용 {b['text']}@L{b['line']}"
            frm = "영업외수익 - 영업외비용 [전기 누적]"
        else:
            key, lab, _nm = LABN[it]
            cite = f"{lab} {rec[key]['text']}@L{rec[key]['line']}"
            frm = f"{lab} [전기 누적 열]"
        add_cell("KR0032", q, it, vals[str(it)], lv("KR0032", it, q),
                 HEAD_NH + f"{FYN[q]} 전기 누적 열 → {vals[str(it)]:.6f} 백만원. 원문 {f} {cite} 원. 변경 전 마스터값 {lv('KR0032', it, q)}. 산식: {frm}. "
                 + CHAIN.format(a=rec["chk_22_23_24_won"], b=rec["chk_20_21_22_won"], c=rec["chk_24_25_31_won"]) + f" 증거 {EVJ_NH}")
HEAD_OCI = (f"2026-10-24 parser/ifrs17 (pass3, ticket {TICKET} 항목 3: 마스터가 공란이던 2023.2Q OCI 항목 25~32 를 후속 공시(FY2024 반기) 별도 포괄손익계산서의 전기 누적 열 인쇄값으로 채운다 — 같은 분기 항목 24 의 정밀도 차이를 "
            "위 22·23·24 로 정리해 31 = 24+25 가 닫힌다; 박제·잔차 끼움·게이트 예외 없음): 별도(OFS) 기준, ")
o = nh["oci"]["2023.2Q"]
rec = nh["2023.2Q"]
for it in (25, 26, 27, 28, 29, 30, 31, 32):
    if it == 25:
        cite = f"기타포괄손익 {o['i25']['text']} L{o['i25']['line']}"
        frm = "기타포괄손익 [전기 누적 열]"
    elif it == 31:
        cite = f"총포괄손익 {o['i31']['text']} L{o['i31']['line']}"
        frm = "총포괄손익 [전기 누적 열]"
    else:
        leafs = o["leafs"][str(it)]
        cite = " + ".join(f"{x['label']} {x['cell']['text']} L{x['cell']['line']}" for x in leafs)
        frm = "e21 분류 규칙(classify_leaf)으로 모은 OCI 말단 행의 합 [전기 누적 열]" + (" — 26~30 슬롯에 안 잡히는 말단 행 전부(확정급여제도의 재측정요소 등)" if it == 32 else "")
    add_cell("KR0032", "2023.2Q", it, o["vals_mn"][str(it)], lv("KR0032", it, "2023.2Q"),
             HEAD_OCI + f"NH농협손해보험 2023.2Q ← FY2024_Q2 별도 포괄손익계산서(원) 전기 누적 열 → {o['vals_mn'][str(it)]:.6f} 백만원. 원문 {o['file']} {cite}. 변경 전 마스터값 {lv('KR0032', it, '2023.2Q')}(공란). 산식: {frm}. "
             f"검산: 25 = 26+27+28+29+30+32 (잔차 {o['residual_check']:.6f}), 31 = 24+25 (인쇄 {rec['i24']['text']} + {rec['i25']['text']} 원, 잔차 {o['ni_oci_total_check_won']:,.0f} 원); 단일분기(2Q-1Q)는 인쇄 3개월 열과 일치. 증거 {EVJ_NH}")
# seams (single quarter 2Q - 1Q vs the printed prior 3M column, and the new 3Q single vs the FY2024_Q3 printed 3M column)
sm = nh["seam_2Q_minus_1Q"]
for it_s in ("20", "21", "22", "23", "24"):
    if it_s in ("20", "21"):
        continue                       # items 20 / 21 of 2023.2Q stay blank (outside the ticket)
    x = sm[it_s]
    c = nh["2023.2Q"][{"22": "i22", "23": "i23", "24": "i24"}[it_s] + "_3m"]
    seam("KR0032", "2023.2Q", int(it_s), nh["2023.2Q"]["vals_mn"][it_s] - nh["2023.1Q"]["vals_mn"][it_s], x["printed_3m"], nh["2023.2Q"]["file"], c["line"], c["text"], tol=0.001)
o1 = nh["oci"]["2023.1Q"]
for it in (25, 26, 27, 28, 29, 30, 31, 32):
    printed = o["vals_3m_mn"][str(it)]
    seam("KR0032", "2023.2Q", it, o["vals_mn"][str(it)] - o1["vals_mn"][str(it)], printed, o["file"], None, "prior 3-month column of the OCI statement", tol=0.001)
# 2023.3Q single quarter = live 3Q cumulative (FY2024_Q3 prior cumulative == live master, proven in n02) - the new 2Q cumulative; the live 3Q singles of 22 / 23 / 24 are blank (hand-blanked while the 2Q cumulative was the
# 억원-rounded legacy value) and become the derivation, which equals the FY2024_Q3 printed prior 3-month column to the won
n3, o3 = nh["2023.3Q"], nh["oci"]["2023.3Q"]
for it_s in ("22", "23", "24"):
    x = nh["seam_3Q_minus_2Q"][it_s]
    assert abs(x["prior_cum_minus_master"]) < 1e-6, x
    c = n3[{"22": "i22", "23": "i23", "24": "i24"}[it_s] + "_3m"]
    seam("KR0032", "2023.3Q", int(it_s), x["derived"], x["printed_3m"], n3["file"], c["line"], c["text"], tol=0.001)
for it in (25, 26, 27, 28, 29, 30, 31, 32):
    assert abs(o3["vals_mn"][str(it)] - lv("KR0032", it, "2023.3Q")) < 1e-6, (it, o3["vals_mn"][str(it)], lv("KR0032", it, "2023.3Q"))
    seam("KR0032", "2023.3Q", it, lv("KR0032", it, "2023.3Q") - o["vals_mn"][str(it)], o3["vals_3m_mn"][str(it)], o3["file"], None, "prior 3-month column of the OCI statement (FY2024_Q3)", tol=0.001)

# ====================================================================================================== not loaded (per-cell reasons, for the ticket answer)
not_loaded += [
    dict(code="KR0070", cells="2025.3Q item 7 single quarter (null_dangi kept)", reason="the new cumulative difference -5,374.023 differs from the value implied by the printed 3-month column (3 single 15,417.977 - (21,127 + 2,666 - 3,003) = -5,372.023) by exactly 2.0, "
            "which is the item 6 single (-3,001 = -12,199 - (-9,198)) against its printed 3-month -3,003: the H1 comparative (FY2026_Q2 prior column) and the 9M column of the FY2025_Q3 report differ by 2 on the eight-row item 6. "
            "Item 6 is outside the ticket; blank beats wrong, so the 2025.3Q item 7 single stays null. Items 5 / 10 / 12 singles of 2025.3Q match the printed 3M (2,666 / -240 / 916.776 vs 917 other-rows)."),
    dict(code="KR0087", cells="2024.3Q items 9 / 10 / 11 / 12 (cumulative)", reason="the FY2025_Q3 prior-period (전분기) 재보험수익 / 재보험비용 분석 tables print TOTALS ONLY (9,151 / 32,314 and 7,457 / 37,942 style rows, no 발생한 보험금 / 예상 보험금 / 위험조정 / 보험계약마진 rows) and the original FY2024_Q3 report "
            "prints only 재보험수익 / 재보험비용 / 재보험계약의 보험서비스결과 totals, so no 2024.3Q detail can be read. Item 11 (-479 = the 3-month 재보험계약의 보험서비스결과 (479), FY2025_Q3 L64091) stays as it is and only its single quarter is blanked; "
            "blanking the cumulative needs a go"),
    dict(code="KR0087", cells="2024.1Q item 11 (3,805) and 2024.4Q item 11 (5,758)", reason="same defect as 2024.2Q/3Q (the printed 재보험계약의 보험서비스결과 total = item 8, not the 예실차); outside the ticket (2024.1Q: FY2025_Q1 prints no reinsurance detail; 2024.4Q: items 9/10/12 are owner xlsx-fill gold built around 5,758), reported"),
    dict(code="KR0087", cells="2025.1Q items 9 / 10 (owner gold)", reason="untouched by the ticket's rule"),
    dict(code="KR0032", cells="2023.2Q items 1 / 17 / 18 / 19 / 20 / 21 (blank)", reason="outside the ticket (OCI + item 24 precision); readable from the same FY2024_Q2 statement (20 = 191,809.856780, 21 = -11,911.001073, 17 = II.투자손익 78,508.134986, 1 = I.보험손익 113,301.721794)"),
    dict(code="KR0032", cells="2023.2Q item 16 (41,900 + null_dangi)", reason="outside the ticket; the latest comparative is 기타사업비용 40,748.545805 (FY2024_Q2 L6654) and 2Q - 1Q (20,951.967361) = 19,796.578444 equals the printed 3M, so the e20 (c) blank could be released after adopting it"),
    dict(code="KR0032", cells="2023.1Q item 19 (-56,596.0)", reason="outside the ticket; the latest comparative implies -56,595.452489 (= 17 - 18 of the e20 gold cells), identity 17 = 18 + 19 has been open by 0.548 since e20"),
    dict(code="KR0070", cells="2026.2Q item 9 neighbours: 2025.3Q-2026.1Q item 9 / 4 / 6 / 11", reason="equal to the printed cumulative (checked in r10_abl_cur_read.txt)"),
    dict(code="KDB KR0072", cells="all", reason="held by owner decision (2026-10-23), untouched"),
]

plan = dict(
    generated="2026-10-24", ticket=TICKET, scenario="PASS3_NEIGHBOR_STALE_CELLS",
    buckets=sorted(buckets.values(), key=lambda b: (b["code"], b["quarter"])), csm_buckets=[], seams=seams, not_loaded=not_loaded,
    apply_contract=dict(gold_new=gold_new, gold_replace=gold_replace, csm_gold_new=[], csm_gold_replace=[], csm_gold_remove=[], null_dangi_add=null_dangi_add, null_dangi_remove=null_dangi_remove,
                        set_dangi_add=set_dangi_add, set_dangi_remove=[], held=[], drift_fix=[]),
)
json.dump(plan, open(f"{EV}/p3_plan.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("gold_new", len(gold_new), "gold_replace", len(gold_replace), "null_dangi_add", len(null_dangi_add), "null_dangi_remove", len(null_dangi_remove), "set_dangi_add", len(set_dangi_add), "buckets", len(plan["buckets"]), "seams", len(seams))
for e in gold_new + gold_replace:
    print(f"  {e['code']} {e['quarter']} item {e['item']:>2}: {e['was']} -> {e['value']}" + ("  [REPLACE]" if "old_entry" in e else ""))
for s in seams:
    print(f"  seam {s['code']} {s['quarter']} item {s['item']:>2}: derived {s['derived_after']} vs printed 3M {s['printed_3m']['value']} diff {s['diff_vs_printed_3m']} -> {s['cls']}" + (f" (vs other rows 3M {s['vs_other_rows_3m']})" if "vs_other_rows_3m" in s else ""))
