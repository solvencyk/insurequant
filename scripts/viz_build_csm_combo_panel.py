"""Build the data panel for the IFRS17 section-3 combo-chart MOCKUP (LRC stack + LIC stack + new-business CSM line).

Reads (READ ONLY, never written):
    insurance_liability_portfolio.json  (경영공시 2-4, 억원, 잔여보장요소 LRC 기준, 2025.1Q~)
    CSM_waterfall.json                  (기말 CSM item 6 / 신계약 CSM 당기 증분 item 2 값_당분기, 억원)
    IFRS17_BS.json                      (item 20 보험계약부채, 백만원 -> 억원; 발생사고요소 LIC 추정에만 쓴다)
Writes:
    data/csm_combo/panel_csm_combo.json   (company code -> {n, type, q:{disclosure quarter -> array row}}; codes are JSON keys only, never rendered)

Row layout (억원, null = no value):
    [csm_gen, csm_vfa, bel_gen, bel_vfa, ra_gen, ra_vfa, paa, lrc_total, nb_csm, lic_est, bs20]
    bs20    = BS 보험계약부채(IFRS17_BS item 20, 백만원 -> 억원)
    lic_est = 발생사고요소(LIC) **추정**. 지금은 bs20 - lrc_total (lic_estimate() 한 곳).
    ** SWAP POINT ** parser 가 LIC BEL/RA 실공시를 적재하면 lic_estimate() 만 고친다(그리고 meta.lic_basis).
    화면(IFRS17.html)은 이 열과 meta.lic_basis 만 읽는다.

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


LIC_BASIS = "추정: BS 보험계약부채(item 20) − 잔여보장요소 합계(2-4 item 8). 발생사고요소 BEL·RA 실공시 아님"


def lic_estimate(bs20_eok, lrc_total):
    """SWAP POINT — 발생사고요소(LIC) 값. 실공시(BEL·RA)를 확보하면 이 함수와 LIC_BASIS 만 바꾼다."""
    if bs20_eok is None or lrc_total is None or bs20_eok <= lrc_total:
        return None
    return round(bs20_eok - lrc_total, 1)


def num(v):
    return None if v is None else float(v)


def main(check: bool) -> int:
    port = load("insurance_liability_portfolio.json")
    wf = load("CSM_waterfall.json")
    bs = load("IFRS17_BS.json")

    pf = defaultdict(dict)
    name_of, type_of = {}, {}
    for r in port:
        c = r["원보험사코드"]
        pf[(c, r["공시분기"])][r["항목번호"]] = num(r["값"])
        name_of[c] = r["원수사명"]
        type_of[c] = r["생손보여부"]
    nb = {(r["원보험사코드"], r["공시분기"]): num(r.get("값_당분기")) for r in wf if r["항목번호"] == 2}
    end_csm = {(r["원보험사코드"], r["공시분기"]): num(r["값"]) for r in wf if r["항목번호"] == 6}
    bs20 = {(r["원보험사코드"], r["공시분기"]): num(r["값"]) for r in bs if r["항목번호"] == 20}

    code_of = {v: k for k, v in name_of.items()}
    quarters = sorted({q for (_, q) in pf})
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
        row = [d.get(3), d.get(6), d.get(1), d.get(4), d.get(2), d.get(5), d.get(7), total, nb.get((c, q)), lic_estimate(b, total), b]
        co = companies.setdefault(c, {"n": name_of[c], "type": "생보" if type_of[c] == "생명보험" else "손보", "q": {}})
        co["q"][q] = row

    out = {
        "meta": {
            "unit": "억원",
            "quarters": quarters,
            "columns": ["csm_gen", "csm_vfa", "bel_gen", "bel_vfa", "ra_gen", "ra_vfa", "paa", "lrc_total", "nb_csm", "lic_est", "bs20"],
            "lic_basis": LIC_BASIS,
            "basis": "잔여보장요소(LRC) 기준 — 경영공시 2-4. 발생사고요소(LIC)는 실공시값이 없어 lic_est(BS 보험계약부채 - LRC 합계) 추정만 제공",
            "pending": [[code_of[n], q] for n, q in PENDING_NAMES if n in code_of],
            "csm_mismatch": mism,
            "csm_recon": f"포트폴리오 CSM(3+6) vs CSM_waterfall 기말(6): 대조 {cmp_n}건 중 불일치 {cmp_bad}건(허용 0.5%)",
            "sources": ["insurance_liability_portfolio.json", "CSM_waterfall.json", "IFRS17_BS.json"],
        },
        "companies": companies,
    }
    data = json.dumps(out, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    if len(data) > MAX_BYTES:
        raise SystemExit(f"{OUT.name}: {len(data):,} bytes exceeds budget")
    print(f"companies {len(companies)}, quarters {quarters[0]}~{quarters[-1]}, {len(data):,} bytes; {out['meta']['csm_recon']}")
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
