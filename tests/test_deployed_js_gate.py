# -*- coding: utf-8 -*-
"""배포 JS 런타임 게이트(`scripts/validate_deployed_js.py`)의 회귀·변이시험.

**왜 있나.** 2026-09-20 designer 커밋 `2dbc4ca` 가 `K-ICS.html` 의 `function IQP(){…}` 정의만
지우고 호출부 2곳을 남겼다. 라이브 금리민감도 패널이 39사 중 36사에서
`ReferenceError: IQP is not defined` 로 죽은 채 하루 넘게 배포됐는데 **게이트는 전부 초록**
이었다(데이터는 100% 정상 — 순수한 렌더링 사망). 사고 기록은
`docs/postmortems/PM-20260921_kics_sens_iqp_referenceerror.md`.

게이트를 만드는 것만으로는 재발을 못 막는다는 게 이 저장소의 실측 이력이라, 여기서 세 가지를
매 push 마다 강제한다:

  ① **오탐 0** — 지금 트리의 배포 4종이 RED 0. 오탐이 한 번 나면 게이트는 그날로 꺼진다.
  ② **이 사고를 실제로 잡는다** — `IQP` 정의를 (메모리에서) 지우면 RED, 되돌리면 GREEN.
  ③ **동어반복이 아니다** — 탐지기의 규칙을 하나씩 무력화(killer 변이)하면 케이스가 죽는다.
     변이가 전부 살아남는 테스트는 "검사했다" 가 아니라 "아무것도 안 봤다" 이다.

저장소 파일은 **한 바이트도 안 고친다.** 변이는 전부 읽어 온 문자열에만 건다
(`check_page(html=…)`). K-ICS.html 은 designer 소관이라 검증 목적으로도 수정하지 않는다.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import validate_deployed_js as G  # noqa: E402

RULE = "DEPLOYED_JS_UNDEFINED_CALL"
# 사고 그 자체. 이 심볼은 `K-ICS.html` 의 차트 색상 헬퍼이고, 삭제된 것이 이 한 줄이었다.
INCIDENT_PAGE = "K-ICS.html"
INCIDENT_NAME = "IQP"


@pytest.fixture(autouse=True)
def _no_stale_analysis():
    """게이트는 분석 결과를 소스 문자열로 메모이즈한다(변이시험 가속). 변이는 그 함수 자체를
    갈아끼우므로 캐시를 남기면 **변이가 안 보이는** 거짓 통과가 된다 — 매 케이스 비운다."""
    G._ANALYSIS.clear()
    yield
    G._ANALYSIS.clear()


def _html(page: str) -> str:
    p = ROOT / page
    if not p.exists():
        pytest.skip(f"slim 워킹트리: {page} 없음")
    return p.read_text(encoding="utf-8")


def _red(page: str, html: str | None = None) -> list:
    findings, _stats = G.check_page(page, html=html)
    return findings


def _drop_decl(html: str, name: str) -> str:
    """`function NAME(…){…}` 선언 **한 줄**을 지운다 = 이번 사고의 실제 diff 모양
    (`2dbc4ca` 는 한 줄짜리 정의를 통째로 지웠다)."""
    pat = re.compile(rf"^[^\S\n]*function\s+{re.escape(name)}\s*\(.*$\n?", re.M)
    out, n = pat.subn("", html, count=1)
    assert n == 1, f"{name} 선언을 한 줄로 못 찾았다 — 변이시험의 전제가 깨졌다"
    return out


# ---------------------------------------------------------------------------
# ① 오탐 0 — 이 주장이 깨지면 게이트를 끄지 말고 원인을 고쳐라
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("page", G.PAGES)
def test_current_tree_has_no_findings(page):
    """지금 트리의 배포본은 RED 0 이어야 한다(오탐 0 실측의 상주판)."""
    if not (ROOT / page).exists():
        pytest.skip(f"slim 워킹트리: {page} 없음")
    red = _red(page)
    assert not red, (
        f"{page} 에서 배포 JS 게이트가 물었다:\n  "
        + "\n  ".join(f"[{f.rule}] {f.page}:{f.line} {f.name} — {f.message}" for f in red)
        + "\n오탐이라면 scripts/validate_deployed_js.py 의 allowlist·규칙을 고쳐라. "
          "진짜 결함이면 designer 에 발주해서 0 으로 만들어라 — 테스트를 끄지 말 것."
    )


@pytest.mark.parametrize("page", G.PAGES)
def test_every_page_is_actually_scanned(page):
    """"RED 0" 이 "아무것도 안 읽었다" 일 수 있다 — 페이지마다 실제 토큰 수를 못 박는다."""
    if not (ROOT / page).exists():
        pytest.skip(f"slim 워킹트리: {page} 없음")
    _f, st = G.check_page(page)
    assert st["scanned"] == st["pieces"] and st["pieces"] >= 3, (
        f"{page}: 스크립트 조각 {st['scanned']}/{st['pieces']} — 렉서가 못 읽은 조각이 있다")
    assert st["tokens"] > 5000, f"{page}: 토큰 {st['tokens']} — 스크립트 추출이 깨졌다"
    assert st["calls"] > 100, f"{page}: 참조지점 {st['calls']} — 참조 수집이 죽었다"


# ---------------------------------------------------------------------------
# ② 이 사고를 실제로 잡는가 (RED → 복구 → GREEN)
# ---------------------------------------------------------------------------
def test_the_iqp_incident_is_caught_and_the_fix_clears_it():
    """정의를 지우면 RED(호출부 2곳), 되돌리면 GREEN. 2026-09-21 사고의 박제."""
    good = _html(INCIDENT_PAGE)
    assert not _red(INCIDENT_PAGE, good), "출발점이 이미 RED — 변이시험의 대조군이 깨졌다"

    broken = _drop_decl(good, INCIDENT_NAME)
    red = _red(INCIDENT_PAGE, broken)
    hits = [f for f in red if f.rule == RULE and f.name == INCIDENT_NAME]
    assert len(hits) >= 2, (
        f"정의를 지웠는데 {INCIDENT_NAME} 미검출 — 이 게이트는 사고를 못 잡는다. got={red}")
    # 사고 당시 라이브의 호출부는 두 줄이었다(K-ICS.html 1368·1369 on origin/main).
    assert len({f.line for f in hits}) >= 2, "호출부를 한 줄만 보고한다 — 줄 귀속이 깨졌다"

    assert not _red(INCIDENT_PAGE, good), "복구했는데 RED 가 남는다 — GREEN 복귀 실패"


def test_the_incident_shape_is_caught_on_every_deployed_page():
    """같은 사고형태(정의 삭제·호출 잔존)를 4종 **전부**에서 잡는지 전수로 잰다.

    `K-ICS.html` 한 장만 잡는 게이트는 다음에 `IFRS17.html` 이 같은 식으로 죽을 때 또 초록이다.
    페이지마다 `function NAME(` 선언을 하나씩 지워 보고 **검출률 하한**을 강제한다(고정
    심볼 목록을 박으면 designer 가 이름만 바꿔도 테스트가 죽는다 — 하한으로 건다).
    """
    report = {}
    for page in G.PAGES:
        if not (ROOT / page).exists():
            continue
        html = _html(page)
        base = {(f.rule, f.name, f.line) for f in _red(page, html)}
        names = sorted(set(re.findall(r"\bfunction\s+([A-Za-z_$][\w$]*)\s*\(", html)))
        hit = tried = 0
        for nm in names:
            mut, n = re.subn(rf"\bfunction\s+{re.escape(nm)}\s*\(",
                             f"function {nm}__MUTANT(", html, count=1)
            if n != 1:
                continue
            tried += 1
            got = {f.name for f in _red(page, mut) if (f.rule, f.name, f.line) not in base}
            hit += (nm in got)
        report[page] = (hit, tried)
    assert report, "배포 페이지를 하나도 못 읽었다(slim 워킹트리?)"
    for page, (hit, tried) in report.items():
        assert tried >= 15, f"{page}: function 선언 {tried}개 — 표본이 너무 작다"
        assert hit / tried >= 0.70, (
            f"{page}: 정의 삭제 {tried}건 중 {hit}건만 검출({hit/tried:.0%}) — 탐지력이 "
            f"2026-09-21 실측(전체 172/183 = 94%)보다 크게 떨어졌다. "
            f"`defined` 과대추정이 넓어졌는지 확인해라. 전체 보고: {report}")


# ---------------------------------------------------------------------------
# ③ killer 변이 — 탐지기를 무력화하면 ②가 죽어야 한다(동어반복 방지)
# ---------------------------------------------------------------------------
def _iqp_detected() -> bool:
    good = _html(INCIDENT_PAGE)
    broken = _drop_decl(good, INCIDENT_NAME)
    return any(f.rule == RULE and f.name == INCIDENT_NAME
               for f in _red(INCIDENT_PAGE, broken))


def test_mutant_a_allowlisting_everything_kills_the_case(monkeypatch):
    """M-A: 미해결 이름을 전부 내장으로 치면(= allowlist 를 넓히면) 사고를 못 잡는다."""
    monkeypatch.setattr(G, "BROWSER_GLOBALS", frozenset(G.BROWSER_GLOBALS | {INCIDENT_NAME}))
    assert not _iqp_detected(), "allowlist 를 넓혔는데도 검출됐다 — 케이스가 규칙을 안 찌른다"


def test_mutant_b_treating_every_call_as_a_definition_kills_the_case(monkeypatch):
    """M-B: 호출 자리를 정의로 세면(`defined` 무한확장) 아무것도 안 걸린다."""
    real = G.collect

    def wide(toks):
        d, c = real(toks)
        return d | {nm for nm, _ln in c}, c

    monkeypatch.setattr(G, "collect", wide)
    assert not _iqp_detected(), "모든 호출을 정의로 쳤는데도 검출됐다"


def test_mutant_c_dropping_reference_collection_kills_the_case(monkeypatch):
    """M-C: 참조 수집을 비우면(= 룰을 조용히 끄면) 사고를 못 잡는다."""
    real = G.collect
    monkeypatch.setattr(G, "collect", lambda toks: (real(toks)[0], []))
    assert not _iqp_detected(), "참조를 하나도 안 모았는데 검출됐다"


def test_mutant_d_skipping_inline_scripts_kills_the_case(monkeypatch):
    """M-D: 인라인 `<script>` 를 안 읽으면(외부 .js 만 보면) 이 사고는 통째로 안 보인다.

    사고가 난 자리가 바로 인라인 블록이다 — 이 축이 빠지면 게이트가 `SCRIPT_MISSING` 만 보는
    껍데기가 된다."""
    real = G.page_pieces

    def only_external(page, html, git_ref):
        pieces, cdn, missing = real(page, html, git_ref)
        return [p for p in pieces if "(inline @" not in p.label], cdn, missing

    monkeypatch.setattr(G, "page_pieces", only_external)
    assert not _iqp_detected(), "인라인 스크립트를 빼고도 검출됐다"


def test_mutant_e_unscannable_script_is_red_not_silence():
    """M-E: 렉서가 못 읽는 스크립트를 **조용히 넘기면** 그게 다음 false-green 이다.

    fail-closed 여야 한다 — 미종료 문자열을 넣으면 `DEPLOYED_JS_UNSCANNABLE` RED."""
    good = _html(INCIDENT_PAGE)
    broken = good.replace("</head>", "<script>var x = 'unterminated;\n</script></head>", 1)
    rules = {f.rule for f in _red(INCIDENT_PAGE, broken)}
    assert "DEPLOYED_JS_UNSCANNABLE" in rules, (
        f"못 읽은 스크립트가 RED 로 안 올라왔다 (got={rules}) — SKIP-on-unparseable 은 "
        f"검증 무력화다")


def test_mutant_f_missing_local_script_is_red():
    """M-F: `<script src>` 가 가리키는 로컬 파일이 사라져도 RED — 그 페이지 JS 는 통째로 죽는다."""
    good = _html(INCIDENT_PAGE)
    broken = good.replace('src="theme.js"', 'src="theme-gone-forever.js"', 1)
    assert 'theme-gone-forever.js' in broken, "변이 앵커(theme.js)가 바뀌었다 — 테스트를 고쳐라"
    rules = {f.rule for f in _red(INCIDENT_PAGE, broken)}
    assert "DEPLOYED_JS_SCRIPT_MISSING" in rules, f"없는 스크립트가 RED 가 아니다 (got={rules})"


# ---------------------------------------------------------------------------
# 노이즈 내성 — 티켓이 명시적으로 지목한 오탐원(CSS var() · 주석 · 한국어 산문)
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("snippet", [
    "el.style.background = 'var(--iq-accent)'; el.style.color = 'rgba(0,0,0,.5)';",
    "// 없는함수(); 주석 안의 호출은 호출이 아니다\nvar a = 1;",
    "/* var(--x) rgba(1,2,3) 없는함수() */ var b = 2;",
    "var s = `색상 var(--iq-accent) · 없는함수() 는 문자열이다`;",
    "var re = /없는함수\\(/g; var d = 10 / 2 / 1;",
    "var t = `합계 ${String(1 + 2)}`;",
])
def test_lexer_drops_noise_but_keeps_template_expressions(snippet):
    """문자열·주석·정규식은 참조가 아니고, 템플릿 `${}` **안쪽은** 참조다."""
    toks = G.scan_tokens(snippet)
    _defined, refs = G.collect(toks)
    assert "없는함수" not in {n for n, _ln in refs}, "주석/문자열/정규식에서 호출을 주웠다"
    if "${" in snippet:
        assert "String" in {n for n, _ln in refs}, "템플릿 표현식 안의 호출을 못 봤다"


def test_lexer_sees_a_call_inside_a_template_expression():
    """템플릿 안쪽을 안 읽으면 거기서 죽는 코드를 영원히 못 본다(거짓음성 봉쇄)."""
    _d, refs = G.collect(G.scan_tokens("var h = `<b>${없는함수(1)}</b>`;"))
    assert "없는함수" in {n for n, _ln in refs}


def test_member_calls_are_not_flagged():
    """`a.b()` · `a?.b()` 는 전역이 아니다 — 여기서 물면 오탐이 폭발한다."""
    _d, refs = G.collect(G.scan_tokens("x.없는메서드(); y?.또다른(); z['k']();"))
    assert not {n for n, _ln in refs} & {"없는메서드", "또다른"}
