# Long-Term AI Agent (Streamlit) — 문서 인덱스

이 저장소의 **메인 진입점**은 루트의 `streamlit_app.py`입니다. 장기 실적(L&H) 분석·정합성 검증·뉴스/이슈·LLM 보고서까지 한 화면에서 전환합니다.

## 다음 세션을 위한 안내

여러 세션이 이어서 작업할 때는 가장 먼저 [변경 이력](docs/claude-changelog.md)을 확인해 직전에 무엇이 바뀌었는지 파악합니다. 문서나 앱 동작을 바꾼 뒤에는 changelog 맨 위에 항목을 추가합니다.

## 문서 구성

### 앱·인프라

- [변경 이력 (시간 역순)](docs/claude-changelog.md)
- [개요·용어·디렉터리·화면↔모듈 매핑](docs/claude-overview.md) · [최상위 폴더 규약](docs/claude-overview.md#folder-layout-convention)
- [데이터 유입 플로우 (DB 업로드·L&H 풀·뉴스)](docs/claude-download-flow.md)
- [LLM 운영 모델 (Ollama / OpenAI / Gemini)](docs/claude-gemini-flow.md)
- [챗봇 PDF RAG (DB/Reference → Chroma → 챗봇 인용)](docs/claude-rag.md)
- [분석 컨텍스트 (`ctx`)·보고서/챗봇 직렬화](docs/claude-json-build.md)
- [코드 품질·검증 가이드 (일반)](docs/claude-validation-harness.md)

### 머신러닝 분석 (설계 노트·태스크 프롬프트)

- [보험료·손해율 예측 MLOps 리서치 (Agent A~D)](docs/MLOps-research.md) — **이상적 practice 리서치**: 데이터 granularity·클러스터링(A), GLM/GBDT·평가(B), 시계열·credibility 폴백(C), 드리프트·모니터링·실험 로그(D). 앱 코드와 직접 연동되지 않는 설계 참고 노트.
- [Feature Engineering 규칙](docs/feature-engineering.md) — 상품·담보·연령·채널의 **OOV·결측·재정의 방어**(step-down granularity, 드롭 조건). 모든 모델링 태스크의 전제.
- [신계약 보험료 예측](docs/newbiz-premium-predict.md) — Count × Amount × Rate 분해 vs 직접 예측, 절판 마케팅·가격탄력성 휴리스틱.
- [보유계약 보험료 예측](docs/inforce-premium-predict.md) — 전월 대비 변동률 + offset, 담보코드 첫자리 서브모델, 갱신·면책 점프 트리거.
- [이상클레임 탐지](docs/claim-anomaly-detect.md) — Two-stage Hurdle(발생/심도), fat-tail 제약, 잔차 기반 robust outlier 탐지.

문서 간 충돌·중복은 [모델링 기본 원칙](#모델링-기본-원칙-glm-first)을 우선 적용하고, 태스크 문서 하단의 "Related Documents / 관련 문서" 섹션에서 교차참조를 따른다.

## 빠른 결론

- **실행**: 프로젝트 루트에서 `streamlit run streamlit_app.py` (의존성은 루트 `requirements.txt`).
- **데이터**: `DB/L&H Data Pool`(실적), `DB/News`(뉴스·스크래핑 결과). 사이드바에서 업로드하거나 폴더에 직접 배치.
- **화면**: `st.session_state.main_view` — `dash` · `perf_dash` · `outlier` · `premium` · `issue` · `report` (상단 3구역 6버튼).
- **상태**: `ctx`에 화면별 분석 결과, `lh_snapshot`에 기간·원수사·특약 범위. 우측 LLM Chatbot은 이 요약 + 대화 기록을 사용.
- **레거시**: 과거에 이 폴더에 있던 KICS PDF→JSON 파이프라인 설명은 본 문서 세트에서 제거되었습니다. 솔벤시 실험 코드는 `outdated/solvency` 등에 남아 있을 수 있습니다.

## 모델링 기본 원칙 (GLM-first)

신계약·보유계약 보험료 예측, 이상클레임 탐지 등 **모든 예측 모델은 GLM 베이스라인부터 빠르게 적합한 뒤, 고도화 여부를 사용자와 합의하고 진행한다.** 이 원칙은 [docs/MLOps-research.md — Agent B](docs/MLOps-research.md#agent-b-지도학습-모델-비교효율평가-프레임워크)의 모델 비교 프레임과 함께 읽는다.

1. **1차 — GLM 베이스라인으로 빠른 가설 검증.**
   - 작업 성격에 맞는 지수족·링크를 선택한다(빈도: Poisson + log-exposure offset, 심도: Gamma/Lognormal, 퓨어프리미엄: Tweedie 등).
   - 목적은 정밀 튜닝이 아니라 **데이터·피처·라벨 정의가 가설과 합치하는지 sanity check**.
   - 산출물: 베이스라인 deviance·캘리브레이션·주요 셀별 Lift를 [실험 로그 템플릿](docs/MLOps-research.md#3-documentation--experiment-log-템플릿)에 기록.

2. **2차 — 고도화는 사용자 동의 후에만.**
   - GLM이 "가설이 어느 정도 맞다"고 판단되고 추가 개선 여지(강한 비선형·교호)가 있을 때, XGBoost / LightGBM / Random Forest(Bagging) 등으로 확장한다.
   - 전환 전에 사용자에게 **현재 GLM 성능, 한계, 대안의 비용·해석·감사 트레이드오프**를 보고하고 명시적 동의를 받는다.
   - 평가는 항상 베이스라인 GLM과 **동일한 데이터 분할·동일한 복합 지표**(deviance + Lift/Gini + 버킷 캘리브레이션)로 비교한다.

3. **3차 — GLM이 안 맞으면 모델을 키우기 전에 "어디서 막혔는지" 보고한다.**
   - 막힘의 형태를 구체적으로 설명한다: 특정 셀의 잔차 편향, deviance 발산, 캘리브레이션 붕괴 구간, 시간 홀드아웃에서의 성능 급락 등.
   - 가능한 원인을 후보로 제시한다: 피처 누수·정의 불일치, 노출 분모 변동, 라벨 시점 어긋남, 구조 변화, 희소 셀 등([Agent A 누수 목록](docs/MLOps-research.md#2-예측용-피처와-비지도-세그먼트), [Agent C 노출 분모 함정](docs/MLOps-research.md#1-time-series) 참고).
   - 사용자가 **(a) 진단·데이터 수정, (b) 피처/라벨 재정의, (c) 더 큰 모델 시도** 중 어디로 갈지 결정하도록 한다.

## 적용 원칙

1. UI·데이터 계약(경로, `ctx` 키, 필터 의미)을 먼저 확인한 뒤 코드를 수정한다.
2. 큰 변경은 [docs/claude-changelog.md](docs/claude-changelog.md)에 기록한다.
3. 자동 통합 하네스는 루트에 없으므로, 배포 전에는 [docs/claude-validation-harness.md](docs/claude-validation-harness.md)의 수동·도구 검증을 참고한다.
4. 단일 `streamlit_app.py`로 인한 병합 충돌·향후 화면 분리 로드맵은 [docs/claude-overview.md — 단일 엔트리 UI와 협업](docs/claude-overview.md#single-file-ui-collab)을 참고한다.
5. 루트 폴더를 늘리거나 정리할 때는 [docs/claude-overview.md — 최상위 폴더 규약](docs/claude-overview.md#folder-layout-convention)을 따른다.
6. 모델링 태스크(신계약·보유계약·이상클레임)는 [모델링 기본 원칙](#모델링-기본-원칙-glm-first)을 따른다. GLM 베이스라인 없이 곧바로 부스팅/딥러닝으로 가지 않는다.
