# X1-S4: ReAct Agent + LangChain + LangSmith

> **[v1.6.15]** KOREATECH 제조AI 실무 교육과정 — X1-S4 (4시간)

## 학습 목표

- ReAct 패턴 이해: Thought → Action → Observation 루프
- LangChain Tool 설계 및 연동 (품질조회, 이상알림)
- LangSmith 모니터링 대시보드 설정
- 제조 현장 Agent 시나리오 실습

## 실습 구성

| 순서 | 실습 | 소요 시간 |
|:----:|------|:---------:|
| 1 | ReAct 개념 + 기본 Agent 구현 | 1.5h |
| 2 | 제조 Tool 설계 | 1.5h |
| 3 | LangSmith 모니터링 연동 | 1h |

## 연계 세션

- 선수: [X1-S3: RAG 구축](https://github.com/manufacturing-ai-koreatechac/x1-s3-rag-streamlit)
- 후속: [X1-S5: 파일럿설계서](https://github.com/manufacturing-ai-koreatechac/x1-s5-pilot-design)

## 관련 공개 데이터셋

| # | 데이터셋 | 설명 | 형태 | 링크 |
|:-:|---------|------|:----:|------|
| 1 | **KAMP 스마트제조 IoT 센서 데이터** | 한국 제조 현장 PLC·센서 실시간 데이터 20종+. ReAct Agent Tool의 `query_quality_data()` 실제 연동 대상. JSON/CSV 형태로 API 제공. | JSON/CSV | [KAMP](https://www.kamp-ai.kr/front/dataset/AiDataList.jsp) |
| 2 | **NASA Prognostics Data Repository** | NASA Ames에서 제공하는 예지보전 다종 데이터셋. Track A 신호(anomaly/rul)의 실제 데이터 기반. Agent Tool 테스트 시나리오 설계에 활용. | CSV | [NASA](https://www.nasa.gov/intelligent-systems-division/discovery-and-systems-health/pcoe/pcoe-data-set-repository/) |
| 3 | **LangSmith Public Traces Dataset** | LangChain 공식 제공 Agent 실행 트레이스 예시. ReAct 루프 디버깅 및 LangSmith 모니터링 실습 참고자료. 실행 로그 분석 패턴 학습. | JSON | [LangSmith](https://smith.langchain.com/) |

---
*KOREATECH 제조AI 실무 교육과정 v1.6.15 | 2026-03-04*
