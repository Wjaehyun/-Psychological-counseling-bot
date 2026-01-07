"""
FileName    : main.py
Auth        : 박수빈
Date        : 2026-01-05
Description : Flask Application - 심리 상담 AI Chatbot
              회원가입/로그인 시스템 구현 (Bcrypt 암호화, 세션 기반 인증)
Issue/Note  : 주소 데이터는 RAG 챗봇 상담 시 활용 가능
"""

# -------------------------------------------------------------
# Imports
# -------------------------------------------------------------

from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from datetime import datetime
import bcrypt
import sqlite3
import os
<<<<<<< HEAD
from pathlib import Path

=======
import sys
from pathlib import Path

# RAG 시스템 임포트를 위한 경로 설정
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# RAG 시스템 모듈 임포트
try:
    from src.rag.chain import RAGChain
    from src.database.db_manager import DatabaseManager
    RAG_AVAILABLE = True
except ImportError as e:
    print(f"[Warning] RAG 시스템 로드 실패: {e}")
    RAG_AVAILABLE = False

>>>>>>> 9c39686aa3c4ad77a6cab5476e9547e5f8f8af8d
# -------------------------------------------------------------
# Flask App Configuration
# -------------------------------------------------------------

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-in-production'  # 실제 배포 시 환경변수로 관리

# 세션 설정
app.config['SESSION_TYPE'] = 'filesystem'
app.config['PERMANENT_SESSION_LIFETIME'] = 86400  # 24시간

# -------------------------------------------------------------
# Database Configuration
# -------------------------------------------------------------

# 데이터베이스 경로
PROJECT_ROOT = Path(__file__).parent.parent
DB_PATH = PROJECT_ROOT / "data" / "mind_care.db"


def get_db_connection():
    """
    SQLite 데이터베이스 연결 생성
    
    Returns:
        sqlite3.Connection: 데이터베이스 연결 객체
    """
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row  # 딕셔너리 형태로 결과 반환
    return conn


def init_database():
    """
    데이터베이스 테이블 초기화
    users 테이블이 없으면 생성
    """
    # data 디렉토리 생성
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # ---------------------------------------------------------
    # users 테이블 생성 (없으면)
    # ---------------------------------------------------------
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            name TEXT,
            gender TEXT,
            birthdate TEXT,
            phone TEXT,
            address TEXT,
            address_detail TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            last_login TEXT
        )
    ''')
    
    conn.commit()
    conn.close()
    print(f"데이터베이스 초기화 완료: {DB_PATH}")


# 앱 시작 시 데이터베이스 초기화
init_database()

<<<<<<< HEAD
=======
# RAG 시스템 초기화
rag_chain = None
db_manager = None

if RAG_AVAILABLE:
    try:
        db_manager = DatabaseManager(echo=False)
        rag_chain = RAGChain(db_manager=db_manager)
        print("[INFO] RAG 시스템 초기화 완료")
    except Exception as e:
        print(f"[Warning] RAG 시스템 초기화 실패: {e}")
        rag_chain = None
else:
    print("[Warning] RAG 모듈을 사용할 수 없습니다. 데모 모드로 실행합니다.")

>>>>>>> 9c39686aa3c4ad77a6cab5476e9547e5f8f8af8d

# =============================================================
# Page Routes
# =============================================================

def login_required(f):
    """
    로그인 필수 데코레이터
    세션에 사용자 정보가 없으면 로그인 페이지로 리다이렉트
    """
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


@app.route('/')
def root():
    """루트 페이지 - 로그인 페이지로 리다이렉트"""
    if 'user' in session:
        return redirect(url_for('index'))
    return redirect(url_for('login'))


@app.route('/index')
@login_required
def index():
    """메인 채팅 페이지 (로그인 필수)"""
    # 세션에서 사용자 정보 전달
    user_data = session.get('user', {})
    return render_template('index.html', user=user_data)


@app.route('/login')
def login():
    """로그인 페이지"""
    # 이미 로그인된 경우 메인 페이지로
    if 'user' in session:
        return redirect(url_for('index'))
    return render_template('login.html')


@app.route('/signup')
def signup():
    """회원가입 페이지"""
    return render_template('signup.html')


@app.route('/mypage')
@login_required
def mypage():
    """마이페이지 (로그인 필수)"""
    return render_template('mypage.html')


@app.route('/survey')
@login_required
def survey():
    """심리 상태 검사 페이지"""
    return render_template('survey.html')


# =============================================================
# Authentication API Routes
# =============================================================

@app.route('/api/check-username', methods=['POST'])
def api_check_username():
    """
    아이디 중복 확인 API
    
    Request Body:
        - username: 확인할 아이디
    
    Returns:
        - available: 사용 가능 여부 (True/False)
        - message: 결과 메시지
    """
    data = request.get_json()
    username = data.get('username', '').strip()
    
    # ---------------------------------------------------------
    # 유효성 검사
    # ---------------------------------------------------------
    if not username:
        return jsonify({
            'success': False,
            'available': False,
            'message': '아이디를 입력해주세요'
        }), 400
    
    if len(username) < 4:
        return jsonify({
            'success': False,
            'available': False,
            'message': '아이디는 4자 이상이어야 합니다'
        }), 400
    
    # ---------------------------------------------------------
    # 데이터베이스에서 중복 확인
    # ---------------------------------------------------------
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
    existing_user = cursor.fetchone()
    conn.close()
    
    if existing_user:
        return jsonify({
            'success': True,
            'available': False,
            'message': '이미 사용 중인 아이디입니다'
        })
    else:
        return jsonify({
            'success': True,
            'available': True,
            'message': '사용 가능한 아이디입니다'
        })


@app.route('/api/signup', methods=['POST'])
def api_signup():
    """
    회원가입 API
    
    Request Body:
        - username: 아이디
        - password: 비밀번호
        - name: 이름
        - gender: 성별 (male/female)
        - birthdate: 생년월일 (YYYY-MM-DD)
        - phone: 전화번호
        - address: 기본 주소
        - address_detail: 상세 주소
    
    Returns:
        - success: 성공 여부
        - message: 결과 메시지
        - redirect: 리다이렉트 URL
    """
    data = request.get_json()
    
    # ---------------------------------------------------------
    # 필수 필드 추출
    # ---------------------------------------------------------
    username = data.get('username', '').strip()
    password = data.get('password', '')
    name = data.get('name', '').strip()
    gender = data.get('gender', '')
    birthdate = data.get('birthdate', '')
    phone = data.get('phone', '').strip()
    address = data.get('address', '').strip()
    address_detail = data.get('address_detail', '').strip()
    
    # ---------------------------------------------------------
    # 유효성 검사
    # ---------------------------------------------------------
    if not all([username, password, name]):
        return jsonify({
            'success': False,
            'message': '아이디, 비밀번호, 이름은 필수입니다'
        }), 400
    
    if len(username) < 4:
        return jsonify({
            'success': False,
            'message': '아이디는 4자 이상이어야 합니다'
        }), 400
    
    if len(password) < 8:
        return jsonify({
            'success': False,
            'message': '비밀번호는 8자 이상이어야 합니다'
        }), 400
    
    # ---------------------------------------------------------
    # 데이터베이스에 저장
    # ---------------------------------------------------------
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # 아이디 중복 확인
        cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
        if cursor.fetchone():
            conn.close()
            return jsonify({
                'success': False,
                'message': '이미 사용 중인 아이디입니다'
            }), 400
        
        # Bcrypt로 비밀번호 해싱
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        # 새 사용자 생성
        cursor.execute('''
            INSERT INTO users (username, password_hash, name, gender, birthdate, phone, address, address_detail, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (username, password_hash.decode('utf-8'), name, gender, birthdate, phone, address, address_detail, datetime.utcnow().isoformat()))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': '회원가입이 완료되었습니다',
            'redirect': url_for('login')
        })
        
    except Exception as e:
        conn.close()
        return jsonify({
            'success': False,
            'message': f'회원가입 중 오류가 발생했습니다: {str(e)}'
        }), 500


@app.route('/api/login', methods=['POST'])
def api_login():
    """
    로그인 API
    
    Request Body:
        - username: 아이디
        - password: 비밀번호
    
    Returns:
        - success: 성공 여부
        - message: 결과 메시지
        - redirect: 리다이렉트 URL
        - user: 사용자 정보 (성공 시)
    """
    data = request.get_json()
    username = data.get('username', '').strip()
    password = data.get('password', '')
    
    # ---------------------------------------------------------
    # 유효성 검사
    # ---------------------------------------------------------
    if not username or not password:
        return jsonify({
            'success': False,
            'message': '아이디와 비밀번호를 입력해주세요'
        }), 400
    
    # ---------------------------------------------------------
    # 데이터베이스에서 사용자 조회
    # ---------------------------------------------------------
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
    user = cursor.fetchone()
    
    if not user:
        conn.close()
        return jsonify({
            'success': False,
            'message': '존재하지 않는 아이디입니다'
        }), 401
    
    # ---------------------------------------------------------
    # Bcrypt 비밀번호 검증
    # ---------------------------------------------------------
    if not bcrypt.checkpw(password.encode('utf-8'), user['password_hash'].encode('utf-8')):
        conn.close()
        return jsonify({
            'success': False,
            'message': '비밀번호가 일치하지 않습니다'
        }), 401
    
    # ---------------------------------------------------------
    # 로그인 성공 - 세션에 사용자 정보 저장
    # ---------------------------------------------------------
    cursor.execute('UPDATE users SET last_login = ? WHERE id = ?', 
                   (datetime.utcnow().isoformat(), user['id']))
    conn.commit()
    conn.close()
    
    # Flask 세션에 사용자 정보 저장 (SessionData)
    session['user'] = {
        'id': user['id'],
        'username': user['username'],
        'name': user['name'],
        'gender': user['gender'],
        'birthdate': user['birthdate'],
        'phone': user['phone'],
        'address': user['address'],
        'address_detail': user['address_detail']
    }
    session.permanent = True
    
    return jsonify({
        'success': True,
        'message': '로그인 성공',
        'redirect': url_for('index'),
        'user': session['user']
    })


@app.route('/api/logout', methods=['POST'])
def api_logout():
    """
    로그아웃 API
    
    Returns:
        - success: 성공 여부
        - message: 결과 메시지
        - redirect: 리다이렉트 URL
    """
    # 세션에서 사용자 정보 제거
    session.pop('user', None)
    
    return jsonify({
        'success': True,
        'message': '로그아웃 되었습니다',
        'redirect': url_for('login')
    })


@app.route('/api/session', methods=['GET'])
def api_session():
    """
    현재 세션 정보 조회 API
    
    Returns:
        - logged_in: 로그인 상태
        - user: 사용자 정보 (로그인 시)
    """
    if 'user' in session:
        return jsonify({
            'logged_in': True,
            'user': session['user']
        })
    else:
        return jsonify({
            'logged_in': False,
            'user': None
        })


# =============================================================
<<<<<<< HEAD
=======
# Recent Chats API
# =============================================================

@app.route('/api/recent-chats', methods=['GET'])
def api_recent_chats():
    """
    사용자의 최근 채팅 세션 목록 조회 API
    
    Returns:
        - success: 성공 여부
        - chats: 최근 채팅 세션 목록 [{id, title, date, started_at}, ...]
    """
    # 로그인 확인
    if 'user' not in session:
        return jsonify({
            'success': False,
            'chats': [],
            'message': '로그인이 필요합니다'
        }), 401
    
    # RAG 시스템 사용 가능 여부 확인
    if db_manager is None:
        return jsonify({
            'success': True,
            'chats': [],
            'message': 'RAG 시스템이 초기화되지 않았습니다'
        })
    
    try:
        user_info = session['user']
        
        # RAG DB에서 사용자 조회
        db_user = db_manager.get_user_by_username(user_info['username'])
        
        if db_user is None:
            return jsonify({
                'success': True,
                'chats': [],
                'message': '채팅 기록이 없습니다'
            })
        
        # 최근 채팅 세션 조회
        recent_chats = db_manager.get_user_recent_sessions(db_user.id, limit=5)
        
        return jsonify({
            'success': True,
            'chats': recent_chats
        })
        
    except Exception as e:
        print(f"[Error] 최근 채팅 조회 중 오류: {e}")
        return jsonify({
            'success': False,
            'chats': [],
            'message': f'조회 중 오류가 발생했습니다: {str(e)}'
        }), 500


@app.route('/api/new-session', methods=['POST'])
def api_new_session():
    """
    새 채팅 세션 시작 API
    현재 세션을 초기화하고 새 세션을 시작할 준비를 함
    
    Returns:
        - success: 성공 여부
        - message: 결과 메시지
    """
    # 로그인 확인
    if 'user' not in session:
        return jsonify({
            'success': False,
            'message': '로그인이 필요합니다'
        }), 401
    
    try:
        # Flask 세션에서 현재 채팅 세션 ID 제거
        session.pop('chat_session_id', None)
        
        return jsonify({
            'success': True,
            'message': '새 대화가 시작되었습니다'
        })
        
    except Exception as e:
        print(f"[Error] 새 세션 생성 중 오류: {e}")
        return jsonify({
            'success': False,
            'message': f'새 세션 생성 중 오류가 발생했습니다: {str(e)}'
        }), 500


@app.route('/api/delete-session/<int:session_id>', methods=['DELETE'])
def api_delete_session(session_id):
    """
    채팅 세션 삭제 API
    
    Args:
        session_id: 삭제할 세션 ID
        
    Returns:
        - success: 성공 여부
        - message: 결과 메시지
    """
    # 로그인 확인
    if 'user' not in session:
        return jsonify({
            'success': False,
            'message': '로그인이 필요합니다'
        }), 401
    
    if db_manager is None:
        return jsonify({
            'success': False,
            'message': 'RAG 시스템이 초기화되지 않았습니다'
        })
    
    try:
        user_info = session['user']
        db_user = db_manager.get_user_by_username(user_info['username'])
        
        if db_user is None:
            return jsonify({
                'success': False,
                'message': '사용자를 찾을 수 없습니다'
            }), 404
        
        # 세션 조회 및 소유권 확인
        chat_session = db_manager.get_chat_session(session_id)
        
        if chat_session is None or chat_session.user_id != db_user.id:
            return jsonify({
                'success': False,
                'message': '채팅 세션을 찾을 수 없습니다'
            }), 404
        
        # 세션 삭제 (메시지도 함께 삭제됨 - cascade)
        db_manager.delete_chat_session(session_id)
        
        # 현재 활성 세션이 삭제되었다면 세션 초기화
        if session.get('chat_session_id') == session_id:
            session.pop('chat_session_id', None)
        
        return jsonify({
            'success': True,
            'message': '대화가 삭제되었습니다'
        })
        
    except Exception as e:
        print(f"[Error] 세션 삭제 중 오류: {e}")
        return jsonify({
            'success': False,
            'message': f'삭제 중 오류가 발생했습니다: {str(e)}'
        }), 500


@app.route('/api/chat-history/<int:session_id>', methods=['GET'])
def api_chat_history(session_id):
    """
    특정 채팅 세션의 대화 기록 조회 API
    
    Args:
        session_id: 채팅 세션 ID
        
    Returns:
        - success: 성공 여부
        - messages: 메시지 목록 [{role, content, created_at}, ...]
    """
    # 로그인 확인
    if 'user' not in session:
        return jsonify({
            'success': False,
            'messages': [],
            'message': '로그인이 필요합니다'
        }), 401
    
    if db_manager is None:
        return jsonify({
            'success': False,
            'messages': [],
            'message': 'RAG 시스템이 초기화되지 않았습니다'
        })
    
    try:
        user_info = session['user']
        db_user = db_manager.get_user_by_username(user_info['username'])
        
        if db_user is None:
            return jsonify({
                'success': False,
                'messages': [],
                'message': '사용자를 찾을 수 없습니다'
            }), 404
        
        # 세션 조회 및 소유권 확인
        chat_session = db_manager.get_chat_session(session_id)
        
        if chat_session is None or chat_session.user_id != db_user.id:
            return jsonify({
                'success': False,
                'messages': [],
                'message': '채팅 세션을 찾을 수 없습니다'
            }), 404
        
        # 채팅 기록 조회
        messages = db_manager.get_chat_history(session_id)
        
        messages_data = [{
            'role': msg.role,
            'content': msg.content,
            'created_at': msg.created_at.isoformat() if msg.created_at else None
        } for msg in messages]
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'messages': messages_data
        })
        
    except Exception as e:
        print(f"[Error] 채팅 기록 조회 중 오류: {e}")
        return jsonify({
            'success': False,
            'messages': [],
            'message': f'조회 중 오류가 발생했습니다: {str(e)}'
        }), 500


@app.route('/api/switch-session', methods=['POST'])
def api_switch_session():
    """
    활성 채팅 세션 전환 API
    
    Request Body:
        - session_id: 전환할 세션 ID
        
    Returns:
        - success: 성공 여부
        - session_id: 전환된 세션 ID
    """
    # 로그인 확인
    if 'user' not in session:
        return jsonify({
            'success': False,
            'message': '로그인이 필요합니다'
        }), 401
    
    data = request.get_json()
    new_session_id = data.get('session_id')
    
    if not new_session_id:
        return jsonify({
            'success': False,
            'message': '세션 ID가 필요합니다'
        }), 400
    
    if db_manager is None:
        return jsonify({
            'success': False,
            'message': 'RAG 시스템이 초기화되지 않았습니다'
        })
    
    try:
        user_info = session['user']
        db_user = db_manager.get_user_by_username(user_info['username'])
        
        if db_user is None:
            return jsonify({
                'success': False,
                'message': '사용자를 찾을 수 없습니다'
            }), 404
        
        # 세션 조회 및 소유권 확인
        chat_session = db_manager.get_chat_session(new_session_id)
        
        if chat_session is None or chat_session.user_id != db_user.id:
            return jsonify({
                'success': False,
                'message': '채팅 세션을 찾을 수 없습니다'
            }), 404
        
        # Flask 세션에 chat_session_id 업데이트
        session['chat_session_id'] = new_session_id
        
        return jsonify({
            'success': True,
            'session_id': new_session_id,
            'message': '세션이 전환되었습니다'
        })
        
    except Exception as e:
        print(f"[Error] 세션 전환 중 오류: {e}")
        return jsonify({
            'success': False,
            'message': f'세션 전환 중 오류가 발생했습니다: {str(e)}'
        }), 500


# =============================================================
>>>>>>> 9c39686aa3c4ad77a6cab5476e9547e5f8f8af8d
# Chat & Survey API Routes
# =============================================================

@app.route('/api/chat', methods=['POST'])
def api_chat():
    """채팅 API - RAG 시스템 연동"""
<<<<<<< HEAD
    data = request.get_json()
    message = data.get('message')
    
    # TODO: RAG 시스템 연동
    # response = rag_system.generate_response(message)
    
    # Demo response
    response = "안녕하세요! 심리 상담 AI입니다. 무엇을 도와드릴까요?"
    
    return jsonify({
        'success': True,
        'response': response
    })
=======
    # 로그인 확인
    if 'user' not in session:
        return jsonify({
            'success': False,
            'message': '로그인이 필요합니다'
        }), 401
    
    data = request.get_json()
    message = data.get('message', '').strip()
    
    if not message:
        return jsonify({
            'success': False,
            'message': '메시지를 입력해주세요'
        }), 400
    
    user_info = session['user']
    user_id = user_info.get('id')
    
    # RAG 시스템 사용 가능 여부 확인
    if rag_chain is None:
        # 데모 모드 응답
        return jsonify({
            'success': True,
            'response': "안녕하세요! 심리 상담 AI입니다. 현재 데모 모드로 실행 중입니다. RAG 시스템이 준비되면 더 나은 상담을 받으실 수 있습니다.",
            'demo_mode': True
        })
    
    try:
        # 세션 ID 관리 (Flask 세션에 chat_session_id 저장)
        chat_session_id = session.get('chat_session_id')
        
        if chat_session_id is None:
            # 새 채팅 세션 생성
            # DatabaseManager의 user와 Flask session의 user 동기화
            db_user = db_manager.get_user_by_username(user_info['username'])
            if db_user is None:
                # RAG DB에 사용자가 없으면 생성
                db_user = db_manager.create_user(user_info['username'])
            
            # 새 채팅 세션 생성
            chat_session = db_manager.create_chat_session(db_user.id)
            chat_session_id = chat_session.id
            session['chat_session_id'] = chat_session_id
            user_id = db_user.id
        else:
            # 기존 세션 사용
            db_user = db_manager.get_user_by_username(user_info['username'])
            if db_user:
                user_id = db_user.id
        
        # RAG 시스템으로 응답 생성
        response = rag_chain.run(user_id, chat_session_id, message)
        
        return jsonify({
            'success': True,
            'response': response,
            'session_id': chat_session_id
        })
        
    except Exception as e:
        print(f"[Error] 채팅 처리 중 오류: {e}")
        return jsonify({
            'success': False,
            'message': '죄송합니다. 응답 생성 중 오류가 발생했습니다.',
            'error': str(e)
        }), 500
>>>>>>> 9c39686aa3c4ad77a6cab5476e9547e5f8f8af8d


@app.route('/api/survey', methods=['POST'])
def api_survey():
    """설문 결과 저장 API"""
    data = request.get_json()
    answers = data.get('answers')
    
    # TODO: 설문 결과 저장 로직
    return jsonify({
        'success': True,
        'message': '설문이 저장되었습니다'
    })


# =============================================================
# Run Application
# =============================================================

if __name__ == '__main__':
    app.run(debug=True, port=5000)
