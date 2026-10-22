# -*- coding: utf-8 -*-
"""배포 스크립트 `--only` 범위 한정 (owner 2026-10-23).

왜 있나. jp 레인이 브랜치 `lane/jp` 로 갈라진 뒤(2026-10-22) 그 브랜치의 한국 파일은 낡은 사본이다.
`android_push_and_deploy.sh` 는 main 의 **모든** 파일을 브랜치 사본과 비교해 다르면 덮는다. 그래서
범위 없이 lane/jp 를 배포하면 라이브의 K-ICS·IFRS17 파일이 과거로 되돌아간다. `--only jp/` 가 그걸 막고,
lane/jp 는 `--only` 없이는 스크립트가 시작조차 하지 않는다.

로컬 bare 저장소로 스크립트를 실제로 돌린다(test_private_deploy.py 와 같은 방식, 네트워크 불필요).
**변이 대조**가 핵심이다: 낡은 한국 파일을 가진 브랜치(stale)를 `--only` 없이 돌리면 낡은 사본이 main 을
실제로 덮는다. 이 대조가 없으면 "안 덮였다" 가 `--only` 덕인지 우연인지 알 수 없다.

push 훅(`prepush_check.py`)에는 걸지 않았다: 스크립트를 실제로 돌려 약 2~3분이 걸리고, 같은 방식의
`test_private_deploy.py` 도 훅 밖에 있다. 배포 스크립트나 이 옵션을 고친 뒤에는 손으로 돌린다.
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
from pathlib import Path

import pytest

from test_private_deploy import SCRIPT, _bash, _git

SECRET = "public_exports/secret.json"          # 합성 비공개 경로 — jp/ 범위 밖에 있다
MAIN_NEWER = "main-newer\n"                      # main 에 이미 올라간 최신 한국 파일
STALE = "stale\n"                                # 갈라진 브랜치가 들고 있는 낡은 사본
STALE_KR_FILES = {                               # 갈라진 브랜치가 들고 있는 낡은 한국 파일
    "K-ICS.html": STALE,
    "index.html": STALE,
    "public_exports/a.json": STALE,
    SECRET: "secret\n",
}
JP_FILES = {                                     # lane/jp 에만 있는 jp 쪽 내용
    "jp/jesr_esr.json": "new jp\n",              # main 의 jp-f9027362/jesr_esr.json 과 다르다 -> 갱신 대상
    "jp/index.html": "same jp\n",                # main 과 같다 -> 변화 없음
    "jp/jesr.html": "added jp\n",                # main 에 없는 신규 jp 파일(NEW_FILES 목록에 있는 이름)
}
BRANCHES = {"lane/jp": {**STALE_KR_FILES, **JP_FILES}, "stale": STALE_KR_FILES}   # 대조군 stale 은 jp 가 없어 더 빨리 돈다
MAIN_FILES = {
    "K-ICS.html": MAIN_NEWER,
    "index.html": MAIN_NEWER,
    "public_exports/a.json": MAIN_NEWER,
    SECRET: "secret\n",
    "jp-f9027362/jesr_esr.json": "old jp\n",
    "jp-f9027362/index.html": "same jp\n",
}


def _script_text() -> str:
    """실제 스크립트에 합성 비공개 목록(SECRET 하나)을 주입한다 — 실제 목록은 재공개로 비어 있다."""
    text = SCRIPT.read_text(encoding="utf-8")
    m = re.search(r'^PRIVATE_PATHS="([^"]*)"', text, re.M)
    assert m, "배포 스크립트에 PRIVATE_PATHS=\"...\" 가 없다"
    return text.replace(m.group(0), f'PRIVATE_PATHS="{SECRET}"')


def _put(root: Path, rel: str, text: str) -> None:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8", newline="\n")


def _make_origin(tmp_path: Path, tag: str) -> Path:
    """origin(bare): main = 최신 한국 + 옛 jp. 브랜치 lane/jp = 낡은 한국 + 새 jp, stale = 낡은 한국만(대조군)."""
    bare, seed = tmp_path / f"{tag}.git", tmp_path / f"{tag}_seed"
    subprocess.run(["git", "init", "-q", "--bare", "-b", "main", str(bare)], check=True)
    seed.mkdir()
    _git(seed, "init", "-q", "-b", "main")
    _git(seed, "remote", "add", "origin", str(bare))
    for rel, text in MAIN_FILES.items():
        _put(seed, rel, text)
    _git(seed, "add", "-A")
    _git(seed, "commit", "-q", "-m", "main")
    _git(seed, "push", "-q", "origin", "main")
    for branch, files in BRANCHES.items():
        _git(seed, "checkout", "-q", "-B", branch, "main")
        for rel, text in files.items():
            _put(seed, rel, text)
        _put(seed, "scripts/android_push_and_deploy.sh", _script_text())
        _git(seed, "add", "-A")
        _git(seed, "commit", "-q", "-m", branch)
        _git(seed, "push", "-q", "origin", branch)
    return bare


@pytest.fixture(scope="module")
def origin_template(tmp_path_factory) -> Path:
    """origin 을 모듈에서 한 번만 만든다(git 프로세스 기동이 느린 PC 라 시험마다 만들면 시험당 ~17초가 든다)."""
    return _make_origin(tmp_path_factory.mktemp("only_scope"), "tpl")


def _deploy(tmp_path: Path, tag: str, branch: str, template: Path, *extra: str):
    bash = _bash()
    assert bash and shutil.which("git"), "bash/git 이 없다 — 배포 스크립트를 못 돌리면 이 시험은 아무것도 안 본다"
    bare = tmp_path / f"{tag}.git"
    shutil.copytree(template, bare)                  # 스크립트가 main 을 push 로 바꾸므로 시험마다 새 사본
    clone = tmp_path / f"{tag}_phone"
    _git(tmp_path, "clone", "-q", str(bare), str(clone))
    _git(clone, "fetch", "-q", "origin", branch)
    _git(clone, "checkout", "-q", "-B", branch, f"origin/{branch}")
    env = dict(os.environ, GIT_TERMINAL_PROMPT="0", GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_SYSTEM=os.devnull,
               GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t", GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@t")
    r = subprocess.run([bash, "scripts/android_push_and_deploy.sh", "--from-origin", "--branch", branch, *extra],
                       cwd=clone, capture_output=True, text=True, encoding="utf-8", errors="replace",
                       env=env, timeout=900)
    return r, bare


def _main_blob(bare: Path, rel: str) -> str:
    return _git(bare, "show", f"main:{rel}").stdout


def _main_files(bare: Path) -> set[str]:
    return set(_git(bare, "ls-tree", "-r", "--name-only", "main").stdout.splitlines())


def test_only_jp_deploys_jp_and_leaves_every_other_main_file_alone(tmp_path, origin_template):
    r, bare = _deploy(tmp_path, "only", "lane/jp", origin_template, "--only", "jp/")
    assert r.returncode == 0, r.stdout + r.stderr
    # jp 는 갱신/추가됐다(저장소 jp/ -> main 의 비공개 폴더 jp-f9027362/)
    assert _main_blob(bare, "jp-f9027362/jesr_esr.json") == "new jp\n"
    assert _main_blob(bare, "jp-f9027362/jesr.html") == "added jp\n"
    assert _main_blob(bare, "jp-f9027362/index.html") == "same jp\n"
    # 한국 파일은 낡은 사본으로 덮이지 않았다 — 이 시험의 존재 이유
    for rel in ("K-ICS.html", "index.html", "public_exports/a.json"):
        assert _main_blob(bare, rel) == MAIN_NEWER, f"{rel} 이 --only 범위 밖인데 main 에서 바뀌었다"
    # 범위 밖 비공개 경로도 건드리지 않는다(범위 없이 돌리면 지워진다 — 아래 대조 시험)
    assert SECRET in _main_files(bare), "--only 범위 밖의 비공개 경로가 main 에서 지워졌다"
    assert not any(p.startswith("jp/") for p in _main_files(bare)), "공개 경로 jp/ 가 main 에 생겼다"


def test_lane_jp_without_only_is_refused_and_main_is_untouched(tmp_path, origin_template):
    r, bare = _deploy(tmp_path, "refuse", "lane/jp", origin_template)
    assert r.returncode != 0, "lane/jp 를 --only 없이 배포하도록 허용했다 — 라이브가 과거로 되돌아간다"
    assert "--only" in (r.stdout + r.stderr), "거부 사유에 --only 안내가 없다"
    for rel, text in MAIN_FILES.items():
        assert _main_blob(bare, rel) == text, f"거부했는데 main 의 {rel} 이 바뀌었다"
    assert "jp-f9027362/jesr.html" not in _main_files(bare)


def test_control_without_only_the_stale_branch_does_overwrite_main(tmp_path, origin_template):
    """변이 대조: 같은 내용을 다른 브랜치 이름으로 --only 없이 돌리면 낡은 사본이 main 을 덮는다(종전 동작 그대로)."""
    r, bare = _deploy(tmp_path, "control", "stale", origin_template)
    assert r.returncode == 0, r.stdout + r.stderr
    for rel in ("K-ICS.html", "index.html", "public_exports/a.json"):
        assert _main_blob(bare, rel) == STALE, f"대조군에서 {rel} 이 안 덮였다 — 위 시험의 '안 덮임'이 우연일 수 있다"
    assert SECRET not in _main_files(bare), "옵션 없이 돌렸는데 비공개 경로 제거가 안 됐다 — 종전 동작이 바뀌었다"


@pytest.mark.parametrize("form", [("--only", "nonexistent/"), ("--only=nonexistent/",)])   # 두 표기를 여기서 싸게 확인한다
def test_only_that_matches_nothing_deploys_nothing(tmp_path, origin_template, form):
    r, bare = _deploy(tmp_path, "nothing", "stale", origin_template, *form)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "배포 범위 한정(--only): nonexistent/" in r.stdout, "--only 값이 스크립트에 전달되지 않았다"
    for rel, text in MAIN_FILES.items():
        assert _main_blob(bare, rel) == text, f"범위에 아무것도 없는데 main 의 {rel} 이 바뀌었다"
