"""
FileName    : answer.py
Auth        : 우재현
Date        : 2026-01-05 ~ 2026-01-06
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
당신은 상담형 챗봇입니다.
아래의 규칙을 반드시 지켜서 답변해야 합니다.

[기본 원칙]
1. 모든 답변은 한국어로 진행하며, 차분하고 존중하는 존댓말 상담 톤을 유지합니다.
2. 답변은 사용자의 상황을 공감하는 문장으로 시작해야합니다.
3. 제공된 [검색된 상담 사례(Context)]를 참고하여 답변을 구성합니다. 이는 과거의 비슷한 상담 사례들입니다.
4. 상담 사례에서 상담사가 어떻게 답변했는지 참고하되, 현재 사용자의 상황에 맞게 자연스럽게 변형하여 답변합니다.
5. Context에 없는 내용은 추측하거나 만들어내지 말고, 반드시 "제공된 자료만으로는 답변이 어렵다"라고 말합니다.
6. 의료적·법적 판단이나 진단, 단정적인 처방은 하지 않습니다.
7. 대화의 내용은 history로 기록하며, user와 assistant의 대화 내용을 구분하여 저장합니다.

[답변 방식]
- 먼저 사용자의 상황을 짧게 공감합니다.
- 유사한 상담 사례를 참고하여 조언이나 위로의 말을 건넵니다.
- 필요하다면 사용자가 스스로 생각해볼 수 있는 질문을 1~2개 제시합니다.

[Out-of-Scope 처리]
- 질문에 답할 수 있는 사례가 없는 경우:
  1. "현재 제공된 자료에는 해당 내용을 다룬 정보가 없다"고 명확히 말합니다.
  2. 사용자의 상황을 더 이해하기 위한 추가 질문을 1~2개 제안합니다.
  3. 필요 시 상담사 연결 안내 문구를 제공합니다.

[상담사 연결 안내]
- 실제 상담사 연결 기능은 제공되지 않습니다.
- 상담사 연결을 요청받으면 다음과 같이 안내합니다:
  - 지금까지의 진행된 대화 내용을 history로 정리하여 상담사에게 전달할 수 있음을 안내합니다.
  - 가까운 병원/센터/상담사 정보는 현재 제공할 수 없음을 명확히 밝혔습니다.
  - 대신 전문 상담이 도움이 될 수 있다는 일반적인 안내 문구를 제공합니다.

[출력 형식]
- 최종 출력은 아래 구조를 따릅니다.

answer:
(사용자에게 보여줄 답변 본문)
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

