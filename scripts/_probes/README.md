# scripts/_probes

One-off diagnostic scripts only (disposable: write, run, delete). The repo's own tests already treat this folder as disposable.

The four tools below stay because `docs/flows/kics_quarterly_round.md` and `docs/agents/source-catalog.yaml` call them every quarter:

- `census_q2_disclosure_listings.py`, `census_q2_life_own_sites.py`: which 정기경영공시 filings are posted yet.
- `verify_q2_disclosure_content.py`: content check right after a download.
- `render_kics_page.py`, `render_kics_pages.py`: render a PDF page or a contact sheet for a visual read.

Older probes (about 1,600 files) and the dated one-shot `fix_*` / `apply_*` / `bspl_*` scripts were removed on 2026-10-24. Recover one with `git log --diff-filter=D --oneline -1 -- <path>`, then `git show <that-commit>^:<path>`.
