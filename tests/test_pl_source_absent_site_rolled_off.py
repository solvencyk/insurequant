# -*- coding: utf-8 -*-
"""서울보증보험 KR0150 PL 2024.2Q·2024.3Q 원천부재 등재(`SITE_ROLLED_OFF`)의 **변이시험** (owner 승인 2026-10-12).

배경: 서울보증은 회사 사이트가 지난 분기 공시를 내려(다운로더 `NO_RAW_PDF` 최종) PL 2024.2Q·2024.3Q 가 통째 구멍이다.
하노버(재보사)와 달리 전용 매니페스트(`reinsurer_{code}_manifest.json`)가 없어서, 매니페스트 자리를 다운로더의
사이트 판 census 가 대신한다(`validate_kics_disclosure._site_edition_census_cell`). 이 파일은 그 **새 읽는 쪽**과
**쓰는 쪽 재검산**(raw 폴더·census status·원장·인용)을 각각 변이시킨다. 하노버 쪽은 `test_pl_source_absent_exemption.py`.
"""
from __future__ import annotations

import copy
import json
import sys
import types
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

import validate_kics_disclosure as K  # noqa: E402

KEYS = [("KR0150", "2024.2Q"), ("KR0150", "2024.3Q")]
LEDGER_PATH = ROOT / "data" / "_gold" / "kics_exemption_provenance.json"
CENSUS_REL = "data/disclosure/_meta/site_edition_census_result_20261011.json"
NAMES = {"KR0150": "서울보증보험"}


def _ledger():
    return json.loads(LEDGER_PATH.read_text(encoding="utf-8"))


def _present():
    # 서울보증의 다른 분기 버킷만 있고 2024.2Q·2024.3Q 는 없다(= 실제 마스터의 모양)
    return {("KR0150", "2024.1Q"), ("KR0150", "2024.4Q"), ("KR0150", "2025.1Q")}


def _run(ledger=None, registry=None, present=None, root=None):
    return K.pl_source_absent_exemptions(
        present if present is not None else _present(), NAMES,
        registry=registry, ledger=ledger if ledger is not None else _ledger(), root=root)


def _only(keys):
    return {k: v for k, v in K._PL_SOURCE_ABSENT.items() if k in keys}


def _ledger_with(mutator, key=None):
    led = _ledger()
    for e in led["entries"]:
        if e.get("registry") == "_PL_SOURCE_ABSENT" and (key is None or (e["company"], e["quarter"]) == key):
            mutator(e)
    return led


def _rules(red, key):
    return {r["rule"] for r in red if (r["code"], r["quarter"]) == key}


# ---------------------------------------------------------------------------------------------------
# 등재 범위 = owner 승인 (서울보증 2칸), 코드·원장 일치
# ---------------------------------------------------------------------------------------------------
def test_registry_scope_is_the_two_approved_cells_and_ledger_agrees():
    got = {k: v for k, v in K._PL_SOURCE_ABSENT.items() if k[0] == "KR0150"}
    assert set(got) == set(KEYS), f"서울보증 등재 범위가 owner 승인(2026-10-12, 2024.2Q·3Q)과 다르다: {sorted(got)}"
    for k in KEYS:
        spec = got[k]
        assert spec["kind"] == "SITE_ROLLED_OFF" and spec["raw"] == {} and "2026-10-12" in spec["approved"]
    led = {(e["company"], e["quarter"]): e for e in _ledger()["entries"]
           if e.get("registry") == "_PL_SOURCE_ABSENT" and e["company"] == "KR0150"}
    assert set(led) == set(KEYS)
    for k in KEYS:
        assert led[k]["status"] == "VERIFIED" and led[k]["claim_kind"] == "SITE_ROLLED_OFF"
        assert led[k]["citation"]["file"] == CENSUS_REL
    assert K._exemption_registries()["_PL_SOURCE_ABSENT"] == frozenset(K._PL_SOURCE_ABSENT)


def test_live_baseline_passes_and_pl_master_really_has_no_bucket():
    ok, red = _run(registry=_only(KEYS))
    assert set(ok) == set(KEYS) and not red, red
    rows = json.loads((ROOT / "PL_breakdown.json").read_text(encoding="utf-8"))
    for c, q in KEYS:
        assert not [r for r in rows if r["원보험사코드"] == c and r["공시분기"] == q]
    # 원천이 정말 없다: 그 분기 raw 폴더에 KR0150 파일 0, 이듬해 같은 분기 공시(전년동기 열의 출처)도 0
    for fy in ("FY2024_Q2", "FY2024_Q3", "FY2025_Q2", "FY2025_Q3"):
        d = ROOT / "data" / "disclosure" / fy / "raw"
        assert not list(d.glob("KR0150[._]*")), (fy, list(d.glob("KR0150[._]*")))


# ---------------------------------------------------------------------------------------------------
# 쓰는 쪽 -- 재검산이 깨지면 면제가 없고 장치 RED 가 난다
# ---------------------------------------------------------------------------------------------------
def _tmp_root(tmp_path, mutate_cells=None, add_raw_for=None):
    """사이트 판 census(복사본)·raw 폴더만 흉내 낸 임시 루트. 원장 인용 원천은 실제 ROOT 의 것을 쓴다."""
    meta = tmp_path / "data" / "disclosure" / "_meta"
    meta.mkdir(parents=True)
    census = json.loads((ROOT / CENSUS_REL).read_text(encoding="utf-8"))
    if mutate_cells:
        census["cells"] = mutate_cells(census["cells"])
    (tmp_path / CENSUS_REL).write_text(json.dumps(census, ensure_ascii=False), encoding="utf-8")
    for fy in ("FY2024_Q2", "FY2024_Q3"):
        (tmp_path / "data" / "disclosure" / fy / "raw").mkdir(parents=True)
    if add_raw_for:
        c, q = add_raw_for
        d = tmp_path / "data" / "disclosure" / f"FY{q[:4]}_Q{q[5]}" / "raw"
        (d / f"{c}_서울보증보험.pdf").write_bytes(b"%PDF-1.4 fake")
    return tmp_path


def test_tmp_root_baseline_passes(tmp_path):
    ok, red = _run(registry=_only(KEYS), root=_tmp_root(tmp_path))
    assert set(ok) == set(KEYS) and not red, red


@pytest.mark.parametrize("key", KEYS)
def test_a_new_raw_document_breaks_it(tmp_path, key):
    """사이트가 그 분기를 다시 게시해 raw 가 들어오면 면제 무효 -- parser 가 적재하고 등재를 풀 차례다."""
    ok, red = _run(registry=_only(KEYS), root=_tmp_root(tmp_path, add_raw_for=key))
    assert key not in ok and "PL_SOURCE_ABSENT_RAW_CHANGED" in _rules(red, key)
    assert (set(KEYS) - {key}) <= set(ok)          # 다른 칸은 영향 없다


@pytest.mark.parametrize("key", KEYS)
def test_census_status_drift_breaks_it(tmp_path, key):
    def mut(cells):
        return [dict(c, status="OK") if (c["kr"], c["q"]) == key else c for c in cells]
    ok, red = _run(registry=_only(KEYS), root=_tmp_root(tmp_path, mutate_cells=mut))
    assert key not in ok and "PL_SOURCE_ABSENT_MANIFEST_DRIFT" in _rules(red, key)


@pytest.mark.parametrize("key", KEYS)
def test_census_cell_missing_or_duplicated_breaks_it(tmp_path, key):
    def gone(cells):
        return [c for c in cells if (c["kr"], c["q"]) != key]

    def dup(cells):
        return cells + [c for c in cells if (c["kr"], c["q"]) == key]

    for label, mut in (("gone", gone), ("dup", dup)):
        ok, red = _run(registry=_only(KEYS), root=_tmp_root(tmp_path / label, mutate_cells=mut))
        assert key not in ok and "PL_SOURCE_ABSENT_MANIFEST_DRIFT" in _rules(red, key)


def test_census_file_absent_breaks_it(tmp_path):
    """census 도 전용 매니페스트도 없는 루트 -- 근거가 없으면 면제도 없다(결측은 SKIP 이 아니라 RED)."""
    ok, red = _run(registry=_only(KEYS), root=tmp_path)
    assert not ok and all("PL_SOURCE_ABSENT_MANIFEST_DRIFT" in _rules(red, k) for k in KEYS)


def test_other_kind_does_not_accept_the_census_status(tmp_path):
    """NOT_POSTED(재보사용, status not_posted)로 적으면 census 의 NO_RAW 가 안 맞아 MANIFEST_DRIFT -- 사유 종류가 상태를 고른다."""
    reg = {k: dict(v, kind="NOT_POSTED") for k, v in _only(KEYS).items()}
    ok, red = _run(registry=reg, root=_tmp_root(tmp_path))
    assert not ok
    rules = {r["rule"] for r in red}
    assert "PL_SOURCE_ABSENT_MANIFEST_DRIFT" in rules and "PL_SOURCE_ABSENT_LEDGER_DISAGREE" in rules


def test_ledger_record_missing_breaks_it():
    led = _ledger()
    led["entries"] = [e for e in led["entries"] if not (e.get("registry") == "_PL_SOURCE_ABSENT" and e["company"] == "KR0150")]
    ok, red = _run(registry=_only(KEYS), ledger=led)
    assert not ok and all("PL_SOURCE_ABSENT_LEDGER_DISAGREE" in _rules(red, k) for k in KEYS)


def test_k_ics_ledger_record_does_not_cover_pl():
    """원장에 K-ICS 쪽(`_CENSUS_SOURCE_ABSENT`)으로 같은 키를 적어도 PL 면제는 안 생긴다 -- 덮어쓰기 금지."""
    led = _ledger()
    moved = []
    for e in led["entries"]:
        if e.get("registry") == "_PL_SOURCE_ABSENT" and e["company"] == "KR0150":
            moved.append(dict(e, registry="_CENSUS_SOURCE_ABSENT"))
    led["entries"] = [e for e in led["entries"] if not (e.get("registry") == "_PL_SOURCE_ABSENT" and e["company"] == "KR0150")] + moved
    ok, red = _run(registry=_only(KEYS), ledger=led)
    assert not ok


def test_ledger_claim_kind_mismatch_breaks_it():
    ok, red = _run(registry=_only(KEYS), ledger=_ledger_with(lambda e: e.update(claim_kind="NOT_POSTED"), key=KEYS[0]))
    assert KEYS[0] not in ok and "PL_SOURCE_ABSENT_LEDGER_DISAGREE" in _rules(red, KEYS[0])
    assert KEYS[1] in ok


def test_ledger_status_not_verified_breaks_it():
    ok, red = _run(registry=_only(KEYS), ledger=_ledger_with(lambda e: e.update(status="UNVERIFIED"), key=KEYS[1]))
    assert KEYS[1] not in ok and "PL_SOURCE_ABSENT_LEDGER_DISAGREE" in _rules(red, KEYS[1])


def test_ledger_marker_contradicted_breaks_it():
    """인용 원천(census)에 근거 문구가 사라지면(= census 가 그 분기를 NO_RAW 가 아니라고 바꾸면) 면제가 무효다."""
    def mut(e):
        v = copy.deepcopy(e["verify"])
        v["present_markers"] = list(v["present_markers"]) + ["이 문구는 원천에 없다 zz-not-in-census"]
        e["verify"] = v
    ok, red = _run(registry=_only(KEYS), ledger=_ledger_with(mut))
    assert not ok and all("PL_SOURCE_ABSENT_LEDGER_DISAGREE" in _rules(red, k) for k in KEYS)


def test_ledger_without_markers_breaks_it():
    ok, red = _run(registry=_only(KEYS), ledger=_ledger_with(lambda e: e.update(verify={"file": CENSUS_REL})))
    assert not ok and all("PL_SOURCE_ABSENT_LEDGER_DISAGREE" in _rules(red, k) for k in KEYS)


@pytest.mark.parametrize("key", KEYS)
def test_bucket_appearing_in_master_makes_it_inert_red(key):
    ok, red = _run(registry=_only(KEYS), present=_present() | {key})
    assert key not in ok and "PL_SOURCE_ABSENT_INERT" in _rules(red, key)


def test_hannover_notposted_still_uses_its_own_manifest():
    """재보사는 전용 매니페스트를 그대로 쓴다(census 대체는 전용 매니페스트가 없을 때만) -- 하노버 판정이 안 바뀐다."""
    cell, why = K._census_manifest_entry("KR1104", "2025.3Q")
    assert cell is not None and cell.get("status") == "not_posted", why
    cell2, _ = K._census_manifest_entry("KR0150", "2024.2Q")
    assert cell2 is not None and cell2.get("status") == "NO_RAW"


# ---------------------------------------------------------------------------------------------------
# 소스 변이 -- 새 읽는 분기(census 대체)를 지우면 시험이 깨져야 한다
# ---------------------------------------------------------------------------------------------------
def _mutant(path: Path, name: str, repl):
    src = path.read_text(encoding="utf-8")
    for old, new in repl:
        assert src.count(old) == 1, f"변이 앵커가 정확히 1번 있어야 한다: {old!r} ({src.count(old)}회)"
        src = src.replace(old, new)
    mod = types.ModuleType(name)
    mod.__file__ = str(path)
    sys.modules[name] = mod
    try:
        exec(compile(src, str(path), "exec"), mod.__dict__)  # noqa: S102
    except BaseException:
        sys.modules.pop(name, None)
        raise
    return mod


def test_mutant_census_fallback_removed_leaves_it_red():
    mod = _mutant(ROOT / "scripts" / "validate_kics_disclosure.py", "_mut_k_fallback",
                  [("    if not p.exists():\n        # 재보사가 아닌 회사", "    if False:\n        # 재보사가 아닌 회사")])
    try:
        ok, red = mod.pl_source_absent_exemptions(_present(), NAMES, registry=_only(KEYS), ledger=_ledger())
    finally:
        sys.modules.pop("_mut_k_fallback", None)
    assert not ok and any(r["rule"] == "PL_SOURCE_ABSENT_MANIFEST_DRIFT" for r in red), \
        "census 대체 분기를 지웠는데도 면제가 통과했다 -- 시험이 무력하다"


def test_mutant_status_check_removed_would_accept_wrong_status(tmp_path):
    """사유 종류별 status 비교를 지우면 census 상태가 OK 로 바뀌어도 통과해 버린다 -- 이 변이를 시험이 잡아야 한다."""
    def mut(cells):
        return [dict(c, status="OK") if (c["kr"], c["q"]) == KEYS[0] else c for c in cells]
    root = _tmp_root(tmp_path, mutate_cells=mut)
    ok_real, _ = _run(registry=_only(KEYS), root=root)
    assert KEYS[0] not in ok_real                                   # 실물은 막는다
    mod = _mutant(ROOT / "scripts" / "validate_kics_disclosure.py", "_mut_k_status",
                  [("            if st != k[\"manifest_status\"]:", "            if False:")])
    try:
        ok_mut, _r = mod.pl_source_absent_exemptions(_present(), NAMES, registry=_only(KEYS), ledger=_ledger(), root=root)
    finally:
        sys.modules.pop("_mut_k_status", None)
    assert KEYS[0] in ok_mut, "status 비교를 지운 변이가 통과하지 않는다 -- 이 시험이 status 비교를 못 본다"
