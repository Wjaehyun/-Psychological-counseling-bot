"""
FileName    : chain.py
Auth        : 우재현
Date        : 2026-01-06
Description : RAG 전체 파이프라인 관리
Issue/Note  : DB 연결, Rewrite, Retrieve, Answer 모든 단계 통합
"""

# -------------------------------------------------------------
# Imports
# -------------------------------------------------------------

import sys
from pathlib import Path
from typing import Dict, List, Optional, Any

# Root 경로 설정
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from operator import itemgetter
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from config.model_config import create_chat_model
from src.database.db_manager import DatabaseManager
from src.database.vector_store import VectorStore
from src.rag.retriever import create_retriever, load_vector_db
from src.rag.rewrite import create_rewrite_chain, format_history
from src.rag.answer import create_answer_chain, format_sources

# -------------------------------------------------------------
# RAG Main Class
# -------------------------------------------------------------

class RAGChain:
    """
    RAG 시스템의 전체 흐름을 제어하는 클래스 (LCEL 기반 전체 파이프라인 구성)
    """
    
    def __init__(self, db_manager: DatabaseManager = None):
        """
        초기화 및 체인 구성
        """
        # 1. DB Manager
        self.db = db_manager if db_manager else DatabaseManager()
        
        # 2. Vector DB 로드
        self.vector_db = load_vector_db()
        
        # 3. 모델 및 컴포넌트 초기화
        self.model = create_chat_model()
        retriever_func = create_retriever(self.vector_db)
        
        # 4. 서브 체인 정의
        rewrite_chain = create_rewrite_chain(self.model)
        answer_chain = create_answer_chain(self.model)
        
        # ---------------------------------------------------------
        # RAG 전체 파이프라인 구성 (Compose Full RAG Pipeline)
        # Input: {"query": str, "history_text": str}
        # ---------------------------------------------------------
        
        # 1. 질문 재작성 (Rewrite)
        # Input: {query, history_text} -> Output: rewritten_query (str)
        rewrite_step = RunnablePassthrough.assign(
            rewritten_query=lambda x: rewrite_chain.invoke({
                "history": x["history_text"], 
                "query": x["query"]
            }).strip().strip('"\'').splitlines()[0]
        )
        
        # 2. 문서 검색 (Retrieve)
        # Input: {..., rewritten_query} -> Output: context (문서 내용)
        retrieve_step = RunnablePassthrough.assign(
            context=lambda x: format_sources(retriever_func(query=x["rewritten_query"]))
        )
        
        # 3. 답변 생성 (Answer)
        # Input: {..., context, history_text, rewritten_query} -> Output: answer (최종 답변)
        answer_step = RunnablePassthrough.assign(
            answer=lambda x: answer_chain.invoke({
                "context": x["context"],
                "history": x["history_text"],
                "query": x["rewritten_query"] 
            })
        )
        
        # Pipeline Chain
        self.rag_pipeline = rewrite_step | retrieve_step | answer_step

    def run(self, user_id: int, session_id: int, query: str) -> str:
        """
        사용자 발화에 대한 RAG 응답 생성 및 처리 전체 과정
        """
        print(f"\n[Flow Start] User: {user_id}, Session: {session_id}")
        
        # 1. 사용자 메시지 저장 (부수 효과)
        self.db.add_chat_message(session_id, "user", query)
        
        # 2. 대화 히스토리 로드
        history_objs = self.db.get_chat_history(session_id)
        history_dicts = [{"role": msg.role, "content": msg.content} for msg in history_objs]
        pre_history = history_dicts[:-1] # 방금 추가한 메시지 제외
        history_text = format_history(pre_history)
        
        print(f"[DB Info] 세션(ID: {session_id})의 히스토리 {len(pre_history)}개를 로드했습니다.")
        print(f"[Step] RAG 파이프라인 실행 중... Input: {query}")
        
        # 3. 체인 실행 (Invoke)
        try:
            result = self.rag_pipeline.invoke({
                "query": query,
                "history_text": history_text
            })
            
            answer = result["answer"].strip()
            rewritten = result["rewritten_query"]
            print(f"[Step] Rewritten: {rewritten}")
            
            # 4. 전문가 연결 감지 (후처리)
            if "[EXPERT_REFERRAL_NEEDED]" in answer:
                answer = answer.replace("[EXPERT_REFERRAL_NEEDED]", "").strip()
                self._handle_expert_referral(session_id, answer)
                if "상담" not in answer:
                    answer += "\n\n(전문가와의 상담이 필요해 보여 전문 상담 센터 정보를 준비하고 있습니다.)"
            
            # 5. Assistant 메시지 저장 (부수 효과)
            self.db.add_chat_message(session_id, "assistant", answer)
            
            print(f"[Flow End] 답변 생성 완료")
            return answer
            
        except Exception as e:
            print(f"[Error] RAG 파이프라인 실패: {e}")
            return "죄송합니다. 처리 중 오류가 발생했습니다."

    def _handle_expert_referral(self, session_id: int, answer: str):
        """전문가 연결 DB 기록"""
        try:
            self.db.create_expert_referral(
                session_id=session_id,
                severity_level="high",
                recommended_action="전문 상담사 연결 권장"
            )
        except Exception as e:
            print(f"[Error] 전문가 연결 로깅 실패: {e}")

# -------------------------------------------------------------
# Entry Point
# -------------------------------------------------------------
if __name__ == "__main__":
    # Test Setup
    print("=== RAG Chain Test (LCEL) ===")
    
    # 임시 DB Manager (테스트용)
    test_db = DatabaseManager(echo=False)
    rag_chain = RAGChain(db_manager=test_db)
    
    # 1. User/Session Create
    try:
        user = test_db.create_user("test_lcel_user_01")
    except Exception:
        user = test_db.get_user_by_username("test_lcel_user_01")
        
    session = test_db.create_chat_session(user.id)
    
    # 2. Run Flow
    q1 = "사는게 재미가 없어"
    ans1 = rag_chain.run(user.id, session.id, q1)
    print(f"\n[Bot]: {ans1}\n")

