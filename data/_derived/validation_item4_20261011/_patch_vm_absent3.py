p = "scripts/validate_master_tables.py"
s = open(p, "rb").read().decode("utf-8").replace("\r\n", "\n")
def rep(old, new):
    global s
    assert s.count(old) == 1, old
    s = s.replace(old, new)
rep("    wf_holes, pl_holes = _check_coverage(wf, pl)\n",
    "    pl_absent: dict = {}\n    wf_holes, pl_holes = _check_coverage(wf, pl, absent_out=pl_absent)\n")
rep('''          f"{pl_src_na.get('zleg', 0)}zleg | "
          f"impossible0:''', '''          f"{pl_src_na.get('zleg', 0)}zleg | "
          f"pl_src_absent:{pl_absent.get('ok', 0)}ok/{pl_absent.get('red', 0)}red | "
          f"impossible0:''')
rep('''    # 그대로 남고 아래 `ABSENT-RED` 행이 같이 나간다(= pl_holes 에 들어가 exit code 에 반영).''',
    '''    # 그대로 남고 `원천부재 등재 무효` 행이 HOLE-PL 로 같이 나간다(= pl_holes 에 들어가 exit code 에 반영).''')
open(p, "wb").write(s.replace("\n", "\r\n").encode("utf-8"))
