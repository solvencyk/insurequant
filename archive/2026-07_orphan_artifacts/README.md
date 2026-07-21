# Orphaned data artifacts, archived 2026-07-22

Three tracked JSONs under `data/` that **no code, page or doc mentions** —
verified by name-search across every `.py`/`.html`/`.js`/`.md`/`.json` outside
`archive/` and the resolved inbox.

| file | size | why it is dead |
|---|---:|---|
| `csm_bubble_v2.json` | 9.7 KB | the 4-axis bubble V2 was abandoned; `index.html` ships the completed 3-axis bubble **inline** (memory: `project_csm_bubble_complete`) |
| `csm_waterfall_2025.json` | 36.1 KB | superseded by `csm_waterfall.json` + `csm_waterfall_history.json` |
| `nb_csm_widespread_check.json` | 8.1 KB | output of `scripts/check_nb_csm_widespread.py`, which **has never existed in git history** (the validation prompt's V7 row pointed at it; corrected 2026-07-22) |

Untracked from git and moved here rather than deleted — they are the only
record of those runs. Restore with `git mv` + `git add -f` if a rebuild ever
needs to diff against them.
