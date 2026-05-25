# Downloader profiles

Each YAML file describes one insurer's disclosure page. Adding a new
company should mean adding a YAML file here, not a new Python module.

## Required keys

- `company_code` - the canonical KR identifier
- `company_name` - human readable
- `site_type` - one of `case_a_direct_pdf`, `case_b_button_click`,
  `case_c_zip_attachment`. Mapped to handlers in
  `src/solvency/downloader/runner.py`.
- `base_url`, `disclosure_url`
- `selectors` - DOM selectors that the handler uses
- `filename_rule` - templated string used by the engine

## Status

These files are skeletons. The matching handlers in `runner.py` log a
warning and produce zero candidates. The legacy implementations under
`src/solvency/legacy/downloaders/` are kept as the reference behaviour
to port in.
