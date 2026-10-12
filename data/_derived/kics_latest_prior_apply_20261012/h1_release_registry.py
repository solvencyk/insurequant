"""h1_release_registry.py [--apply] -- release the two owner-approved `_TIER2_ISSUER_INCONSISTENT` pins in scripts/validate_kics_disclosure.py
(KR0003 2025.1Q and KR0032 2024.3Q; ticket 20261012T2200Z item 3: the latest prior column values close the rule, so the value pin has no premise left).

Byte-level edit (the file is CRLF): each entry block (comment header + dict entry) is replaced by a short 'released' comment that keeps the
history so nobody re-registers it.  Verification: the module still imports, exactly those two keys are gone from the dict, every other key
and value is identical, the file stays BOM-free and CRLF-only.  Without --apply: verification only, nothing written.
"""
import importlib.util
import re
import sys
from pathlib import Path

sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/kics_latest_prior_apply_20261012")
from lib_apply import *  # noqa: F401,F403,E402

utf8_stdout()
SRC = REPO / "scripts" / "validate_kics_disclosure.py"
apply = "--apply" in sys.argv
raw = SRC.read_bytes()
assert not raw.startswith(b"\xef\xbb\xbf")
text = raw.decode("utf-8")
assert "\n" not in text.replace("\r\n", ""), "file has LF-only line endings - expected pure CRLF"


def block_span(text, head_regex, key_line):
    """[start, end) of a registry entry = from its '# --- ... ---' header line up to and including the closing '    },' line of the dict entry."""
    m = re.search(head_regex, text)
    assert m, head_regex
    start = m.start()
    k = text.index(key_line, start)
    end = text.index("\r\n    },\r\n", k) + len("\r\n    },\r\n")
    return start, end


REL_KR0003 = """    # --- 롯데손해 KR0003 2025.1Q — **2026-10-12 해제됨(owner 승인, 티켓 20261012T2200Z). 다시 등재하지 마라** ---------
    # 등재 사유는 '헤드라인표의 Ⅲ.재분류항목(19,202)만 나머지 행과 1,205억 어긋난다' 였다. 후속 공시 둘(FY2025_Q2 p20 당분기-1분기 열 ·
    # FY2025_Q3 p20 당분기-2분기 열)이 같은 칸을 **17,997** 로 인쇄한다 — 15,657 - 8 - 17,997 = -2,348 = 같은 열의 기본자본으로 정확히 닫힌다.
    # 즉 발행사 자기모순이 아니라 이후 공시의 정정이었고, owner 규칙 '최신 공시 직전 컬럼 채택(2026-10-12)' 으로 마스터 항목 13 을
    # 19,202 → 17,997 로 바꿨다(`data/_gold/kics_restatement_ledger.json` KR0003|2025.1Q|13 as_restated, 되돌리는 값 = 계획
    # `data/_derived/kics_latest_prior_apply_20261012/plans/KR0003_2025.1Q.json` 의 옛값). 박제 셀이 움직여 `TIER2_EXEMPTION_INPUT_DRIFT` +
    # `TIER2_EXEMPTION_INERT` 가 발화하므로 등재를 푼다. 원장(`kics_exemption_provenance.json`)의 이 항목은 status=CONTRADICTED 로 남겼다
    # (같은 (회사,분기)가 다시 등재되면 게이트가 즉시 RED — 한화생명 2025.2Q 선례).
"""
REL_KR0032 = """    # --- NH농협손해 KR0032 2024.3Q — **2026-10-12 해제됨(owner 승인, 티켓 20261012T2200Z). 다시 등재하지 마라** ---------
    # 등재 사유는 '다리 잔차 -522(Ⅲ.재분류항목 8,867 이 자기 각주 공식과 안 맞는다)' 였고, 해제조건은 원장에 이미 적혀 있었다: owner 가
    # as-restated(FY2024_Q4 p43 의 9,390) 채택을 결정하고 parser 가 항목 13 을 갈아끼우면 푼다. 후속 공시 둘(FY2024_Q4 p43 직전분기 열 ·
    # FY2025_Q1 v20261011 p15 전전분기 열)이 모두 **9,390** 을 인쇄하고, 23,478 - 0 - 9,390 = 14,088 ~ 기본자본 14,089(잔차 +1, 반올림)로
    # 닫힌다. owner 규칙 '최신 공시 직전 컬럼 채택(2026-10-12)' 으로 항목 13 을 8,867 → 9,390 으로 바꿨다(`kics_restatement_ledger.json`
    # KR0032|2024.3Q|13 as_restated, 되돌리는 값 = 계획 `data/_derived/kics_latest_prior_apply_20261012/plans/KR0032_2024.3Q.json` 의 옛값).
    # 원장(`kics_exemption_provenance.json`)의 이 항목은 status=CONTRADICTED 로 남겼다(재등재 즉시 RED).
"""
REL_KR0003 = REL_KR0003.replace("\n", "\r\n")
REL_KR0032 = REL_KR0032.replace("\n", "\r\n")

s1, e1 = block_span(text, r"    # --- 롯데손해 KR0003 2025\.1Q -+\r\n", '("KR0003", "2025.1Q"): {')
t1 = text[:s1] + REL_KR0003 + text[e1:]
s2, e2 = block_span(t1, r"    # --- NH농협손해 KR0032 2024\.3Q -+\r\n", '("KR0032", "2024.3Q"): {')
t2 = t1[:s2] + REL_KR0032 + t1[e2:]
print(f"removed block 1: {e1 - s1} chars, block 2: {e2 - s2} chars; file {len(text)} -> {len(t2)} chars")
new_raw = t2.encode("utf-8")
assert not new_raw.startswith(b"\xef\xbb\xbf")
assert "\n" not in t2.replace("\r\n", ""), "LF-only line crept in"

# --- verification: import both versions, compare the registry dicts
import types
def load(path_text, name):
    p = OUT / "_tmp" / f"{name}.py"
    p.parent.mkdir(exist_ok=True)
    p.write_bytes(path_text)
    sys.path.insert(0, str(REPO / "scripts"))
    sys.path.insert(0, str(REPO / "src"))
    spec = importlib.util.spec_from_file_location(name, p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

old_mod = load(raw, "vkd_old")
new_mod = load(new_raw, "vkd_new")
o, n = old_mod._TIER2_ISSUER_INCONSISTENT, new_mod._TIER2_ISSUER_INCONSISTENT
gone = sorted(set(o) - set(n))
assert gone == [("KR0003", "2025.1Q"), ("KR0032", "2024.3Q")], gone
assert set(n) <= set(o)
assert all(o[k] == n[k] for k in n), "a remaining entry changed"
print(f"registry: {len(o)} -> {len(n)} entries; removed {gone}; all other entries identical")
# the rest of the module is unchanged (compare every other module-level registry dict by repr)
for name in ("_LIFE8_ISSUER_INCONSISTENT", "_IDENT_ISSUER_INCONSISTENT", "IRR_DERIVE_ISSUER_INCONSISTENT", "_AFTER_SOURCE_ABSENT_CELLS", "_POST_PARENT_SOURCE_ABSENT_CELLS"):
    assert repr(getattr(old_mod, name, None)) == repr(getattr(new_mod, name, None)), name
if not apply:
    print("dry run: nothing written")
    sys.exit(0)
assert sha_file(SRC) == sha_bytes(raw), "validate_kics_disclosure.py changed while preparing"
tmp = SRC.with_name(SRC.name + ".latestprior.tmp")
tmp.write_bytes(new_raw)
atomic_replace(tmp, SRC)
assert sha_file(SRC) == sha_bytes(new_raw)
print("WROTE", SRC.relative_to(REPO), "sha", sha_file(SRC)[:12])
