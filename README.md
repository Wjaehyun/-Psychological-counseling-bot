# RAG 기반 심리상담 챗봇 프로젝트

> **역할 중심 요약** <br>
> 본 팀 프로젝트에서 저는 **RAG & Logic 파트장**이자 **부팀장**으로서, **응답 제어 로직 결정, 모델 평가 기준 정의**를 주도했습니다.<br>
> 본 README는 **개인 포트폴리오 관점**에서 제가 수행한 역할과 기술적 판단을 중심으로 정리되어 있습니다.

---

## 📌 Project Overview

* **주제**: RAG 기반 심리상담 챗봇
* **목표**: 감정 상담 도메인에 적합한 검색·응답 구조 설계 및 안정적인 응답 품질 확보
* **핵심 관점**: *Retriever와 Model Selection을 통한 품질 통제*와 *응답 로직 설계*의 중요성 검증

---

## 👤 My Role (RAG & Logic Lead / Sub-Leader)

### 🔹 프로젝트 내 책임 범위

* RAG 전체 구조 설계 및 로직 흐름 정의
* Retriever 실험 방향 수립 및 팀원에게 실험 지시
* Retriever 성능 비교 결과를 반영한 응답 제어 로직 구현
* 모델 테스트 시 **지연시간(latency)** 측정 항목 추가 및 평가 기준 정의
* 작성한 구동 코드를 기준으로 팀 전체 테스트 프로세스 통일

---

## 🧠 Key Design Decisions

* **Retriever 실험 통제** <br>
  → 상담 도메인에서는 다양성보다 *감정 맥락의 일관성*이 더 중요하다고 판단

* **Retriever score 기반 응답 제어** <br>
  → 검색 신뢰도가 낮을 경우, LLM의 과도한 추론을 방지하기 위함

* **지연시간 우선 평가** <br>
  → 상담 서비스 특성상 응답 지연은 사용자 감정 이탈로 직결

---

## ⚙️ System Architecture

```
User Input
   ↓
Retriever (Similarity / MMR 실험)
   ↓
Score 기반 필터링 및 분기 처리
   ↓
LLM Answer Generation
   ↓
Response Output
```

* Retriever 결과의 **score**를 기준으로 응답 전략을 분기
* 검색 품질이 낮을 경우, LLM 응답 범위를 제한하거나 안전한 기본 응답 사용

---

## 🔬 Retriever Experiment Strategy

* 다양한 Retriever 기법을 단순 비교가 아닌 **응답 로직 연계를 전제로 한 실험 설계** 관점에서 접근

* Retriever 단계에서는

  * 검색 결과의 **문맥 적합성**
  * score 분포의 안정성
  * 응답 제어 로직과의 결합 가능성
    을 중심으로 정성적 비교를 수행

* Retriever 실험 결과는 **즉시 성능 지표로 판단하지 않고**,
  이후 **최종 모델 선정 단계의 평가 기준에 반영**하는 방식으로 활용

* 이러한 흐름을 통해 **Similarity Retriever**를 최종 채택

  * 상담 문맥 유지 및 score 기반 응답 제어에 가장 적합하다고 판단

---

## 🧩 Logic Implementation Focus

* `src/rag/chain.py`에서 Retriever score에 따라 응답 흐름 제어

* 검색 결과 신뢰도가 낮을 경우:

  * 무리한 추론 응답 방지
  * 감정적으로 안전한 기본 응답 출력

* 단순 RAG 연결이 아닌 **“검색 결과를 어떻게 사용할 것인가”**에 초점

---

## 📄 Counseling Report Export (PDF)

* 상담 세션 종료 후, 대화 내용을 **PDF 리포트 형태로 자동 생성**

* `src/utils/pdf_exporter.py` 모듈을 별도로 설계하여

  * 상담 로직과 출력 포맷 로직을 명확히 분리

* 상담 내용을 단순 로그가 아닌 **사용자 제공 결과물**로 확장

* 리포트 구성:

  * 상담 요약
  * 주요 감정 키워드
  * 상담 흐름 정리

→ RAG 기반 상담 시스템을 *대화형 모델*에서 *서비스 기능 단위*로 확장한 구현

---

## ▶️ Execution Entry Points

본 프로젝트는 아래 구동 코드를 기준으로 실행 및 테스트를 진행했습니다.

* `app/main.py` : Flask 기반 메인 실행 엔트리
* `src/rag/chain.py` : Retriever 결과 처리 및 응답 생성 로직
* `model_config.py` : 모델 및 환경 설정

> 팀원들은 해당 구동 코드를 기준으로 동일한 환경에서 모델 테스트를 진행하도록 지시

---

## 📊 Evaluation Strategy

* **정량 평가**

  * Retriever 응답 정확도
  * 모델 응답 지연시간 (Latency)

* **정성 평가**

  * 감정 문맥 유지 여부
  * 과도한 추론 또는 부적절한 답변 발생 여부

> 상담 챗봇 특성상 *지연시간*을 핵심 평가 요소로 설정

---

## 📌 Outcome

* RAG 시스템에서 **모델 성능보다 로직 설계가 더 중요할 수 있음**을 체감
* Retriever 실험 결과를 실제 응답 로직에 반영하는 경험 확보
* 팀 프로젝트에서 *설계 및 기술 의사결정 역할*을 수행한 경험을 명확히 정리

---

## 🧭 Positioning Summary

이 프로젝트를 통해 저는 다음과 같은 역할 경험을 갖추었습니다.

* RAG 시스템 구현 및 설계자
* 실험 결과를 코드 레벨 의사결정으로 연결하는 역할
* 팀 내 기술 판단 및 방향성을 제시하는 포지션
