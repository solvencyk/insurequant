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

2026-09-13 에 축이 하나 더 붙었다(UH-21): `JP_ESR_ADJUSTED_FIGURE` — **"그 문서에 그 숫자가
있나" 가 아니라 "그 숫자가 그 문서에서 우리가 싣겠다고 한 정의의 값인가"**. 사고 3건 중
かんぽ 220% 는 앞의 축으로 원리상 안 걸린다(220 은 p35 에 실재하는 조정치라 `found` 다).

그리고 이 저장소가 반복해서 데인 것: **"배선했다" 와 "실제로 exit code 를 바꾼다" 는 다른 말이다.**
`test_gate_*` 의 사본 실행 케이스들이 진짜 빌더를 서브프로세스로 돌려 그걸 직접 잰다.
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


def _collector():
    """증거 수집기(`check_esr_in_source.py`)를 import 한다.

    조정치 판정식의 **정본은 수집기**다(게이트는 박제된 verdict 만 읽는다). 그래서 판정식
    자체의 회귀는 여기서 잰다. `fitz` 는 `scan_pdf` 안에서만 import 하므로 이 테스트가
    검사하는 `scan_adjusted` 는 **순수 텍스트 함수**라 PDF 도 네트워크도 필요 없다.
    """
    path = JESR / "check_esr_in_source.py"
    if not path.exists():
        pytest.skip("수집기가 없는 slim 트리")
    sys.path.insert(0, str(JESR))
    spec = importlib.util.spec_from_file_location("jesr_esr_collector_under_test", path)
    m = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(m)
    except ImportError as exc:            # requests 없는 환경
        pytest.skip(f"수집기 의존성 없음: {exc}")
    return m


def _ids(errors: list[str]) -> list[str]:
    return sorted({m.group(1) for e in errors if (m := _RULE_ID.match(e))})


OK_URL = "https://www.example-life.co.jp/ir/2026/esr.pdf"


def _scenario(tmp_path, *, url=OK_URL, company="テスト生命", census_checked="2026-09-13",
              health_checked="2026-09-13T14:30Z", scope="all", classification="ok",
              in_health=True, health_present=True, exceptions=None, exceptions_present=True,
              esr_pct=268.0, esr_checked="2026-09-13T16:10Z", esr_scope="all",
              esr_verdict="found", esr_row_pct=None, in_esr=True, esr_present=True,
              adjusted="unqualified", adjusted_alts=None, drop_adjusted=False):
    """게이트 입력 한 벌을 tmp 에 만든다. 기본값은 '전부 정상' 이다.

    증거 파일이 **둘**이다(출처 생존 · 값이 문서 안에 있나). 둘 다 같은 봉투를 쓰고 같은
    신선도 검사를 받는다 — 한쪽만 채운 시나리오는 나머지 한쪽 때문에 RED 가 나는 것이 정상.
    """
    records = [{"company_jp": company, "source_url": url, "esr_pct": esr_pct}]
    census = [{"company_jp": company, "fy2025_esr_status": "posted", "esr_pct": esr_pct,
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
    esr_path = tmp_path / "esr_in_source_health.json"
    if esr_present:
        rows = []
        if in_esr:
            row = {"origin": "fy2025_esr_census.csv", "company": company,
                   "field": "source_url", "url": url,
                   "esr_pct": ("%g" % float(esr_pct)) if esr_row_pct is None else esr_row_pct,
                   "verdict": esr_verdict, "page": 5, "distance": 3, "label": "ESR",
                   "pages": 40, "evidence": "…ESR は 268% …"}
            if not drop_adjusted:
                # 조정치 축(UH-21). `drop_adjusted` 는 **옛 수집기가 만든 증거**를 흉내 내는
                # 변이다 — 필드 부재를 통과로 읽으면 이 축이 조용히 사라진다.
                row.update({"adjusted_verdict": adjusted, "adjusted_qualifiers":
                            ["除いた場合"] if adjusted in ("adjusted_alt", "adjusted_only") else [],
                            "adjusted_frags": 3 if adjusted != "abstain_no_prose" else 0,
                            "adjusted_frags_unqualified": 0,
                            "adjusted_alternatives": (adjusted_alts if adjusted_alts is not None
                                                      else ([{"pct": "181", "page": 35,
                                                              "evidence": "ESRは181%"}]
                                                            if adjusted == "adjusted_alt" else [])),
                            "adjusted_evidence": "p35 한정어 ['除いた場合']: …を除いた場合のESRは220%"})
            rows.append(row)
        esr_path.write_text(
            json.dumps({"checked_at": esr_checked, "scope": esr_scope, "rows": rows},
                       ensure_ascii=False), encoding="utf-8")
    exc_path = tmp_path / "jp_source_exceptions.json"
    if exceptions_present:
        exc_path.write_text(json.dumps({"exceptions": exceptions or []}, ensure_ascii=False),
                            encoding="utf-8")
    return records, census, health_path, esr_path, exc_path


def _run(mod, tmp_path, *, today="2026-09-13", **kw):
    records, census, health_path, esr_path, exc_path = _scenario(tmp_path, **kw)
    return mod.source_gate_check(records, census, health_path=health_path,
                                 esr_health_path=esr_path,
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
    records = [{"company_jp": r["company_jp"], "source_url": r.get("source_url"),
                "esr_pct": float(r["esr_pct"])} for r in posted]
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
# JP_ESR_NOT_IN_SOURCE — "그 문서에 그 숫자가 있나" (2026-09-13 배선, PM §4c-pre-실측)
#
# 이 축이 없어서 2026-09-12 에 東京海上HD 238%(어느 1차 문서에도 없는 2차보도 인용값)와
# MS&AD 의 무관한 출처(ESR 한 줄 없는 합병 보도자료)가 통과했다. 둘 다 URL 은 살아 있었고
# 만료 호스트도 아니었으므로 먼저 배선된 4종으로는 못 잡는다(실측: 사고 당시 MS&AD URL 을
# 지금 probe 하면 ok_requires_headers = 살아 있음).
# --------------------------------------------------------------------------

def test_value_not_in_source_is_red(mod, tmp_path):
    errors = _run(mod, tmp_path, esr_verdict="not_found")
    assert "JP_ESR_NOT_IN_SOURCE" in _ids(errors)


@pytest.mark.parametrize("verdict", ["skip_landing", "skip_no_text"])
def test_skip_verdicts_are_yellow_not_red(mod, tmp_path, verdict):
    """실측 근거: 랜딩 페이지 정본 1사(T&D) · 이미지형 PDF 0사.

    §2 초안은 "같은 문장" 이었고 그대로 걸면 표 행·차트 데이터라벨로만 공존하는 7사가
    거짓 RED 였다. skip 두 종은 차단하지 않고 YELLOW 로 보고한다.
    """
    assert _run(mod, tmp_path, esr_verdict=verdict) == []


def test_unknown_verdict_is_red_not_silently_skipped(mod, tmp_path):
    """모르는 verdict 를 SKIP 으로 넘기면 그 행은 **아무 검사도 안 받는다**.

    이 저장소가 반복해서 데인 모양이 정확히 그것이다 — 룰이 그 항목을 순회조차 안 하면
    게이트는 0 을 찍는데 축은 깨끗하지 않다.
    """
    assert "JP_ESR_NOT_IN_SOURCE" in _ids(_run(mod, tmp_path, esr_verdict="probably_fine"))


def test_fetch_failed_is_incomplete_not_a_pass(mod, tmp_path):
    """문서를 못 받은 것은 '없다' 도 '있다' 도 아니다 — 판정 없는 행은 통과시키지 않는다."""
    assert "JP_SOURCE_EVIDENCE_INCOMPLETE" in _ids(_run(mod, tmp_path, esr_verdict="fetch_failed"))


def test_value_changed_without_recollecting_is_red(mod, tmp_path):
    """**사고 재현의 핵심**: census 값만 고치고 수집기를 다시 안 돌린 상태.

    증거 행의 키가 url 뿐이면 옛 값의 `found` 를 새 값이 그대로 물려받아 통과한다.
    키가 (url, esr_pct) 라서 RED 가 난다 — 실측으로 東京海上HD 268→238 · かんぽ 181→220
    두 행 모두 여기서 걸렸다(2026-09-13 사본 재현 A).
    """
    errors = _run(mod, tmp_path, esr_pct=238.0, esr_row_pct="268")
    assert "JP_SOURCE_EVIDENCE_INCOMPLETE" in _ids(errors)
    assert "238" in errors[0] and "268" in errors[0]


def test_pct_notation_differences_are_not_red(mod, tmp_path):
    """`268` / `268.0` / `"268%"` 는 같은 값이다 — 표기 차이로 거짓 RED 를 내면 안 된다."""
    assert _run(mod, tmp_path, esr_pct=268.0, esr_row_pct="268.0") == []
    assert _run(mod, tmp_path, esr_pct=268.0, esr_row_pct="268%") == []
    assert _run(mod, tmp_path, esr_pct=208.7, esr_row_pct="208.70") == []


def test_uncovered_row_in_esr_evidence_is_red(mod, tmp_path):
    assert "JP_SOURCE_EVIDENCE_INCOMPLETE" in _ids(_run(mod, tmp_path, in_esr=False))


def test_missing_esr_evidence_file_is_red(mod, tmp_path):
    """증거가 낡거나 없으면 이 룰도 같이 낡는다 — 둘은 한 쌍이다."""
    assert "JP_SOURCE_EVIDENCE_STALE" in _ids(_run(mod, tmp_path, esr_present=False))


@pytest.mark.parametrize("esr_scope", ["partial", "page", "", None])
def test_narrow_esr_scope_is_red(mod, tmp_path, esr_scope):
    assert "JP_SOURCE_EVIDENCE_STALE" in _ids(_run(mod, tmp_path, esr_scope=esr_scope))


def test_stale_esr_evidence_is_red(mod, tmp_path):
    errors = _run(mod, tmp_path, census_checked="2026-09-14",
                  health_checked="2026-09-15T00:00Z", esr_checked="2026-09-13T16:10Z")
    assert "JP_SOURCE_EVIDENCE_STALE" in _ids(errors)
    assert any("esr_in_source_health.json" in e for e in errors)


def test_esr_exception_is_cell_scoped(mod, tmp_path):
    """owner 면제는 (rule, company, field) 셀 단위 — 한 줄이 축 전체를 눈감기지 못한다."""
    ok = _exc(rule="JP_ESR_NOT_IN_SOURCE", company="テスト生命")
    assert _run(mod, tmp_path, esr_verdict="not_found", exceptions=[ok]) == []
    other = _exc(rule="JP_ESR_NOT_IN_SOURCE", company="よその生命")
    assert "JP_ESR_NOT_IN_SOURCE" in _ids(
        _run(mod, tmp_path, esr_verdict="not_found", exceptions=[other]))


def test_esr_exception_does_not_cover_the_procedural_rules(mod, tmp_path):
    """면제는 '값이 문서에 없다' 만 덮는다. '점검을 안 돌렸다' 는 못 덮는다."""
    exc = _exc(rule="JP_ESR_NOT_IN_SOURCE", company="テスト生命")
    assert "JP_SOURCE_EVIDENCE_INCOMPLETE" in _ids(
        _run(mod, tmp_path, in_esr=False, exceptions=[exc]))


def test_live_esr_evidence_covers_every_posted_row(mod):
    """실데이터 — 실제 census 의 posted 전량이 실제 증거 파일에 (url, 값) 으로 들어 있나.

    합성 케이스만 있으면 룰이 진짜 데이터에서 어떻게 구는지 모른다. 이게 깨지면 값이나
    출처를 고치고 수집기를 다시 안 돌린 것이다.
    """
    import csv
    census = list(csv.DictReader(
        (JESR / "fy2025_esr_census_20260912.csv").open(encoding="utf-8-sig", newline="")))
    posted = [r for r in census if (r.get("fy2025_esr_status") or "").strip() == "posted"]
    ev = json.loads((JESR / "esr_in_source_health.json").read_text(encoding="utf-8"))
    keys = {(r["url"], mod._norm_pct(r.get("esr_pct"))) for r in ev["rows"]}
    missing = [(r["company_jp"], r["esr_pct"]) for r in posted
               if (r["source_url"], mod._norm_pct(r["esr_pct"])) not in keys]
    assert not missing, f"증거에 없는 posted 행: {missing}"


# --------------------------------------------------------------------------
# JP_ESR_ADJUSTED_FIGURE — "그 문서에서 **우리가 싣겠다고 한 정의의** 숫자인가" (UH-21)
#
# 위 축은 "그 문서에 그 숫자가 있나" 만 묻는다. 사고 3건 중 かんぽ 220% 는 그걸로 **원리상**
# 안 걸린다 — 220 은 자료 p35 에 실재하는 「大量解約リスクを除いた場合」 조정치이기 때문이다
# (실측 d=1 → found). 같은 문서에 한정어 없는 진짜 헤드라인 181% 가 나란히 있었다.
#
# 판정식은 두 조건의 곱이다: ① 화면값의 라벨동반 조각이 **전부** 한정어를 달았다
# ② 같은 문서에 **한정어 없는 다른 ESR 값**이 있다. ② 가 본 룰인 이유는 실측이다 —
# definition marker 4종(ベース·内部管理·規制·速報値)을 한정어로 오인해 넣으면 ① 단독은
# 정상 3사(日本生命·住友·朝日)가 거짓 발화하는데 ② 를 붙이면 그 3사가 전부 조용하다.
# --------------------------------------------------------------------------

def _gate_stdout(mod, tmp_path, capsys, **kw):
    """verbose 로 돌려 YELLOW 노트까지 본다. YELLOW 는 errors 가 아니라 stdout 으로 나간다."""
    records, census, health_path, esr_path, exc_path = _scenario(tmp_path, **kw)
    errors = mod.source_gate_check(records, census, health_path=health_path,
                                   esr_health_path=esr_path, exceptions_path=exc_path,
                                   today="2026-09-13", verbose=True)
    return errors, capsys.readouterr().out


def test_adjusted_figure_is_yellow_not_red(mod, tmp_path):
    """severity 는 YELLOW — 조건부 값을 정당하게 헤드라인으로 쓰는 회사가 있을 수 있다.

    RED 로 걸면 그런 회사의 정상 배포가 막히고, 면제는 owner 권한이라 그 자리에서 못 푼다
    (UH-5·UH-9 선례). 대신 배포본 증거에 발화가 남아 있으면 아래 live 테스트가 막는다.
    """
    assert _run(mod, tmp_path, adjusted="adjusted_alt") == []
    assert _run(mod, tmp_path, adjusted="adjusted_only") == []


def test_adjusted_alt_message_names_the_unqualified_alternative(mod, tmp_path, capsys):
    """**사고 재현의 핵심.** 사람이 바로 고칠 수 있는 메시지가 아니면 룰의 절반은 쓸모없다.

    かんぽ 사고의 정답(181%)은 같은 문서 안에 있었다. 그러니 발화는 그 값을 같이 찍어야 한다.
    """
    errors, out = _gate_stdout(mod, tmp_path, capsys, adjusted="adjusted_alt")
    assert errors == []
    assert "JP_ESR_ADJUSTED_FIGURE" in out and "/YELLOW]" in out
    assert "181%(p35)" in out, f"대안값이 메시지에 없다:\n{out}"


def test_adjusted_only_says_there_is_no_alternative(mod, tmp_path, capsys):
    """보조 신호. 대안이 없으면 없다고 적는다 — 있는 척하면 사람이 엉뚱한 값을 찾는다."""
    _, out = _gate_stdout(mod, tmp_path, capsys, adjusted="adjusted_only")
    assert "JP_ESR_ADJUSTED_FIGURE" in out and "대안값은 그 문서에 없다" in out


@pytest.mark.parametrize("verdict", ["unqualified", "abstain_no_prose", "not_applicable"])
def test_clean_and_abstained_adjusted_verdicts_do_not_fire(mod, tmp_path, capsys, verdict):
    """**오탐억제.** 라벨동반 산문 조각이 0개인 표·차트 전용 문서가 15사 중 7사다.

    기권 조건 없이 걸면 그 7사가 한꺼번에 거짓 YELLOW 다(2026-09-13 실측).
    """
    errors, out = _gate_stdout(mod, tmp_path, capsys, adjusted=verdict)
    assert errors == []
    # 요약 줄에는 룰 이름이 늘 나온다(분포를 세는 줄). 발화는 YELLOW 노트로만 센다.
    assert "/YELLOW] JP_ESR_ADJUSTED_FIGURE" not in out


def test_abstained_rows_are_counted_not_silently_skipped(mod, tmp_path, capsys):
    """기권은 SKIP 이 아니라 **따로 세는 분류**다 — 몇 사가 판정 대상이 아니었는지 남아야 한다.

    "룰이 0이라고 말한다" 와 "그 축이 깨끗하다" 는 다른 말이고, 그 차이가 census 로만 보인다.
    """
    _, out = _gate_stdout(mod, tmp_path, capsys, adjusted="abstain_no_prose")
    assert "판정 분포" in out and "abstain_no_prose=1" in out


def test_missing_adjusted_field_is_red_not_a_pass(mod, tmp_path):
    """옛 수집기가 만든 증거(필드 없음)를 통과로 읽으면 이 축이 **조용히 사라진다**.

    이 저장소가 반복해서 데인 모양이 정확히 그것이다 — 룰이 순회조차 안 하면 게이트는 0 을
    찍는데 축은 검사된 적이 없다.
    """
    errors = _run(mod, tmp_path, drop_adjusted=True)
    assert "JP_SOURCE_EVIDENCE_INCOMPLETE" in _ids(errors)
    assert any("adjusted_verdict" in e for e in errors)


def test_unknown_adjusted_verdict_is_red(mod, tmp_path):
    assert "JP_ESR_ADJUSTED_FIGURE" in _ids(_run(mod, tmp_path, adjusted="looks_ok_to_me"))


def test_adjusted_exception_is_cell_scoped(mod, tmp_path, capsys):
    """면제도 (rule, company, field) 셀 단위. 한 줄이 축 전체를 눈감기지 못한다."""
    ok = _exc(rule="JP_ESR_ADJUSTED_FIGURE", company="テスト生命")
    _, out = _gate_stdout(mod, tmp_path, capsys, adjusted="adjusted_alt", exceptions=[ok])
    assert "면제 적용 JP_ESR_ADJUSTED_FIGURE" in out and "/YELLOW]" not in out
    other = _exc(rule="JP_ESR_ADJUSTED_FIGURE", company="よその生命")
    _, out2 = _gate_stdout(mod, tmp_path, capsys, adjusted="adjusted_alt", exceptions=[other])
    assert "/YELLOW]" in out2


def test_adjusted_exception_does_not_cover_the_procedural_rules(mod, tmp_path):
    """면제는 '조정치일 수 있다' 만 덮는다. '축을 안 돌렸다' 는 못 덮는다."""
    exc = _exc(rule="JP_ESR_ADJUSTED_FIGURE", company="テスト生命")
    assert "JP_SOURCE_EVIDENCE_INCOMPLETE" in _ids(
        _run(mod, tmp_path, drop_adjusted=True, exceptions=[exc]))


def test_live_esr_evidence_judges_the_adjusted_axis_on_every_row(mod):
    """실데이터 — 배포본 증거의 **모든 행**이 조정치 축을 실제로 통과했나.

    수집기를 옛 버전으로 돌리면 필드가 통째로 빠지는데, 게이트는 그 행을 보기 전에
    다른 이유로 끝날 수도 있다. 그러니 증거 파일 자체를 직접 센다.
    """
    ev = json.loads((JESR / "esr_in_source_health.json").read_text(encoding="utf-8"))
    known = set(mod.ESR_ADJUSTED_PASS + mod.ESR_ADJUSTED_YELLOW + mod.ESR_ADJUSTED_ABSTAIN)
    bad = [(r.get("company"), r.get("adjusted_verdict", "<필드없음>")) for r in ev["rows"]
           if r.get("adjusted_verdict") not in known]
    assert not bad, f"조정치 판정이 없거나 모르는 값인 행: {bad}"


def test_live_esr_evidence_has_no_unexempted_adjusted_figure(mod):
    """**이 YELLOW 의 이빨.** 인쇄만 하는 YELLOW 는 통제가 아니다.

    2026-09-12 에는 census notes 에 「特定条件を除いた場合の ESR は 220%」 라고 **적혀 있었는데도**
    그 값이 그대로 화면에 올라갔다. 그래서 빌더 severity 는 YELLOW 로 두되(정상 배포를 막지
    않는다), 배포본 증거에 면제 없는 발화가 남아 있으면 **push 묶음이 여기서 막는다**.
    깨졌다면 둘 중 하나다 — 값을 고치거나, owner 가 면제를 등재하거나. 테스트를 고치는 것이
    아니다(`J-ESR/jp_source_exceptions.json`, 등재는 owner 권한).
    """
    ev = json.loads((JESR / "esr_in_source_health.json").read_text(encoding="utf-8"))
    exempt, errors, _notes = mod.load_source_exceptions(today=None)
    assert errors == [], f"면제 레지스트리 자체가 RED 다: {errors}"
    fired = [r for r in ev["rows"] if r.get("adjusted_verdict") in mod.ESR_ADJUSTED_YELLOW
             and ("JP_ESR_ADJUSTED_FIGURE", r.get("company"), "source_url") not in exempt]
    assert not fired, (
        "조정치 후보가 배포본 증거에 남아 있다 — 원문을 열어 헤드라인 값을 확인해라:\n" +
        "\n".join(f"  {r.get('company')} esr={r.get('esr_pct')}"
                  f" 한정어={r.get('adjusted_qualifiers')}"
                  f" 대안={[a.get('pct') for a in (r.get('adjusted_alternatives') or [])]}"
                  for r in fired))


def test_qualifier_list_is_not_empty_and_excludes_definition_markers():
    """한정어 목록을 비우면 이 룰은 **아무것도 안 잡는다**(かんぽ 220 이 unqualified 가 된다).

    반대로 definition marker 를 넣으면 정상사가 거짓 발화한다 — 실측으로
    `ベース`·`内部管理`·`規制`·`速報値` 를 넣으면 日本生命·住友·朝日 3사가 발화했다.
    이 둘은 대칭이라 양쪽을 다 박는다.
    """
    c = _collector()
    assert c.ADJUSTED_QUALIFIERS, "한정어 목록이 비었다 — 룰이 아무것도 안 잡는다"
    assert "除いた場合" in c.ADJUSTED_QUALIFIERS, "사고 그 문장의 한정어가 빠졌다"
    assert "適正水準" in c.ADJUSTED_QUALIFIERS, (
        "適正水準 을 빼면 かんぽ p18 「ESR適正水準 150~220%」 가 한정어 없는 조각이 되어"
        " 220 이 빠져나간다(실측)")
    for marker in ("ベース", "内部管理", "規制", "速報値"):
        assert marker not in c.ADJUSTED_QUALIFIERS, (
            f"{marker} 는 '어느 ESR 이냐' 지 '조정했다' 가 아니다 —"
            " 넣으면 정상사 3사가 거짓 발화한다(2026-09-13 실측)")


def test_adjusted_value_range_is_the_builders_not_a_retyped_literal(mod):
    """값 후보 범위는 빌더가 정본이다. 재타이핑하면 수집기와 게이트가 서로 다른 범위를 쓴다."""
    c = _collector()
    assert (c.ADJ_PCT_MIN, c.ADJ_PCT_MAX) == (mod.ESR_PCT_MIN, mod.ESR_PCT_MAX)


# --- 수집기 판정식 자체(오프라인, 실제 원문 문장으로) -----------------------
# かんぽ 자료(2026-05, p18·p35·p37)에서 그대로 딴 문장이다. 요약하거나 다듬지 않는다 —
# 다듬으면 검증기가 원문이 아닌 것을 검증하게 된다.
_KAMPO_P18 = "・ ESR適正水準 150~220%"
_KAMPO_P35 = (
    "◼26.3末のESRは大量解約リスクの影響により181%1と、25.3末から15ポイント低下したが、"
    "適正水準の範囲内にある\n"
    "26.3末のESRは181%と、大量解約リスクの影響等により25.3末から15ポ\n"
    "なお、大量解約リスクを除いた場合のESRは220%と適正水準の上限水準"
)
_KAMPO_P37 = "◼26.3末のESRは25.3末のESR(新基準)から15ポイント低下し、181%となった"


def test_collector_separates_the_accident_value_from_the_correct_one():
    """**사고 재현.** 같은 문서에서 220 은 발화하고 181 은 발화하지 않아야 한다.

    이게 이 룰의 존재 이유다. 둘 다 그 문서에 실재하므로 JP_ESR_NOT_IN_SOURCE 로는
    둘 다 `found` 이고 구분이 안 된다(실측 d=1).
    """
    c = _collector()
    pages = [_KAMPO_P18, _KAMPO_P35, _KAMPO_P37]
    bad = c.scan_adjusted(pages, "220")
    assert bad["adjusted_verdict"] == "adjusted_alt", bad
    assert [a["pct"] for a in bad["adjusted_alternatives"]] == ["181"], bad
    good = c.scan_adjusted(pages, "181")
    assert good["adjusted_verdict"] == "unqualified", good


def test_collector_abstains_when_there_is_no_label_bearing_prose():
    """표·차트 전용 문서(15사 중 7사). 기권이 없으면 거짓 발화 7건이다."""
    c = _collector()
    assert c.scan_adjusted(["ESRの推移", "253%|267%|268%"], "268")[
        "adjusted_verdict"] == "abstain_no_prose"


def test_collector_does_not_fire_on_a_range_sentence_beside_a_clean_headline():
    """富国 형태 — 밴드 문장(ターゲットレンジ 230%~270%)이 따로 있고 화면값은 깨끗한 문장에 있다.

    한정어가 **다른 조각의 다른 값**에 붙은 것을 화면값에 옮겨 붙이면 거짓 발화다.
    """
    c = _collector()
    pages = ["配当還元を行ったうえで業界最高水準のESR248.5%を確保し\n"
             "ESRをターゲットレンジ内(230%~270%)に維持することで、"]
    assert c.scan_adjusted(pages, "248.5")["adjusted_verdict"] == "unqualified"


def test_esr_labels_are_all_named_in_the_domain_doc():
    """라벨 목록의 정본은 `docs/domains/claude-agent-jp.md §3` 이다.

    코드가 지어낸 라벨로 검증하면 **검증기가 정본과 다른 목록으로 검증**하게 된다
    (K-ICS 상관행렬을 재타이핑하지 말라는 것과 같은 병). 라벨을 늘리려면 §3 을 먼저 고친다.
    """
    collector = JESR / "check_esr_in_source.py"
    doc = REPO / "docs" / "domains" / "claude-agent-jp.md"
    if not collector.exists() or not doc.exists():
        pytest.skip("jp 도메인 문서/수집기가 없는 트리")
    spec = importlib.util.spec_from_file_location("jesr_esr_collector_under_test", collector)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    text = doc.read_text(encoding="utf-8")
    body = text.split("## 3.", 1)[1].split("\n## 4", 1)[0]
    # 빈 튜플로 떨어지면 라벨이 하나도 없어 **모든 문서가 not_found** 가 되거나(거짓 RED),
    # 근접 판정이 통째로 no-op 이 된다. jesr_http.EXPIRING_HOSTS 와 같은 이유의 방어.
    assert m.ESR_LABELS_STRONG, "라벨 목록이 비었다 — 근접 판정이 no-op 이다"
    assert m.ESR_NEW_STANDARD_MARKERS, "신기준 표지가 비었다 — 구기준 라벨 조건이 무력화된다"
    for lab in list(m.ESR_LABELS_STRONG) + [m.ESR_LABEL_AMBIGUOUS] + list(m.ESR_NEW_STANDARD_MARKERS):
        assert lab in body, f"§3 에 없는 라벨을 코드가 쓰고 있다: {lab!r}"
    # 구기준 단독 라벨은 **ESR 이 아니다**(분모가 リスクの合計額 ×1/2). 무조건 라벨에
    # 섞이면 au損保·明治安田損保의 5개년 구기준 표가 라벨로 읽혀 거짓 통과가 난다.
    assert m.ESR_LABEL_AMBIGUOUS not in m.ESR_LABELS_STRONG


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
    records, census, health_path, esr_path, exc_path = _scenario(tmp_path)
    exc_path.write_text("{ this is not json", encoding="utf-8")
    errors = mod.source_gate_check(records, census, health_path=health_path,
                                   esr_health_path=esr_path, exceptions_path=exc_path,
                                   verbose=False)
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
    # 룰 id 모양만 딴다. `JP_SOURCE_*`(총칭) 나 티켓 파일명의 `JP_MULTI__` 까지 주워
    # 담으면 이 대조가 문서 산문에 따라 흔들린다.
    named = set(re.findall(r"\bJP_[A-Z]+(?:_[A-Z]+)+\b", readme)) - {"JP_SOURCE_EXCEPTIONS"}
    assert named == set(mod.SOURCE_RULE_IDS), (
        f"_README 가 말하는 룰 {sorted(named)} != 코드의 {sorted(mod.SOURCE_RULE_IDS)}")
    for rule in mod.EXEMPTABLE_RULE_IDS:
        assert rule in mod.SOURCE_RULE_IDS


# --------------------------------------------------------------------------
# "배선했다" 가 아니라 "실제로 exit code 를 바꾼다" 를 잰다
# --------------------------------------------------------------------------

_COPY = ["build_jesr_page_json.py", "jesr_http.py", "fy2025_esr_census_20260912.csv",
         "jesr_sources_2026Q1.csv", "jp_insurers.csv", "source_url_health.json",
         "esr_in_source_health.json", "jp_source_exceptions.json", "esr_target_ranges.json"]


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


def test_gate_esr_not_in_source_changes_exit_code(tmp_path):
    """**2026-09-12 사고의 직접 재현.** 東京海上HD 를 238(2차보도 인용값)으로 되돌린다.

    실측(2026-09-13 사본 재현 B): 그 값으로 수집기를 다시 돌리면 決算プレゼン 56페이지
    어디에도 238 이 ESR 라벨 근처에 없어 `not_found` 가 나고, 빌더가 exit 1 이 된다.
    여기서는 네트워크를 타지 않으려고 그 수집 결과를 증거 파일에 직접 심는다.
    """
    script = _sandbox(tmp_path)
    jesr = script.parent
    census = jesr / "fy2025_esr_census_20260912.csv"
    text = census.read_text(encoding="utf-8-sig")
    ev_path = jesr / "esr_in_source_health.json"
    ev = json.loads(ev_path.read_text(encoding="utf-8"))
    victim = next(r for r in ev["rows"] if r["verdict"] == "found" and r["url"] in text)
    old, new = victim["esr_pct"], "238"
    census.write_text(
        re.sub(r"(?m)^(%s,.*?),%s," % (re.escape(victim["company"]), re.escape(old)),
               r"\1,%s," % new, text, count=1), encoding="utf-8")
    assert new in census.read_text(encoding="utf-8"), "census 변이가 안 먹었다"
    victim2 = dict(victim, esr_pct=new, verdict="not_found", page=None, distance=None,
                   label=None, match_rule=None,
                   evidence="56페이지 전체에서 238 이 ESR 라벨 200자/같은 표 행 안에 없다")
    ev["rows"] = [r for r in ev["rows"] if r is not victim] + [victim2]
    ev_path.write_text(json.dumps(ev, ensure_ascii=False), encoding="utf-8")

    proc = _run_builder(script)
    assert proc.returncode == 1, f"화면값이 원문에 없는데 exit {proc.returncode}:\n{proc.stdout}"
    assert "JP_ESR_NOT_IN_SOURCE" in proc.stderr


def test_gate_value_changed_without_recollect_changes_exit_code(tmp_path):
    """census 값만 고치고 수집기를 다시 안 돌리면 **그 자체로** exit 1.

    "고쳤는데 안 돌렸다" 가 조용히 통과하면 이 룰의 이빨은 다음 라운드에 사라진다.
    """
    script = _sandbox(tmp_path)
    jesr = script.parent
    census = jesr / "fy2025_esr_census_20260912.csv"
    text = census.read_text(encoding="utf-8-sig")
    ev = json.loads((jesr / "esr_in_source_health.json").read_text(encoding="utf-8"))
    victim = next(r for r in ev["rows"] if r["verdict"] == "found" and r["url"] in text)
    census.write_text(
        re.sub(r"(?m)^(%s,.*?),%s," % (re.escape(victim["company"]), re.escape(victim["esr_pct"])),
               r"\1,%s," % "999", text, count=1), encoding="utf-8")

    proc = _run_builder(script)
    assert proc.returncode == 1, f"값만 고쳤는데 exit {proc.returncode}:\n{proc.stdout}"
    assert "JP_SOURCE_EVIDENCE_INCOMPLETE" in proc.stderr


def test_gate_adjusted_axis_missing_changes_exit_code(tmp_path):
    """옛 수집기가 만든 증거(= `adjusted_verdict` 없음)는 **exit 1** 이다.

    조정치 축 자체는 YELLOW 라 exit code 를 바꾸지 않는다. 그래서 이 축이 조용히 사라지는
    경로는 딱 하나 — "수집기를 옛 버전으로 돌렸다" 다. 그 경로를 절차 룰이 막는지를 진짜
    빌더를 돌려서 잰다("배선했다" 와 "exit code 를 바꾼다" 는 다른 말이다).
    """
    script = _sandbox(tmp_path)
    ev_path = script.parent / "esr_in_source_health.json"
    ev = json.loads(ev_path.read_text(encoding="utf-8"))
    for row in ev["rows"]:
        row.pop("adjusted_verdict", None)
    ev_path.write_text(json.dumps(ev, ensure_ascii=False), encoding="utf-8")

    proc = _run_builder(script)
    assert proc.returncode == 1, f"조정치 축이 통째로 빠졌는데 exit {proc.returncode}:\n{proc.stdout}"
    assert "adjusted_verdict" in proc.stderr


def test_gate_prints_the_adjusted_finding_end_to_end(tmp_path):
    """**사고 재현(엔드투엔드).** かんぽ를 220 으로 되돌린 사본에서 진짜 빌더가 발화하나.

    실측(2026-09-13): 그 값으로 수집기를 다시 돌리면 `JP_ESR_NOT_IN_SOURCE` 는 **found** 라
    조용하고(220 은 p35 에 실재한다), 조정치 축만 `adjusted_alt` 로 발화하면서 같은 문서의
    한정어 없는 대안값 181% 를 같이 찍는다. 여기서는 네트워크를 안 타려고 그 수집 결과를
    증거 파일에 심는다.
    """
    script = _sandbox(tmp_path)
    jesr = script.parent
    census = jesr / "fy2025_esr_census_20260912.csv"
    text = census.read_text(encoding="utf-8-sig")
    ev_path = jesr / "esr_in_source_health.json"
    ev = json.loads(ev_path.read_text(encoding="utf-8"))
    victim = next(r for r in ev["rows"] if r["company"] == "かんぽ生命保険")
    census.write_text(
        re.sub(r"(?m)^(%s,.*?),%s," % (re.escape(victim["company"]), re.escape(victim["esr_pct"])),
               r"\1,%s," % "220", text, count=1), encoding="utf-8")
    assert ",220," in census.read_text(encoding="utf-8"), "census 변이가 안 먹었다"
    victim2 = dict(victim, esr_pct="220", verdict="found", page=35, distance=1,
                   adjusted_verdict="adjusted_alt",
                   adjusted_qualifiers=["適正水準", "除いた場合"],
                   adjusted_frags=3, adjusted_frags_unqualified=0,
                   adjusted_alternatives=[{"pct": "181", "page": 35,
                                           "evidence": "26.3末のESRは181%と、"}],
                   adjusted_evidence="p35 한정어 ['除いた場合']: …を除いた場合のESRは220%")
    ev["rows"] = [r for r in ev["rows"] if r is not victim] + [victim2]
    ev_path.write_text(json.dumps(ev, ensure_ascii=False), encoding="utf-8")

    proc = _run_builder(script)
    assert proc.returncode == 0, f"YELLOW 인데 exit {proc.returncode}:\n{proc.stdout}{proc.stderr}"
    out = proc.stdout + proc.stderr
    assert "/YELLOW] JP_ESR_ADJUSTED_FIGURE" in out, f"발화가 없다:\n{out}"
    assert "181%(p35)" in out, f"대안값이 메시지에 없다:\n{out}"
    assert "adjusted_alt=1" in out, f"분포 census 에 안 잡혔다:\n{out}"
