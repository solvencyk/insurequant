# -*- coding: utf-8 -*-
p = "C:/Users/sangwook.cho/Desktop/insurequant/scripts/apply_chubb_ilp_d2_20261012.py"
s = open(p, encoding="utf-8", newline="").read()
def rep(a, b, n=1):
    global s
    assert s.count(a) == n, (a[:70], s.count(a))
    s = s.replace(a, b)
# 1. key names: never use `original_basis*` (scripts/build_master_xlsx.py labels a cell with `original_basis` as a 소급재작성 cell)
rep('ADDED_KEYS = ("original_basis", "original_basis_value", "basis_note", "components_won", "restated_at")',
    '# NOTE: the key `original_basis` must NOT be used here -- scripts/build_master_xlsx.py labels every provenance cell that has it a 소급재작성 (restated) cell\n'
    'ADDED_KEYS = ("general_account_values_eok", "d2_note", "components_won", "d2_applied_at")')
rep('''        pc["original_basis"] = "general_account"
        pc["original_basis_value"] = {"14": c["item14"]["old"], "15": c["item15"]["old"]}
''', '''        pc["general_account_values_eok"] = {"14": c["item14"]["old"], "15": c["item15"]["old"]}
''')
rep('pc["restated_at"] = stamp', 'pc["d2_applied_at"] = stamp')
rep('pc["basis_note"] = (', 'pc["d2_note"] = (')
rep('"정정 전(일반계정) 값은 original_basis_value.")', '"정정 전(일반계정) 값은 general_account_values_eok.")')
rep('(`original_basis_value`) and the components', '(`general_account_values_eok`) and the components')
# 2. robust replace on Windows (another process may hold the file open for a moment)
rep('''def same(a, b) -> bool:''', '''def replace_retry(tmp: Path, path: Path, tries: int = 40, wait: float = 3.0) -> None:
    """os.replace fails with WinError 5 while another process has the target open (a gate run reading it); wait and retry, never half-write"""
    for k in range(tries):
        try:
            tmp.replace(path)
            return
        except PermissionError:
            time.sleep(wait)
    raise SystemExit(f"ABORT: could not replace {path.name} after {tries} tries (file locked) -- the temp file {tmp.name} is left for inspection")


def same(a, b) -> bool:''')
rep('''    for path, data in ((PROV, new_p), (MASTER, new_m)):
        tmp = path.with_suffix(".json.tmp_chubbd2")
        tmp.write_bytes(data)
        tmp.replace(path)
''', '''    for path, data in ((PROV, new_p), (MASTER, new_m)):
        tmp = path.with_suffix(".json.tmp_chubbd2")
        tmp.write_bytes(data)
        replace_retry(tmp, path)
''')
open(p, "w", encoding="utf-8", newline="").write(s)
print("patched")
