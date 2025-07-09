import sqlite3
from typing import Dict, Optional
from database.setup_database import get_connection


def get_project_by_project_code(project_code: int) -> Optional[Dict]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT project_code, project_name, created_by, created_at FROM projects WHERE project_code = ?", (project_code,))
    row = cur.fetchone()
    conn.close()
    if row:
        return {
            "project_code": row[0],
            "project_name": row[1],
            "created_by": row[2],
            "created_at": row[3]
        }
    return None

def list_projects():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT project_code, project_name, created_by, created_at FROM projects ORDER BY created_at DESC")
    rows = cur.fetchall()
    conn.close()
    return [{"project_code": r[0], "project_name": r[1], "created_by": r[2], "created_at": r[3]} for r in rows]

def create_project(project_code, project_name=None, created_by=None):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute('''
        INSERT INTO projects (project_code, project_name, created_by, updated_by)
        VALUES (?, ?, ?, ?)
    ''', (project_code, project_name, created_by, created_by))
    conn.commit()
    conn.close()

def update_project(project_code, project_name=None, updated_by=None):
    conn = get_connection()
    cur = conn.cursor()

    fields = []
    params = []

    if project_name is not None:
        fields.append("project_name = ?")
        params.append(project_name)

    if updated_by is not None:
        fields.append("updated_by = ?")
        params.append(updated_by)

    if fields:
        fields.append("updated_at = CURRENT_TIMESTAMP")
        sql = f"UPDATE projects SET {', '.join(fields)} WHERE project_code = ?"
        params.append(project_code)
        cur.execute(sql, params)
        conn.commit()
    conn.close()