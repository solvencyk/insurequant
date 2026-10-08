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
- 보험손익/당기순이익(당분기, 억원): PL_breakdown.json 항목 1/24, 값_당분기, 비면 누계 차분(백만원 -> 억원 /100)
- ROE(연환산): 당기순이익 누계(항목 24) x 4/q / 평균(직전 4Q 자본, 당분기말 자본)(IFRS17_BS 항목 3), 두 자본 > 0 일 때만, 2024.1Q 부터
- 유지율 13/25/37/61회차: master_persistency.json 회차별 채널행 합산 Σ유지/Σ대상 (원문오기 SWAPPED=맞교환, INCONSISTENT=제외). 화면에서는 한 차트에 모아 비교
- 손해율: master_loss_ratio.json 합계/합계/현재가치 Σ예상보험금/Σ위험보험료 (세그먼트 합산)

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

roster = {}
for r in kics:
    c = r["원보험사코드"]
    roster[c] = {"code": c, "name": r["원수사명"], "type": "생보" if r["생손보여부"] == "생명보험" else "손보"}
for c, d in roster.items():
    d["short"] = short_name(d["name"])
    d["sector"] = {"KR1000": "재보험", "KR0150": "보증"}.get(c, "")

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
for t in ("생보", "손보"):
    ordered = sorted((d for d in roster.values() if d["type"] == t and d["scr"] is not None), key=lambda d: -d["scr"])
    for i, d in enumerate(ordered):
        d["size_rank"] = i + 1
for d in roster.values():
    d.setdefault("size_rank", None)
    base = (d["size_rank"] or 0) - 1
    d["color_idx"] = (base + (2 if d["type"] == "손보" else 0)) % 4
    d["peer_ok"] = d["code"] not in ("KR0150", "KR1000", "KR0004", "KR1098", "KR0051")
    d["median_pool"] = d["code"] not in ("KR1000", "KR0150")

# ---------------------------------------------------------------- IFRS17 masters
csm = load("CSM_waterfall.json")
csm_closing = defaultdict(lambda: [None] * NQ)
for r in csm:
    if r["항목번호"] == 6 and r["원보험사코드"] in roster and r["공시분기"] in QI:
        csm_closing[r["원보험사코드"]][QI[r["공시분기"]]] = num(r["값"])

nb = load("NB_CSM_multiple.json")
nb_mult = defaultdict(lambda: [None] * NQ)
for r in nb:
    if r["원보험사코드"] in roster and r["공시분기"] in QI:
        nb_mult[r["원보험사코드"]][QI[r["공시분기"]]] = num(r["신계약CSM배수_연누계"])

pl = load("PL_breakdown.json")
ytd = {}
qgiven = {}
for r in pl:
    if r["원보험사코드"] not in roster or r["공시분기"] not in QI:
        continue
    it = int(r["항목번호"]) if str(r["항목번호"]).isdigit() else None
    if it in (1, 24):
        ytd[(it, r["원보험사코드"], r["공시분기"])] = num(r["값"])
        qgiven[(it, r["원보험사코드"], r["공시분기"])] = num(r.get("값_당분기"))


def quarterly_eok(item):
    out = {}
    mism = 0
    cmp_n = 0
    for c in roster:
        arr = [None] * NQ
        for q in QUARTERS:
            y, n = qkey(q)
            given = qgiven.get((item, c, q))
            cur = ytd.get((item, c, q))
            derived = None
            if cur is not None:
                if n == 1:
                    derived = cur
                else:
                    prev = ytd.get((item, c, f"{y}.{n-1}Q"))
                    if prev is not None:
                        derived = cur - prev
            if given is not None and derived is not None:
                cmp_n += 1
                if abs(given - derived) > 1.5:
                    mism += 1
            v = given if given is not None else derived
            arr[QI[q]] = None if v is None else v / 100.0
        out[c] = arr
    print(f"  PL item {item}: given-vs-derived compared {cmp_n}, mismatch(>1.5백만) {mism}")
    return out


ins_profit = quarterly_eok(1)
net_income = quarterly_eok(24)

bs = load("IFRS17_BS.json")
equity = {}
for r in bs:
    if r["항목번호"] == 3 and r["원보험사코드"] in roster and r["공시분기"] in QI:
        equity[(r["원보험사코드"], r["공시분기"])] = num(r["값"])

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
    dict(id="ins_profit", group="IFRS17 · 손익", label="보험손익", unit="억원", kind="eok", dec=0,
         period="분기", connect=True, median=False, clip=False,
         defn="보험서비스 결과, 별도 기준 당분기",
         note="당분기 값이 없는 결산 분기는 연 누계에서 3Q 누계를 뺀 값입니다. 연 1회 공시사의 1~3Q는 경영공시 요약값이라 억원 단위로 반올림돼 있습니다.",
         v=ins_profit),
    dict(id="net_income", group="IFRS17 · 손익", label="당기순이익", unit="억원", kind="eok", dec=0,
         period="분기", connect=True, median=False, clip=False,
         defn="별도 기준 당분기",
         note="당분기 값이 없는 결산 분기는 연 누계에서 3Q 누계를 뺀 값입니다.",
         v=net_income),
    dict(id="roe", group="IFRS17 · 손익", label="ROE (연환산)", unit="%", kind="pct", dec=1,
         period="분기", connect=True, median=True, clip=True,
         defn="당기순이익 누계 연환산 ÷ 평균자본(직전 결산말·당분기말)",
         note="공시 ROE와 같은 정의로 계산했고 2024.1Q부터 가능합니다. 자본이 0 이하인 구간은 산출하지 않습니다. 1Q는 4배, 2Q는 2배로 연환산해 계절성이 있습니다.",
         v=roe),
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
    for t in ("생보", "손보"):
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
        "default_from": "KR0009",
        "median_rule": "같은 생/손보 유형, 재보험(KR1000)·보증(KR0150) 제외, 그 분기에 값이 있는 회사만(결측은 건너뜀), 5곳 미만이면 없음",
        "sources": ["kics_disclosure.json", "CSM_waterfall.json", "NB_CSM_multiple.json", "PL_breakdown.json",
                    "IFRS17_BS.json", "data/persistency/master_persistency.json", "data/loss_ratio/master_loss_ratio.json"],
    },
    "companies": [{k: d[k] for k in COMPANY_KEYS}
                  for d in sorted(roster.values(), key=lambda d: (d["type"] != "생보", d["size_rank"] or 99))],
    "metrics": METRICS,
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
    for m in METRICS:
        li = NQ - 1
        n_last = sum(1 for c in roster if m["v"][c][li] is not None)
        n_any = sum(1 for c in roster if any(x is not None for x in m["v"][c]))
        print(f"  {m['id']:12s} last-quarter n={n_last:2d}  any-data n={n_any:2d}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
