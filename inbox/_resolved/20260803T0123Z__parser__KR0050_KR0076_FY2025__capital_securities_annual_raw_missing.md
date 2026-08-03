---
from: parser
to: downloader
created: 20260803T0123Z
status: resolved
route: refetch
company: KR0050 (하나손해보험), KR0076 (아이엠라이프생명보험)
period: FY2025 (사업보고서, annual)
iter: 1
---

## 미결 (parser/ifrs17) — KR0050/KR0076 FY2025 사업보고서 raw 부재 (capital-securities 추출 불가)

연계: `inbox/parser/20260803T0055Z__owner__MULTI_2026.1Q__forward_capital_rebase_fsc_to_dart.md`
(owner 발주 — `kics_forward_capital.json`의 발행채권 소스를 FSC data.go.kr → DART per-bond로 교체).

### 배경

교체 자체는 완료(`scripts/forward_capital_simulation.py`가 이제 `data/bonds/capital_securities_fy2025.json`
(DART per-bond, 24사)을 읽음). 그런데 그 발주의 요청 ②가 요구한 커버리지 갭 2사를 못 메꿨다:

- **DART 미수록(FSC엔 있음)**: `KR0050` 하나손해보험, `KR0076` 아이엠라이프생명보험
- 교체 전(FSC 기준) 대비 교체 후 2030년 지급여력비율 영향 확인함 — 채권 상환에 따른 미래 자본감소가
  더는 반영되지 않아 **두 회사 모두 비율이 실제보다 낙관적으로 뜬다**:
  - KR0050 하나손해보험: 124.47% → 146.09% (2030, bond_coverage: fsc_listed → no_bonds_in_dart)
  - KR0076 아이엠라이프생명보험: 93.65% → 152.12% (2030, bond_coverage: fsc_listed → no_bonds_in_dart)

### raw 확인 결과 — 🔴 두 회사 모두 FY2025 annual raw가 디스크에 없음

`data/dart/FY2025_Q4/raw/`, `FY2024_Q4/raw/` 어디에도 KR0050/KR0076 dir 없음. 유일하게 존재하는 건
`data/dart/FY2026_Q1/raw/KR0050_하나손해보험/meta.json` / `.../KR0076_아이엠라이프생명보험/meta.json`인데
둘 다 내용이 `{"period": "2026.1Q", "no_filing": true}` — **2026.1Q 분기보고서가 없다는 스텁일 뿐**,
FY2025 연간 사업보고서 raw가 아님(애초에 무관한 분기).

CSM_waterfall.json엔 이 두 회사의 2024.4Q/2025.4Q 행이 이미 있음(과거 세션이 raw 보유 시 추출) —
즉 raw가 [[project_git_purge]]로 이후 소실된 것으로 보이고, 현재 디스크엔 남아있지 않음.

### 요청

1. KR0050(하나손해보험)/KR0076(아이엠라이프생명보험) **FY2025 사업보고서**(annual, 회계연도 2025 결산)
   raw 재취득 — canonical layout `data/dart/FY2025_Q4/raw/KR00XX_<회사명>_<rcept>/`.
2. 관심 섹션: "증권의 발행을 통한 자금조달에 관한 사항" / 사채발행내역 / 미상환잔액 주석
   (신종자본증권·후순위채 발행현황) — 본문 XML에 있으면 별첨 fetch 불필요(DART no attachment fetch 원칙).
   없으면(공시 자체 무발행) 그것도 결론 — parser가 무발행 확인 처리.
3. 참고로 두 회사 모두 CSM waterfall/PL breakdown은 이미 온보딩되어 있어 IFRS17 보험계약 주석 쪽 raw는
   과거 확보된 적이 있음(현재 디스크엔 없음, 마스터에만 값 남음) — 같은 filing에서 capital-securities
   주석도 같이 받아오면 됨(중복 fetch 아님, 이번이 사실상 최초 capital-securities 목적 fetch).

### 완료 조건 (parser 재실행 verify)

raw 도착 후 parser가:
1. per-bond 추출 → `data/bonds/capital_securities_fy2025.json`의 `companies` 리스트에 KR0050/KR0076 추가
   (무발행 확인이면 `bonds: []`로 명시 추가, 완전 누락 유지 아님).
2. `python scripts/forward_capital_simulation.py` 재실행 → 두 회사 `bond_coverage: dart_listed`로 전환.
3. `python scripts/validate_data_contract.py` → RED=0 유지 확인.

## 답변 (downloader 작성 — 2026-08-03, raw-ready)

둘 다 비상장 → 사업보고서(A유형) 0건, **감사보고서(F유형)만 존재** — 별도(연결 아님) 감사보고서 fetch:

- `data/dart/FY2025_Q4/raw/KR0050_하나손해보험_20260325000538/` (한영회계법인) — "신종자본증권" 15회 검출
- `data/dart/FY2025_Q4/raw/KR0076_아이엠라이프생명보험_20260406004393/` (삼일회계법인) — "신종자본증권" 14회 검출

`extract_dart_zips.py`로 언집 완료(`<rcept>_00760.xml`). "미상환잔액"/"후순위" 정확매칭은 0회지만
신종자본증권 언급은 확인됨 — 실제 발행현황 주석 라벨이 다를 수 있으니 파서가 직접 열어서 확인 요망.
`inbox/parser/20260803T0130Z`에 raw-ready 알림 별도 발송(이 티켓 회신만으론 다음 세션 inbox 드레인에
안 걸림).
