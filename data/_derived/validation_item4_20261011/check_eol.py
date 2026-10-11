import sys
for p in ["scripts/validate_kics_disclosure.py","scripts/validate_data_contract.py","scripts/validate_master_tables.py","scripts/_data_contract_selftest.py","tests/test_pl_fs_note_lineage.py","tests/test_pl_source_absent_exemption.py","tests/test_pl_ytd_collapse_owner_confirmed.py","data/_gold/user_pl_confirmed_cells.json","data/_gold/kics_exemption_provenance.json","TODO_validation.md","docs/changelog_validation.md","docs/kics_gate_exceptions.md","docs/claude-changelog.md","docs/todo_archive_validation.md"]:
    b = open(p, "rb").read()
    crlf = b.count(b"\r\n"); lf = b.count(b"\n") - crlf
    print(f"{p:55s} BOM={b[:3]==b'\xef\xbb\xbf'} CRLF={crlf} bareLF={lf}")
