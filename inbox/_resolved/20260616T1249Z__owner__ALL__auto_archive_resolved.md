---
from: owner
to: validation
created: 20260616T1249Z
status: resolved
route: backlog
company: MULTI
period: ALL
iter: 1
---

## 발주 (owner) — resolved 스레드 자동 아카이브 (B, 영구 자동화)

owner 복명령: 끝난 스레드(`status: resolved`)를 에이전트들이 stage 폴더에 **쥐고 안 옮긴다.** 손으로 옮기는 건 같은 수동 취약성이니 **`consolidate_inbox.py`에 자동 단계로 박는다.**

### 구현
- `consolidate_inbox.py` 실행 시: 각 stage 폴더(`inbox/{downloader,parser,validation,publishing,designer}/`)의 `*.md` frontmatter를 읽어 **`status: resolved`면 `inbox/_resolved/`로 이동**. idempotent(이미 `_resolved/`면 skip). 파일명·내용 보존(이동만).
- **`status: answered`는 옮기지 말 것** — sender 재확인 대기 상태(protocol). `resolved`만.
- 이동 시 git-friendly(존재하면 `git mv`, 아니면 plain move). 한글 파일명 안전 처리.

### 일회성 sweep (지금 backlog)
현재 stage 폴더에 `resolved`인데 안 옮겨진 게 13건+ (census 확인분: validation 5 · parser 8). 자동 단계 넣은 뒤 **한 번 실행해 현 적체 전부 `_resolved/`로 정리**하고 몇 건 옮겼는지 회신.

### 주의
- python 풀패스 `C:\Users\sangwook.cho\venvs\insurequant\Scripts\python.exe`. 인라인 멀티라인 `python -c` 금지. UTF-8 no BOM.
- 이동 중 다른 세션이 같은 파일 쓰는 중일 수 있으니 resolved(=완료)만 건드림 = 안전.

## 답변 (validation 2026-06-16 — 자동 아카이브 단계 추가 + 일회 sweep 완료)

✅ **`consolidate_inbox.py`에 자동 단계 박음**: `_archive_resolved()` — 매 실행 시 5개 stage 폴더 frontmatter
스캔, **`status: resolved`만 `inbox/_resolved/`로 이동**(`answered`는 남김 = sender 재확인 대기). idempotent
(`_resolved/`에 동명 있으면 skip), 추적파일=git mv·아니면 plain move, 한글 파일명 안전. main() 말미에 호출.

✅ **일회 sweep 실행**: `python scripts/consolidate_inbox.py` → **14건 이동**(parser 8 · downloader 2 · validation 4).
이제부터 consolidate 돌릴 때마다 끝난 스레드가 자동으로 `_resolved/`로 정리됨 = 손으로 안 옮겨도 됨.

(참고: 동시 세션이 같은 자동화를 돌렸는지 일부 resolved가 이미 _resolved에 있어 동명 skip된 케이스 있음 = 안전.)
status: resolved.
