"""
FileName    : answer_results.py
Auth        : 손현우
Date        : 2026-01-05
Description : 파일 설명
Issue/Note  : 비고
"""

# -------------------------------------------------------------
# Imports
# -------------------------------------------------------------

import os
import sys

from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
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
- 사용자의 감정과 고민에 진심으로 공감하며 경청합니다.
- 위로와 지지를 제공하고, 필요시 구체적이고 실천 가능한 조언을 제공합니다.
- 의료적 진단 없이 심리적 지지와 정서적 안정을 돕습니다.

[답변 원칙]
1. **공감과 수용으로 시작**: 
    - 예시: "그동안 마음 고생이 크셨겠어요", "들어보니 정말 쉽지 않으셨겠어요", "충분히 그런 마음이 드실 수 있어요"
    - 매번 같은 문구를 반복하지 말고, 의미는 유지하되 표현을 조금씩 바꿔주세요.
    - 사용자의 감정을 먼저 인정하고 받아들여주세요.

2. **맥락 기반 답변**:
   - Context에 유사한 상담 사례가 있으면 자연스럽게 참고하세요.
   - 과거 대화(History)가 있으면 연결성 있게 답변하세요.
   - Context가 없어도 상담사로서 직접 답변하세요.

3. **구체성과 실용성**:
   - 막연한 위로보다는 구체적인 제안을 포함하세요.
   - 예: "호흡 조절", "일기 쓰기", "산책", "작은 목표 세우기" 등
   - 단, 강요하지 말고 "~해보는 건 어떨까요?" 형태로 제안하세요.

4. **적절한 길이**:
   - 2~4문장으로 작성합니다.
   - 너무 짧으면 건성, 너무 길면 부담스러움.

5. **열린 질문 포함** (선택적):
   - 대화를 이어가기 위한 자연스러운 질문을 1개 추가할 수 있습니다.
   - 예: "어떤 순간에 특히 그런 감정이 드시나요?", "평소 스트레스를 어떻게 푸시나요?"

6. **반복·유사 주제 대응**:
    - 이전에 드린 조언을 그대로 반복하지 마세요.
    - "전에 말씀드린 것처럼"으로 짧게 짚고, **새로운 작은 팁 1~2개**를 추가하세요.
    - 예: 수면: 호흡·기상시간 언급 후 이번에는 침실 환경(조도/온도)이나 가벼운 스트레칭, 이미지 리허설 등 다른 소항목 제안.
    - 같은 주제라도 표현을 살짝 바꿔 부드럽게 변주하세요.

7. **조언 템포(경청 우선)**:
    - 사용자가 "일단 내 얘기 들어줘"처럼 요청하면, **바로 조언하지 말고** 1~2개의 부드러운 확인/탐색 질문을 먼저 던지세요.
    - 이후 **짧은 요약·확인 → 간단한 조언 1~2개** 순서로 진행하세요.
    - 사용자가 "구체적 조언"을 명시적으로 요구할 때만 조금 더 디테일한 조언을 추가하세요.
    - 전체 톤은 "당신 이야기를 듣고 있다"는 느낌을 주도록, 조언보다 경청과 안전감 강조.

[상황별 대응]
- **인사** ("안녕", "안녕하세요", "처음이에요", "hi", "hello" 등): 
  따뜻하고 환영하는 톤으로 먼저 인사하고, 안전한 공간임을 느끼게 해주세요.
  예: "안녕하세요! 만나서 반가워요. 여기는 당신의 이야기를 충분히 들을 수 있는 편안한 공간이에요. 
  최근에 마음이 무거운 일이 있으신가요, 아니면 누군가와 이야기하고 싶으신 게 있으신가요? 편하게 나눠주세요."
  
- **위기 신호** (자살/자해 언급): 
  공감하되 전문가 도움 권유, 답변 끝에 [EXPERT_REFERRAL_NEEDED] 태그
  
- **반복 질문**: 
  "이전에 말씀하셨던 [내용]과 관련이 있으신가요?" 로 연결
  
- **감사 인사**: 
  "함께 이야기 나눌 수 있어서 감사해요. 당신의 용기에 응원합니다. 언제든 다시 찾아주세요."

[금지 사항]
- 의학적 진단, 약물 처방, 질병명 단정 금지
- 자살/자해 관련 직접적 언어나 구체적 방법 언급 금지
- "제공된 자료만으로는 답변이 어렵습니다" 같은 회피성 답변 금지
- 지나치게 기계적이거나 정형화된 답변 금지

[톤앤매너]
- 존댓말 사용, 따뜻하고 부드러운 어조
- 판단하지 않고 있는 그대로 받아들이는 태도
- 과도한 긍정보다는 현실적 공감과 지지
- 첫 만남의 어색함을 자연스럽게 풀어주기

**중요**: 사용자가 "안녕", "안녕하세요" 같은 간단한 인사만 했다면, Context나 History를 무시하고 위 [상황별 대응 - 인사]의 예시처럼 자연스럽게 환영하고 안전감을 주면서 대화를 시작하세요.
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
    # 대화형 테스트
    print("=== RAG Answer Generation Test ===")
    print("'exit' 입력 시 종료\n")
    
    # Mock Docs (기본 예시)
    mock_docs = [
        {"content": "우울증은 전문가의 도움을 받으면 호전될 수 있습니다.", "metadata": {"category": "DEPRESSION", "speaker": "상담사", "severity": 2}},
        {"content": "규칙적인 운동과 수면이 정신 건강에 도움이 됩니다.", "metadata": {"category": "NORMAL", "speaker": "상담사", "severity": 0}}
    ]
    
    # 대화 히스토리
    history = []
    
    try:
        model = create_chat_model()
        chain = create_answer_chain(model)
        
        while True:
            # 사용자 입력
            query = input("\n[당신] ").strip()
            
            if query.lower() in ["exit", "종료", "quit"]:
                print("테스트를 종료합니다.")
                break
            
            if not query:
                continue
            
            # Context 구성
            ctx = format_sources(mock_docs)
            hist = format_history(history)
            
            # 답변 생성
            response = chain.invoke({
                "context": ctx,
                "history": hist if hist else "없음",
                "query": query
            })
            
            print(f"\n[상담사] {response}")
            
            # 히스토리 저장
            history.append({"role": "user", "content": query})
            history.append({"role": "assistant", "content": response})
            
    except KeyboardInterrupt:
        print("\n\n테스트를 종료합니다.")
    except Exception as e:
        print(f"[Error] {e}")