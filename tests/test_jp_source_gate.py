# -*- coding: utf-8 -*-
"""jp 레인 출처 게이트(`JP_SOURCE_*`)의 회귀 케이스.

왜 이 파일이 있나
-----------------
2026-09-12 census 로 /jp/ 랭킹 15사가 올라갈 때 `build_jesr_page_json.py` 의 self-check 는
**전부 통과**했는데, 다음 날 원문을 열어 보니 3사의 값·출처가 틀려 있었다(東京海上HD 238→268 ·
かんぽ 220→181 · MS&AD 출처가 ESR 한 줄 없는 합병 보도자료). 종전 self-check 가 범위·형식·합계만
보는 자기참조라 "출처가 살아 있나 / 점검을 돌리긴 했나" 축이 없었기 때문이다.
근거: docs/postmortems/PM-2026-09-13_jp_secondary_source_and_dead_url.md (UH-18)

케이스 없는 룰은 다음 리팩터에서 조용히 죽는다. 그래서 양방향을 다 박는다 —
**위반이 실제로 RED 를 내는 것**과 **정상 데이터가 통과하는 것**. 특히 후자는 이 도메인에서
값이 크다: 2026-09-13 전수 실측에서 blocked 20 · ok_requires_headers 16 · tls_client_issue 4 가
나왔고, 이걸 dead 와 섞으면 멀쩡한 회사 40건이 한꺼번에 거짓 RED 가 된다.

그리고 이 저장소가 반복해서 데인 것: **"배선했다" 와 "실제로 exit code 를 바꾼다" 는 다른 말이다.**
`test_gate_*_changes_exit_code_*` 두 개가 진짜 빌더를 서브프로세스로 돌려 그걸 직접 잰다.
전부 tmp 사본에서만 변이시키고 원본 파일은 건드리지 않는다(변이시험 잔해 사고 3회 선례).
"""
from __future__ import annotations

import importlib.util
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
JESR = REPO / "J-ESR"
BUILDER = JESR / "build_jesr_page_json.py"

_RULE_ID = re.compile(r"^\[([A-Z_]+)\]")

pytestmark = pytest.mark.skipif(not BUILDER.exists(), reason="jp 레인이 없는 slim 트리")


@pytest.fixture(scope="module")
def mod():
    sys.path.insert(0, str(JESR))
    spec = importlib.util.spec_from_file_location("jesr_page_builder_under_test", BUILDER)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _ids(errors: list[str]) -> list[str]:
    return sorted({m.group(1) for e in errors if (m := _RULE_ID.match(e))})


OK_URL = "https://www.example-life.co.jp/ir/2026/esr.pdf"


def _scenario(tmp_path, *, url=OK_URL, company="テスト生命", census_checked="2026-09-13",
              health_checked="2026-09-13T14:30Z", scope="all", classification="ok",
              in_health=True, health_present=True, exceptions=None, exceptions_present=True):
    """게이트 입력 한 벌을 tmp 에 만든다. 기본값은 '전부 정상' 이다."""
    records = [{"company_jp": company, "source_url": url}]
    census = [{"company_jp": company, "fy2025_esr_status": "posted",
               "source_url": url, "checked_at": census_checked}]
    health_path = tmp_path / "source_url_health.json"
    if health_present:
        rows = []
        if in_health:
            rows.append({"origin": "fy2025_esr_census.csv", "company": company,
                         "field": "source_url", "url": url,
                         "classification": classification, "expiring_host": False})
        health_path.write_text(
            json.dumps({"checked_at": health_checked, "scope": scope, "rows": rows},
                       ensure_ascii=False), encoding="utf-8")
    exc_path = tmp_path / "jp_source_exceptions.json"
    if exceptions_present:
        exc_path.write_text(json.dumps({"exceptions": exceptions or []}, ensure_ascii=False),
                            encoding="utf-8")
    return records, census, health_path, exc_path


def _run(mod, tmp_path, *, today="2026-09-13", **kw):
    records, census, health_path, exc_path = _scenario(tmp_path, **kw)
    return mod.source_gate_check(records, census, health_path=health_path,
                                 exceptions_path=exc_path, today=today, verbose=False)


# --------------------------------------------------------------------------
# 정상 데이터는 통과한다
# --------------------------------------------------------------------------

def test_clean_scenario_passes(mod, tmp_path):
    assert _run(mod, tmp_path) == []


def test_live_repo_data_passes(mod, tmp_path):
    """실제 census + 실제 증거 파일 + 실제 레지스트리로 RED 0.

    합성 케이스만 있으면 룰이 진짜 데이터에서 어떻게 구는지 모른다. 이 케이스가 깨지면
    둘 중 하나다 — 출처가 실제로 썩었거나(그러면 고쳐야 한다), 점검을 안 돌리고 census 를
    고쳤거나(그러면 돌려야 한다). 어느 쪽이든 통과시킬 이유가 없다.
    """
    import csv
    census = list(csv.DictReader(
        (JESR / "fy2025_esr_census_20260912.csv").open(encoding="utf-8-sig", newline="")))
    posted = [r for r in census if (r.get("fy2025_esr_status") or "").strip() == "posted"]
    records = [{"company_jp": r["company_jp"], "source_url": r.get("source_url")} for r in posted]
    assert posted, "census 에 posted 행이 없다 — 픽스처 전제가 깨졌다"
    errors = mod.source_gate_check(records, census, verbose=False)
    assert errors == [], "라이브 jp 출처 게이트 RED:\n  " + "\n  ".join(errors)


@pytest.mark.parametrize("classification", ["ok", "ok_requires_headers", "blocked",
                                            "tls_client_issue", "spa_shell", "error"])
def test_non_dead_classifications_are_not_red(mod, tmp_path, classification):
    """dead 말고는 아무것도 RED 가 아니다 — 오탐 억제의 핵심.

    2026-09-13 전수 실측: blocked 20 · ok_requires_headers 16 · tls_client_issue 4.
    'ok 가 아니면 RED' 로 짜면 그 40건이 전부 거짓 RED 다. 화면 15사만 봐도
    ok_requires_headers 2(MS&AD·ソニーFG) · tls_client_issue 1(ソニー生命) 이 걸린다.
    """
    assert _run(mod, tmp_path, classification=classification) == []


# --------------------------------------------------------------------------
# 위반은 RED 를 낸다
# --------------------------------------------------------------------------

def test_every_expiring_host_fires(mod, tmp_path):
    """`jesr_http.EXPIRING_HOSTS` 의 **모든** 호스트가 발화한다.

    이 게이트는 그 튜플을 import 해서 쓴다(재타이핑 금지). 이 케이스는 그 계약을 강제한다 —
    목록에 호스트를 추가했는데 빌더가 안 보는 상황이 생기면 여기서 깨진다.
    """
    import jesr_http
    assert jesr_http.EXPIRING_HOSTS, "EXPIRING_HOSTS 가 비었다 — 룰이 통째로 no-op 이다"
    for host in jesr_http.EXPIRING_HOSTS:
        url = f"https://{host}/inbs/140120260520500000.pdf"
        errors = _run(mod, tmp_path, url=url)
        assert "JP_SOURCE_EXPIRING_HOST" in _ids(errors), f"{host} 가 발화하지 않았다: {errors}"


def test_expiring_host_matches_netloc_case_insensitively(mod, tmp_path):
    errors = _run(mod, tmp_path, url="https://RELEASE.TDnet.INFO/inbs/x.pdf")
    assert "JP_SOURCE_EXPIRING_HOST" in _ids(errors)


def test_lookalike_host_is_not_flagged(mod, tmp_path):
    """`release.tdnet.info.example.com` 처럼 닮은 호스트를 잡으면 오탐이다(정확일치)."""
    assert _run(mod, tmp_path, url="https://release.tdnet.info.example.com/x.pdf") == []


def test_dead_classification_is_red(mod, tmp_path):
    assert "JP_SOURCE_URL_DEAD" in _ids(_run(mod, tmp_path, classification="dead"))


def test_stale_evidence_is_red(mod, tmp_path):
    """증거가 census 보다 하루라도 낡으면 RED — '점검을 안 돌리고 census 를 고쳤다'."""
    errors = _run(mod, tmp_path, census_checked="2026-09-14", health_checked="2026-09-13T14:30Z")
    assert "JP_SOURCE_EVIDENCE_STALE" in _ids(errors)


def test_evidence_newer_than_census_passes(mod, tmp_path):
    assert _run(mod, tmp_path, census_checked="2026-09-12",
                health_checked="2026-09-13T14:30Z") == []


def test_missing_evidence_file_is_red(mod, tmp_path):
    errors = _run(mod, tmp_path, health_present=False)
    assert "JP_SOURCE_EVIDENCE_STALE" in _ids(errors)


@pytest.mark.parametrize("scope", ["page", "census", "insurers", "", None])
def test_narrow_scope_is_red(mod, tmp_path, scope):
    """좁은 범위 산출로 통과시키면 검사한 척만 하는 것이다."""
    errors = _run(mod, tmp_path, scope=scope)
    assert "JP_SOURCE_EVIDENCE_STALE" in _ids(errors)


def test_uncovered_source_url_is_red(mod, tmp_path):
    """census 의 source_url 이 증거 파일에 아예 없으면 RED.

    checked_at 이 날짜 단위라 '같은 날 census 만 고친' 경우는 신선도 검사로는 안 잡힌다.
    그 구멍을 이 커버리지 검사가 막는다 — 새 URL 은 점검된 적이 없으므로 반드시 걸린다.
    """
    errors = _run(mod, tmp_path, in_health=False)
    assert "JP_SOURCE_EVIDENCE_INCOMPLETE" in _ids(errors)


def test_posted_row_without_checked_at_is_red(mod, tmp_path):
    """checked_at 을 비우면 최댓값이 내려가 낡은 증거가 통과한다 — 결측이 우회수단이 된다."""
    errors = _run(mod, tmp_path, census_checked="")
    assert "JP_SOURCE_EVIDENCE_STALE" in _ids(errors)


def test_unparseable_checked_at_is_red(mod, tmp_path):
    errors = _run(mod, tmp_path, census_checked="2026/09/13")
    assert "JP_SOURCE_EVIDENCE_STALE" in _ids(errors)


# --------------------------------------------------------------------------
# 예외 레지스트리 (등재는 owner 권한)
# --------------------------------------------------------------------------

def _exc(rule="JP_SOURCE_EXPIRING_HOST", company="テスト生命", field="source_url",
         reason="owner 판단: 대체 영구 경로가 아직 없다", approved="2026-09-13", expires=None):
    return {"rule": rule, "company_jp": company, "field": field, "reason": reason,
            "owner_approved_on": approved, "expires_on": expires}


TDNET_URL = "https://release.tdnet.info/inbs/140120260520500000.pdf"


def test_owner_exception_suppresses_the_red(mod, tmp_path):
    assert _run(mod, tmp_path, url=TDNET_URL, exceptions=[_exc()]) == []


def test_exception_is_cell_scoped_not_blanket(mod, tmp_path):
    """다른 회사에 붙은 면제는 이 회사를 통과시키지 않는다."""
    errors = _run(mod, tmp_path, url=TDNET_URL, exceptions=[_exc(company="よその生命")])
    assert "JP_SOURCE_EXPIRING_HOST" in _ids(errors)


def test_exception_for_another_rule_does_not_cross_apply(mod, tmp_path):
    errors = _run(mod, tmp_path, url=TDNET_URL, exceptions=[_exc(rule="JP_SOURCE_URL_DEAD")])
    assert "JP_SOURCE_EXPIRING_HOST" in _ids(errors)


@pytest.mark.parametrize("key", ["rule", "company_jp", "field", "reason", "owner_approved_on"])
def test_exception_missing_required_key_is_red(mod, tmp_path, key):
    """사유·owner 승인일 없는 익명 면제는 등재 자체가 RED 다."""
    entry = _exc()
    entry[key] = ""
    errors = _run(mod, tmp_path, url=TDNET_URL, exceptions=[entry])
    assert "JP_SOURCE_EXCEPTIONS" in _ids(errors)
    assert "JP_SOURCE_EXPIRING_HOST" in _ids(errors), "면제가 죽었으면 원 위반이 다시 나와야 한다"


def test_exception_on_non_exemptable_rule_is_red(mod, tmp_path):
    """절차 룰(증거 신선도)을 면제하려 들면 그 시도 자체가 RED 다."""
    errors = _run(mod, tmp_path, exceptions=[_exc(rule="JP_SOURCE_EVIDENCE_STALE")])
    assert "JP_SOURCE_EXCEPTIONS" in _ids(errors)


def test_unknown_rule_id_is_red(mod, tmp_path):
    """오타난 rule id 는 아무것도 면제 못 하면서 면제해 뒀다는 착각만 남긴다."""
    errors = _run(mod, tmp_path, exceptions=[_exc(rule="JP_SOURCE_EXPIRING_HOSTS")])
    assert "JP_SOURCE_EXCEPTIONS" in _ids(errors)


def test_expired_exception_stops_suppressing(mod, tmp_path):
    errors = _run(mod, tmp_path, url=TDNET_URL, today="2026-12-01",
                  exceptions=[_exc(expires="2026-10-31")])
    assert "JP_SOURCE_EXPIRING_HOST" in _ids(errors)


def test_unexpired_exception_still_suppresses(mod, tmp_path):
    assert _run(mod, tmp_path, url=TDNET_URL, today="2026-10-01",
                exceptions=[_exc(expires="2026-10-31")]) == []


def test_corrupt_registry_is_red_not_silently_empty(mod, tmp_path):
    records, census, health_path, exc_path = _scenario(tmp_path)
    exc_path.write_text("{ this is not json", encoding="utf-8")
    errors = mod.source_gate_check(records, census, health_path=health_path,
                                   exceptions_path=exc_path, verbose=False)
    assert "JP_SOURCE_EXCEPTIONS" in _ids(errors)


def test_missing_registry_is_not_red(mod, tmp_path):
    """면제 0건은 게이트가 더 엄해지는 방향이라 막지 않는다."""
    assert _run(mod, tmp_path, exceptions_present=False) == []


def test_shipped_registry_is_loadable_and_empty(mod):
    keys, errors, _ = mod.load_source_exceptions()
    assert errors == [], f"저장소에 실린 예외 레지스트리가 스키마 위반이다: {errors}"
    assert keys == set(), f"예외가 0건이 아니다 — owner 승인 기록을 확인해라: {sorted(keys)}"


def test_registry_readme_names_exactly_the_code_rule_ids(mod):
    """레지스트리 _README 의 룰 id 목록 ↔ 코드의 SOURCE_RULE_IDS 가 어긋나면 안 된다.

    문서와 코드가 같은 사실을 두 벌 들고 있으면 한쪽이 조용히 낡는다 —
    이 저장소가 골든 테스트 표에서 이미 배운 것(test_deploy_assets.py).
    """
    data = json.loads((JESR / "jp_source_exceptions.json").read_text(encoding="utf-8"))
    readme = "\n".join(data["_README"])
    named = set(re.findall(r"JP_SOURCE_[A-Z_]+", readme)) - {"JP_SOURCE_EXCEPTIONS"}
    assert named == set(mod.SOURCE_RULE_IDS), (
        f"_README 가 말하는 룰 {sorted(named)} != 코드의 {sorted(mod.SOURCE_RULE_IDS)}")
    for rule in mod.EXEMPTABLE_RULE_IDS:
        assert rule in mod.SOURCE_RULE_IDS


# --------------------------------------------------------------------------
# "배선했다" 가 아니라 "실제로 exit code 를 바꾼다" 를 잰다
# --------------------------------------------------------------------------

_COPY = ["build_jesr_page_json.py", "jesr_http.py", "fy2025_esr_census_20260912.csv",
         "jesr_sources_2026Q1.csv", "jp_insurers.csv", "source_url_health.json",
         "jp_source_exceptions.json", "esr_target_ranges.json"]


def _sandbox(tmp_path) -> Path:
    """저장소 사본. 변이는 여기서만 한다 — 원본은 절대 건드리지 않는다."""
    jesr = tmp_path / "J-ESR"
    jesr.mkdir()
    for name in _COPY:
        src = JESR / name
        if src.exists():
            shutil.copy2(src, jesr / name)
    (tmp_path / "jp").mkdir()
    return jesr / "build_jesr_page_json.py"


def _run_builder(script: Path):
    return subprocess.run([sys.executable, str(script)], capture_output=True, text=True)


def test_sandbox_copy_builds_green(tmp_path):
    """변이 전 사본은 exit 0 — 뒤의 exit 1 이 사본 탓이 아님을 보증하는 음성대조군."""
    proc = _run_builder(_sandbox(tmp_path))
    assert proc.returncode == 0, f"사본이 이미 RED 다:\n{proc.stdout}\n{proc.stderr}"


def test_gate_expiring_host_changes_exit_code(tmp_path):
    script = _sandbox(tmp_path)
    jesr = script.parent
    census = jesr / "fy2025_esr_census_20260912.csv"
    text = census.read_text(encoding="utf-8-sig")
    health = json.loads((jesr / "source_url_health.json").read_text(encoding="utf-8"))
    victim = next(r for r in health["rows"] if r["field"] == "source_url"
                  and r["url"] in text)
    # 증거 파일에도 같이 넣어 커버리지 룰이 아니라 **만료호스트 룰만** 발화하게 한다.
    census.write_text(text.replace(victim["url"], TDNET_URL), encoding="utf-8")
    health["rows"].append({**victim, "url": TDNET_URL, "classification": "ok"})
    (jesr / "source_url_health.json").write_text(
        json.dumps(health, ensure_ascii=False), encoding="utf-8")

    proc = _run_builder(script)
    assert proc.returncode == 1, f"만료호스트인데 exit {proc.returncode}:\n{proc.stdout}"
    assert "JP_SOURCE_EXPIRING_HOST" in proc.stderr
    assert "release.tdnet.info" in proc.stderr


def test_gate_stale_evidence_changes_exit_code(tmp_path):
    script = _sandbox(tmp_path)
    jesr = script.parent
    health_path = jesr / "source_url_health.json"
    health = json.loads(health_path.read_text(encoding="utf-8"))
    health["checked_at"] = "2020-01-01T00:00Z"  # 점검을 안 돌리고 census 를 고친 상태
    health_path.write_text(json.dumps(health, ensure_ascii=False), encoding="utf-8")

    proc = _run_builder(script)
    assert proc.returncode == 1, f"증거가 낡았는데 exit {proc.returncode}:\n{proc.stdout}"
    assert "JP_SOURCE_EVIDENCE_STALE" in proc.stderr


def test_gate_missing_evidence_changes_exit_code(tmp_path):
    script = _sandbox(tmp_path)
    (script.parent / "source_url_health.json").unlink()
    proc = _run_builder(script)
    assert proc.returncode == 1, f"증거가 없는데 exit {proc.returncode}:\n{proc.stdout}"
    assert "JP_SOURCE_EVIDENCE_STALE" in proc.stderr
