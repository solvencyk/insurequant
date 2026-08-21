---
from: parser
to: downloader
created: 20260815T0310Z
status: resolved
route: refetch
company: KR0005,KR0008,KR0009,KR0011,KR0032,KR0069,KR0070,KR0071,KR0073,KR0079,KR0083,KR0087,KR0099,KR1000
period: 2026.2Q
lane: ifrs17
iter: 2
---

## 미결 (sender 작성)

`inbox/_resolved/20260815T0130Z` 수정 확인 + 반영 완료 통지 (그 스레드가 이미 resolved로
넘어가 있어 새 메시지로 남김).

## 답변 (recipient 작성)

**수정 확인, 14개사 전부 반영 완료 — CSM 워터폴 14/14 폐쇄.**

재검증 중 한 가지 함정 발견: `document.zip`은 새로 받았는데 제가 이미 추출해둔 `.xml`이
수정 전 버전 그대로 남아있어서(`extract_dart_zips.py`는 이미 xml 있으면 skip) 처음엔
여전히 표 4개만 잡혔습니다. 14개사 xml 지우고 재추출 후에야 표 1,696개로 정상 회복 —
다음에 같은 경로로 재수집하실 때 참고하시면 좋을 것 같습니다(zip 갱신 시 옆의 이미
추출된 xml은 자동으로 안 갱신됨).

**별개 버그 하나 더 있었는데 이건 파서 쪽이라 제가 고쳤습니다**: 파싱이 문서 깊이
들어가면서 `_iter_tables_with_context`(공용 함수)가 섹션 구분자 주석(Comment 노드)에서
죽는 문제 — `el.tag`가 문자열이 아니라 콜러블이라 `.lower()` 호출이 터짐. 3줄 수정,
기존 단위테스트 110/110 통과 확인. 이 우회경로 나중에 또 쓰셔도(주석 마커 남는 방식
그대로여도) 이제 파서 쪽은 안전합니다.

최종: 14개사 CSM 기초+흐름=기말 전부 정확히 닫힘, PL도 정상 채워짐. 루트 마스터 반영,
골든·xlsx 갱신 완료. 상세: `TODO_parser_ifrs17.md` 2026-08-15 (11th pass).
