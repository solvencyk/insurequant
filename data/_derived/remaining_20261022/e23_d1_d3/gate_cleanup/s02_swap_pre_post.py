# -*- coding: utf-8 -*-
"""Swap the three edited validation files between the POST (edited) and PRE (as found this session) versions,
so the same test list can be run on both.  usage: s02_swap_pre_post.py save|pre|post
  save : copy the current (edited) files to post_copies/ and build pre_copies/ by reversing this session's edits
  pre  : put pre_copies/ in place      post : put post_copies/ back (and verify bytes)"""
import hashlib
import shutil
import sys
from pathlib import Path

ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
HERE = Path(__file__).resolve().parent
FILES = ["scripts/validate_master_tables.py", "tests/test_rule_coverage_manifest.py",
         "tests/fixtures/master_tables_golden.json"]
PRE_GOLDEN = ROOT / "data/_derived/remaining_20261022/e23_d1_d3/backup_before_apply/gate_cleanup/master_tables_golden.json"


def md5(p):
    return hashlib.md5(Path(p).read_bytes()).hexdigest()


def cut(s, start_marker, end_marker, keep_end=True):
    a = s.index(start_marker)
    b = s.index(end_marker, a)
    return s[:a] + (s[b:] if keep_end else s[b + len(end_marker):])


mode = sys.argv[1]
post, pre = HERE / "post_copies", HERE / "pre_copies"
if mode == "save":
    post.mkdir(exist_ok=True)
    pre.mkdir(exist_ok=True)
    for f in FILES:
        shutil.copyfile(ROOT / f, post / Path(f).name)
    # validate_master_tables.py: drop the Lotte WFY entry block and the item-23 entry + its new comment, restore old comment
    s = (ROOT / FILES[0]).read_text(encoding="utf-8")
    s = cut(s, "    # 2026-10-23 owner 결정(D2, ticket 20261023T0900Z)", '    ("롯데손해보험", "2023"),\n', keep_end=False)
    old_comment = (
        "    # item23(법인세)은 2026-09-12(inbox/parser/20260901T1630Z) 에 여기서 빠졌다 -- item23 =\n"
        "    # 22-24 plug 로 무조건 덮어쓰는 동작 자체는 안 바뀌었으니 \"폐쇄식이 검증한다\"는 뜻은\n"
        "    # 아니다. 다만 validate_data_contract.PL_YTD_COLLAPSE_TO_ZERO(같은 FY 인접분기, 직전값\n"
        "    # non-zero -> 이번값 정확히 0.0)가 \"덮어쓴 값이 우연히 0.0\"인 경우를 잡을 수 있게 됐다\n"
        "    # (KDB생명 2023.1Q 를 신규로 채워 2023.2Q 에 처음으로 '직전분기'가 생기면서 실측).\n"
        "    # 상세 근거는 tests/test_rule_coverage_manifest.py::PL_CONSTRUCTIVE_GUARDED[23].\n")
    a = s.index('    23: "법인세 — item23 = 22-24 plug')
    b = s.index("\n}\n", a)
    s = s[:a] + old_comment + s[b + 1:]
    (pre / "validate_master_tables.py").write_text(s, encoding="utf-8", newline="")
    # manifest: move 23 back to GUARDED (old text) and drop the WFY test block
    t = (ROOT / FILES[1]).read_text(encoding="utf-8")
    a = t.index('    23: "법인세 — assemble 이 22-24 로 무조건 덮어쓴다. 2026-09-12~2026-10-23')
    b = t.index("\n}\n", a)
    t = t[:a] + t[b + 1:]
    old23 = (
        '    23: "법인세 — **좁은 커버리지**: assemble 이 22-24 로 무조건 덮어쓰는 건 여전하지만, "\n'
        '        "PL_YTD_COLLAPSE_TO_ZERO(같은 FY 인접분기, 직전값 non-zero -> 이번값 정확히 0.0) 가 "\n'
        '        "\'덮어쓴 값이 우연히 0.0\' 인 경우만 잡는다 — item23 오염 전반을 보는 룰이 아니다. "\n'
        '        "2026-09-12(inbox/parser/20260901T1630Z) 실측: KR0072(케이디비생명) 2023.1Q 를 신규로 "\n'
        '        "채우자(item23=-0.209323, 원문 직접값) 그 전엔 존재하지 않았던 \'직전분기\' 가 생겼고, "\n'
        '        "변이시험이 2023.2Q(기존 override 값 -0.2)를 22-24 로 재계산하면 정확히 0.0 이 되어 "\n'
        '        "걸렸다(대상 회사-분기가 한 번도 없었으면 이 축은 여전히 BLIND — 회사별 인접분기 "\n'
        '        "존재 여부에 좌우된다는 점에서 22 번(2f, 전항 무조건 적용)과 다르다).",\n')
    anchor = '    25: "기타포괄손익 — EQ8 · EQ9(item32 leaf 카탈로그 합)",\n'
    assert t.count(anchor) == 1
    t = t.replace(anchor, anchor + old23)
    t = cut(t, "# 2026-10-23 owner 결정(D2): 롯데손해보험 FY2023", "def test_tax22_prior_tier1_reads_annual_and_quarterly_prior_columns():")
    (pre / "test_rule_coverage_manifest.py").write_text(t, encoding="utf-8", newline="")
    shutil.copyfile(PRE_GOLDEN, pre / "master_tables_golden.json")
    for f in FILES:
        print("saved", f, "post", md5(post / Path(f).name), "pre", md5(pre / Path(f).name))
elif mode in ("pre", "post"):
    src = pre if mode == "pre" else post
    for f in FILES:
        shutil.copyfile(src / Path(f).name, ROOT / f)
        print(mode, f, md5(ROOT / f), "==", md5(src / Path(f).name))
else:
    raise SystemExit("usage: save|pre|post")
