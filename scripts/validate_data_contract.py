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

import datetime as _dt
import itertools
import json
import re
import statistics
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
    _absence_pin_census,
    _axis_eval_findings,
    _axis_evaluation_census,
    _axis_mirror_findings,
    _coverage_census,
    _diversification_negative,
    _exemption_provenance_findings,
    _exemption_registries,
    _item12_equals_item1,
    _life8_issuer_inconsistent,
    _load_exemption_ledger,
    _other_capital_children_sum,
    _parent_present_child_incomplete_after,
    _parent_zero_child_nonzero,
    _pin_ledger_agreement_findings,
    _post_transition_parent_census,
    _ratio_series_spikes,
    _scan_breakdown_presence,
    _source_readability,
    _tier2_issuer_inconsistent,
    _transition_identities_after,
    _transition_irr_after,
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


SOURCE_VISION_LEDGER = ROOT / "data" / "_gold" / "kics_source_vision_verified.json"

# 원장이 반드시 갖춰야 하는 필드. 하나라도 비면 `SOURCE_VISION_RECORD_INCOMPLETE` RED —
# "누군가 확인했다" 는 산문과 같다(`EXEMPTION_OWNER_RECORD_INCOMPLETE` 와 같은 잣대).
SOURCE_VISION_REQUIRED = ("company", "quarter", "claim", "method", "read_by", "read_date",
                          "pdf", "pages_0idx", "printed_quote", "pinned_cells")


def _load_source_vision_ledger():
    """`data/_gold/kics_source_vision_verified.json` → dict 또는 None.

    없거나 안 읽히면 None = '등재 없음'. 그러면 해당 축이 종전대로 YELLOW 를 낸다 —
    **파일이 사라졌다고 조용히 통과하지 않는다.** 사이드카 stale 사고의 반대 방향 방어다."""
    try:
        return json.loads(SOURCE_VISION_LEDGER.read_text(encoding="utf-8"))
    except Exception:
        return None


def _source_vision_index(ledger) -> dict:
    """(company, quarter) -> entry. 원장이 없으면 빈 dict."""
    if not isinstance(ledger, dict):
        return {}
    out = {}
    for e in ledger.get("entries") or []:
        if isinstance(e, dict) and e.get("company") and e.get("quarter"):
            out[(e["company"], e["quarter"])] = e
    return out


def _source_vision_findings(entry: dict, kd_records: list, parent, tag: str):
    """등재된 육안판독 근거 하나를 **매 실행 재검산**한다 → [(severity, rule, message)].

    통째 skip 이 아니다. 네 가지를 다시 건다:

      ① 필수 필드      비면 `SOURCE_VISION_RECORD_INCOMPLETE` **RED**.
      ② 결측           박제 셀이 마스터에서 사라지면 `SOURCE_VISION_INPUT_MISSING` **RED**
                       (결측은 SKIP 이 아니다).
      ③ 주장 재검산    등재 주장은 "경과조치 미적용 → 전 항목 적용후=적용전" 이다. 박제한
                       항목 중 하나라도 `값 != 값_적용후` 면 `SOURCE_VISION_CLAIM_REFUTED`
                       **RED** — 판독 결과가 데이터와 어긋난다.
      ④ 값 드리프트    주장은 서 있는데 박제값이 움직였으면 `SOURCE_VISION_PIN_DRIFT` YELLOW.
                       판독은 그때의 숫자에 대해 한 것이라 다시 봐야 하지만, 주장 자체가
                       깨진 것은 아니므로 차단하지 않는다(원래 이 축이 YELLOW 였다).

    전부 통과하면 `SOURCE_VISION_VERIFIED` YELLOW(review) 로 **매 실행 인쇄한다.** 조용해지면
    다음 세션이 이 칸을 '검사된 칸' 으로 오독한다. 판독 깊이(`reproduced_by_sender`)도 같이
    찍는다 — parser 판독만 있는 것과 원 sender 가 재현한 것은 강도가 다르다.
    """
    missing_fields = [f for f in SOURCE_VISION_REQUIRED if not entry.get(f)]
    if missing_fields:
        return [("RED", "SOURCE_VISION_RECORD_INCOMPLETE",
                 f"item{parent}후 육안판독 등재인데 필수 필드 {missing_fields} 가 비었다 — "
                 "판독자·판독일·본 페이지·인쇄된 문구가 없으면 '누군가 확인했다' 는 산문과 같다")]

    code, quarter = entry["company"], entry["quarter"]
    live = {}
    for r in kd_records:
        if r.get("원보험사코드") != code or r.get("공시분기") != quarter:
            continue
        try:
            live[str(int(r.get("항목번호")))] = (r.get("값"), r.get("값_적용후"))
        except (TypeError, ValueError):
            continue

    absent, refuted, drifted = [], [], []
    for item, pin in (entry.get("pinned_cells") or {}).items():
        cur = live.get(str(item))
        if cur is None:
            absent.append(item)
            continue
        pre, post = cur
        if str(pre) != str(post):
            refuted.append(f"item{item} 전={pre!r} 후={post!r}")
        if str(pre) != str(pin.get("값")) or str(post) != str(pin.get("값_적용후")):
            drifted.append(f"item{item} 박제={pin.get('값')!r} 실측={pre!r}")

    out = []
    if absent:
        out.append(("RED", "SOURCE_VISION_INPUT_MISSING",
                    f"item{parent}후 육안판독 등재의 박제 셀 item{absent} 이 마스터에서 사라졌다 "
                    "— 결측은 SKIP 이 아니다. 판독 근거가 가리키는 값이 없으면 등재는 무효다"))
    if refuted:
        out.append(("RED", "SOURCE_VISION_CLAIM_REFUTED",
                    f"item{parent}후 육안판독 등재의 주장('경과조치 미적용 → 적용후=적용전')이 "
                    f"마스터와 어긋난다: {', '.join(refuted)}. 판독이 틀렸거나 데이터가 바뀐 것이다"))
    if drifted:
        out.append(("YELLOW", "SOURCE_VISION_PIN_DRIFT",
                    f"item{parent}후 육안판독 등재의 박제값이 움직였다: {', '.join(drifted)}. "
                    "주장(전=후)은 아직 서 있으나 판독은 옛 숫자에 대해 한 것이라 재판독 대상이다"))
    if out:
        return out
    return [("YELLOW", "SOURCE_VISION_VERIFIED",
             f"item{parent}후 세부결측(후=전) — raw 텍스트레이어 {tag} 이지만 "
             f"**육안 판독으로 판정 완료**. 판독자={entry['read_by']} 판독일={entry['read_date']} "
             f"sender재현={entry.get('reproduced_by_sender', '?')} "
             f"{entry['pdf']} p{entry['pages_0idx']}(0-idx) — "
             f"인쇄된 문구: {str(entry['printed_quote'])[:180]}")]


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


def _quarter_end_date(q: str | None) -> _dt.date | None:
    """'2026.1Q' -> date(2026, 3, 31)."""
    m = re.match(r"(\d{4})\.(\d)Q", str(q or ""))
    if not m:
        return None
    y, qn = int(m.group(1)), int(m.group(2))
    mo = qn * 3
    return _dt.date(y, mo, {3: 31, 6: 30, 9: 30, 12: 31}[mo])


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
        kics_findings = kics_report.get("findings", [])
        # documented exception 도 **같이 위임한다.** 룰만 위임하고 면제를 안 위임하면 두 게이트가
        # 같은 finding 을 놓고 서로 다른 대답을 한다 — K-ICS 게이트는 '차단 안 함', 여기서는
        # '차단' 이 되어 등재가 조용히 무효가 되고, 다음 사람은 그 불일치를 다른 곳을 넓혀서
        # 푼다. **재구현하지 않고 같은 함수를 부른다**(위 §1b(ii) 의 duplicate-and-drift 회피와
        # 같은 이유): 면제 재검산이 두 벌이 되는 순간 한쪽만 깨지는 경로가 생긴다.
        # 면제가 깨져 있으면(`tier2_exempt_red`) 그것 자체가 아래에서 RED 로 나간다 — 즉 여기서
        # 빠지는 것은 '매 실행 재검산에 통과한 면제' 뿐이다.
        tier2_exempt, tier2_exempt_red, _t2_review, _t2_detail = _tier2_issuer_inconsistent(
            kd_records, kics_findings)
        life8_ok, life8_exempt_red, _l8_review, _l8_detail = _life8_issuer_inconsistent(kd_records)
        exempt_ids = {id(f) for f in tier2_exempt}
        exempt_ids |= {id(f) for f in kics_findings
                       if f.get("status") == "RED" and str(f.get("rule")) == "8_life"
                       and (f.get(KEY_CODE), f.get(KEY_QUARTER)) in life8_ok}
        for f in tier2_exempt_red + life8_exempt_red:
            res.add(check="census", severity="RED", master="kics_disclosure",
                    company=env.code_name.get(f.get("code"), f.get("code")),
                    quarter=f.get("quarter"), rule=f"KICS_{f.get('rule')}",
                    message=f"documented exception 재검산 실패: {f.get('detail')}")
        for f in kics_findings:
            if f.get("status") != "RED":
                continue
            if id(f) in exempt_ids:
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
    post_parent_red, _post_parent_review, _post_parent_pinned =         _post_transition_parent_census(kd_records)
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
    # 2026-08-21: 아래 3개는 **전사 39사 × 적용후** 로 확대됐다(종전 적용사 18사 한정 = 비-applier
    # 21사의 적용후 8,914셀이 통째로 미검사 = false-green). mmult 는 축 15(기본요구자본 R4)도 추가.
    # 반환 3/2-튜플의 마지막 원소는 '계산불가 명시집계'라 차단엔 안 쓰되 리포트엔 남긴다.
    mmult_mismatch, _mmult_submissing, _mmult_skipped, mmult_unverifiable = \
        _transition_mmult_after(kd_records, env.source_readability)
    for c, q, n, parent, post_v, computed in mmult_mismatch:
        if not _emit(q):
            continue
        res.add(check="census", severity="RED", master="kics_disclosure", company=n, quarter=q,
                rule="TRANSITION_AFTER_MMULT_MISMATCH",
                message=f"item{parent}후 공시={post_v} ≠ sqrt(세부후·상관행렬)={computed} — 적용후 세부 미정합")
    # 2026-08-21 ④: '적용후 세부결측(후=전)' 중 **원천이 스캔본이라 판정 자체가 불가능한** 칸.
    # 종전엔 이 칸들이 "구조적으로 정당" 버킷에 섞여 정당 카운트를 부풀렸다 — 확인한 게 아니라
    # 못 읽은 것이다. 결함이라고 단정할 근거도 없으므로 차단은 안 하되(YELLOW) 별도 카테고리로
    # 세어 OCR/재수집 워크리스트가 되게 한다.
    # 2026-08-24: 이 20칸 중 상당수는 **이미 육안으로 판정이 끝났다**(폰트 유니코드 매핑 실패라
    # 렌더링하면 읽힌다). 판정을 게이트에 안 넣으면 같은 YELLOW 20줄이 매 라운드 반복되고
    # 아무도 안 보게 되며, 나중에 진짜 미판독 칸이 그 사이에 섞여도 안 보인다. 그래서 근거
    # 원장(`data/_gold/kics_source_vision_verified.json`)을 두고 **매 실행 재검산**한다 —
    # 조용히 지우는 것이 아니다. 선례: `EXEMPTION_VERIFIED_BY_IMAGE_ONLY`(KR0079 2023.2Q).
    _vision = _source_vision_index(env.source_vision_ledger)
    _vision_hit: set = set()
    for c, q, n, parent, tag in mmult_unverifiable:
        if not _emit(q):
            continue
        entry = _vision.get((c, q))
        if entry is None:
            res.add(check="census", severity="YELLOW", master="kics_disclosure",
                    company=n, quarter=q, rule="SOURCE_UNREADABLE_NOT_VERIFIED",
                    message=f"item{parent}후 세부결측(후=전)인데 raw 텍스트레이어 {tag} — "
                            f"'전=후라 정당'이 아니라 **판정 불가**(OCR/재수집 전까지 미검증)")
            continue
        _vision_hit.add((c, q))
        for sev, rule, msg in _source_vision_findings(entry, kd_records, parent, tag):
            res.add(check="census", severity=sev, master="kics_disclosure",
                    company=n, quarter=q, rule=rule, message=msg)
    # 등재했는데 그 축이 더 이상 미판독을 안 내면 죽은 핀이다 — 조용히 두면 다음 세션이
    # "그 칸은 검증돼 있다" 로 잘못 읽는다(면제 레지스트리의 `..._INERT` 와 같은 장치).
    for key, entry in sorted(_vision.items()):
        if key in _vision_hit or not _emit(key[1]):
            continue
        res.add(check="census", severity="YELLOW", master="kics_disclosure",
                company=env.code_name.get(key[0], key[0]), quarter=key[1],
                rule="SOURCE_VISION_INERT",
                message="육안판독 근거를 등재했는데 이 (회사,분기)가 더 이상 "
                        "SOURCE_UNREADABLE_NOT_VERIFIED 를 내지 않는다 — 원천이 판독 가능해졌거나 "
                        "세부가 적재됐다. 등재를 풀어라(죽은 핀)")
    _ident_after, _ident_skipped = _transition_identities_after(kd_records)
    for c, q, n, rule, exp_after, disc_after, diff in _ident_after:
        if not _emit(q):
            continue
        res.add(check="census", severity="RED", master="kics_disclosure", company=n, quarter=q,
                rule="TRANSITION_AFTER_IDENTITY",
                message=f"[{rule}] 공시후={disc_after} 계산후={exp_after} diff={diff} — 적용후 항등식 위반")
    _irr_after, _irr_skipped = _transition_irr_after(kd_records)
    for c, q, n, disc_after, exp_after in _irr_after:
        if not _emit(q):
            continue
        res.add(check="census", severity="RED", master="kics_disclosure", company=n, quarter=q,
                rule="TRANSITION_AFTER_IRR_MISMATCH",
                message=f"item36후 공시={disc_after} ≠ 시나리오후(41-46) 도출={exp_after} — 적용후 금리위험 미정합")
    # 2026-08-21: item23 = item24+25+26 (기타 요구자본 분해). 24/25/26 은 **어떤 항등식도 참조하지
    # 않던 항목**이라 셀이 있어도 값은 아무도 안 봤다. K-ICS 게이트에만 걸면 prepush 경로 밖이라
    # (prepush_check.py 는 validate_kics_disclosure.py 를 호출하지 않는다) 여기서 같이 건다.
    # 적용전·적용후 양 컬럼을 한 함수가 본다 — 적용후가 검증사각이었던 전례(PM-2026-07-07).
    _other_cap, _other_cap_skipped = _other_capital_children_sum(kd_records)
    for c, q, n, col, disclosed, expected, kids in _other_cap:
        if not _emit(q):
            continue
        res.add(check="census", severity="RED", master="kics_disclosure", company=n, quarter=q,
                rule="OTHER_CAPITAL_CHILDREN_SUM",
                message=f"[{col}] item23(기타 요구자본)={disclosed} ≠ item24+25+26={expected} "
                        f"{list(kids)} — 원문 라벨이 선언한 합(1+2+3)이 안 닫힘")
    _after_incomplete, _after_pinned_absent = _parent_present_child_incomplete_after(kd_records)
    for c, q, parent, n, missing in _after_incomplete:
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

    # --- 1b(v). 메타룰: 축이 '돌았는가' 가 아니라 '판정했는가' (owner 2026-08-21) ---
    # 어느 축도 평가율을 방출하지 않아서, 그리드의 21%만 판정하는 축이 `FAIL 0` 한 줄로 통과처럼
    # 읽혔다. 실질 평가 0칸인 축은 이 저장소가 이미 RED 로 다루는 '검사축 소실'
    # (CAPSEC_SOURCE_UNRESOLVED · DIV_CENSUS_SOURCE_MISSING)과 같은 부류다.
    # 축 단위 finding 이라 quarter 가 없다 → display-scope 필터를 타지 않고 항상 방출된다(의도).
    #
    # ⚠️ 2026-08-21 (f) 정정: 처음엔 "적용후 입력이 적용전과 전부 동일 = 동어반복" 이라 보고 미러를
    # 통째로 실질평가에서 뺐다가 `36_irr 적용후`·`R2 적용후` 를 잘못 RED 로 올렸다.
    # **경과조치 미적용사에게 후 = 전은 정의상 참**이다(적용사 미러 실측 0건) — 정의를 결함으로
    # 뒤집어 읽은 것이다. 이제 미러의 결함성은 `AXIS_SELF_MIRRORED_APPLIER` 가 **적용사 + 그 축을
    # 움직이는 종류를 실제 신청한 경우에만** 판정한다.
    _axis_census = _axis_evaluation_census(kd_records)
    axis_red, axis_review = _axis_eval_findings(_axis_census)
    for f in _axis_mirror_findings(_axis_census):
        if not _emit(f["quarter"]):
            continue
        res.add(check="census", severity="RED", master="kics_disclosure",
                company=env.code_name.get(f["code"], f["code"]), quarter=f["quarter"],
                rule="AXIS_SELF_MIRRORED_APPLIER",
                message=f"{f['axis']}[{f['column']}] — 경과조치 {f['kinds']} 신청사인데 적용후가 "
                        f"적용전과 한 자리도 다르지 않다(대상+전 입력 수치 동일) = 적용후 컬럼 복사 지문")
    for r in axis_red:
        why = ("계산된 칸이 전부 적용사 미러링 오염"
               if r["mirror_applier_suspect"] and r["mirror_applier_suspect"] == r["evaluated"]
               else "계산가능 칸이 0")
        res.add(check="census", severity="RED", master="kics_disclosure", company=None, quarter=None,
                rule="AXIS_NOT_EVALUATED",
                message=f"{r['axis']} [{r['column']}] grid={r['grid']} 평가={r['evaluated']} "
                        f"오염의심={r['mirror_applier_suspect']} 실질=0 — {why}. 이 축의 'FAIL 0' 은 "
                        f"증거가 아니다 (해소: 원천을 채우거나 owner 가 축 면제를 등재)")
    for r in axis_review:
        res.add(check="census", severity="YELLOW", master="kics_disclosure", company=None,
                quarter=None, rule="AXIS_EVAL_RATE_LOW",
                message=f"{r['axis']} [{r['column']}] 평가 {r['evaluated']}칸 = 축그리드 "
                        f"{100*r['rate']:.1f}% / 전버킷 {100*r['rate_all']:.1f}% "
                        f"(바닥: {r['low_on']}) — 'FAIL 0' 이 그리드 절반도 설명하지 못한다")

    # --- 1b(vi). 메타룰: 면제 근거(provenance) ---
    # 면제 2건이 '(raw 정독 확인)' 을 근거로 달고 있었는데 raw 에는 표가 멀쩡히 있었다(실제로 본 건
    # docling MD). 근거가 검증 불가능한 산문이면 아무도 반박할 수 없다 → 모든 면제는 기계가 열어볼
    # 수 있는 인용을 들어야 하고, 없으면 그 사실 자체가 finding 이다. 특히 **레지스트리엔 있는데
    # 원장에 기록조차 없는 항목은 RED** — 새 면제를 조용히 추가하는 경로를 즉시 막는다.
    exempt_red, exempt_review = _exemption_provenance_findings(
        env.exemption_registries, env.exemption_ledger)
    # --- 1b(vi-b). 부재형 면제의 **셀 단위 부재 박제** + 원장↔코드 박제 대조 (2026-08-24) ---
    # 종전 부재형 면제는 `(회사,분기)` 통째로 축을 순회에서 뺐다. 그 사각에서 하나생명 2024.4Q 의
    # item33후·item34후가 직전분기 값 복사(stale)로 앉아 있었고, 그 4셀을 정정 전 값으로 되돌린
    # 마스터로 게이트를 돌려도 출력이 **바이트 동일**했다 = 값이 바뀌어도 게이트가 모른다.
    # → 면제는 축을 빼는 방식이 아니라 **셀 단위 부재 박제**로만 걸리고, 박제 그룹이 부분충전이면
    #   RED 다(섞인 상태는 항등식을 입력결측 SKIP 으로 만들어 채워진 값이 무검사가 된다).
    # 그리고 원장 `expected_residual`/`absent_cells` 는 코드 박제의 사본이라 어긋나면 RED —
    # 그 전까지 원장 숫자를 읽는 코드가 하나도 없어서 원장은 장식이었다.
    # **여기에 lift 하는 이유**: `prepush_check.py` 는 이 게이트를 부르고 `validate_kics_disclosure.py`
    # 도 부르지만, 차단 회계의 정본은 이 파일이다(문서에 mandatory 라고 쓰는 것은 강제가 아니다).
    _absence_detail, absence_red, absence_review = _absence_pin_census(
        kd_records, env.absence_pins)
    exempt_red = exempt_red + absence_red + _pin_ledger_agreement_findings(
        env.exemption_ledger, code_pins=env.code_pins)
    exempt_review = exempt_review + absence_review
    for f in exempt_red:
        res.add(check="census", severity="RED", master="kics_disclosure",
                company=f.get("code"), quarter=f.get("quarter"), rule=f["rule"],
                message=f"[{f['registry']}] {f['detail']}")
    for f in exempt_review:
        res.add(check="census", severity="YELLOW", master="kics_disclosure",
                company=f.get("code"), quarter=f.get("quarter"), rule=f["rule"],
                message=f"[{f['registry']}] {f['detail']}")

    # --- 1e. capital-securities 커버리지 census (owner 20260803T0310Z) ---
    # 라벨 계보(20260803T0056Z)는 "틀린 소스라고 말하는 것"을 막았지만, **소스가 통째로 비어도**
    # 게이트는 RED=0이었다: DART annual raw가 없는 2사의 채권이 마스터에서 사라져 상환차감이 없어지고
    # 2030 지급여력비율이 실제보다 좋게(iM라이프 93.65%→152.12%, 권고선 아래→위) 나오는데도 통과.
    # 판정축은 git diff가 아니라 **선언된 per-bond 소스 안의 회사 존재 여부**다(1차 방어선).
    for kw in itertools.chain(_capsec_coverage_findings(env), _capsec_prior_snapshot_drop(env)):
        if not _emit(kw.get("quarter")):
            continue
        res.add(check="census", **kw)

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
    # PL 누계(YTD) 붕괴 — 재빌드가 셀을 못 채운 지문. 신설 YELLOW(관찰기).
    # **_DISPLAY_QUARTERS 스코프 미적용**(CSM 연속성 룰과 동일 판단): 붕괴는 중간분기에서 일어나고
    # 그 여파가 표시분기의 `값_당분기`를 음수로 뒤집는다. 스코프를 걸면 원인 분기가 통째로 사각이 된다
    # (실제로 흥국화재·KB손해 2024.3Q 2건이 그렇게 숨어 있었다). YELLOW라 push는 막지 않는다.
    for co, q, item, prev in _pl_ytd_collapse(env.pl):
        res.add(check="census", severity="RED", master="PL_breakdown", company=co, quarter=q,
                rule="PL_YTD_COLLAPSE_TO_ZERO",
                message=f"{item} 누계가 직전분기 {prev:,.1f} → 이번분기 정확히 0.0 — FY 누계는 "
                        f"이렇게 사라지지 않는다(파생 값_당분기가 음수로 뒤집힘). 재빌드 결손 의심")
    # CSM 상대규모 plausibility (parser 20260730T0040Z, PM-2026-07-30 UH-6). 항등식은 스케일과
    # 무관하게 닫히므로 단위오류(×100)를 closure 검사로는 절대 못 잡는다 — 회사 규모로 정규화한
    # 비율만이 잡는다. 초기 YELLOW(관찰 1~2 릴리스 후 RED 전환, UH-3 sidecar 선례).
    for co, q, csm, cap, r, med, thr in _csm_magnitude_implausible(env):
        res.add(check="census", severity="YELLOW", master="CSM_waterfall", company=co, quarter=q,
                rule="CSM_WATERFALL_PLAUSIBILITY",
                message=f"기말CSM {csm:,.0f}억 ÷ 지급여력금액 {cap:,.0f}억 = {r:.2f} "
                        f"(전사 median {med:.2f}의 {r / med:.0f}배, 임계 {thr:.2f}) — 항등식은 닫히나 "
                        f"규모가 비정상(단위 ×100/×1000 오류 지문). 초기 YELLOW, RED 전환 예정")


# CSM_WATERFALL_PLAUSIBILITY (parser 20260730T0040Z / PM-2026-07-30 UH-6).
# 판정식: r = 기말CSM ÷ 지급여력금액(item1), 회사별 최신 분기, KR코드 조인, 둘 다 억원.
# 임계 = 전사 median × _CSM_PLAUS_MULT (상대값 — 신규사 온보딩으로 median이 이동해도 자동 추종).
#
# 임계값 재조정 근거 (validation 2026-08-03 실측, parser 초안 ×20에서 ×10으로 조정):
#   parser가 제시한 실측(KR0075 r=153.01 → ×273, 차순위 KR1098 r=3.49 → ×6.2)은 **정정 전** 값이다.
#   정정 후 라이브 36사 조인 분포: median 0.563 · 최대 1.530(KR0075) = median의 2.7배 · 최소 -0.0.
#   → ×20(r>11.3)은 살아있는 코호트 대비 여유가 7.4배로 과하게 느슨해, **중간 규모 회사의 ×10 단위
#     오류**(r 0.563→5.63 = ×10)를 놓친다. ×10(r>5.63)은 라이브 최대의 3.7배 여유를 남기면서 그
#     부류를 잡는다. KR0075 100× 사고는 ×273로 어느 쪽이든 발화.
# 오탐 억제: (a) K-ICS 미공시사(AIA 등) = 분모 부재 → skip. (b) 조인 표본 <10사 → median 불안정,
#   룰 전체 skip. (c) 상한만 검사(소형사 낮은 비율은 정상). (d) 지급여력금액 ≤ 0(자본잠식사,
#   예: 예별손해)은 비율이 무의미 → skip(규모 이상치는 CHECK 5 generic scan이 담당).
_CSM_PLAUS_MULT = 10.0
_CSM_PLAUS_MIN_SAMPLE = 10


def _csm_magnitude_implausible(env: "Env"):
    """[(company_name, quarter, closing_csm, capital, ratio, median, threshold), ...]"""
    # 회사별 최신 분기의 기말CSM (code-keyed 인덱스 재사용)
    closing = {}
    for (code, q), m in (env.wf_by_code or {}).items():
        v = _num(m.get("기말CSM"))
        if not code or not q or v is None:
            continue
        if code not in closing or q_to_num(q) > q_to_num(closing[code][0]):
            closing[code] = (q, v)
    # 회사별 최신 분기의 item1 지급여력금액 (적용전 값; 없으면 적용후)
    cap = {}
    for r in env.kics_records:
        if str(r.get("항목번호")) != "1":
            continue
        code, q = r.get("원보험사코드"), r.get("공시분기")
        v = _num(r.get("값"))
        if v is None:
            v = _num(r.get("값_적용후"))
        if not code or not q or v is None:
            continue
        if code not in cap or q_to_num(q) > q_to_num(cap[code][0]):
            cap[code] = (q, v)

    joined = []
    for code, (q, csm) in closing.items():
        if code not in cap:
            continue            # (a) K-ICS 미공시사 → 분모 부재 skip
        cq, cv = cap[code]
        if cv <= 0:
            continue            # (d) 자본잠식사 → 비율 무의미 skip
        joined.append((code, q, csm, cv, csm / cv))
    if len(joined) < _CSM_PLAUS_MIN_SAMPLE:
        return []               # (b) median 불안정 → 룰 skip
    med = statistics.median([j[4] for j in joined])
    if med <= 0:
        return []
    thr = med * _CSM_PLAUS_MULT
    out = []
    for code, q, csm, cv, r in sorted(joined, key=lambda j: -j[4]):
        if r > thr:             # (c) 상한만
            out.append((env.code_name.get(code, code), q, csm, cv, r, med, thr))
    return out


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


def _pl_ytd_collapse(pl):
    """같은 FY 안에서 누계(YTD)가 non-zero → **정확히 0.0** 으로 떨어지는 셀.

    PL 마스터의 `값`은 FY 누계라 분기가 갈수록 단조로 쌓인다(부호는 항목마다 다르되 이미 인식된
    누계가 통째로 사라지지는 않는다). 3Q 35,264 → 4Q 0.0 같은 자리는 회계 사건이 아니라 **재빌드가
    그 셀을 못 채운 지문**이고, 파생 `값_당분기` 가 −35,264 같은 물리적으로 불가능한 값으로 뒤집힌다.

    폐쇄식·브리지가 이걸 못 잡는 이유: 0 은 등식을 깨지 않고 조용히 통과한다(다른 항으로 닫히면 끝).
    2026-08-15 에 마스터가 HEAD 로 되돌아갔다 재빌드된 뒤 19셀이 이 상태로 회귀한 것을 놓쳤다.
    owner 지시(2026-08-15) 로 관찰기 없이 **RED**. "신설 룰도 당연히 맞아야 한다" —
    라이브 오표시를 놓친 직후라 관찰기를 두는 것 자체가 같은 실수의 반복이다.
    """
    def _qn(q):
        m = re.match(r"(\d{4})\.(\d)Q", str(q or ""))
        return (int(m.group(1)), int(m.group(2))) if m else None

    by_item: dict = {}
    for (co, q), m in pl.items():
        n = _qn(q)
        if not n:
            continue
        for item, v in m.items():
            by_item.setdefault((co, item), {})[n] = v
    out = []
    for (co, item), series in sorted(by_item.items(), key=lambda kv: (str(kv[0][0]), str(kv[0][1]))):
        for (y, qq), v in sorted(series.items()):
            if qq == 1:
                continue
            prev = series.get((y, qq - 1))
            if isinstance(prev, (int, float)) and prev != 0 and v == 0.0:
                out.append((co, f"{y}.{qq}Q", item, prev))
    return out


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
#   - sidecar ABSENT   → **RED `MISSING_PROVENANCE_SIDECAR`** (UH-3 end-state, 2026-08-03) +
#                        the Phase-1 inference below still runs for diagnosis.
# END-STATE REACHED (2026-08-03): all four CHECK-2 masters (sensitivity_heatmap ·
# forward_capital · tier1_utilization · tier2_utilization) now emit sidecars, so live
# MISSING_PROVENANCE_SIDECAR hit 0 → the graceful YELLOW was retired and no-sidecar is RED
# (owner principle 0 — never SKIP-as-pass). The earlier YELLOW existed only because red-ing
# out un-emitted masters would have blocked push forever; that condition is gone.
# ===========================================================================
# Authoritative source per master (capital-securities effective list).
_CAPITAL_SECURITIES_MASTERS = {"forward_capital", "tier1_utilization", "tier2_utilization"}

# PL↔워터폴 CSM상각 교차대조 임계. 상각 10억 미만은 소음, 배수 밴드는 개념차(손보 생명장기 leg vs
# 전사)를 흡수할 만큼 넓게 — 이 룰의 목표는 미세오차가 아니라 **한쪽만 비어 있는 자리**다.
_XCHK_MIN_AMORT_EOK = 10.0
_XCHK_LO, _XCHK_HI = 0.4, 2.5

# `source_id` must match the ACTUAL lineage of `source_file` — not a hardcoded enum
# (owner inbox/validation/20260803T0056Z).
# 2026-06-20부터 tier1/tier2 소진율의 per-bond 원천은 FSC(data.go.kr 채권등록)가 아니라 DART
# 사업보고서(`data/bonds/capital_securities_fy2025.json`)다. 그런데 이 게이트는 세 마스터 전부에
# `source_id == "FSC_BONDS"`를 강제하고 있었고, 사이드카는 그 요구를 만족시키려고 **DART 파일에
# FSC 라벨**을 달아 통과했다 = 게이트가 "소스를 검증한다"면서 틀린 주장을 확인해준 false-green.
# 고정 enum을 `{FSC_BONDS, DART}`로 넓히면 아무 라벨이나 통과해 검증력이 사라진다 → 대신
# **경로 계보 ↔ 선언 라벨 일치**를 검사한다(불일치 = SOURCE_ID_LINEAGE_MISMATCH RED).
_SOURCE_LINEAGE = (
    ("data/bonds/capital_securities_", "DART"),   # DART 사업보고서 per-bond 추출물
    ("data/bonds/disclosure/", "DART"),           # DART 주요사항보고서 supplement
    ("data/dart/", "DART"),
    ("data/bonds/normalized/", "FSC_BONDS"),      # FSC data.go.kr 채권등록 크롤 정규화
    ("data/bonds/raw/", "FSC_BONDS"),
)


def source_id_for_lineage(source_file: str | None) -> str | None:
    """`source_file` 경로가 함의하는 source_id. None = 계보 미등록(=검증 불가, 통과시키지 않는다)."""
    p = str(source_file or "").replace("\\", "/").lstrip("./")
    for prefix, sid in _SOURCE_LINEAGE:
        if p.startswith(prefix):
            return sid
    return None


def capsec_sources_in_use(sidecars: dict | None) -> dict[str, set[str]]:
    """서빙되는 capital-securities 마스터들이 **실제로** 원천으로 선언한 {계보: {source_file, ...}}.
    사이드카가 없으면 알 수 없으므로 역사적 기본값 FSC_BONDS를 요구한다(검사 축이 사라지지 않게 —
    빈 dict을 돌려주면 2c가 아무것도 검사하지 않는 빈 껍데기가 된다)."""
    out: dict[str, set[str]] = {}
    for m in sorted(_CAPITAL_SECURITIES_MASTERS):
        sc = (sidecars or {}).get(m)
        if not sc:
            continue
        for c in sc.get("cells") or []:
            sf = c.get("source_file")
            sid = source_id_for_lineage(sf)
            if sid:
                out.setdefault(sid, set()).add(str(sf).replace("\\", "/"))
    return out or {"FSC_BONDS": set()}


# ---------------------------------------------------------------------------
# CAPSEC_COVERAGE_REGRESSION (owner inbox/validation/20260803T0310Z) — CHECK 1의 1e에서 소비.
#
# 축 = **선언된 per-bond 소스 안에 회사 레코드가 있는가**. git diff(직전 배포본 대조)는 보조축일 뿐이라
# 1차 판정에 쓰지 않는다. 세 상태를 구분해야 룰이 성립한다:
#   (1) 소스에 회사 자체가 없다        → RED  (raw 부재 = 검증 불가. 마스터의 0은 "무발행"이 아니다)
#   (2) 소스에 있고 잔액 전부 0        → 통과 (스캔했고 무발행 확인 = 정당한 0)
#   (3) 소스에 잔액>0 인데 마스터가 0  → RED  (어댑터/필터 버그)
# 마스터가 스스로 붙인 `bond_coverage` 라벨은 **믿지 않는다** — 라벨을 믿는 검증이 false-green이 된 게
# PM-2026-08-03(사이드카가 DART 파일에 FSC 라벨). 존재 여부는 게이트가 소스에서 직접 도출한다.
# 기대 모집단도 하드코딩하지 않는다: 마스터가 실제로 행을 발행한 회사 = 검사 대상(self-census).
_CAPSEC_SLICE_FIELDS = {
    # master: (소스 슬라이스, 마스터쪽 "발행잔액 존재" 필드들 — 합이 0이면 마스터는 이 회사에 채권이
    #          없다고 말하는 것. tier 마스터는 소진율 분자(신규분)만 보면 경과조치 전액인 회사가
    #          정당한 0으로 보이므로 **면제분까지 더한 총액**을 존재 신호로 쓴다.)
    "forward_capital": ("all", ("outstanding_bonds_total_eok",)),
    "tier1_utilization": ("hybrid", ("tier1_hybrid_issued_eok", "tier1_grandfathered_hybrid_eok")),
    "tier2_utilization": ("sub", ("new_subordinated_gross_eok", "grandfathered_subordinated_eok")),
}
_CAPSEC_AMOUNT_TOL_EOK = 1.0
_CAPSEC_AMOUNT_TOL_REL = 0.01
_CAPSEC_PRIOR_DROP_REL = 0.20      # 보조축(§2 그물): 전체 발행잔액 20% 이상 급감 = YELLOW


def index_bond_source(doc, idx: dict | None = None) -> dict:
    """per-bond 소스를 `{code: {n_bonds, hybrid_mn, sub_mn, total_mn}}`로 정규화(백만원).

    두 계보의 스키마를 모두 받는다:
      DART  `{"companies": [{"code": .., "bonds": [{"tier": "hybrid|subordinated",
                                                   "outstanding_mn": ..}]}]}`
      FSC   `{"<code>": {"bonds": [{"tier": "tier1_hybrid|tier2_subordinated",
                                    "issue_amount_won": .., "status": "outstanding"}]}}`
    **레코드 존재 자체가 신호**다 — bonds가 비어 있어도 key를 만든다(= 스캔했고 무발행 확인).
    """
    idx = {} if idx is None else idx

    def _put(code, bonds, hybrid_mn, sub_mn):
        if not code:
            return
        e = idx.setdefault(str(code), {"n_bonds": 0, "hybrid_mn": 0.0, "sub_mn": 0.0, "total_mn": 0.0})
        e["n_bonds"] += bonds
        e["hybrid_mn"] += hybrid_mn
        e["sub_mn"] += sub_mn
        e["total_mn"] += hybrid_mn + sub_mn

    if isinstance(doc, dict) and isinstance(doc.get("companies"), list):        # DART per-bond
        for c in doc["companies"]:
            hyb = sub = 0.0
            bl = c.get("bonds") or []
            for b in bl:
                amt = _num(b.get("outstanding_mn")) or 0.0
                if str(b.get("tier")) == "hybrid":
                    hyb += amt
                else:
                    sub += amt
            _put(c.get("code"), len(bl), hyb, sub)
        return idx
    if isinstance(doc, dict):                                                   # FSC normalized
        for code, grp in doc.items():
            if not isinstance(grp, dict):
                continue
            hyb = sub = 0.0
            bl = [b for b in (grp.get("bonds") or []) if b.get("status") == "outstanding"]
            for b in bl:
                amt = (_num(b.get("issue_amount_won")) or 0.0) / 1e6
                if str(b.get("tier")) == "tier1_hybrid":
                    hyb += amt
                else:
                    sub += amt
            _put(grp.get("insurer_code") or code, len(bl), hyb, sub)
    return idx


def _capsec_published_rows(env: "Env") -> dict[str, list[tuple]]:
    """{master: [(code, name, row, quarter), ...]} — 각 마스터가 **실제로 발행한** 회사 행."""
    t1 = env.tier1_latest or {}
    t2 = env.tier2_latest or {}
    fq = (env.forward_manifest or {}).get("baseline_quarter")
    return {
        "forward_capital": [(r.get("insurer_code"), r.get("insurer_name"), r, fq)
                            for r in (env.forward_rows or []) if r.get("insurer_code")],
        "tier1_utilization": [(r.get("code"), r.get("company"), r, r.get("quarter") or t1.get("quarter"))
                              for r in (t1.get("results") or []) if r.get("code")],
        "tier2_utilization": [(r.get("code"), r.get("company"), r, r.get("quarter") or t2.get("quarter"))
                              for r in (t2.get("results") or []) if r.get("code")],
    }


def _capsec_coverage_findings(env: "Env"):
    """CAPSEC_COVERAGE_REGRESSION findings (res.add kwargs). CHECK 1의 1e가 소비."""
    src = env.capsec_bond_source or {}
    declared = env.capsec_source_files or {}
    rows_by_master = _capsec_published_rows(env)
    absent: dict[str, list] = {}          # code -> [master, ...] (회사당 1건으로 묶어 보고)
    absent_meta: dict[str, tuple] = {}

    for master, rows in rows_by_master.items():
        if not rows:
            continue
        files = declared.get(master) or []
        if not files:
            # 소스를 못 찾으면 커버리지 검사가 **빈 껍데기**가 된다(2c가 겪은 실패 유형).
            # 조용히 통과시키지 않는다 — 미검증 = RED (owner 원칙 0).
            yield dict(severity="RED", master=master, company=None, quarter=rows[0][3],
                       rule="CAPSEC_SOURCE_UNRESOLVED",
                       message=f"{master}: 회사 {len(rows)}행을 발행하면서 per-bond 소스를 선언하지 "
                               f"않았다(사이드카 source_file 부재) — 커버리지 census를 수행할 축이 "
                               f"없음(검증 불가 = RED)")
            continue
        slice_key, presence_fields = _CAPSEC_SLICE_FIELDS[master]
        for code, name, row, quarter in rows:
            rec = src.get(code)
            if rec is None:
                absent.setdefault(code, []).append(master)
                absent_meta[code] = (name, quarter, files)
                continue
            src_eok = rec[{"all": "total_mn", "hybrid": "hybrid_mn", "sub": "sub_mn"}[slice_key]] / 100.0
            master_eok = sum((_num(row.get(f)) or 0.0) for f in presence_fields)
            if src_eok <= 0:
                continue                    # (2) 스캔했고 그 슬라이스는 무발행 = 정당한 0
            tol = max(_CAPSEC_AMOUNT_TOL_EOK, _CAPSEC_AMOUNT_TOL_REL * src_eok)
            if master_eok <= 0:             # (3) 소스엔 잔액이 있는데 마스터는 0 = 어댑터/필터 버그
                yield dict(severity="RED", master=master, company=name or code, quarter=quarter,
                           rule="CAPSEC_COVERAGE_REGRESSION",
                           message=f"{name or code}({code}): 소스 {files[0]} 에 {slice_key} 발행잔액 "
                                   f"{src_eok:,.0f}억이 있는데 마스터 "
                                   f"{'+'.join(presence_fields)}=0 — 어댑터/필터가 조용히 떨어뜨림 "
                                   f"(상환차감·소진율 분자가 사라져 낙관 방향으로 틀림)")
            elif abs(master_eok - src_eok) > tol:
                # 부분 유실은 아직 라이브 실측 0건 → 관찰기 YELLOW(그물). 안정 확인 후 RED 승격.
                yield dict(severity="YELLOW", master=master, company=name or code, quarter=quarter,
                           rule="CAPSEC_AMOUNT_MISMATCH",
                           message=f"{name or code}({code}): 마스터 {master_eok:,.1f}억 ≠ 소스 "
                                   f"{src_eok:,.1f}억 ({slice_key} 슬라이스, tol {tol:,.1f}) — "
                                   f"부분 유실/이중계상 의심(관찰기 YELLOW)")

    for code, masters in sorted(absent.items()):
        name, quarter, files = absent_meta[code]
        yield dict(severity="RED", master="capital_securities_coverage", company=name or code,
                   quarter=quarter, rule="CAPSEC_COVERAGE_REGRESSION",
                   message=f"{name or code}({code}): 선언된 per-bond 소스({files[0]})에 회사 레코드 "
                           f"자체가 없다 — {', '.join(sorted(masters))}가 발행한 0은 '무발행'이 아니라 "
                           f"'미검증'이다(raw 부재). 무발행이면 소스에 빈 레코드(bonds: [])로 명시해야 "
                           f"'스캔 후 0'과 구분된다")


def _capsec_prior_snapshot_drop(env: "Env"):
    """보조축(owner §2) — 직전 배포 스냅샷 대비 발행잔액 후퇴 감지. 1e가 1차 방어선이고 이건 그물이라
    **YELLOW**(비차단). 소스에 레코드가 있는 채 값만 무너지는 부류(어댑터 회귀)를 늦게라도 잡는다."""
    prior = env.forward_prior_rows
    if not prior:
        return
    now = {r.get("insurer_code"): (_num(r.get("outstanding_bonds_total_eok")) or 0.0)
           for r in (env.forward_rows or []) if r.get("insurer_code")}
    was = {r.get("insurer_code"): (_num(r.get("outstanding_bonds_total_eok")) or 0.0)
           for r in prior if r.get("insurer_code")}
    q = (env.forward_manifest or {}).get("baseline_quarter")
    for code, prev in sorted(was.items()):
        cur = now.get(code)
        if cur is None or prev <= 0:
            continue
        if cur <= 0:
            yield dict(severity="YELLOW", master="forward_capital", company=code, quarter=q,
                       rule="CAPSEC_COVERAGE_DROP_VS_PRIOR",
                       message=f"{code}: 직전 스냅샷 발행잔액 {prev:,.0f}억 → 현재 0 "
                               f"(배포본 대비 후퇴 — 소스 교체/어댑터 회귀 의심)")
    tot_now, tot_was = sum(now.values()), sum(was.values())
    if tot_was > 0 and (tot_was - tot_now) / tot_was >= _CAPSEC_PRIOR_DROP_REL:
        yield dict(severity="YELLOW", master="forward_capital", company=None, quarter=q,
                   rule="CAPSEC_COVERAGE_DROP_VS_PRIOR",
                   message=f"전사 발행잔액 합계 {tot_was:,.0f}억 → {tot_now:,.0f}억 "
                           f"({(tot_was - tot_now) / tot_was:.0%} 급감) — 커버리지 후퇴 의심")


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
        # capital-securities: (i) declared source_id must match source_file's real lineage,
        # (ii) effective_filtered must be true (the actual donut-bug invariant).
        if master in _CAPITAL_SECURITIES_MASTERS:
            declared = cell.get("source_id")
            expected = source_id_for_lineage(sf)
            if expected is None:
                res.add(check="as_of", severity="RED", master=master, company=company,
                        quarter=quarter, rule="SOURCE_ID_LINEAGE_MISMATCH",
                        message=f"{company or '-'} {quarter or '-'}: source_file={sf or '(none)'} "
                                f"의 계보가 _SOURCE_LINEAGE에 미등록 → source_id={declared} 주장을 "
                                f"검증할 수 없음 (미검증 = RED, owner 원칙 0)")
            elif declared != expected:
                res.add(check="as_of", severity="RED", master=master, company=company,
                        quarter=quarter, rule="SOURCE_ID_LINEAGE_MISMATCH",
                        message=f"{company or '-'} {quarter or '-'}: source_id={declared} 로 선언했으나 "
                                f"source_file={sf} 의 실제 계보는 {expected} — provenance 라벨 거짓")
            if cell.get("effective_filtered") is not True:
                res.add(check="as_of", severity="RED", master=master, company=company,
                        quarter=quarter, rule="EFFECTIVE_LIST_NOT_FILTERED",
                        message=f"{company or '-'} {quarter or '-'}: capital-securities provenance "
                                f"effective_filtered={cell.get('effective_filtered')} — must be "
                                f"true (상환·콜 도래분이 outstanding에 섞이는 도넛 버그 가드)")


def check_as_of(res: GateResult, env: "Env") -> None:
    """(a) each published artifact's as_of period must equal its disclosure quarter;
    (c) tier/forward capital-securities must carry evidence that as-of effective filtering
    was applied. Missing evidence = RED (spec §2c, §0).

    Phase 2: per master, if a provenance sidecar EXISTS, verify it strictly; otherwise fall
    back to the Phase-1 inference below and emit one informational note (see header)."""
    latest_q = env.latest_kics_quarter  # the as-of the live site should be rendering
    sidecars = env.provenance_sidecars

    def _fallback_note(master):
        # UH-3 이력 — 3단계로 굳었다:
        #  (1) ~2026-07-21: notes에만 적어 **조용히 통과**(집계도 안 되고 눈에 안 띔) = 두 달
        #      글리치(PM-2026-06-16)의 원형이 부분적으로 살아 있던 상태.
        #  (2) 2026-07-21: 집계되는 YELLOW로 승격. RED로 못 올린 이유 = 그 시점엔 4개 마스터
        #      전부 미발행이라 즉시 red-out으로 push가 영구히 막혔다.
        #  (3) **2026-08-03: RED 전환 = UH-3 end-state 도달.** 4종(sensitivity_heatmap·
        #      forward_capital·tier1/tier2_utilization) 사이드카가 모두 발행돼 라이브
        #      MISSING_PROVENANCE_SIDECAR YELLOW가 0이 됐다 → 이제 "부재"는 정상 상태가 아니라
        #      **발행 주체가 씻겨나갔다는 신호**다. 통과시키면 소스 신선도 검사축이 조용히 사라진다
        #      (owner 원칙 0: SKIP-on-missing 금지).
        # 아래 Phase-1 추론 블록은 지우지 않고 남긴다 — 이 분기는 이제 RED이므로 통과 경로가 아니고,
        # 무엇이 어긋났는지(stale quarter / 결측 meta) 진단을 같이 보여주는 값이 있다.
        res.add(check="as_of", severity="RED", master=master, company=None, quarter=None,
                rule="MISSING_PROVENANCE_SIDECAR",
                message=f"{master}: provenance sidecar 부재 — 소스 신선도·계보가 미검증이다. "
                        f"4종 전부 발행 완료(2026-08-03) 후이므로 부재 = 발행 경로가 씻겨나간 것. "
                        f"`<master>_provenance.json` 재발행 필요 "
                        f"(capital-securities 3종은 `scripts/emit_capsec_provenance.py`) "
                        f"— 계약은 `--print-provenance-contract`")
        res.notes.append(
            f"provenance sidecar absent for {master} → RED (UH-3 end-state active since "
            f"2026-08-03; no-sidecar is no longer a pass, owner principle 0)")

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

    # --- 2a(iv). kics_rate_sensitivity provenance (2026-08-21 배선, UH-8) ---
    # 배경: 이 마스터는 `Env.MASTER_FILES` 에 등재돼 mtime 감시만 받고 **as-of·계보 축은 아무도
    # 보지 않았다**(inbox/parser/20260803T0520Z). 값 정합은 validate_kics_rate_sensitivity.py 가
    # 보지만 그건 "이 값이 맞는가" 이고 "어느 분기·어느 파일에서 나왔는가" 는 미검증이었다 —
    # PM-2026-06-16 두 달 글리치와 같은 부류(맞는 산수·틀린 소스).
    # 사이드카는 parser 가 2026-08-20 에 발행했다(scripts/emit_rate_sensitivity_provenance.py, 87셀).
    #
    # **target_q 를 None 으로 넘긴다 — 의도적이다.** sensitivity_heatmap·forward_capital·tier1/2 는
    # '최신 한 분기'만 담는 단일기준 아티팩트라 target_q(=최신분기)보다 오래되면 stale 이 맞다.
    # 이 마스터는 **이력형**이다(실측 2026-08-21: 2024.4Q 102행 · 2025.2Q 192행 · 2025.4Q 228행).
    # 여기에 target_q=latest_q 를 걸면 과거분기 86/87 셀이 전부 STALE_AS_OF RED 로 터진다 —
    # 데이터가 틀려서가 아니라 검사축을 잘못 잡아서다. 그래서 셀 단위 축만 강제한다:
    #   as_of_date 의 분기 == 그 셀의 공시분기 / source_file 디스크 존재 / source_id 계보 일치.
    # 마스터 전체의 신선도(최신분기가 최신 공시분기인가)는 **별개 축**이고, 지금은 미배선이다 —
    # 근거 없이 걸면 red-out 이라 스레드에 열린 항목으로 남긴다(공시 주기가 회사·분기마다 달라
    # "2026.1Q 가 없으면 stale" 이 참인지 실데이터로 확정하지 않았다. 카테고리로 단정 금지).
    rs_rows = env.rate_sensitivity_rows
    if sidecars.get("kics_rate_sensitivity") is not None:
        published = sorted({
            (r.get("원보험사코드"), r.get("공시분기"), "rate_sensitivity")
            for r in rs_rows if r.get("원보험사코드") and r.get("공시분기")
        })
        verify_provenance_sidecar(res, "kics_rate_sensitivity",
                                  sidecars["kics_rate_sensitivity"], published, None)
    elif not rs_rows:
        res.add(check="as_of", severity="RED", master="kics_rate_sensitivity", company=None,
                quarter=None, rule="MISSING_PROVENANCE",
                message="kics_rate_sensitivity.json absent/empty — cannot resolve provenance (RED)")
    else:
        _fallback_note("kics_rate_sensitivity")

    # --- 2c. effective-list applied evidence (capital-securities) ---
    # The donut bug (spec §5.1): downloader used a stale snapshot WITHOUT filtering to bonds
    # effective (outstanding) as of the baseline. Evidence = bonds carry status/effective_call_date
    # AND only outstanding bonds feed the recognized totals. Absent evidence = RED.
    #
    # 2026-08-03 (owner 20260803T0056Z §3) — 증거를 **실제로 서빙되는 계보에서** 확인하도록 재조준.
    # 종전에는 `data/bonds/normalized/<최신stamp>/bonds_by_insurer.json`(FSC 전용) 하나만 봤다.
    # tier1/tier2는 이미 2026-06-20부터 DART per-bond가 원천이므로, 서빙되는 그 파일의 effective
    # 필터는 **아무도 검증하지 않는 상태**였다(FSC 스냅샷이 통과해주면 그걸로 끝). forward_capital
    # 까지 DART로 옮기면 FSC 스냅샷이 사라져 이 검사는 빈 껍데기가 된다.
    # → 사이드카가 선언한 계보 집합을 구해, **쓰이는 계보마다** 증거를 요구한다. 증거 파일 부재 =
    #   RED(통과 아님, owner 원칙 0).
    evid = env.bond_effective_evidence
    for lineage in sorted(evid):
        ev = evid.get(lineage) or {}
        if not ev.get("snapshot_present"):
            res.add(check="as_of", severity="RED", master="capital_securities_effective_list",
                    company=None, quarter=None, rule="MISSING_EFFECTIVE_LIST",
                    message=f"{lineage}: 사이드카가 이 계보를 원천으로 선언했으나 per-bond 스냅샷이 "
                            f"없거나 읽히지 않음 — capital-securities effective as-of 필터 적용을 "
                            f"증명할 수 없음 (증거 부재 = RED, 도넛 버그 가드)")
            continue
        if not ev.get("has_status_field") or not ev.get("has_effective_call_date"):
            res.add(check="as_of", severity="RED", master="capital_securities_effective_list",
                    company=None, quarter=None, rule="EFFECTIVE_LIST_NOT_FILTERED",
                    message=f"{lineage}: per-bond 스냅샷에 status/outstanding · call/maturity 필드가 "
                            f"없음 — effective as-of 필터를 적용할 수 없다 (도넛 버그)")
        elif ev.get("called_or_matured_in_recognized"):
            detail = ev.get("leak_detail") or "상환·콜 도래분이 outstanding 인정액에 포함"
            res.add(check="as_of", severity="RED", master="capital_securities_effective_list",
                    company=None, quarter=None, rule="EFFECTIVE_LIST_NOT_FILTERED",
                    message=f"{lineage}: {detail} — effective as-of 필터 미적용 (도넛 버그)")


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
    # --- 3z. PL_breakdown 의 CSM상각 ↔ CSM_waterfall 의 상각액 (owner 2026-08-15) ---
    # 왜 필요했나: 두 마스터가 **같은 회사·같은 분기의 같은 사건**을 각자 들고 있는데 서로를 한 번도
    # 안 봤다. 그래서 라이브에 삼성화재 2026.2Q PL 생명장기 분해가 통째로 null(화면 0)인 채로
    # 나갔다 — 같은 분기 워터폴엔 상각 8,029.5억이 멀쩡히 있었는데도 게이트는 조용했다.
    # 폐쇄식은 결측을 통과시킨다(0/None 이 등식을 안 깬다) → 교차대조만이 유일한 탐지기다.
    #
    # 개념이 완전히 같지는 않다(손보 PL 은 생명장기 leg 만, 워터폴은 전사) → **배수는 느슨하게**,
    # 대신 "한쪽이 0/결측인데 다른 쪽은 유의미" 라는 명백한 자리를 잡는다(different-concept guard 정신).
    for (co, q), m in sorted(env.pl.items()):
        wfm = env.wf.get((co, q))
        if not wfm:
            continue
        amort = wfm.get("CSM상각")
        direct = m.get("원수CSM상각")
        # 역방향: PL 엔 상각이 있는데 워터폴 상각이 결측/0. 폐쇄식은 조정(plug)이 흡수해 닫히므로
        # 절대 못 잡는다(미래에셋 2026.2Q: 기초+신계약+이자+조정 = 기말 이 정확히 닫히는데 상각만 null).
        # 기존 IMPOSSIBLE_ZERO_AMORT 는 `상각 == 0` 만 봐서 **None 을 통과**시킨다.
        if isinstance(direct, (int, float)) and abs(direct) / 100.0 >= _XCHK_MIN_AMORT_EOK \
                and (amort is None or amort == 0):
            res.add(check="cross_source", severity="RED", master="CSM_waterfall",
                    company=co, quarter=q, rule="CSM_AMORT_MISSING_VS_PL",
                    message=f"CSM_waterfall 상각={amort!s} 인데 같은 분기 PL 원수CSM상각은 "
                            f"{abs(direct) / 100.0:,.1f}억 — 워터폴 쪽이 비었다. 폐쇄식은 조정 항이 "
                            f"흡수해 닫히므로 이 결측을 못 잡는다")
            continue
        if not isinstance(amort, (int, float)) or abs(amort) < _XCHK_MIN_AMORT_EOK:
            continue                       # 워터폴 상각 자체가 미미하면 대조 의미 없음
        if direct is None or direct == 0:
            res.add(check="cross_source", severity="RED", master="PL_breakdown",
                    company=co, quarter=q, rule="PL_CSM_AMORT_VS_WATERFALL",
                    message=f"PL 원수CSM상각={direct!s} 인데 같은 분기 CSM_waterfall 상각은 "
                            f"{abs(amort):,.1f}억 — 한쪽만 비었다(생명장기 분해 결측 지문)")
            continue
        pl_eok = (abs(direct) + abs(m.get("재보험CSM상각") or 0)) / 100.0   # 백만원 → 억원
        ratio = pl_eok / abs(amort)
        if ratio < _XCHK_LO or ratio > _XCHK_HI:
            res.add(check="cross_source", severity="RED", master="PL_breakdown",
                    company=co, quarter=q, rule="PL_CSM_AMORT_SCALE_GAP",
                    message=f"PL CSM상각 {pl_eok:,.1f}억 vs 워터폴 상각 {abs(amort):,.1f}억 "
                            f"(배수 {ratio:.2f}, 허용 {_XCHK_LO}~{_XCHK_HI}) — 단위·범위 불일치 의심")

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
# CSM 워터폴 부호 규약 — 전사 355:1 로 만장일치인 축이라 위반은 사실상 추출 사고다.
#   신계약 CSM < 0 : IFRS17 상 최초인식이 손실부담이면 CSM=0 + 손실요소(즉시 손익)라 음수가 못 나온다.
#   CSM 상각  > 0 : 상각은 CSM 을 소모하므로 음수여야 한다. 양수면 그 필링의 변동 블록이
#                   손익(P&L) 기준인데 부호를 그대로 옮긴 것이다(예별 2023.4Q 가 그 사례).
# **폐쇄식은 이 클래스에 무력하다** — 조정(item4)이 잔차로 채워지면 부호가 뒤집혀도 그대로 닫힌다.
_CSM_SIGN_EXCEPTIONS = {
    # (원수사명, 공시분기, 항목): 사유. raw 로 확인된 공시 자체의 표기만 등재한다.
    ("예별손해보험", "2025.4Q", "신계약CSM"):
        "raw 확인(20260406003175): 이 회사는 손실부담계약 전입/환입을 **CSM 열 안에** 표시한다"
        "(표준 표기는 CSM 열을 비운다 — 라이나 동일 표 대조). 그래서 신계약인식효과 행이 "
        "onerous 분을 net 한 (1,166,995)천원으로 찍힌다. PV +380,349 / RA +786,646 / CSM (1,166,995) "
        "합계 0 으로 행이 닫히고, 같은 필링의 상각은 (17,399,016) 로 **정상 부호**라 2023.4Q 식 "
        "부호역전이 아니다. 공시 표기를 그대로 옮긴 값.",
}


def _csm_sign_violations(wf):
    out = []
    for (co, q), m in sorted(wf.items()):
        for key, bad, why in (("신계약CSM", lambda v: v < 0, "신계약 CSM 은 음수가 될 수 없다"
                               "(손실부담이면 CSM=0 + 손실요소)"),
                              ("CSM상각", lambda v: v > 0, "CSM 상각은 CSM 을 소모하므로 음수여야 한다"
                               " — 양수면 변동 블록이 손익 기준인데 부호를 그대로 옮긴 지문")):
            v = m.get(key)
            if isinstance(v, (int, float)) and v != 0 and bad(v):
                exc = _CSM_SIGN_EXCEPTIONS.get((co, q, key))
                out.append((co, q, key, v, why, exc))
    return out


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
    # CSM 부호 규약(2026-08-17). 등재된 예외는 사유를 메시지에 실어 YELLOW 로 남긴다 —
    # 조용히 사라지면 다음에 진짜 부호역전이 와도 같은 자리에서 안 보인다.
    for co, q, key, v, why, exc in _csm_sign_violations(env.wf):
        if exc:
            res.add(check="domain", severity="YELLOW", master="CSM_waterfall", company=co,
                    quarter=q, rule="CSM_SIGN_CONVENTION_EXCEPTED",
                    message=f"{key}={v:,.1f} — 등재된 예외: {exc}")
        else:
            res.add(check="domain", severity="RED", master="CSM_waterfall", company=co,
                    quarter=q, rule="CSM_SIGN_CONVENTION",
                    message=f"{key}={v:,.1f} — {why}. 전사 규약은 355:1 로 만장일치다")
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
        # key MUST match the lookup names used in check_as_of (sidecars.get("forward_capital") /
        # "tier1_utilization" / "tier2_utilization") — a mismatch here means _load_provenance_sidecars
        # silently never finds an emitted sidecar (UH-3 follow-up bug, found 2026-07-21 while wiring
        # the 3 sidecars validation requested: "forward_capital_latest" never matched "forward_capital",
        # and tier1/tier2_utilization had no entry at all).
        # 2026-07-22: 배포되는 아티팩트를 가리키도록 교정. 이전 경로
        # templates/tier{1,2}_utilization_latest.json은 **쓰는 스크립트가 하나도 없는**
        # 수기 사본이었고 2025.4Q(38사)에 얼어붙어 있었다 — 사이트는 2026.1Q(39사)를
        # 서빙 중. 값 검사는 _load_tier가 output/ 빌더 산출물을 읽어 무사했지만,
        # mtime 감시와 provenance 사이드카 조회가 그 죽은 사본에 걸려 있었다
        # (사이드카는 2026.1Q를 기술하는데 2025.4Q 파일 옆에 놓여 있었음).
        # 게이트가 검사하는 대상 = 사용자가 보는 파일, 이 규칙을 여기서 강제한다.
        "forward_capital": "kics_forward_capital.json",
        "tier1_utilization": "kics_tier1_utilization.json",
        "tier2_utilization": "kics_tier2_utilization.json",
        # 2026-08-14 17BS 정본(owner 20260814T0232Z). 직전 equity_composition(항목 1-49)은
        # archive/2026-08_equity_composition/ 로 내려갔고 룰도 함께 아카이브됐다 —
        # 여기 남는 검사는 check_ifrs17_bs 의 두 개(BS 항등식 + 코어 census)뿐이다.
        "IFRS17_BS": "IFRS17_BS.json",
        # 2026-08-14 배당 마스터(owner 20260814T1625Z V-0). 여기 없으면 mtime 감시·
        # ARTIFACT_UNREADABLE·동시백필 판정이 전부 이 마스터를 건너뛴다 — 신규 마스터가
        # 게이트 밖에 방치되는 그 상태가 바로 등록 사유다.
        "dividend": "dividend.json",
    }

    def __init__(self, inject: dict | None = None):
        self.inject = inject or {}
        # delegate K-ICS market/life parent-child completeness to the cadence-aware K-ICS gate.
        # selftest injects minimal synthetic records (only item1) → passes delegate_kics=False.
        self.delegate_kics = self.inject.get("delegate_kics", True)
        # artifacts that exist but could not be parsed (see _load_json_opt)
        self.unreadable: list[tuple[str, str]] = []
        self.mtimes_before = self._snapshot_mtimes()

        self.kics_records = self._get("kics_records", lambda: self._load_json("kics_disclosure.json"))
        self.wf = self._get("wf", lambda: load_long("CSM_waterfall.json"))
        self.pl = self._get("pl", lambda: load_long("PL_breakdown.json"))
        self.sensitivity_heatmap = self._get("sensitivity_heatmap",
                                             lambda: self._load_json_opt("data/dart/viz/sensitivity_heatmap.json"))
        self.forward_manifest = self._get("forward_manifest", self._load_forward_manifest)
        self.forward_rows = self._get("forward_rows",
                                      lambda: self._load_json_opt("kics_forward_capital.json") or [])
        self.tier1_latest = self._get("tier1_latest", lambda: self._load_tier("tier1_utilization"))
        self.tier2_latest = self._get("tier2_latest", lambda: self._load_tier("tier2_utilization"))
        # 2026-08-21 CHECK 2 2a(iv) 배선용. 이 마스터는 **이력형**(여러 분기 동시 보유)이라
        # 단일기준 아티팩트(forward/tier)와 달리 target_q 를 걸지 않는다 — 아래 배선부 주석 참조.
        self.rate_sensitivity_rows = self._get(
            "rate_sensitivity_rows",
            lambda: self._load_json_opt("kics_rate_sensitivity.json") or [])
        # sidecars FIRST — bond evidence는 사이드카가 선언한 source_file에서 계보를 뽑아 검사한다.
        self.provenance_sidecars = self._get("provenance_sidecars", self._load_provenance_sidecars)
        self.bond_effective_evidence = self._get("bond_effective_evidence", self._load_bond_evidence)
        # capital-securities 커버리지 census(owner 20260803T0310Z)의 입력. 마스터가 스스로 붙인
        # bond_coverage 라벨이 아니라 **선언된 소스 파일**을 읽어 회사 존재 여부를 게이트가 도출한다.
        self.capsec_source_files = self._get("capsec_source_files",
                                             self._resolve_capsec_source_files)
        self.capsec_bond_source = self._get("capsec_bond_source", self._load_capsec_bond_source)
        self.forward_prior_rows = self._get("forward_prior_rows", self._load_forward_prior_rows)
        # selftest(inject 모드)는 합성데이터 격리 — 디스크 마스터를 읽지 않는다(wf_by_code 와 동일 규칙).
        # 격리하지 않으면 실제 17BS RED 가 합성 케이스 전부에 섞여 들어간다. 2026-08-14 에
        # 직전 equity 마스터에서 실제로 터진 자리다(심각도가 YELLOW→RED 로 승격되자 selftest 가
        # 0/22 로 무너졌다. 그전엔 YELLOW 라 조용히 통과 중이었다).
        self.ifrs17_bs = self._get(
            "ifrs17_bs",
            (lambda: []) if self.inject else lambda: self._load_json_opt("IFRS17_BS.json") or [])
        self.ifrs17_bs_published = self._get(
            "ifrs17_bs_published",
            (lambda: False) if self.inject else lambda: self._html_fetches("IFRS17_BS.json"))
        # 배당 마스터도 같은 3종 세트(데이터 · 배포여부 · 수집 census). 수집 census 는
        # dividend.json 의 **기대 그리드 원천**이다 — 어느 (회사,분기) 필링이 실제로 존재하는지는
        # 회사 목록이 아니라 fetch 결과(status)가 정한다. 회사 목록으로 기대치를 세우면 비상장
        # 15개사의 정상적 부재가 통째로 RED 가 된다.
        self.dividend = self._get(
            "dividend", (lambda: []) if self.inject else lambda: self._load_json_opt("dividend.json") or [])
        self.dividend_published = self._get(
            "dividend_published",
            (lambda: False) if self.inject else lambda: self._html_fetches("dividend.json"))
        self.dividend_fetch_census = self._get(
            "dividend_fetch_census",
            (lambda: None) if self.inject else lambda: self._load_json_opt(DIV_FETCH_CENSUS))
        # 2026-08-21 메타룰 입력 3종. selftest(inject 모드)는 합성데이터 격리 — 디스크의 실제
        # 레지스트리·원장·판독성 사이드카를 읽지 않는다(안 읽으면 clean baseline 이 실데이터
        # finding 에 오염된다. 17BS·dividend 와 같은 규칙).
        self.exemption_registries = self._get(
            "exemption_registries", (lambda: {}) if self.inject else _exemption_registries)
        self.exemption_ledger = self._get(
            "exemption_ledger", (lambda: None) if self.inject else _load_exemption_ledger)
        # 부재 박제(셀 단위) / 코드 박제 — selftest 주입용. 주입은 **추가만** 하고 기본 동작을
        # 안 바꾼다(기본값 None = 게이트가 라이브 레지스트리를 그대로 본다).
        self.absence_pins = self._get("absence_pins", lambda: None)
        self.code_pins = self._get("code_pins", lambda: None)
        self.source_readability = self._get(
            "source_readability", (lambda: {}) if self.inject else _source_readability)
        # 2026-08-24: 원천 육안판독 근거 원장(`SOURCE_UNREADABLE_NOT_VERIFIED` 축 전용).
        # 없으면 빈 dict = '등재 없음' 이고, 그러면 축이 종전대로 전부 YELLOW 를 낸다.
        # **파일이 사라지면 조용히 통과가 아니라 조용히 미판독으로 돌아간다** — 안전한 쪽이다.
        self.source_vision_ledger = self._get(
            "source_vision_ledger",
            (lambda: None) if self.inject else _load_source_vision_ledger)

        # derived
        self.code_name = {r["원보험사코드"]: r["원수사명"] for r in self.kics_records
                          if r.get("원보험사코드")}
        # wf is keyed by (원수사명, 공시분기); the code lookup is built from the K-ICS
        # records instead. (Until 2026-07-22 an empty `for ... : pass` loop walked the
        # whole waterfall here doing nothing — leftover scaffolding, removed.)
        # selftest(inject 모드)는 합성데이터 격리 — 디스크 마스터를 읽지 않는다(안 그러면
        # CSM_WATERFALL_PLAUSIBILITY 같은 조인 룰이 실데이터에 오염된다).
        if "wf_by_code" in self.inject:
            self.wf_by_code = self.inject["wf_by_code"]
        elif self.inject:
            self.wf_by_code = {}
        else:
            self.wf_by_code = {}
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
        """Optional artifact. Absent -> None. Present-but-unparseable -> None AND
        recorded, because the two must not look alike: a truncated or
        mis-encoded master would otherwise be read as "this artifact was never
        emitted", which silently downgrades the as-of/provenance checks to their
        inference fallback and lets a corrupt file through GREEN."""
        p = ROOT / rel
        if not p.exists():
            return None
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception as e:
            self.unreadable.append((rel, f"{type(e).__name__}: {e}"))
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

    def _resolve_capsec_source_files(self) -> dict[str, list[str]]:
        """{capital-securities master: [사이드카가 선언한 per-bond source_file, ...]}.
        선언이 없으면 빈 리스트 → 커버리지 census가 CAPSEC_SOURCE_UNRESOLVED RED을 낸다
        (조용히 검사가 사라지는 '빈 껍데기'를 만들지 않는다)."""
        out: dict[str, list[str]] = {}
        for master in sorted(_CAPITAL_SECURITIES_MASTERS):
            files: list[str] = []
            sc = (self.provenance_sidecars or {}).get(master)
            for c in (sc or {}).get("cells") or []:
                sf = str(c.get("source_file") or "").replace("\\", "/")
                if sf and sf not in files:
                    files.append(sf)
            out[master] = files
        return out

    def _load_capsec_bond_source(self) -> dict[str, dict]:
        """선언된 per-bond 소스 전부를 `{code: {n_bonds, hybrid_mn, sub_mn, total_mn}}`로 병합."""
        idx: dict[str, dict] = {}
        seen: set[str] = set()
        for files in (self.capsec_source_files or {}).values():
            for rel in files:
                if rel in seen:
                    continue
                seen.add(rel)
                doc = self._load_json_opt(rel)   # 깨진 파일은 unreadable에 기록 → ARTIFACT_UNREADABLE
                if doc:
                    index_bond_source(doc, idx)
        return idx

    def _load_forward_prior_rows(self):
        """직전 forward 스냅샷(`output/kics_forward_capital/<stamp>/forward_simulation_v3.json`)의
        행들. 최신 stamp는 현 배포본과 같은 실행이므로 **그 앞 stamp**를 비교 대상으로 쓴다.
        selftest(inject 모드)는 합성데이터 격리 — 디스크를 읽지 않는다."""
        if self.inject:
            return None
        base = ROOT / "output" / "kics_forward_capital"
        if not base.exists():
            return None
        dirs = sorted([d for d in base.iterdir()
                       if d.is_dir() and (d / "forward_simulation_v3.json").exists()])
        if len(dirs) < 2:
            return None
        return self._load_json_opt(
            (dirs[-2] / "forward_simulation_v3.json").relative_to(ROOT).as_posix())

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
                except Exception as e:
                    self.unreadable.append((str(man.relative_to(ROOT)), f"{type(e).__name__}: {e}"))
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
        except Exception as e:
            self.unreadable.append((str(files[-1].relative_to(ROOT)), f"{type(e).__name__}: {e}"))
            return None

    def _load_bond_evidence(self):
        """Evidence that capital-securities effective as-of filtering was applied, **per lineage in
        actual use** (owner 20260803T0056Z §3). Returns {lineage: evidence-dict}.

        종전에는 `data/bonds/normalized/<최신stamp>/bonds_by_insurer.json`(FSC 전용) 한 파일만 봤다.
        tier1/tier2는 2026-06-20부터 DART per-bond가 원천이므로 **서빙되는 그 파일의 effective
        필터는 아무도 검증하지 않았다**. 이제 사이드카가 선언한 source_file 집합에서 계보를 뽑아,
        쓰이는 계보마다 그 **선언된 파일**을 검사한다 — 게이트가 검사하는 파일 = 사용자가 보는 파일."""
        in_use = capsec_sources_in_use(self.provenance_sidecars)
        out = {}
        for lineage, files in in_use.items():
            if lineage == "DART":
                out[lineage] = self._merge_bond_evidence(
                    [self._load_dart_bond_evidence(f) for f in sorted(files)] or
                    [self._blank_bond_evidence()])
            else:
                out[lineage] = self._merge_bond_evidence(
                    [self._load_fsc_bond_evidence(f) for f in sorted(files)] or
                    [self._load_fsc_bond_evidence(None)])
        return out

    @staticmethod
    def _blank_bond_evidence():
        return {"snapshot_present": False, "has_status_field": False,
                "has_effective_call_date": False, "called_or_matured_in_recognized": False,
                "leak_detail": None}

    @staticmethod
    def _merge_bond_evidence(evs):
        """여러 선언 파일의 증거 결합: 필드존재/스냅샷은 AND(하나라도 못 갖추면 미증명),
        누출은 OR(하나라도 새면 도넛 버그)."""
        evs = [e for e in evs if e]
        if not evs:
            return Env._blank_bond_evidence()
        det = [e.get("leak_detail") for e in evs if e.get("leak_detail")]
        return {"snapshot_present": all(e["snapshot_present"] for e in evs),
                "has_status_field": all(e["has_status_field"] for e in evs),
                "has_effective_call_date": all(e["has_effective_call_date"] for e in evs),
                "called_or_matured_in_recognized": any(e["called_or_matured_in_recognized"] for e in evs),
                "leak_detail": "; ".join(det) or None}

    @staticmethod
    def _bond_date(s):
        if not s:
            return None
        try:
            parts = str(s).replace(".", "-").replace("/", "-").split("-")[:3]
            return _dt.date(*(int(x) for x in parts))
        except Exception:
            return None

    def _load_dart_bond_evidence(self, rel: str):
        """DART 사업보고서 per-bond 추출물(사이드카가 선언한 `rel`)의 effective 증거.
        이 파일이 2026-06-20부터 tier1/tier2 소진율 분자의 실제 원천인데 종전 게이트는 FSC 스냅샷만
        봤다 = 서빙되는 파일이 미검증. 두 축으로 확인한다:
          (i) 아티팩트 자체 as-of 기준: 콜/만기가 이미 도래했는데 outstanding>0이면 미행사 사실을
              `past_call_outstanding: true`로 명시해야 한다(흥국식 콜경과 예외). 미표기 = 상환분이
              인정액에 섞인 것.
          (ii) 소비 시점 갭: 아티팩트 as-of < 마스터 as-of 구간에 콜이 도래한 채권. 후순위는
              wire_capital_securities_to_utilization.amort()가 0으로 떨어뜨려 걸러지지만, 신종(hybrid)은
              tier1 분자에 무조건 합산되므로(같은 스크립트 `new_hyb += out`) 이 검사만이 막는다."""
        ev = self._blank_bond_evidence()
        doc = self._load_json_opt(rel) if rel else None
        if not doc:
            return ev
        ev["snapshot_present"] = True
        snap = self._bond_date(doc.get("as_of"))
        master_as_of = _quarter_end_date((self.tier1_latest or {}).get("quarter")
                                         or (self.tier2_latest or {}).get("quarter")) or snap
        leaks = []
        for c in doc.get("companies") or []:
            for b in c.get("bonds") or []:
                if ("outstanding_mn" in b) and ("past_call_outstanding" in b):
                    ev["has_status_field"] = True
                if b.get("call_date") or b.get("legal_maturity"):
                    ev["has_effective_call_date"] = True
                eff = self._bond_date(b.get("call_date")) or self._bond_date(b.get("legal_maturity"))
                out = b.get("outstanding_mn") or 0
                if eff is None or snap is None or not out or b.get("past_call_outstanding") is True:
                    continue
                if eff <= snap:
                    leaks.append(f"{c.get('code')} {b.get('name') or b.get('tier')} "
                                 f"(eff {eff} <= 스냅샷 {snap}, outstanding {out}백만, 미행사 미표기)")
                elif master_as_of and eff <= master_as_of and b.get("tier") == "hybrid":
                    leaks.append(f"{c.get('code')} {b.get('name') or 'hybrid'} "
                                 f"(콜 {eff} 이 마스터 as-of {master_as_of} 이전인데 신종 분자에 "
                                 f"{out}백만 전액 합산)")
        if leaks:
            ev["called_or_matured_in_recognized"] = True
            ev["leak_detail"] = "; ".join(leaks[:5]) + (f" (+{len(leaks) - 5}건)" if len(leaks) > 5 else "")
        return ev

    def _load_fsc_bond_evidence(self, rel: str | None = None):
        """FSC(data.go.kr 채권등록) 정규화 스냅샷의 effective 증거.
        `rel`이 주어지면 **사이드카가 선언한 그 파일**을, 없으면 최신 stamp 디렉터리를 본다.
        snapshot_present + status/effective_call_date fields + no called/matured bond counted in
        the outstanding totals (the donut-bug guard)."""
        ev = self._blank_bond_evidence()
        if rel:
            doc = self._load_json_opt(rel)
            if not doc:
                return ev
        else:
            base = ROOT / "data" / "bonds" / "normalized"
            if not base.exists():
                return ev
            dirs = sorted([d for d in base.iterdir() if d.is_dir()])
            if not dirs:
                return ev
            bi = dirs[-1] / "bonds_by_insurer.json"
            if not bi.exists():
                return ev
            doc = self._load_json_opt(bi.relative_to(ROOT).as_posix())
            if not doc:
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

    @staticmethod
    def _html_fetches(master_file: str) -> bool:
        """루트 배포 HTML 중 이 마스터를 실제로 fetch 하는 페이지가 있는가.

        불변식 "게이트가 검사하는 파일 = 사용자가 보는 파일" 의 적용: 아직 어느 페이지도
        읽지 않는 신규 마스터의 결측을 push 차단 사유로 쓰면, 무관한 배포까지 함께 막힌다.
        배포되기 전까지는 YELLOW(보고), 디자이너/퍼블리싱이 패널에 물리는 순간 **코드 수정
        없이** 자동으로 RED 로 승격된다(owner 20260813T0422Z V-3 "배포 아티팩트가 되면 배선").
        2026-08-14: 배당 마스터가 같은 패턴을 두 번째로 쓰게 되어 파일명 인자로 일반화.
        """
        for p in ROOT.glob("*.html"):
            try:
                if master_file in p.read_text(encoding="utf-8", errors="ignore"):
                    return True
            except Exception:
                continue
        return False

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
def check_artifact_readable(res: GateResult, env: "Env") -> None:
    """An artifact that exists but will not parse is RED, never a silent skip."""
    for rel, err in getattr(env, "unreadable", []):
        res.add(check="census", severity="RED", master=rel, company=None, quarter=None,
                rule="ARTIFACT_UNREADABLE",
                message=f"file exists but could not be parsed ({err}) — "
                        f"downstream checks would have treated it as absent")


# 17BS 코어 = 자산/부채/자본/AOCI. 5·6·7(해약환급금·비상위험·대손 준비금)은 optional —
# owner 20260814T0232Z §2 "가능하면 찾아서 추가하되 안 되면 pass. 코어로 올리지 말 것".
IFRS17_BS_CORE_ITEMS = (1, 2, 3, 4)
IFRS17_BS_LABELS = {1: "자산총계", 2: "부채총계", 3: "자본총계", 4: "기타포괄손익 누계액"}
IFRS17_BS_TOL_REL = 0.001   # 0.1%
IFRS17_BS_TOL_ABS = 1.0     # 백만원
# 코어 census 면제 = **소스가 존재하지 않는 회사**(owner 종결 지시 2026-08-14: "걔네는 걍 접어").
# 전부 비상장이라 DART 에 감사보고서(F)만 내고 XBRL 첨부가 없다. 2026-08-14 실측:
#   fnlttSinglAcntAll(2019020) = status 013 · fnlttXbrl(2019019) = status 014, 필링 6건 전수.
#   같은 호출로 상장 대조군(한화생명)은 3/3 성공 → 우리 호출 문제가 아니라 파일 부재.
# 채울 경로가 없는 결측을 RED 로 두면 게이트가 영구히 push 를 막는다. 면제는 **census 한정**이고
# BS_IDENTITY 는 계속 돈다 — 값이 들어오는 순간 구조검사는 그대로 받는다.
IFRS17_BS_NO_SOURCE = {
    "KR0029",  # AIG손해보험
    "KR0050",  # 하나손해보험
    "KR0051",  # 신한이지손해보험
    "KR0075",  # 비엔피파리바카디프생명보험
    "KR0095",  # 메트라이프생명보험
    "KR1011",  # IBK연금보험
}




def check_ifrs17_bs(res: GateResult, env: "Env") -> None:
    """17BS 마스터(IFRS17_BS.json) — 룰은 딱 둘(owner 20260814T0232Z §2, "그 외 아무것도 만들지 마라").

      BS_IDENTITY          항목1(자산총계) == 항목2(부채총계) + 항목3(자본총계)
      CENSUS_MISSING_ITEM  코어 항목 1·2·3·4 중 결측

    자본총계 폐쇄식(1=2+3+…)은 이 마스터에 자본 세부항목이 없어 성립하지 않는다 — AOCI 태그
    채택 검산은 파서가 자체적으로 한다(발주 20260814T0216Z P-2).

    심각도는 기존 방식 그대로 **배포 여부**가 정한다(불변식 "게이트가 검사하는 파일 = 사용자가
    보는 파일"): 어느 배포 HTML 도 IFRS17_BS.json 을 아직 fetch 하지 않으면 YELLOW, 패널에
    물리는 순간 코드 수정 없이 RED 로 자동 승격.
    """
    def _sev(msg: str) -> tuple[str, str]:
        if env.ifrs17_bs_published:
            return "RED", msg
        return "YELLOW", msg + "  [미배포 — 어떤 페이지도 IFRS17_BS.json 을 아직 읽지 않아 " \
                               "push 차단은 보류. 배포 keep-list 에 오르면 자동 RED]"

    cells: dict[tuple, dict] = {}
    names: dict[str, str] = {}
    for r in env.ifrs17_bs:
        code, q, item = r.get("원보험사코드"), r.get("공시분기"), r.get("항목번호")
        if not code or not q or item is None:
            continue
        cells.setdefault((code, q), {})[item] = r.get("값")
        names.setdefault(code, r.get("원수사명") or code)

    skipped: list[str] = []
    try:
        sys.path.insert(0, str(ROOT / "scripts"))
        import validate_statutory_reserves as _rsv   # noqa: E402
        carry_ok, carry_rejected = _rsv.carry_forward_exempt()
    except Exception as _e:      # 모듈이 없으면 면제 없음 = 보수적(더 많이 RED)
        carry_ok, carry_rejected = set(), []
        res.add(check="census", severity="YELLOW", master="IFRS17_BS", company=None,
                quarter=None, rule="BS_CARRY_FORWARD_LOADER_UNAVAILABLE",
                message=f"이월 면제 로더 사용 불가 — 면제 없이 검사한다: {_e}")
    carry_skipped: list[str] = []
    for (code, q), cell in sorted(cells.items()):
        if not (env.inject or _in_scope(q)):   # live: 화면에 뜨는 분기만, selftest: 전수
            continue
        nm = names.get(code, code)
        # census 면제(BS_IDENTITY 는 계속 검사한다 — 값이 들어오면 구조검사는 공짜다)
        core_missing = [i for i in IFRS17_BS_CORE_ITEMS if cell.get(i) is None]
        if core_missing and not env.inject and code in IFRS17_BS_NO_SOURCE:
            skipped.append(f"{nm} {q}({len(core_missing)})")
            core_missing = []
        elif core_missing and not env.inject and (code, q) in carry_ok:
            # 준비금 이월로 생긴 칸 — 그 분기엔 회사가 재무제표를 안 낸다(위에서 재검증함).
            # 회사 통째 면제가 아니라 **이 칸만** 빠지므로 같은 회사의 4Q 는 계속 검사된다.
            carry_skipped.append(f"{nm} {q}({len(core_missing)})")
            core_missing = []
        for item in core_missing:
            sev, msg = _sev(f"코어 항목 {item}({IFRS17_BS_LABELS[item]}) 결측 — "
                            f"이 (회사,분기) 행은 존재하는데 코어 셀이 비었다")
            res.add(check="census", severity=sev, master="IFRS17_BS", company=nm,
                    quarter=q, rule="BS_CENSUS_MISSING_ITEM", message=msg)
        a, l, e = cell.get(1), cell.get(2), cell.get(3)
        if a is not None and l is not None and e is not None:
            s = l + e
            if abs(a - s) > max(IFRS17_BS_TOL_ABS, IFRS17_BS_TOL_REL * max(abs(a), abs(s))):
                sev, msg = _sev(f"자산총계 1({a:,.0f}) != 부채총계 2 + 자본총계 3 ({s:,.0f}) "
                                f"[잔차 {a - s:,.0f}] — 연결/별도 오선택·단위 오적용·행 오인식 의심")
                res.add(check="domain", severity=sev, master="IFRS17_BS", company=nm,
                        quarter=q, rule="BS_IDENTITY", message=msg)

    if carry_skipped:
        res.add(check="census", severity="YELLOW", master="IFRS17_BS", company=None,
                quarter=None, rule="BS_CENSUS_CARRY_FORWARD_CELL",
                message=f"준비금 hold-forward 로 생긴 {len(carry_skipped)}블록 코어 census 면제 "
                        f"(연1회 공시사, 그 분기 필링 없음을 raw meta.json `no_filing` 로 재확인): "
                        f"{', '.join(carry_skipped[:12])}"
                        + (f" …외 {len(carry_skipped)-12}" if len(carry_skipped) > 12 else "")
                        + ". 근거 사이드카 data/_derived/bs_carry_forward_cells.json, "
                          "owner 2026-08-20 이월 결정. BS_IDENTITY 는 계속 검사한다")
    for code, q, why in carry_rejected:
        # 사이드카가 면제를 주장했지만 독립 근거가 안 맞는 칸 — 조용히 넘기지 않는다.
        res.add(check="census", severity="RED", master="IFRS17_BS",
                company=names.get(code, code), quarter=q,
                rule="BS_CARRY_FORWARD_EXEMPTION_REJECTED",
                message=f"이월 면제 주장이 근거와 어긋난다: {why}")

    if skipped:   # 조용히 사라지지 않게 집계 1건으로 항상 보인다
        res.add(check="census", severity="YELLOW", master="IFRS17_BS", company=None,
                quarter=None, rule="BS_CENSUS_NO_SOURCE_COMPANY",
                message=f"비상장 {len(IFRS17_BS_NO_SOURCE)}개사 코어 census 면제 — "
                        f"{len(skipped)}블록 스킵: {', '.join(skipped)}. "
                        f"근거: OpenDART fnlttSinglAcntAll=013 / fnlttXbrl=014(상장 대조군은 정상) "
                        f"+ owner 종결 지시 2026-08-14. BS_IDENTITY 는 계속 검사한다")


# 배당 마스터(dividend.json, DART alotMatter) — 룰은 딱 셋(owner 20260814T1625Z V-1
# "3개로 끝낸다"). 항목번호: 2=(연결)당기순이익 · 5=현금배당금총액 · 6=주식배당금총액 ·
# 7=(연결)현금배당성향 · 8=주당현금배당금 · 9=주당주식배당 · 10=현금배당수익률.
DIV_FETCH_CENSUS = "data/_derived/alotmatter_fetch_census.json"
DIV_REPRT_Q = {"11013": "1Q", "11012": "2Q", "11014": "3Q", "11011": "4Q"}
DIV_PAYOUT_TOL_PP = 0.5     # %p — DART 공시 배당성향이 소수 1자리 반올림이라 그 폭은 허용


def check_dividend(res: GateResult, env: "Env") -> None:
    """배당 마스터 3룰.

      DIV_PAYOUT_IDENTITY     항목7 == 항목5 / 항목2 × 100 (연결 기준 배당성향)
      DIV_CENSUS_MISSING      수집 census 가 status=000(필링 존재)이라는데 마스터에 행이 없음
      DIV_ZERO_CONTRADICTION  배당총액=0 인데 같은 (회사,분기)에 주당배당금/수익률은 양수

    **기대 그리드는 회사 목록이 아니라 수집 census 에서 나온다.** alotMatter 는 비상장 15개사를
    아예 다루지 않아(전 기간 status=013) 회사 목록으로 census 를 세우면 정상적 부재가 전부 RED 로
    둔갑한다. status=000 인 셀만 "있어야 할 셀"이다.

    분기 스코프를 걸지 않는다(K-ICS 의 _DISPLAY_QUARTERS 미적용): 배당 화면은 2023.1Q~2026.2Q
    전 계열을 그리므로, 표시분기로 좁히면 화면에 뜨는 셀이 검사 밖에 남는다.

    심각도는 17BS 와 같은 배포여부 승격(불변식 "게이트가 검사하는 파일 = 사용자가 보는 파일"):
    아직 아무 HTML 도 dividend.json 을 fetch 하지 않으면 YELLOW, 공시보고서.html 이 물리는
    순간 코드 수정 없이 RED.
    """
    if not env.dividend:
        return

    def _sev(msg: str) -> tuple[str, str]:
        if env.dividend_published:
            return "RED", msg
        return "YELLOW", msg + "  [미배포 — 어떤 페이지도 dividend.json 을 아직 읽지 않아 " \
                               "push 차단은 보류. 배포 keep-list 에 오르면 자동 RED]"

    comp: dict[tuple, dict] = {}     # (code, quarter) -> {항목번호: 값}   회사단위(종류주="-")
    per_class: dict[tuple, dict] = {}  # (code, quarter) -> {(항목번호, 종류주): 값}
    names: dict[str, str] = {}
    for r in env.dividend:
        code, q, item = r.get("원보험사코드"), r.get("공시분기"), r.get("항목번호")
        if not code or not q or item is None:
            continue
        names.setdefault(code, r.get("원수사명") or code)
        kind = r.get("종류주")
        if kind in (None, "-"):
            comp.setdefault((code, q), {})[item] = r.get("값")
        else:
            per_class.setdefault((code, q), {})[(item, kind)] = r.get("값")

    # ---- R1: 배당성향 항등식 -------------------------------------------------
    for (code, q), cell in sorted(comp.items()):
        payout, total, ni = cell.get(7), cell.get(5), cell.get(2)
        if payout is None or total is None or ni is None or ni <= 0:
            continue          # 적자/미공시 분기는 배당성향 자체가 정의되지 않는다
        expected = total / ni * 100
        if abs(expected - payout) > DIV_PAYOUT_TOL_PP:
            sev, msg = _sev(f"(연결)현금배당성향 공시 {payout:.2f}% != 현금배당금총액"
                            f"({total:,.0f}) / (연결)당기순이익({ni:,.0f}) × 100 = "
                            f"{expected:.2f}% — 연결/별도 오선택(항목2 vs 항목3)·기간 오매칭 의심")
            res.add(check="domain", severity=sev, master="dividend", company=names.get(code, code),
                    quarter=q, rule="DIV_PAYOUT_IDENTITY", message=msg)

    # ---- R2: 수집 census 대비 결측 -------------------------------------------
    census = env.dividend_fetch_census
    if not census:
        sev, msg = _sev(f"수집 census({DIV_FETCH_CENSUS})가 없어 배당 마스터의 완전성을 "
                        f"검증할 수 없다 — 결측 검사축이 통째로 사라진 상태")
        res.add(check="census", severity=sev, master="dividend", company=None, quarter=None,
                rule="DIV_CENSUS_SOURCE_MISSING", message=msg)
    else:
        have = set(comp) | set(per_class)
        no_filing_only = {}          # code -> 000 필링이 하나도 없는 회사(정상적 전 기간 부재)
        missing = []
        for c in census.get("cells", []):
            qlabel = DIV_REPRT_Q.get(c.get("reprt"))
            code = c.get("kr")
            if not qlabel or not code:
                continue
            q = f"{c.get('year')}.{qlabel}"
            ok = c.get("status") == "000"
            no_filing_only[code] = no_filing_only.get(code, True) and not ok
            if ok and (code, q) not in have:
                missing.append((code, q, c.get("corp_code")))
        for code, q, cc in missing:
            sev, msg = _sev(f"수집 census 는 이 분기 필링이 존재한다고(status=000) 기록했는데 "
                            f"마스터에 행이 하나도 없다 — raw: "
                            f"data/dart/_alotmatter_cache/{cc}_{q[:4]}_*.json. "
                            f"무배당(값=0)과 미공시(행 없음)를 뒤바꾼 케이스이거나 빌더 누락")
            res.add(check="census", severity=sev, master="dividend", company=names.get(code, code),
                    quarter=q, rule="DIV_CENSUS_MISSING", message=msg)
        absent = sorted(c for c, only in no_filing_only.items() if only)
        if absent:
            res.add(check="census", severity="YELLOW", master="dividend", company=None, quarter=None,
                    rule="DIV_NO_FILING_COMPANY",
                    message=f"{len(absent)}개사는 전 기간 alotMatter 필링 자체가 없다"
                            f"(status 013 전량) — 비상장이라 이 엔드포인트가 다루지 않는 정상 상태. "
                            f"기대 그리드에서 제외됨: {', '.join(absent)}")

    # ---- R3: 0값 맹점 (총액 0인데 주당배당/수익률은 양수) ----------------------
    for (code, q), cell in sorted(comp.items()):
        cls = per_class.get((code, q), {})
        for total_item, evidence_items, what in ((5, (8, 10), "현금배당"), (6, (9,), "주식배당")):
            if cell.get(total_item) != 0:
                continue
            pos = {f"항목{item}·{kind}": v for (item, kind), v in cls.items()
                   if item in evidence_items and isinstance(v, (int, float)) and v > 0}
            if pos:
                sev, msg = _sev(f"{what}금총액=0 인데 같은 분기에 {pos} 가 양수 — "
                                f"공시 '-'(미공시)를 0으로 뭉갠 지문(0값 맹점). "
                                f"raw alotMatter 의 해당 se 행을 다시 볼 것")
                res.add(check="census", severity=sev, master="dividend",
                        company=names.get(code, code), quarter=q,
                        rule="DIV_ZERO_CONTRADICTION", message=msg)


# CSM 연속성(FY 경계) — owner 2026-08-15 승격 지시로 push 차단 게이트에 편입.
# 종전엔 validate_master_tables.py 의 CONT 에만 있었고, prepush_check.py 는
# validate_data_contract 만 호출하므로 **위반이 있어도 push 가 나갔다**(UH 계열 구조갭).
# 판정식·허용오차는 그쪽 CONT 와 동일하게 맞춘다 — 두 게이트가 다른 답을 내면 안 된다.
# 차이는 하나: 그쪽은 FY→분기 목록이 하드코딩(`FY_Q`, 2026.1Q 까지)이라 **2026.2Q 가 검사
# 밖이었다.** 여기서는 분기에서 FY 를 도출해 새 분기가 자동 편입되게 한다(실측: 그 하드코딩
# 때문에 안 보이던 위반이 5건 더 있었다).
CSM_CONT_TOL_REL = 0.005
CSM_CONT_TOL_ABS = 2.0      # 억원


def check_csm_continuity(res: GateResult, env: "Env") -> None:
    """FY[t] 각 분기의 기초 CSM == FY[t-1].4Q 기말 CSM.

    누계(`값`) 컬럼 기준이다 — 반기/분기 보고서의 기초는 **FY 시작(전년 12/31) 앵커**이고,
    그 분기 자체의 기초는 파서가 `값_당분기`에 따로 담는다(2026.2Q 검토에서 확정).
    두 컬럼을 섞으면 23사 전건 오탐이 난다.

    **break = 무조건 RED, 면제 없음.** "소급재작성으로 보인다"는 raw 대조로 확정되기 전에는
    사유가 못 된다 (owner 2026-06-16: self-closing identity 는 opening 을 검증하지 못한다 —
    2026.1Q 5사 기시 misparse 를 '재작성'으로 오판한 사건). 정정은 면제셋이 아니라 **데이터
    수정**으로 한다(후속 분기 공시의 '전기(비교)' 테이블에서 재작성값 추출).

    표시분기 스코프(`_in_scope`)를 걸지 않는다: `_DISPLAY_QUARTERS` 는 2026.2Q 를 아직
    포함하지 않는데 사이트는 그 분기를 그린다 — 스코프를 걸면 최신 분기가 검사 사각이 된다.
    """
    by_co: dict[str, dict[str, dict]] = {}
    for (co, q), m in env.wf.items():
        by_co.setdefault(co, {})[q] = m
    for co, qmap in sorted(by_co.items()):
        for q in sorted(qmap):
            try:
                fy = int(str(q)[:4])
            except ValueError:
                continue
            prev_close = (qmap.get(f"{fy - 1}.4Q") or {}).get("기말CSM")
            opening = (qmap.get(q) or {}).get("기초CSM")
            if prev_close is None or opening is None:
                continue
            gap = opening - prev_close
            if abs(gap) > max(CSM_CONT_TOL_REL * abs(prev_close), CSM_CONT_TOL_ABS):
                res.add(check="domain", severity="RED", master="CSM_waterfall", company=co,
                        quarter=q, rule="CSM_CONTINUITY_FY_BOUNDARY",
                        message=f"기초 CSM {opening:,.0f} != {fy - 1}.4Q 기말 {prev_close:,.0f} "
                                f"[Δ{gap:+,.0f}] — 기시≠직전기말은 면제 대상이 아니다. "
                                f"raw 대조로 재작성 근거를 확정하거나 마스터를 정정할 것")



def check_statutory_reserves(res: GateResult, env: "Env") -> None:
    """법정준비금 룰 R-RSV-1~12 (owner 발주 inbox/validation/20260819T0558Z).

    구현은 `scripts/validate_statutory_reserves.py` 한 곳에 있고 여기서는 **호출만** 한다
    (룰 로직을 두 벌로 만들지 않는다). 그 모듈이 하는 세 가지:

      1. 마스터(IFRS17_BS.json)만 보고 판정한다. raw 부호를 재해석하지 않는다 —
         부호 해석은 개념별·표별로 갈리고 그 지식은 이미 빌더에 있다. 2026-08-19 에
         validation 이 그걸 재구현했다가 NH농협손보 2026.2Q 를 297,481 로 오판했고
         parser 반박으로 309,489 가 정답으로 확정됐다(모듈 docstring 참조).
      2. legit-zero 는 `data/_gold/user_pl_confirmed_cells.json`(master="IFRS17_BS")로 면제.
      3. **래칫 baseline**: `data/_gold/statutory_reserve_baseline.json` 에 건별로 열거된
         기존 결함 58건은 비차단(BASELINE), 목록에 없는 새 RED 만 차단. CLAUDE.md 의
         "RED=0 또는 documented exception(회사·분기·룰·사유)" 계약을 기계검사 형태로 만족한다.
         parser 가 한 건 고칠 때마다 그 줄을 지운다.

    심각도는 이 파일의 기존 관례를 따른다 — IFRS17_BS 가 아직 어느 배포 HTML 에도 안 물리면
    YELLOW, 물리는 순간 RED 로 자동 승격(`check_ifrs17_bs._sev` 와 같은 규칙).
    """
    try:
        sys.path.insert(0, str(ROOT / "scripts"))
        import validate_statutory_reserves as rsv    # noqa: E402
    except Exception as e:
        res.add(check="census", severity="YELLOW", master="IFRS17_BS", company=None,
                quarter=None, rule="RESERVE_RULES_UNAVAILABLE",
                message=f"법정준비금 룰 모듈 로드 실패 — 이 축은 검사되지 않았다: {e}")
        return
    rows = env.ifrs17_bs
    if not rows:
        return
    findings = rsv.run(rows, rsv.load_registry())
    findings = rsv.apply_baseline(findings, rsv.load_baseline())

    counts = {"RED": 0, rsv.BASELINE_SEV: 0, "ORANGE": 0, "SUPPRESSED": 0}
    for f in findings:
        counts[f["severity"]] = counts.get(f["severity"], 0) + 1
        if f["severity"] == "SUPPRESSED":
            continue
        q = f.get("quarter")
        # 시계열 룰의 quarter 는 "2023.1Q~2024.3Q" 형태 구간일 수 있어 스코프 판정에 앞 분기를 쓴다.
        q_head = str(q).split("~")[0] if q else None
        if q_head and not (env.inject or _in_scope(q_head)):
            continue
        if f["severity"] == "RED":
            sev = "RED" if env.ifrs17_bs_published else "YELLOW"
            msg = f["message"] if env.ifrs17_bs_published else                 f["message"] + "  [미배포 — push 차단 보류]"
        else:
            sev = "YELLOW"
            msg = f["message"]
        res.add(check="census", severity=sev, master="IFRS17_BS",
                company=f.get("company"), quarter=q,
                rule=f["rule"].replace("-", "_"), message=msg)
    res.add(check="census", severity="YELLOW", master="IFRS17_BS", company=None, quarter=None,
            rule="RESERVE_RULES_SUMMARY",
            message=(f"법정준비금 R-RSV 룰: 신규 RED={counts['RED']} · "
                     f"기존 baseline={counts[rsv.BASELINE_SEV]}(건별 열거, "
                     f"data/_gold/statutory_reserve_baseline.json) · "
                     f"ORANGE={counts['ORANGE']} · legit-zero 면제={counts['SUPPRESSED']}. "
                     f"baseline 이 0 이 되면 이 축은 완전 차단 모드가 된다"))


def run_gate(env: Env) -> GateResult:
    res = GateResult()
    check_artifact_readable(res, env)
    check_ifrs17_bs(res, env)
    check_statutory_reserves(res, env)
    check_dividend(res, env)
    check_csm_continuity(res, env)
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
