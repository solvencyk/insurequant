# -*- coding: utf-8 -*-
"""`_CENSUS_SOURCE_ABSENT` (coverage census 원천부재 면제) 의 **변이시험**.

## 왜 이 파일이 있나

2026-10-10 재보사 단계 9 에서 owner 가 census `MISSING_CELLS` 칸 중 원천에 채울 것이 없는 칸의 등재 장치를
승인했다("공시 예정" 문서 · 사이트 미게시 · owner 수집 정책). 면제는 '끄기' 가 아니다 — 등재 칸마다 근거를
하나씩 흔들면(버킷 생김 · raw 새 문서 · 매니페스트 사유 변경 · 원장 근거 삭제/반증) 그 칸이 census RED 로
돌아오고 장치 RED 가 같이 뜨는 것을 여기서 증명한다. 라이브 마스터·라이브 원장을 읽고, 흔드는 것은
메모리 사본 또는 함수 인자로만 한다(디스크는 안 건드린다).
"""
from __future__ import annotations

import copy
import json
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
MASTER = ROOT / "kics_disclosure.json"
LEDGER = ROOT / "data" / "_gold" / "kics_exemption_provenance.json"

import validate_kics_disclosure as gate  # noqa: E402

REG = gate._CENSUS_SOURCE_ABSENT

# owner 승인 2026-10-10 범위 그대로 (inbox/validation/20261010T1300Z, downloader 런로그 9d §5).
APPROVED = {
    ("KR1102", "2023.2Q"): "DOCUMENT_PENDING_NOTICE",
    ("KR1102", "2023.3Q"): "DOCUMENT_PENDING_NOTICE",
    ("KR1104", "2023.4Q"): "DOCUMENT_PENDING_NOTICE",
    ("KR1104", "2024.1Q"): "DOCUMENT_PENDING_NOTICE",
    ("KR1104", "2025.3Q"): "NOT_POSTED",
    ("KR1105", "2023.2Q"): "DOCUMENT_PENDING_NOTICE",
    ("KR1107", "2023.1Q"): "COLLECTION_POLICY",
    ("KR1107", "2023.2Q"): "COLLECTION_POLICY",
}
KEYS = sorted(APPROVED)


@pytest.fixture(autouse=True)
def _memo_disk_reads(monkeypatch):
    """원장 마커 재확인(fitz 로 PDF 전문 읽기)과 raw sha 계산을 입력 단위로 기억한다 — 판정 로직은 그대로,
    같은 파일을 수십 번 다시 읽는 비용만 없앤다(이게 없으면 이 파일이 2분 반 걸린다)."""
    verify_real, raw_real = _REAL_VERIFY, _REAL_RAW

    def verify(spec):
        k = json.dumps(spec, ensure_ascii=False, sort_keys=True)
        if k not in _VERIFY_MEMO:
            _VERIFY_MEMO[k] = verify_real(spec)
        return _VERIFY_MEMO[k]

    def raw(code, quarter, root=None):
        k = (code, quarter, str(root))
        if k not in _RAW_MEMO:
            _RAW_MEMO[k] = raw_real(code, quarter, root)
        return dict(_RAW_MEMO[k])
    monkeypatch.setattr(gate, "_verify_absent_markers", verify)
    monkeypatch.setattr(gate, "_census_raw_state", raw)


_REAL_VERIFY, _REAL_RAW = gate._verify_absent_markers, gate._census_raw_state
_VERIFY_MEMO: dict = {}
_RAW_MEMO: dict = {}


@pytest.fixture(scope="module")
def records():
    raw = json.loads(MASTER.read_text(encoding="utf-8"))
    return raw["records"] if isinstance(raw, dict) else raw


@pytest.fixture(scope="module")
def census(records):
    return gate._coverage_census(records)


@pytest.fixture(scope="module")
def ledger():
    return json.loads(LEDGER.read_text(encoding="utf-8"))


def _run(records, census, **kw):
    return gate._census_source_absent(records, census["missing_rows"], **kw)


def _rules_for(red, key):
    return {r["rule"] for r in red if (r["code"], r["quarter"]) == key}


# ---------------------------------------------------------------------------
# 1. 범위와 라이브 상태
# ---------------------------------------------------------------------------
def test_registry_is_exactly_the_owner_approved_scope():
    assert {k: v["kind"] for k, v in REG.items()} == APPROVED
    assert all(v.get("approved") == "owner 2026-10-10" for v in REG.values())


def test_every_registered_cell_is_exempted_on_the_live_master(records, census):
    kept, exempted, red = _run(records, census)
    assert red == [], red
    assert {(c, q) for q, c, _n, _k, _a in exempted} == set(REG)
    kept_keys = {(c, q) for q, c, _n in kept}
    assert not (kept_keys & set(REG))
    # 면제는 등재분만 뺀다 — 결측 총수 = 남은 것 + 면제
    assert len(kept) + len(exempted) == len(census["missing_rows"])


def test_unregistered_missing_row_stays_red(records, census):
    fake = ("2026.2Q", "KR9999", "가짜정기공시사")
    kept, exempted, _red = gate._census_source_absent(records, census["missing_rows"] + [fake])
    assert fake in kept
    assert all(row[1] != "KR9999" for row in exempted)


# ---------------------------------------------------------------------------
# 2. 등재 칸마다 근거를 흔들면 RED 로 돌아온다
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("key", KEYS)
def test_bucket_appearing_is_inert_red(records, census, key):
    """마스터에 그 분기 버킷이 생기면 census 가 더는 결측으로 안 세고, 등재는 INERT RED(등재를 풀어라)."""
    c, q = key
    probe = copy.deepcopy(next(r for r in records if r.get("원보험사코드") == c))
    probe["공시분기"] = q
    recs = records + [probe]
    cen = gate._coverage_census(recs)
    _kept, exempted, red = gate._census_source_absent(recs, cen["missing_rows"])
    assert "CENSUS_EXEMPTION_INERT" in _rules_for(red, key)
    assert key not in {(cc, qq) for qq, cc, *_x in exempted}


@pytest.mark.parametrize("key", KEYS)
def test_new_raw_document_revives_red(records, census, key, monkeypatch):
    real = gate._census_raw_state

    def fake(code, quarter, root=None):
        out = dict(real(code, quarter, root))
        if (code, quarter) == key:
            out[f"data/disclosure/FYxxxx/raw/{code}_신판.pdf"] = "0" * 64
        return out
    monkeypatch.setattr(gate, "_census_raw_state", fake)
    kept, _ex, red = _run(records, census)
    assert "CENSUS_EXEMPTION_RAW_CHANGED" in _rules_for(red, key)
    assert key in {(c, q) for q, c, _n in kept}


@pytest.mark.parametrize("key", [k for k in KEYS if APPROVED[k] == "DOCUMENT_PENDING_NOTICE"])
def test_changed_raw_sha_revives_red(records, census, key, monkeypatch):
    real = gate._census_raw_state

    def fake(code, quarter, root=None):
        out = dict(real(code, quarter, root))
        if (code, quarter) == key:
            out = {p: "f" * 64 for p in out}
        return out
    monkeypatch.setattr(gate, "_census_raw_state", fake)
    kept, _ex, red = _run(records, census)
    assert "CENSUS_EXEMPTION_RAW_CHANGED" in _rules_for(red, key)
    assert key in {(c, q) for q, c, _n in kept}


@pytest.mark.parametrize("key", KEYS)
def test_manifest_reason_change_revives_red(records, census, key, monkeypatch):
    real = gate._census_manifest_entry

    def fake(code, quarter, root=None):
        e, why = real(code, quarter, root)
        if (code, quarter) == key and e is not None:
            e = dict(e, status="ok_kics_received")
        return e, why
    monkeypatch.setattr(gate, "_census_manifest_entry", fake)
    kept, _ex, red = _run(records, census)
    assert "CENSUS_EXEMPTION_MANIFEST_DRIFT" in _rules_for(red, key)
    assert key in {(c, q) for q, c, _n in kept}


@pytest.mark.parametrize("key", [k for k in KEYS if APPROVED[k] == "DOCUMENT_PENDING_NOTICE"])
def test_manifest_new_version_revives_red(records, census, key, monkeypatch):
    real = gate._census_manifest_entry

    def fake(code, quarter, root=None):
        e, why = real(code, quarter, root)
        if (code, quarter) == key and e is not None:
            e = dict(e, versions=[{"file": "신판.pdf"}])
        return e, why
    monkeypatch.setattr(gate, "_census_manifest_entry", fake)
    _kept, _ex, red = _run(records, census)
    assert "CENSUS_EXEMPTION_MANIFEST_DRIFT" in _rules_for(red, key)


@pytest.mark.parametrize("key", KEYS)
def test_ledger_entry_removed_revives_red(records, census, ledger, key):
    led = copy.deepcopy(ledger)
    led["entries"] = [e for e in led["entries"]
                      if not (e.get("registry") == "_CENSUS_SOURCE_ABSENT"
                              and (e.get("company"), e.get("quarter")) == key)]
    kept, _ex, red = _run(records, census, ledger=led)
    assert "CENSUS_EXEMPTION_LEDGER_DISAGREE" in _rules_for(red, key)
    assert key in {(c, q) for q, c, _n in kept}
    # 같은 원장으로 provenance 검사도 RED 를 낸다(두 겹)
    pred, _rv = gate._exemption_provenance_findings(ledger=led)
    assert any(r["rule"] == "EXEMPTION_PROVENANCE_MISSING" and r["registry"] == "_CENSUS_SOURCE_ABSENT"
               and (r["code"], r["quarter"]) == key for r in pred)


@pytest.mark.parametrize("key", KEYS)
def test_ledger_evidence_contradicted_revives_red(records, census, ledger, key):
    """근거 문구가 인용 원천에서 사라졌다(= 원천이 바뀌었다)를 흉내 낸다 — 없는 문구를 근거로 요구한다."""
    led = copy.deepcopy(ledger)
    for e in led["entries"]:
        if e.get("registry") == "_CENSUS_SOURCE_ABSENT" and (e.get("company"), e.get("quarter")) == key:
            e["verify"]["present_markers"] = list(e["verify"]["present_markers"]) + ["존재하지않는근거문구XYZ"]
    kept, _ex, red = _run(records, census, ledger=led)
    assert "CENSUS_EXEMPTION_LEDGER_DISAGREE" in _rules_for(red, key)
    assert key in {(c, q) for q, c, _n in kept}


@pytest.mark.parametrize("key", KEYS)
def test_ledger_kind_disagreeing_with_code_is_red(records, census, ledger, key):
    led = copy.deepcopy(ledger)
    for e in led["entries"]:
        if e.get("registry") == "_CENSUS_SOURCE_ABSENT" and (e.get("company"), e.get("quarter")) == key:
            e["claim_kind"] = "NOT_POSTED" if APPROVED[key] != "NOT_POSTED" else "COLLECTION_POLICY"
    _kept, _ex, red = _run(records, census, ledger=led)
    assert "CENSUS_EXEMPTION_LEDGER_DISAGREE" in _rules_for(red, key)


def test_absent_marker_appearing_contradicts_pending_notice(records, census, ledger):
    """공시 예정형은 K-ICS 표제어 부재도 박제한다 — K-ICS 표가 실린 판이 같은 파일로 들어오면 반증된다.
    여기서는 같은 회사의 K-ICS 수록 신판(스위스리 2023.4Q v20240510)을 인용 파일로 바꿔 끼워 흉내 낸다."""
    key = ("KR1102", "2023.2Q")
    led = copy.deepcopy(ledger)
    for e in led["entries"]:
        if e.get("registry") == "_CENSUS_SOURCE_ABSENT" and (e.get("company"), e.get("quarter")) == key:
            e["verify"]["file"] = "data/disclosure/FY2023_Q4/raw/KR1102_스위스리아시아_v20240510.pdf"
            e["verify"]["present_markers"] = []
    _kept, _ex, red = _run(records, census, ledger=led)
    assert any("부재 주장 반증" in r["detail"] for r in red if (r["code"], r["quarter"]) == key)


def test_malformed_entry_is_red_not_exempt(records, census):
    reg = dict(REG)
    reg[("KR1104", "2025.3Q")] = {"kind": "SOMETHING_ELSE", "approved": "owner 2026-10-10", "raw": {}}
    reg[("KR1107", "2023.1Q")] = {"kind": "COLLECTION_POLICY", "approved": "", "raw": {}}
    reg[("KR1102", "2023.2Q")] = {"kind": "DOCUMENT_PENDING_NOTICE", "approved": "owner 2026-10-10", "raw": {}}
    kept, exempted, red = _run(records, census, registry=reg)
    for key in (("KR1104", "2025.3Q"), ("KR1107", "2023.1Q"), ("KR1102", "2023.2Q")):
        assert "CENSUS_EXEMPTION_MALFORMED" in _rules_for(red, key)
        assert key in {(c, q) for q, c, _n in kept}
        assert key not in {(c, q) for q, c, *_x in exempted}


def test_empty_registry_exempts_nothing(records, census):
    kept, exempted, red = _run(records, census, registry={})
    assert exempted == [] and red == [] and kept == census["missing_rows"]


# ---------------------------------------------------------------------------
# 3. 배선 — 근거 원장 · 두 게이트 · exit code
# ---------------------------------------------------------------------------
def test_registry_is_wired_into_provenance():
    assert "_CENSUS_SOURCE_ABSENT" in gate._exemption_registries()
    assert gate._exemption_registries()["_CENSUS_SOURCE_ABSENT"] == frozenset(REG)


def test_every_registered_cell_has_a_verified_ledger_entry(ledger):
    have = {(e.get("company"), e.get("quarter")): e for e in ledger["entries"]
            if e.get("registry") == "_CENSUS_SOURCE_ABSENT"}
    assert set(have) == set(REG), "원장과 코드 등재 칸이 다르다"
    for key, spec in REG.items():
        e = have[key]
        assert e.get("status") == "VERIFIED"
        assert e.get("claim_kind") == spec["kind"]
        v = e.get("verify") or {}
        assert v.get("file") and v.get("present_markers")
        assert "협회" in e.get("note", ""), "원천 부재 근거의 한계(협회 공시 미확인)를 원장에 적는다"
        contradicted, why = gate._verify_absent_markers(v)
        assert not contradicted, why


def test_raw_pins_match_disk_and_manifest():
    for (c, q), spec in REG.items():
        assert gate._census_raw_state(c, q) == spec["raw"], (c, q)
        e, why = gate._census_manifest_entry(c, q)
        assert e is not None, why
        assert e.get("status") == gate._CENSUS_KINDS[spec["kind"]]["manifest_status"]


def test_both_gates_call_the_same_function():
    """데이터계약 게이트가 면제를 재구현하지 않고 같은 함수를 부른다(두 게이트가 같은 대답)."""
    src = (ROOT / "scripts" / "validate_data_contract.py").read_text(encoding="utf-8")
    assert "_census_source_absent(" in src
    assert not re.search(r"(?<![A-Za-z])_CENSUS_SOURCE_ABSENT\b", src), "레지스트리를 복사했다 — 위임해야 한다"
    assert "MISSING_FILER_CELL_SOURCE_ABSENT" in src, "면제 칸을 매 실행 인쇄하지 않는다"
    # 데이터계약 게이트의 룰엔진 위임이 K-ICS 게이트와 같은 입력(원천부재 등재부 포함)을 받는다
    assert "life_subrisk_source_absent=_load_life_subrisk_source_absent()" in src
    assert "tfi_applicability=_load_tfi_applicability()" in src
    gsrc = (ROOT / "scripts" / "validate_kics_disclosure.py").read_text(encoding="utf-8")
    assert "census_red = len(census_kept)" in gsrc
    assert "or census_exempt_red" in gsrc, "면제가 깨졌을 때 exit code 에 안 들어간다"
    assert '"source_absent_exemption"' in gsrc, "면제 기록이 아티팩트에 안 남는다"


def test_data_contract_census_uses_the_device(records):
    """데이터계약 게이트 check_census 의 결과에서 등재 칸이 RED 가 아니라 YELLOW 로 인쇄된다(표시 분기분)."""
    import validate_data_contract as dc
    # inject 모드는 스코프를 전 분기로 연다(_emit) — 등재 8칸 전부가 이 절을 지나간다. 등재부는 명시적으로
    # None(= 정본 레지스트리)을 주입한다(inject 기본값은 빈 맵 = selftest 격리).
    env = dc.Env(inject={"kics_records": records, "delegate_kics": False,
                         "census_source_absent": None})
    res = dc.GateResult()
    dc.check_census(res, env)
    red_keys = {(f.company, f.quarter) for f in res.red if f.rule == "MISSING_FILER_CELL"}
    yel = {(f.company, f.quarter) for f in res.yellow if f.rule == "MISSING_FILER_CELL_SOURCE_ABSENT"}
    names = {c: env.code_name.get(c, c) for c, _q in REG}
    for c, q in REG:
        assert (names[c], q) not in red_keys
        assert (names[c], q) in yel
    assert not [f for f in res.red if f.rule.startswith("KICS_CENSUS_EXEMPTION_")]
    # 등재 안 된 결측은 여전히 RED
    cen = gate._coverage_census(records)
    for q, c, n in cen["missing_rows"]:
        if (c, q) not in REG:
            assert (n, q) in red_keys
