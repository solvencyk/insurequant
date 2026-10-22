"""jp 레인(일본 ESR)은 이 브랜치에 없다 — 브랜치 `lane/jp`, 워크트리 `iq_jp` 에서만 작업한다.

2026-10-22 owner 가 "J-ESR·일본 자료는 별도 작업브랜치로" 라고 지시해 분리했다.
이유는 세션 시작 때 붙는 git status·최근 커밋에 CSM 과 jp 가 뒤섞이는 컨텍스트 오염이다.

문서에 "여기서 jp 하지 마라" 라고만 써 두면 honor-system 이다(이 저장소의 반복 사고형태).
옛 세션이 메인 폴더에서 jp 파일을 다시 고쳐 커밋해도 아무것도 막지 못한다. 그래서 push 훅이
돌리는 테스트로 건다: 이 브랜치에 jp 레인 파일이 추적되면 FAIL.

`lane/jp` 에는 이 테스트가 없다(거기서는 jp 파일이 있는 게 정상이다). 두 브랜치를 통째로 merge
하면 이 파일과 jp 삭제가 같이 넘어가 서로를 망가뜨린다 — 공유 파일(게이트·CLAUDE.md·배포
스크립트)은 cherry-pick 으로만 옮긴다.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# jp 레인 소유 경로. `/` 로 끝나면 접두(디렉토리), 아니면 정확 일치(파일).
JP_LANE_PATHS = (
    "J-ESR/",
    "jp/",
    "inbox/jp/",
    "docs/changelog_archive/jp/",
    "TODO_jp.md",
    "docs/changelog_jp.md",
    "docs/todo_archive_jp.md",
    "docs/domains/claude-agent-jp.md",
    "docs/domains/jp_esr_disclosure_template.md",
    ".claude/agents/jp-collector.md",
    "tests/test_jp_source_gate.py",
    "tests/test_jp_deploy_matches_census.py",
)


def jp_lane_files(paths) -> list[str]:
    return sorted(p for p in paths
                  if any(p == j or (j.endswith("/") and p.startswith(j)) for j in JP_LANE_PATHS))


def _tracked() -> list[str]:
    # -z: 기본 git 은 비ASCII 경로를 따옴표 이스케이프로 내보낸다(prepush_check 와 같은 이유).
    p = subprocess.run(["git", "ls-files", "-z"], cwd=str(ROOT), capture_output=True, check=True)
    return [x for x in p.stdout.decode("utf-8").split("\0") if x]


def test_no_jp_lane_file_is_tracked_on_this_branch():
    found = jp_lane_files(_tracked())
    assert not found, (
        f"jp 레인 파일 {len(found)}개가 이 브랜치에 추적돼 있다: {found[:8]} … — jp 는 브랜치 "
        "`lane/jp`(워크트리 iq_jp)에서만 작업한다. 이 커밋에서 jp 파일을 빼라(git rm / 커밋 제외).")


def test_detector_catches_jp_paths_and_only_them():
    """변이시험: 탐지기가 비어 있거나 너무 넓으면 가드가 조용히 무력화된다."""
    assert jp_lane_files(["jp/index.html", "J-ESR/jesr_master.json", "TODO_jp.md",
                          "kics_disclosure.json"]) == [
        "J-ESR/jesr_master.json", "TODO_jp.md", "jp/index.html"]
    # main 의 jp 비공개 폴더 이름·비슷한 이름·다른 스테이지 문서는 잡으면 안 된다
    assert jp_lane_files(["jp-f9027362/index.html", "jpeg/a.json", "docs/changelog_designer.md",
                          "docs/postmortems/PM-2026-09-13_jp_secondary_source_and_dead_url.md"]) == []
