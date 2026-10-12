"""Doc updates for ticket 20261012T2230Z (TODO status, TODO archive, changelog, GOLD_OVERLAY_CENSUS declaration).

Pure text transforms (functions take the file text and return the new text) so the SAME edit can be applied to
  (a) the working-tree file (keeps other sessions' uncommitted hunks) and
  (b) the HEAD blob (so the commit contains only this ticket's hunks).

usage:
  s131_docs_update.py worktree                 apply to the working-tree files in place
  s131_docs_update.py blobs <outdir>           write HEAD-based versions to <outdir>/<repo-relative path>
All files are written UTF-8 without BOM, LF.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]

STATUS = (HERE / "s130_status_text.txt").read_text(encoding="utf-8").rstrip("\n") + "\n"
CHANGELOG = (HERE / "s130_changelog_text.txt").read_text(encoding="utf-8")
PYTEST_TXT = (HERE / "s130_pytest_text.txt").read_text(encoding="utf-8").strip() if (HERE / "s130_pytest_text.txt").exists() else ""
CHANGELOG = CHANGELOG.replace("@@PYTEST@@", PYTEST_TXT)

TODO = "TODO_parser_ifrs17.md"
ARCH = "docs/todo_archive_parser_ifrs17.md"
CHLOG = "docs/changelog_parser_ifrs17.md"
MANIFEST = "tests/test_rule_coverage_manifest.py"

OLD_10 = "- **2026-10-12 10차:"
STATUS_HEAD = "## Status (최신 3개)\n\n"
TODO_NEXT_SECTION = "## 열린 일"


def split_old10(todo: str) -> tuple[str, str]:
    """-> (todo without the 10차 block, the 10차 block verbatim)"""
    a = todo.index(OLD_10)
    b = todo.index(TODO_NEXT_SECTION, a)
    block = todo[a:b]
    return todo[:a] + todo[b:], block


def edit_todo(todo: str) -> tuple[str, str]:
    if "12차: 최신 비교열 우선 원칙 적재" in todo:
        raise SystemExit("TODO already contains the 12차 block")
    todo = todo.replace("> 갱신 2026-10-12 ·", "> 갱신 2026-10-13 ·", 1)
    todo, moved = split_old10(todo)
    i = todo.index(STATUS_HEAD) + len(STATUS_HEAD)
    return todo[:i] + STATUS + todo[i:], moved


def edit_archive(arch: str, moved: str) -> str:
    title, rest = arch.split("\n\n", 1)
    if moved.split("\n", 1)[0] in rest:
        raise SystemExit("archive already contains the moved block")
    if not moved.endswith("\n"):
        moved += "\n"
    return title + "\n\n" + moved + rest


def edit_changelog(ch: str) -> str:
    if "12차: 최신 비교열 우선 원칙 적재" in ch:
        raise SystemExit("changelog already contains the 12차 section")
    ch = ch.replace("> Last updated: 2026-10-12 ·", "> Last updated: 2026-10-13 ·", 1)
    marker = "## 2026-10-12 (11차:"
    i = ch.index(marker)
    return ch[:i] + CHANGELOG.rstrip("\n") + "\n\n" + ch[i:]


def edit_manifest(src: str) -> str:
    old = '# 실측 2026-08-30 (중복 키 7건 제거 후). 오버레이별 (gold 칸 수, 마스크 칸 수).\nGOLD_OVERLAY_CENSUS = {"CSM": (276, 86), "PL": (203, 29)}'
    new = ('# 실측 2026-08-30 (중복 키 7건 제거 후). 오버레이별 (gold 칸 수, 마스크 칸 수).\n'
           '# 2026-10-13 ticket 20261012T2230Z (parser/ifrs17): gold 만 늘었다 -- CSM +27 · PL +157 (마스크 칸 수 86·29 불변 = 허용오차 불변, 새 gold 칸은 전부 소스와 다르다).\n'
           'GOLD_OVERLAY_CENSUS = {"CSM": (303, 86), "PL": (360, 29)}')
    if old not in src:
        raise SystemExit("GOLD_OVERLAY_CENSUS declaration not found in the expected form")
    return src.replace(old, new, 1)


def head_text(rel: str) -> str:
    return subprocess.run(["git", "show", f"HEAD:{rel}"], cwd=ROOT, capture_output=True, check=True).stdout.decode("utf-8")


def transform_all(get) -> dict[str, str]:
    todo, moved = edit_todo(get(TODO))
    return {TODO: todo, ARCH: edit_archive(get(ARCH), moved), CHLOG: edit_changelog(get(CHLOG))}


def main() -> int:
    mode = sys.argv[1]
    if mode == "worktree":
        def get(rel):
            return (ROOT / rel).read_bytes().decode("utf-8").replace("\r\n", "\n")
        out = transform_all(get)
        # manifest: already edited in the working tree by hand (Edit tool); only verify
        man = get(MANIFEST)
        if '"CSM": (303, 86), "PL": (360, 29)' not in man:
            raise SystemExit("working-tree manifest not updated")
        for rel, txt in out.items():
            (ROOT / rel).write_bytes(txt.encode("utf-8"))
            print("worktree updated", rel, len(txt))
        return 0
    if mode == "blobs":
        outdir = Path(sys.argv[2])
        out = transform_all(head_text)
        out[MANIFEST] = edit_manifest(head_text(MANIFEST))
        for rel, txt in out.items():
            p = outdir / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(txt.encode("utf-8"))
            print("blob written", rel, len(txt))
        return 0
    raise SystemExit(__doc__)


if __name__ == "__main__":
    raise SystemExit(main())
