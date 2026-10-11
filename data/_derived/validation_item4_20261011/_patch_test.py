p = "tests/test_pl_fs_note_lineage.py"
s = open(p, encoding="utf-8", newline="").read()
old = '''    # 항목을 가리지 않고 셀 전체를 빼 버린다(가장 흔한 과잉 허용)
    "whole_cell_exempted": ([('        _disc -= _fs_note if not _fs_note else _disc\n', '        _disc -= _fs_note if not _fs_note else _disc\n')],'''
assert old not in s
a = s.index('    # 항목을 가리지 않고 셀 전체를 빼 버린다')
b = s.index('}\n\n\n@pytest.mark.parametrize("name", sorted(DC_MUTANTS))')
new = '''    # 항목을 가리지 않고 entry 의 items 전부를 빼 버린다(가장 흔한 과잉 허용: `& allowed` 누락)
    "entry_items_not_intersected": ([('out |= {int(i) for i in (sf.get("items") or []) if str(i).isdigit()} & allowed',
                                      'out |= {int(i) for i in (sf.get("items") or []) if str(i).isdigit()}')],
                                    {"f_pl_fs_note_reference_only_item", "f_pl_fs_note_mixed_with_item17",
                                     "f_pl_fs_note_other_contract_note_item"}),
'''
s = s[:a] + new + s[b:]
open(p, "w", encoding="utf-8", newline="").write(s)
