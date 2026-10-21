# -*- coding: utf-8 -*-
from pathlib import Path
p = Path("TODO_publishing.md"); s = p.read_text(encoding="utf-8")
old = "공개본 재생성 완료(교보 51·152·9행 + manifest build_id `eea3f61c`, `validate_live_artifacts` RED 0). 남은 것: 공개본 재커밋 뒤 배포 시"
new = "2라운드(parser `5f818b59`, 교보 2023.3Q `값_당분기` 19셀): xlsx `손익분해PL` 19셀 재동기화 · 공개본 재생성(교보 19행 + manifest build_id `5f818b59`), 게이트 RED 0. 남은 것: 재커밋 뒤 배포 시"
assert old in s; p.write_text(s.replace(old, new), encoding="utf-8")
c = Path("docs/changelog_publishing.md"); t = c.read_text(encoding="utf-8")
anchor = "## 2026-10-19 (밤) — 손해율 비교 단위 데이터"
add = ("- **2라운드(parser `5f818b59`: 교보 2023.3Q `값_당분기` 19셀, 항목 15 는 빈 칸)**: `손익분해PL` 시트만 다시 동기화(`.bak_20261022_kyobo_pl_r2`, 변한 셀 19 전부 KR0073 2023.3Q `값_당분기`, 나머지 18시트 값 동일). "
       "`export_public_sheets.py` 재실행: `손익분해PL.json` 교보 19행 · `manifest.json`(build_id `eea3f61c` -> `5f818b59`, generated_at_utc) 뿐. 패널 2종은 `--check` 로 변동 없음 확인(비교 패널은 `값` YTD 만 읽음). "
       "`validate_data_contract` RED=0 · `validate_live_artifacts` RED=0 · `test_master_xlsx_clean_state_has_no_red` 통과. 배포 파일 9개 불변, 라이브 build_id = `5f818b59`.\n\n")
i = t.index(anchor); j = t.rfind("\n\n", 0, i)  # end of previous (Kyobo) block
t = t[:j + 2] + add + t[j + 2:] if False else t
# append inside the Kyobo block: insert before the blank line preceding anchor
t = t[:i].rstrip("\n") + "\n" + add.rstrip("\n") + "\n\n" + t[i:]
c.write_text(t, encoding="utf-8")
