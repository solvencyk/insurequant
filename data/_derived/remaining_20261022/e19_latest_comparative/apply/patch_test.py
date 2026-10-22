from pathlib import Path
p = Path("C:/Users/sangwook.cho/Desktop/insurequant/tests/test_rule_coverage_manifest.py")
raw = p.read_bytes()
crlf = b"\r\n" in raw
s = raw.decode("utf-8").replace("\r\n", "\n")
old1 = '_TAX22_KYOBO_RESTATED = [("교보생명보험", q) for q in ("2023.3Q", "2023.4Q", "2024.1Q", "2024.2Q")]\n'
new1 = old1 + '''# 2026-10-22 ticket 20261022T0900Z: 다른 6사 18버킷도 최신 비교열로 갱신됐다(DB생명은 세금 불변). 분기를 빼면 이 22칸이 FAIL 로 돌아온다(실측).
_TAX22_LATEST_COMPARATIVE_ONLY = set(_TAX22_KYOBO_RESTATED) | {
    ("NH농협손해보험", q) for q in ("2023.4Q", "2024.1Q", "2024.2Q", "2024.3Q")} | {("농협생명보험", "2023.3Q")} | {
    ("동양생명", q) for q in ("2023.4Q", "2024.1Q", "2024.2Q", "2024.3Q")} | {
    ("에이비엘생명보험", q) for q in ("2024.1Q", "2024.2Q", "2024.3Q")} | {("푸본현대생명보험", q) for q in ("2024.1Q", "2024.2Q")} | {
    ("흥국화재", q) for q in ("2023.3Q", "2023.4Q", "2024.1Q", "2024.2Q")}
'''
assert s.count(old1) == 1
s = s.replace(old1, new1)
old2 = "        assert _tax22_fail_keys(V, rows) == set(_TAX22_KYOBO_RESTATED)\n"
new2 = "        assert _tax22_fail_keys(V, rows) == _TAX22_LATEST_COMPARATIVE_ONLY\n"
assert s.count(old2) == 1
s = s.replace(old2, new2)
s = s.replace("    # (a) 분기를 빼면 교보 4칸이 RED 로 돌아온다 = 이 분기가 실제로 읽힌다", "    # (a) 분기를 빼면 최신 비교열로만 통과하는 22칸(교보 4 + 다른 6사 18)이 RED 로 돌아온다 = 이 분기가 실제로 읽힌다")
out = s.replace("\n", "\r\n") if crlf else s
p.write_bytes(out.encode("utf-8"))
print("crlf", crlf)
