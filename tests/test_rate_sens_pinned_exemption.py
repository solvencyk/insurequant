# -*- coding: utf-8 -*-
"""금리민감도 게이트 RS1·RS5 **근거 박제 면제 장치**(`rs_pinned_exemptions`)의 변이시험.

## 왜 이 파일이 있나

2026-10-10 재보사 단계 11 뒤 금리민감도 게이트에 RED 5건이 남았다 — 제네럴재보험(KR1103) 2026.2Q +100bp 의
발행사 표 자기모순(RS1, 적용전·적용후)과 마이브라운(KR1108) 2025.2Q·2025.4Q·2026.2Q 의 원천 부재(RS5).
owner 가 등재를 승인했는데, 이 게이트의 기존 등재부(RS1/RS2/RS5_EXCEPTIONS)는 **키 집합**이라 근거를 다시 보지
않는다. 그래서 K-ICS 게이트의 `_IDENT_ISSUER_INCONSISTENT`·`_CENSUS_SOURCE_ABSENT` 와 같은 사상의 장치를 새로
만들었고(inbox/validation/20261010T1830Z), 이 파일은 그 장치가 '끄기' 가 아님을 증명한다:
등재 5칸마다 근거를 하나씩 흔들면(원장 삭제·종류 불일치·마커 반증·raw sha·매니페스트·셀 값·잔차·버킷 생김)
그 칸이 원래 RED 로 돌아오고 장치 RED 가 같이 뜬다. 라이브 마스터·원장을 읽고, 흔드는 것은 메모리 사본·함수
인자·tmp 디렉터리뿐이다(저장소 디스크는 안 건드린다).
"""
from __future__ import annotations

import copy
import json
import shutil
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

import validate_kics_disclosure as gate  # noqa: E402
import validate_kics_rate_sensitivity as RS  # noqa: E402

# owner 승인 2026-10-10 범위 그대로 — 늘거나 줄면 여기서 막힌다(조용히 넓어지는 면제 금지).
APPROVED_RS1 = {("KR1103", "2026.2Q"): {"RS1|적용전|+100bp", "RS1|적용후|+100bp"}}
APPROVED_RS5 = {("KR1108", "2025.2Q"): "SECTION_ABSENT",
                ("KR1108", "2025.4Q"): "STATED_NOT_APPLICABLE",
                ("KR1108", "2026.2Q"): "STATED_NOT_APPLICABLE"}
DEVICE_RULES = {"RS_EXEMPTION_MALFORMED", "RS_EXEMPTION_INERT", "RS_EXEMPTION_CELL_MISSING",
                "RS_EXEMPTION_CELL_DRIFT", "RS_EXEMPTION_RESIDUAL_DRIFT", "RS_EXEMPTION_RAW_CHANGED",
                "RS_EXEMPTION_MANIFEST_DRIFT", "RS_EXEMPTION_LEDGER_DISAGREE"}

_REAL_VERIFY = gate._verify_absent_markers
_MEMO: dict = {}


@pytest.fixture(autouse=True)
def _memo_marker_reads(monkeypatch):
    """원장 마커 재확인(fitz 로 PDF 읽기)을 입력 단위로 기억한다 — 판정은 그대로, 같은 파일 재독 비용만 없앤다."""
    def verify(spec):
        k = json.dumps(spec, ensure_ascii=False, sort_keys=True)
        if k not in _MEMO:
            _MEMO[k] = _REAL_VERIFY(spec)
        return _MEMO[k]
    monkeypatch.setattr(gate, "_verify_absent_markers", verify)


@pytest.fixture(scope="module")
def live():
    rs_rows, kd_rows = RS.load_rs(), RS.load_kd()
    ledger = gate._load_exemption_ledger()
    return rs_rows, kd_rows, ledger


def _run(live, rows=None, ledger=None, reg1=None, reg5=None, root=None):
    rs_rows, kd_rows, led = live
    return RS.run(rs_rows if rows is None else rows, kd_rows,
                  ledger=led if ledger is None else ledger, root=root,
                  rs1_registry=reg1, rs5_registry=reg5)


def _ledger_without(led, registry, code, quarter):
    out = copy.deepcopy(led)
    out["entries"] = [e for e in out["entries"]
                      if (e.get("registry"), e.get("company"), e.get("quarter")) != (registry, code, quarter)]
    return out


def _ledger_edit(led, registry, code, quarter, fn):
    out = copy.deepcopy(led)
    for e in out["entries"]:
        if (e.get("registry"), e.get("company"), e.get("quarter")) == (registry, code, quarter):
            fn(e)
    return out


def _rules(res, code, quarter):
    return {f["rule"] for f in res["pin_red"] if (f["code"], f["quarter"]) == (code, quarter)}


def _rs1_back(res, name="제네럴재보험", q="2026.2Q"):
    return {(r[2], r[3]) for r in res["rs1"] if r[0] == name and r[1] == q}


def _rs5_back(res, code, q):
    return any(r[0] == code and r[2] == q for r in res["rs5"])


# ---------------------------------------------------------------------------
# 0. 등재 범위·라이브 상태
# ---------------------------------------------------------------------------
def test_registries_match_owner_approval():
    assert {k: set(v["findings"]) for k, v in RS._RS1_ISSUER_INCONSISTENT.items()} == APPROVED_RS1
    assert {k: v["kind"] for k, v in RS._RS5_SOURCE_ABSENT.items()} == APPROVED_RS5
    for spec in list(RS._RS1_ISSUER_INCONSISTENT.values()) + list(RS._RS5_SOURCE_ABSENT.values()):
        assert spec["approved"] == "owner 2026-10-10" and spec["raw"]


def test_live_all_five_exempted_and_device_clean(live):
    res = _run(live)
    assert res["pin_red"] == [], res["pin_red"]
    assert {(r[2], r[3]) for r in res["rs1_pinned"]} == {("적용전", "+100bp"), ("적용후", "+100bp")}
    assert {(r[0], r[2]) for r in res["rs5_pinned"]} == set(APPROVED_RS5)
    assert not _rs1_back(res) and not any(r[0] == "KR1108" for r in res["rs5"])


def test_empty_registries_leave_all_five_red(live):
    """등재가 없으면 다섯 칸 모두 RED — 장치가 아무것도 숨기지 않는다는 기준선."""
    res = _run(live, reg1={}, reg5={})
    assert _rs1_back(res) == {("적용전", "+100bp"), ("적용후", "+100bp")}
    assert all(_rs5_back(res, *k) for k in APPROVED_RS5)
    assert res["pin_red"] == []


def test_device_rule_ids_match_source():
    import re
    src = (ROOT / "scripts" / "validate_kics_rate_sensitivity.py").read_text(encoding="utf-8")
    found = set(re.findall(r"\b(RS_EXEMPTION_[A-Z_]+)\b", src)) - {"RS_EXEMPTION_REGISTRIES"}
    assert found == DEVICE_RULES


# ---------------------------------------------------------------------------
# 1. 근거 원장 — 5칸 전부 × {삭제 · 종류 불일치 · status · 마커 반증}
# ---------------------------------------------------------------------------
_ALL = ([("_RS1_ISSUER_INCONSISTENT",) + k for k in APPROVED_RS1]
        + [("_RS5_SOURCE_ABSENT",) + k for k in APPROVED_RS5])


def _assert_back(res, reg, code, q):
    if reg == "_RS1_ISSUER_INCONSISTENT":
        assert _rs1_back(res) == {("적용전", "+100bp"), ("적용후", "+100bp")}
    else:
        assert _rs5_back(res, code, q)
    assert res["gate_red"] > 0


@pytest.mark.parametrize("reg,code,q", _ALL)
@pytest.mark.parametrize("how", ["deleted", "claim_kind", "status", "marker_contradicted"])
def test_ledger_mutation_brings_red_back(live, reg, code, q, how):
    led = live[2]
    if how == "deleted":
        mut = _ledger_without(led, reg, code, q)
    elif how == "claim_kind":
        mut = _ledger_edit(led, reg, code, q, lambda e: e.update(claim_kind="NOT_POSTED"))
    elif how == "status":
        mut = _ledger_edit(led, reg, code, q, lambda e: e.update(status="UNVERIFIED"))
    else:
        def bad(e):
            v = e["verify"]
            v["present_markers"] = [m + "없는문장" for m in v.get("present_markers", [])]
        mut = _ledger_edit(led, reg, code, q, bad)
    res = _run(live, ledger=mut)
    assert "RS_EXEMPTION_LEDGER_DISAGREE" in _rules(res, code, q)
    _assert_back(res, reg, code, q)


def test_rs5_absent_marker_refuted_by_a_document_with_the_table(live):
    """마이브라운 마커를 표가 있는 하노버 2026.2Q 문서에 대면 부재 주장이 반증된다(마커가 변별력이 있다)."""
    def swap(e):
        e["verify"]["file"] = "data/disclosure/FY2026_Q2/raw/KR1104_하노버재보험.pdf"
    res = _run(live, ledger=_ledger_edit(live[2], "_RS5_SOURCE_ABSENT", "KR1108", "2026.2Q", swap))
    det = " ".join(f["detail"] for f in res["pin_red"])
    assert "부재 주장 반증" in det and _rs5_back(res, "KR1108", "2026.2Q")


def test_rs1_ledger_residual_disagreeing_with_code_is_red(live):
    def bump(e):
        e["expected_residual"]["RS1|적용후|+100bp"] = 2.9
    res = _run(live, ledger=_ledger_edit(live[2], "_RS1_ISSUER_INCONSISTENT", "KR1103", "2026.2Q", bump))
    assert "RS_EXEMPTION_LEDGER_DISAGREE" in _rules(res, "KR1103", "2026.2Q")
    _assert_back(res, "_RS1_ISSUER_INCONSISTENT", "KR1103", "2026.2Q")


# ---------------------------------------------------------------------------
# 2. raw 박제·형식 — 5칸 전부 × {sha 바뀜 · 새 파일 · 종류 · 승인 · raw 비움}
# ---------------------------------------------------------------------------
def _reg_copy(reg, code, q, fn):
    base = RS._RS1_ISSUER_INCONSISTENT if reg == "_RS1_ISSUER_INCONSISTENT" else RS._RS5_SOURCE_ABSENT
    out = copy.deepcopy(base)
    fn(out[(code, q)])
    return ({"reg1": out} if reg == "_RS1_ISSUER_INCONSISTENT" else {"reg5": out})


@pytest.mark.parametrize("reg,code,q", _ALL)
@pytest.mark.parametrize("how,rule", [("sha", "RS_EXEMPTION_RAW_CHANGED"),
                                      ("extra_file", "RS_EXEMPTION_RAW_CHANGED"),
                                      ("kind", "RS_EXEMPTION_MALFORMED"),
                                      ("approved", "RS_EXEMPTION_MALFORMED"),
                                      ("raw_empty", "RS_EXEMPTION_MALFORMED")])
def test_registry_mutation_brings_red_back(live, reg, code, q, how, rule):
    def fn(spec):
        p = next(iter(spec["raw"]))
        if how == "sha":
            spec["raw"][p] = "0" * 64
        elif how == "extra_file":
            spec["raw"][p.replace(".pdf", "_v2.pdf")] = "1" * 64
        elif how == "kind":
            spec["kind"] = "DOCUMENT_PENDING_NOTICE"
        elif how == "approved":
            spec["approved"] = ""
        else:
            spec["raw"] = {}
    res = _run(live, **_reg_copy(reg, code, q, fn))
    assert rule in _rules(res, code, q), res["pin_red"]
    _assert_back(res, reg, code, q)


def test_manifest_drift_and_new_document_on_disk(live, tmp_path):
    """tmp 루트에 raw·매니페스트를 복사해 ① 매니페스트 status 를 바꾸면 MANIFEST_DRIFT ② raw 폴더에 새 판이
    생기면 RAW_CHANGED — 다운로더가 새 문서를 받아 오면 등재가 자동으로 재판정 대상이 된다."""
    code, q, fy = "KR1108", "2025.2Q", "FY2025_Q2"
    src = ROOT / "data" / "disclosure" / fy / "raw"
    dst = tmp_path / "data" / "disclosure" / fy / "raw"
    dst.mkdir(parents=True)
    for p in src.glob(f"{code}[._]*"):
        shutil.copy2(p, dst / p.name)
    man_rel = Path("data/disclosure/_meta/reinsurer_KR1108_manifest.json")
    (tmp_path / man_rel).parent.mkdir(parents=True, exist_ok=True)
    man = json.loads((ROOT / man_rel).read_text(encoding="utf-8"))
    (tmp_path / man_rel).write_text(json.dumps(man, ensure_ascii=False), encoding="utf-8")
    only = {(code, q): RS._RS5_SOURCE_ABSENT[(code, q)]}
    res = _run(live, root=tmp_path, reg1={}, reg5=only)
    assert res["pin_red"] == [] and _rs5_back(res, code, q) is False      # 복사본이 원본과 같으면 통과
    for e in man["periods"]:
        if e.get("period") == q:
            e["status"] = "not_posted"
    (tmp_path / man_rel).write_text(json.dumps(man, ensure_ascii=False), encoding="utf-8")
    res = _run(live, root=tmp_path, reg1={}, reg5=only)
    assert "RS_EXEMPTION_MANIFEST_DRIFT" in _rules(res, code, q) and _rs5_back(res, code, q)
    (dst / f"{code}_amended.pdf").write_bytes(b"%PDF-1.4 new edition")
    res = _run(live, root=tmp_path, reg1={}, reg5=only)
    assert "RS_EXEMPTION_RAW_CHANGED" in _rules(res, code, q)


# ---------------------------------------------------------------------------
# 3. 마스터 쪽 — RS1 셀·잔차, RS5 버킷 생김(INERT)
# ---------------------------------------------------------------------------
def _rows_edit(rows, code, q, ph, meas, col, val):
    out = copy.deepcopy(rows)
    hit = [r for r in out if (r["원보험사코드"], r["공시분기"], r["경과조치여부"], r["measure구분"]) == (code, q, ph, meas)]
    assert len(hit) == 1
    hit[0][col] = val
    return out


@pytest.mark.parametrize("ph", ["적용전", "적용후"])
@pytest.mark.parametrize("meas,val,rules", [
    ("지급여력금액", 857.0, {"RS_EXEMPTION_CELL_DRIFT", "RS_EXEMPTION_RESIDUAL_DRIFT"}),
    ("지급여력기준금액", 271.0, {"RS_EXEMPTION_CELL_DRIFT", "RS_EXEMPTION_RESIDUAL_DRIFT"}),
    ("지급여력비율", 320.5, {"RS_EXEMPTION_CELL_DRIFT", "RS_EXEMPTION_RESIDUAL_DRIFT"}),
    ("지급여력비율", 317.04, {"RS_EXEMPTION_CELL_DRIFT", "RS_EXEMPTION_INERT"}),   # 닫히면 「등재를 풀어라」
    ("지급여력금액", None, {"RS_EXEMPTION_CELL_MISSING"}),
])
def test_rs1_cell_mutation(live, ph, meas, val, rules):
    rows = _rows_edit(live[0], "KR1103", "2026.2Q", ph, meas, "+100bp", val)
    res = _run(live, rows=rows)
    got = _rules(res, "KR1103", "2026.2Q")
    assert rules <= got, got
    assert res["rs1_pinned"] == [] and res["gate_red"] > 0


def test_rs1_residual_pin_drift(live):
    reg = copy.deepcopy(RS._RS1_ISSUER_INCONSISTENT)
    reg[("KR1103", "2026.2Q")]["findings"]["RS1|적용전|+100bp"] = 2.76
    res = _run(live, reg1=reg)
    got = _rules(res, "KR1103", "2026.2Q")
    assert {"RS_EXEMPTION_RESIDUAL_DRIFT", "RS_EXEMPTION_LEDGER_DISAGREE"} <= got, got
    _assert_back(res, "_RS1_ISSUER_INCONSISTENT", "KR1103", "2026.2Q")


@pytest.mark.parametrize("key", ["RS2|적용전|+100bp", "RS1|적용 전|+100bp", "RS1|적용전|+150bp"])
def test_rs1_malformed_key(live, key):
    reg = copy.deepcopy(RS._RS1_ISSUER_INCONSISTENT)
    reg[("KR1103", "2026.2Q")]["findings"][key] = 1.0
    res = _run(live, reg1=reg)
    assert "RS_EXEMPTION_MALFORMED" in _rules(res, "KR1103", "2026.2Q")
    _assert_back(res, "_RS1_ISSUER_INCONSISTENT", "KR1103", "2026.2Q")


def test_rs1_cells_must_cover_inputs(live):
    reg = copy.deepcopy(RS._RS1_ISSUER_INCONSISTENT)
    del reg[("KR1103", "2026.2Q")]["cells"]["적용후|지급여력기준금액|+100bp"]
    res = _run(live, reg1=reg)
    assert "RS_EXEMPTION_MALFORMED" in _rules(res, "KR1103", "2026.2Q")
    assert ("적용후", "+100bp") in _rs1_back(res)


@pytest.mark.parametrize("code,q", sorted(APPROVED_RS5))
def test_rs5_bucket_appears_is_inert_red(live, code, q):
    """금리민감도 행이 생기면 RS5 가 더는 발화하지 않는다 → 「등재를 풀어라」 RED."""
    rows = copy.deepcopy(live[0])
    donor = [r for r in rows if (r["원보험사코드"], r["공시분기"]) == ("KR1103", "2026.2Q")]
    assert len(donor) == 6
    for r in donor:
        g = dict(r)
        g["원보험사코드"], g["원수사명"], g["공시분기"] = code, "마이브라운반려동물전문보험", q
        rows.append(g)
    res = _run(live, rows=rows)
    assert "RS_EXEMPTION_INERT" in _rules(res, code, q)
    assert res["gate_red"] > 0


# ---------------------------------------------------------------------------
# 4. 두 번째 겹 — K-ICS·데이터계약 게이트의 원장 검사
# ---------------------------------------------------------------------------
def test_registered_in_kics_gate_registries_and_pin_map():
    regs = gate._exemption_registries()
    assert regs["_RS1_ISSUER_INCONSISTENT"] == frozenset(APPROVED_RS1)
    assert regs["_RS5_SOURCE_ABSENT"] == frozenset(APPROVED_RS5)
    pins = gate._code_pin_map()
    assert set(pins[("_RS1_ISSUER_INCONSISTENT", "KR1103", "2026.2Q")]["expected_residual"]) \
        == APPROVED_RS1[("KR1103", "2026.2Q")]


@pytest.mark.parametrize("reg,code,q", _ALL)
def test_kics_gate_provenance_blocks_missing_ledger(live, reg, code, q):
    red, _review = gate._exemption_provenance_findings(ledger=_ledger_without(live[2], reg, code, q))
    assert any(r["rule"] == "EXEMPTION_PROVENANCE_MISSING" and (r["registry"], r["code"], r["quarter"])
               == (reg, code, q) for r in red)


def test_kics_gate_live_provenance_clean_for_rate_sens(live):
    red, _review = gate._exemption_provenance_findings(ledger=live[2])
    assert not [r for r in red if r["registry"] in RS.RS_EXEMPTION_REGISTRIES], red
    assert not [r for r in gate._pin_ledger_agreement_findings(ledger=live[2])
                if r["registry"] in RS.RS_EXEMPTION_REGISTRIES]


def test_kics_gate_pin_ledger_disagreement(live):
    def bump(e):
        e["expected_residual"]["RS1|적용전|+100bp"] = 3.5
    led = _ledger_edit(live[2], "_RS1_ISSUER_INCONSISTENT", "KR1103", "2026.2Q", bump)
    red = gate._pin_ledger_agreement_findings(ledger=led)
    assert any(r["rule"] == "EXEMPTION_PIN_LEDGER_DISAGREE" and r["registry"] == "_RS1_ISSUER_INCONSISTENT"
               for r in red)


def test_data_contract_gate_uses_the_same_registry_functions():
    src = (ROOT / "scripts" / "validate_data_contract.py").read_text(encoding="utf-8")
    assert "_exemption_registries" in src and "_pin_ledger_agreement_findings" in src
    assert "_exemption_provenance_findings(\n        env.exemption_registries" in src.replace("\r\n", "\n")


def test_rate_sens_gate_counts_device_red():
    src = (ROOT / "scripts" / "validate_kics_rate_sensitivity.py").read_text(encoding="utf-8")
    assert "red_total = len(rs1) + len(rs2) + len(rs5) + len(rs6) + len(pin_red)" in src
