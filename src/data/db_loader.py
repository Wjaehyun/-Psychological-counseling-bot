"""
FileName    : db_loader.py
Auth        : 박수빈
Date        : 2026-01-05
Description : SQLite DB 공통 함수 (저장 + 조회)
Issue/Note  : counseling_data, counseling_paragraphs 테이블 조작
"""

# -------------------------------------------------------------
# Imports
# -------------------------------------------------------------

import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from config.db_config import DatabaseConfig
from src.database.database_schema import (
    CounselingData, 
    CounselingParagraph,
    User,
    ChatSession,
    ChatMessage
)

# -------------------------------------------------------------
# DB Connection
# -------------------------------------------------------------

def get_db_session() -> Session:
    """DB 세션 생성"""
    engine = create_engine(DatabaseConfig.get_sqlite_url())
    return Session(engine)


# -------------------------------------------------------------
# Counseling Data (상담 세션) 조회
# -------------------------------------------------------------

def get_all_counselings(limit: int = 100) -> List[Dict[str, Any]]:
    """
    모든 상담 데이터 조회
    
    Returns:
        [{'id': 1, 'source_id': 'D012', 'category': 'DEPRESSION', ...}, ...]
    """
    session = get_db_session()
    try:
        results = session.query(CounselingData).limit(limit).all()
        return [_counseling_to_dict(c) for c in results]
    finally:
        session.close()


def get_counseling_by_id(counseling_id: int) -> Optional[Dict[str, Any]]:
    """ID로 상담 데이터 조회"""
    session = get_db_session()
    try:
        result = session.query(CounselingData).filter_by(id=counseling_id).first()
        return _counseling_to_dict(result) if result else None
    finally:
        session.close()


def get_counseling_by_source_id(source_id: str) -> Optional[Dict[str, Any]]:
    """source_id로 상담 데이터 조회 (예: D012)"""
    session = get_db_session()
    try:
        result = session.query(CounselingData).filter_by(source_id=source_id).first()
        return _counseling_to_dict(result) if result else None
    finally:
        session.close()


def get_counselings_by_category(category: str, limit: int = 100) -> List[Dict[str, Any]]:
    """카테고리별 상담 데이터 조회"""
    session = get_db_session()
    try:
        results = session.query(CounselingData).filter_by(category=category).limit(limit).all()
        return [_counseling_to_dict(c) for c in results]
    finally:
        session.close()


def get_counseling_count() -> int:
    """상담 데이터 수 조회"""
    session = get_db_session()
    try:
        return session.query(CounselingData).count()
    finally:
        session.close()


# -------------------------------------------------------------
# Counseling Paragraphs (발화 단락) 조회
# -------------------------------------------------------------

def get_paragraphs_by_counseling(counseling_id: int) -> List[Dict[str, Any]]:
    """특정 상담의 모든 발화 조회"""
    session = get_db_session()
    try:
        results = session.query(CounselingParagraph)\
            .filter_by(counseling_id=counseling_id)\
            .order_by(CounselingParagraph.paragraph_index)\
            .all()
        return [_paragraph_to_dict(p) for p in results]
    finally:
        session.close()


def get_paragraphs_by_speaker(speaker: str, limit: int = 100) -> List[Dict[str, Any]]:
    """화자별 발화 조회"""
    session = get_db_session()
    try:
        results = session.query(CounselingParagraph)\
            .filter_by(speaker=speaker)\
            .limit(limit)\
            .all()
        return [_paragraph_to_dict(p) for p in results]
    finally:
        session.close()


def get_paragraph_count() -> int:
    """발화 단락 수 조회"""
    session = get_db_session()
    try:
        return session.query(CounselingParagraph).count()
    finally:
        session.close()


# -------------------------------------------------------------
# 통계
# -------------------------------------------------------------

def get_db_statistics() -> Dict[str, int]:
    """DB 전체 통계"""
    session = get_db_session()
    try:
        return {
            'users': session.query(User).count(),
            'chat_sessions': session.query(ChatSession).count(),
            'chat_messages': session.query(ChatMessage).count(),
            'counseling_data': session.query(CounselingData).count(),
            'counseling_paragraphs': session.query(CounselingParagraph).count()
        }
    finally:
        session.close()


# -------------------------------------------------------------
# Helper Functions
# -------------------------------------------------------------

def _counseling_to_dict(c: CounselingData) -> Dict[str, Any]:
    """CounselingData → Dict 변환"""
    return {
        'id': c.id,
        'source_id': c.source_id,
        'category': c.category,
        'severity': c.severity,
        'summary': c.summary,
        'source_file': c.source_file,
        'has_detailed_label': c.has_detailed_label,
        'created_at': str(c.created_at) if c.created_at else None
    }


def _paragraph_to_dict(p: CounselingParagraph) -> Dict[str, Any]:
    """CounselingParagraph → Dict 변환"""
    return {
        'id': p.id,
        'counseling_id': p.counseling_id,
        'paragraph_index': p.paragraph_index,
        'speaker': p.speaker,
        'content': p.content,
        'labels': p.labels
    }


# -------------------------------------------------------------
# Entry Point (테스트용)
# -------------------------------------------------------------

if __name__ == "__main__":
    print("=== SQLite DB 함수 테스트 ===\n")
    
    stats = get_db_statistics()
    print("1. DB 통계:")
    for k, v in stats.items():
        print(f"   - {k}: {v}")
    
    counselings = get_all_counselings(limit=3)
    print(f"\n2. 상담 데이터 (상위 3개):")
    for c in counselings:
        print(f"   - {c['source_id']} | {c['category']}")
