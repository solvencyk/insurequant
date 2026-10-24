# -*- coding: utf-8 -*-
"""Build p4_plan.json (apply contract) for ticket 20261024T1000Z (complete the blocks of 동양생명 KR0087 reinsurance items 9-12 and NH농협손해보험 KR0032 2023 statement).  PL only: no CSM cell is touched, no pin.
Inputs (read-only, produced by the readers of this folder; every number carries its physical xml line):
  kr0032_nhfire/n11_nh_stmt_read.json   NH farm statement prior-period (latest comparative) columns of FY2024_Q1/Q2/Q3, separate basis
  kr0087_dongyang/r12_dy_rollfwd_read.json  동양 separate reinsurance rollforward prior-period tables of FY2025_Q1 / FY2025_Q3 (+ current-period cross-check tables)
  kr0087_dongyang/r11_dy_reins_read.json (pass3) for the 2024.2Q sign note
  live PL_breakdown.json + data/_gold/user_pl_cells.json
Nothing here writes the repo: the plan is written next to this script (p4_plan.json)."""
import json
import sys
from collections import Counter

sys.stdout.reconfigure(encoding="utf-8")
ROOT = "C:/Users/sangwook.cho/Desktop/insurequant"
EV = f"{ROOT}/data/_derived/remaining_20261022/e25_followups/pass4"
EVREL = "data/_derived/remaining_20261022/e25_followups/pass4"
TICKET = "20261024T1000Z"
live = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r for r in json.load(open(f"{ROOT}/PL_breakdown.json", encoding="utf-8"))}
gold = json.load(open(f"{ROOT}/data/_gold/user_pl_cells.json", encoding="utf-8"))
gold_by = {(e["원보험사코드"], e["항목번호"], e["공시분기"]): e for e in gold["set"]}
NAMES = {1: "보험손익", 8: "생명장기 재보험손익", 9: "재보험 CSM상각", 10: "재보험 위험조정 변동", 11: "재보험 예실차", 12: "기타 생명장기 재보험손익", 16: "기타사업비용", 17: "투자손익", 18: "투자이익", 19: "보험금융손익",
         20: "영업이익", 21: "영업외손익"}


def r6(x):
    return None if x is None else round(float(x), 6)


def lv(code, item, q):
    r = live.get((code, item, q))
    return None if r is None else r.get("값")


gold_new, gold_note_append, buckets, seams, null_dangi_add, null_dangi_remove, not_loaded = [], [], {}, [], [], [], []


def add_cell(code, q, item, value, note):
    assert (code, item, q) not in gold_by, (code, item, q, "already has a gold entry")
    was = lv(code, item, q)
    gold_new.append(dict(code=code, item=item, quarter=q, value=r6(value), was=r6(was), note=note))
    b = buckets.setdefault((code, q), dict(code=code, quarter=q, kind="pass4_complete_blocks", cells=[]))
    b["cells"].append(dict(item=item, item_name=NAMES.get(item, str(item)), old=was, new=r6(value), delta=(None if (was is None or value is None) else r6(value - was))))


def seam(code, q, item, derived_after, printed, file, line, text, tol=1.0, extra=None):
    if printed is None:
        e = dict(code=code, quarter=q, item=item, derived_after=r6(derived_after), printed_3m=None, diff_vs_printed_3m=None, cls="no_printed_3m", proposal="none (no printed 3-month column for this item/quarter in any filing)")
    else:
        d = r6(derived_after - printed)
        e = dict(code=code, quarter=q, item=item, derived_after=r6(derived_after), printed_3m=dict(value=r6(printed), file=file, line=line, printed=text), diff_vs_printed_3m=d,
                 cls="consistent" if abs(d) <= tol + 1e-9 else "mismatch", proposal="none" if abs(d) <= tol + 1e-9 else "null_dangi")
    if extra:
        e.update(extra)
    seams.append(e)
    return e


# ====================================================================================================== 1. NH농협손해보험 KR0032 (item 1 of the ticket)
nh = json.load(open(f"{EV}/kr0032_nhfire/n11_nh_stmt_read.json", encoding="utf-8"))
EVJ_NH = f"{EVREL}/kr0032_nhfire/n11_nh_stmt_read.json"
FYN = {"2023.1Q": "FY2024_Q1 분기보고서", "2023.2Q": "FY2024_Q2 반기보고서"}
HEAD_NH = (f"2026-10-24 parser/ifrs17 (pass4, ticket {TICKET} 항목 1: NH농협손해보험 2023.2Q 손익계산서 앞부분(보험손익·기타영업수익[구조적 0]·기타사업비용·투자손익·투자이익·보험금융손익·영업이익·영업외손익)과 2023.1Q 보험금융손익을 "
           "후속 공시(FY2024 1분기·반기) 별도 손익계산서의 전기 누적 열 원 단위 인쇄값으로 맞춘다 — 2023.2Q 는 이 칸들이 공란이었고(항목 16 만 경영공시 요약 PL 의 0.01억 반올림 41,900), 2023.1Q 항목 19 는 반올림된 -56,596 이었다; "
           "박제·잔차 끼움·게이트 예외 없음): 별도(OFS) 기준, ")


def chain(rec):
    c = rec["chk_cum_won"]
    return (f"검산(원 단위 정확): 보험손익 + 투자손익 - 영업이익 = {c['c_1_17_20']:,.0f}, 영업이익 + 영업외수익 - 영업외비용 - 세전이익 = {c['c_20_21_22']:,.0f}, 세전이익 - 법인세 - 순이익 = {c['c_22_23_24']:,.0f}, "
            f"투자영업수익 - 투자영업비용 - 투자손익 = {c['c_inv']:,.0f}, 투자이익(레그 식) - (투자손익 - 보험금융손익) = {c['c_18_leg']:,.0f}.")


def cite(rec, keys):
    return " ".join(f"{k}={rec[k]['text']}@L{rec[k]['line']}" for k in keys)


# 2023.2Q: items 1, 16, 17, 18, 19, 20, 21
q = "2023.2Q"
rec, vals = nh[q], nh[q]["vals_mn"]
f = rec["file"]
tail = f"원문 {f} (원). 증거 {EVJ_NH}"
single2 = nh["seam_2Q_minus_1Q"]
single3 = nh["seam_3Q_minus_2Q"]
SING = (" 단일분기(2Q - 1Q)는 FY2024_Q2 인쇄 3개월 열과 소수 6자리까지 일치하고, 3Q 단일분기(3Q 누계 - 2Q 누계)도 FY2024_Q3 인쇄 3개월 열과 소수 6자리까지 일치한다(2023.3Q 누계는 이미 FY2024_Q3 전기 누적 열과 같다).")
add_cell("KR0032", q, 1, vals["1"], HEAD_NH + f"FY2024_Q2 반기보고서 전기 누적 열 → {vals['1']:.6f} 백만원. {tail} I.보험손익 {rec['i1']['text']}@L{rec['i1']['line']}. 변경 전 마스터값 {lv('KR0032', 1, q)}(공란). 산식: I.보험손익 [전기 누적 열]. " + chain(rec) + SING)
add_cell("KR0032", q, 15, 0.0, HEAD_NH + "구조적 0 (기타영업수익 행 없음) → 0.0 백만원. 원문 " + f"{f} 별도 손익계산서(표 L{rec['table']}, 원)의 보험손익 구간은 보험영업수익(보험수익 · 재보험수익) / 보험영업비용(보험서비스비용 · 재보험비용 · 기타사업비용) 뿐이고 기타영업수익 행이 없다; "
         "FS-API 응답(frmtrm_add)에도 기타영업 계정이 없다(kr0032_nhfire/n12_fsapi_item15.txt). 이 저장소의 관례는 계정이 없으면 0.0 이다(scripts/fetch_dart_fs.py L398 `t1.setdefault(15, 0.0)`, scripts/build_pl_breakdown.py L129-132, "
         "삼성화재 2023.1Q 전례 L719-724): NH농협손보도 2023.1Q(빌더 _GOLD_CELL_OVERRIDE) · 2023.3Q 이후(FS-API 기본값) 전 분기가 0.0 이고 2023.2Q 만 FS-API 응답이 없어(status 013) 공란이었다. "
         f"변경 전 마스터값 {lv('KR0032', 15, q)}(공란). 이 칸이 있어야 보험손익 폐쇄식의 adj 형태(1 = 2 + 15 - 16; PL_BRIDGE 는 15·16 이 둘 다 있을 때만 후보를 만든다)가 평가된다: 154,049 + 0 - 40,748.545805 = 113,300.454195 대 "
         "보험손익 113,301.721794, 잔차 -1.268(항목 2 가 정수 백만원). 15 가 비어 있으면 ΣLOB 만 비교돼 기타사업비용만큼(약 40,747) 어긋난 것으로 보인다. 15 의 크기는 이 폐쇄식이 다시 검산한다(±1.3 밖의 값이면 깨진다) — 잔차 끼움이 아니다. "
         f"증거 {EVJ_NH}")
add_cell("KR0032", q, 16, vals["16"], HEAD_NH + f"FY2024_Q2 반기보고서 전기 누적 열 → {vals['16']:.6f} 백만원. {tail} 3)기타사업비용 {rec['i16']['text']}@L{rec['i16']['line']}. 변경 전 마스터값 {lv('KR0032', 16, q)} "
         f"(경영공시 요약 PL 의 0.01억 단위 반올림 6개월 값; 최신 비교열과의 {vals['16'] - lv('KR0032', 16, q):+.6f} 차이는 반올림이 아니라 공시 판 차이 — 같은 항목의 2023.1Q 는 e20 에서 이미 같은 필링의 전기 열 20,951.967361 로 바뀌었다). "
         f"산식: 3)기타사업비용 [전기 누적 열]. 이 값으로 2Q 단일분기(누계 - 1Q 누계) = {single2['16']['derived']:.6f} 가 FY2024_Q2 인쇄 3개월 {rec['i16_3m']['text']}@L{rec['i16_3m']['line']} 와 같아져 e20 (c) 가 비워 둔 단일분기(null_dangi)를 푼다." + SING)
add_cell("KR0032", q, 17, vals["17"], HEAD_NH + f"FY2024_Q2 반기보고서 전기 누적 열 → {vals['17']:.6f} 백만원. {tail} II.투자손익 {rec['i17']['text']}@L{rec['i17']['line']}. 변경 전 마스터값 {lv('KR0032', 17, q)}(공란). 산식: II.투자손익 [전기 누적 열]. " + chain(rec) + SING)
add_cell("KR0032", q, 18, vals["18"], HEAD_NH + f"FY2024_Q2 반기보고서 전기 누적 열 → {vals['18']:.6f} 백만원. {tail} 산식: 투자손익 - 보험금융손익 (= 17 - 19; 레그 식 (투자영업수익 {rec['inv_rev']['text']}@L{rec['inv_rev']['line']} - 보험금융수익 - 재보험금융수익) "
         f"- (투자영업비용 {rec['inv_exp']['text']}@L{rec['inv_exp']['line']} - 보험금융비용 - 재보험금융비용) 과 원 단위까지 같다). 같은 정의가 마스터 2023.1Q 투자이익(e20 gold) · 2023.3Q 에서 쓰였다. 변경 전 마스터값 {lv('KR0032', 18, q)}(공란). " + chain(rec) + SING)
add_cell("KR0032", q, 19, vals["19"], HEAD_NH + f"FY2024_Q2 반기보고서 전기 누적 열 → {vals['19']:.6f} 백만원. {tail} 산식: (1)보험금융수익 {rec['ins_fin_inc']['text']}@L{rec['ins_fin_inc']['line']} + 2)재보험금융수익 {rec['re_fin_inc']['text']}@L{rec['re_fin_inc']['line']}) "
         f"- (1)보험금융비용 {rec['ins_fin_exp']['text']}@L{rec['ins_fin_exp']['line']} + 2)재보험금융비용 {rec['re_fin_exp']['text']}@L{rec['re_fin_exp']['line']}) [전기 누적]; 같은 정의가 마스터 2023.3Q 보험금융손익 -176,393.797006 을 원 단위까지 재현한다. "
         f"변경 전 마스터값 {lv('KR0032', 19, q)}(공란). " + chain(rec) + SING)
add_cell("KR0032", q, 20, vals["20"], HEAD_NH + f"FY2024_Q2 반기보고서 전기 누적 열 → {vals['20']:.6f} 백만원. {tail} III.영업이익 {rec['i20']['text']}@L{rec['i20']['line']}. 변경 전 마스터값 {lv('KR0032', 20, q)}(공란). 산식: III.영업이익 [전기 누적 열]. " + chain(rec) + SING)
add_cell("KR0032", q, 21, vals["21"], HEAD_NH + f"FY2024_Q2 반기보고서 전기 누적 열 → {vals['21']:.6f} 백만원. {tail} IV.영업외수익 {rec['i21a']['text']}@L{rec['i21a']['line']} - V.영업외비용 {rec['i21b']['text']}@L{rec['i21b']['line']}. 변경 전 마스터값 {lv('KR0032', 21, q)}(공란). "
         f"산식: 영업외수익 - 영업외비용 [전기 누적]. " + chain(rec) + SING)
# 2023.1Q item 19
q = "2023.1Q"
rec, vals = nh[q], nh[q]["vals_mn"]
add_cell("KR0032", q, 19, vals["19"], HEAD_NH + f"FY2024_Q1 분기보고서 전기 누적 열 → {vals['19']:.6f} 백만원. 원문 {rec['file']} (원) 산식: (1)보험금융수익 {rec['ins_fin_inc']['text']}@L{rec['ins_fin_inc']['line']} + 2)재보험금융수익 {rec['re_fin_inc']['text']}@L{rec['re_fin_inc']['line']}) "
         f"- (1)보험금융비용 {rec['ins_fin_exp']['text']}@L{rec['ins_fin_exp']['line']} + 2)재보험금융비용 {rec['re_fin_exp']['text']}@L{rec['re_fin_exp']['line']}) [전기 누적]. 변경 전 마스터값 {lv('KR0032', 19, q)} (반올림된 정수 백만원; 같은 분기 e20 gold 의 투자손익 54,365.643131 · 투자이익 110,961.09562 와 "
         f"17 = 18 + 19 이 {lv('KR0032', 17, q) - lv('KR0032', 18, q) - lv('KR0032', 19, q):+.6f} 열려 있었다). 변경 {vals['19'] - lv('KR0032', 19, q):+.6f}; 이 값으로 17 = 18 + 19 가 원 단위까지 닫힌다. " + chain(rec) +
         " 같은 필링에서 1Q 의 보험손익(55,130.707378) · 기타사업비용(20,951.967361) · 투자손익 · 투자이익 · 영업이익 · 영업외손익 · 세전이익 · 법인세 · 순이익은 마스터와 소수 6자리까지 같아 바꾸지 않았다(n11_nh_stmt_read.txt). " + f"증거 {EVJ_NH}")
# seams: 2Q single and 3Q single vs the printed prior 3-month columns
r2, r3 = nh["2023.2Q"], nh["2023.3Q"]
KEYMAP = {1: "i1", 16: "i16", 17: "i17", 20: "i20"}
for it in (1, 16, 17, 18, 19, 20, 21):
    s = single2[str(it)]
    k = KEYMAP.get(it)
    line = r2[k + "_3m"]["line"] if k else None
    txt = r2[k + "_3m"]["text"] if k else "derived from the printed 3-month rows (" + ("보험금융수익·재보험금융수익·보험금융비용·재보험금융비용" if it == 19 else "17 - 19" if it == 18 else "IV.영업외수익 - V.영업외비용") + ")"
    seam("KR0032", "2023.2Q", it, s["derived"], s["printed_3m"], r2["file"], line, txt, tol=0.001)
for it in (1, 16, 17, 18, 19, 20, 21):
    s = single3[str(it)]
    k = KEYMAP.get(it)
    line = r3[k + "_3m"]["line"] if k else None
    txt = r3[k + "_3m"]["text"] if k else "derived from the printed 3-month rows"
    seam("KR0032", "2023.3Q", it, s["derived"], s["printed_3m"], r3["file"], line, txt, tol=0.001)
# 2023.3Q cumulative proof (live master == FY2024_Q3 prior cumulative) is part of n11 (cum vs live master diff 0.000000 for every item)
for it in (1, 16, 17, 18, 19, 20, 21):
    assert abs(r3["vals_mn"][str(it)] - lv("KR0032", it, "2023.3Q")) < 1e-6, (it, r3["vals_mn"][str(it)], lv("KR0032", it, "2023.3Q"))
assert abs(nh["2023.1Q"]["vals_mn"]["1"] - lv("KR0032", 1, "2023.1Q")) < 1e-6 and abs(nh["2023.1Q"]["vals_mn"]["16"] - lv("KR0032", 16, "2023.1Q")) < 1e-6
assert abs(nh["2023.1Q"]["vals_mn"]["17"] - lv("KR0032", 17, "2023.1Q")) < 1e-6 and abs(nh["2023.1Q"]["vals_mn"]["18"] - lv("KR0032", 18, "2023.1Q")) < 1e-6
assert all(abs(s["diff"]) < 1e-6 for s in single2.values()) and all(abs(s["diff"]) < 1e-6 for s in single3.values())
null_dangi_remove.append(["KR0032", "2023.2Q", 16])

# ====================================================================================================== 2. 동양생명 KR0087 reinsurance items 9 / 10 (+ blank 11) of 2024.1Q and 2024.3Q (item 2 of the ticket)
dy = json.load(open(f"{EV}/kr0087_dongyang/r12_dy_rollfwd_read.json", encoding="utf-8"))
EVJ_DY = f"{EVREL}/kr0087_dongyang/r12_dy_rollfwd_read.json"
pre_all = [(r["원보험사코드"], r["공시분기"], r["값"]) for r in live.values() if r["항목번호"] == 9 and r["값"] is not None and r["값"] != 0]
n_neg = sum(1 for _c, _q, v in pre_all if v < 0)
SIGN_EV = (f"부호는 생산 정의 -|값|(extract_tier2_dongyang · docs/domains/csm-pl-basis-methodology.md '출재 CSM, 음수')를 쓴다 — 마스터 동양 2025.2Q -878/-565 · 2025.3Q -1,401/-841 · 2025.4Q -2,193/-1,124 와 같은 방식이다"
           f"(2025.3Q 는 같은 롤포워드 서식의 당분기 표 합계 +1,401/841 을 -|값| 로 실었다; 적재 전 마스터 항목 9 비영 {len(pre_all)}칸 중 음수 {n_neg}칸). 인쇄 부호는 서식마다 다르다(분기 롤포워드 서식 (i) 2024.1Q CSM +1,936 · RA (425), "
           "서식 (ii) 2024.3Q CSM (3,079) · RA +1,180 = 재보험계약부채(자산) 관점의 반대 부호). owner 손입력 2024.4Q·2025.1Q gold 는 인쇄 부호를 썼다 — 시리즈 부호 규약은 owner 결정 대기(TODO 24차 후속 ①).")
HEAD_DY = (f"2026-10-24 parser/ifrs17 (pass4, ticket {TICKET} 항목 2: 동양생명 2024.1Q·2024.3Q 재보험 항목 9·10 을 후속 공시(FY2025 1분기·3분기 보고서)의 별도 재보험 측정요소 롤포워드 전분기 표(최신 비교열)의 보험계약마진 해제 · "
           "비금융위험 위험조정 해제 합계 열로 채우고, 항목 11 의 기존 값은 같은 필링의 재보험계약 보험서비스결과 합계(= 항목 8)이지 예실차(발생한 재보험금 - 예상 재보험금)가 아니라 빈칸으로 한다 — 구성 행(발생한 보험금 · 예상 보험금)은 반기보고서만 "
           "인쇄하고 1분기·3분기 보고서는 합계만 인쇄한다; 항목 12 = 8 - (9+10+11) 은 11 이 확정돼야 하므로 빈칸 유지; 박제·잔차 끼움·게이트 예외 없음): 별도(OFS) 기준, ")
ITEM_DY = {}
for q, key, fy_lab, view in (("2024.1Q", "FY2025_Q1|prior", "FY2025_Q1 분기보고서", "서식 (i), 순자산(부채) 관점"), ("2024.3Q", "FY2025_Q3|prior", "FY2025_Q3 분기보고서", "서식 (ii), 재보험계약부채(자산) 관점")):
    d = dy[key]
    c, ra = d["csm_total"], d["ra_total"]
    v9, v10 = -abs(c["v"]), -abs(ra["v"])
    ITEM_DY[q] = (v9, v10)
    base = (f"{fy_lab} 전분기 롤포워드 → ")
    chk = ("검증: 같은 보고서(FY2025_Q2 반기)의 전반기 별도 롤포워드에서 CSM 해제 (70)+2,599 = 2,529 · RA 해제 (33)+(791) = (824) 이 2024.2Q 마스터(손익 분석 표 기반) -2,528 / -824 와 일치하고(반올림 1), "
           f"전분기 표의 기초 잔액(76,215 / 23,030 / (452) / (89,800) / 3,340)이 FY2025 1분기 · 3분기 전분기 표에서 같아 3분기 전분기 표는 2024-01-01 부터 9개월 누계다. 표 합계 열은 구성 열의 합과 ±1 이내(n12 출력).")
    add_cell("KR0087", q, 9, v9, HEAD_DY + base + f"{v9:,.0f} 백만원. 원문 {d['file']} L{c['line']} (보험계약마진 해제 합계 열 {c['text']}; 행 R{d['csm_row_line']}, 표 L{d['table'][0]}-{d['table'][1]}, {view}). 변경 전 마스터값 {lv('KR0087', 9, q)}(공란). "
             f"산식: -|CSM 해제 합계|. {SIGN_EV} {chk} 증거 {EVJ_DY}")
    add_cell("KR0087", q, 10, v10, HEAD_DY + base + f"{v10:,.0f} 백만원. 원문 {d['file']} L{ra['line']} (비금융위험 위험조정 해제 합계 열 {ra['text']}; 행 R{d['ra_row_line']}, 표 L{d['table'][0]}-{d['table'][1]}, {view}). 변경 전 마스터값 {lv('KR0087', 10, q)}(공란). "
             f"산식: -|RA 해제 합계|. 부호 근거는 항목 9 와 같다. {chk} 증거 {EVJ_DY}")
OLD11 = {"2024.1Q": lv("KR0087", 11, "2024.1Q"), "2024.3Q": lv("KR0087", 11, "2024.3Q")}
assert OLD11 == {"2024.1Q": 3805.0, "2024.3Q": -479.0}, OLD11
add_cell("KR0087", "2024.1Q", 11, None, HEAD_DY + "빈칸(null). 변경 전 마스터값 3,805 = 같은 필링 FY2025_Q1 순보험손익 노트 「재보험계약의 보험서비스결과」 전분기 열 3,805 (data/dart/FY2025_Q1/raw/KR0087_동양생명/20250515001025.xml L21182, "
         "별도 L39379) = 항목 8 (3,804.477666) 이지 예실차가 아니다. 예실차 구성 행(재보험수익 발생한 보험금 · 재보험비용 예상 보험금)은 1분기 보고서가 인쇄하지 않아(반기보고서만 분석 표를 인쇄) 확정할 수 없다 → 틀린 값 대신 빈칸. "
         "항목 12 도 8 - (9+10+11) 이라 11 이 확정돼야 하므로 빈칸 유지. 2024.2Q 항목 11(14,273)은 반기보고서 분석 표라 그대로. " + f"증거 {EVJ_DY}")
add_cell("KR0087", "2024.3Q", 11, None, HEAD_DY + "빈칸(null). 변경 전 마스터값 -479 = 같은 필링 FY2025_Q3 의 3개월 열 「재보험계약의 보험서비스결과」 (479) (data/dart/FY2025_Q3/raw/KR0087_동양생명/xml/20251114002594.xml L64091, pass3 확인) — "
         "누계(3,848.737943)와 기간이 다른 3개월 합계이지 예실차가 아니다. 예실차 구성 행은 3분기 보고서가 인쇄하지 않아 확정할 수 없다(2025.3Q 항목 11 gold null 과 같은 사유) → 빈칸. 항목 12 도 11 이 확정돼야 하므로 빈칸 유지. " + f"증거 {EVJ_DY}")
# sign confirmation: append the evidence to the pass3 notes of 2024.2Q items 9 and 12 (value untouched)
APPEND_93 = (f" [2026-10-24 pass4, 티켓 {TICKET} 항목 3 — 부호 확인: -|값| 을 유지한다(값 불변). 근거: {SIGN_EV} 부호를 인쇄 부호로 바꾸면 9 = +2,528 · 12 = -11649.382027 이고 8 = 9+10+11+12 합은 같다.]")
for it in (9, 12):
    g = gold_by[("KR0087", it, "2024.2Q")]
    gold_note_append.append(dict(code="KR0087", item=it, quarter="2024.2Q", old_note=g["note"], append=APPEND_93, value=g["값"]))
# single-quarter seams: 2Q single of 9 / 10 (new 1Q cumulative) vs the printed 3-month column of the FY2025_Q2 prior-half tables; 3Q single has no printed 3-month column
r11 = json.load(open(f"{ROOT}/data/_derived/remaining_20261022/e25_followups/pass3/kr0087_dongyang/r11_dy_reins_read.json", encoding="utf-8"))
f2 = r11["file"]
pr = r11["prior"]
seam("KR0087", "2024.2Q", 9, -2528.0 - ITEM_DY["2024.1Q"][0], -abs(pr["csm"]["m3"]["v"]), f2, pr["csm"]["m3"]["line"], pr["csm"]["m3"]["text"], tol=1.0)
seam("KR0087", "2024.2Q", 10, -824.0 - ITEM_DY["2024.1Q"][1], -abs(pr["ra"]["m3"]["v"]), f2, pr["ra"]["m3"]["line"], pr["ra"]["m3"]["text"], tol=1.0)
seam("KR0087", "2024.3Q", 9, ITEM_DY["2024.3Q"][0] - (-2528.0), None, None, None, None)
seam("KR0087", "2024.3Q", 10, ITEM_DY["2024.3Q"][1] - (-824.0), None, None, None, None)
# the owner xlsx-fill cumulatives of 2024.4Q (9: -1,711, 10: +1,559) are on another sign/basis than the 3Q rollforward cumulative: the builder difference would be garbage (+1,368 / +2,739) -> single quarter blank (value untouched)
g49, g410 = gold_by[("KR0087", 9, "2024.4Q")], gold_by[("KR0087", 10, "2024.4Q")]
assert (g49["값"], g410["값"]) == (-1711.0, 1559.0)
null_dangi_add.append(["KR0087", "2024.4Q", 9])
null_dangi_add.append(["KR0087", "2024.4Q", 10])
seam("KR0087", "2024.4Q", 9, g49["값"] - ITEM_DY["2024.3Q"][0], None, None, None, None, extra=dict(note="owner gold cumulative -1,711 minus the new 3Q rollforward cumulative -3,079 = +1,368 (garbage) -> null_dangi"))
seam("KR0087", "2024.4Q", 10, g410["값"] - ITEM_DY["2024.3Q"][1], None, None, None, None, extra=dict(note="owner gold cumulative +1,559 minus the new 3Q rollforward cumulative -1,180 = +2,739 (garbage) -> null_dangi"))

# ====================================================================================================== not loaded (per-cell reasons)
not_loaded += [
    dict(code="KR0087", cells="2024.1Q / 2024.3Q item 11 (예실차) and item 12", reason="FY2025_Q1 and FY2025_Q3 print no reinsurance expected/actual claims rows (only FY2025_Q2 prints the 재보험수익 / 재보험비용 분석 tables); the old cells (3,805 / -479) were the 보험서비스결과 totals "
            "= item 8, not 예실차, so they are blanked (gold null, like the 2025.3Q precedent) and item 12 (= 8 - (9+10+11)) stays blank"),
    dict(code="KR0087", cells="2024.4Q items 9 / 10 / 12 and 2025.1Q items 9 / 10 / 11 / 12 (owner xlsx-fill gold)", reason="untouched by the ticket's rule; the 4Q cumulatives (-1,711 / +1,559) are inconsistent in sign and size with the new 3Q rollforward cumulatives (-3,079 / -1,180): "
            "the only change is null_dangi on the 4Q single quarters of items 9 / 10 so the builder does not print a +1,368 / +2,739 difference"),
    dict(code="KR0087", cells="2024.4Q item 11 (5,758 = item 8)", reason="same defect as 2024.1Q/3Q, but the owner gold items 9/10/12 of 2024.4Q close around 5,758 (8 = 9+10+11+12), so it stays; the 4Q single quarter of item 11 changes from 6,237 (= 5,758 - (-479)) to blank because 3Q is now blank"),
    dict(code="KR0032", cells="2023.2Q LOB-note items 6 / 7 / 11 / 12", reason="outside the ticket (no statement line)"),
]
plan = dict(
    generated="2026-10-24", ticket=TICKET, scenario="PASS4_COMPLETE_BLOCKS_DONGYANG_NHFIRE",
    buckets=sorted(buckets.values(), key=lambda b: (b["code"], b["quarter"])), csm_buckets=[], seams=seams, not_loaded=not_loaded,
    apply_contract=dict(gold_new=gold_new, gold_replace=[], gold_note_append=gold_note_append, csm_gold_new=[], csm_gold_replace=[], csm_gold_remove=[], null_dangi_add=null_dangi_add, null_dangi_remove=null_dangi_remove,
                        set_dangi_add=[], set_dangi_remove=[], held=[], drift_fix=[]),
)
json.dump(plan, open(f"{EV}/p4_plan.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("gold_new", len(gold_new), "gold_note_append", len(gold_note_append), "null_dangi_add", len(null_dangi_add), "null_dangi_remove", len(null_dangi_remove), "buckets", len(plan["buckets"]), "seams", len(seams))
for e in gold_new:
    print(f"  {e['code']} {e['quarter']} item {e['item']:>2}: {e['was']} -> {e['value']}")
for s in seams:
    p3 = s["printed_3m"]
    print(f"  seam {s['code']} {s['quarter']} item {s['item']:>2}: derived {s['derived_after']} vs printed 3M {None if p3 is None else p3['value']} diff {s['diff_vs_printed_3m']} -> {s['cls']}")
print("APPEND len", len(APPEND_93))
