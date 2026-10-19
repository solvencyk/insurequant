"""사별 비교 화면(compare.html)의 패널 JSON 빌더.

읽기 전용 입력(루트 마스터 JSON 7종)에서 `data/compare/panel_compare.json` 하나만 만든다. 마스터는 쓰지 않는다.
화면은 이 파일을 fetch 하고, 데이터는 HTML 에 인라인하지 않는다.

실행: C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/viz_build_compare_panel.py
검사: ... viz_build_compare_panel.py --check
      마스터에서 다시 만든 바이트가 디스크의 패널 JSON(화면이 fetch 하는 파일)과 같은지 + 1.5MB 예산을 본다.
      다르면 exit 1. 아무것도 쓰지 않는다(불변식 1: 화면 파일 = 검사한 파일).

지표 정의(스카우트 실측 레시피)
- 지급여력비율/기본자본비율: kics_disclosure.json 항목 27/28, 적용후 = 값_적용후 ?? 값, 적용전 = 값
- 기말 CSM: CSM_waterfall.json 항목 6 (억원)
- 신계약 CSM 배수: NB_CSM_multiple.json 신계약CSM배수_연누계
- 보험손익/당기순이익/투자손익(연 누계 YTD, 억원): PL_breakdown.json 항목 1/24/17 의 `값`(백만원 -> 억원 /100). 1Q=1Q, 2Q=1~2Q 누계, 3Q=1~3Q 누계, 4Q=연간.
  당분기 값(`값_당분기`)·누계 차분은 쓰지 않는다(owner 2026-10-11: 손익은 당분기가 아니라 YTD 기준).
- 기본 지표 해약환급금준비금(IFRS17_BS 5, 적립 잔액, 백만원 -> 억원)은 ROE 다음 기본 목록에 들어간다(owner 2026-10-08).
- 추가 지표(화면 기본 목록에는 없고 사용자가 끌어다 넣는 것, default=false): 지급여력금액(K-ICS 1)·지급여력기준금액(K-ICS 14)·신계약 CSM(NB_CSM_multiple 신계약CSM_연누계)·
  투자손익(PL 17 연 누계)·자본총계(IFRS17_BS 3)·자산총계(IFRS17_BS 1). 전부 금액이라 중앙값은 만들지 않는다.
- ROE(연환산): 당기순이익 연 누계(항목 24) x 4/q (1Q x4 · 2Q x2 · 3Q x4/3 · 4Q x1) / 평균(직전 4Q 자본, 당분기말 자본)(IFRS17_BS 항목 3), 두 자본 > 0 일 때만, 2024.1Q 부터
- 유지율 13/25/37/61회차: master_persistency.json 회차별 채널행 합산 Σ유지/Σ대상 (원문오기 SWAPPED=맞교환, INCONSISTENT=제외). 화면에서는 한 차트에 모아 비교
- 손해율: master_loss_ratio.json 합계/합계/현재가치 Σ예상보험금/Σ위험보험료 (세그먼트 합산)
- 손해율 가정 곡선(loss_curve): 같은 합계/합계 행을 경과차년(1~10년·11~15·16~20·21~25·26~30·30년 이후)별로 같은 방식으로 합산.
  미래에셋생명만 1~10년을 한 구간("1~10년")으로 공시해 별도 칸에 둔다. 업계 중앙값은 칸별로 같은 규칙(같은 유형, 재보험·보증 제외, 5곳 미만 null).
- 비교 단위(loss_curve.units·u·up·med_u·unit_note·default_unit, loss_pv.vu·medu; 2026-10-19 추가 키): 구분 x 상품구분 x 포트폴리오 한 줄 단위로 같은 방식 합산.
  원수사(생보·손보 따로)는 최신 결산에서 10사 이상 공시 + 업권 위험보험료 1% 이상, 재보사는 세그먼트 x Non-Par x 포트폴리오로 4사 이상. 정본 docs/loss_ratio_comparable_unit_20261019.md.

업계 중앙값: 같은 생/손보 유형 안에서, 재보험(KR1000)·보증(KR0150) 제외, 그 분기에 값이 있는 회사만으로 계산한다
(결측은 0 으로 채우지 않고 건너뜀). 표본이 5곳 미만이면 중앙값을 만들지 않는다(null).
"""
import json
import re
import statistics
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "compare" / "panel_compare.json"
MAX_BYTES = int(1.5 * 1024 * 1024)


def load(rel):
    with open(ROOT / rel, encoding="utf-8") as f:
        return json.load(f)


def num(v):
    if v is None or v == "":
        return None
    try:
        x = float(str(v).replace(",", ""))
    except ValueError:
        return None
    return x


NAME_ABBR = {
    "스위스리아시아": "스위스리", "알지에이리인슈어런스": "RGA", "마이브라운반려동물전문보험": "마이브라운",
    "케이비손해보험": "KB손보", "케이비라이프생명보험": "KB라이프", "신한이지손해보험": "신한EZ손해",
    "에이비엘생명보험": "ABL생명", "케이디비생명보험": "KDB생명", "아이엠라이프생명보험": "iM라이프",
    "디지비생명보험": "DGB생명", "엠지손해보험": "MG손보", "에이아이지손해보험": "AIG손보",
    "에이아이에이생명보험": "AIA생명", "비엔피파리바카디프생명보험": "BNP카디프생명",
    "교보라이프플래닛생명보험": "교보라이프플래닛", "처브라이프생명보험": "처브라이프",
    "메트라이프생명보험": "메트라이프", "악사손해보험": "악사손보", "신한라이프생명보험": "신한라이프",
    "푸본현대생명보험": "푸본현대",
}


def short_name(n):
    if n in NAME_ABBR:
        return NAME_ABBR[n]
    n = re.sub(r"화재해상보험$", "화재", n)
    n = re.sub(r"해상화재보험$", "해상", n)
    n = re.sub(r"손해보험$", "손보", n)
    n = re.sub(r"생명보험$", "생명", n)
    n = re.sub(r"재보험$", "", n)
    n = re.sub(r"보증보험$", "보증", n)
    return n


def qkey(q):
    m = re.match(r"^(\d{4})\.(\d)Q$", q)
    return (int(m.group(1)), int(m.group(2)))


# ---------------------------------------------------------------- K-ICS
kics = load("kics_disclosure.json")
QUARTERS = sorted({r["공시분기"] for r in kics}, key=qkey)
QI = {q: i for i, q in enumerate(QUARTERS)}
NQ = len(QUARTERS)

# 업권 3분류: data/company_segment.json 의 코드->구분 매핑이 마스터 생손보여부보다 우선한다(index.html 과 같은 파일).
# 재보험·보증(Re)은 type 을 "재보·보증" 으로 따로 두어 생보/손보 비교·업계 중앙값 모집단에 섞이지 않게 한다.
SEG_MAP = load("data/company_segment.json")["by_code"]
T_RE = "재보·보증"
TYPES = ("생보", "손보", T_RE)
roster = {}
for r in kics:
    c = r["원보험사코드"]
    if SEG_MAP.get(c, {}).get("seg") == "Re":
        ty = T_RE
    else:
        ty = "생보" if r["생손보여부"] == "생명보험" else "손보"
    roster[c] = {"code": c, "name": r["원수사명"], "type": ty}
for c, d in roster.items():
    d["short"] = short_name(d["name"])
    d["sector"] = SEG_MAP.get(c, {}).get("tag", "")

kics_rows = {}
for r in kics:
    kics_rows[(r["원보험사코드"], r["공시분기"], r["항목번호"])] = r


def kics_series(item, mode):
    out = {}
    for c in roster:
        arr = [None] * NQ
        for q in QUARTERS:
            r = kics_rows.get((c, q, item))
            if r is None:
                continue
            pre = num(r["값"])
            post = num(r.get("값_적용후"))
            v = (post if post is not None else pre) if mode == "post" else pre
            arr[QI[q]] = v
        out[c] = arr
    return out


# size rank within type by 2026.2Q SCR (item 14, post)
LAST_Q = QUARTERS[-1]
for c, d in roster.items():
    r = kics_rows.get((c, LAST_Q, 14))
    v = None
    if r:
        v = num(r.get("값_적용후"))
        if v is None:
            v = num(r["값"])
    d["scr"] = v
for t in TYPES:
    ordered = sorted((d for d in roster.values() if d["type"] == t and d["scr"] is not None), key=lambda d: -d["scr"])
    for i, d in enumerate(ordered):
        d["size_rank"] = i + 1
for d in roster.values():
    d.setdefault("size_rank", None)
    base = (d["size_rank"] or 0) - 1
    d["color_idx"] = (base + (2 if d["type"] == "손보" else 0)) % 4
    d["peer_ok"] = d["type"] != T_RE and d["code"] not in ("KR0004", "KR1098", "KR0051")
    d["median_pool"] = d["type"] != T_RE

# ---------------------------------------------------------------- IFRS17 masters
csm = load("CSM_waterfall.json")
csm_closing = defaultdict(lambda: [None] * NQ)
for r in csm:
    if r["항목번호"] == 6 and r["원보험사코드"] in roster and r["공시분기"] in QI:
        csm_closing[r["원보험사코드"]][QI[r["공시분기"]]] = num(r["값"])

nb = load("NB_CSM_multiple.json")
nb_mult = defaultdict(lambda: [None] * NQ)
nb_amt = defaultdict(lambda: [None] * NQ)
for r in nb:
    if r["원보험사코드"] in roster and r["공시분기"] in QI:
        nb_mult[r["원보험사코드"]][QI[r["공시분기"]]] = num(r["신계약CSM배수_연누계"])
        nb_amt[r["원보험사코드"]][QI[r["공시분기"]]] = num(r["신계약CSM_연누계"])

pl = load("PL_breakdown.json")
ytd = {}
for r in pl:
    if r["원보험사코드"] not in roster or r["공시분기"] not in QI:
        continue
    it = int(r["항목번호"]) if str(r["항목번호"]).isdigit() else None
    if it in (1, 17, 24):
        ytd[(it, r["원보험사코드"], r["공시분기"])] = num(r["값"])


def ytd_eok(item):
    """연 누계(YTD) 손익, 억원. PL_breakdown `값` 이 이미 1Q=1Q · 2Q=1~2Q · 3Q=1~3Q · 4Q=연간 누계다."""
    out = {}
    for c in roster:
        arr = [None] * NQ
        for q in QUARTERS:
            v = ytd.get((item, c, q))
            arr[QI[q]] = None if v is None else v / 100.0   # 백만원 -> 억원
        out[c] = arr
    return out


ins_profit = ytd_eok(1)
net_income = ytd_eok(24)
inv_profit = ytd_eok(17)

bs = load("IFRS17_BS.json")
equity = {}
assets = {}
surrender = {}
for r in bs:
    if r["항목번호"] in (1, 3, 5) and r["원보험사코드"] in roster and r["공시분기"] in QI:
        {1: assets, 3: equity, 5: surrender}[r["항목번호"]][(r["원보험사코드"], r["공시분기"])] = num(r["값"])


def bs_eok(src):
    out = {}
    for c in roster:
        out[c] = [None if src.get((c, q)) is None else src[(c, q)] / 100.0 for q in QUARTERS]   # 백만원 -> 억원
    return out


equity_eok = bs_eok(equity)
assets_eok = bs_eok(assets)
surrender_eok = bs_eok(surrender)

roe = {}
for c in roster:
    arr = [None] * NQ
    for q in QUARTERS:
        y, n = qkey(q)
        if (y, n) < (2024, 1):
            continue
        ni = ytd.get((24, c, q))
        e1 = equity.get((c, q))
        e0 = equity.get((c, f"{y-1}.4Q"))
        if ni is None or e1 is None or e0 is None or e1 <= 0 or e0 <= 0:
            continue
        arr[QI[q]] = ni * 4.0 / n / ((e0 + e1) / 2.0) * 100.0
    roe[c] = arr

# ---------------------------------------------------------------- persistency 13/25/37/61
per = load("data/persistency/master_persistency.json")


def persist_series(label):
    grp = defaultdict(list)
    for r in per:
        if r["회차구분"] == label and r["원보험사코드"] in roster and r["공시분기"] in QI:
            grp[(r["원보험사코드"], r["공시분기"])].append(r)
    out = defaultdict(lambda: [None] * NQ)
    for (c, q), rows in grp.items():
        sn = sm = 0.0
        for r in rows:
            n, m, f = r["대상신계약액"], r["유지계약액"], r.get("플래그") or ""
            if "원문오기" in f:
                if "AMOUNT_ROWS_SWAPPED" in f:
                    n, m = m, n
                elif "AMOUNT_INCONSISTENT" in f:
                    continue
            if n is None or m is None or n <= 0:
                continue
            sn += n
            sm += m
        if sn > 0:
            out[c][QI[q]] = sm / sn * 100.0
    return out


PERSIST_N = (13, 25, 37, 61)
persist = {n: persist_series(f"{n}회차") for n in PERSIST_N}

# ---------------------------------------------------------------- loss ratio PV
lr = load("data/loss_ratio/master_loss_ratio.json")
lrg = defaultdict(lambda: [0.0, 0.0, set(), 0])
for r in lr:
    if r["구분"] == "합계" and r["포트폴리오"] == "합계" and r["경과차년"] == "현재가치":
        if r["원보험사코드"] not in roster or r["공시분기"] not in QI:
            continue
        rp, ec = r["위험보험료"], r["예상보험금"]
        if rp is None or ec is None:
            continue
        a = lrg[(r["원보험사코드"], r["공시분기"])]
        a[0] += rp
        a[1] += ec
        a[2].add(r["단위"])
        a[3] += 1
loss_pv = defaultdict(lambda: [None] * NQ)
for (c, q), (rp, ec, units, k) in lrg.items():
    assert len(units) == 1, (c, q, units)
    if rp > 0:
        loss_pv[c][QI[q]] = ec / rp * 100.0

# ---------------------------------------------------------------- loss ratio curve (경과차년별)
LR_LABELS = [f"{n}년" for n in range(1, 11)] + ["11~15년", "16~20년", "21~25년", "26~30년", "30년 이후"]
LR_COARSE = "1~10년"
LR_SLOTS = LR_LABELS + [LR_COARSE]
lr_acc = defaultdict(lambda: [0.0, 0.0])
lr_unit = defaultdict(set)
for r in lr:
    if r["구분"] != "합계" or r["포트폴리오"] != "합계" or r["경과차년"] not in LR_SLOTS:
        continue
    if r["원보험사코드"] not in roster or r["공시분기"] not in QI:
        continue
    rp, ec = r["위험보험료"], r["예상보험금"]
    if rp is None or ec is None:
        continue
    a = lr_acc[(r["원보험사코드"], r["공시분기"], r["경과차년"])]
    a[0] += rp
    a[1] += ec
    lr_unit[(r["원보험사코드"], r["공시분기"])].add(r["단위"])
assert all(len(u) == 1 for u in lr_unit.values()), "한 공시의 손해율 행에 단위가 섞였다"
loss_curve_v = defaultdict(dict)
for (c, q, lab), (rp, ec) in lr_acc.items():
    if rp > 0:
        row = loss_curve_v[c].setdefault(q, [None] * len(LR_SLOTS))
        row[LR_SLOTS.index(lab)] = round(ec / rp * 100.0, 1)
loss_curve_med = {}
for ty in TYPES:
    pool = [c for c, d in roster.items() if d["type"] == ty and d["median_pool"]]
    byq = {}
    for q in sorted({q for c in pool for q in loss_curve_v.get(c, {})}, key=qkey):
        row = []
        for k in range(len(LR_LABELS)):
            xs = [loss_curve_v[c][q][k] for c in pool if q in loss_curve_v.get(c, {}) and loss_curve_v[c][q][k] is not None]
            row.append(round(statistics.median(xs), 1) if len(xs) >= 5 else None)
        byq[q] = row
    loss_curve_med[ty] = byq

# ---------------------------------------------------------------- loss ratio by 구분 (Non-Par / Direct-Par / Indirect-Par)
# 합계 경로(위)는 그대로 두고 구분 축만 더한다. 마스터에는 구분 소계 행이 없으므로 그 구분의 잎 행(모든 포트폴리오·세그먼트)을
# (회사, 공시분기, 경과차년) 단위로 더한다: Σ예상보험금 / Σ위험보험료 x 100, 두 금액이 모두 있는 칸만, 위험보험료 합이 0 이하이면 없음.
# (viz_build_persistency_lossratio_panels._agg 와 같은 규칙이라 IFRS17 8절 구분 소계 행과 맞는다. 세그먼트는 가로질러 합산.)
LR_GROUPS = ["Non-Par", "Direct-Par", "Indirect-Par"]
LR_PV = "현재가치"
lrg2_acc = defaultdict(lambda: [0.0, 0.0])
lrg2_unit = defaultdict(set)
for r in lr:
    g = r["구분"]
    if g not in LR_GROUPS or r["포트폴리오"] in ("합계", ""):
        continue
    if r["원보험사코드"] not in roster or r["공시분기"] not in QI:
        continue
    lab = r["경과차년"]
    if lab not in LR_SLOTS and lab != LR_PV:
        continue
    rp, ec = r["위험보험료"], r["예상보험금"]
    if rp is None or ec is None:
        continue
    a = lrg2_acc[(g, r["원보험사코드"], r["공시분기"], lab)]
    a[0] += rp
    a[1] += ec
    lrg2_unit[(g, r["원보험사코드"], r["공시분기"])].add(r["단위"])
assert all(len(u) == 1 for u in lrg2_unit.values()), "한 공시·한 구분의 손해율 행에 단위가 섞였다"
loss_curve_g = {g: defaultdict(dict) for g in LR_GROUPS}
loss_pv_g = {g: defaultdict(lambda: [None] * NQ) for g in LR_GROUPS}
for (g, c, q, lab), (rp, ec) in lrg2_acc.items():
    if rp <= 0:
        continue
    if lab == LR_PV:
        loss_pv_g[g][c][QI[q]] = ec / rp * 100.0
    else:
        row = loss_curve_g[g][c].setdefault(q, [None] * len(LR_SLOTS))
        row[LR_SLOTS.index(lab)] = round(ec / rp * 100.0, 1)
loss_curve_med_g = {}
for ty in TYPES:
    pool = [c for c, d in roster.items() if d["type"] == ty and d["median_pool"]]
    per_g = {}
    for g in LR_GROUPS:
        byq = {}
        for q in sorted({q for c in pool for q in loss_curve_g[g].get(c, {})}, key=qkey):
            row = []
            for k in range(len(LR_LABELS)):
                xs = [loss_curve_g[g][c][q][k] for c in pool if q in loss_curve_g[g].get(c, {}) and loss_curve_g[g][c][q][k] is not None]
                row.append(round(statistics.median(xs), 1) if len(xs) >= 5 else None)
            if any(x is not None for x in row):
                byq[q] = row
        if byq:
            per_g[g] = byq
    loss_curve_med_g[ty] = per_g
LR_GROUPS_SHOWN = [g for g in LR_GROUPS if loss_curve_g[g]]

# ---------------------------------------------------------------- loss ratio by 비교 단위 (구분 x 상품구분 x 포트폴리오)
# 정본 docs/loss_ratio_comparable_unit_20261019.md (2·4·7절). 합계·구분 경로는 그대로 두고 단위 축만 더한다(추가 키).
# 단위 = 공시 표의 한 줄: 원수사(생보·손보 따로)는 구분 x 상품구분 x 포트폴리오, 재보사는 세그먼트(생명/장기손해) x Non-Par x 포트폴리오.
# 목록에 넣는 규칙(전부 최신 공시분기 기준): 원수사 단위는 10사 이상이 위험보험료 합 > 0 으로 공시하고 업권 위험보험료의 1% 이상,
# 재보사 단위는 4사 이상. 값 규칙(셀 배치·반올림·존재 조건)은 위 g 축과 같다: Σ예상보험금 / Σ위험보험료 x 100 (두 금액이 모두 있는 잎 행만), 합이 0 이하면 없음.
UNIT_MIN_CO = 10               # 원수사 단위: 이 수 이상의 회사가 공시
UNIT_MIN_SHARE_PCT = 1.0       # 원수사 단위: 업권 위험보험료 비중 하한(%)
RE_UNIT_MIN_CO = 4             # 재보사 단위: 이 수 이상의 재보사가 공시
UNIT_MEDIAN_MIN = 5            # 업계 중앙값: 값이 있는 회사 수 하한(g 축 med_g 와 같음)
UNIT_FADE_EOK = 100            # 화면이 흐리게 그릴 위험보험료 기준(억원): up 이 이 값 미만인 칸
UNIT_SECTOR = {"생보": "생보", "손보": "손보", T_RE: "재보"}      # roster type -> 단위 업권 이름
RE_PAIRS = (("생명", "건강"), ("생명", "사망"), ("장기손해", "질병"), ("장기손해", "상해"))   # 재보사 Non-Par 후보 (세그먼트 x 포트폴리오)
RE_NAME = "재보"
# 마스터 위험보험료·예상보험금은 이미 억원이다(build_loss_ratio_master.py 가 백만원 원문을 ÷100 해서 싣고 `단위` 열에는 원문 표기만 남긴다).
# 그래서 두 단위 모두 배수 1.0 이다(2026-10-19 수정: 0.01 로 또 나눠 백만원 공시사 up 이 100배 작았다). 모르는 단위 표기는 KeyError 로 멈춘다.
UNIT_SCALE = {"억원": 1.0, "백만원": 1.0}
# 키 토큰(ASCII): 단위가 생기면 아래 표에 없는 이름이 걸려 빌드가 멈춘다(조용히 지어내지 않는다).
TOK_SECTOR = {"생보": "life", "손보": "nl", RE_NAME: "re"}
TOK_GUBUN = {"Non-Par": "np", "Indirect-Par": "ip", "Direct-Par": "dp"}
TOK_PRODUCT = {"무배당": "mb", "유배당": "yb", "변액": "va", "": "x"}
TOK_PORTFOLIO = {"사망": "death", "건강": "health", "상해": "injury", "질병": "illness", "재물": "property",
                 "연금저축": "pension", "자산연계형연금저축": "alpension", "기타": "other", "복합": "mixed"}
TOK_SEGMENT = {"생명": "life", "장기손해": "ltnl"}


def re_seg_group(seg, pf):
    """재보사 잎 행의 세그먼트 묶음. 세그먼트가 '생명…'/'장기손해…'(공동·전통형 포함)이면 그대로, 비었으면 포트폴리오 이름으로 정한다."""
    if seg.startswith("생명"):
        return "생명"
    if seg.startswith("장기손해"):
        return "장기손해"
    if seg == "":
        return "생명" if pf in ("건강", "사망") else ("장기손해" if pf in ("질병", "상해") else None)
    return None


# 잎 행 수집: leaf[(코드, 분기)][(세그먼트, 구분, 상품구분, 포트폴리오)][경과차년] = (위험보험료, 예상보험금, 억원 환산 배수)
leaf = defaultdict(dict)
for r in lr:
    if r["구분"] not in LR_GROUPS or r["포트폴리오"] in ("합계", ""):
        continue
    if r["원보험사코드"] not in roster or r["공시분기"] not in QI:
        continue
    yr = r["경과차년"]
    if yr not in LR_SLOTS and yr != LR_PV:
        continue
    lk = (r.get("세그먼트") or "", r["구분"], r.get("상품구분") or "", r["포트폴리오"])
    slot = leaf[(r["원보험사코드"], r["공시분기"])].setdefault(lk, {})
    assert yr not in slot, ("잎 행 키 중복", r["원보험사코드"], r["공시분기"], lk, yr)
    slot[yr] = (r["위험보험료"], r["예상보험금"], UNIT_SCALE[r["단위"]])
UQ = max({q for (_, q) in leaf}, key=qkey)           # 단위 목록을 정하는 최신 공시분기
for (c, q), lks in leaf.items():                    # 금액이 있는 칸의 단위는 한 공시 안에서 하나(금액 없는 '-' 칸은 단위가 달리 찍혀도 무시)
    assert len({sc for ym in lks.values() for rp, ec, sc in ym.values() if rp is not None and ec is not None}) <= 1, (c, q)


def leaf_weight(ym):
    """업권 비중·회사 수 판정용 위험보험료(억원): 경과차년 칸(현재가치 제외)의 양수 합."""
    return sum(rp * sc for y, (rp, ec, sc) in ym.items() if y in LR_SLOTS and rp is not None and rp > 0)


def unit_of(sector, lk):
    """잎 행 -> 단위 식별 튜플(없으면 None). 원수사: (업권, 구분, 상품구분, 포트폴리오). 재보사: (재보, 세그먼트 묶음, Non-Par, 포트폴리오)."""
    seg, g, p, f = lk
    if sector != RE_NAME:
        return (sector, g, p, f)
    sg = re_seg_group(seg, f)
    if g != "Non-Par" or p not in ("", "무배당") or sg is None or (sg, f) not in RE_PAIRS:
        return None
    return (RE_NAME, sg, "Non-Par", f)


roster_sector = {c: UNIT_SECTOR[d["type"]] for c, d in roster.items()}
sector_cos = defaultdict(set)                        # 최신 분기에 잎 행이 있는 회사 (n/N 의 N)
for (c, q), lks in leaf.items():
    if q == UQ:
        sector_cos[roster_sector[c]].add(c)

u_rp = defaultdict(lambda: defaultdict(float))       # 단위 -> 회사 -> 최신 분기 위험보험료 합(억원)
sector_total = defaultdict(float)
co_labels = defaultdict(set)                         # 회사 -> {(구분, 상품구분, 포트폴리오)} (양의 위험보험료, 원수사만; 변액사망 구분 어긋남 확인용)
for (c, q), lks in leaf.items():
    if q != UQ:
        continue
    sec = roster_sector[c]
    for lk, ym in lks.items():
        w = leaf_weight(ym)
        if w <= 0:
            continue
        sector_total[sec] += w
        ukey = unit_of(sec, lk)
        if ukey is not None:
            u_rp[ukey][c] += w
        if sec != RE_NAME:
            co_labels[c].add(lk[1:])
# 재보사: 같은 회사가 상품구분 '' 와 '무배당' 을 같은 단위에 함께 싣지 않았는지(둘을 더하면 이중 계상)
for (c, q), lks in leaf.items():
    if roster_sector[c] == RE_NAME:
        seen = defaultdict(set)
        for lk in lks:
            uk = unit_of(RE_NAME, lk)
            if uk is not None:
                seen[(lk[0], uk)].add(lk[2])
        assert all(len(v) == 1 for v in seen.values()), ("재보사 상품구분 공란·무배당 중복", c, q)

units_sel = []
for ukey, per_co in u_rp.items():
    sec = ukey[0]
    n = sum(1 for w in per_co.values() if w > 0)
    share = sum(per_co.values()) / sector_total[sec] * 100.0
    if (sec == RE_NAME and n >= RE_UNIT_MIN_CO) or (sec != RE_NAME and n >= UNIT_MIN_CO and share >= UNIT_MIN_SHARE_PCT):
        units_sel.append((ukey, n, share))
units_sel.sort(key=lambda t: (list(UNIT_SECTOR.values()).index(t[0][0]), -t[2]))
selected_keys = {t[0] for t in units_sel}


def unit_token(ukey):
    sec, a, b, c3 = ukey
    if sec == RE_NAME:
        return "_".join((TOK_SECTOR[sec], TOK_SEGMENT[a], TOK_GUBUN[b], TOK_PORTFOLIO[c3]))
    return "_".join((TOK_SECTOR[sec], TOK_GUBUN[a], TOK_PRODUCT[b], TOK_PORTFOLIO[c3]))


def unit_label(ukey):
    sec, a, b, c3 = ukey
    return f"{a} {b} {c3}" if sec == RE_NAME else f"{a} {b}{c3}"


UNITS = []
for ukey, n, share in units_sel:
    sec = ukey[0]
    d = {"key": unit_token(ukey), "label": unit_label(ukey), "sector": sec}
    if sec == RE_NAME:
        d.update(gubun=ukey[2], seg=ukey[1], product="", portfolio=ukey[3])
        alt = {}
    else:
        d.update(gubun=ukey[1], product=ukey[2], portfolio=ukey[3])
        # 이 단위가 없는 회사 중 같은 상품구분 x 포트폴리오 이름을 다른 구분으로 공시했고 그 다른 구분 단위도 목록에 없는 회사: 이 단위에서는 빈 칸이 된다.
        have = {c for c, w in u_rp[ukey].items() if w > 0}
        alt = {}
        for c in sector_cos[sec] - have:
            gs = {lab[0] for lab in co_labels[c] if lab[1:] == ukey[2:] and lab[0] != ukey[1] and (sec,) + lab not in selected_keys}
            if gs:
                alt[c] = gs
    d.update(n_companies=n, n_sector=len(sector_cos[sec]), share_pct=round(share, 1), alt_n=len(alt),
             alt_gubun=sorted({g for gs in alt.values() for g in gs}))
    UNITS.append(d)
assert len({d["key"] for d in UNITS}) == len(UNITS), "단위 키 토큰 중복"
UNIT_BY_KEY = {unit_token(t[0]): t[0] for t in units_sel}

# 기본 단위(업권별): 그 업권 회사 전원이 공시한 목록 단위 중 위험보험료 비중이 가장 큰 것. 전원 공시 단위가 없으면 None.
DEFAULT_UNIT = {}
for sec in UNIT_SECTOR.values():
    full = [d for d in UNITS if d["sector"] == sec and d["n_companies"] == d["n_sector"]]
    DEFAULT_UNIT[sec] = max(full, key=lambda d: d["share_pct"])["key"] if full else None
assert DEFAULT_UNIT["생보"] == "life_np_mb_health", DEFAULT_UNIT       # Non-Par 무배당건강 (보고서 7절 기본값)
assert DEFAULT_UNIT["손보"] == "nl_np_mb_injury", DEFAULT_UNIT          # Non-Par 무배당상해


def build_unit_cells(yrs):
    """단위 -> 회사 -> 분기 -> 경과차년 -> [Σ위험보험료(원단위), Σ예상보험금(원단위), Σ위험보험료(억원)] (두 금액이 모두 있는 잎 행만)."""
    acc = defaultdict(lambda: defaultdict(lambda: defaultdict(dict)))
    for (c, q), lks in leaf.items():
        sec = roster_sector[c]
        for lk, ym in lks.items():
            uk = unit_of(sec, lk)
            if uk is None or uk not in selected_keys:
                continue
            for y, (rp, ec, sc) in ym.items():
                if y not in yrs or rp is None or ec is None:
                    continue
                a = acc[uk][c][q].setdefault(y, [0.0, 0.0, 0.0])
                a[0] += rp
                a[1] += ec
                a[2] += rp * sc
    return acc


unit_acc = build_unit_cells(set(LR_SLOTS))
unit_acc_pv = build_unit_cells({LR_PV})
unit_u, unit_up = {}, {}
for t in units_sel:
    uk, tok = t[0], unit_token(t[0])
    ud, upd = {}, {}
    for c in sorted(unit_acc[uk]):
        qd, qpd = {}, {}
        for q in sorted(unit_acc[uk][c], key=qkey):
            row = [None] * len(LR_SLOTS)
            prow = [None] * len(LR_SLOTS)
            for y, (rp, ec, rpe) in unit_acc[uk][c][q].items():
                if rp > 0:
                    k = LR_SLOTS.index(y)
                    row[k] = round(ec / rp * 100.0, 1)
                    v = round(rpe, 2)
                    prow[k] = int(v) if v == int(v) else v
            if any(x is not None for x in row):
                qd[q], qpd[q] = row, prow
        if qd:
            ud[c], upd[c] = qd, qpd
    unit_u[tok], unit_up[tok] = ud, upd


def unit_pool(sec):
    if sec == RE_NAME:
        return [c for c, d in roster.items() if d["type"] == T_RE and SEG_MAP.get(c, {}).get("tag") == "재보험"]
    return [c for c, d in roster.items() if UNIT_SECTOR[d["type"]] == sec and d["median_pool"]]


unit_med = {sec: {} for sec in UNIT_SECTOR.values()}
for d in UNITS:
    tok, sec = d["key"], d["sector"]
    pool = unit_pool(sec)
    byq = {}
    for q in sorted({q for c in pool for q in unit_u[tok].get(c, {})}, key=qkey):
        row = []
        for k in range(len(LR_LABELS)):
            xs = [unit_u[tok][c][q][k] for c in pool if q in unit_u[tok].get(c, {}) and unit_u[tok][c][q][k] is not None]
            row.append(round(statistics.median(xs), 1) if len(xs) >= UNIT_MEDIAN_MIN else None)
        if any(x is not None for x in row):
            byq[q] = row
    if byq:
        unit_med[sec][tok] = byq

# 변액사망 구분 어긋남 문구는 마스터에서 센 수로 쓴다(Direct-Par 변액사망 단위가 목록에 있을 때만).
_va = next((d for d in UNITS if d["gubun"] == "Direct-Par" and d["product"] == "변액" and d["portfolio"] == "사망"), None)
_unit_note_va = (f" Direct-Par 변액사망은 {_va['n_companies']}개 회사가 공시하고, {_va['alt_n']}개 회사는 같은 변액사망을 {', '.join(_va['alt_gubun'])}로 공시해 이 단위에서는 빈 칸입니다."
                 if _va and _va["alt_n"] else "")
UNIT_NOTE = (
    "구분은 공시 각주의 금리 연동 분류입니다. Non-Par는 금융위험 가정 변화가 계약자 지급액에 상당한 영향을 주지 않는 계약 집합(무배당 금리확정형), "
    "Indirect-Par는 영향을 주는 집합(유배당 또는 금리연동형), Direct-Par는 직접참가특성이 있는 집합(변액)이며, 사망·건강 같은 위험 종류가 아닙니다. "
    "비교 단위는 공시 표의 한 줄(구분 × 상품구분 × 포트폴리오)이고, 같은 단위끼리만 비교합니다. "
    f"원수보험사 목록에는 최신 결산에서 {UNIT_MIN_CO}개 회사 이상이 공시하고 같은 업권(생보·손보) 위험보험료의 {UNIT_MIN_SHARE_PCT:g}% 이상인 단위만 둡니다. "
    f"재보험사는 세그먼트(생명·장기손해)와 포트폴리오로 나누고 {RE_UNIT_MIN_CO}개 회사 이상이 공시한 Non-Par 단위만 두며, 원수보험사와 섞어 비교하지 않습니다."
    + _unit_note_va
)

# ---------------------------------------------------------------- metrics config
NA = {
    "csm_closing": {"KR0051": "PAA 전용이라 CSM 없음", "KR0150": "보증보험이라 CSM 없음", "KR0004": "CSM 공시 거의 없음"},
    "nb_multiple": {"KR0051": "PAA 전용이라 CSM 없음", "KR0150": "보증보험이라 CSM 없음", "KR0004": "CSM 공시 거의 없음"},
    "roe": {"KR0004": "자본잠식(자본 0 이하)", "KR0050": "자본 미공시 구간"},
    **{f"persist{n}": {"KR1000": "재보험사라 판매채널표 없음", "KR0150": "장기손해보험 없음"} for n in (13, 25, 37, 61)},
    "loss_pv": {"KR1011": "연금보험 단종사로 위험보험료 미산출", "KR0150": "장기손해보험 없음"},
}

CSM_NOTE = "분기 공시사 23곳은 매 분기, 연 1회 공시사는 결산(4Q)만 있습니다."
METRICS = [
    dict(id="kics_ratio", group="건전성 · K-ICS", label="지급여력비율", unit="%", kind="pct", dec=1,
         period="분기", connect=False, median=True, clip=True, basis=True,
         ref=[dict(y=130, label="권고 130%")],
         defn="지급여력금액 ÷ 지급여력기준금액 × 100",
         note="경과조치 적용 후/전 토글을 따릅니다. 분기말 기준이며, 값이 극단적으로 큰 소규모사는 막대가 범위를 넘으면 끝을 잘라 표시하고 실제 값은 막대 옆 숫자로 보입니다.",
         v=kics_series(27, "post"), v_pre=kics_series(27, "pre")),
    dict(id="kics_basic", group="건전성 · K-ICS", label="기본자본비율", unit="%", kind="pct", dec=1,
         period="분기", connect=False, median=True, clip=True, basis=True,
         ref=[dict(y=50, label="기준 50%")],
         defn="기본자본 ÷ 지급여력기준금액 × 100",
         note="공시 원문 값이 아니라 기본자본과 지급여력기준금액으로 산출한 값입니다.",
         v=kics_series(28, "post"), v_pre=kics_series(28, "pre")),
    dict(id="csm_closing", group="IFRS17 · 손익", label="기말 CSM", unit="억원", kind="eok", dec=0,
         period="분기·결산", connect=True, median=False, clip=False,
         defn="계약서비스마진 기말 잔액",
         note=CSM_NOTE + " 연 1회 공시사는 최신 값이 직전 결산이라 분기 칩이 붙습니다.",
         v=csm_closing),
    dict(id="nb_multiple", group="IFRS17 · 손익", label="신계약 CSM 배수", unit="배", kind="x", dec=1,
         period="분기·결산", connect=True, median=True, clip=True,
         defn="신계약 CSM ÷ 월납환산 초회보험료, 연 누계",
         note="연 누계라 1Q에서 4Q로 갈수록 해당 연도 누적분이 쌓인 값입니다. 재보험·보증은 구조상 산출하지 않습니다.",
         v=nb_mult),
    dict(id="ins_profit", group="IFRS17 · 손익", label="보험손익 · 연 누계", unit="억원", kind="eok", dec=0,
         period="분기", connect=True, median=False, clip=False, ytd=True,
         defn="보험서비스 결과, 별도 기준 연 누계(YTD)",
         note="그 해 1분기부터 해당 분기까지 쌓은 연 누계(YTD)입니다. 1Q는 1분기, 2Q는 상반기(1~2Q), 3Q는 1~3Q, 4Q는 연간 값이라 분기가 갈수록 커지며, 당분기만의 값이 아닙니다. 연 1회 공시사의 1~3Q는 경영공시 요약값이라 억원 단위로 반올림돼 있습니다.",
         v=ins_profit),
    dict(id="net_income", group="IFRS17 · 손익", label="당기순이익 · 연 누계", unit="억원", kind="eok", dec=0,
         period="분기", connect=True, median=False, clip=False, ytd=True,
         defn="별도 기준 연 누계(YTD)",
         note="그 해 1분기부터 해당 분기까지 쌓은 연 누계(YTD)입니다. 1Q는 1분기, 2Q는 상반기(1~2Q), 3Q는 1~3Q, 4Q는 연간 값이라 분기가 갈수록 커지며, 당분기만의 값이 아닙니다.",
         v=net_income),
    dict(id="roe", group="IFRS17 · 손익", label="ROE (연환산)", unit="%", kind="pct", dec=1,
         period="분기", connect=True, median=True, clip=True,
         defn="당기순이익 연 누계 연환산 ÷ 평균자본(직전 결산말·당분기말)",
         note="입력은 당기순이익 연 누계(YTD)이고, 1Q는 4배·2Q는 2배·3Q는 4/3배·4Q는 1배로 연환산합니다. 공시 ROE와 같은 정의로 계산했고 2024.1Q부터 가능합니다. 자본이 0 이하인 구간은 산출하지 않습니다. 분기마다 연환산 배수가 달라 계절성이 있습니다.",
         v=roe),
    dict(id="surrender_reserve", group="IFRS17 · 손익", label="해약환급금준비금", unit="억원", kind="eok", dec=0,
         period="분기", median=False, clip=False,
         defn="해약환급금준비금 적립 잔액(분기말, 별도 기준)",
         note="적립액 잔액입니다(그 분기에 새로 쌓은 금액이 아님). 생명보험 중심 항목이고 공시하지 않는 회사는 n/a 입니다. 금액이라 회사 규모에 비례합니다.",
         v=surrender_eok),
    *[dict(id=f"persist{n}", group="유지율 · 손해율", label=f"{n}회차 유지율", unit="%", kind="pct", dec=1,
           period="반기", connect=True, median=True, clip=False,
           chart_group="persist", chart_label="유지율 (회차별)", sub=f"{n}회차",
           defn="전 채널 합산 유지계약액 ÷ 대상신계약액",
           note="13·25·37·61회차 유지율을 한 차트에 모았습니다. 반기(2Q·4Q) 공시라 1Q·3Q 값은 없고, 신계약이 오래되지 않은 회사는 뒤쪽 회차가 비어 있습니다. 생보와 손보는 채널 구성이 달라 수준 차이가 있어 같은 유형끼리 비교하세요.",
           v=persist[n]) for n in PERSIST_N],
    dict(id="loss_pv", group="유지율 · 손해율", label="손해율 (현재가치)", unit="%", kind="pct", dec=1,
         period="연 1회", connect=True, median=True, clip=True,
         defn="합계 포트폴리오의 예상보험금 ÷ 위험보험료, 미래 가정치",
         note="결산 시점의 미래 손해율 가정이지 실적이 아닙니다. 값은 2023.4Q·2024.4Q·2025.4Q 최대 3개 시점이고 2023.4Q는 10곳뿐입니다. 위험보험료가 작은 소규모사는 값이 흔들립니다.",
         v=loss_pv),
    # ---- 추가 지표: 화면 기본 목록에는 없고(default=False) 사용자가 '지표 편집'에서 끌어다 넣는다. 전부 금액이라 중앙값 없음.
    dict(id="kics_avail", group="건전성 · K-ICS", label="지급여력금액", unit="억원", kind="eok", dec=0,
         period="분기", median=False, clip=False, basis=True, default=False,
         defn="가용자본: 건전성감독기준 순자산에서 불인정 항목을 빼고 재분류 항목을 더한 지급여력금액",
         note="경과조치 적용 후/전 토글을 따릅니다. 금액이라 회사 규모에 비례합니다.",
         v=kics_series(1, "post"), v_pre=kics_series(1, "pre")),
    dict(id="kics_scr", group="건전성 · K-ICS", label="지급여력기준금액", unit="억원", kind="eok", dec=0,
         period="분기", median=False, clip=False, basis=True, default=False,
         defn="요구자본: 지급여력비율의 분모",
         note="경과조치 적용 후/전 토글을 따릅니다. 금액이라 회사 규모에 비례합니다.",
         v=kics_series(14, "post"), v_pre=kics_series(14, "pre")),
    dict(id="nb_csm", group="IFRS17 · 손익", label="신계약 CSM", unit="억원", kind="eok", dec=0,
         period="분기·결산", median=False, clip=False, default=False,
         defn="해당 연도 누적 신계약 CSM",
         note="연 누계라 1Q에서 4Q로 갈수록 해당 연도 누적분이 쌓인 값입니다. 재보험·보증은 구조상 산출하지 않습니다.",
         v=nb_amt),
    dict(id="inv_profit", group="IFRS17 · 손익", label="투자손익 · 연 누계", unit="억원", kind="eok", dec=0,
         period="분기", median=False, clip=False, default=False, ytd=True,
         defn="투자이익에서 보험금융비용을 뺀 값, 별도 기준 연 누계(YTD)",
         note="그 해 1분기부터 해당 분기까지 쌓은 연 누계(YTD)입니다. 1Q는 1분기, 2Q는 상반기(1~2Q), 3Q는 1~3Q, 4Q는 연간 값이라 분기가 갈수록 커지며, 당분기만의 값이 아닙니다.",
         v=inv_profit),
    dict(id="equity", group="IFRS17 · 손익", label="자본총계", unit="억원", kind="eok", dec=0,
         period="분기", median=False, clip=False, default=False,
         defn="IFRS17 재무상태표 자본총계, 분기말 별도 기준",
         note="금액이라 회사 규모에 비례합니다.",
         v=equity_eok),
    dict(id="assets", group="IFRS17 · 손익", label="자산총계", unit="억원", kind="eok", dec=0,
         period="분기", median=False, clip=False, default=False,
         defn="IFRS17 재무상태표 자산총계, 분기말 별도 기준",
         note="금액이라 회사 규모에 비례합니다.",
         v=assets_eok),
]


def finalize_vals(mdef, key):
    src = mdef[key]
    out = {}
    for c in roster:
        arr = src[c] if c in src else [None] * NQ
        out[c] = [None if x is None else round(x, mdef["dec"] if mdef["kind"] != "eok" else 0) for x in arr]
        if mdef["kind"] == "eok":
            out[c] = [None if x is None else int(x) for x in out[c]]
    return out


def medians(vals):
    res = {}
    cnt = {}
    for t in TYPES:
        pool = [c for c, d in roster.items() if d["type"] == t and d["median_pool"]]
        row, nrow = [], []
        for i in range(NQ):
            xs = [vals[c][i] for c in pool if vals[c][i] is not None]
            nrow.append(len(xs))
            row.append(round(statistics.median(xs), 1) if len(xs) >= 5 else None)
        res[t] = row
        cnt[t] = nrow
    return res, cnt


for m in METRICS:
    m["v"] = finalize_vals(m, "v")
    if m.get("basis"):
        m["v_pre"] = finalize_vals(m, "v_pre")
    if m["median"]:
        m["med"], m["med_n"] = medians(m["v"])
        if m.get("basis"):
            m["med_pre"], m["med_n_pre"] = medians(m["v_pre"])
    m["na"] = NA.get(m["id"], {})
    for c in list(m["na"]):
        if any(x is not None for x in m["v"][c]):
            del m["na"][c]
    if m["id"] == "loss_pv":      # 구분별 현재가치 시계열과 업계 중앙값(추가 필드, 위의 v·med 는 그대로)
        m["vg"], m["medg"] = {}, {}
        for g in LR_GROUPS_SHOWN:
            full = {c: [None if x is None else round(x, m["dec"]) for x in (loss_pv_g[g][c] if c in loss_pv_g[g] else [None] * NQ)]
                    for c in roster}
            m["vg"][g] = {c: full[c] for c in sorted(full) if any(x is not None for x in full[c])}
            mg, _ = medians(full)
            m["medg"][g] = {t: row for t, row in mg.items() if any(x is not None for x in row)}
        # 비교 단위별 현재가치(위 vg·medg 와 같은 모양, 구분 대신 단위 키): vu[단위키][회사] = 분기별 배열, medu[단위키][업권] = 분기별 중앙값
        m["vu"], m["medu"] = {}, {}
        for d in UNITS:
            uk, tok, sec = UNIT_BY_KEY[d["key"]], d["key"], d["sector"]
            full = {}
            for c in sorted(unit_acc_pv[uk]):
                arr = [None] * NQ
                for q, ym in unit_acc_pv[uk][c].items():
                    rp, ec, _ = ym[LR_PV]
                    if rp > 0:
                        arr[QI[q]] = round(ec / rp * 100.0, m["dec"])
                if any(x is not None for x in arr):
                    full[c] = arr
            m["vu"][tok] = full
            pool = unit_pool(sec)
            row = []
            for i in range(NQ):
                xs = [full[c][i] for c in pool if c in full and full[c][i] is not None]
                row.append(round(statistics.median(xs), 1) if len(xs) >= UNIT_MEDIAN_MIN else None)
            if any(x is not None for x in row):
                m["medu"][tok] = {sec: row}

# 화면이 쓰지 않는 필드는 싣지 않는다(파일 크기·오해 방지).
COMPANY_KEYS = ("code", "name", "type", "short", "sector")
METRIC_DROP = ("connect", "med_n", "med_n_pre")
for m in METRICS:
    for k in METRIC_DROP:
        m.pop(k, None)

out = {
    "meta": {
        "quarters": QUARTERS,
        "latest": LAST_Q,
        "median_rule": "같은 생/손보 유형, 재보험·보증 구분(data/company_segment.json) 회사는 모집단에서 제외하고 중앙값도 내지 않음, 그 분기에 값이 있는 회사만(결측은 건너뜀), 5곳 미만이면 없음",
        "sources": ["kics_disclosure.json", "CSM_waterfall.json", "NB_CSM_multiple.json", "PL_breakdown.json",
                    "IFRS17_BS.json", "data/persistency/master_persistency.json", "data/loss_ratio/master_loss_ratio.json"],
    },
    "companies": [{k: d[k] for k in COMPANY_KEYS}
                  for d in sorted(roster.values(), key=lambda d: (TYPES.index(d["type"]), d["size_rank"] or 99))],
    "metrics": METRICS,
    "loss_curve": {
        "label": "손해율 가정 (경과차년별)", "unit": "%",
        "defn": "합계 포트폴리오의 예상보험금 ÷ 위험보험료, 경과차년별 미래 가정치",
        "note": "결산 시점의 미래 손해율 가정이지 실적이 아닙니다. 선 하나는 그 회사의 가장 최근 결산 공시이고, 현재가치 기준 손해율은 선에 넣지 않고 숫자로 적었습니다. 위험보험료가 작은 소규모사는 값이 흔들립니다.",
        "labels": LR_SLOTS, "n_std": len(LR_LABELS),
        "v": {c: dict(sorted(loss_curve_v[c].items(), key=lambda kv: qkey(kv[0]))) for c in sorted(loss_curve_v)},
        "med": loss_curve_med,
        "g_order": LR_GROUPS_SHOWN,
        "note_g": ("구분을 고르면 그 계약 유형(Non-Par, Direct-Par, Indirect-Par)만 모아 계산합니다. 합계 곡선은 경과차년이 길어질수록 계약 유형 구성이 달라져"
                   "(칸마다 세 유형의 비중이 다름) 유형 자체의 손해율이 같아도 곡선이 꺾일 수 있습니다. 같은 유형끼리 비교하려면 구분을 고르세요. "
                   "다만 구분을 골라도 그 유형 자체의 공시값이 경과차년에 따라 크게 달라지면(위험보험료가 작은 칸 등) 곡선은 그대로 꺾입니다. "
                   "구분 값은 그 구분의 모든 포트폴리오 예상보험금 합 ÷ 위험보험료 합이라 공시 합계 행과 소수 첫째 자리에서 어긋날 수 있고, 위험보험료가 작은 칸은 크게 흔들립니다. "
                   "공시 기준과 구성은 해마다 다를 수 있습니다."),
        "g": {g: {c: dict(sorted(loss_curve_g[g][c].items(), key=lambda kv: qkey(kv[0]))) for c in sorted(loss_curve_g[g])} for g in LR_GROUPS_SHOWN},
        "med_g": loss_curve_med_g,
        "unit_rule": {"quarter": UQ, "min_companies": UNIT_MIN_CO, "min_share_pct": UNIT_MIN_SHARE_PCT,
                      "re_min_companies": RE_UNIT_MIN_CO, "median_min": UNIT_MEDIAN_MIN, "fade_below_eok": UNIT_FADE_EOK},
        "units": UNITS,
        "default_unit": DEFAULT_UNIT,
        "u": unit_u,
        "up": unit_up,
        "med_u": unit_med,
        "unit_note": UNIT_NOTE,
    },
}
payload = json.dumps(out, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def main() -> int:
    if len(payload) > MAX_BYTES:
        print(f"{OUT.name}: {len(payload):,} bytes exceeds the {MAX_BYTES:,} byte budget")
        return 1
    if "--check" in sys.argv[1:]:
        disk = OUT.read_bytes() if OUT.exists() else None
        if disk != payload:
            print(f"DIFF {OUT.relative_to(ROOT)}: rebuilt {len(payload):,} bytes vs disk "
                  f"{'missing' if disk is None else format(len(disk), ',') + ' bytes'}")
            return 1
        print(f"OK   {OUT.relative_to(ROOT)}: {len(payload):,} bytes, identical to a rebuild from the masters")
        return 0
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_bytes(payload)
    print("wrote", OUT, len(payload), "bytes;", len(roster), "companies;", len(METRICS), "metrics;", NQ, "quarters")
    print(f"  loss_curve: {len(loss_curve_v)} companies, quarters {sorted({q for c in loss_curve_v for q in loss_curve_v[c]}, key=qkey)}")
    for m in METRICS:
        li = NQ - 1
        n_last = sum(1 for c in roster if m["v"][c][li] is not None)
        n_any = sum(1 for c in roster if any(x is not None for x in m["v"][c]))
        print(f"  {m['id']:12s} last-quarter n={n_last:2d}  any-data n={n_any:2d}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
