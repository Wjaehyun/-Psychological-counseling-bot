# 시스템 아키텍처

## RAG 시스템 구성도

![RAG Architecture](images/rag_architecture.png)

## 구성 요소

### 1. 데이터 수집 및 전처리
- **역할**: 원본 데이터를 수집하고 청킹하여 임베딩 가능한 형태로 변환
- **기술**: Python, BeautifulSoup, LangChain TextSplitter

### 2. Vector Database
- **역할**: 임베딩된 문서 청크를 저장하고 유사도 검색 수행
- **기술**: ChromaDB

### 3. Retriever
- **역할**: 사용자 질문과 유사한 문서 청크를 검색
- **기술**: LangChain Retriever

### 4. LLM
- **역할**: 검색된 컨텍스트를 기반으로 답변 생성
- **기술**: OpenAI GPT / Claude

### 5. RAG Chain
- **역할**: Retriever와 LLM을 연결하여 질의응답 파이프라인 구성
- **기술**: LangChain

### 6. UI (Streamlit)
- **역할**: 사용자 인터페이스 제공
- **기술**: Streamlit
