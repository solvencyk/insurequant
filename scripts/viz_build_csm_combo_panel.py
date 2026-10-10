"""Build the data panel for the IFRS17 section-3 combo chart (LRC stack + LIC stack + new-business CSM line).

Reads (READ ONLY, never written):
    insurance_liability_portfolio.json  (경영공시 2-4, 억원, 잔여보장요소 LRC 기준, 2025.1Q~; 항목 10~15 = 발생사고요소 LIC 실공시, 항목 16·17 = LIC 2단계 계산값(있을 때만))
    CSM_waterfall.json                  (기말 CSM item 6 / 신계약 CSM 당기 증분 item 2 값_당분기, 억원)
    IFRS17_BS.json                      (item 20 보험계약부채, 백만원 -> 억원; LIC 추정·상계 차이에 쓴다)
    data/_derived/ilp_includes_lic.json (사이드카: 2-4 합계가 이미 LIC 를 포함한 회사·분기 -- ABL·KDB생명·푸본현대)
Writes:
    data/csm_combo/panel_csm_combo.json   (company code -> {n, type, q:{disclosure quarter -> array row}}; codes are JSON keys only, never rendered)

Row layout (억원, null = no value):
    [csm_gen, csm_vfa, bel_gen, bel_vfa, ra_gen, ra_vfa, paa, lrc_total, nb_csm, lic_total, bs20,
     lic_bel, lic_ra, lic_unsplit, lic_bel_calc, lic_ra_calc, lic_kind]
    bs20       = BS 보험계약부채(IFRS17_BS item 20, 백만원 -> 억원)
    lic_total  = 발생사고요소 합계 (lic_kind 로 출처가 갈린다)
    lic_kind   = 1 실공시(항목 10) / 0 추정(= bs20 - lrc_total) / 2 사이드카(lic_total 은 실공시 참고값, 2-4 합계에 이미 포함 -> 오른쪽 막대 안 그림) / null 값 없음
    lic_bel/ra = 항목 11/12 (회사가 BEL·RA 를 직접 나눠 공시한 몫)   lic_bel_calc/ra_calc = 항목 16/17 (LIC 2단계 계산값, 화면 「계산값」)
    lic_unsplit= 실공시 합계 - 위 4조각(= 항목 13 과 같다; 항목 16·17 이 없으면 항목 13 을 그대로)
    ** SWAP POINT ** lic_cells() 한 곳. 화면(IFRS17.html)은 이 열과 meta.lic_basis 만 읽는다.

Run:    C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/viz_build_csm_combo_panel.py
Check:  ... --check   rebuilds in memory, compares bytes with the file on disk; exit 1 on difference.
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "csm_combo" / "panel_csm_combo.json"
MAX_BYTES = int(1.5 * 1024 * 1024)

# owner 판단 대기 칸(2026-10-10 티켓): 값이 바뀔 수 있어 화면에서 '확인 중' 표시.
PENDING_NAMES = [["하나생명보험", "2026.2Q"], ["아이엠라이프생명보험", "2025.1Q"]]


def load(rel):
    with (ROOT / rel).open(encoding="utf-8") as f:
        return json.load(f)


LIC_BASIS = ("발생사고요소(LIC): 실공시 = 포트폴리오 마스터 항목 10~13(DART 주석, 부채 기준) / 계산값 = 항목 16·17(측정요소별 BEL·RA − 2-4) / "
             "추정 = BS 보험계약부채(item 20) − 잔여보장요소(2-4 item 8), 실공시가 없는 분기만")
EST_TOL = 0.15   # 같은 회사에서 실공시가 있는 분기의 추정이 실공시와 15% 넘게 다르면 그 회사의 다른 분기 추정은 믿을 수 없어 그리지 않는다
SIDECAR = "data/_derived/ilp_includes_lic.json"


def lic_estimate(bs20_eok, lrc_total):
    """추정: 실공시(항목 10)가 없는 분기에만 쓴다."""
    if bs20_eok is None or lrc_total is None or bs20_eok <= lrc_total:
        return None
    return round(bs20_eok - lrc_total, 1)


def r2(x):
    return None if x is None else round(x, 2)


def lic_cells(d, bs20_eok, lrc_total, in_sidecar, est_ok):
    """SWAP POINT -> [lic_total, lic_bel, lic_ra, lic_unsplit, lic_bel_calc, lic_ra_calc, lic_kind]."""
    tot = d.get(10)
    if tot is not None:
        bel, ra, bc, rc = d.get(11), d.get(12), d.get(16), d.get(17)
        if bc is None and rc is None and d.get(13) is not None:
            un = d.get(13)
        else:
            un = round(tot - sum(x for x in (bel, ra, bc, rc) if x is not None), 2)
        return [tot, bel, ra, r2(un), bc, rc, 2 if in_sidecar else 1]
    est = lic_estimate(bs20_eok, lrc_total) if est_ok else None
    if est is None:
        return [None, None, None, None, None, None, None]
    return [est, None, None, None, None, None, 0]


def num(v):
    return None if v is None else float(v)


def main(check: bool) -> int:
    port = load("insurance_liability_portfolio.json")
    wf = load("CSM_waterfall.json")
    bs = load("IFRS17_BS.json")

    pf = defaultdict(dict)
    name_of, type_of, item_name = {}, {}, {}
    for r in port:
        c = r["원보험사코드"]
        pf[(c, r["공시분기"])][r["항목번호"]] = num(r["값"])
        name_of[c] = r["원수사명"]
        type_of[c] = r["생손보여부"]
        item_name[r["항목번호"]] = r["항목명"]
    # 항목 16·17 은 LIC 2단계가 BEL·RA 계산값으로 붙인다. 번호만 믿고 엉뚱한 항목을 그리지 않도록 이름을 확인한다.
    for no, key in ((16, "최선추정"), (17, "위험조정")):
        if no in item_name and key not in item_name[no]:
            raise SystemExit(f"포트폴리오 항목 {no} 이름이 '{item_name[no]}' -- 계산값 BEL·RA 가 아닌 듯해 중단")
    side = load(SIDECAR)["companies"]
    side_q = {c: set(v["quarters"]) for c, v in side.items()}
    nb = {(r["원보험사코드"], r["공시분기"]): num(r.get("값_당분기")) for r in wf if r["항목번호"] == 2}
    end_csm = {(r["원보험사코드"], r["공시분기"]): num(r["값"]) for r in wf if r["항목번호"] == 6}
    bs20 = {(r["원보험사코드"], r["공시분기"]): num(r["값"]) for r in bs if r["항목번호"] == 20}

    code_of = {v: k for k, v in name_of.items()}
    quarters = sorted({q for (_, q) in pf})
    # 추정이 믿을 만한 회사: 실공시가 있는 분기에서 추정(bs20 - 2-4 합계)이 실공시와 EST_TOL 이내로 맞아야 한다.
    # 실공시 분기가 하나도 없는 회사는 확인할 수단이 없어 기존대로 추정을 허용한다.
    est_ok, est_dev = {}, {}
    for (c, q), d in pf.items():
        b, t = bs20.get((c, q)), d.get(8)
        if d.get(10) and b is not None and t is not None and c not in side_q:
            dev = abs((b / 100.0 - t) / d[10] - 1)
            est_dev[c] = max(est_dev.get(c, 0.0), dev)
    for c in name_of:
        est_ok[c] = est_dev.get(c, 0.0) <= EST_TOL
    kinds = defaultdict(int)
    split_bad = 0
    companies = {}
    cmp_n = cmp_bad = 0
    mism = []
    for (c, q), d in sorted(pf.items(), key=lambda kv: (kv[0][0], kv[0][1])):
        total = d.get(8)
        csm = (d.get(3) or 0.0) + (d.get(6) or 0.0)
        e = end_csm.get((c, q))
        if e is not None:
            cmp_n += 1
            if abs(csm - e) > max(2.0, abs(e) * 0.005):
                cmp_bad += 1
        b = bs20.get((c, q))
        b = None if b is None else round(b / 100.0, 1)   # 백만원 -> 억원
        if e is not None and abs(csm - e) > max(2.0, abs(e) * 0.005):
            mism.append([c, q, round(csm, 1), e])
        lic = lic_cells(d, b, total, q in side_q.get(c, ()), est_ok[c])
        kinds[lic[6]] += 1
        if d.get(10) is not None and lic[3] is not None and lic[3] < -0.5:
            split_bad += 1
        row = [d.get(3), d.get(6), d.get(1), d.get(4), d.get(2), d.get(5), d.get(7), total, nb.get((c, q)), lic[0], b] + lic[1:]
        co = companies.setdefault(c, {"n": name_of[c], "type": "생보" if type_of[c] == "생명보험" else "손보", "q": {}})
        co["q"][q] = row

    out = {
        "meta": {
            "unit": "억원",
            "quarters": quarters,
            "columns": ["csm_gen", "csm_vfa", "bel_gen", "bel_vfa", "ra_gen", "ra_vfa", "paa", "lrc_total", "nb_csm", "lic_total", "bs20",
                        "lic_bel", "lic_ra", "lic_unsplit", "lic_bel_calc", "lic_ra_calc", "lic_kind"],
            "lic_kind": {"0": "추정", "1": "실공시", "2": "2-4 에 이미 포함"},
            "lic_basis": LIC_BASIS,
            "basis": "잔여보장요소(LRC) 기준 — 경영공시 2-4. 발생사고요소(LIC)는 DART 주석 실공시(항목 10~13)를 우선하고, 없는 분기만 lic_total 에 추정(BS 보험계약부채 - LRC 합계)",
            "includes_lic": {c: sorted(v) for c, v in side_q.items()},
            "est_unreliable": sorted(c for c, ok in est_ok.items() if not ok),
            "pending": [[code_of[n], q] for n, q in PENDING_NAMES if n in code_of],
            "csm_mismatch": mism,
            "csm_recon": f"포트폴리오 CSM(3+6) vs CSM_waterfall 기말(6): 대조 {cmp_n}건 중 불일치 {cmp_bad}건(허용 0.5%)",
            "lic_recon": f"발생사고요소 셀: 실공시 {kinds[1]} · 사이드카(2-4 에 포함) {kinds[2]} · 추정 {kinds[0]} · 없음 {kinds[None]}",
            "sources": ["insurance_liability_portfolio.json", "CSM_waterfall.json", "IFRS17_BS.json", SIDECAR],
        },
        "companies": companies,
    }
    data = json.dumps(out, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    if len(data) > MAX_BYTES:
        raise SystemExit(f"{OUT.name}: {len(data):,} bytes exceeds budget")
    print(f"companies {len(companies)}, quarters {quarters[0]}~{quarters[-1]}, {len(data):,} bytes; {out['meta']['csm_recon']}")
    print(out["meta"]["lic_recon"], f"| 추정 불신 회사 {len(out['meta']['est_unreliable'])} | 미분리 음수 {split_bad}")
    if check:
        on_disk = OUT.read_bytes() if OUT.exists() else None
        if on_disk != data:
            print(f"FAIL {OUT.relative_to(ROOT).as_posix()}: on-disk differs from fresh build")
            return 1
        print(f"OK   {OUT.relative_to(ROOT).as_posix()} identical to a rebuild")
        return 0
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("wb") as f:
        f.write(data)
    return 0


if __name__ == "__main__":
    sys.exit(main("--check" in sys.argv[1:]))
