# Doc style — TODO_<stage>.md & changelog_<stage>.md

Canonical writing rules for every stage's TODO and changelog (and the root `TODO.md` / `docs/claude-changelog.md`).
Established 2026-06-13 to stop convention drift (stale "Last updated", DONE narrative bloating TODOs).

Encoding: UTF-8 **no BOM**. Write English where Korean rendering is fragile. After writing, read back the
first lines; if Korean shows as CJK/mojibake the file got UTF-16 — rewrite. See `CLAUDE.md` encoding rule.

## Header (both file types)

First lines after the `# Title`:

```
> Last updated: YYYY-MM-DD · Stage N/5 — <stage>
> Prompt: docs/agents/claude-agent-<stage>.md · Changelog: docs/changelog_<stage>.md
```

**Rule (the one that kept breaking):** `Last updated` = the most recent date that appears anywhere in the
file. If you add a 2026-06-12 item, the header says 2026-06-12. No exceptions.

## TODO body — section order

1. `## Status` — 1 short paragraph: where the stage is now + gate status if any.
2. `## 🔴 Open — P1` / `## 🟠 Open — P2` / `## 🟡 Open / waiting` — actionable work only.
   Item shape: `### <ID> — <title>` then detail bullets, or `- [ ] <ID> <one-liner>`. Keep full substance.
3. `## ✅ Done (archive)` — **one line per finished item**:
   `- <ID> <one-line what> — YYYY-MM-DD (changelog <ref>)`. No multi-paragraph narrative here.
4. `## Decisions` (optional) — durable owner decisions, table form.
5. `## Reading order` (optional).

## Changelog body

- Reverse chronological: `## YYYY-MM-DD (x) — <title>` then bullets.
- **Detailed window** = entries in the current month (and the last week of the previous month). Keep full.
- **Older** = collapse into one `## Archive (pre-YYYY-MM)` section, one bullet per entry:
  `- YYYY-MM-DD (x) — <title>: <one-line>`. Full detail stays in git history.

## Trim rules (when compressing an existing heavy file)

- **Never drop an unchecked `[ ]` item or open question.** If it lives inside a DONE block, lift it into the
  right Open section — don't delete it.
- Don't alter the meaning or numbers of open items; only reformat / relocate / retag.
- "Compress" = replace completed multi-paragraph narrative with a one-liner + changelog/git ref. Detail is
  recoverable from git + changelog, so the TODO stays an *index of open work*, not a history dump.
- Keep IDs stable (F7, V2, NEW-1, RS1, …).
