# Unreferenced scripts, archived 2026-07-22

60 files (7,783 lines) moved out of `scripts/` because **nothing in the repo
mentioned them** — not code, not docs, not `.claude/skills/`, not the inbox
threads, not provenance JSON under `data/`. They were not deleted: in this
repo a one-shot script is often the only record of how a particular cell was
produced, and the `fix/csm` raw-data purge means some of it cannot be
re-derived.

## Why archive rather than delete

`scripts/` is the first place an agent looks. 60 of 217 files being dead
weight makes every survey of it noisier and invites someone to "fix" a
script that no longer has a job. Moving them keeps the audit trail while
letting `scripts/` describe what the pipeline actually runs today.

## How the list was derived

Walked every file in the repo except `.git/`, `__pycache__/`, `node_modules/`
and `archive/` — 4,204 text files including `.claude/skills/` and `data/` —
and kept the scripts whose stem appeared in **zero** other files. Dynamic
invocation was checked separately: every `subprocess.run` call site in
`scripts/` passes a literal filename, so those references are caught by the
same substring scan.

A first pass used `pathlib.glob('**/*.md')`, which silently skips
dot-directories and therefore never read `.claude/skills/` — the operational
SOT. Re-running over the full walk produced the same 60, so the list is not
an artefact of that gap.

## What is in here

| group | files | note |
|---|---|---|
| `crawl_ir_*`, `parse_ir_*`, `redownload_*_ir_*` | 16 | per-company IR deck/factbook crawlers + parsers (F18 IR track) |
| `backfill_q123_*` | 6 | per-company 2023 Q1–Q3 K-ICS backfills, already applied |
| `ifrs17_batch_*`, `ifrs17_{summarise,dump_table,fetch_samsung_life}` | 8 | per-extractor batch runners; `ifrs17_batch_all.py` (still in `scripts/`) is the live entry point |
| `_probes/*`, `_diag_*`, `_csmprobe`, `_ab_compare`, `_plint_check` | 13 | one-shot diagnostics from specific investigations |
| misc one-shots | 17 | `verify_q4`, `sample_pdf_content`, `xlsx_to_kics_disclosure_json`, … |

## Restoring one

```
git mv archive/2026-07_unreferenced_scripts/<name>.py scripts/<name>.py
```

Check it still runs before relying on it — these have not been exercised
since they were written, and the 2026-07-21 refactor removed
`src/solvency/{legacy,transform}` and `validation/{rules,schema}.py`, so
anything importing those will need updating.
