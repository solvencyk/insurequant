# -*- coding: utf-8 -*-
"""push 게이트 **범위 판정**의 셀프테스트 — 축소는 빼는 방향이라 여기가 유일한 안전장치다.

## 왜 있나

`CLAUDE.md` §5 는 2026-09-12 에 owner 가 정한 규칙을 적어 뒀다: "번들 범위 diff 가
`jp/`·`J-ESR/`·docs·inbox·TODO·배포 스크립트뿐이면 한국 마스터 게이트(8분)를 돌리지 않는다."
그런데 `scripts/prepush_check.py` 는 **그 규칙을 코드로 보지 않았다** — 무조건 전부 돌았다.
그래서 2026-09-13 에 jp 만 고친 번들이 `RED=197 … BLOCKED` 로 막혔고, 그 197 은 전부 한국
원문(`data/disclosure/`) 부재 때문이라 jp 변경과 인과가 0 이었다. 규칙이 문서에만 있으면
강제도 완화도 안 된다 — 이 저장소가 반복해 온 "문서에 mandatory 라고 썼다 ≠ 강제" 와 같은
병이고 방향만 반대다.

**그런데 범위 축소는 게이트를 좁히는 행위라 이 저장소에서 가장 위험한 코드다.** 목록에 한 줄만
잘못 들어가면 한국 마스터가 무검사로 나간다 — 게이트는 그때도 `gate-clear` 를 찍는다(전형적인
false-green). 그래서 판정기는 ① git 을 안 부르는 순수 함수로 분리돼 있고 ② 여기서 변이시험으로
지킨다. 아래 `MUST_BE_JP` / `MUST_BE_FULL` 은 **판정기의 목록을 참조하지 않고 손으로 다시
적은 기대치**다 — 참조해서 도는 테스트는 목록에서 한 줄이 사라져도 같이 사라져서 통과한다.
"""
from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import prepush_check as P  # noqa: E402


# ---------------------------------------------------------------------------
# 1. 경로 분류 — fail-closed
# ---------------------------------------------------------------------------
# 판정기의 상수를 **쓰지 않고** 손으로 적는다(변이시험 대상). 여기서 한 줄을 지우면
# 판정기에서 그 줄을 지워도 테스트가 통과해 버린다.
MUST_BE_JP = [
    "jp/index.html",
    "jp/jesr_esr.json",
    "J-ESR/jesr_master.json",
    "J-ESR/raw/fy2025_samples/x.json",
    "docs/changelog_jp.md",
    "docs/agents/claude-agent-validation.md",
    "inbox/jp/20260913T0000Z__x.md",
    ".claude/agents/jp-collector.md",
    "TODO_jp.md",
    "TODO.md",
    "TODO_validation.md",
    "scripts/android_push_and_deploy.sh",
    "tests/test_jp_source_gate.py",
    "tests/test_jp_deploy_matches_census.py",
    "CLAUDE.md",
]

MUST_BE_FULL = [
    # 루트 마스터 JSON · 배포 HTML · 워크북 · 프런트 자산
    "kics_disclosure.json",
    "CSM_waterfall.json",
    "PL_breakdown.json",
    "index.html",
    "K-ICS.html",
    "공시보고서.html",                      # 비ASCII 경로도 제대로 분류돼야 한다
    "insurequant_master_tables.xlsx",
    "download-survey.js",
    "common.css",
    # 코드·데이터·테스트
    "scripts/validate_kics_disclosure.py",
    "scripts/validate_data_contract.py",
    "scripts/build_pl_breakdown.py",
    "scripts/sync_tier_utilization_to_deploy.py",   # 배포용이지만 .py 라 전체다
    "src/ifrs17/extract_csm.py",
    "src/solvency/parser/fill_market.py",
    "data/dart/viz/csm_waterfall.json",
    "data/_gold/user_pl_confirmed_cells.json",
    "tests/test_kics_rules_golden.py",
    "tests/unit/test_something.py",
    "templates/kics_template.html",
    "public_exports/CSM_waterfall.json",
    "config/companies.yaml",
    "gold/overlay.json",
    "output/tier1_utilization/x.json",
    ".githooks/pre-push",
    # 모르는 신규 경로 — fail-closed
    "brand_new_dir/whatever.bin",
    "some_new_root_file.txt",
]


@pytest.mark.parametrize("path", MUST_BE_JP)
def test_jp_scope_paths_are_reducible(path):
    v = P.classify_path(path)
    assert v.scope == "jp", (
        f"{path} 가 jp 범위에서 빠졌다(scope={v.scope}: {v.rule}) — jp 전용 번들이 다시 "
        f"8분짜리 한국 게이트에 막힌다. prepush_check.JP_SCOPE_* 를 확인해라."
    )
    assert v.rule.strip(), "판정 근거가 비어 있다 — 화면에 이유가 안 찍힌다"


@pytest.mark.parametrize("path", MUST_BE_FULL)
def test_korean_axis_paths_force_the_full_gate(path):
    v = P.classify_path(path)
    assert v.scope != "jp", (
        f"{path} 가 jp 범위로 분류됐다(rule={v.rule}) — 한국 마스터 축이 무검사로 push 된다. "
        f"이것이 이 파일이 존재하는 이유다."
    )
    assert not P.decide_scope([path]).reduced


def test_unknown_path_is_fail_closed():
    """모르는 경로는 '아마 괜찮겠지' 가 아니라 전체 게이트다."""
    v = P.classify_path("totally/new/thing.parquet")
    assert v.scope == "unknown" and "fail-closed" in v.rule
    d = P.decide_scope(["jp/index.html", "totally/new/thing.parquet"])
    assert not d.reduced and "미분류" in d.reason


def test_absolute_and_traversal_paths_are_unknown():
    assert P.classify_path("/etc/passwd").scope == "unknown"
    assert P.classify_path("jp/../kics_disclosure.json").scope == "unknown"
    assert P.classify_path("").scope == "unknown"


# ---------------------------------------------------------------------------
# 2. 묶음 판정 — 한 개만 섞여도 전체
# ---------------------------------------------------------------------------
JP_ONLY_BUNDLE = ["jp/jesr_esr.json", "jp/jesr_app.js", "J-ESR/jesr_master.json",
                  "docs/changelog_jp.md", "TODO_jp.md"]


def test_jp_only_diff_reduces():
    d = P.decide_scope(JP_ONLY_BUNDLE)
    assert d.reduced, f"jp 전용 번들이 축소되지 않았다: {d.reason}"
    assert len(d.decisive) == len(JP_ONLY_BUNDLE)


def test_one_korean_master_forces_full():
    d = P.decide_scope(JP_ONLY_BUNDLE + ["kics_disclosure.json"])
    assert not d.reduced
    assert [v.path for v in d.decisive] == ["kics_disclosure.json"], \
        "결정적 파일이 정확히 짚여야 한다 — 사람이 '왜 8분이 도나' 를 그 줄로 안다"


def test_one_validator_edit_forces_full():
    d = P.decide_scope(JP_ONLY_BUNDLE + ["scripts/validate_kics_disclosure.py"])
    assert not d.reduced
    assert d.decisive[0].path == "scripts/validate_kics_disclosure.py"


def test_empty_diff_forces_full():
    """빈 diff 는 '바뀐 게 없다' 가 아니라 '탐지에 실패했다' 다 — 축소하면 무검사 push 다."""
    d = P.decide_scope([])
    assert not d.reduced and "판정 불가" in d.reason


def test_force_full_override():
    d = P.resolve_scope(force_full=True)
    assert not d.reduced and "--full" in d.reason


def test_no_upstream_forces_full():
    d = P.resolve_scope(collect=lambda root: (None, "@{upstream} 이 없다(추적 브랜치 미설정)"))
    assert not d.reduced
    assert "upstream" in d.reason and "fail-closed" in d.reason


def test_git_failure_forces_full():
    d = P.resolve_scope(collect=lambda root: (None, "git diff 실패: 워킹트리"))
    assert not d.reduced and "판정 실패" in d.reason


def test_collect_returning_empty_forces_full():
    d = P.resolve_scope(collect=lambda root: ([], "빈 목록"))
    assert not d.reduced


# ---------------------------------------------------------------------------
# 3. 판정 출력 — 조용히 축소되면 그게 다음 사고다
# ---------------------------------------------------------------------------
def test_print_scope_shows_basis_and_decisive_files(capsys):
    d = P.resolve_scope(paths=JP_ONLY_BUNDLE + ["data/dart/viz/csm_waterfall.json"])
    P.print_scope(d)
    out = capsys.readouterr().out
    assert "data/dart/viz/csm_waterfall.json" in out, "결정적 파일이 화면에 안 찍힌다"
    assert "FULL" in out and "비교 기준" in out and "변경 파일" in out


def test_print_scope_reduced_says_what_is_not_running(capsys):
    P.print_scope(P.resolve_scope(paths=JP_ONLY_BUNDLE))
    out = capsys.readouterr().out
    assert "REDUCED (jp-scope)" in out
    assert "jp/jesr_esr.json" in out, "축소 근거가 된 파일 목록이 안 찍힌다"
    assert "안 돈다" in out, "무엇을 안 돌리는지 화면에 없으면 조용한 축소다"


def test_cli_scope_only_is_print_only():
    """`--scope-only` 는 판정만 인쇄하고 게이트를 한 줄도 안 돌려야 한다(디버그 모드)."""
    p = subprocess.run([sys.executable, str(ROOT / "scripts" / "prepush_check.py"),
                        "--scope-only", "jp/jesr_esr.json", "docs/x.md"],
                       cwd=str(ROOT), capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    assert p.returncode == 0, p.stdout[-800:] + p.stderr[-800:]
    assert "REDUCED (jp-scope)" in p.stdout
    assert "jp/jesr_esr.json" in p.stdout
    assert "PRE-PUSH VERDICT" not in p.stdout, "판정만 하라고 했는데 게이트가 돌았다"


def test_cli_rejects_unknown_flags():
    p = subprocess.run([sys.executable, str(ROOT / "scripts" / "prepush_check.py"),
                        "--skip-korean"],
                       cwd=str(ROOT), capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    assert p.returncode == 2, "모르는 플래그를 조용히 무시하면 우회로가 된다"


# ---------------------------------------------------------------------------
# 4. 축소 모드가 **실제로** 무엇을 돌리고 무엇을 건너뛰는가 (배선 ≠ 동작)
# ---------------------------------------------------------------------------
def _stub_offline(monkeypatch, seen):
    """pytest 재귀를 막기 위해 오프라인 묶음 실행을 가짜로 바꾼다(무엇을 넘겼는지 기록)."""
    class _P:
        returncode = 0
        stdout = "1 passed"
        stderr = ""

    def fake_run(cmd, *a, **kw):
        seen.append(list(cmd))
        return _P()

    monkeypatch.setattr(P.subprocess, "run", fake_run)
    import check_inbox_hygiene as hyg
    monkeypatch.setattr(hyg, "main", lambda argv: 0)


def test_reduced_mode_skips_korean_gates_and_runs_only_the_jp_bundle(monkeypatch, capsys):
    seen: list[list[str]] = []
    _stub_offline(monkeypatch, seen)

    def boom():
        raise AssertionError("축소 모드인데 한국 마스터 게이트를 불렀다")

    monkeypatch.setattr(P, "_run_korean_master_gates", boom)
    monkeypatch.setattr(P, "resolve_scope",
                        lambda **kw: P.decide_scope(JP_ONLY_BUNDLE))
    rc = P.main([])
    out = capsys.readouterr().out
    assert rc == 0
    assert "SKIPPED(jp-scope)" in out, "안 돌린 게이트가 'pass' 로 찍히면 그게 false-green 이다"
    bundle = [c for c in seen if "pytest" in " ".join(c)]
    assert bundle, "오프라인 묶음이 아예 안 돌았다"
    ran = [x for x in bundle[0] if x.startswith("tests/")]
    assert ran == P.REDUCED_TEST_BUNDLE, f"축소 묶음이 선언과 다르다: {ran}"
    assert "tests/test_kics_rules_golden.py" not in ran


def test_full_mode_runs_the_korean_gates_and_the_full_bundle(monkeypatch, capsys):
    seen: list[list[str]] = []
    _stub_offline(monkeypatch, seen)
    called = {"n": 0}

    def fake_korean():
        called["n"] += 1
        return {"red": 0, "kics": 0, "dom": 0, "raw": 0, "fp": 0}

    monkeypatch.setattr(P, "_run_korean_master_gates", fake_korean)
    monkeypatch.setattr(P, "resolve_scope",
                        lambda **kw: P.decide_scope(["kics_disclosure.json"]))
    rc = P.main([])
    out = capsys.readouterr().out
    assert rc == 0 and called["n"] == 1, "전체 모드인데 한국 게이트를 안 불렀다"
    assert "SKIPPED(jp-scope)" not in out
    ran = [x for x in [c for c in seen if "pytest" in " ".join(c)][0] if x.startswith("tests/")]
    assert "tests/test_kics_rules_golden.py" in ran and "tests/unit/" in ran


# ---------------------------------------------------------------------------
# 5. 축소 묶음 자체의 무결성
# ---------------------------------------------------------------------------
def test_reduced_bundle_files_exist():
    for rel in P.REDUCED_TEST_BUNDLE:
        assert (ROOT / rel).exists(), f"축소 묶음에 없는 파일 {rel} — push 때 pytest 가 죽는다"


def test_reduced_bundle_is_a_subset_of_the_full_bundle():
    """축소에서만 도는 테스트가 있으면 안 된다 — 전체 게이트가 더 좁아진다는 뜻이다."""
    src = (ROOT / "scripts" / "prepush_check.py").read_text(encoding="utf-8")
    m = re.search(r"fast = \[(.*?)\"tests/unit/\"\]", src, re.S)
    assert m, "prepush_check.py 에서 전체 오프라인 묶음(fast = [...]) 을 못 찾았다"
    full = m.group(1)
    for rel in P.REDUCED_TEST_BUNDLE:
        assert f'"{rel}"' in full, f"{rel} 이 전체 묶음에 없다 — 축소에서만 도는 테스트가 된다"


def test_claude_md_guards_stay_in_the_reduced_bundle():
    """CLAUDE.md 를 jp 범위에 넣은 **전제**를 못 박는다.

    CLAUDE.md 에서 기계가 검사하는 주장은 두 개다: 골든 테스트 표 ↔ tests/test_*_golden.py
    동기화(`test_deploy_assets`), 'mandatory' 게이트 배선(`test_push_gate_wiring`). 둘 다
    축소 묶음에 있어야 CLAUDE.md 수정이 축소돼도 검사 범위가 안 줄어든다. 하나라도 빠지면
    CLAUDE.md 를 jp 범위에서 빼거나 묶음에 되넣어야 한다."""
    assert P.classify_path("CLAUDE.md").scope == "jp"
    for need in ("tests/test_deploy_assets.py", "tests/test_push_gate_wiring.py"):
        assert need in P.REDUCED_TEST_BUNDLE, (
            f"{need} 이 축소 묶음에서 빠졌다 — 그러면 CLAUDE.md 를 jp 범위에 둘 근거가 없다.")


# ---------------------------------------------------------------------------
# 6. 무엇을 비교하나 — git 수집기 (임시 저장소로 실제 git 을 돌린다)
# ---------------------------------------------------------------------------
def _git(repo: Path, *args: str) -> str:
    p = subprocess.run(["git", *args], cwd=str(repo), capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    assert p.returncode == 0, f"git {' '.join(args)} 실패: {p.stderr}"
    return p.stdout


@pytest.fixture()
def tiny_repo(tmp_path: Path) -> Path:
    if shutil.which("git") is None:
        pytest.skip("git 없음")
    repo = tmp_path / "r"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "work")
    _git(repo, "config", "user.email", "t@t")
    _git(repo, "config", "user.name", "t")
    (repo / "seed.txt").write_text("x", encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", "seed")
    return repo


def test_collect_without_upstream_is_unjudgeable(tiny_repo: Path):
    paths, why = P.collect_changed_paths(tiny_repo)
    assert paths is None and "upstream" in why
    assert not P.resolve_scope(root=tiny_repo).reduced


def _pin_upstream(repo: Path) -> None:
    """원격 없이 `@{upstream}` 을 만든다 — 지금 HEAD 가 이미 밀려 있는 상태를 흉내낸다."""
    head = _git(repo, "rev-parse", "HEAD").strip()
    _git(repo, "update-ref", "refs/remotes/origin/work", head)
    _git(repo, "config", "remote.origin.url", ".")
    # fetch refspec 이 없으면 git 이 refs/heads/work -> refs/remotes/origin/work 매핑을 못 찾아
    # `@{upstream}` 이 fatal 로 죽는다(실측). 진짜 클론에는 항상 있는 설정이다.
    _git(repo, "config", "remote.origin.fetch", "+refs/heads/*:refs/remotes/origin/*")
    _git(repo, "config", "branch.work.remote", "origin")
    _git(repo, "config", "branch.work.merge", "refs/heads/work")


def test_collect_sees_commits_staged_worktree_and_untracked(tiny_repo: Path):
    _pin_upstream(tiny_repo)
    (tiny_repo / "jp").mkdir()
    (tiny_repo / "jp" / "a.json").write_text("1", encoding="utf-8")
    _git(tiny_repo, "add", "-A")
    _git(tiny_repo, "commit", "-qm", "jp commit")         # 커밋(업스트림 뒤)
    (tiny_repo / "seed.txt").write_text("y", encoding="utf-8")   # 워킹트리
    (tiny_repo / "staged.md").write_text("s", encoding="utf-8")
    _git(tiny_repo, "add", "staged.md")                   # 스테이지
    (tiny_repo / "loose.bin").write_text("u", encoding="utf-8")  # 미추적
    paths, basis = P.collect_changed_paths(tiny_repo)
    assert set(paths) == {"jp/a.json", "seed.txt", "staged.md", "loose.bin"}, paths
    assert "upstream=origin/work" in basis and "merge-base=" in basis


def test_collect_does_not_quote_non_ascii_paths(tiny_repo: Path):
    """`-z` 가 없으면 git 이 한글 경로를 \\352… 로 이스케이프해 **전부 미분류**가 된다.

    이 저장소에는 `공시보고서.html` 같은 경로가 실재한다 — 그게 미분류로 찍히면 판정은
    fail-closed 라 안전한 쪽이지만, jp 번들도 영원히 축소가 안 된다."""
    _pin_upstream(tiny_repo)
    (tiny_repo / "docs").mkdir()
    (tiny_repo / "docs" / "한글문서.md").write_text("x", encoding="utf-8")
    paths, _ = P.collect_changed_paths(tiny_repo)
    assert "docs/한글문서.md" in paths, f"경로가 이스케이프됐다: {paths}"
    assert P.decide_scope(paths).reduced


def test_collect_keeps_both_sides_of_a_rename(tiny_repo: Path):
    """rename 을 한 줄로 접으면 **없어진 쪽 경로가 목록에서 사라진다**.

    한국 마스터를 jp/ 로 옮기는 커밋이 '전부 jp' 로 보이면 축소가 열린다 — `--no-renames`."""
    (tiny_repo / "kics_disclosure.json").write_text('{"a":1}', encoding="utf-8")
    _git(tiny_repo, "add", "-A")
    _git(tiny_repo, "commit", "-qm", "master")
    _pin_upstream(tiny_repo)
    (tiny_repo / "jp").mkdir()
    _git(tiny_repo, "mv", "kics_disclosure.json", "jp/kics_disclosure.json")
    _git(tiny_repo, "commit", "-qm", "move")
    paths, _ = P.collect_changed_paths(tiny_repo)
    assert "kics_disclosure.json" in paths, f"삭제된 쪽이 사라졌다: {paths}"
    assert not P.decide_scope(paths).reduced
