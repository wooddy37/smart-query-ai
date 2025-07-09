import sqlite3
from database.setup_database import get_connection

def assign_user_to_project(user_id, project_code, created_by=None):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute('''
            INSERT INTO user_projects (user_id, project_code, created_by)
            VALUES (?, ?, ?)
        ''', (user_id, project_code, created_by))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        # 이미 매핑되어 있으면 무시하거나 False 반환
        return False
    finally:
        conn.close()

def remove_user_from_project(user_id, project_code):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute('''
        DELETE FROM user_projects
        WHERE user_id = ? AND project_code = ?
    ''', (user_id, project_code))
    conn.commit()
    conn.close()

def list_user_projects(user_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute('''
        SELECT p.project_code, p.project_name
        FROM projects p
        JOIN user_projects up ON p.project_code = up.project_code
        WHERE up.user_id = ?
    ''', (user_id,))
    rows = cur.fetchall()
    conn.close()
    return [{"project_code": r[0], "project_name": r[1]} for r in rows]