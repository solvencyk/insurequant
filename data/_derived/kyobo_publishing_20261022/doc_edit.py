# -*- coding: utf-8 -*-
from pathlib import Path
p = Path("TODO_publishing.md"); s = p.read_text(encoding="utf-8")
old = "남은 것: ① 오케스트레이터 커밋 뒤 `export_public_sheets.py`(공개본 3시트 + manifest) 재실행·재커밋 ② 배포 시 origin/main 과 다른 파일은"
new = "공개본 재생성 완료(교보 51·152·9행 + manifest build_id `eea3f61c`, `validate_live_artifacts` RED 0). 남은 것: 공개본 재커밋 뒤 배포 시 origin/main 과 다른 파일은"
assert old in s; p.write_text(s.replace(old, new), encoding="utf-8")
c = Path("docs/changelog_publishing.md"); t = c.read_text(encoding="utf-8")
old2 = "공개본은 커밋 뒤 `export_public_sheets.py` 로 재생성한다(다음 단계)."
new2 = "공개본은 커밋 `eea3f61c` 뒤 `export_public_sheets.py` 로 재생성했다: `public_exports/` 변경 4파일(`CSM워터폴` 교보 51행·91셀 · `손익분해PL` 교보 152행·274셀 · `신계약CSM배수` 교보 9행·27셀 · `manifest.json` build_id `99c7ead7` -> `eea3f61c`·generated_at_utc 뿐, 시트별 행수·분기 범위 불변), 나머지 14시트 바이트 동일, `validate_live_artifacts` RED 0 · `validate_data_contract` RED=0."
assert old2 in t; c.write_text(t.replace(old2, new2), encoding="utf-8")
