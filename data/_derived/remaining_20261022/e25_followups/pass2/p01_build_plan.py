# -*- coding: utf-8 -*-
"""Build p2_plan.json (apply contract) for ticket 20261024T0300Z (neighbor stale cells sweep pass 2).  PL only: no CSM cell is touched (KB라이프 CSM chain = verdict only).
Inputs (all read-only, produced by the reader scripts of this folder, each cell with its physical xml line):
  kr0070_abl/r03_abl_read.json       ABL 2023.1Q-2025.2Q note legs (prior-period cumulative column of the next fiscal year's same-quarter filing)
  kr0087_dongyang/r01_dy_read.json   동양 2024.2Q / 2024.3Q prior-period 보험수익 / 보험서비스비용 analysis tables
  kr0009_hyundai/r01_hd_read.json    현대해상 2023.1Q-2023.4Q 장기 column of the LOB note (천원)
  kr0068_hanwha/r02_hw_read.json     한화생명 2023.1Q-2023.4Q LOB note 합계 column
  oci_read.json                      NH농협손보 KR0032 2023.1Q + DB생명 KR0082 2023.1Q/2Q separate comprehensive income statement (원)
  live PL_breakdown.json + data/_gold/user_pl_cells.json
Nothing here writes the repo: the plan is written next to this script (p2_plan.json)."""
import json
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = "C:/Users/sangwook.cho/Desktop/insurequant"
EV = f"{ROOT}/data/_derived/remaining_20261022/e25_followups/pass2"
EVREL = "data/_derived/remaining_20261022/e25_followups/pass2"
TICKET = "20261024T0300Z"
live = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r for r in json.load(open(f"{ROOT}/PL_breakdown.json", encoding="utf-8"))}
gold = json.load(open(f"{ROOT}/data/_gold/user_pl_cells.json", encoding="utf-8"))
gold_by = {(e["원보험사코드"], e["항목번호"], e["공시분기"]): e for e in gold["set"]}
NAMES = {1: "보험손익", 3: "생명장기 원수손익", 4: "원수 CSM상각", 5: "원수 위험조정 변동", 6: "원수 예실차", 7: "기타 생명장기 원수손익", 8: "생명장기 재보험손익", 9: "재보험 CSM상각", 10: "재보험 위험조정 변동",
         11: "재보험 예실차", 12: "기타 생명장기 재보험손익", 25: "기타포괄손익", 26: "FVOCI 채무증권 평가손익", 27: "보험계약금융손익(OCI)", 28: "위험회피 파생상품 평가손익", 29: "FVOCI 지분증권 평가손익",
         30: "재보험금융손익(OCI)", 31: "총포괄손익", 32: "기타 포괄손익(미분류)"}


def r6(x):
    return round(float(x), 6)


def lv(code, item, q):
    r = live.get((code, item, q))
    return None if r is None else r.get("값")


gold_new, gold_replace, buckets, seams, null_dangi_add, set_dangi_add, not_loaded = [], [], {}, [], [], [], []


def add_cell(code, q, item, value, was, note, kind="new", old_entry=None):
    ent = dict(code=code, item=item, quarter=q, value=r6(value), was=(None if was is None else r6(was)), note=note)
    if kind == "replace":
        ent["old_entry"] = old_entry
        gold_replace.append(ent)
    else:
        gold_new.append(ent)
    b = buckets.setdefault((code, q), dict(code=code, quarter=q, kind="pass2_neighbor", cells=[]))
    b["cells"].append(dict(item=item, item_name=NAMES.get(item, str(item)), old=lv(code, item, q), new=r6(value), delta=(None if lv(code, item, q) is None else r6(value - lv(code, item, q)))))


def stale_prefix(code, q, item, old_g, why):
    return (f"2026-10-24 parser/ifrs17 (pass2, ticket {TICKET}): 정적 파생 gold(항목 {item} = 잔차)가 낡아 제자리 교체 — 이전 gold 값 {old_g['값']}, 이전 was {old_g.get('was')}, 이전 note 원문 「{old_g.get('note')}」. {why} ")


def put_derived(code, q, item, value, note_core, why):
    """gold entry for a derived item (7 / 12): replaced in place when a static gold already exists, else new"""
    old_g = gold_by.get((code, item, q))
    if old_g is not None:
        add_cell(code, q, item, value, old_g["값"], stale_prefix(code, q, item, old_g, why) + note_core, kind="replace", old_entry=old_g)
    else:
        add_cell(code, q, item, value, lv(code, item, q), note_core)


# ====================================================================================================== 1. ABL KR0070 (items 5 / 9 / 10 / 11 + derived 7 / 12)
abl = json.load(open(f"{EV}/kr0070_abl/r03_abl_read.json", encoding="utf-8"))
HEAD_ABL = (f"2026-10-24 parser/ifrs17 (pass2, ticket {TICKET} 항목 1: ABL 노트 항목을 최신 비교열로 — 2024.1Q-2025.2Q 항목 5 는 재보험 위험조정(또는 구성내역 표의 다른 열)을 잘못 집은 값, 항목 9·10 공란, 2023 항목 11·12 미적재; "
            "박제·잔차 끼움·게이트 예외 없음): 별도(OFS) 기준 life_note 경로, ")
SRC_ABL = {"2023.1Q": "FY2024_Q1 의 전기 2023.1Q 누적(3월) 열", "2023.2Q": "FY2024_Q2 의 전반기 누적 열", "2023.3Q": "FY2024_Q3 의 전분기 누적 열", "2023.4Q": "FY2024_Q4 의 전기 열",
           "2024.1Q": "FY2025_Q1 의 전분기(2024.1Q) 열", "2024.2Q": "FY2025_Q2 의 전반기 누적 열", "2024.3Q": "FY2025_Q3 의 전분기 누적 열", "2024.4Q": "FY2025_Q4 의 전기(2024) 열",
           "2025.1Q": "FY2026_Q1 의 전분기(2025.1Q) 열", "2025.2Q": "FY2026_Q2 의 전반기 누적 열"}
EVJ = f"{EVREL}/kr0070_abl/r03_abl_read.json"
for q in ("2024.1Q", "2024.2Q", "2024.3Q", "2024.4Q", "2025.1Q", "2025.2Q"):
    rec = abl[q]
    f = rec["file"]
    pc = rec["prior_cum"]
    it = rec["items"]
    c5 = pc["rev"]["위험조정변동"]
    c10 = pc["re_cost"]["위험조정변동"]
    c9 = pc["re_cost"]["보험계약마진상각"]
    base = f"{SRC_ABL[q]} → "
    # item 5 (always changes)
    add_cell("KR0070", q, 5, it["5"], lv("KR0070", 5, q),
             HEAD_ABL + base + f"{it['5']:.0f} 백만원. 원문 {f} L{c5['line']} (보험수익 구간 위험조정변동 {c5['text']}; 같은 파일의 측정요소 롤포워드 RA 해제 {rec['rollforward_prior'].get('ins_ra_release', {}).get('text', '?')} 와 ±1 이내). "
             f"변경 전 마스터값 {lv('KR0070', 5, q)}. 변동 {r6(it['5'] - lv('KR0070', 5, q))}. 산식: 보험수익 구간 위험조정변동 [최신 비교열 누적]. 증거 {EVJ}")
    if q in ("2024.1Q", "2024.2Q", "2024.3Q"):
        add_cell("KR0070", q, 9, it["9"], lv("KR0070", 9, q),
                 HEAD_ABL + base + f"{it['9']:.0f} 백만원. 원문 {f} L{c9['line']} (재보험비용 구간 보험계약마진상각 {c9['text']}; 재보험 롤포워드 CSM 해제 {rec['rollforward_prior'].get('rein_csm_release', {}).get('text', '?')} 와 ±1 이내). "
                 f"변경 전 마스터값 {lv('KR0070', 9, q)}(공란). 산식: -|재보험비용 구간 보험계약마진상각| [최신 비교열 누적]. 증거 {EVJ}")
    add_cell("KR0070", q, 10, it["10"], lv("KR0070", 10, q),
             HEAD_ABL + base + f"{it['10']:.0f} 백만원. 원문 {f} L{c10['line']} (재보험비용 구간 위험조정변동 {c10['text']}; 재보험 롤포워드 RA 해제 {rec['rollforward_prior'].get('rein_ra_release', {}).get('text', '?')} 와 ±1 이내). "
             f"변경 전 마스터값 {lv('KR0070', 10, q)}. 산식: -|재보험비용 구간 위험조정변동| [최신 비교열 누적]. 증거 {EVJ}")
    # derived 7 = 3 - (4+5+6)
    m = rec["master"]
    cl7 = rec["closure7"]
    core7 = (HEAD_ABL + base + f"항목들로 유도 → {r6(it['7'])} 백만원. 산식: 3 - (4+5+6). 피연산자: 3번={m['3']}(마스터), 4번={m['4']}(마스터·gold), 5번={it['5']}(위 줄), 6번={it['6']}(노트: 예상4종-발생4종, 마스터와 같음). "
             f"같은 표의 나머지 행(보험취득현금흐름상각·손실요소배분액·기타보험수익 - 손실부담계약관련비용·발생사고요소조정·보험취득현금흐름상각·손실요소배분액·기타보험서비스비용)의 합 {cl7['value']:.0f} 과 {cl7['diff']:+.3f} 차이(반올림). "
             f"변경 전 마스터값 {lv('KR0070', 7, q)}. 증거 {EVJ}")
    put_derived("KR0070", q, 7, it["7"], core7, f"항목 5 가 {lv('KR0070', 5, q)} → {it['5']:.0f} 로 최신 비교열 값으로 바뀌어 잔차가 달라진다.")
    cl12 = rec["closure12"]
    core12 = (HEAD_ABL + base + f"항목들로 유도 → {r6(it['12'])} 백만원. 산식: 8 - (9+10+11). 피연산자: 8번={m['8']}(마스터), 9번={it['9']}, 10번={it['10']}(위 줄), 11번={it['11']}(노트: 발생재보험금+발생손해조사비-예상재보험금-예상손해조사비, 마스터와 같음). "
              f"같은 표의 나머지 재보험 행(손실회수요소관련수익·발생사고요소조정·손실회수요소배분액·기타재보험수익 - 손실회수요소배분액·기타재보험비용)의 합 {cl12['value']:.0f} 과 {cl12['diff']:+.3f} 차이(반올림). 변경 전 마스터값 {lv('KR0070', 12, q)}. 증거 {EVJ}")
    put_derived("KR0070", q, 12, it["12"], core12, "재보험 항목 9/10 이 최신 비교열 값으로 바뀌어 잔차가 달라진다.")
for q in ("2023.1Q", "2023.2Q", "2023.3Q", "2023.4Q"):
    rec = abl[q]
    f = rec["file"]
    it = rec["items"]
    m = rec["master"]
    ract = [x for x in rec["ract2"] if x]
    rexp = [x for x in rec["rexp2"] if x]
    base = f"{SRC_ABL[q]} → "
    add_cell("KR0070", q, 11, it["11"], lv("KR0070", 11, q),
             HEAD_ABL + base + f"{it['11']:.0f} 백만원. 원문 {f} 발생재보험금·발생손해조사비 {[(x['text'], 'L%d' % x['line']) for x in ract]} - 예상재보험금·예상손해조사비 {[(x['text'], 'L%d' % x['line']) for x in rexp]}. "
             f"변경 전 마스터값 {lv('KR0070', 11, q)}(공란). 산식: (발생재보험금+발생손해조사비 [재보험수익 구간]) - (예상재보험금+예상손해조사비 [재보험비용 구간]). 증거 {EVJ}")
    cl12 = rec["closure12"]
    core12 = (HEAD_ABL + base + f"항목들로 유도 → {r6(it['12'])} 백만원. 산식: 8 - (9+10+11). 피연산자: 8번={m['8']}(마스터), 9번={m['9']}(마스터·앞선 적재), 10번={m['10']}(마스터·앞선 적재), 11번={it['11']}(위 줄). "
              f"같은 표의 나머지 재보험 행의 합 {cl12['value']:.0f} 과 {cl12['diff']:+.3f} 차이(반올림). 변경 전 마스터값 {lv('KR0070', 12, q)}(공란). 증거 {EVJ}")
    put_derived("KR0070", q, 12, it["12"], core12, "")
# seam: 2025.3Q items 5 / 7 (3Q cumulative stays on the old wrong leg; the single quarter would mix 2025.2Q latest and 2025.3Q old leg -> blank beats wrong)
for it_ in (5, 7):
    null_dangi_add.append(["KR0070", "2025.3Q", it_])
# seam table (single quarter vs the printed 3-month column of the same filing)
for q, prev in (("2024.2Q", "2024.1Q"), ("2024.3Q", "2024.2Q"), ("2025.2Q", "2025.1Q")):
    r3 = abl[q].get("prior_3m")
    for itm, key, lab in ((5, "rev", "위험조정변동"), (10, "re_cost", "위험조정변동"), (9, "re_cost", "보험계약마진상각")):
        if q == "2025.2Q" and itm == 9:
            pass
        c3 = r3[key][lab]
        v3 = abs(c3["v"]) * (1 if itm == 5 else -1)
        cur, prv = abl[q]["items"][str(itm)], abl[prev]["items"][str(itm)]
        seams.append(dict(code="KR0070", quarter=q, item=itm, derived_after=r6(cur - prv), printed_3m=dict(value=r6(v3), file=abl[q]["file"], line=c3["line"], printed=c3["text"]), diff_vs_printed_3m=r6(cur - prv - v3),
                          cls="consistent" if abs(cur - prv - v3) <= 1.0 else "mismatch", proposal="none" if abs(cur - prv - v3) <= 1.0 else "check"))

# ====================================================================================================== 2. 동양 KR0087 2024.2Q / 2024.3Q items 5 / 6 + derived 7
dy = json.load(open(f"{EV}/kr0087_dongyang/r01_dy_read.json", encoding="utf-8"))
HEAD_DY = (f"2026-10-24 parser/ifrs17 (pass2, ticket {TICKET} 항목 2: 동양생명 2024.2Q·3Q 항목 5 는 3개월 열(11,829 / 11,840)이 누계 자리에 들어 있었다 — 같은 표의 예상 발생보험금 대 실제 발생보험금(항목 6)도 3개월 열이고 "
           "잔차 항목 7 이 둘에 매달려 있다; 박제·잔차 끼움·게이트 예외 없음): 별도(OFS) 기준, 후속 공시의 전기·전반기·전분기 비교표 누적(누적) 열 → ")
SRC_DY = {"2024.2Q": "FY2025_Q2 반기보고서 전반기 표", "2024.3Q": "FY2025_Q3 분기보고서 전분기 표"}
EVDY = f"{EVREL}/kr0087_dongyang/r01_dy_read.json"
for q in ("2024.2Q", "2024.3Q"):
    rec = dy[q]
    f = rec["file"]
    rr, cr = rec["rev_rows"], rec["cost_rows"]
    ra, exp, act = rr["ra"], rr["exp"], cr["act"]
    it = rec["items"]
    add_cell("KR0087", q, 5, it["5"], lv("KR0087", 5, q),
             HEAD_DY + f"{it['5']:.0f} 백만원 ({SRC_DY[q]}). 원문 {f} L{ra['cum']['line']} (위험조정 변동 누적 {ra['cum']['text']}; 3개월 열 {ra['m3']['text']} L{ra['m3']['line']} 가 마스터에 들어 있던 값). 변경 전 마스터값 {lv('KR0087', 5, q)}. "
             f"변동 {r6(it['5'] - lv('KR0087', 5, q))}. 단일분기(누계 차분) = 인쇄 3개월 열. 증거 {EVDY}")
    add_cell("KR0087", q, 6, it["6"], lv("KR0087", 6, q),
             HEAD_DY + f"{it['6']:.0f} 백만원. 원문 {f} 예상 발생보험금 누적 {exp['cum']['text']} L{exp['cum']['line']} - 실제 발생보험금 누적 {act['cum']['text']} L{act['cum']['line']}. 변경 전 마스터값 {lv('KR0087', 6, q)}"
             f"(3개월 열 {exp['m3']['text']} - {act['m3']['text']} = {rec['items_3m']['6']:.0f}). 변동 {r6(it['6'] - lv('KR0087', 6, q))}. 산식: |예상 발생보험금| - |실제 발생보험금| (2024.1Q 마스터 831 = 136,816 - 135,985 와 같은 정의). 증거 {EVDY}")
    m = rec["master"]
    core7 = (HEAD_DY + f"항목들로 유도 → {r6(rec['i7'])} 백만원. 산식: 3 - (4+5+6). 피연산자: 3번={m['3']}(마스터), 4번={m['4']}(마스터·gold, 표의 제공된 서비스의 보험계약마진 누적과 같다), 5번={it['5']}, 6번={it['6']}(위 줄). "
             f"같은 두 표의 나머지 행의 합 {rec['other7']:.0f} 과 {rec['i7'] - rec['other7']:+.3f} 차이(반올림). 보험수익 행 합 {rec['closure_rows']['rev_sum']:.0f} = 인쇄 합계 {rec['closure_rows']['rev_total']:.0f}. 변경 전 마스터값 {lv('KR0087', 7, q)}. 증거 {EVDY}")
    put_derived("KR0087", q, 7, rec["i7"], core7, f"항목 5 {lv('KR0087', 5, q)} → {it['5']:.0f}, 항목 6 {lv('KR0087', 6, q)} → {it['6']:.0f} 로 바뀌어 잔차가 달라진다.")
    prev = "2024.1Q" if q == "2024.2Q" else "2024.2Q"
    for itm in (5, 6):
        v3 = rec["items_3m"][str(itm)]
        cur = it[str(itm)]
        pv = lv("KR0087", itm, prev) if q == "2024.2Q" else dy["2024.2Q"]["items"][str(itm)]
        seams.append(dict(code="KR0087", quarter=q, item=itm, derived_after=r6(cur - pv), printed_3m=dict(value=r6(v3), file=f, line=(ra["m3"]["line"] if itm == 5 else exp["m3"]["line"]), printed=(ra["m3"]["text"] if itm == 5 else exp["m3"]["text"] + " - " + act["m3"]["text"])),
                          diff_vs_printed_3m=r6(cur - pv - v3), cls="consistent" if abs(cur - pv - v3) <= 1.0 else "mismatch", proposal="none" if abs(cur - pv - v3) <= 1.0 else "check"))

# ====================================================================================================== 3. 현대해상 KR0009 2023.1Q / 2023.2Q items 5 / 9 / 10
hd = json.load(open(f"{EV}/kr0009_hyundai/r01_hd_read.json", encoding="utf-8"))
HEAD_HD = (f"2026-10-24 parser/ifrs17 (pass2, ticket {TICKET} 항목 3: 현대해상 2023.1Q·2Q 항목 5·9·10 을 최신 비교열로 — 후속 공시가 같은 분기를 재작성했다(3Q·4Q 는 그대로); 박제·잔차 끼움·게이트 예외 없음): "
           "별도(OFS) 기준 LOB 노트(천원, 장기 열), ")
SRC_HD = {"2023.1Q": "FY2024_Q1 의 (2) 전분기 표", "2023.2Q": "FY2024_Q2 의 (3) 전반기 누적 표"}
EVHD = f"{EVREL}/kr0009_hyundai/r01_hd_read.json"
for q in ("2023.1Q", "2023.2Q"):
    rec = hd[q]
    f = rec["file"]
    it = rec["items_raw"]
    vals = rec["items_mn"]
    cl = rec["closure"]
    for itm, lab, sign in ((5, "보험수익 구간 위험조정변동", "|…|"), (9, "재보험서비스비용 구간 보험계약마진상각", "-|…|"), (10, "재보험서비스비용 구간 위험조정변동", "-|…|")):
        c = it[str(itm)]
        add_cell("KR0009", q, itm, vals[str(itm)], lv("KR0009", itm, q),
                 HEAD_HD + f"{SRC_HD[q]} → {vals[str(itm)]} 백만원. 원문 {f} L{c['line']} ({lab} 장기 열 {c['text']} 천원 = {abs(c['v']) / 1000:.3f} 백만원). 변경 전 마스터값 {lv('KR0009', itm, q)}. "
                 f"변동 {r6(vals[str(itm)] - lv('KR0009', itm, q))}. 산식: {sign}{lab}. 검산: 장기 열 행 합 = 인쇄 합계 (보험수익 {cl['rev'][0]:,.0f} = {cl['rev'][1]:,.0f}, 재보험 {cl['re'][0]:,.0f} = {cl['re'][1]:,.0f} 천원). 증거 {EVHD}")
    # seam vs printed 3-month table (Q2 only: previous quarter is Q1)
    if q == "2023.2Q":
        tm = rec["three_month"][0]
        for itm, key in ((5, "c5"), (9, "c9"), (10, "c10")):
            v3 = abs(tm[key]["v"]) / 1000.0 * (1 if itm == 5 else -1)
            cur, prv = hd["2023.2Q"]["items_mn"][str(itm)], hd["2023.1Q"]["items_mn"][str(itm)]
            seams.append(dict(code="KR0009", quarter=q, item=itm, derived_after=r6(cur - prv), printed_3m=dict(value=r6(v3), file=f, line=tm[key]["line"], printed=tm[key]["text"]), diff_vs_printed_3m=r6(cur - prv - v3),
                              cls="consistent" if abs(cur - prv - v3) <= 0.01 else "mismatch", proposal="none" if abs(cur - prv - v3) <= 0.01 else "check"))

# ====================================================================================================== 4. 한화생명 KR0068 2023.1Q-2023.4Q items 5 / 6 / 9 / 10 / 11 + derived 7 / 12
hw = json.load(open(f"{EV}/kr0068_hanwha/r02_hw_read.json", encoding="utf-8"))
HEAD_HW = (f"2026-10-24 parser/ifrs17 (pass2, ticket {TICKET} 항목 4: 한화생명 FY2023 LOB 노트 항목(5·6·9·10·11)을 최신 비교열로 — 2026-10-23 적재(READY-25)가 항목 3·4·8 만 옮기고 노트 항목은 옛 판으로 남겼다; "
           "박제·잔차 끼움·게이트 예외 없음): 별도(OFS) 기준 보험손익내역 노트(백만원), 합계 열 누적, ")
SRC_HW = {"2023.1Q": "FY2024_Q1 의 2) 전분기 표", "2023.2Q": "FY2024_Q2 의 2) 전반기 표", "2023.3Q": "FY2024_Q3 의 2) 전분기 표", "2023.4Q": "FY2024_Q4 의 2) 전기 표"}
EVHW = f"{EVREL}/kr0068_hanwha/r02_hw_read.json"
LAB_HW = {"5": ("ra", "위험해제에 따른 위험조정의 변동"), "9": ("recsm", "제공받은 서비스의 재보험계약마진"), "10": ("rera", "위험해제로 인한 위험조정의 변동(재보험비용)")}
for q in ("2023.1Q", "2023.2Q", "2023.3Q", "2023.4Q"):
    rec = hw[q]
    f = rec["file"]
    it = rec["items"]
    rows = rec["rows"]
    m = rec["master"]
    base = f"{SRC_HW[q]} → "
    for itm in (5, 6, 9, 10, 11):
        if str(itm) not in it:
            continue
        old = lv("KR0068", itm, q)
        if old is not None and abs(old - it[str(itm)]) < 5e-4:
            continue
        if itm == 5:
            src = f"위험해제에 따른 위험조정의 변동 합계 {rows['ra']['cum']['text']} L{rows['ra']['cum']['line']}"
            frm = "|위험해제에 따른 위험조정의 변동|"
        elif itm == 6:
            src = f"예상보험금 및 예상보험서비스 비용 합계 {rows['exp']['cum']['text']} L{rows['exp']['cum']['line']} - 실제보험금 및 실제보험서비스비용 합계 {rows['cact']['cum']['text']} L{rows['cact']['cum']['line']}"
            frm = "|예상보험금 및 예상보험서비스 비용| - |실제보험금 및 실제보험서비스비용|"
        elif itm == 9:
            src = f"제공받은 서비스의 재보험계약마진 합계 {rows['recsm']['cum']['text']} L{rows['recsm']['cum']['line']}"
            frm = "-|제공받은 서비스의 재보험계약마진|"
        elif itm == 10:
            src = f"위험해제로 인한 위험조정의 변동(재보험비용) 합계 {rows['rera']['cum']['text']} L{rows['rera']['cum']['line']}"
            frm = "-|위험해제로 인한 위험조정의 변동 (재보험비용)|"
        else:
            src = f"발생 재보험금 및 재보험서비스비용 회수액 합계 {rows['ract']['cum']['text']} L{rows['ract']['cum']['line']} - 회수예상 보험금 및 보험서비스비용 합계 {rows['rexp']['cum']['text']} L{rows['rexp']['cum']['line']}"
            frm = "|발생 재보험금 및 재보험서비스비용 회수액| - |회수예상 보험금 및 보험서비스비용|"
        add_cell("KR0068", q, itm, it[str(itm)], old,
                 HEAD_HW + base + f"{it[str(itm)]:.0f} 백만원. 원문 {f} {src}. 변경 전 마스터값 {old}. 변동 {r6(it[str(itm)] - old)}. 산식: {frm}. 검산: 구간 행 합 = 소계, 소계+보험료배분접근법 = 총계(모두 일치). 증거 {EVHW}")
    # derived 7
    cl7 = rec["closure7"]
    core7 = (HEAD_HW + base + f"항목들로 유도 → {r6(it['7'])} 백만원. 산식: 3 - (4+5+6). 피연산자: 3번={m['3']}(마스터·gold), 4번={m['4']}(마스터·gold), 5번={it['5']}, 6번={it['6']}(노트). "
             f"같은 표의 나머지 행의 합 {cl7['value']:.0f} 과 {cl7['diff']:+.3f} 차이(반올림·3번의 재무제표 정밀도). 변경 전 마스터값 {lv('KR0068', 7, q)}. 증거 {EVHW}")
    put_derived("KR0068", q, 7, it["7"], core7, f"항목 5 {lv('KR0068', 5, q)} → {it['5']:.0f}, 항목 6 {lv('KR0068', 6, q)} → {it['6']:.0f} 로 바뀌어 잔차가 달라진다.")
    if q in ("2023.1Q", "2023.2Q"):
        cl12 = rec["closure12"]
        core12 = (HEAD_HW + base + f"항목들로 유도 → {r6(it['12'])} 백만원. 산식: 8 - (9+10+11). 피연산자: 8번={m['8']}(마스터·gold), 9번={it['9']}, 10번={it['10']}, 11번={it['11']}(위 줄). "
                  f"같은 표의 나머지 재보험 행의 합 {cl12['value']:.0f} 과 {cl12['diff']:+.3f} 차이(반올림). 변경 전 마스터값 {lv('KR0068', 12, q)}. 증거 {EVHW}")
        put_derived("KR0068", q, 12, it["12"], core12, "재보험 항목 9/10/11 이 최신 비교열 값으로 바뀌어 잔차가 달라진다.")
# seams (Q2 / Q3 filings print the 3-month 합계 column): the 2023.2Q single quarter of items 5 / 6 / 7 differs from the printed 3-month column (the FY2024 H1 report re-restated its own 1Q comparative)
r2, r1 = hw["2023.2Q"], hw["2023.1Q"]
for itm in (5, 6, 9, 10, 11):
    cur, prv = r2["items"][str(itm)], r1["items"][str(itm)]
    v3 = r2["items_3m"][str(itm)]
    cell_key = {5: "ra", 6: "exp", 9: "recsm", 10: "rera", 11: "ract"}[itm]
    c3 = r2["rows"][cell_key]["m3"]
    seams.append(dict(code="KR0068", quarter="2023.2Q", item=itm, derived_after=r6(cur - prv), printed_3m=dict(value=r6(v3), file=r2["file"], line=c3["line"], printed=c3["text"]), diff_vs_printed_3m=r6(cur - prv - v3),
                      cls="consistent" if abs(cur - prv - v3) <= 1.0 else "mismatch", proposal="none" if abs(cur - prv - v3) <= 1.0 else "set_dangi"))
for itm in (5, 6, 9, 10, 11):
    cur, prv = hw["2023.3Q"]["items"][str(itm)], hw["2023.2Q"]["items"][str(itm)]
    v3 = hw["2023.3Q"]["items_3m"][str(itm)]
    cell_key = {5: "ra", 6: "exp", 9: "recsm", 10: "rera", 11: "ract"}[itm]
    c3 = hw["2023.3Q"]["rows"][cell_key]["m3"]
    seams.append(dict(code="KR0068", quarter="2023.3Q", item=itm, derived_after=r6(cur - prv), printed_3m=dict(value=r6(v3), file=hw["2023.3Q"]["file"], line=c3["line"], printed=c3["text"]), diff_vs_printed_3m=r6(cur - prv - v3),
                      cls="consistent" if abs(cur - prv - v3) <= 1.0 else "mismatch", proposal="none" if abs(cur - prv - v3) <= 1.0 else "set_dangi"))
# set_dangi: 2023.2Q items 5 and 6 = printed 3-month 합계 column; item 7 = 3 single - 4 single(derived, displayed) - printed 3M of 5 and 6 (the 3-month other rows sum is 7,791 +-1)
f2 = r2["file"]
c5, c6e, c6a = r2["rows"]["ra"]["m3"], r2["rows"]["exp"]["m3"], r2["rows"]["cact"]["m3"]
v5_3m, v6_3m = r2["items_3m"]["5"], r2["items_3m"]["6"]
i3_single = lv("KR0068", 3, "2023.2Q") - lv("KR0068", 3, "2023.1Q")
i4_single = lv("KR0068", 4, "2023.2Q") - lv("KR0068", 4, "2023.1Q")
v7_3m = i3_single - i4_single - v5_3m - v6_3m
set_dangi_add.append(["KR0068", "2023.2Q", 5, r6(v5_3m), f"{f2} L{c5['line']} (위험해제에 따른 위험조정의 변동 합계 3개월 {c5['text']}; 2) 전반기 표) — 후속 공시의 1분기 비교열(FY2024_Q1: 33,858)과 반기 보고서가 암시하는 1분기가 달라 누계 차분(30,976)이 인쇄 3개월과 어긋난다"])
set_dangi_add.append(["KR0068", "2023.2Q", 6, r6(v6_3m), f"{f2} L{c6e['line']} 예상보험금 합계 3개월 {c6e['text']} - L{c6a['line']} 실제보험금 합계 3개월 {c6a['text']} (2) 전반기 표) — 누계 차분(10,213)이 인쇄 3개월(5,793)과 어긋난다(FY2024_Q2 가 자기 1분기 비교열을 다시 재작성)"])
set_dangi_add.append(["KR0068", "2023.2Q", 7, r6(v7_3m), f"유도값: 3 단일분기({r6(i3_single)}) - 4 단일분기({r6(i4_single)}) - 5 인쇄 3개월({v5_3m}) - 6 인쇄 3개월({v6_3m}); 같은 표 나머지 행의 3개월 합 {r2['other7_3m']:.0f} 과 ±1 이내 ({f2} 2) 전반기 표)"])

# ====================================================================================================== 5. OCI KR0032 2023.1Q + KR0082 2023.1Q / 2023.2Q (items 25-32)
oci = json.load(open(f"{EV}/oci_read.json", encoding="utf-8"))
HEAD_OCI = (f"2026-10-24 parser/ifrs17 (pass2, ticket {TICKET} 항목 6: 마스터가 공란이던 OCI 항목 25~32 를 후속 공시 별도 포괄손익계산서의 전기 누적 열 인쇄값으로 채운다 — 원 공시에서는 하위 항목을 못 뽑았고 "
            "최신 비교열이 유일한 원천이다; 박제·잔차 끼움·게이트 예외 없음): 별도(OFS) 기준, ")
for key, nm in (("KR0032|2023.1Q", "NH농협손해보험"), ("KR0082|2023.1Q", "DB생명보험"), ("KR0082|2023.2Q", "DB생명보험")):
    code, q = key.split("|")
    o = oci[key]
    f = o["file"]
    vals = o["vals_mn"]
    lab_of = {25: "기타포괄손익", 31: "총포괄손익"}
    for itm in (25, 26, 27, 28, 29, 30, 31, 32):
        if itm == 25:
            cite = f"기타포괄손익 {o['i25']['text']} L{o['i25']['line']}"
            frm = "기타포괄손익 [전기 누적 열]"
        elif itm == 31:
            cite = f"총포괄손익 {o['i31']['text']} L{o['i31']['line']}"
            frm = "총포괄손익 [전기 누적 열]"
        else:
            leafs = o["leafs"][str(itm)]
            cite = " + ".join(f"{x['label']} {x['cell']['text']} L{x['cell']['line']}" for x in leafs)
            frm = "e21 분류 규칙(classify_leaf)으로 모은 OCI 말단 행의 합 [전기 누적 열]" + (" — 26~30 슬롯에 안 잡히는 말단 행 전부(기대신용손실·확정급여 재측정요소 등)" if itm == 32 else "")
        add_cell(code, q, itm, vals[str(itm)], lv(code, itm, q),
                 HEAD_OCI + f"{nm} {q} ← {o['fy']} 별도 포괄손익계산서(원) 전기 누적 열 → {vals[str(itm)]:.6f} 백만원. 원문 {f} {cite}. 변경 전 마스터값 {lv(code, itm, q)}(공란). 산식: {frm}. "
                 f"검산: 25 = 26+27+28+29+30+32 (잔차 {o['residual_check']:.6f}), 31 = 24+25 (인쇄 {o['i24']['text']} + {o['i25']['text']} 원, 잔차 {o['ni_oci_total_check_won']:,.0f} 원). 증거 {EVREL}/oci_read.json")
# single-quarter seam check (KR0082 2023.2Q vs the printed prior 3-month column)
o2, o1 = oci["KR0082|2023.2Q"], oci["KR0082|2023.1Q"]
for itm in (25, 26, 27, 28, 29, 30, 31, 32):
    v3 = o2["vals_3m_mn"][str(itm)]
    cur, prv = o2["vals_mn"][str(itm)], o1["vals_mn"][str(itm)]
    seams.append(dict(code="KR0082", quarter="2023.2Q", item=itm, derived_after=r6(cur - prv), printed_3m=dict(value=r6(v3), file=o2["file"], line=None, printed="prior 3-month column"), diff_vs_printed_3m=r6(cur - prv - v3),
                      cls="consistent" if abs(cur - prv - v3) <= 0.001 else "mismatch", proposal="none" if abs(cur - prv - v3) <= 0.001 else "check"))

# ====================================================================================================== not loaded (per-cell reasons, for the ticket answer)
not_loaded += [
    dict(code="KR0070", cells="2025.3Q..2026.2Q items 5 / 10 (and derived 7 / 12)", reason="same wrong-leg defect as 2024.4Q-2025.2Q item 5 (master 8,826 / 8,346 / 1,953 / 3,770 are the 구성내역 (4) 표의 위험조정 변동분(*) 열, note table prints 7,271 / 9,587 / 2,248 / 4,081) but the quarters are outside the ticket period 2023.1Q-2025.2Q; reported, not loaded. The 2025.3Q single quarter of items 5 and 7 is blanked (null_dangi) because 2025.2Q now carries the latest note leg while 2025.3Q still carries the old one"),
    dict(code="KR0070", cells="2025.2Q item 15 / 2024.1Q-3Q item 9 original 3-month", reason="item 15 (UNVERIFIED_ITEM15_PRESENCE) is not in the ticket list and was not read; rounding-only CSM differences (CSM1..6 ±1..6 백만원) not loaded (rounding-only cells are never loaded, e21/e25 precedent)"),
    dict(code="KR0087", cells="2024.4Q items 4 / 5 / 9 / 10", reason="sweep false positive: the 'latest' values 246,751 / 43,633 / 2,193 / 1,124 are the 2025 current-period table of the FY2025 annual report (L121693 / L121698 / L122195 / L122200); the 2024 prior-period table prints RA 47,227 (L121775), CSM 259,986 (L121780), 재보험 RA 1,559 (L122267), CSM (1,710) (L122272) = master within rounding (259,987 vs 259,986; -1,711 vs -1,710). Items 9 / 10 are owner xlsx-fill gold (review-loop 2026-06-19/20)"),
    dict(code="KR0087", cells="2025.1Q items 9 / 10", reason="owner xlsx-fill gold (+461 / +295, review-loop 2026-06-19/20); the FY2026_Q1 prior-period 재보험비용 table prints 460 / 294 (L80826 / L80821, expense magnitudes; production definition 9 = -|CSM|, 10 = -|RA| gives -460 / -294); the original FY2025_Q1 filing has no such table (its 재보험 roll-forward prints (461) / (295), L36125 / L36132). Gold is neither the original print nor the latest comparative with the series sign convention -> gold_other, left for the owner. Derived item 12 (owner gold, 2025.1Q) therefore also untouched"),
    dict(code="KR0087", cells="2024.2Q / 2024.3Q items 9 / 10 / 11 / 12", reason="blank (9, 10, 12) or 3-month-total (11 = 523 / -479 = the 3-month 재보험계약의 보험서비스결과) in the master; not in the ticket list; readable from the FY2025 H1 / Q3 재보험 분석 tables only with a new reader; reported"),
    dict(code="KR0079", cells="2024.2Q / 2024.3Q item 5", reason="sweep read the 현행서비스 위험조정 변동분 roll-forward row (18,163.393 / 27,028.878); the production definition (보험수익 구성 RA row, summed over the product tables) is 21,971 / 32,632 in the master and the latest comparative's same row prints 21,970.390 (FY2025_Q2 L99538 + 14 product cells) / 32,631.176 (FY2025_Q3 L52932..) -> rounding-only, not loaded"),
    dict(code="KR0005", cells="2024.3Q item 16 (and 2024.4Q item 16)", reason="printed 18,005 (FY2024_Q3 L3981, FY2025_Q3 L3436; 3-month 6,759) and 27,686 (FY2024_Q4 L5634, FY2025_Q4 L4749) vs master 18,000 / 27,600 (hand-loaded legacy rounding). The builder source already holds 18,005 / 27,686, so a gold cell would equal the source (SAME_EXACT = masked) and need a NEW ledger pin; a fresh build_pl() writes blank for both (zero_other_expense) -> not loaded (pin not allowed)"),
    dict(code="KR0005", cells="2024.3Q item 9", reason="11,571 vs 11,570: rounding-only"),
    dict(code="KR0009", cells="2023.4Q item 16", reason="38,491 vs 38,490.968: rounding-only"),
    dict(code="KR0032", cells="2023.2Q OCI items 25-32 (not in the ticket list) and 2023.1Q items 19-24 (rounding)", reason="2023.2Q latest vector is readable (25 = 20,012.597, 31 = 161,280.165) but the master item 24 = 141,300.0 is a coarse legacy value (printed 141,267.568) so 31 - (24+25) would open by 32.4 백만원; 1Q items 19-24 differ from the printed values by < 1 (rounding-only), not loaded; the 1Q OCI block closes with the master item 24 within 0.288"),
    dict(code="KR0099", cells="2024.1Q-3Q CSM waterfall (latest comparative vector)", reason="chain does not close without a new exemption: latest 2024 vector opens at 31,798.26억 (FY2025_Q1 L37618 3,179,826 mn) = the FY2024 annual's 2023.4Q closing 3,179,825, but the master 2023.4Q closing stays 30,176.4억 (owner D1 option B) and 2024.4Q is owner-verified gold with opening 30,176.4 -> FY-boundary 1,621.86억 (5.4%) and within-FY opening spread 5.4% vs tolerance max(0.5%, 2억): CSM_CONT / WFY RED, an exemption or pin would be needed -> not loaded"),
    dict(code="KDB KR0072", cells="all", reason="held by owner decision (2026-10-23), untouched"),
]

plan = dict(
    generated="2026-10-24", ticket=TICKET, scenario="PASS2_NEIGHBOR_STALE_CELLS",
    buckets=sorted(buckets.values(), key=lambda b: (b["code"], b["quarter"])), csm_buckets=[], seams=seams, not_loaded=not_loaded,
    apply_contract=dict(gold_new=gold_new, gold_replace=gold_replace, csm_gold_new=[], csm_gold_replace=[], csm_gold_remove=[], null_dangi_add=null_dangi_add, null_dangi_remove=[],
                        set_dangi_add=set_dangi_add, set_dangi_remove=[], held=[], drift_fix=[]),
)
json.dump(plan, open(f"{EV}/p2_plan.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("gold_new", len(gold_new), "gold_replace", len(gold_replace), "null_dangi_add", len(null_dangi_add), "set_dangi_add", len(set_dangi_add), "buckets", len(plan["buckets"]), "seams", len(seams))
for e in gold_new + gold_replace:
    print(f"  {e['code']} {e['quarter']} item {e['item']:>2}: {e['was']} -> {e['value']}" + ("  [REPLACE]" if "old_entry" in e else ""))
bad = [s for s in seams if s["cls"] != "consistent"]
print("seams mismatching the printed 3-month column:", [(s["code"], s["quarter"], s["item"], s["derived_after"], s["printed_3m"]["value"]) for s in bad])
