"""Build the two IFRS17.html panel JSONs for sections 8 (loss-ratio assumptions) and
9 (persistency by sales channel).

Reads (READ ONLY, never written):
    data/loss_ratio/master_loss_ratio.json   -> data/loss_ratio/panel_loss_ratio.json
    data/persistency/master_persistency.json -> data/persistency/panel_persistency.json

Both outputs are company -> disclosure-quarter nested with array-compressed rows, only the
columns the screen draws, so each stays well under 1.5MB. IFRS17.html fetches them; nothing
is inlined into the HTML.

Run:    C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/viz_build_persistency_lossratio_panels.py
Check:  ... viz_build_persistency_lossratio_panels.py --check
        rebuilds both panels in memory from the masters and compares the bytes with the files on disk
        (what the screen fetches) + the 1.5MB budget; exit 1 on any difference. Writes nothing.
"""

from __future__ import annotations

import hashlib
import json
import sys
from collections import OrderedDict, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LR_SRC = ROOT / "data" / "loss_ratio" / "master_loss_ratio.json"
PS_SRC = ROOT / "data" / "persistency" / "master_persistency.json"
LR_OUT = ROOT / "data" / "loss_ratio" / "panel_loss_ratio.json"
PS_OUT = ROOT / "data" / "persistency" / "panel_persistency.json"
MAX_BYTES = int(1.5 * 1024 * 1024)

# ---- loss ratio ---------------------------------------------------------------------------
# Canonical elapsed-year column order (current value is last, drawn as a single number).
YEARS = ["1년", "2년", "3년", "4년", "5년", "6년", "7년", "8년", "9년", "10년",
         "11~15년", "16~20년", "21~25년", "26~30년", "30년 이후", "현재가치"]
# KR0079 prints "1~10년" as one merged column; it sorts before 11~15년.
YEAR_RANK = {y: i for i, y in enumerate(YEARS)}
YEAR_RANK["1~10년"] = -1

# ---- persistency --------------------------------------------------------------------------
ROUNDS = [13, 25, 37, 61]
BUNDLES = ["전속설계사", "GA(대리점)", "방카슈랑스", "비대면", "기타"]
BUNDLE_OF = {
    ("설계사", ""): "전속설계사",
    ("개인대리점", ""): "GA(대리점)",
    ("법인대리점", "기타"): "GA(대리점)",
    ("법인대리점", "금융기관보험대리점"): "방카슈랑스",
    ("법인대리점", "TM"): "비대면",
    ("법인대리점", "홈쇼핑"): "비대면",
    ("직영", "다이렉트"): "비대면",
    ("직영", "임직원"): "기타",
    ("직영", "복합"): "기타",
    ("중개사", ""): "기타",
    ("기타", ""): "기타",
}


def _load(path: Path):
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def _sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()[:12]


def _num(v):
    return v if isinstance(v, (int, float)) and v == v else None


CHECK = False        # --check: compare instead of write
CHECK_FAILS: list[str] = []


def _write(path: Path, obj) -> int:
    text = json.dumps(obj, ensure_ascii=False, separators=(",", ":"))
    data = text.encode("utf-8")
    if len(data) > MAX_BYTES:
        raise SystemExit(f"{path.name}: {len(data):,} bytes exceeds the {MAX_BYTES:,} byte budget")
    if CHECK:
        on_disk = path.read_bytes() if path.exists() else None
        if on_disk != data:
            CHECK_FAILS.append(f"{path.relative_to(ROOT).as_posix()}: on-disk bytes differ from a fresh build of the master "
                               f"(disk={None if on_disk is None else len(on_disk)}, rebuilt={len(data)})")
        return len(data)
    with path.open("wb") as f:     # bytes -> no BOM, no CRLF translation
        f.write(data)
    return len(data)


# Tree order for the 구분 level (anything unknown goes after, in source order) and the 상품구분 level.
GROUP_ORDER = ["Non-Par", "Direct-Par", "Indirect-Par"]
PRODUCT_ORDER = ["유배당", "무배당", "변액"]


def _rank(order, v):
    return order.index(v) if v in order else len(order)


def _agg(leaves, years):
    """Group loss ratio per year column = sum(예상보험금) / sum(위험보험료) x 100 over the leaves
    that have BOTH amounts (never an average of ratios). Risk premium sum 0 / no leaf -> None."""
    out = []
    for yr in years:
        sa = sb = 0.0
        used = 0
        for cell in leaves:
            c = cell.get(yr)
            if c is None:
                continue
            _, a, b = c
            if a is None or b is None:
                continue
            sa += a
            sb += b
            used += 1
        out.append(round(sa / sb * 100, 2) if used and sb > 0 else None)
    return out


def build_loss_ratio() -> dict:
    rows = _load(LR_SRC)
    comp: dict[str, dict] = {}
    # (code, quarter, segment) -> OrderedDict[(구분, 상품, 포트)] -> {year: (ratio, 예상보험금, 위험보험료)}
    cells: dict = defaultdict(lambda: OrderedDict())
    names: dict[str, str] = {}
    cols_seen: dict = defaultdict(set)
    recon_bad = 0
    for r in rows:
        code, q, seg = r["원보험사코드"], r["공시분기"], r.get("세그먼트") or ""
        yr = r["경과차년"]
        names[code] = r["원수사명"]
        key = (r["구분"], r.get("상품구분") or "", r["포트폴리오"])
        v = _num(r["손해율"])
        a, b = _num(r.get("예상보험금")), _num(r.get("위험보험료"))
        cells[(code, q, seg)].setdefault(key, {})[yr] = (None if v is None else round(v, 2), a, b)
        cols_seen[(code, q, seg)].add(yr)
        if v is not None and a is not None and b:
            if abs(a / b * 100 - v) > 0.6 + abs(v) * 0.005:
                recon_bad += 1

    quarters = sorted({k[1] for k in cells})
    no_total = []
    rows_in = rows_out = dropped_empty = group_rows = 0
    for (code, q, seg), groups in sorted(cells.items()):
        cols = sorted(cols_seen[(code, q, seg)], key=lambda y: YEAR_RANK.get(y, 99))
        std = cols == YEARS
        tot_key = ("합계", "", "합계")
        if tot_key not in groups:
            no_total.append((code, q, seg))
        body = []
        if tot_key in groups:
            body.append(["합계", "", "합계", [(groups[tot_key].get(y) or (None,))[0] for y in cols]])
        # leaves: drop rows that are '-' in every column for this company+quarter+segment
        leaves = []
        for (g, p, f), vals in groups.items():
            if g == "합계":
                continue
            rows_in += 1
            if all((vals.get(y) or (None,))[0] is None for y in cols):
                dropped_empty += 1
                continue
            leaves.append((g, p, f, vals))
        # tree: 구분 -> (상품구분 -> 포트폴리오 | 포트폴리오 directly)
        tree: dict = OrderedDict()
        for g, p, f, vals in leaves:
            tree.setdefault(g, OrderedDict()).setdefault(p, []).append((f, vals))
        for g in sorted(tree, key=lambda x: _rank(GROUP_ORDER, x)):
            prods = tree[g]
            all_leaf = [vals for pl in prods.values() for _, vals in pl]
            body.append([g, "", "", _agg(all_leaf, cols)])
            group_rows += 1
            for p in sorted((x for x in prods if x), key=lambda x: _rank(PRODUCT_ORDER, x)):
                body.append([g, p, "", _agg([vals for _, vals in prods[p]], cols)])
                group_rows += 1
                for f, vals in prods[p]:
                    body.append([g, p, f, [(vals.get(y) or (None,))[0] for y in cols]])
            for f, vals in prods.get("", []):
                body.append([g, "", f, [(vals.get(y) or (None,))[0] for y in cols]])
        rows_out += len(body)
        c = comp.setdefault(code, {"n": names[code], "q": {}})
        qd = c["q"].setdefault(q, {"s": {}})
        if not std:
            qd.setdefault("c", {})[seg] = cols
        qd["s"][seg] = body

    for c in comp.values():          # non-standard cols stored per segment only when needed
        for qd in c["q"].values():
            if "c" in qd and len(set(map(tuple, qd["c"].values()))) == 1 and len(qd["c"]) == len(qd["s"]):
                qd["c"] = list(next(iter(qd["c"].values())))
    out = {
        "meta": {
            "source": "master_loss_ratio.json",
            "source_rows": len(rows),
            "source_sha12": _sha(LR_SRC),
            "years": YEARS,
            "quarters": quarters,
            "note": ("q[분기]: s={세그먼트:[[구분,상품구분,포트폴리오,[손해율%...]]]}, c=열 라벨(표준 16칸이 아닐 때만, 아니면 meta.years). "
                     "행 종류: 합계=[합계,'',합계] / 구분 소계=[구분,'',''] / 상품구분 소계=[구분,상품,''] / 잎=포트폴리오 있음. "
                     "소계 손해율=Σ예상보험금÷Σ위험보험료×100(빌더 계산, 마스터에는 소계 행 없음). 전 칸 '-' 인 행은 뺌."),
        },
        "companies": comp,
    }
    size = _write(LR_OUT, out)
    print(f"[loss_ratio] companies={len(comp)} quarters={quarters} bytes={size:,}")
    print(f"[loss_ratio] non-standard column sets: "
          f"{sum(1 for c in comp.values() for qd in c['q'].values() if 'c' in qd)} (company,quarter)")
    print(f"[loss_ratio] (company,quarter,segment) without a total row: {len(no_total)} {no_total[:8]}")
    print(f"[loss_ratio] leaf rows {rows_in} -> all-dash rows dropped {dropped_empty}; "
          f"group (구분/상품구분) rows computed {group_rows}; rows shipped {rows_out}")
    print(f"[loss_ratio] ratio vs expected/risk-premium recon outside tolerance: {recon_bad} cells (info)")
    return out


def _row_rate(n, m, printed):
    """One channel row's displayed retention rate. None = show '-'."""
    if n is not None and n == 0:
        return None
    if printed is not None:
        if n is None and printed == 0:       # rate-only zero cannot be told from a dash
            return None
        return printed
    if n and m is not None:
        return m / n * 100
    return None


def build_persistency() -> dict:
    rows = _load(PS_SRC)
    by = defaultdict(lambda: defaultdict(OrderedDict))   # code -> quarter -> (대,소) -> {round: (n,m,rate)}
    units: dict = {}
    names: dict = {}
    unmapped = defaultdict(int)
    for r in rows:
        code, q = r["원보험사코드"], r["공시분기"]
        names[code] = r["원수사명"]
        units.setdefault((code, q), r.get("단위") or "")
        rnd = int(str(r["회차구분"]).replace("회차", ""))
        ch = (r["채널대분류"], r.get("채널소분류") or "")
        if ch not in BUNDLE_OF:
            unmapped[ch] += 1
        by[code][q].setdefault(ch, {})[rnd] = (_num(r["대상신계약액"]), _num(r["유지계약액"]), _num(r["유지율"]))
    if unmapped:
        print(f"[persistency] WARNING channel combos outside the bundle map -> 기타: {dict(unmapped)}")

    quarters = sorted({q for c in by.values() for q in c})
    comp = {}
    rate_only_dropped = 0
    amt_missing_excluded = 0
    for code in sorted(by):
        qd = {}
        for q in sorted(by[code]):
            chans = by[code][q]
            bundle_members = defaultdict(list)
            for ch in chans:
                bundle_members[BUNDLE_OF.get(ch, "기타")].append(ch)
            rowsout = []
            groups = {}
            for b in BUNDLES:
                mem = bundle_members.get(b, [])
                if not mem:
                    continue
                brate, bn, bm = [], [], []
                for rnd in ROUNDS:
                    sn = sm = 0.0
                    used = 0
                    rate_only = []
                    for ch in mem:
                        cell = chans[ch].get(rnd)
                        if cell is None:
                            continue
                        n, m, pr = cell
                        if n is not None and m is not None:
                            sn += n
                            sm += m
                            used += 1
                        elif n is None and m is None and pr is not None:
                            rate_only.append(pr)
                        elif n is not None and n > 0:
                            amt_missing_excluded += 1
                    if used:
                        brate.append(None if sn == 0 else round(sm / sn * 100, 2))
                        bn.append(sn)
                        bm.append(sm)
                        rate_only_dropped += len(rate_only)
                    elif len(rate_only) == 1 and len([c for c in mem if chans[c].get(rnd) is not None]) == 1 \
                            and rate_only[0] != 0:
                        brate.append(round(rate_only[0], 2))
                        bn.append(None)
                        bm.append(None)
                    else:
                        brate.append(None)
                        bn.append(None)
                        bm.append(None)
                groups[b] = brate
                rowsout.append([b, "", 1, brate, bn, bm])      # kind 1 = bundle subtotal
                for ch in mem:
                    rr, nn, mm = [], [], []
                    for rnd in ROUNDS:
                        cell = chans[ch].get(rnd)
                        if cell is None:
                            rr.append(None)
                            nn.append(None)
                            mm.append(None)
                            continue
                        n, m, pr = cell
                        v = _row_rate(n, m, pr)
                        rr.append(None if v is None else round(v, 2))
                        nn.append(n)
                        mm.append(m)
                    rowsout.append([ch[0], ch[1], 0, rr, nn, mm])   # kind 0 = original channel row
            qd[q] = {"u": units.get((code, q), ""), "r": rowsout}
        comp[code] = {"n": names[code], "q": qd}
    out = {
        "meta": {
            "source": "master_persistency.json",
            "source_rows": len(rows),
            "source_sha12": _sha(PS_SRC),
            "rounds": ROUNDS,
            "bundles": BUNDLES,
            "quarters": quarters,
            "note": "q[분기].r=[[대분류(묶음행이면 묶음명),소분류,kind(1=묶음소계 0=원행),[유지율%x4],[대상신계약액x4],[유지계약액x4]]], 회차=meta.rounds, u=금액 단위",
        },
        "companies": comp,
    }
    size = _write(PS_OUT, out)
    print(f"[persistency] companies={len(comp)} quarters={quarters} bytes={size:,}")
    print(f"[persistency] rate-only rows ignored inside amount-based bundles: {rate_only_dropped}; "
          f"rows with target>0 but no retained amount excluded from sums: {amt_missing_excluded}")
    return out


def main() -> int:
    global CHECK
    CHECK = "--check" in sys.argv[1:]
    build_loss_ratio()
    build_persistency()
    if CHECK:
        for m in CHECK_FAILS:
            print("[check] FAIL", m)
        print("[check]", "FAIL" if CHECK_FAILS else "OK: both panel JSONs are byte-identical to a fresh build of their masters")
        return 1 if CHECK_FAILS else 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
