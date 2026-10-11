for p, pairs in (("TODO_validation.md", [("신규 pytest 36건", "신규 pytest 37건(훅 묶음 편입)")]),
                 ("docs/changelog_validation.md", [("pytest 신규 36건 --", "pytest 신규 37건(훅 묶음 `prepush_check.py` 에 편입; selftest 래퍼 `tests/test_data_contract_selftest.py` 포함 -- selftest 는 UH-4 이후 훅이 한 번도 안 돌렸다) --")])):
    raw = open(p, "rb").read()
    s = raw.decode("utf-8")
    for a, b in pairs:
        assert s.count(a) == 1, (p, a)
        s = s.replace(a, b)
    open(p, "wb").write(s.encode("utf-8"))
print("ok")
