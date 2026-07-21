#!/usr/bin/env python3
"""DATA CONTRACT pre-push gate — Phase 1 (owner spec 20260616T1155Z, §4).

Single blocking runner that publishing runs #0 (before the older validation/assembly
gates) right before recommending a git push. It codifies two months of live-QA "기초정합성"
findings (memory: coverage-census-mandatory, validation-blind-spots) into a hard gate plus
ONE new axis — source provenance / as-of — that the scattered validators never had.

Anti-gaming character (spec §0):
  - RED=0 to pass (no exception mechanism — fix or owner-escalate, owner 2026-06-16). Exit 2 on any RED.
  - MISSING census / MISSING provenance = RED, NEVER counted as a silent SKIP-pass.
  - mtime snapshot before/after; if a master changed under us (concurrent backfill) the report
    is stamped "provisional".

Phase 1 = buildable from EXISTING fields only (no new metadata emission required):
  CHECK 1 — Completeness census   (spec §1): expected (filer × quarter × item-block) grid per
            master; missing cell / collapsed filer-count / parent-disclosed-but-children-missing
            = RED. Reuses validate_kics_disclosure._coverage_census + _parent_zero_child_nonzero
            and validate_master_tables.coverage_holes (imported, not duplicated).
  CHECK 2 — As-of match + effective-list flag (spec §2 a/c): each published artifact's as_of
            period must equal its disclosure quarter (stale 2025.4Q-rendered-as-2026.1Q = RED);
            and tier/forward capital-securities must show evidence that as-of effective filtering
            was applied (absent = RED).
  CHECK 3 — Same-concept cross-source tolerance + DIFFERENT-concept guard (spec §3): compare
            sources only where a concept registry says they are "comparable"; NEVER dock
            confidence for structurally different concepts (tier2 Face vs BS grandfathered).

Phase 2 (NOT built here) = full per-master provenance sidecars emitted by parser/downloader.
This runner only defines the provenance contract it WILL require; see the schema printed by
`--print-provenance-contract` (handed to parser/downloader inbox).

Run:   python scripts/validate_data_contract.py
Self-test (regression suite, spec §5):  python scripts/validate_data_contract.py --selftest

Python full path (env rule): C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe
"""
from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))

try:
    sys.stdout.reconfigure(encoding="utf-8")  # Windows console defaults to cp949
except Exception:
    pass

# Reuse existing validators rather than re-implementing (spec §1 "흡수·통합"):
from validate_kics_disclosure import (  # noqa: E402
    _coverage_census,
    _diversification_negative,
    _item12_equals_item1,
    _parent_present_child_incomplete_after,
    _parent_zero_child_nonzero,
    _post_transition_parent_census,
    _ratio_series_spikes,
    _scan_breakdown_presence,
    _transition_identities_after,
    _transition_mmult_after,
    _transition_ratio_after_capture,
)
from validate_master_tables import coverage_holes, load_long  # noqa: E402
from solvency.validation.kics_json_rules import (  # noqa: E402
    KEY_CODE,
    KEY_QUARTER,
    run_validation as kics_run_validation,
)

QS = ["2023.1Q", "2023.2Q", "2023.3Q", "2023.4Q", "2024.1Q", "2024.2Q", "2024.3Q",
      "2024.4Q", "2025.1Q", "2025.2Q", "2025.3Q", "2025.4Q", "2026.1Q"]


def q_to_num(q: str) -> int:
    """'2025.4Q' -> 20254  (sortable)."""
    m = re.match(r"(\d{4})\.(\d)Q", q or "")
    return int(m.group(1)) * 10 + int(m.group(2)) if m else -1


def _num(v):
    """Parse a K-ICS cell value to float (handles commas, △ / − negatives)."""
    if v is None:
        return None
    try:
        return float(str(v).replace(",", "").replace("△", "-").replace("−", "-").strip())
    except Exception:
        return None


def period_label_to_quarter(period: str | None, as_of: str | None) -> str | None:
    """Map an artifact's stated period/as_of to a K-ICS disclosure quarter.
    'FY2024'+'2024-12-31' -> '2024.4Q'; 'FY2025'+'2025-12-31' -> '2025.4Q'.
    A bare 'FYyyyy' is treated as that year's 4Q (annual filing)."""
    if as_of:
        m = re.match(r"(\d{4})-(\d{2})-\d{2}", as_of)
        if m:
            y = int(m.group(1))
            mo = int(m.group(2))
            qn = (mo - 1) // 3 + 1
            return f"{y}.{qn}Q"
    if period:
        m = re.match(r"FY(\d{4})", period)
        if m:
            return f"{m.group(1)}.4Q"
    return None


# ---------------------------------------------------------------------------
# Finding model
# ---------------------------------------------------------------------------
@dataclass
class Finding:
    check: str          # "census" | "as_of" | "cross_source"
    severity: str       # "RED" | "YELLOW"
    master: str
    company: str | None
    quarter: str | None
    rule: str
    message: str


@dataclass
class GateResult:
    findings: list = field(default_factory=list)
    provisional: bool = False
    notes: list = field(default_factory=list)

    def add(self, **kw):
        self.findings.append(Finding(**kw))

    @property
    def red(self):
        return [f for f in self.findings if f.severity == "RED"]

    @property
    def yellow(self):
        return [f for f in self.findings if f.severity == "YELLOW"]


# ===========================================================================
# CHECK 1 — Completeness census
# ===========================================================================
# owner scope (2026-06-20): the site displays only these 7 quarters. Census RED is scoped to
# them on LIVE data — middle quarters (2023.1-3Q / 2024.1-3Q) are not displayed and their gaps
# (git-purged raw, owner won't backfill) must not block push. NOTE: scope is applied only when
# NOT env.inject, so --selftest keeps full-rigor census over synthetic quarters (7/7 invariant).
_DISPLAY_QUARTERS = {"2023.4Q", "2024.4Q", "2025.1Q", "2025.2Q", "2025.3Q", "2025.4Q", "2026.1Q"}


def _in_scope(q) -> bool:
    """True if q is a display quarter, or not a quarter-form token (None / FY aggregate pass)."""
    s = str(q or "")
    return (s in _DISPLAY_QUARTERS) or (re.match(r"\d{4}\.\dQ", s) is None)


def check_census(res: GateResult, env: "Env") -> None:
    """Expected (filer × quarter × item-block) grid per master. Missing cell / collapsed
    filer count / parent-disclosed-but-children-missing = RED. No exception mechanism — every
    RED counts (fix or owner-escalate, owner 2026-06-16)."""
    def _emit(q) -> bool:                # live: scope to display quarters; selftest: full rigor
        return env.inject or _in_scope(q)
    # --- 1a. K-ICS filer × quarter census (reuse validate_kics_disclosure._coverage_census) ---
    kd_records = env.kics_records
    census = _coverage_census(kd_records)
    for q, c, n in census["missing_rows"]:
        if not _emit(q):
            continue
        res.add(check="census", severity="RED", master="kics_disclosure", company=n, quarter=q,
                rule="MISSING_FILER_CELL",
                message=f"regular filer {n} ({c}) missing in {q} (expected by census grid)")
    for q, n_filers in census["collapsed_quarters"]:
        if not _emit(q):
            continue
        res.add(check="census", severity="RED", master="kics_disclosure", company=None, quarter=q,
                rule="FILER_COUNT_COLLAPSE",
                message=f"{q} has only {n_filers} filers vs median {census['median_filers_per_q']} "
                        f"(gross under-parse — e.g. the 2026.1Q-1-filer incident)")

    # --- 1b. parent-disclosed / children-all-missing & parent-zero / child-nonzero ---
    # (i) structural misparse: parent present & ~0 but a child is non-zero (reuse existing rule)
    for c, q, parent, n, nz in _parent_zero_child_nonzero(kd_records):
        kids = ", ".join(f"item{k}={v}" for k, v in nz)
        res.add(check="census", severity="RED", master="kics_disclosure", company=n, quarter=q,
                rule="PARENT_ZERO_CHILD_NONZERO",
                message=f"parent item{parent}=0 but child {kids} — row misalignment/cell shift")
    # (ii) parent-child completeness (parent disclosed but children stitched-missing) is the
    # 19_market / 36_irr under-parse pattern. The authoritative, CADENCE-AWARE implementation
    # already lives in the K-ICS gate (kics_json_rules.run_validation reads the disclosure MD to
    # distinguish odd-quarter 간이공시 원천부재 from a real parser gap). To avoid duplicate-and-
    # drift (spec §0/§4) we DELEGATE to it and lift only its completeness REDs, rather than re-
    # deriving with a blanket "children all missing" rule (which over-fires on cadence-legit cells).
    if env.delegate_kics:
        kics_report = kics_run_validation(
            kd_records, source_has_breakdown=_scan_breakdown_presence(kd_records))
        for f in kics_report.get("findings", []):
            if f.get("status") != "RED":
                continue
            rule = f.get("rule")
            code = f.get(KEY_CODE)
            q = f.get(KEY_QUARTER)
            if not _emit(q):
                continue
            res.add(check="census", severity="RED", master="kics_disclosure",
                    company=env.code_name.get(code, code), quarter=q,
                    rule=f"KICS_{rule}",
                    message=f"K-ICS rule {rule}: {f.get('detail') or ''} "
                            f"(expected={f.get('expected')} actual={f.get('actual')} "
                            f"diff={f.get('diff')})".strip())

    # --- 1b(iii). 경과조치 적용후 요구자본 부모(15~21) continuity break (owner 2026-07-15 blind spot) ---
    # 부모후가 통째 결측이면 기존 적용후 census/identity/mmult가 전부 skip → false-green (2026.1Q 5사
    # 통과사고). 인접분기에 적용후가 있었는데 당 분기 결측 = 추출갭 → RED. display 분기만 push 차단
    # (git-purge 과거분기 제외, 다른 census와 동일 scope). 22/23 단독 break는 review(비차단)라 여기서 제외.
    post_parent_red, _post_parent_review = _post_transition_parent_census(kd_records)
    for c, q, n, item, nb, kind in post_parent_red:
        if not _emit(q):
            continue
        res.add(check="census", severity="RED", master="kics_disclosure", company=n, quarter=q,
                rule="POST_TRANSITION_PARENT_MISSING",
                message=f"item{item} 값_적용후 missing but present in adjacent quarter {nb} "
                        f"({kind}) — 경과조치 적용사 요구자본 부모 continuity break (추출갭, 구조적 "
                        f"미공시 아님; 부모후 결측이 하위 census/identity를 전부 skip시키던 사각)")

    # --- 1b(iv). K-ICS 경과조치 '적용후' 검증 lift (UH-1, owner 2026-07-21) ---
    # 사고 포스트모템 소급(docs/postmortems)에서 적발: PM-2026-07-07(적용후 전면 미검증)·
    # PM-2026-07-08(V17 가짜복사)의 대응 룰이 validate_kics_disclosure.py의 main()에만 있고
    # **push 차단 경로에 없었다** — prepush_check.py는 그 스크립트를 호출조차 안 하므로 push를 못 막음.
    # 여기서 lift해 display-scope로 차단한다.
    #
    # ⚠️ K-ICS 전용 (owner 2026-07-21): '경과조치'는 K-ICS 고유의 적용전/적용후 이중공시다.
    # IFRS17에는 대응 개념이 없다(전환방법=수정소급/공정가치는 도입시점 측정방법이지 이중컬럼이 아님)
    # → 복사할 짝 자체가 없으므로 IFRS17 유사룰을 만들지 말 것.
    for c, q, n, item, before, after, kind in _transition_ratio_after_capture(kd_records):
        if not _emit(q):
            continue
        res.add(check="census", severity="RED", master="kics_disclosure", company=n, quarter=q,
                rule=f"TRANSITION_AFTER_{kind}",
                message=f"item{item} 적용후={after} 적용전={before} [{kind}] — 선택경과조치 적용사의 "
                        f"적용후 유실/복사/역전/항등식붕괴")
    mmult_mismatch, _mmult_submissing = _transition_mmult_after(kd_records)
    for c, q, n, parent, post_v, computed in mmult_mismatch:
        if not _emit(q):
            continue
        res.add(check="census", severity="RED", master="kics_disclosure", company=n, quarter=q,
                rule="TRANSITION_AFTER_MMULT_MISMATCH",
                message=f"item{parent}후 공시={post_v} ≠ sqrt(세부후·상관행렬)={computed} — 적용후 세부 미정합")
    for c, q, n, rule, exp_after, disc_after, diff in _transition_identities_after(kd_records):
        if not _emit(q):
            continue
        res.add(check="census", severity="RED", master="kics_disclosure", company=n, quarter=q,
                rule="TRANSITION_AFTER_IDENTITY",
                message=f"[{rule}] 공시후={disc_after} 계산후={exp_after} diff={diff} — 적용후 항등식 위반")
    for c, q, parent, n, missing in _parent_present_child_incomplete_after(kd_records):
        if not _emit(q):
            continue
        kids = ", ".join(f"item{k}" for k in missing)
        res.add(check="census", severity="RED", master="kics_disclosure", company=n, quarter=q,
                rule="POST_TRANSITION_CHILD_MISSING",
                message=f"부모 item{parent}후 present인데 {kids}후 결측 — 적용후 부분충전")
    for c, q, n, mode, value, kind in _diversification_negative(kd_records):
        if not _emit(q):
            continue
        res.add(check="census", severity="RED", master="kics_disclosure", company=n, quarter=q,
                rule="DIVERSIFICATION_NEGATIVE",
                message=f"[{mode}] 분산효과 {value} < 0 [{kind}] — 물리적 불가능(구성요소 과소/기준금액 과대)")
    for c, q, n, value in _item12_equals_item1(kd_records):
        if not _emit(q):
            continue
        res.add(check="census", severity="RED", master="kics_disclosure", company=n, quarter=q,
                rule="ITEM12_EQUALS_ITEM1",
                message=f"item12(불인정항목)={value} = item1(지급여력금액) — 셀밀림/미스매핑")
    # 시계열 스파이크는 원 룰 정의대로 YELLOW(비차단 워크리스트) — 휴리스틱이라 단독 push 차단 금지.
    for c, q, n, x, qa, a, qb, b in _ratio_series_spikes(kd_records):
        if not _emit(q):
            continue
        res.add(check="census", severity="YELLOW", master="kics_disclosure", company=n, quarter=q,
                rule="RATIO_SERIES_SPIKE",
                message=f"지급여력비율 {x} (인접 {qa}={a}, {qb}={b}) — 소스오염 의심(비차단, parser 재확인)")

    # --- 1c. IFRS17 long-master holes (reuse validate_master_tables.coverage_holes) ---
    for master, idx, key_items in (
        ("CSM_waterfall", env.wf, ["기초CSM", "신계약CSM", "이자부리", "가정및경험조정", "CSM상각", "기말CSM"]),
        ("PL_breakdown", env.pl, ["보험손익", "생명장기손익", "당기순이익"]),
    ):
        real, _known, _struct = coverage_holes(idx, key_items)
        for co, q, kind in real:
            if not _emit(q):
                continue
            res.add(check="census", severity="RED", master=master, company=co, quarter=q,
                    rule="MASTER_HOLE",
                    message=f"real hole (2024+): {kind} missing for active filer {co}")

    # --- 1d. impossible-0 in IFRS17 (spec §5.4): CSM 상각=0 with positive opening/closing ---
    for co, q, o, c, a in _csm_amort_zero(env.wf):
        if not _emit(q):
            continue
        res.add(check="census", severity="RED", master="CSM_waterfall", company=co, quarter=q,
                rule="IMPOSSIBLE_ZERO_AMORT",
                message=f"CSM상각=0 with opening={o}/closing={c} (impossible — extraction error)")
    # PL 생명장기 leg = 0 (impossible for a long-term insurer) — owner-confirmed legit-zero 제외
    for co, q, item in _pl_impossible_zero_leg(env.pl, _load_owner_confirmed()):
        if not _emit(q):
            continue
        res.add(check="census", severity="RED", master="PL_breakdown", company=co, quarter=q,
                rule="IMPOSSIBLE_ZERO_LEG",
                message=f"{item}=0 (long-term insurer leg cannot be exactly 0 — extraction error)")


def _csm_amort_zero(wf):
    out = []
    for (co, q), m in sorted(wf.items()):
        a, o, c = m.get("CSM상각"), m.get("기초CSM"), m.get("기말CSM")
        endpoints_pos = (o is not None and o > 0) or (c is not None and c > 0)
        if a is not None and a == 0 and endpoints_pos:
            out.append((co, q, o, c, a))
    return out


_PL_IMPOSSIBLE_LEGS = ["생명장기원수손익", "기타생명장기원수손익",
                       "생명장기재보험손익", "기타생명장기재보험손익"]

# owner-verified legit cells (same registry the anomaly skeptic honors,
# triage_anomaly_candidates._load_owner_confirmed). The gate must not RED a value the owner has
# explicitly confirmed correct — e.g. IBK연금보험(순수 연금사)은 재보험이 없어 재보험 leg이 정당하게
# 0이다. Suppression only holds while the master still matches the confirmed value within tol, so a
# later drift to a different value re-surfaces the RED.
_OWNER_CONFIRMED_GOLD = ROOT / "data" / "_gold" / "user_pl_confirmed_cells.json"


def _norm_ws(s) -> str:
    return re.sub(r"\s+", "", str(s or ""))


def _load_owner_confirmed() -> tuple[dict, float, float]:
    if not _OWNER_CONFIRMED_GOLD.exists():
        return {}, 2.0, 0.01
    d = json.loads(_OWNER_CONFIRMED_GOLD.read_text(encoding="utf-8"))
    out = {(c["master"], _norm_ws(c["company"]), str(c["quarter"]), _norm_ws(c["item"])): float(c["value"])
           for c in d.get("cells", [])}
    return out, float(d.get("tolerance_abs", 2.0)), float(d.get("tolerance_rel", 0.01))


def _owner_confirmed(confirmed, master, co, q, item, value) -> bool:
    owner_ok, tol_abs, tol_rel = confirmed
    cval = owner_ok.get((master, _norm_ws(co), str(q), _norm_ws(item)))
    return cval is not None and value is not None and abs(value - cval) <= max(tol_abs, tol_rel * abs(cval))


def _pl_impossible_zero_leg(pl, confirmed=None):
    out = []
    for (co, q), m in sorted(pl.items()):
        if q.startswith("2023."):
            continue
        for k in _PL_IMPOSSIBLE_LEGS:
            if m.get(k) == 0:
                if confirmed and _owner_confirmed(confirmed, "PL_breakdown", co, q, k, 0.0):
                    continue  # owner-confirmed legit-zero (예: 연금사 무재보험) — not an extraction error
                out.append((co, q, k))
    return out


# ===========================================================================
# CHECK 2 — As-of match + effective-list flag
#
# Phase 2 transition (owner 1242Z): CHECK 2 reads a per-master provenance sidecar
# (`<master>_provenance.json`) DIRECTLY when present, instead of inferring as-of from
# existing period/path/quarter fields. The transition is GRACEFUL:
#   - sidecar PRESENT  → strict verification per the provenance contract
#                        (--print-provenance-contract): MISSING_PROVENANCE / STALE_AS_OF /
#                        EFFECTIVE_LIST_NOT_FILTERED.
#   - sidecar ABSENT   → fall back to the Phase-1 inference below (so the gate keeps working
#                        TODAY) + a single informational note per such master.
# END-STATE (once parser/downloader emit sidecars for ALL masters): delete the fallback and
# treat no-sidecar as MISSING_PROVENANCE RED (owner principle 0 — never SKIP-as-pass). Until
# then, no-sidecar must NOT be RED, or the gate would red-out everything before emission exists.
# ===========================================================================
# Authoritative source enum per master (capital-securities effective list → FSC_BONDS).
_CAPITAL_SECURITIES_MASTERS = {"forward_capital", "tier1_utilization", "tier2_utilization"}


def _sidecar_quarter(as_of_date: str | None) -> str | None:
    """Quarter implied by a provenance cell's as_of_date ('2025-12-31' -> '2025.4Q')."""
    return period_label_to_quarter(None, as_of_date)


def verify_provenance_sidecar(res: GateResult, master: str, sidecar: dict,
                              published_cells: list, target_q: str | None) -> None:
    """Strict Phase-2 verification of a master against its provenance sidecar (contract per
    --print-provenance-contract). `published_cells` = the (company, quarter, item_block) tuples
    actually published by this master. Emits:
      - MISSING_PROVENANCE: a published cell has no matching provenance cell, OR a cell's
        source_file does not exist on disk.
      - STALE_AS_OF: as_of_date's quarter != the cell's quarter (or older than target basis).
      - EFFECTIVE_LIST_NOT_FILTERED: capital-securities cell not source_id==FSC_BONDS with
        effective_filtered==true (authoritative-source requirement)."""
    prov = sidecar.get("cells") or []
    # index provenance by (company, quarter, item_block); company keyed by code OR name.
    index = {}
    for c in prov:
        co = c.get("company_code") or c.get("insurer_code") or c.get("company")
        index[(co, c.get("quarter"), c.get("item_block"))] = c
        index[(co, c.get("quarter"), None)] = c  # block-agnostic fallback match

    for (company, quarter, item_block) in published_cells:
        cell = index.get((company, quarter, item_block)) or index.get((company, quarter, None))
        if cell is None:
            res.add(check="as_of", severity="RED", master=master, company=company, quarter=quarter,
                    rule="MISSING_PROVENANCE",
                    message=f"published cell ({company or '-'}, {quarter or '-'}, "
                            f"{item_block or '-'}) has no matching provenance cell (sidecar present "
                            f"→ strict; missing = RED, owner principle 0)")
            continue
        # as_of_date quarter must equal the cell quarter (and not be older than target basis)
        aq = _sidecar_quarter(cell.get("as_of_date"))
        if quarter and aq and aq != quarter:
            res.add(check="as_of", severity="RED", master=master, company=company, quarter=quarter,
                    rule="STALE_AS_OF",
                    message=f"{company or '-'}: provenance as_of_date={cell.get('as_of_date')} "
                            f"(={aq}) != cell quarter {quarter} — stale as-of")
        elif target_q and aq and q_to_num(aq) < q_to_num(target_q):
            res.add(check="as_of", severity="RED", master=master, company=company, quarter=aq,
                    rule="STALE_AS_OF",
                    message=f"{company or '-'}: provenance as_of_date={cell.get('as_of_date')} "
                            f"(={aq}) older than required basis {target_q} — stale baseline")
        # source_file must exist on disk
        sf = cell.get("source_file")
        if not sf or not (ROOT / sf).exists():
            res.add(check="as_of", severity="RED", master=master, company=company, quarter=quarter,
                    rule="MISSING_PROVENANCE",
                    message=f"{company or '-'} {quarter or '-'}: source_file "
                            f"{sf or '(none)'} not found on disk (provenance unverifiable = RED)")
        # capital-securities: authoritative source must be FSC_BONDS w/ effective_filtered==true
        if master in _CAPITAL_SECURITIES_MASTERS:
            if cell.get("source_id") != "FSC_BONDS" or cell.get("effective_filtered") is not True:
                res.add(check="as_of", severity="RED", master=master, company=company,
                        quarter=quarter, rule="EFFECTIVE_LIST_NOT_FILTERED",
                        message=f"{company or '-'} {quarter or '-'}: capital-securities provenance "
                                f"source_id={cell.get('source_id')} effective_filtered="
                                f"{cell.get('effective_filtered')} — must be FSC_BONDS + "
                                f"effective_filtered==true (donut bug guard)")


def check_as_of(res: GateResult, env: "Env") -> None:
    """(a) each published artifact's as_of period must equal its disclosure quarter;
    (c) tier/forward capital-securities must carry evidence that as-of effective filtering
    was applied. Missing evidence = RED (spec §2c, §0).

    Phase 2: per master, if a provenance sidecar EXISTS, verify it strictly; otherwise fall
    back to the Phase-1 inference below and emit one informational note (see header)."""
    latest_q = env.latest_kics_quarter  # the as-of the live site should be rendering
    sidecars = env.provenance_sidecars

    def _fallback_note(master):
        res.notes.append(
            f"provenance sidecar absent for {master} → Phase-1 inference fallback (strict "
            f"no-sidecar=RED activates after Phase 2 emission, owner principle 0)")

    # --- 2a(i). sensitivity_heatmap as_of vs disclosure basis ---
    # Owner V12: heatmap must be on 25.4Q 경영공시 basis. A company still stamped FY2024
    # (as_of 2024-12-31) while the latest disclosure is 2025.4Q is a stale baseline (= RED).
    sh = env.sensitivity_heatmap
    target_q = env.sensitivity_target_quarter  # expected disclosure quarter for the heatmap
    if sidecars.get("sensitivity_heatmap") is not None:
        # Phase 2: strict verify against the sidecar. Published cells = companies w/ scenarios.
        published = [(comp.get("company"),
                      period_label_to_quarter(comp.get("period"), comp.get("as_of")),
                      "sensitivity")
                     for comp in (sh.get("companies", []) if sh else []) if comp.get("scenarios")]
        verify_provenance_sidecar(res, "sensitivity_heatmap",
                                  sidecars["sensitivity_heatmap"], published, target_q)
    elif sh is None:
        res.add(check="as_of", severity="RED", master="sensitivity_heatmap", company=None,
                quarter=None, rule="MISSING_PROVENANCE",
                message="sensitivity_heatmap.json absent — cannot resolve as_of (missing meta = RED)")
    else:
        _fallback_note("sensitivity_heatmap")
        for comp in sh.get("companies", []):
            if not comp.get("scenarios"):
                continue  # no published numbers → not rendered, skip
            name = comp.get("company")
            aq = period_label_to_quarter(comp.get("period"), comp.get("as_of"))
            if aq is None:
                res.add(check="as_of", severity="RED", master="sensitivity_heatmap", company=name,
                        quarter=None, rule="MISSING_AS_OF",
                        message=f"{name}: no resolvable as_of/period (missing meta = RED)")
            elif q_to_num(aq) < q_to_num(target_q):
                res.add(check="as_of", severity="RED", master="sensitivity_heatmap", company=name,
                        quarter=aq, rule="STALE_AS_OF",
                        message=f"{name}: as_of={comp.get('as_of')} (={aq}) is older than the "
                                f"required disclosure basis {target_q} — stale baseline rendered")

    # --- 2a(ii). forward_capital baseline_quarter vs latest K-ICS quarter ---
    # Catches hardcoded BASELINE_QUARTER staleness: a 2025.4Q baseline shown after 2026.1Q exists.
    man = env.forward_manifest
    if sidecars.get("forward_capital") is not None:
        published = [(None, (man or {}).get("baseline_quarter"), "forward_capital")]
        verify_provenance_sidecar(res, "forward_capital",
                                  sidecars["forward_capital"], published, latest_q)
    elif man is None:
        res.add(check="as_of", severity="RED", master="forward_capital", company=None, quarter=None,
                rule="MISSING_PROVENANCE",
                message="forward_capital manifest absent — cannot resolve baseline_quarter (RED)")
    else:
        _fallback_note("forward_capital")
        bq = man.get("baseline_quarter")
        if not bq:
            res.add(check="as_of", severity="RED", master="forward_capital", company=None,
                    quarter=None, rule="MISSING_AS_OF",
                    message="forward_capital manifest has no baseline_quarter (missing meta = RED)")
        elif q_to_num(bq) < q_to_num(latest_q):
            res.add(check="as_of", severity="RED", master="forward_capital", company=None,
                    quarter=bq, rule="STALE_BASELINE",
                    message=f"forward sim baseline_quarter={bq} is older than latest K-ICS "
                            f"quarter {latest_q} — hardcoded stale baseline (BASELINE_QUARTER)")

    # --- 2a(iii). tier utilization quarter vs latest K-ICS quarter ---
    for label, doc in (("tier1_utilization", env.tier1_latest),
                       ("tier2_utilization", env.tier2_latest)):
        if sidecars.get(label) is not None:
            published = [(None, (doc or {}).get("quarter"), label)]
            verify_provenance_sidecar(res, label, sidecars[label], published, latest_q)
            continue
        if doc is None:
            res.add(check="as_of", severity="RED", master=label, company=None, quarter=None,
                    rule="MISSING_PROVENANCE",
                    message=f"{label} latest artifact absent — cannot resolve quarter (RED)")
            continue
        _fallback_note(label)
        tq = doc.get("quarter")
        if not tq:
            res.add(check="as_of", severity="RED", master=label, company=None, quarter=None,
                    rule="MISSING_AS_OF",
                    message=f"{label} artifact has no quarter field (missing meta = RED)")
        elif q_to_num(tq) < q_to_num(latest_q):
            res.add(check="as_of", severity="RED", master=label, company=None, quarter=tq,
                    rule="STALE_AS_OF",
                    message=f"{label} latest is {tq} but latest K-ICS quarter is {latest_q} — stale")

    # --- 2c. effective-list applied evidence (capital-securities) ---
    # The donut bug (spec §5.1): downloader used a stale snapshot WITHOUT filtering to bonds
    # effective (outstanding) as of the baseline. Evidence = bonds carry status/effective_call_date
    # AND only outstanding bonds feed the recognized totals. Absent evidence = RED.
    evid = env.bond_effective_evidence
    if not evid["snapshot_present"]:
        res.add(check="as_of", severity="RED", master="forward_capital", company=None, quarter=None,
                rule="MISSING_EFFECTIVE_LIST",
                message="no normalized bonds snapshot — cannot prove capital-securities effective "
                        "as-of filtering was applied (donut bug guard, missing evidence = RED)")
    else:
        if not evid["has_status_field"] or not evid["has_effective_call_date"]:
            res.add(check="as_of", severity="RED", master="forward_capital", company=None,
                    quarter=None, rule="EFFECTIVE_LIST_NOT_FILTERED",
                    message="bonds snapshot lacks status / effective_call_date fields — effective "
                            "as-of filter cannot be applied (donut bug)")
        elif evid["called_or_matured_in_recognized"]:
            res.add(check="as_of", severity="RED", master="forward_capital", company=None,
                    quarter=None, rule="EFFECTIVE_LIST_NOT_FILTERED",
                    message="recognized/outstanding capital-securities total includes called or "
                            "matured bonds — effective as-of filter NOT applied (donut bug)")


# ===========================================================================
# CHECK 3 — Same-concept cross-source tolerance + DIFFERENT-concept guard
# ===========================================================================
# Concept registry (spec §3): classify which (source_a, source_b) pairs measure the SAME concept
# (comparable → tolerance check) vs structurally DIFFERENT concepts (reference-only → NEVER penalize).
CONCEPT_REGISTRY = {
    # comparable: same economic concept across two sources → tolerance check
    "csm_steps_dart_vs_ir": {
        "kind": "comparable",
        "tol_rel": 0.05, "tol_abs_eok": 100.0,
        "note": "DART CSM waterfall step ↔ IR factsheet same step (opening/new_business/...)",
    },
    # reference-only: DIFFERENT concepts — display side-by-side but NEVER dock confidence
    "tier2_face_vs_bs": {
        "kind": "reference_only",
        "note": "tier2 Face (FSC 채권등록 outstanding) vs BS (K-ICS 경과조치 grandfathered issued) "
                "are structurally different — comparing/penalizing them is forbidden (parser-kics "
                "2026-06-16). Confidence MUST stay decoupled.",
    },
}


def check_cross_source(res: GateResult, env: "Env") -> None:
    """Same-concept tolerance check + the different-concept guard.

    Phase 1 reality: the IR-side formal JSON (data/ir/<period>/parsed/<KR>.json) that powers
    csm_steps_dart_vs_ir is not yet delivered (validation V1 SKIP), so the comparable path emits
    no findings today — but the registry + guard are wired so they activate the moment IR JSON
    lands, and the guard is exercised now (regression #5) to prove tier2 Face↔BS never docks."""
    # --- 3a. comparable: DART↔IR CSM steps (active only when IR parsed JSON present) ---
    ir_dir = ROOT / "data" / "ir"
    reg = CONCEPT_REGISTRY["csm_steps_dart_vs_ir"]
    compared = 0
    for ir_path in ir_dir.glob("*/parsed/*.json") if ir_dir.exists() else []:
        try:
            ir = json.loads(ir_path.read_text(encoding="utf-8"))
        except Exception:
            continue
        kr = ir.get("kr")
        period = ir.get("period")  # e.g. FY2026_Q1
        q = _ir_period_to_quarter(period)
        steps = ir.get("csm_waterfall") or {}
        STEP_MAP = {"opening": "기초CSM", "new_business": "신계약CSM", "interest": "이자부리",
                    "assumption": "가정및경험조정", "amortization": "CSM상각", "closing": "기말CSM"}
        dart = env.wf.get((env.code_name.get(kr, kr), q)) or _wf_by_code(env, kr, q)
        if not dart:
            continue
        for ir_key, wf_key in STEP_MAP.items():
            iv = steps.get(ir_key)
            dv = dart.get(wf_key)
            if iv is None or dv is None:
                continue
            compared += 1
            diff = abs(dv - iv)
            if diff > max(reg["tol_rel"] * abs(iv), reg["tol_abs_eok"]):
                res.add(check="cross_source", severity="RED", master="CSM_waterfall",
                        company=kr, quarter=q, rule="CSM_STEP_DART_VS_IR",
                        message=f"{ir_key}: DART {dv} vs IR {iv} (Δ{dv-iv:+.1f}억 > tol) — same-concept "
                                f"cross-source mismatch")
    res.notes.append(f"cross_source comparable (DART↔IR CSM steps): {compared} step-pairs checked "
                     f"({'IR JSON present' if compared else 'IR parsed JSON absent — SKIP, will activate on delivery'})")

    # --- 3b. DIFFERENT-concept guard: tier2 Face vs BS must NOT dock confidence ---
    # Assert the guard holds on real data: the forward/tier confidence must be decoupled from the
    # tier2 Face-vs-BS gap. If a tier2 Face≠BS gap were (wrongly) forcing low confidence, that's a
    # guard violation → we flag it (so a future regression of the bug is caught). Today it's
    # advisory-only by design (manifest note), so this emits nothing.
    violations = _tier2_concept_guard_violations(env)
    for name, msg in violations:
        res.add(check="cross_source", severity="RED", master="tier2_utilization", company=name,
                quarter=None, rule="WRONG_CONCEPT_PENALTY",
                message=f"{name}: {msg} — tier2 Face↔BS are different concepts; penalizing this "
                        f"comparison is forbidden (guard violation)")
    res.notes.append(f"cross_source guard (tier2 Face↔BS reference-only): {len(violations)} "
                     f"wrong-concept penalties detected (must be 0)")


def _ir_period_to_quarter(period):
    m = re.match(r"FY(\d{4})_Q(\d)", period or "")
    return f"{m.group(1)}.{m.group(2)}Q" if m else None


def _wf_by_code(env, kr, q):
    return env.wf_by_code.get((kr, q))


def _tier2_concept_guard_violations(env):
    """Detect if tier2 Face-vs-BS concept difference is (wrongly) being used to dock confidence.
    The contract (manifest 2026-06-16(a) note): overall confidence = T1 reconciliation only; the
    T2 Face↔BS gap is advisory and must NOT enter overall confidence. We verify forward_capital
    rows: a row whose ONLY confidence-lowering signal is a tier2 Face↔BS gap but is still 'low'
    = guard violation. Phase-1 heuristic: trust the manifest decoupling note; emit only if a
    forward row exposes a concept-based penalty field. Returns [] when the guard holds."""
    rows = env.forward_rows or []
    out = []
    for r in rows:
        # A correctly-decoupled row never carries a 'tier2_face_bs_gap' reason inside its
        # confidence drivers. If a future build re-introduces that coupling, the field would
        # appear in the confidence reasons and we'd catch it here.
        reasons = r.get("confidence_reasons") or r.get("confidence_drivers") or []
        if isinstance(reasons, str):
            reasons = [reasons]
        for why in reasons:
            if isinstance(why, str) and ("t2_face_vs_bs" in why or "tier2_face_bs_gap" in why
                                         or "face_vs_bs" in why):
                out.append((r.get("insurer_name") or r.get("company"),
                            f"confidence lowered by concept-difference reason '{why}'"))
    return out


# ===========================================================================
# CHECK 4 — Domain identity (K-ICS capital recognition-limit 분모/소진율)
# ===========================================================================
def check_domain_identity(res: GateResult, env: "Env") -> None:
    """Domain plausibility identities for K-ICS capital recognition limits.

    Source (owner 2026-06-16, source-verified from research/): K-ICS 해설서 Ⅲ.2.마 p108
    (보완자본 한도 = 총요구자본×50%) · p101 (기본자본 자본증권 인정한도 = SCR×10%, 조건부/신종 15%) ·
    p288 (기본자본의 100%는 *RBC 구제도* 룰이지 K-ICS 아님) · 송미정 [표6]. Two months of live-QA
    misses (KB손보 보완자본 소진율 >100%) → now a hard identity gate.
      R-T2-DENOM: 보완자본 한도(분모) ≈ SCR(item14)×0.5. A denominator near 기본자본(item2) (the RBC
                  rule) = RED.
      R-T2-UTIL : 보완자본 인정한도 소진율 ≤ 100% UNLESS the 경과조치 면제표 (기발행 신종/후순위) was
                  actually parsed. >100% where the 5-2-2 table was NOT parsed (data_source != "table")
                  = inflated numerator = artifact = RED (KB손보 패턴). >100% WITH the table parsed =
                  genuine over-issuance (송미정) → YELLOW (designer shows "100%+").
    """
    doc = env.tier2_latest
    if not doc or not doc.get("results"):
        return  # absence is a CHECK 2 (MISSING_PROVENANCE) concern, not here
    tq = doc.get("quarter")
    scr_by_code = {r.get("원보험사코드"): _num(r.get("값"))
                   for r in env.kics_records
                   if r.get("공시분기") == tq and r.get("항목번호") == 14}
    for row in doc["results"]:
        code = row.get("code")
        name = row.get("company") or code
        limit = row.get("tier2_limit_eok")
        util = row.get("utilization_pct")
        scr = scr_by_code.get(code)
        # R-T2-DENOM: 분모 = SCR×50%, NOT 기본자본
        if limit is not None and scr:
            expected = scr * 0.5
            if abs(limit - expected) > max(0.07 * expected, 100.0):
                res.add(check="domain", severity="RED", master="tier2_utilization",
                        company=name, quarter=tq, rule="T2_DENOM_NOT_SCR_HALF",
                        message=f"보완자본 한도 분모 {limit}억 ≠ SCR×50% {expected:.0f}억 "
                                f"(item14 SCR={scr}억). K-ICS 분모=SCR×50% (해설서 Ⅲ.2.마); "
                                f"기본자본×100%는 RBC 구제도(p288), K-ICS 아님.")
        # R-T2-UTIL: 소진율 >100% only trustworthy if the 면제표 was parsed
        if util is not None and util > 100.0:
            if row.get("data_source") != "table":
                res.add(check="domain", severity="RED", master="tier2_utilization",
                        company=name, quarter=tq, rule="T2_UTIL_OVER_100_NO_EXEMPTION",
                        message=f"보완자본 인정한도 소진율 {util}% >100% 이나 경과조치 면제표(기발행 "
                                f"신종/후순위)가 파싱 안 됨 (data_source={row.get('data_source')}, "
                                f"hybrid={row.get('hybrid_eok')}, sub={row.get('subordinated_eok')}) "
                                f"— 분자가 면제분 못 빼 부풀음 = artifact (KB손보 패턴). 면제표 추출 필요.")
            else:
                res.add(check="domain", severity="YELLOW", master="tier2_utilization",
                        company=name, quarter=tq, rule="T2_UTIL_OVER_100_LEGIT",
                        message=f"보완자본 인정한도 소진율 {util}% >100% (면제표 파싱됨) — genuine "
                                f"over-issuance (송미정); designer display '100%+'.")


# ===========================================================================
# CHECK 5 — Generic anomaly DISCOVERY (metric-AGNOSTIC; no per-metric rules)
# ===========================================================================
def check_generic_anomalies(res: GateResult, env: "Env") -> None:
    """The GENERAL layer (vs CHECK 1–4 which each encode ONE known identity by hand). This
    scanner needs NO per-metric domain knowledge: for every item across the long masters it
    DERIVES the item's normal cohort behaviour from the data itself and flags cells that
    contradict it. This automates the manual 'eyeball every cell' QA — the actual whack-a-mole.
    Output = YELLOW ANOMALY_CANDIDATE (a discovery surface for review), never a hard push block:
    a generic heuristic must not gate a push by itself; it feeds the human/agent triage queue.

    G-COHORT-ZERO  : item nonzero for ≥70% of its cohort but EXACTLY 0 here = candidate miss.
                     (Generalises CHECK 1's hardcoded impossible-0 lists — here 'which items
                     can't be 0' is LEARNED from the data, not coded.)
    G-PEER-OUTLIER : |value| > 50× or < 1/50× the item's cohort median = candidate (NB-multiple
                     0.02 / 240% 류). Coarse on purpose (YELLOW only) to keep noise low.
    """
    import statistics
    for master, long in (("CSM_waterfall", env.wf), ("PL_breakdown", env.pl)):
        by_item: dict = {}
        for (co, q), m in long.items():
            if (q or "").startswith("2023."):  # 2023 known-sparse (site non-disclosure)
                continue
            for item, val in m.items():
                if isinstance(val, (int, float)):
                    by_item.setdefault(item, []).append((co, q, float(val)))
        for item, cells in by_item.items():
            if len(cells) < 8:  # too few to learn a cohort norm
                continue
            vals = [v for _, _, v in cells]
            nz = [v for v in vals if v != 0]
            if not nz:
                continue
            nz_frac = len(nz) / len(vals)
            med = statistics.median([abs(v) for v in nz])
            for co, q, v in cells:
                if v == 0 and nz_frac >= 0.7:
                    res.add(check="anomaly", severity="YELLOW", master=master, company=co,
                            quarter=q, rule="ANOMALY_COHORT_ZERO",
                            message=f"{item}=0 but nonzero for {nz_frac:.0%} of cohort "
                                    f"(median |{med:.0f}|) — candidate extraction-miss "
                                    f"(generic scan: learned, not hardcoded)")
                elif v != 0 and med > 0 and (abs(v) > med * 50 or abs(v) < med / 50):
                    res.add(check="anomaly", severity="YELLOW", master=master, company=co,
                            quarter=q, rule="ANOMALY_PEER_OUTLIER",
                            message=f"{item}={v:.0f} vs cohort median |{med:.0f}| (>50× off) — "
                                    f"candidate outlier (generic scan)")


# ===========================================================================
# Environment loader (real data) + mtime snapshot
# ===========================================================================
class Env:
    """Loads all masters + provenance artifacts and snapshots their mtimes."""

    MASTER_FILES = {
        "kics_disclosure": "kics_disclosure.json",
        "CSM_waterfall": "CSM_waterfall.json",
        "PL_breakdown": "PL_breakdown.json",
        "kics_rate_sensitivity": "kics_rate_sensitivity.json",
        "sensitivity_heatmap": "data/dart/viz/sensitivity_heatmap.json",
        "forward_capital_latest": "templates/forward_capital_latest.json",
    }

    def __init__(self, inject: dict | None = None):
        self.inject = inject or {}
        # delegate K-ICS market/life parent-child completeness to the cadence-aware K-ICS gate.
        # selftest injects minimal synthetic records (only item1) → passes delegate_kics=False.
        self.delegate_kics = self.inject.get("delegate_kics", True)
        self.mtimes_before = self._snapshot_mtimes()

        self.kics_records = self._get("kics_records", lambda: self._load_json("kics_disclosure.json"))
        self.wf = self._get("wf", lambda: load_long("CSM_waterfall.json"))
        self.pl = self._get("pl", lambda: load_long("PL_breakdown.json"))
        self.sensitivity_heatmap = self._get("sensitivity_heatmap",
                                             lambda: self._load_json_opt("data/dart/viz/sensitivity_heatmap.json"))
        self.forward_manifest = self._get("forward_manifest", self._load_forward_manifest)
        self.forward_rows = self._get("forward_rows",
                                      lambda: self._load_json_opt("templates/forward_capital_latest.json") or [])
        self.tier1_latest = self._get("tier1_latest", lambda: self._load_tier("tier1_utilization"))
        self.tier2_latest = self._get("tier2_latest", lambda: self._load_tier("tier2_utilization"))
        self.bond_effective_evidence = self._get("bond_effective_evidence", self._load_bond_evidence)
        self.provenance_sidecars = self._get("provenance_sidecars", self._load_provenance_sidecars)

        # derived
        self.code_name = {r["원보험사코드"]: r["원수사명"] for r in self.kics_records
                          if r.get("원보험사코드")}
        self.wf_by_code = {}
        for (name, q), m in self.wf.items():
            pass  # wf keyed by (원수사명, 공시분기) — build code lookup from records
        self._build_wf_by_code()
        self.latest_kics_quarter = self._latest_quarter(self.kics_records)
        # sensitivity heatmap target = the disclosure quarter the heatmap SHOULD be on.
        # Owner V12 anchored it to the 25.4Q 경영공시 basis. Use the latest sensitivity-bearing
        # K-ICS rate-sensitivity quarter as the authoritative disclosure basis (data-driven).
        self.sensitivity_target_quarter = self._sensitivity_target()

    # ---- injection-aware loaders (selftest overrides these) ----
    def _get(self, key, loader):
        return self.inject[key] if key in self.inject else loader()

    def _load_json(self, rel):
        return json.loads((ROOT / rel).read_text(encoding="utf-8"))

    def _load_json_opt(self, rel):
        p = ROOT / rel
        if not p.exists():
            return None
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            return None

    def _load_provenance_sidecars(self):
        """Phase 2 provenance 사이드카 로드: 마스터별 `<master>_provenance.json` (있으면 dict, 없으면 None
        → check_as_of가 Phase-1 추론 fallback). emission 전이면 전부 None. selftest(inject 모드)는
        합성데이터라 디스크 사이드카 무시(빈 dict)."""
        if self.inject:
            return {}
        out = {}
        for master, rel in self.MASTER_FILES.items():
            side = (rel[:-5] if rel.endswith(".json") else rel) + "_provenance.json"
            out[master] = self._load_json_opt(side)
        return out

    def _load_forward_manifest(self):
        base = ROOT / "output" / "kics_forward_capital"
        if not base.exists():
            return None
        dirs = sorted([d for d in base.iterdir() if d.is_dir()])
        for d in reversed(dirs):
            man = d / "manifest.json"
            if man.exists():
                try:
                    return json.loads(man.read_text(encoding="utf-8"))
                except Exception:
                    return None
        return None

    def _load_tier(self, sub):
        base = ROOT / "output" / sub
        if not base.exists():
            return None
        files = sorted(base.glob(f"{sub}_*.json"))
        if not files:
            return None
        # latest by embedded quarter token (…_20261Q.json sorts after …_20254Q.json)
        try:
            return json.loads(files[-1].read_text(encoding="utf-8"))
        except Exception:
            return None

    def _load_bond_evidence(self):
        """Evidence that capital-securities effective as-of filtering was applied.
        snapshot_present + status/effective_call_date fields + no called/matured bond counted in
        the outstanding totals (the donut-bug guard)."""
        base = ROOT / "data" / "bonds" / "normalized"
        ev = {"snapshot_present": False, "has_status_field": False,
              "has_effective_call_date": False, "called_or_matured_in_recognized": False}
        if not base.exists():
            return ev
        dirs = sorted([d for d in base.iterdir() if d.is_dir()])
        if not dirs:
            return ev
        bi = dirs[-1] / "bonds_by_insurer.json"
        if not bi.exists():
            return ev
        try:
            doc = json.loads(bi.read_text(encoding="utf-8"))
        except Exception:
            return ev
        ev["snapshot_present"] = True
        for grp in doc.values():
            for b in (grp.get("bonds") or []):
                if "status" in b:
                    ev["has_status_field"] = True
                if "effective_call_date" in b:
                    ev["has_effective_call_date"] = True
            # outstanding total reconciliation: the snapshot exposes per-insurer outstanding
            # sums; if those sums silently include non-outstanding bonds, the effective filter
            # was not applied. Verify amount_outstanding_won == Σ(status==outstanding amounts).
            outs = [b for b in (grp.get("bonds") or []) if b.get("status") == "outstanding"]
            declared = grp.get("amount_outstanding_won")
            if declared is not None:
                recomputed = sum(b.get("issue_amount_won") or 0 for b in outs)
                # if a called/matured bond's amount leaked into the declared outstanding total
                if recomputed != declared and abs(recomputed - declared) > 0:
                    # only a problem if the discrepancy is explained by non-outstanding bonds
                    all_total = sum(b.get("issue_amount_won") or 0 for b in (grp.get("bonds") or []))
                    if declared > recomputed and declared <= all_total:
                        ev["called_or_matured_in_recognized"] = True
        return ev

    def _build_wf_by_code(self):
        # CSM_waterfall rows carry 원보험사코드; load_long keys by 원수사명 — build code-keyed too.
        try:
            rows = self._load_json("CSM_waterfall.json")
        except Exception:
            rows = []
        from validate_master_tables import norm
        idx = {}
        for r in rows:
            idx.setdefault((r.get("원보험사코드"), r.get("공시분기")), {})[norm(r.get("항목명"))] = r.get("값")
        self.wf_by_code = idx

    @staticmethod
    def _latest_quarter(records):
        qs = {r.get("공시분기") for r in records if r.get("공시분기")}
        return max(qs, key=q_to_num) if qs else None

    def _sensitivity_target(self):
        rs = self._load_json_opt("kics_rate_sensitivity.json") or []
        qs = {r.get("공시분기") for r in rs if r.get("공시분기")}
        return max(qs, key=q_to_num) if qs else self.latest_kics_quarter

    def _snapshot_mtimes(self):
        out = {}
        for label, rel in self.MASTER_FILES.items():
            p = ROOT / rel
            out[label] = p.stat().st_mtime if p.exists() else None
        return out

    def check_concurrent_backfill(self):
        for label, rel in self.MASTER_FILES.items():
            p = ROOT / rel
            now = p.stat().st_mtime if p.exists() else None
            if now != self.mtimes_before.get(label):
                return True
        return False


# ===========================================================================
# Runner
# ===========================================================================
def run_gate(env: Env) -> GateResult:
    res = GateResult()
    check_census(res, env)
    check_as_of(res, env)
    check_cross_source(res, env)
    check_domain_identity(res, env)
    check_generic_anomalies(res, env)
    res.provisional = env.check_concurrent_backfill()
    return res


def print_report(res: GateResult) -> None:
    print("#" * 78)
    print("DATA CONTRACT GATE — Phase 1  (census + as-of/effective + cross-source guard)")
    if res.provisional:
        print("⚠️  PROVISIONAL: a master changed mtime during this run (concurrent backfill).")
    print("#" * 78)

    by_check = {"census": [], "as_of": [], "cross_source": [], "domain": [], "anomaly": []}
    for f in res.findings:
        by_check.setdefault(f.check, []).append(f)

    titles = {
        "census": "1. COMPLETENESS CENSUS (missing cell / parent-child / impossible-0)",
        "as_of": "2. AS-OF MATCH + EFFECTIVE-LIST (stale baseline / donut bug)",
        "cross_source": "3. CROSS-SOURCE same-concept tolerance + different-concept guard",
        "domain": "4. DOMAIN IDENTITY (capital recognition-limit 분모=SCR×50% / 소진율≤100%)",
        "anomaly": "5. GENERIC ANOMALY DISCOVERY (metric-agnostic; learned from cohort)",
    }
    for check in ("census", "as_of", "cross_source", "domain", "anomaly"):
        items = by_check.get(check, [])
        red = [f for f in items if f.severity == "RED"]
        yel = [f for f in items if f.severity == "YELLOW"]
        print("=" * 78)
        print(f"{titles[check]}   RED={len(red)} YELLOW={len(yel)}")
        print("=" * 78)
        # CHECK 5 (anomaly) is a high-recall/low-precision DISCOVERY queue — summarize, don't dump.
        shown = items[:6] if check == "anomaly" else items
        for f in shown:
            cq = f"{f.company or '-'} {f.quarter or '-'}"
            print(f"  {f.severity:6s} [{f.master}] {f.rule}  {cq}")
            print(f"         {f.message}")
        if check == "anomaly" and len(items) > len(shown):
            from collections import Counter
            by_rule = Counter(f.rule for f in items)
            print(f"  ...+{len(items) - len(shown)} more candidates (triage queue, not blocking). "
                  f"breakdown: {dict(by_rule)}")
        if not items:
            print("  (clean)")

    if res.notes:
        print("-" * 78)
        print("notes:")
        for n in res.notes:
            print(f"  - {n}")

    print("#" * 78)
    print(f"SUMMARY  RED={len(res.red)}  YELLOW={len(res.yellow)}  "
          f"provisional={res.provisional}")
    print("#" * 78)


PROVENANCE_CONTRACT = """\
PHASE 2 PROVENANCE CONTRACT (validation → parser/downloader)
============================================================
Goal: every published metric must resolve to (source_id, as_of_date, source_file) so the
data-contract gate's CHECK 2 (as-of/effective) can verify provenance from emitted metadata
instead of inferring it from period/path/flags. Recommendation: one sidecar per master
(cell schema unchanged) at the path shown.

For EACH master, emit a sidecar JSON `<master>_provenance.json`:

  {
    "master": "<master_name>",                 # kics_disclosure | CSM_waterfall | PL_breakdown |
                                                #   kics_rate_sensitivity | tier1_utilization |
                                                #   tier2_utilization | forward_capital |
                                                #   sensitivity_heatmap
    "generated_at": "20260616T1200Z",          # ISO8601-basic UTC of emission
    "cells": [
      {
        "company_code": "KR0008",              # 원보험사코드 (or insurer_code)
        "quarter": "2025.4Q",                  # disclosure quarter the value belongs to
        "item_block": "market_subrisk|csm_waterfall|...",  # logical block (optional, per master)
        "source_id": "DART|FSC_BONDS|KIDI|DISCLOSURE_MD|IR_FACTSHEET",  # authoritative source enum
        "as_of_date": "2025-12-31",            # ISO date the SOURCE figure is effective as of
        "source_file": "data/dart/FY2025_Q4/raw/KR0008_...xml",  # repo-relative provenance path
        "effective_filtered": true             # capital-securities ONLY: as-of effective (call/
                                               #   maturity) filter actually applied to the list
      }
    ]
  }

Hard requirements the gate enforces (Phase 2):
  - as_of_date's quarter MUST equal `quarter` (else STALE_AS_OF RED).
  - source_id MUST be the authoritative source for that metric (e.g. capital-securities effective
    list → source_id == "FSC_BONDS" with effective_filtered == true; else MISSING_EFFECTIVE_LIST /
    EFFECTIVE_LIST_NOT_FILTERED RED).
  - A published (company, quarter, item_block) with NO matching provenance cell = MISSING_PROVENANCE
    RED (never SKIP-as-pass, spec §0).
  - source_file MUST exist on disk (else MISSING_PROVENANCE RED).

Routing: downloader owns source_file + as_of_date + effective_filtered for fetched artifacts
(bonds, DART raw); parser owns source_id + item_block mapping when it writes the master.
"""


def main(argv=None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    if "--print-provenance-contract" in argv:
        print(PROVENANCE_CONTRACT)
        return 0
    if "--selftest" in argv:
        from _data_contract_selftest import run_selftest
        return run_selftest()
    env = Env()
    res = run_gate(env)
    print_report(res)
    # No exception mechanism (owner 2026-06-16): every RED blocks. Fix or owner-escalate.
    return 2 if res.red else 0


if __name__ == "__main__":
    raise SystemExit(main())
