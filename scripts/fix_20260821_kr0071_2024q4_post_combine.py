# -*- coding: utf-8 -*-
"""KR0071 (흥국생명) 2024.4Q - combined 경과조치 적용후 요구자본 부모(15/16/22/23) fill.

Context (inbox/parser/20260821T1720Z__orchestrator__KR0071_2024.4Q__file_was_correct_all_along.md):
raw data/disclosure/FY2024_Q4/raw/KR0071_흥국생명보험.pdf was wrongly declared "wrong document"
three times in a row because fitz text search for "경과조치" returns 0 hits across all 538 pages.
p1-112 of THIS file are scanned images (the K-ICS body); p113-450 is the (searchable) financial
statements/audit report where the keyword legitimately never appears. Keyword-miss != content-
absent. Rendered p44/47/49/50/51 at 260dpi and read them directly (see ticket for the page map).

흥국생명 selected TWO transitions (p47 application table): TIR(O, 신규보험위험=장수/사업비/해지/
대재해, table (2) p50) + TER(O, 주식위험, table (3) p51). Each single-axis table in the filing shows
ONLY its own risk reduced with every other row held at 적용전 - there is no third "combined" table
in the source. This reuses the ALREADY-VETTED combine algorithm in
scripts/rebuild_combined_transition_after.py (leaf-from-whichever-table-moved-it + R4/R7/MARKET_M
parent recompute + headline-anchored 기준금액후 + tax-as-residual) via import, rather than
retyping the correlation matrices or the combination logic - this script only supplies the target
selection that the resident script's `main()` doesn't cover: it requires 값_적용후(item15) to
ALREADY be present (mismatch repair), and ours is null (missing entirely, a census gap not a
mismatch), so `targets` in that script's main() skips it (line ~371-379, `if p15 is None: continue`).
The resident script's own `AFFILIATE = {"KR0071": "KR0005"}` (already in its source) is what makes
item23 solvable here: 흥국생명's item23 ("업권별 자본규제를 활용한 관계회사의 요구자본 환산치")
is a fixed multiple of 흥국화재(KR0005)'s item14, not readable stand-alone from either table (2)/(3)
(they show DIFFERENT numbers for it - 599,206 vs 703,625 백만원 - exactly the "다중경과조치 결합
불명, 절대 추측 금지" case scripts/fill_post_transition_adjust_items.py already refuses to guess).

Verification before writing (same battery as the resident script, all logged):
  1. leaf reproduces the raw table's own 적용전 기본요구자본 (R4/R7/M unit+row match).
  2. reconstructed 생명장기후/시장후 reproduce what tables (2)/(3) print for THEIR OWN axis.
  3. combined 기준금액후 anchored to the filing's own headline 경과조치 후 지급여력비율 (p44:
     207.0%, machine-read from 주요경영지표 page) - reconciliation anchor per the ticket.
  4. combined 기본요구자본후/기준금액후 is <= every single-axis table's own value (monotonicity -
     applying two transitions can only reduce further, never increase, vs either alone).
  5. residual 법인세조정액후 is non-negative and <= 1.2x its 적용전 value.

UPSERT-only, cell-by-cell, printed before/after census. Never touches insurequant_master_tables.xlsx.

Usage: C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe \
           scripts/fix_20260821_kr0071_2024q4_post_combine.py [--dry-run]
"""
from __future__ import annotations

import io
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "src"))

from rebuild_combined_transition_after import (  # noqa: E402
    AFFILIATE, ITEM_OF, LIFE7, MARKET5, _num, _pdf, q2p, resolve_leaf, scan_occurrences,
)
from solvency.validation.kics_json_rules import R4, R7, MARKET_M  # noqa: E402

TARGET = REPO / "kics_disclosure.json"
CODE, QUARTER = "KR0071", "2024.4Q"


def main() -> int:
    dry = "--dry-run" in sys.argv

    data = json.loads(TARGET.read_text(encoding="utf-8"))
    by_cq: dict[tuple, dict] = defaultdict(dict)
    name = {}
    for r in data:
        c, q = r["원보험사코드"], r["공시분기"]
        name[c] = r.get("원수사명", c)
        by_cq[(c, q)][int(r["항목번호"])] = r

    def val(items, n, post):
        r = items.get(n)
        if r is None:
            return None
        return _num(r.get("값_적용후" if post else "값"))

    items = by_cq[(CODE, QUARTER)]
    print("=== BEFORE ===")
    for it in (14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 27, 28):
        r = items.get(it)
        print(f"  item{it:>2} [{r.get('항목명') if r else '?'}] 값={val(items, it, False)} "
              f"값_적용후={val(items, it, True)}")

    pdf = _pdf(q2p(QUARTER), CODE)
    print(f"\nraw pdf: {pdf}")
    assert pdf is not None, "raw PDF missing"

    occ_scan, headline = scan_occurrences(pdf)
    n_scan = sum(len(v) for v in occ_scan.values())
    print(f"scan_occurrences() text-scan found {n_scan} occurrences across all leaves "
          f"(expected 0: p1-112 incl. p49-51 are scanned images, fitz native text is empty there "
          f"— confirmed 0 char extraction when rendering p43-52 earlier this session)")
    assert n_scan == 0, (
        "text scan unexpectedly found data — the manual occ below would then be redundant/stale; "
        "re-check whether this PDF's K-ICS section gained a text layer")

    # occ built BY HAND from rendering p49/p50/p51 at 260dpi (fitz get_pixmap) and reading them
    # directly — this is the vision-read the ticket calls for, not a keyword/text-layer extraction.
    # Page footers ("- 49 -"/"- 50 -"/"- 51 -") were checked against the physical PDF page index
    # (1-indexed, no offset) before transcribing. Each tuple is (경과조치 적용 전, 경과조치 적용 후)
    # in raw 백만원, exactly as printed — no rounding/derivation performed here.
    #
    # p50 "(2) 장수위험·사업비위험·해지위험 및 대재해위험 경과조치" (TIR, this company's 신규보험위험
    # transition, p47 application table: TIR=O) — the ONLY table that breaks out the 7 life leaves;
    # its own 시장위험액 row is unchanged (674,275/674,275), confirming TIR does not touch market risk.
    # p51 "(3) 주식위험 경과조치 또는 금리위험 경과조치" (TER, this company elected 주식위험 not
    # 금리위험 — p47: TER=O, TIRR=X) — the ONLY table that breaks out the 5 market leaves; its own
    # 생명·장기손해보험 위험액 row is unchanged (1,400,224/1,400,224), confirming TER does not touch
    # life risk. Neither table's post column for the OTHER axis's parent/leaves is a "0" — it is the
    # unchanged 적용전 figure copied across, per the disclosure's own convention (ticket: "각 표는
    # 자기가 줄인 위험만 줄이고 나머지는 적용전 그대로다").
    occ = {
        # --- LIFE7 (only p50 breaks these out) ---
        "사망": [(121112.0, 121112.0)],
        "장수": [(68771.0, 14272.0)],
        "장해질병": [(853010.0, 853010.0)],
        "장기재물": [(0.0, 0.0)],          # "-"/"-" (printed dash both cols)
        "해지": [(821228.0, 0.0)],          # "-" 적용후 = fully phased to 0 under TIR, printed as-is
        "사업비": [(214577.0, 57537.0)],
        "생명대재해": [(36294.0, 1777.0)],
        # --- MARKET5 (only p51 breaks these out) ---
        "금리": [(235629.0, 235629.0)],
        "주식": [(339125.0, 208389.0)],
        "부동산": [(354049.0, 354049.0)],
        "외환": [(82252.0, 82252.0)],
        "자산집중": [(0.0, 0.0)],           # "-"/"-"
        # --- unaffected by either axis, both tables agree ---
        "신용": [(405758.0, 405758.0), (405758.0, 405758.0)],
        "운영": [(80133.0, 80133.0), (80133.0, 80133.0)],
        "일반손해": [(0.0, 0.0), (0.0, 0.0)],
        # --- parent-level cross-check occurrences (one per table; used for disc_* sanity, not
        #     fed through resolve_leaf) ---
        "생명장기": [(1400224.0, 922222.0), (1400224.0, 1400224.0)],   # p50 reduces, p51 unchanged
        "시장": [(674275.0, 674275.0), (674275.0, 591521.0)],          # p50 unchanged, p51 reduces
        "기본요구자본": [(1943692.0, 1530854.0), (1943692.0, 1894899.0)],
        "법인세": [(428816.0, 348792.0), (428816.0, 429635.0)],
        "기타요구자본": [(725567.0, 599206.0), (725567.0, 703625.0)],
        "기준금액": [(2240443.0, 1781268.0), (2240443.0, 2168890.0)],
    }
    # _headline_after() greps native PDF text for '주요경영지표'/'경과조치 후' - this whole K-ICS
    # section is rasterized (see ticket: fitz '경과조치' 0 hits across all 538p), so it correctly
    # finds nothing here. The reconciliation anchor instead comes from p44 [지급여력비율 총괄]
    # (rendered at 260dpi and read by eye - ticket + this session): 경과조치 후 지급여력비율=207.0%,
    # 지급여력금액=35,158억원, 지급여력기준금액=16,987억원 for 24.4Q. item14후=16987 and
    # item27후=206.97003591 (=35158/16987*100) are ALREADY correctly loaded in the master from
    # that same read (only 15/16/22/23후 are missing) - use the master's own item14후 as the
    # anchor rather than re-deriving it, and use the *stored* item27후 (higher precision than the
    # printed 207.0) for the raw-unit back-conversion below.
    headline_precise = val(items, 27, True)
    assert headline_precise is not None, "item27후 (headline ratio, already loaded) missing"
    assert abs(headline_precise - 206.97) < 0.5, f"item27후 {headline_precise} != p44 read ~207.0"

    other_cands = [a for a, _b in occ.get("기타요구자본", []) if a is not None]
    other_pre = max(other_cands) if other_cands else 0.0
    link = AFFILIATE.get(CODE)
    o_pre_m = val(items, 23, False)
    l_pre = val(by_cq.get((link, QUARTER), {}), 14, False)
    l_post = val(by_cq.get((link, QUARTER), {}), 14, True)
    print(f"\naffiliate {link}: item14 전={l_pre} 후={l_post}")
    assert link and o_pre_m and l_pre and l_post, "affiliate item14 pre/post missing"
    ks = []
    for qq in {qq for (cc, qq) in by_cq if cc == CODE}:
        a = val(by_cq[(CODE, qq)], 23, False)
        b = val(by_cq.get((link, qq), {}), 14, False)
        if a and b:
            ks.append(a / b)
    k = o_pre_m / l_pre
    med = sorted(ks)[len(ks) // 2] if ks else k
    print(f"affiliate ratio k(this q)={k:.5f}  median across {len(ks)}q={med:.5f}  "
          f"|k-med|={abs(k - med):.5f}")
    assert abs(k - med) <= 0.002, "affiliate ratio deviates from company median"
    other_after_master = k * l_post

    leaves, notes = {}, {}
    bad = None
    for kk in LIFE7 + MARKET5 + ["신용", "운영", "일반손해"]:
        v, note = resolve_leaf(occ.get(kk, []))
        leaves[kk], notes[kk] = v, note
        print(f"  leaf {kk:<8} -> {v}  ({note})")
        if v is None and kk not in ("자산집중", "장기재물", "장수"):
            bad = f"{kk}: {note}"
    assert not bad, f"leaf resolution failed: {bad}"
    for kk in ("자산집중", "장기재물", "장수"):
        if leaves[kk] is None:
            leaves[kk] = 0.0

    s = np.array([leaves[kk] for kk in LIFE7], float)
    life_after = float(np.sqrt(s @ R7 @ s))
    v = np.array([leaves[kk] for kk in MARKET5], float)
    mkt_after = float(np.sqrt(v @ MARKET_M @ v))
    w = np.array([life_after, leaves["일반손해"], mkt_after, leaves["신용"]], float)
    base_after = float(np.sqrt(w @ R4 @ w)) + leaves["운영"]
    print(f"\nlife_after(R7)={life_after:.2f}  mkt_after(M)={mkt_after:.2f}  "
          f"base_after(R4)+운영={base_after:.2f}  (백만원)")

    sp = np.array([(occ[kk][0][0] if occ.get(kk) else 0.0) for kk in LIFE7], float)
    life_pre = float(np.sqrt(sp @ R7 @ sp))
    vp = np.array([(occ[kk][0][0] if occ.get(kk) else 0.0) for kk in MARKET5], float)
    mkt_pre = float(np.sqrt(vp @ MARKET_M @ vp))
    nl_pre = occ["일반손해"][0][0] if occ.get("일반손해") else 0.0
    cr_pre = occ["신용"][0][0] if occ.get("신용") else 0.0
    op_pre = occ["운영"][0][0] if occ.get("운영") else 0.0
    wp = np.array([life_pre, nl_pre, mkt_pre, cr_pre], float)
    base_pre_calc = float(np.sqrt(wp @ R4 @ wp)) + op_pre
    cands = [a for a, _b in occ["기본요구자본"]
             if base_pre_calc and abs(a - base_pre_calc) <= max(2.0, 0.005 * base_pre_calc)]
    print(f"base_pre_calc(R4 재현)={base_pre_calc:.2f}  raw 기본요구자본전 occurrences="
          f"{sorted({a for a, _ in occ['기본요구자본']})}")
    assert cands, f"적용전 기본요구자본 재현 실패: 계산={base_pre_calc:,.0f}"
    base_pre = cands[0]

    tax_cands = [a for a, _b in occ.get("법인세", []) if 0 <= a <= base_pre]
    tax_pre = max(tax_cands) if tax_cands else 0.0
    print(f"tax_pre(법인세조정액전, raw 백만원)={tax_pre:.2f}")

    disc_life = {round(b, 1) for a, b in occ.get("생명장기", []) if b is not None and abs(a - b) > 0.5}
    disc_mkt = {round(b, 1) for a, b in occ.get("시장", []) if b is not None and abs(a - b) > 0.5}
    print(f"disclosed 생명장기후 candidates(변동만)={sorted(disc_life)}  "
          f"disclosed 시장후 candidates(변동만)={sorted(disc_mkt)}")
    assert not disc_life or any(abs(life_after - d) <= max(2.0, 0.002 * d) for d in disc_life), \
        f"생명장기후 재현 실패 R7={life_after:,.2f} vs 표={sorted(disc_life)}"
    assert (not disc_mkt or any(abs(mkt_after - d) <= max(2.0, 0.002 * d) for d in disc_mkt)
            or len(disc_mkt) >= 2), \
        f"시장후 재현 실패 M={mkt_after:,.2f} vs 표={sorted(disc_mkt)}"

    avail_after = val(items, 1, True)
    assert avail_after is not None, "item1후 없음(비율 검산 불가)"
    scale = (val(items, 15, False) or 0) / base_pre if base_pre else 0
    print(f"scale(마스터 억원/raw 백만원, 적용전 앵커)={scale:.6f}")
    assert 0.009 < scale < 0.011 or 0.99 < scale < 1.01, f"단위 스케일 이상 {scale:.5f}"
    # snap to the exact unit ratio (raw tables are 백만원, master is 억원 = /100) — the empirical
    # scale above carries the ~1e-5 rounding noise of base_pre_calc (R4-reconstructed 적용전) vs
    # the table's own printed integer subtotal, which otherwise bleeds a spurious +/-0.01 into
    # every UNCHANGED leaf (36/38/39/40, 신용/운영) that should reproduce their 적용전 값 exactly
    # (scripts/rebuild_combined_transition_after.py::_leaves_mode does the same snap; main() does
    # not, but there's no reason to inherit that imprecision here).
    scale = 0.01 if scale < 0.5 else 1.0
    print(f"scale snapped to exact unit ratio = {scale}")

    scr_after = avail_after / headline_precise * 100 / scale
    other_after = other_after_master / scale if scale else 0.0
    tax_after = base_after + other_after - scr_after
    print(f"\nscr_after(기준금액후, raw 단위 역산)={scr_after:.2f}  "
          f"other_after(raw 단위)={other_after:.2f}  tax_after(잔차, raw 단위)={tax_after:.2f}")

    disc_base = [b for a, b in occ["기본요구자본"]
                 if b is not None and a == base_pre and abs(a - b) > 0.5]
    disc_scr = [b for a, b in occ.get("기준금액", [])
                if b is not None and b > 0.1 * base_pre and abs(a - b) > 0.5]
    print(f"single-axis 기본요구자본후 candidates={sorted(disc_base)}  "
          f"single-axis 기준금액후 candidates={sorted(disc_scr)}")
    assert not disc_base or base_after <= min(disc_base) + 2.0, \
        f"결합 기본요구자본후 {base_after:,.2f} > 단일표 최소 {min(disc_base):,.2f} (단조성 위반)"
    assert not disc_scr or scr_after <= min(disc_scr) + 2.0, \
        f"결합 기준금액후 {scr_after:,.2f} > 단일표 최소 {min(disc_scr):,.2f} (단조성 위반)"
    assert -0.5 <= tax_after <= max(1.0, tax_pre * 1.2 + 2), \
        f"법인세후 잔차 비정상 {tax_after:,.2f} (전={tax_pre:,.2f})"

    new = {
        15: base_after * scale,
        17: life_after * scale,
        19: mkt_after * scale,
        22: tax_after * scale,
        14: scr_after * scale,
        16: (life_after + leaves["일반손해"] + mkt_after + leaves["신용"] + leaves["운영"]
             - base_after) * scale,
    }
    if abs(other_after_master) > 0.005:
        new[23] = other_after_master
    for kk in MARKET5:
        new[ITEM_OF[kk]] = leaves[kk] * scale
    v2, v14 = val(items, 2, True), new[14]
    new[27] = avail_after / v14 * 100
    if v2 is not None:
        new[28] = v2 / v14 * 100

    # sanity: reconstructed 14 must match already-trusted headline-anchored value from p44 (16,987억)
    print(f"\nreconstructed item14후(억원)={new[14]:.2f}  existing master item14후="
          f"{val(items, 14, True)}  raw headline p44 지급여력기준금액후=16,987")
    assert abs(new[14] - 16987) <= 2.0, f"item14후 재구성값이 헤드라인(16,987)과 불일치: {new[14]:.2f}"
    assert abs(new[14] - val(items, 14, True)) <= 2.0, "재구성 item14후가 기존 저장값과 불일치"

    # Ticket scope is exactly the 4 POST_TRANSITION_PARENT_MISSING cells (15/16/22/23후). The rest
    # of `new` (17/19/27/28/36-40) is computed only as an internal cross-check — those cells are
    # ALREADY correct in the master (this dry-run's own numbers reproduce them, see log above) and
    # are deliberately NOT written here, to keep this a surgical 4-cell fix rather than a type/
    # precision-normalizing rewrite of cells nobody flagged.
    WRITE_SCOPE = (15, 16, 22, 23)
    print(f"\n=== cross-check only, NOT written (already correct) ===")
    for it, v in sorted(new.items()):
        if it in WRITE_SCOPE:
            continue
        row = items.get(it)
        print(f"  item{it:>2} [{row.get('항목명') if row else '?'}] computed={round(v, 2)}  "
              f"stored={row.get('값_적용후') if row else None}")

    print("\n=== TO WRITE (cell-by-cell) ===")
    def fmt(x):
        return str(int(round(x))) if abs(x - round(x)) < 1e-6 else f"{x:.2f}".rstrip("0").rstrip(".")

    writes = []
    for it in WRITE_SCOPE:
        v = new.get(it)
        if v is None:
            print(f"  SKIP item{it}: not computed (see rejects/asserts above)")
            continue
        row = items.get(it)
        if row is None:
            print(f"  SKIP item{it}: row not in master")
            continue
        sv = fmt(round(v, 2))
        old = row.get("값_적용후")
        if old == sv:
            print(f"  item{it:>2}: unchanged ({sv})")
            continue
        print(f"  item{it:>2} [{row.get('항목명')}] 값_적용후: {old!r} -> {sv!r}")
        writes.append((row, sv))

    print("\n=== AFTER (would-be) ===")
    preview = {id(row): sv for row, sv in writes}
    for it in (14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 27, 28):
        r = items.get(it)
        shown = preview.get(id(r), r.get("값_적용후") if r else None)
        print(f"  item{it:>2} 값_적용후={shown}")

    # identity re-check with the values about to be written
    v15, v22, v23 = new.get(15), new.get(22), new.get(23, val(items, 23, True))
    v14chk = v15 - v22 + v23
    print(f"\nidentity check (post-write): item15후-item22후+item23후 = {v15:.2f}-{v22:.2f}+{v23:.2f}"
          f" = {v14chk:.2f}  vs item14후={new[14]:.2f}  diff={abs(v14chk-new[14]):.4f}")
    assert abs(v14chk - new[14]) <= 0.5

    if dry:
        print("\n(dry-run; 파일 안 씀)")
        return 0
    if not writes:
        print("\n변경 없음")
        return 0
    for row, sv in writes:
        row["값_적용후"] = sv
    TARGET.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n{len(writes)}셀 갱신, wrote {TARGET.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
