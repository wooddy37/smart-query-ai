import sqlite3
from typing import Dict, Optional
from database.setup_database import get_connection
from auth.password import hash_password

def get_user(user_id: int) -> Optional[Dict]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT user_id, is_admin, created_by, created_at FROM users WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    conn.close()
    if row:
        return {
            "user_id": row[0],
            "is_admin": bool(row[1]),
            "created_by": row[2],
            "created_at": row[3]
        }
    return None

def list_users(has_admin=False):
    conn = get_connection()
    cur = conn.cursor()
    if has_admin:
        cur.execute("SELECT user_id, is_admin, created_by, created_at FROM users ORDER BY created_at DESC")
    else:
        cur.execute("SELECT user_id, is_admin, created_by, created_at FROM users WHERE is_admin = 0 ORDER BY created_at DESC")
    rows = cur.fetchall()
    conn.close()
    return [{"user_id": r[0], "is_admin": bool(r[1]), "created_by": r[2], "created_at": r[3]} for r in rows]

def create_user(user_id, password, is_admin=False, created_by=None):
    password_hash = hash_password(password)
    conn = get_connection()
    cur = conn.cursor()
    cur.execute('''
        INSERT INTO users (user_id, password_hash, is_admin, created_by, updated_by)
        VALUES (?, ?, ?, ?, ?)
    ''', (user_id, password_hash, int(is_admin), created_by, created_by))
    conn.commit()
    conn.close()

def update_user(user_id, password=None, is_admin=None, updated_by=None):
    conn = get_connection()
    cur = conn.cursor()

    fields = []
    params = []

    if password is not None:
        password_hash = hash_password(password)
        fields.append("password_hash = ?")
        params.append(password_hash)

    if is_admin is not None:
        fields.append("is_admin = ?")
        params.append(int(is_admin))

    if updated_by is not None:
        fields.append("updated_by = ?")
        params.append(updated_by)

    if fields:
        fields.append("updated_at = CURRENT_TIMESTAMP")
        sql = f"UPDATE users SET {', '.join(fields)} WHERE user_id = ?"
        params.append(user_id)
        cur.execute(sql, params)
        conn.commit()

    conn.close()


def delete_user(user_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()