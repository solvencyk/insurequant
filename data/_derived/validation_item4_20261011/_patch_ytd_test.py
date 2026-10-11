p = "tests/test_pl_ytd_collapse_owner_confirmed.py"
raw = open(p, "rb").read()
nl = "\r\n" if b"\r\n" in raw else "\n"
s = raw.decode("utf-8").replace("\r\n", "\n")
old = '''    assert ytd == [KEY], f"등재 범위가 owner 승인(2026-10-10, 1칸)과 다르다: {ytd}"
'''
new = '''    approved = {
        KEY,                                                    # owner 2026-10-10 (예별 2025.3Q, 보고주체 단절)
        ("스위스리아시아", "2023.2Q", "법인세"),                  # owner 2026-10-11 (원문에 0 인쇄)
        ("퍼시픽라이프리", "2024.4Q", "법인세"),                  # owner 2026-10-11 (감사보고서 당기법인세 '-')
        ("퍼시픽라이프리", "2025.4Q", "법인세"),
    }
    assert len(ytd) == len(set(ytd)) and set(ytd) == approved, (
        f"등재 범위가 owner 승인(2026-10-10 1칸 + 2026-10-11 3칸)과 다르다: {sorted(ytd)}")


def test_every_registered_cell_is_reconfirmed_against_its_source():
    """등재 4칸 전부가 라이브 마스터에서 **붕괴로 잡히고**(INERT 아님) 원천 마커 재확인을 통과해 YELLOW 로 내려온다.
    값·마커가 어긋난 칸이 하나라도 있으면 이 시험이 RED 로 깨진다(디스크 PL_breakdown.json + 원문 PDF 를 연다)."""
    import validate_master_tables as VM
    pl = VM.load_long(VM.PL_PATH)
    env = _Env()
    env.pl = pl
    env.wf = {}
    res = dc.GateResult()
    _ytd_block(res, env)
    ok = {(f.company, f.quarter) for f in res.findings if f.rule == "PL_YTD_COLLAPSE_OWNER_CONFIRMED"}
    assert ok >= {("스위스리아시아", "2023.2Q"), ("퍼시픽라이프리", "2024.4Q"), ("퍼시픽라이프리", "2025.4Q"),
                  ("예별손해보험", "2025.3Q")}, sorted(ok)
    assert not [f for f in res.findings if f.rule in ("PL_YTD_COLLAPSE_TO_ZERO", "PL_YTD_COLLAPSE_CONFIRMED_INERT")], \
        [(f.rule, f.company, f.quarter) for f in res.findings]
'''
assert old in s
s = s.replace(old, new)
if nl == "\r\n":
    s = s.replace("\n", "\r\n")
open(p, "wb").write(s.encode("utf-8"))
