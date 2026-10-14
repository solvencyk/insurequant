# -*- coding: utf-8 -*-
"""scripts/doc_rotate.py 셀프테스트 — 문서를 옮기는 도구가 한 글자도 잃지 않는지 합성 문서로 확인한다.

저장소의 실제 changelog/TODO 는 건드리지 않는다(임시 디렉터리에 ROOT·DOCS 를 바꿔 끼운다).
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import doc_rotate as D  # noqa: E402

CHANGELOG = (
    "# Demo Changelog\r\n\r\n> Last updated: 2026-10-13\r\n\r\n"
    "## 2026-10-13 -- 최신 항목\r\n본문 1\r\n\r\n"
    "## 2026-09-05 -- 전 달 항목\r\n```\r\n## 코드 안의 제목은 항목이 아니다\r\n```\r\n\r\n"
    "## 2026-07-20 -- 옛 항목 A\r\n본문 A\r\n\r\n---\r\n\r\n"
    "## 2026-07-02 -- 옛 항목 B\n본문 B (LF 줄)\n\n"
    "## Archive (pre-2026-06)\n- 압축 보관 한 줄\n"
).encode("utf-8")


@pytest.fixture()
def tree(tmp_path, monkeypatch):
    docs = tmp_path / "docs"
    docs.mkdir()
    monkeypatch.setattr(D, "ROOT", tmp_path)
    monkeypatch.setattr(D, "DOCS", docs)
    monkeypatch.setattr(D, "ARCHIVE_DIR", docs / "changelog_archive")
    return tmp_path


def test_changelog_rotation_keeps_every_byte(tree):
    path = tree / "docs" / "changelog_demo.md"
    path.write_bytes(CHANGELOG)
    D.apply_changelog(D.plan_changelog(path), apply=True)

    active = path.read_bytes()
    assert b"2026-10-13" in active and b"2026-09-05" in active          # 현행 = 최신 달과 그 전 달
    assert "코드 안의 제목은 항목이 아니다".encode() in active           # 코드 블록 안 '## ' 는 경계가 아니다
    assert b"2026-07-20" not in active and "압축 보관".encode() not in active
    assert "> 보관:".encode() in active

    a07 = (tree / "docs" / "changelog_archive" / "demo" / "2026-07.md").read_bytes()
    for needle in (b"## 2026-07-20 -- ", b"---\r\n", b"## 2026-07-02 -- ", "본문 B (LF 줄)".encode()):
        assert needle in a07
    undated = (tree / "docs" / "changelog_archive" / "demo" / "undated.md").read_bytes()
    assert "- 압축 보관 한 줄".encode() in undated

    # 보관된 항목은 원본 바이트 그대로다(줄바꿈 혼재 포함)
    assert "## 2026-07-20 -- 옛 항목 A\r\n본문 A\r\n\r\n---\r\n".encode() in a07


def test_changelog_rotation_is_idempotent(tree):
    path = tree / "docs" / "changelog_demo.md"
    path.write_bytes(CHANGELOG)
    D.apply_changelog(D.plan_changelog(path), apply=True)
    first = {p: p.read_bytes() for p in (tree / "docs").rglob("*.md")}
    D.apply_changelog(D.plan_changelog(path), apply=True)
    second = {p: p.read_bytes() for p in (tree / "docs").rglob("*.md")}
    assert first == second


def test_dry_run_writes_nothing(tree):
    path = tree / "docs" / "changelog_demo.md"
    path.write_bytes(CHANGELOG)
    D.apply_changelog(D.plan_changelog(path), apply=False)
    assert path.read_bytes() == CHANGELOG
    assert not (tree / "docs" / "changelog_archive").exists()


TODO = (
    "# Demo TODO\n\n> 갱신 2026-10-13\n\n## Status (최신 3개)\n\n"
    "- **entry 1** 최신\n  1 의 둘째 줄\n"
    "- **entry 2**\n"
    "- **entry 3**\n"
    "- **entry 4** 밀려야 함\n  4 의 둘째 줄\n\n"
    "- **entry 5** 가장 오래됨\n\n"
    "## 열린 일\n\n- [ ] 남는 일\n"
).encode("utf-8")


def test_todo_status_rotation_moves_only_the_excess(tree):
    path = tree / "TODO_demo.md"
    path.write_bytes(TODO)
    plan = D.plan_todo(path)
    assert len(plan["entries"]) == 5 and len(plan["excess"]) == 2
    D.apply_todo(plan, "2026-10-14", apply=True)

    active = path.read_bytes().decode("utf-8")
    assert "entry 3" in active and "entry 4" not in active and "entry 5" not in active
    assert "## 열린 일" in active and "- [ ] 남는 일" in active
    assert "\n\n## 열린 일" in active                                   # 절 사이 빈 줄 유지

    arch = (tree / "docs" / "todo_archive_demo.md").read_bytes().decode("utf-8")
    assert arch.startswith("# TODO archive")
    assert "## 2026-10-14 밀린 Status" in arch
    assert "- **entry 4** 밀려야 함\n  4 의 둘째 줄" in arch and "- **entry 5** 가장 오래됨" in arch

    D.apply_todo(D.plan_todo(path), "2026-10-14", apply=True)           # 두 번째 실행 = 변화 없음
    assert path.read_bytes().decode("utf-8") == active


def test_todo_rotation_prepends_to_existing_archive(tree):
    path = tree / "TODO_demo.md"
    path.write_bytes(TODO)
    old = "# TODO archive — `TODO_demo.md` (Status 이력, 읽기 지연)\n\n## 옛 블록\n\n- 옛 줄\n"
    (tree / "docs" / "todo_archive_demo.md").write_text(old, encoding="utf-8", newline="")
    D.apply_todo(D.plan_todo(path), "2026-10-14", apply=True)
    arch = (tree / "docs" / "todo_archive_demo.md").read_bytes().decode("utf-8")
    assert arch.index("밀린 Status") < arch.index("## 옛 블록") and arch.endswith("- 옛 줄\n")
