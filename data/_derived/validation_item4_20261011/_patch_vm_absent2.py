p = "scripts/validate_master_tables.py"
raw = open(p, "rb").read()
s = raw.decode("utf-8").replace("\r\n", "\n")

def rep(old, new):
    global s
    assert s.count(old) == 1, old
    s = s.replace(old, new)

rep('''    -> (source_absent {(원수사명, 분기)}, ok {(코드, 분기): (kind, approved)}, red [dict]).''',
    '''    -> (source_absent {(원수사명, 분기): (kind, approved)}, ok {(코드, 분기): (kind, approved)}, red [dict]).''')
rep('''    if not reg:
        return set(), {}, []
    try:
        rows = json.loads((ROOT / pl_path).read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001 -- 마스터를 못 읽으면 면제를 줄 수 없다(fail-closed)
        return set(), {}, []''', '''    if not reg:
        return {}, {}, []
    try:
        rows = json.loads((ROOT / pl_path).read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001 -- 마스터를 못 읽으면 면제를 줄 수 없다(fail-closed)
        return {}, {}, []''')
rep('''    return {(code_name.get(c, c), q) for c, q in ok}, ok, red''',
    '''    return {(code_name.get(c, c), q): v for (c, q), v in ok.items()}, ok, red''')
rep('''    name_of = {}
    for (co_n, q_n) in pl_absent_names:
        name_of[co_n] = True
''', '')
rep('''    for co, q in pl_absent_hit:
        kind, approved = next((v for (c2, q2), v in pl_absent_ok.items() if q2 == q and (co == dict.get(dict(), c2, co) or True)), ("?", "?"))
        print(f"  ABSENT-PL {co:14s} {q} [{kind}] ({approved})")''', '''    for co, q in pl_absent_hit:
        kind, approved = pl_absent_names[(co, q)]
        print(f"  ABSENT-PL {co:14s} {q} [{kind}] ({approved})")''')
open(p, "wb").write(s.replace("\n", "\r\n").encode("utf-8"))
print("ok")
