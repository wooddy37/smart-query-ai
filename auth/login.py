# 로그인 함수
import sqlite3
from database.connection import get_connection
from auth.password import check_password
from database.login_log import create_login_log

def login(user_id: str, password: str):
    """
    사용자 로그인 시도. 성공 시 사용자 dict 반환, 실패 시 None 반환
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT user_id, password_hash, is_admin FROM users WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    conn.close()

    if row:
        user_id, hashed_pw, is_admin = row
        if check_password(password, hashed_pw):
            create_login_log(user_id)  # 로그인 이력 기록
            return {
                "user_id": user_id,
                "is_admin": bool(is_admin)
            }
    return None