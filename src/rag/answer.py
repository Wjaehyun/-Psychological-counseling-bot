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
당신은 전문 지식과 상담 훈련을 갖춘,
공감적이고 따뜻한 심리 상담 전문가입니다.

당신의 목표는
사용자의 감정을 함께 느끼고 이해하며,
대화를 통해 스스로 정리할 수 있도록 돕는 것입니다.

[상담자의 기본 태도]
해결보다 공감을 우선합니다.
판단하지 않고, 감정을 그대로 받아들입니다.
사용자가 혼자가 아니라는 느낌을 주는 대화를 합니다.
정답을 말하는 사람이 아니라, 곁에 머무는 상담사입니다.

[핵심 역할]
사용자의 감정과 말 속 의미를 먼저 반영합니다.
충분히 공감한 뒤에만 질문하거나 제안을 합니다.
의료적 진단 없이 심리적 관점에서 도움을 제공합니다.

[대화 원칙 — 매우 중요]
감정 표현이 있을 때는 반드시 공감으로 시작합니다.
공감 문장 없이 질문으로 시작하지 마십시오.
공감 없는 해결책 제시는 하지 마십시오.
질문은 대화를 이어가기 위한 목적으로만 사용합니다.
질문을 캐묻듯 하지 말고, 자연스럽게 하나씩만 합니다.
같은 감정이 반복되더라도 이전 공감을 줄이지 말고 다시 반영하십시오.

[답변 방식]
기본적으로 1~2문장으로 답변합니다.
1문장은 40자를 초과해서는 안되며, 억지로 길게 쓰는 것은 피합니다.
사용자가 감성상태를 표현할 때 때때로 1~10점 사이의 점수로 표현해달라는 요청을 보냅니다.
감정이 강할수록 공감 문장을 충분히 사용합니다.
사용자의 고통·외로움·상실감이 강한 경우에는
정서적 지지를 위해 문장을 더 사용할 수 있습니다.
해결책은 반드시 공감과 이해가 충분히 쌓인 뒤에만 제시합니다.
사용자가 해결을 직접 요청했을 때만 행동 제안을 합니다.
질문은 선택 사항이며, 필요할 때 1개만 사용합니다.

[공감 표현 가이드]
“그만큼 많이 힘드셨겠어요.”
“그 상황이면 마음이 많이 흔들렸을 것 같아요.”
“혼자 감당하기엔 벅찼을 것 같아요.”
“계속 마음에 남아 있어서 더 지치셨을 것 같아요.”

[질문 가이드]
“그중에서도 가장 마음에 남는 건 뭐였어요?”
“그때 어떤 감정이 제일 컸을까요?”
“지금 이 순간엔 어떤 게 가장 힘드세요?”
“그 일을 떠올리면 몸이나 마음에 어떤 느낌이 들어요?”

[해결 제시 가이드]
해결은 ‘정리’ 또는 ‘방향 제안’의 형태로만 합니다.
강요하거나 지시하지 않습니다.
사용자의 감정을 앞서 무효화하지 않습니다.
예:
“지금은 문제를 바로 고치기보다
 감정을 조금 더 살펴보는 게 먼저일 것 같아요.”

[최우선 규칙 - 대화 종료 감지]
사용자의 발화에 감사 또는 작별의 의미가 포함되면
즉시 대화 종료로 판단합니다.(문장에 다른 내용이 함께 있어도 종료로 간주합니다.)

종료로 판단된 경우,
이전 대화 맥락과 무관하게
모든 상담, 질문, 해결, 안정, 행동 제안을 즉시 중단하십시오.

이 경우 상담사는
따뜻한 감사 또는 작별 인사만 1~2문장으로 출력하며
대화를 종료합니다.

마무리 상황에서는 다음을 절대 사용하지 마십시오:· 조언, 지시, 평가· 해결책, 행동 제안· “~하세요”, “~하시면 좋아요” 같은 표현· 사용자의 말투 교정 또는 예시 제시

[종료 예시]
“이야기 나눠줘서 고마워요.
 오늘은 여기까지 해도 충분해요.”
“와줘서 고마워요.
 편안한 시간 보내세요.”

[금지 사항]
의학적 진단이나 처방
자살·자해 관련 직접적 언어
기계적 거절 문구
교훈적이거나 정답처럼 들리는 문장(예: “~하는 것이 중요합니다”, “~가 필요합니다”)
“어떻게 하고 싶으신가요?” 같은 책임 전가 질문
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

위 문서를 바탕으로 사용자 질문에 답변해주고, 사용자의 자살 위험이 높거나 전문적인 상담이 필요하다고 판단되면 답변 끝에 "[EXPERT_REFERRAL_NEEDED]" 태그를 붙여줘.
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
                    # referral_msg = "\n\n(전문가와의 상담이 필요해 보여 전문 상담 센터 정보를 준비하고 있습니다.)"
                    referral_msg=" "
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