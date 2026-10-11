p = "tests/test_pl_ytd_collapse_owner_confirmed.py"
raw = open(p, "rb").read()
nl = "\r\n" if b"\r\n" in raw else "\n"
s = raw.decode("utf-8").replace("\r\n", "\n")
a = s.index("def test_every_registered_cell_is_reconfirmed_against_its_source")
new = '''def test_every_registered_cell_is_reconfirmed_against_its_source():
    """등재 4칸 전부가 라이브 마스터·원문 PDF 로 재확인된다 -- 값/마커가 어긋난 칸이 하나라도 있으면 RED 가 돌아와 깨진다.
    (데이터가 채워져 붕괴가 사라진 칸은 게이트가 INERT YELLOW 로 알리는 일이라 여기서는 막지 않는다.)"""
    import validate_master_tables as VM
    pl = VM.load_long(VM.PL_PATH)
    env = _Env()
    env.pl = pl
    env.wf = {}
    res = dc.GateResult()
    _ytd_block(res, env)
    reds = [(f.company, f.quarter, f.message) for f in res.findings
            if f.severity == "RED" and f.rule == "PL_YTD_COLLAPSE_TO_ZERO"]
    assert not reds, reds
    seen = {(f.company, f.quarter) for f in res.findings
            if f.rule in ("PL_YTD_COLLAPSE_OWNER_CONFIRMED", "PL_YTD_COLLAPSE_CONFIRMED_INERT")}
    assert seen >= {("스위스리아시아", "2023.2Q"), ("퍼시픽라이프리", "2024.4Q"), ("퍼시픽라이프리", "2025.4Q"),
                    ("예별손해보험", "2025.3Q")}, sorted(seen)
'''
s = s[:a] + new
if nl == "\r\n":
    s = s.replace("\n", "\r\n")
open(p, "wb").write(s.encode("utf-8"))
