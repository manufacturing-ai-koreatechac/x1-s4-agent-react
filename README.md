# X1-S4: ReAct Agent + LangChain + LangSmith

> **[v1.6.15]** 제조 AI 실무 교육과정 — X1 S4 (4시간)

## 학습 목표

- ReAct 패턴 이해 (Thought→Action→Observation)
- LangChain Tool 설계 및 연동
- LangSmith 모니터링 대시보드 설정
- 제조 현장 Agent 시나리오 실습

## 실습 구성

| 순서 | 실습 | 소요 시간 |
|:----:|------|:---------:|
| 1 | ReAct 개념 + 간단한 Agent 구현 | 1.5h |
| 2 | 제조 Tool 설계 (품질조회/이상알림) | 1.5h |
| 3 | LangSmith 모니터링 연동 | 1h |

## 시작하기

```bash
pip install langchain langsmith openai
export LANGCHAIN_TRACING_V2=true
export LANGCHAIN_API_KEY=<your-key>
jupyter lab
```

## 연계 세션

- 선수: [X1-S3: RAG 구축](https://github.com/manufacturing-ai-koreatechac/x1-s3-rag-streamlit)
- 후속: [X1-S5: 파일럿설계서](https://github.com/manufacturing-ai-koreatechac/x1-s5-pilot-design)

---
*KOREATECH 제조AI 실무 교육과정 v1.6.15 | 2026-03-04*
