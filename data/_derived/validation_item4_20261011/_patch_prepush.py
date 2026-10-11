p = "scripts/prepush_check.py"
raw = open(p, "rb").read()
nl = "\r\n" if b"\r\n" in raw else "\n"
s = raw.decode("utf-8").replace("\r\n", "\n")
old = '''            "tests/test_rate_sens_pinned_exemption.py",
            # 분기 지평 트립와이어'''
new = '''            "tests/test_rate_sens_pinned_exemption.py",
            # 데이터계약 selftest(변이 회귀 suite) + PL 주석 계보·원천부재·법인세 확정 등재의 변이시험
            # (2026-10-11, 항목 4 주석 계보 / 하노버 2025.3Q). selftest 는 UH-4 이후 **훅이 한 번도 안 돌렸다**
            # (호출처 0). 게이트에 케이스를 더해도 안 돌면 honor-system 이다. ~55초.
            "tests/test_data_contract_selftest.py",
            "tests/test_pl_fs_note_lineage.py",
            "tests/test_pl_source_absent_exemption.py",
            "tests/test_pl_ytd_collapse_owner_confirmed.py",
            # 분기 지평 트립와이어'''
assert s.count(old) == 1
s = s.replace(old, new)
open(p, "wb").write(s.replace("\n", nl).encode("utf-8"))
print("ok", repr(nl))
