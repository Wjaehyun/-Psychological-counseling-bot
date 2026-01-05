"""
FileName    : database_schema.py
Auth        : 박수빈
Date        : 2026-01-03
Description : SQLAlchemy ORM 모델 정의 - 사용자, 채팅 세션, 상담 데이터 등
Issue/Note  : SQLite 기반, JSON 필드는 SQLAlchemy의 JSON 타입 사용
"""

# -------------------------------------------------------------
# Imports
# -------------------------------------------------------------

from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    create_engine, 
    Column, 
    Integer, 
    String, 
    Text, 
    DateTime, 
    Boolean, 
    ForeignKey,
    JSON
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from sqlalchemy.engine import Engine

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config.db_config import DatabaseConfig

# -------------------------------------------------------------
# SQLAlchemy Base
# -------------------------------------------------------------

Base = declarative_base()

# -------------------------------------------------------------
# User Model
# -------------------------------------------------------------

class User(Base):
    """
    사용자 테이블
    - 익명 사용자도 지원 (username이 자동 생성될 수 있음)
    - password_hash는 선택적 (익명 사용 시 NULL)
    """
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), nullable=False, unique=True)
    password_hash = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    
    # Relationships
    chat_sessions = relationship("ChatSession", back_populates="user")
    
    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}')>"


# -------------------------------------------------------------
# Chat Session Model
# -------------------------------------------------------------

class ChatSession(Base):
    """
    채팅 세션 테이블
    - 사용자와 챗봇 간의 대화 세션을 관리
    - screening_result: 증상 선별 결과 (JSON)
    - status: active(진행중), completed(완료), referred(전문가 연결됨)
    """
    __tablename__ = "chat_sessions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)
    status = Column(String(20), default="active")  # active, completed, referred
    screening_result = Column(JSON, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="chat_sessions")
    messages = relationship("ChatMessage", back_populates="session")
    expert_referral = relationship("ExpertReferral", back_populates="session", uselist=False)
    
    def __repr__(self):
        return f"<ChatSession(id={self.id}, user_id={self.user_id}, status='{self.status}')>"


# -------------------------------------------------------------
# Chat Message Model
# -------------------------------------------------------------

class ChatMessage(Base):
    """
    채팅 메시지 테이블
    - role: user(사용자), assistant(챗봇), system(시스템 메시지)
    """
    __tablename__ = "chat_messages"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id"), nullable=False)
    role = Column(String(10), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    session = relationship("ChatSession", back_populates="messages")
    
    def __repr__(self):
        return f"<ChatMessage(id={self.id}, role='{self.role}')>"


# -------------------------------------------------------------
# Counseling Data Model (상담 원본 데이터)
# -------------------------------------------------------------

class CounselingData(Base):
    """
    상담 데이터 테이블 (세션 단위)
    - 이기종 데이터 통합을 위한 유연한 스키마
    - has_detailed_label: 상세 라벨 존재 여부 (향후 라벨 없는 데이터도 수용)
    - raw_metadata: 원본 JSON 데이터 전체 보존
    """
    __tablename__ = "counseling_data"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    source_id = Column(String(50), nullable=False, unique=True)  # 예: D012, X007
    category = Column(String(20), nullable=False)  # DEPRESSION, ANXIETY, ADDICTION, NORMAL
    severity = Column(Integer, nullable=True)  # 0-3, NULL 허용 (라벨 없는 데이터)
    summary = Column(Text, nullable=True)
    source_file = Column(String(255), nullable=True)
    data_format = Column(String(20), default="labeled")  # labeled, unlabeled
    has_detailed_label = Column(Boolean, default=True)
    raw_metadata = Column(JSON, nullable=True)  # age, gender 등 원본 메타데이터 전체
    imported_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    paragraphs = relationship("CounselingParagraph", back_populates="counseling_data")
    
    def __repr__(self):
        return f"<CounselingData(id={self.id}, source_id='{self.source_id}', category='{self.category}')>"


# -------------------------------------------------------------
# Counseling Paragraph Model (상담 단락)
# -------------------------------------------------------------

class CounselingParagraph(Base):
    """
    상담 단락 테이블
    - 상담 대화를 발화 단위로 분리하여 저장
    - RAG 검색 시 관련 발화만 추출하기 위함
    - vector_id: ChromaDB에 저장된 문서 ID와 매핑
    - labels: 40+ 심리학적 지표 라벨 (JSON, NULL 허용)
    """
    __tablename__ = "counseling_paragraphs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    counseling_id = Column(Integer, ForeignKey("counseling_data.id"), nullable=False)
    paragraph_index = Column(Integer, nullable=False)
    speaker = Column(String(10), nullable=False)  # 상담사, 내담자
    content = Column(Text, nullable=False)
    labels = Column(JSON, nullable=True)  # 심리학적 지표 라벨들
    vector_id = Column(String(100), nullable=True)  # ChromaDB 문서 ID
    
    # Relationships
    counseling_data = relationship("CounselingData", back_populates="paragraphs")
    
    def __repr__(self):
        return f"<CounselingParagraph(id={self.id}, speaker='{self.speaker}', index={self.paragraph_index})>"


# -------------------------------------------------------------
# Expert Referral Model (전문가 연결)
# -------------------------------------------------------------

class ExpertReferral(Base):
    """
    전문가 연결 테이블
    - 증상 선별 결과에 따라 전문가 연결이 필요할 때 기록
    - severity_level: mild, moderate, severe, crisis
    """
    __tablename__ = "expert_referrals"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id"), nullable=False, unique=True)
    severity_level = Column(String(20), nullable=False)  # mild, moderate, severe, crisis
    recommended_action = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    session = relationship("ChatSession", back_populates="expert_referral")
    
    def __repr__(self):
        return f"<ExpertReferral(id={self.id}, severity='{self.severity_level}')>"


# -------------------------------------------------------------
# Database Initialization
# -------------------------------------------------------------

def init_database(echo: bool = False) -> Engine:
    """
    데이터베이스 초기화 - 테이블 생성
    
    Args:
        echo: SQL 로그 출력 여부
    
    Returns:
        SQLAlchemy Engine 객체
    """
    # 디렉토리 생성
    DatabaseConfig.ensure_directories()
    
    # 엔진 생성
    engine = create_engine(DatabaseConfig.get_sqlite_url(), echo=echo)
    
    # 테이블 생성
    Base.metadata.create_all(engine)
    
    return engine


def get_session(engine: Engine):
    """
    SQLAlchemy 세션 생성
    """
    Session = sessionmaker(bind=engine)
    return Session()


# -------------------------------------------------------------
# Entry Point (테스트용)
# -------------------------------------------------------------

if __name__ == "__main__":
    print("데이터베이스 초기화 중...")
    engine = init_database(echo=True)
    print(f"데이터베이스 생성 완료: {DatabaseConfig.SQLITE_DB_PATH}")
    
    # 테스트 세션
    session = get_session(engine)
    print("세션 생성 완료")
    session.close()
