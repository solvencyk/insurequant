# -*- coding: utf-8 -*-
"""Build e25_plan.json (apply contract) for the four open parser/ifrs17 tickets of 2026-10-23/24.  PL only (no CSM cell is touched by tickets 1-4).
Inputs (all read-only, produced by the reader scripts of this folder):
  kr0099_kblife/k01_read_kblife.json   KB라이프 2023.1Q items 9 / 11 / 12 (FY2024 Q1 prior-period reinsurance rows)
  kr0070_abl/a01_read_abl_fy2023.json  ABL FY2023 items 5 / 6 / 9 / 10 (+ item 7 derived) from the FY2024 Q1/H1/Q3/annual prior-period notes
  kr0104_nhlife/n01_read_vs_master.json  농협생명 2024.1Q/2Q items 17 / 18 / 20 / 21 (FY2025 Q1/H1 prior cumulative column of the separate statement)
  kr0010_kbsonbo/k01_item16_series.txt   KB손해보험 item 16 series (diagnosis only; the two hand-loaded wrong cells are fixed by drift_fix = blank)
  live PL_breakdown.json + data/_gold/user_pl_cells.json  (old values, existing gold entries)
Nothing here writes the repo: the plan is written next to this script (e25_plan.json)."""
import json
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = "C:/Users/sangwook.cho/Desktop/insurequant"
EV = f"{ROOT}/data/_derived/remaining_20261022/e25_followups"
EVREL = "data/_derived/remaining_20261022/e25_followups"
TICKET = {
    "KR0099": "20261023T1130Z", "KR0070": "20261023T1210Z", "KR0104": "20261023T0600Z", "KR0010": "20261024T0100Z",
}
live = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r for r in json.load(open(f"{ROOT}/PL_breakdown.json", encoding="utf-8"))}
gold = json.load(open(f"{ROOT}/data/_gold/user_pl_cells.json", encoding="utf-8"))
gold_by = {(e["원보험사코드"], e["항목번호"], e["공시분기"]): e for e in gold["set"]}
NAMES = {1: "보험손익", 3: "생명장기 원수손익", 4: "원수 CSM상각", 5: "원수 위험조정 변동", 6: "원수 예실차", 7: "기타 생명장기 원수손익", 8: "생명장기 재보험손익",
         9: "재보험 CSM상각", 10: "재보험 위험조정 변동", 11: "재보험 예실차", 12: "기타 생명장기 재보험손익", 16: "기타사업비용", 17: "투자손익", 18: "투자이익",
         20: "영업이익", 21: "영업외손익"}


def r6(x):
    return round(float(x), 6)


def lv(code, item, q):
    r = live.get((code, item, q))
    return None if r is None else r.get("값")


gold_new, gold_replace, drift_fix, buckets = [], [], [], {}


def add_cell(code, q, item, value, was, note, kind="new", old_entry=None):
    ent = dict(code=code, item=item, quarter=q, value=r6(value), was=(None if was is None else r6(was)), note=note)
    if kind == "replace":
        ent["old_entry"] = old_entry
        gold_replace.append(ent)
    else:
        gold_new.append(ent)
    b = buckets.setdefault((code, q), dict(code=code, quarter=q, kind="e25_followup", cells=[]))
    b["cells"].append(dict(item=item, item_name=NAMES.get(item, str(item)), old=lv(code, item, q), new=r6(value), delta=(None if lv(code, item, q) is None else r6(value - lv(code, item, q)))))


# ====================================================================================================== 1. KB라이프 KR0099 2023.1Q items 9 / 11 / 12
k = json.load(open(f"{EV}/kr0099_kblife/k01_read_kblife.json", encoding="utf-8"))
q = "2023.1Q"
rec = k[q]
f1 = rec["file"]
cit = rec["cites"]
HEAD = ("2026-10-24 parser/ifrs17 (e25, ticket 20261023T1130Z: KB라이프 2023.1Q 재보험 하위 항목 9/11/12 를 최신 비교열로 갱신, 단일분기 2023.2Q 를 -1118/-27/763 인쇄 3개월 값에 맞춤; "
        "박제·잔차 끼움·게이트 예외 없음): 별도(OFS) 기준 life_note 경로, FY2024_Q1 의 전기 2023.1Q 누적(3월) 열(합계) → ")
add_cell("KR0099", q, 9, rec["cum"]["item9"], lv("KR0099", 9, q),
         HEAD + f"{rec['cum']['item9']} 백만원. 원문 {f1} L{cit['re_csm']['cell_line']} (제공받은 서비스의 재보험계약마진 {cit['re_csm']['printed']}). 변경 전 마스터값 {lv('KR0099', 9, q)}. 변동 {r6(rec['cum']['item9'] - lv('KR0099', 9, q))}. "
         f"산식: -|제공받은 서비스의 재보험계약마진 [합계, 전분기]|. 증거 {EVREL}/kr0099_kblife/k01_read_kblife.json")
add_cell("KR0099", q, 11, rec["cum"]["item11"], lv("KR0099", 11, q),
         HEAD + f"{rec['cum']['item11']} 백만원. 원문 {f1} L{cit['re_act']['cell_line']} (발생 재보험금 및 재보험서비스비용회수액 {cit['re_act']['printed']}) 외 L{cit['re_exp']['cell_line']} (회수예상 보험금 및 보험서비스비용 {cit['re_exp']['printed']}). "
         f"변경 전 마스터값 {lv('KR0099', 11, q)}. 변동 {r6(rec['cum']['item11'] - lv('KR0099', 11, q))}. 산식: |발생 재보험금 및 재보험서비스비용 회수액| - |회수예상 보험금 및 보험서비스비용|. 증거 {EVREL}/kr0099_kblife/k01_read_kblife.json")
add_cell("KR0099", q, 12, rec["cum"]["item12"], lv("KR0099", 12, q),
         HEAD + f"{rec['cum']['item12']} 백만원. 원문 {f1} L{cit['re_csm']['cell_line']} 외 합산 3줄(증거 k01_read_kblife.json cites). 변경 전 마스터값 {lv('KR0099', 12, q)}. 변동 {r6(rec['cum']['item12'] - lv('KR0099', 12, q))}. "
         f"산식: 8 - (9+10+11). 피연산자: 8번={rec['cum']['item8_live']}(master), 9번={rec['cum']['item9']}(plan), 10번={rec['cum']['item10']}(master = 인쇄 L{cit['re_ra']['cell_line']} {cit['re_ra']['printed']}), 11번={rec['cum']['item11']}(plan). 증거 {EVREL}/kr0099_kblife/k01_read_kblife.json")

# ====================================================================================================== 2. 농협생명 KR0104 2024.1Q / 2024.2Q items 17 / 18 / 20 / 21
n = json.load(open(f"{EV}/kr0104_nhlife/n01_read_vs_master.json", encoding="utf-8"))
NH_FILE = {"2024.1Q": ("FY2025_Q1", "20250515001350", "data/dart/FY2025_Q1/raw/KR0104_농협생명보험/20250515001350.xml"),
           "2024.2Q": ("FY2025_Q2", "20250814002779", "data/dart/FY2025_Q2/raw/KR0104_농협생명보험/20250814002779.xml")}
for q in ("2024.1Q", "2024.2Q"):
    fy, rc, path = NH_FILE[q]
    for it in (17, 18, 20, 21):
        c = n[q][str(it)]
        newv = r6(c["val"])
        cites = ", ".join(f"L{x}" for x in c["lines"])
        formula = "statement line" if it != 18 else "derived from statement lines (production definition): 18 = 17 - 19 (19 = -(보험금융비용 + 재보험금융비용))"
        note = (f"2026-10-24 parser/ifrs17 (e25, ticket 20261023T0600Z: 농협생명 2024.1Q/2Q 항목 17/18/20/21 을 FY2025 전기 누적 열로 갱신 — 발행사가 2.909352 백만원을 투자손익에서 영업외손익으로 재분류, 세전·순이익 불변; "
                f"2024.3Q 단일분기 이음매가 닫힌다; 박제·잔차 끼움·게이트 예외 없음): 별도(OFS) 기준 4-2 포괄손익계산서, {fy} rcept {rc} 의 전기 {q} 누적 열 → {newv} 백만원. "
                f"원문 {path} {cites}. 단위 원. 변경 전 마스터값 {c['master']}. 변동 {r6(newv - c['master'])}. 산식: {formula}. 증거 {EVREL}/kr0104_nhlife/n01_read_vs_master.json")
        add_cell("KR0104", q, it, newv, c["master"], note)

# ====================================================================================================== 3. ABL KR0070 FY2023 items 5 / 6 / 7 / 9 / 10
a = json.load(open(f"{EV}/kr0070_abl/a01_read_abl_fy2023.json", encoding="utf-8"))
ABL_Q = ["2023.1Q", "2023.2Q", "2023.3Q", "2023.4Q"]


def sv(x):
    return x if isinstance(x, (int, float)) else x[0]


abl_vals = {}
for q in ABL_Q:
    pc = a[q]["prior_cum"]
    abl_vals[q] = {5: float(sv(pc["5"])), 6: float(sv(pc["6"])), 9: -abs(float(sv(pc["9"]))), 10: -abs(float(sv(pc["10"]))), 4: float(sv(pc["4"]))}
    i3 = lv("KR0070", 3, q)
    abl_vals[q][3] = i3
    abl_vals[q][7] = r6(i3 - (abl_vals[q][4] + abl_vals[q][5] + abl_vals[q][6]))
    # item 4 of the live master must equal the note value read here (gold item 4 of the previous load)
    assert abs(lv("KR0070", 4, q) - abl_vals[q][4]) < 1e-9, (q, lv("KR0070", 4, q), abl_vals[q][4])

ABL_HEAD = ("2026-10-24 parser/ifrs17 (e25, ticket 20261023T1210Z: ABL FY2023 항목 5/6/7/9/10 을 최신 비교열로 갱신 — 같은 판의 항목 3·4 와 맞춤; 2023.1Q 항목 5 = 272 는 재보험 표 값의 오추출; 박제·잔차 끼움·게이트 예외 없음): "
            "별도(OFS) 기준 life_note 경로, ")
ABL_SRC = {"2023.1Q": "FY2024_Q1 의 전기 2023.1Q 누적(3월) 열", "2023.2Q": "FY2024_Q2 의 전반기 누적 열", "2023.3Q": "FY2024_Q3 의 전분기 누적 열", "2023.4Q": "FY2024_Q4 의 전기 열"}
for q in ABL_Q:
    rec = a[q]
    pc, cc = rec["prior_cum"], rec["prior_cum_cites"]
    base = f"{rec['file']}"
    # item 5
    c = pc["5"]
    add_cell("KR0070", q, 5, abl_vals[q][5], lv("KR0070", 5, q),
             ABL_HEAD + f"{ABL_SRC[q]} → {abl_vals[q][5]} 백만원. 원문 {base} L{c[1]} (보험수익 구분 위험조정변동 {c[2]}; 전분기·전기 측정요소 롤포워드 RA 해제 {a[q]['rollforward'].get('ins_ra_release', ['?'])[0]} 와 ±1 이내). "
             f"변경 전 마스터값 {lv('KR0070', 5, q)}. 변동 {r6(abl_vals[q][5] - lv('KR0070', 5, q))}. 산식: 보험수익 구분 위험조정변동 [전기/전분기 누적]. 증거 {EVREL}/kr0070_abl/a01_read_abl_fy2023.json")
    # item 6
    exp_l = [x[1] if x else None for x in cc["exp4"]]
    inc_l = [x[1] if x else None for x in cc["inc4"]]
    add_cell("KR0070", q, 6, abl_vals[q][6], lv("KR0070", 6, q),
             ABL_HEAD + f"{ABL_SRC[q]} → {abl_vals[q][6]} 백만원. 원문 {base} 예상 4종 L{exp_l} - 발생 4종 L{inc_l}. 변경 전 마스터값 {lv('KR0070', 6, q)}. 변동 신규. "
             f"산식: (예상보험금+예상손해조사비+예상계약유지비+예상투자관리비) - (발생보험금+발생손해조사비+발생계약유지비+발생투자관리비). 증거 {EVREL}/kr0070_abl/a01_read_abl_fy2023.json")
    # item 9
    c = pc["9"]
    if abs(abl_vals[q][9] - (lv("KR0070", 9, q) if lv("KR0070", 9, q) is not None else 1e18)) > 1e-9:
        add_cell("KR0070", q, 9, abl_vals[q][9], lv("KR0070", 9, q),
                 ABL_HEAD + f"{ABL_SRC[q]} → {abl_vals[q][9]} 백만원. 원문 {base} L{c[1]} (재보험비용 구분 보험계약마진상각 {c[2]}; 재보험 롤포워드 CSM 해제 {a[q]['rollforward'].get('rein_csm_release', ['?'])[0]} 와 일치). "
                 f"변경 전 마스터값 {lv('KR0070', 9, q)}. 변동 {'신규' if lv('KR0070', 9, q) is None else r6(abl_vals[q][9] - lv('KR0070', 9, q))}. 산식: -|재보험비용 구분 보험계약마진상각 [전기/전분기 누적]|. 증거 {EVREL}/kr0070_abl/a01_read_abl_fy2023.json")
    # item 10
    c = pc["10"]
    if abs(abl_vals[q][10] - (lv("KR0070", 10, q) if lv("KR0070", 10, q) is not None else 1e18)) > 1e-9:
        add_cell("KR0070", q, 10, abl_vals[q][10], lv("KR0070", 10, q),
                 ABL_HEAD + f"{ABL_SRC[q]} → {abl_vals[q][10]} 백만원. 원문 {base} L{c[1]} (재보험비용 구분 위험조정변동 {c[2]}; 재보험 롤포워드 RA 해제 {a[q]['rollforward'].get('rein_ra_release', ['?'])[0]} 와 일치). "
                 f"변경 전 마스터값 {lv('KR0070', 10, q)}. 변동 {'신규' if lv('KR0070', 10, q) is None else r6(abl_vals[q][10] - lv('KR0070', 10, q))}. 산식: -|재보험비용 구분 위험조정변동 [전기/전분기 누적]|. 증거 {EVREL}/kr0070_abl/a01_read_abl_fy2023.json")
    # item 7 = 3 - (4+5+6)
    old_g = gold_by.get(("KR0070", 7, q))
    note7 = (ABL_HEAD + f"{ABL_SRC[q]} 항목들로 유도 → {abl_vals[q][7]} 백만원. 원문 {base} (항목 5·6 은 위 줄, 항목 3·4 는 앞선 적재의 gold). 산식: 3 - (4+5+6). 피연산자: 3번={abl_vals[q][3]}(gold), 4번={abl_vals[q][4]}(gold), 5번={abl_vals[q][5]}(plan), 6번={abl_vals[q][6]}(plan). "
             f"같은 주석의 나머지 행(기타보험수익·손실부담계약관련비용·발생사고요소조정·기타보험서비스비용 등)의 합과 ±1 이내로 같다. 증거 {EVREL}/kr0070_abl/x01_verify_e25.txt")
    if old_g is not None:
        # replaced in place: keep the previous gold value / note verbatim in the new note (same convention as the 2026-10-23 ABL item-4 replacement)
        note7 = (f"owner 2026-10-24 지시 범위(티켓 20261023T1210Z (3) 항목 7 gold 재검산 → 낡았으면 제거): 이전 gold 값 {old_g['값']}, 이전 was {old_g.get('was')}, 이전 note 원문 「{old_g.get('note')}」. "
                 "이전 값은 옛 항목 3·4(원 공시 판)와 오추출 항목 5(272)로 계산된 잔차였고 2026-10-23 적재로 항목 3·4 가 최신 비교열로 바뀌어 낡았다. 제거하고 최신 비교열 항목으로 다시 유도한 값을 싣는다. " + note7)
        add_cell("KR0070", q, 7, abl_vals[q][7], old_g["값"], note7, kind="replace", old_entry=old_g)
    else:
        add_cell("KR0070", q, 7, abl_vals[q][7], lv("KR0070", 7, q), note7)

# ====================================================================================================== 4. KB손보 KR0010 item 16: hand-loaded wrong cells -> fresh-build value (blank)
for q, v in (("2024.4Q", 60900.0), ("2025.2Q", 33300.0)):
    assert lv("KR0010", 16, q) == v, (q, lv("KR0010", 16, q))
    drift_fix.append(dict(code="KR0010", item=16, quarter=q, live_value=v, fresh_value=None))
    b = buckets.setdefault(("KR0010", q), dict(code="KR0010", quarter=q, kind="e25_followup", cells=[]))
    b["cells"].append(dict(item=16, item_name=NAMES[16], old=v, new=None, delta=None))

plan = dict(
    generated="2026-10-24", tickets=TICKET, scenario="E25_FOLLOWUPS",
    buckets=sorted(buckets.values(), key=lambda b: (b["code"], b["quarter"])), csm_buckets=[], seams=[],
    apply_contract=dict(gold_new=gold_new, gold_replace=gold_replace, csm_gold_new=[], csm_gold_replace=[], csm_gold_remove=[], null_dangi_add=[], null_dangi_remove=[], set_dangi_add=[], set_dangi_remove=[],
                        held=[], drift_fix=drift_fix),
)
json.dump(plan, open(f"{EV}/e25_plan.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("gold_new", len(gold_new), "gold_replace", len(gold_replace), "drift_fix", len(drift_fix), "buckets", len(plan["buckets"]))
for e in gold_new + gold_replace:
    print(f"  {e['code']} {e['quarter']} item {e['item']:>2}: {e['was']} -> {e['value']}")
for d in drift_fix:
    print("  drift_fix", d)
