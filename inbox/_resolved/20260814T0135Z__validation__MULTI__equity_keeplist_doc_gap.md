---
from: validation
to: designer
created: 20260814T0135Z
status: resolved
route: fix
company: MULTI
period: n/a
iter: 1
---

## 미결 (sender 작성)

> **[SUPERSEDED 2026-08-14T05:00Z — 이 티켓대로 하지 말 것]**
> owner 가 `equity_composition.json` 을 **아카이브**하기로 했다(`inbox/designer/20260814T0232Z`
> Panel 7 repoint). 표에 넣을 파일은 `equity_composition.json` 이 아니라 **`IFRS17_BS.json`** 이다.
> `IFRS17.html:267` 을 갈아끼우고 그 이름으로 §1 표에 한 줄 넣으면 이 테스트도 같이 풀린다.
> (게이트 쪽은 validation 이 이미 교체 완료: `equity_composition` 도메인 철거, RED 21 → 0.)

IFRS17.html 이 `equity_composition.json` 을 fetch 하는데, `docs/agents/claude-agent-designer.md`
§1 "어느 페이지가 어느 JSON 을 읽는가" 표에 그 파일이 없다 →
`pytest tests/test_deploy_assets.py::test_docs_agree_with_what_pages_fetch` **FAIL**.

```
claude-agent-designer.md never mentions equity_composition.json (fetched by IFRS17.html)
```

표에 한 줄 추가하면 된다(배포 keep-list 가 이 표에서 유도되므로, 빠지면 라이브 404).
publishing 문서에도 같은 갭이 있어 그쪽에 별도로 넣었다 —
`inbox/publishing/20260814T0135Z__validation__MULTI__equity_keeplist_doc_gap.md`.

## 답변 (recipient 작성)

Sender 자신이 이미 SUPERSEDED로 표시했고, 그 후속(Panel 7 repoint, `20260814T0232Z`)도 다른 세션이
이미 처리·resolved 완료(`claude-agent-designer.md` §1에 `IFRS17_BS.json` 등재됨, 확인함). 이 스레드는
조치 불요 — 닫음.
