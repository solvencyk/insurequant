---
from: publishing
to: designer
created: 20260624T0134Z
status: resolved
route: fyi
company: MULTI
period: "-"
lane: "-"
---

## 알림 (publishing, owner 직접지시) — 4개 배포 HTML에 CSP meta 추가 (지우지 말 것) + SRI 후속

owner가 펜테스트 결과 보안 강화 A안(SRI + CSP)을 직접 적용/배포 지시. publishing이 owner 지시로 HTML을
**직접 편집**(평소 designer 소관이나 이번 건 owner override). 라이브 main 배포 완료(`01a9c72`).

### 적용 내용 (index.html · K-ICS.html · IFRS17.html · 공시보고서.html, 각 L5)
`<meta charset>` **바로 뒤** = `<head>` 첫 자식에 CSP meta 삽입:
```
<meta http-equiv="Content-Security-Policy" content="default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; font-src 'self' https://cdn.jsdelivr.net; img-src 'self' data:; connect-src 'self'; object-src 'none'; base-uri 'self'; form-action 'self'"/>
```

**⚠️ designer 주의:**
- 이 meta는 **반드시 `<head>` 첫 위치(CDN `<link>`/`<script>` 태그보다 위)** 유지 — 아래로 내려가면 CDN 로드가 정책 적용 전에 시작돼 통제 누락. 지우거나 위치 옮기지 말 것.
- 새 외부 출처(다른 CDN·도메인) 추가 시 해당 디렉티브에 출처 추가 필수, 안 하면 그 리소스 조용히 차단됨.
- `'unsafe-inline'`은 인라인 데이터 스크립트/스타일 때문에 유지(정적사이트라 nonce 불가). 인라인 JS를 외부 .js로 빼면 추후 tighten 가능.
- frame-ancestors/report-uri는 meta CSP에서 무시됨 → 클릭재킹 방어는 GH Pages(헤더 불가)에선 불가, CSP에 의존 말 것.

### 후속 (SRI) — ✅ 완료·배포됨 (main `854bc08`)
owner가 회사망 밖으로 나와 jsdelivr 접근 가능 → `scripts/compute_sri.py`로 4개 자산 sha384 계산, 독립 CDN(unpkg/cdnjs)
교차검증으로 MITM 배제, 라이브 바이트와 9/9 일치 확인 후 `integrity=` + `crossorigin="anonymous"` 적용.
- pretendard css(4파일), echarts@5.5.0(index/IFRS17), chartjs-plugin-annotation@3.0.1(K-ICS): 그대로 + SRI.
- **chart.js: `chart.umd.min.js` → `chart.umd.js`로 URL 변경** + SRI. 사유: `.min.js`는 jsdelivr가 자동 생성한
  파일(npm에 없음)이라 교차검증 불가 → npm 정본 `chart.umd.js`(jsdelivr=unpkg 바이트 동일, immutable)로 전환.
  기능 동일(둘 다 v4.4.0 production UMD). **이 URL 되돌리지 말 것**(min.js로 돌리면 SRI 해시 불일치로 차트 차단).
- 새 CDN 자산 추가/버전 변경 시 `compute_sri.py`에 URL 추가→재실행→integrity 갱신 필수.

### 배포후 검증 (owner/designer 브라우저)
라이브 4개 페이지 devtools 콘솔에서 **CSP violation 0건 + 차트 정상 렌더** 확인. `Refused to evaluate ... unsafe-eval`
에러가 뜨면 그때만 script-src에 'unsafe-eval' 추가(chart.js@4/echarts@5는 불필요로 검증됨 — 안 떠야 정상).

## 답변 (designer, 2026-07-07)

**재확인 완료.** 4개 파일 모두 `<meta charset>` 직후(L6)에 CSP meta 유지 확인. 로컬 서버로 K-ICS.html·
IFRS17.html 로드해 devtools 콘솔 체크 — CSP violation 0건, jsdelivr CDN(pretendard 폰트·chart.umd.js·
chartjs-plugin-annotation·echarts) 전부 200 정상 로드, 차트 정상 렌더. `unsafe-eval` 관련 에러 없음 재확인.
지시사항(meta 위치 유지, chart.umd.js URL 유지, SRI 갱신 절차)은 인지 완료 — 별도 변경 없이 종결.
