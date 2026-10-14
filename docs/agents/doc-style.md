# Doc style — TODO_<stage>.md & changelog_<stage>.md

Canonical writing rules for every stage's TODO and changelog (and the root `TODO.md` / `docs/claude-changelog.md`).
Established 2026-06-13; rewritten 2026-10-14 to match what the repo actually does (the old "Done section / one-paragraph Status"
rules had drifted from `CLAUDE.md` §2, and the 2026-10-07 cleanup grew back within a week).

Encoding: UTF-8 **no BOM**. Write English where Korean rendering is fragile. After writing, read back the first lines;
if Korean shows as CJK/mojibake the file got UTF-16 — rewrite. See `CLAUDE.md` encoding rule.

## Who reads what

- **Read at session start:** `CLAUDE.md`, root `TODO.md`, the stage `TODO_<stage>.md`, the stage prompt, the stage inbox. Keep these short.
- **Never read at session start (history, open only to find a past decision):** `docs/changelog_*.md`, `docs/changelog_archive/`,
  `docs/claude-changelog.md`, `docs/todo_archive_*.md`, `docs/claude-md-history.md`.

## Where to write what

| What | Where |
|---|---|
| Open work, dormant items, owner decisions pending | stage TODO (`## 열린 일`, `## 보류`) |
| Where the stage is right now | stage TODO `## Status` — **newest 3 entries, <=3 lines each** (what · commit · what remains) |
| How it was done: numbers, checks, false starts | stage `changelog_<stage>.md` |
| Cross-stage change, deploy round, refactor | root `TODO.md` + `docs/claude-changelog.md` |
| Durable owner decision | the `## 정책` table of the root TODO (or the stage TODO `## 결정`) |
| Evidence and reproduction (run logs, census, diffs) | `data/disclosure/_meta/*runlog*`, `data/_derived/<topic>_<date>/`; cite the path, do not paste it |

## TODO body

Header, first lines after the `# Title`:

```
> 갱신 YYYY-MM-DD · 프롬프트 `docs/agents/claude-agent-<stage>.md` · 이력 `docs/changelog_<stage>.md`
```

`갱신` = the most recent date that appears anywhere in the file. Sections in order: `## Status (최신 3개)` · `## 열린 일` ·
`## 보류`/`## owner 결정 대기 · 휴면` · `## 정책`/`## 결정` (optional) · `## 참조` (optional).

- A finished item is **moved verbatim** to the top of `docs/todo_archive_<name>.md`; it is not summarised in place.
- An item older than 3 months without progress becomes a one-line 「휴면」.
- A claim in the TODO ("3 tickets open", "RED 12") is checked by machine first (`scripts/status_report.py --fast`); if the two disagree, fix the TODO.
- An open item that enumerates ①②③ is written as indented sub-bullets, not one 1,000-character line.

## Changelog body

- Reverse chronological: `## YYYY-MM-DD (x) — <title>` then bullets.
- **Active file = the newest month and the one before it.** Older entries move, untouched, to
  `docs/changelog_archive/<stage>/<YYYY-MM>.md` (undated legacy "Archive" sections to `undated.md`). Cross-stage = `cross_stage/`.
- `docs/changelog_parser.md` is the frozen pre-split (2026-06-13) history; nothing is appended and it does not rotate.

## Upkeep — one tool, byte-preserving, dry run by default

```
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/doc_rotate.py --check                 # what needs rotating
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/doc_rotate.py changelog [--apply]     # monthly
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/doc_rotate.py todo --today YYYY-MM-DD [--apply]   # when a Status block passes 3 entries
```

The tool refuses to write if the moved bytes do not reappear verbatim in the archive. If a later edit cites a moved entry by date or round,
point the citation at the archive file (the active changelog header names the archive directory).

## Trim rules (when compressing an existing heavy file)

- **Never drop an unchecked `[ ]` item or open question.** If it lives inside a DONE block, lift it into the right Open section.
- Don't alter the meaning or numbers of open items; only reformat / relocate / retag.
- Keep IDs stable (F7, V2, NEW-1, RS1, …).
