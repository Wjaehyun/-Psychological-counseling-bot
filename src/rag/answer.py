"""
FileName    : answer.py
Auth        : 우재현
Date        : 2026-01-05 ~ 2026-01-07
Description : RAG 시스템의 답변 생성, 대화내용 저장 모듈
Issue/Note  : docs/DATABASE_DESIGN.md를 참고, src/database/db_manager.py 내용을 반영하여서 함수를 제작.
"""

# -------------------------------------------------------------
# Imports
# -------------------------------------------------------------

import os
import sys

from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from typing import List, Dict, Optional, Any

from src.database.vector_store import VectorStore
from src.database import db_manager
from config.model_config import create_chat_model
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# -------------------------------------------------------------
# Constants
# -------------------------------------------------------------

SYSTEM_PROMPT = """\
당신은 공감적이고 따뜻한 심리 상담 전문가입니다.

[핵심 역할]
- 사용자의 감정과 고민에 진심으로 공감합니다.
- 경청하고 위로하며, 필요시 간단한 조언을 제공합니다.
- 의료적 진단 없이 심리적 지지와 정서적 안정을 돕습니다.

[답변 방식]
1. 반드시 공감으로 시작: "그런 마음이 드시는군요", "많이 힘드셨겠어요" 등
2. Context에 참고할 상담 대화가 있으면 활용하세요.
3. Context가 비어있거나 관련 없어도, 직접 따뜻한 상담사로서 답변하세요.
4. 1~2문장으로 간결하게 작성합니다.
5. 상황을 더 이해하기 위한 열린 질문을 1개 추가할 수 있습니다.

[금지 사항]
- 의학적 진단이나 처방 금지
- 자살/자해 관련 직접적 언어 사용 금지
- "제공된 자료만으로는 답변이 어렵습니다" 같은 기계적 거절 금지

[인사 응답]
사용자가 인사하면: "안녕하세요! 오늘 어떤 이야기를 나누고 싶으신가요?"
"""

# -------------------------------------------------------------
# answer helper functions
# -------------------------------------------------------------

def format_sources(docs: List[Dict]) -> str:
    """
    검색된 문서 리스트를 프롬프트에 입력하기 좋은 문자열 형태로 변환
    
    Args:
        docs: 검색된 문서 정보 리스트 (content, metadata 등 포함)
    
    Returns:
        Formatted context string
    """
    if not docs:
        return "검색된 관련 문서가 없습니다."
    
    # 실제 content가 있는 문서만 필터링
    valid_docs = [doc for doc in docs if doc.get("content", "").strip()]
    
    if not valid_docs:
        return "검색된 관련 문서가 없습니다."

    formatted_docs = []
    for i, doc in enumerate(valid_docs):
        content = doc.get("content", "").strip()
        
        # 메타데이터에서 사용 가능한 정보 추출 (실제 VectorDB 키 사용)
        metadata = doc.get("metadata", {})
        session_id = metadata.get("session_id", "")
        category = metadata.get("default_category") or metadata.get("category", "")
        
        # 간결한 포맷: 핵심 내용만 전달
        if category:
            doc_str = f"[상담사례 {i+1} - {category}]\n{content}"
        else:
            doc_str = f"[상담사례 {i+1}]\n{content}"
        formatted_docs.append(doc_str)
        
    return "\n\n---\n\n".join(formatted_docs)

def format_history(history: List[Dict]) -> str:
    """
    대화 히스토리를 문자열로 변환한다.
    """
    if not history:
        return ""
    
    formatted = []
    for msg in history:
        role = msg.get("role", "unknown")
        content = msg.get("content", "")
        # role 표시: user -> 사용자, assistant -> 상담사 (프롬프트 톤앤매너에 맞춤)
        display_role = "사용자" if role == "user" else "상담사"
        formatted.append(f"{display_role}: {content}")
        
    return "\n".join(formatted)


# -------------------------------------------------------------
# LCEL Chain Factory
# -------------------------------------------------------------

def create_answer_chain(model):
    """
    LCEL 방식의 Answer Chain 생성
    Chain: Prompt | Model | StrOutputParser
    """
    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("user", """\
[검색된 문서(Context)]
{context}

[이전 대화(History)]
{history}

[사용자 질문]
{query}

위 문서를 바탕으로 사용자 질문에 답변해주고, 만약 사용자의 자살 위험이 높거나 전문적인 상담이 필요하다고 판단되면 답변 끝에 "[EXPERT_REFERRAL_NEEDED]" 태그를 붙여줘.
""")
    ])
    
    chain = prompt | model | StrOutputParser()
    return chain

# -------------------------------------------------------------
# Main Generate Function (Legacy Wrapper)
# -------------------------------------------------------------

def generate_answer(
    docs: List[Dict],
    query: str,
    history: Optional[List[Dict]] = None,
    session_id: Optional[int] = None,
    db: Optional[Any] = None,
    model=None
) -> str:
    """
    정해진 프롬프트를 따라서 사용자의 질문에 대한 답변을 생성합니다.
    (LCEL create_answer_chain을 내부적으로 사용하는 래퍼 함수)
    """
    # 1) model 준비
    if model is None:
        try:
            model = create_chat_model()
        except Exception:
            return "[Error] 모델을 초기화할 수 없습니다. (model_config.py 확인 필요)"

    # 2) Context 구성
    context_text = format_sources(docs)
    
    # 3) History 구성
    history_text = format_history(history) if history else "없음"

    # 4) LCEL 실행
    try:
        chain = create_answer_chain(model)
        answer = chain.invoke({
            "context": context_text,
            "history": history_text,
            "query": query
        })
        answer = answer.strip()
        
        # 6) 전문가 연결 트리거 확인
        if "[EXPERT_REFERRAL_NEEDED]" in answer:
            # 태그 제거
            answer = answer.replace("[EXPERT_REFERRAL_NEEDED]", "").strip()
            
            # DB에 기록
            if db and session_id:
                try:
                    db.create_expert_referral(
                        session_id=session_id,
                        severity_level="high", # LLM 판단 기반이므로 일단 high로 설정하거나 별도 로직 필요
                        recommended_action="전문 상담사 연결 권장"
                    )
                    # 안내 멘트 추가 (이미 답변에 포함되어 있을 수 있으나 확실히 하기 위해)
                    referral_msg = "\n\n(전문가와의 상담이 필요해 보여 전문 상담 센터 정보를 준비하고 있습니다.)"
                    if "상담" not in answer:
                         answer += referral_msg
                except Exception as e:
                    print(f"[Error] Expert referral logging failed: {e}")

        return answer
        
    except Exception as e:
        return f"[Error] 답변 생성 중 오류가 발생했습니다: {str(e)}"

# -------------------------------------------------------------
# Entry Point
# -------------------------------------------------------------

if __name__ == "__main__":
    # 테스트 실행
    print("=== RAG Answer Generation Test ===")
    
    # Mock Docs Test
    mock_docs = [
        {"content": "우울증은 전문가의 도움을 받으면 호전될 수 있습니다.", "metadata": {"category": "DEPRESSION", "speaker": "상담사", "severity": 2}},
        {"content": "규칙적인 운동과 수면이 정신 건강에 도움이 됩니다.", "metadata": {"category": "NORMAL", "speaker": "상담사", "severity": 0}}
    ]
    query = "우울할 때 어떻게 해야 해?"
    
    print("\n[Input Query]", query)
    
    # generate_answer 함수 직접 테스트 (모델이 설정되어 있다고 가정)
    try:
        model = create_chat_model()
        chain = create_answer_chain(model)
        
        ctx = format_sources(mock_docs)
        response = chain.invoke({"context": ctx, "history": "없음", "query": query})
        
        print("\n[Generated Response (LCEL)]")
        print(response)
        
    except Exception as e:
        print(f"[Error] {e}")