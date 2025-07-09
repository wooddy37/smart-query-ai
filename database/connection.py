# DB 초기화 및 관리자 생성
import sqlite3
from auth.password import hash_password
import os

DB_PATH = os.getenv("DB_PATH", "query_logs.db")

def get_connection():
    return sqlite3.connect(DB_PATH)

def init_db():
    conn = get_connection()
    cur = conn.cursor()
    # users 테이블: 사용자 (일반/관리자 구분 포함)
    # projects 테이블: 프로젝트 코드 및 이름 관리
    # user_projects 테이블: 사용자 ↔ 프로젝트 다대다 매핑
    # login_logs 테이블: 로그인 이력 관리
    # query_logs 테이블: 쿼리 분석 로그 
    cur.executescript('''
        PRAGMA foreign_keys = ON;
                      
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY NOT NULL,
            password_hash TEXT NOT NULL,
            is_admin BOOLEAN DEFAULT 0,
            created_by TEXT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_by TEXT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (created_by) REFERENCES users(user_id),
            FOREIGN KEY (updated_by) REFERENCES users(user_id)
        );

        CREATE TABLE IF NOT EXISTS projects (
            project_code TEXT PRIMARY KEY NOT NULL,
            project_name TEXT,
            created_by TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_by TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (created_by) REFERENCES users(user_id),
            FOREIGN KEY (updated_by) REFERENCES users(user_id)
        );

        CREATE TABLE IF NOT EXISTS user_projects (
            user_id TEXT,
            project_code TEXT,
            created_by INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (user_id, project_code),
            FOREIGN KEY (user_id) REFERENCES users(user_id),
            FOREIGN KEY (project_code) REFERENCES projects(project_code),
            FOREIGN KEY (created_by) REFERENCES users(user_id)
        );

        CREATE TABLE IF NOT EXISTS login_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            login_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            ip_address TEXT,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        );

        CREATE TABLE IF NOT EXISTS query_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            project_code TEXT,
            query_type TEXT,
            duration_ms REAL,
            sql TEXT,
            suggestion TEXT,
            language TEXT,
            dbms_type TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id),
            FOREIGN KEY (project_code) REFERENCES projects(project_code)
        );
    ''')

    # 최초 관리자 계정 자동 생성
    cur.execute("SELECT COUNT(*) FROM users WHERE is_admin = 1")
    if cur.fetchone()[0] == 0:
        admin_id = "admin"
        admin_password = "new1234!"
        admin_hash = hash_password(admin_password)
        cur.execute('''
            INSERT INTO users (user_id, password_hash, is_admin, created_by, updated_by)
            VALUES (?, ?, ?, ?, ?)
        ''', (admin_id, admin_hash, True, None, None))
        print(f"[INFO] 관리자 계정이 생성되었습니다: ID: {admin_id} / PW: {admin_password}")

    conn.commit()
    conn.close()