"""
FileName    : model.py
Auth        : 우재현
Date        : 2026-01-05
Description : 모델 생성 파일. 모델 호출 함수 제공
Issue/Note  : getenv로 env에서 model이름을 받아 정의.
"""

# -------------------------------------------------------------
# Imports
# -------------------------------------------------------------

from langchain_openai import ChatOpenAI
from pathlib import Path
from dotenv import load_dotenv

import os

# -------------------------------------------------------------
# Environment & Constants
# -------------------------------------------------------------

def _load_model_name() -> str:
    env_path= env_path = Path(__file__).resolve().parents[2] / "config" / ".env"
    load_dotenv(dotenv_path=env_path)

    model_name = os.getenv("OPENAI_CHAT_MODEL")

    if not model_name:
        raise ValueError(
            "OPENAI_CHAT_MODEL이 .env에 정의되어 있지 않습니다."
        )

    return model_name

# -------------------------------------------------------------
# Model Create Functions
# -------------------------------------------------------------

def create_model() -> ChatOpenAI:
    """
    정의된 상수 model_name으로 모델 생성.
    """
    model_name = _load_model_name()
    # print(f"모델이름: {model_name}")

    try:
        model = ChatOpenAI(model=model_name)
    except Exception as e:
        raise RuntimeError(
            f"ChatOpenAI 초기화 실패 (model={model_name})"
        ) from e

    return model
    
# -------------------------------------------------------------
# Main Functions
# -------------------------------------------------------------

def main():
    """
    메인 함수 설명
    """
    model=create_model()
    print(type(model))

# -------------------------------------------------------------
# Entry Point
# -------------------------------------------------------------

if __name__ == "__main__":
    main()