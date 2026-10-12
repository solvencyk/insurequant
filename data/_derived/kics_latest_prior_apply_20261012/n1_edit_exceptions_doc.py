"""n1_edit_exceptions_doc.py [--apply] -- align docs/kics_gate_exceptions.md with the code for the two released tier2 pins (ticket 20261012T2200Z).

Edits (LF-only file, UTF-8 no BOM):
  1. dated 'current state' note under the tier2 section header (code is the source of truth: 20 buckets / 40 findings / 35 RED-exempt after the release)
  2. the KR0003 2025.1Q row of the series-2 table is removed
  3. the stale bullet 'KR0032 NH농협손해 2024.3Q - 미조사라 RED 유지' (3 lines) is replaced by the release note; a release bullet for KR0003 2025.1Q is added
"""
import sys

sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/kics_latest_prior_apply_20261012")
from lib_apply import *  # noqa: F401,F403,E402

utf8_stdout()
P = REPO / "docs" / "kics_gate_exceptions.md"
apply = "--apply" in sys.argv
raw = P.read_bytes()
assert not raw.startswith(b"\xef\xbb\xbf") and b"\r\n" not in raw
t = raw.decode("utf-8")
lines = t.split("\n")

# ---- 1. dated note under the tier2 section header
hdr_idx = next(i for i, l in enumerate(lines) if l.startswith("**✅ Tier2/기본자본다리 issuer self-inconsistency"))
note = ("> **2026-10-12 현행(정본은 코드 `_TIER2_ISSUER_INCONSISTENT`):** 20버킷 · finding 40건 재검산(그중 RED 면제 35). 이 절의 표·건수는 2026-08-24 시점 서술이라 "
        "그 뒤 등재분(재보사·AIG 2025.3Q·농협생명 2026.2Q 등)이 빠져 있고 코드보다 뒤처져 있다. **이번 갱신: 롯데손해 2025.1Q · NH농협손해 2024.3Q 2버킷 해제(22 → 20)** — "
        "owner 승인(최신 공시 직전 컬럼 채택, 티켓 `20261012T2200Z`), 아래 맨 끝 목록과 원장 `data/_gold/kics_exemption_provenance.json`(status `CONTRADICTED`)·"
        "`data/_gold/kics_restatement_ledger.json`(as_restated) 참조.")
assert not any("2026-10-12 현행" in l for l in lines)
lines.insert(hdr_idx + 1, "")
lines.insert(hdr_idx + 2, note)

# ---- 2. remove the KR0003 2025.1Q table row
rows = [i for i, l in enumerate(lines) if l.startswith("| **KR0003 롯데손해** | **2025.1Q** | `2_tier1_bridge` |")]
assert len(rows) == 1, rows
del lines[rows[0]]

# ---- 3. the NH 2024.3Q bullet (3 lines) + release bullets
b = [i for i, l in enumerate(lines) if l.startswith("> - **KR0032 NH농협손해 2024.3Q** — 다리 잔차 −522.")]
assert len(b) == 1, b
i0 = b[0]
assert lines[i0 + 1].startswith(">   아니라 추측이다. 다음 라운드."), lines[i0 + 1]
new_bullets = [
    "> - ~~KR0032 NH농협손해 2024.3Q~~ — 2026-08-24(3차)에 등재(원장 `VERIFIED`)됐다가 **2026-10-12 해제**(owner 승인, 티켓 `20261012T2200Z`): 후속 공시 둘(FY2024_Q4 p43 · FY2025_Q1",
    ">   p15)이 `Ⅲ.재분류항목` 을 **9,390** 으로 인쇄하고 `23,478 − 0 − 9,390 = 14,088 ≈ 기본자본 14,089`(잔차 +1, 반올림)로 닫혀 마스터 항목 13 을 8,867 → 9,390 으로 교체했다.",
    ">   박제 `cells`(항목 13)가 움직여 `TIER2_EXEMPTION_INPUT_DRIFT` · `INERT` 가 발화하므로 등재를 풀었다(원장은 status `CONTRADICTED` 로 남김 — 재등재하면 즉시 RED).",
    "> - ~~KR0003 롯데손해 2025.1Q~~ — **2026-10-12 해제**(owner 승인, 티켓 `20261012T2200Z`): 후속 공시 둘(FY2025_Q2 p20 · FY2025_Q3 p20)이 `Ⅲ.재분류항목` 을 **17,997** 로 인쇄하고",
    ">   `15,657 − 8 − 17,997 = −2,348` = 같은 열의 기본자본으로 정확히 닫혀(발행사 자기모순이 아니라 이후 공시의 정정) 마스터 항목 13 을 19,202 → 17,997 로 교체했다.",
    ">   박제 셀이 움직여 `INPUT_DRIFT` · `INERT` 가 발화하므로 등재를 풀었다(원장 `CONTRADICTED`). 되돌리는 값 = `data/_derived/kics_latest_prior_apply_20261012/plans/*.json` 의 옛값.",
]
lines[i0:i0 + 2] = new_bullets
t2 = "\n".join(lines)
new_raw = t2.encode("utf-8")
assert not new_raw.startswith(b"\xef\xbb\xbf") and b"\r\n" not in new_raw
print(f"docs/kics_gate_exceptions.md: {len(raw)} -> {len(new_raw)} bytes | lines {len(t.split(chr(10)))} -> {len(lines)}")
if not apply:
    print("dry run: nothing written")
    sys.exit(0)
assert sha_file(P) == sha_bytes(raw)
P.write_bytes(new_raw)
print("WROTE", P.relative_to(REPO), sha_file(P)[:12])
