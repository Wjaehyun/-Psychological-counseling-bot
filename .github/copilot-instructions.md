<!-- .github/copilot-instructions.md -->
# AI 개발 에이전트를 위한 빠른 안내

이 파일은 이 리포지토리에서 AI 코딩 에이전트(예: Copilot/자동화 에이전트)가 빠르게 생산적으로 작업할 수 있도록 핵심 정보만 요약합니다.

요점 요약
- 엔트리포인트 UI: `app/main.py` (Streamlit 기반 테스트/데모)
- 벡터 DB(Chroma): `vector_store/` (실제 DB 파일: `vector_store/chroma.sqlite3`)
- Vector wrapper: `src/database/vector_store.py` (주요 API: `add_documents`, `search`, `get_document_count`)
- Retriever: `src/rag/retriever.py` (factory 패턴 — `load_vector_db()` + `create_retriever()`)
- LLM 생성: `src/llm/model.py` (`create_model()` — `config/.env`의 `OPENAI_CHAT_MODEL` 사용)
- 데이터 파이프라인: `src/data/data_loader.py`, `src/data/vector_loader.py` (전처리 → DB 저장 흐름)

아키텍처(한 문장)
- 원본 데이터가 `data/raw/`에서 전처리되어 `src/data/*`로 파싱되고, 전처리된 단락들은 `src/database/vector_store.py`를 통해 ChromaDB에 임베딩 저장된다. `src/rag`의 Retriever가 저장된 벡터를 검색하고, `src/llm/model.py`로 생성한 LLM이 검색 결과를 활용해 응답을 생성한다.

핵심 통합 포인트 및 패턴
- VectorStore: `src/database/vector_store.py`는 Chroma PersistentClient를 사용하고 컬렉션을 직접 관리합니다. 메타데이터 필터 키는 `category`, `speaker`, `severity`입니다.
- Retriever: `create_retriever()`는 `VectorStore` 인스턴스를 받아 호출 가능한 `retriever(query, ...)`를 반환합니다. 사용 예시는 `src/rag/retriever.py`의 `main()`과 debug 함수 참고.
- LLM: `create_model()`은 `config/.env`에서 `OPENAI_CHAT_MODEL`을 읽어 `langchain_openai.ChatOpenAI` 인스턴스를 생성합니다. 에이전트는 환경변수 파일 경로(`config/.env`)를 보수적으로 관리해야 합니다.
- DB/FS 경로: `DatabaseConfig`가 Chroma 저장 경로와 컬렉션 이름을 정의합니다 (`config/db_config.py` 참조). 파일 시스템 경로가 코드에서 하드코딩되어 있거나 `ensure_directories()`를 호출하므로 루트에서 스크립트를 실행하는 것을 권장합니다.
- 임시 sys.path 삽입: 일부 모듈(`src/database/vector_store.py` 등)은 `sys.path.insert(0, ...)` 방식으로 상위 폴더를 추가합니다. 에이전트는 패키지 상대 경로를 깨뜨리지 않도록 루트에서 실행하거나 `python -m` 스타일 실행을 권장합니다.

실행 및 디버깅(빠른 명령)
- 의존성 설치: `pip install -r requirements.txt` (가상환경 권장)
- 환경: 반드시 `config/.env`에 `OPENAI_CHAT_MODEL`을 설정
- 로컬 UI 실행(데모):
```
streamlit run app/main.py
```
- Retriever/VectorStore 간단 테스트:
```
python -c "from src.rag.retriever import load_vector_db, create_retriever; vs=load_vector_db(); r=create_retriever(vs); print(r('요즘 우울해요')[:1])"
```

코드 작성 규칙 / 발견된 관습
- 모듈은 `if __name__ == '__main__'`으로 간단한 수동 테스트를 제공합니다. 에이전트는 단일 파일 변경 시 관련 테스트 블록도 업데이트하세요.
- 데이터 저장흐름은 `src/data/vector_loader.py`를 통해 `DatabaseManager`(DB 레이어)와 `VectorStore`를 함께 호출합니다. 변경 시 두 레이어 모두 고려해야 합니다.
- 메타데이터 필터 사용: 검색 시 `where` 인자에 `category`, `speaker`, `severity`를 사용합니다 (예: severity는 0~3 범위).

안전/운영 주의사항
- `config/.env`에 민감한 키가 들어갑니다. 에이전트가 예시 값이나 비밀 키를 커밋하지 않도록 주의하세요.
- ChromaDB 경로(persist)와 컬렉션 이름은 `config/db_config.py`에서 관리됩니다. 로컬 테스트는 `vector_store/`를 재사용하므로 기존 DB를 덮어쓸 위험이 있습니다.

작업 예시(간단한 변경 시나리오)
- 새로운 검색 필터 추가: 1) `src/database/vector_store.py`의 `search()` 쿼 파라미터 확장, 2) `src/rag/retriever.py`에서 `where` 구성 업데이트, 3) 관련 단위 테스트(없으면 간단 스크립트) 추가.

참고 파일
- 엔트리/데모: `app/main.py`
- 벡터 저장/검색: `src/database/vector_store.py`, `vector_store/` 디렉터리
- Retriever: `src/rag/retriever.py`
- LLM 생성: `src/llm/model.py` (읽는 env: `config/.env`)
- 데이터 로드/저장: `src/data/data_loader.py`, `src/data/vector_loader.py`

피드백
- 이 파일을 검토하시고, 빠진 세부 정보(예: CI 명령, 테스트 커맨드, 팀 규칙)가 있으면 알려주세요. 수정해 반영하겠습니다.
