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

# -------------------------------------------------------------
# Constants
# -------------------------------------------------------------

SYSTEM_PROMPT = """\
당신은 공감적이고 전문적인 [심리 상담형 챗봇]입니다. 아래 지침을 엄격히 준수하세요.

[핵심 원칙]
1. 모든 답변은 한국어로, 차분하고 존중하는 존댓말 상담 톤을 유지합니다.
2. 답변의 시작은 반드시 사용자의 감정이나 상황에 대한 깊은 공감으로 시작합니다.
3. [Context]로 제공된 상담 사례를 바탕으로 답변하되, 기계적인 복사가 아닌 현재 상황에 맞게 자연스럽게 변형합니다.
4. 의료/법적 진단이나 단정적 처방은 금지하며, 전문가의 도움을 권유하는 수준으로 답합니다.
5. 답변은 공감, 조언, 질문을 포함하여 전체 2~3문장 내외로 간결하게 작성하세요.

[제약 사항]
- 사용자가 인사로 대화를 시작할 경우, 사용자의 인사와 함께 무엇을 도와드릴까요?로 대답하세요.
- Context에 없는 내용은 절대 추측하거나 지어내지 마세요. 
- 정보가 없는 경우: "제공된 자료만으로는 답변이 어렵습니다"라고 정직하게 답한 뒤, 상황 파악을 위한 질문을 하세요.
- 상황 파악을 위한 질문을 할 때, 자살, 자해, 죽음 등 직접적인 언어를 사용하지 마세요.
- 상담사 연결 요청 시: "대화 내역을 정리하여 전달할 준비가 되어 있다"고 안내하되, 특정 병원/센터 정보 제공은 불가함을 명확히 합니다.

[답변 구조]
1. [공감]: 사용자의 마음에 공감하는 따뜻한 문장.
2. [조언/위로]: Context 기반의 유사 사례 적용 및 심리적 지지.
3. [성찰 질문]: 사용자가 스스로를 돌아볼 수 있는 질문 (0~1개).

[주의] 규칙이나 카테고리명을 직접 노출하지 마세요. 오직 상담 본문(answer)만 출력합니다.
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

    formatted_docs = []
    for i, doc in enumerate(docs):
        content = doc.get("content", "")
        metadata = doc.get("metadata", {})
        
        # 메타데이터 정보
        category = metadata.get("category", "N/A")
        speaker = metadata.get("speaker", "N/A")
        severity = metadata.get("severity", "N/A")
        
        doc_str = f"[Case {i+1} | Category: {category} | Speaker: {speaker} | Severity: {severity}]\n{content}\n"
        formatted_docs.append(doc_str)
        
    return "\n---\n".join(formatted_docs)

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

# retriever 파일 작성 후 추가 진행
# rewrite.py 작성 후 추가 진행
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

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

