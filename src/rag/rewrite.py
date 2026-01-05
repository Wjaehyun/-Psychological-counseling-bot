"""
FileName    : rewrite.py
Auth        : 작성자
Date        : 2026-01-05
Description : 파일 설명
Issue/Note  : 비고
"""

# -------------------------------------------------------------
# Imports
# -------------------------------------------------------------

from typing import List, Dict, Optional
import re

try:
    # 같은 폴더/실행 위치에서 import 되는 것을 가정
    from model import create_model
except Exception:
    create_model = None

# -------------------------------------------------------------
# Constants
# -------------------------------------------------------------

SYSTEM_PROMPT = """\
너는 RAG 챗봇의 Query Rewriter다.
목표: 사용자의 마지막 발화를, 대화 히스토리를 반영한 "검색용 단일 문장 쿼리"로 재작성한다.

규칙:
1) 출력은 오직 한 줄의 한국어 쿼리만.
2) 지시어(그거/아까/저번/그럼 등)는 히스토리로 구체화.
3) 불필요한 감탄/중복/군더더기 제거.
4) 질문 의도가 바뀌지 않게 한다.
5) 사실/정보를 새로 만들어내지 않는다.
"""

DEFAULT_MAX_TURNS = 6

# 상수 정의

# -------------------------------------------------------------
# Main Functions
# -------------------------------------------------------------

def rewrite_query(
    history: List[Dict[str, str]],
    last_user: str,
    model=None,
) -> str:
    """
    대화 히스토리를 반영하여 검색용 Query로 재작성한다.

    Args:
        history: [{"role": "user"/"assistant", "content": "..."}...]
        last_user: 사용자의 마지막 발화
        model: 외부에서 주입 가능한 LangChain ChatOpenAI (None이면 create_model()로 생성)

    Returns:
        rewritten query (한 줄)
    """
    # 1) model 준비
    if model is None and create_model is not None:
        try:
            model = create_model()
        except Exception:
            model = None

    # 2) 모델 없으면 fallback
    if model is None:
        return rule_based_fallback(last_user)

    # 3) LLM rewrite
    hist_text = format_history(history)

    user_prompt = f"""\
[대화 히스토리]
{hist_text}

[사용자 마지막 발화]
{last_user}

위 규칙에 따라 "검색용 단일 문장 쿼리"로 재작성해라.
"""

    res = model.invoke(
        [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ]
    )

    text = getattr(res, "content", str(res)).strip()

    # 안전장치: 여러 줄이면 첫 줄만 사용
    text = text.splitlines()[0].strip()

    # 따옴표 제거 등 최소 정리
    text = text.strip('"\'')

    return text


def main():
    """
    메인 함수 설명
    - standalone 디버그 실행용: rewrite_query가 정상 동작하는지 확인
    """
    sample_history = [
        {"role": "user", "content": "요즘 불안해서 잠이 안 와요."},
        {"role": "assistant", "content": "불안이 심할 때는 호흡과 수면 루틴을 점검해볼 수 있어요."},
    ]
    sample_last_user = "그럼 이거 우울증이랑 관련 있어?"

    rewritten = rewrite_query(sample_history, sample_last_user)
    print("[DEBUG] last_user :", sample_last_user)
    print("[DEBUG] rewritten :", rewritten)

# -------------------------------------------------------------
# Entry Point
# -------------------------------------------------------------

if __name__ == "__main__":
    main()