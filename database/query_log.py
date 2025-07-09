from database.connection import get_connection

def create_query_log(query_type, duration_ms, sql, suggestion, language, dbms_type, project_code, user_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute('''
        INSERT INTO query_logs (query_type, duration_ms, sql, suggestion, language, dbms_type, project_code, user_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (query_type, duration_ms, sql, suggestion, language, dbms_type, project_code, user_id))
    conn.commit()
    conn.close()
    

def list_query_logs_by_user_id(user_id, limit=100):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute('''
        SELECT id, query_type, duration_ms, sql, suggestion, language, dbms_type, created_at, project_code, user_id FROM query_logs
        WHERE user_id = ?
        ORDER BY created_at DESC
        LIMIT ?
    ''', (user_id, limit))
    rows = cur.fetchall()
    conn.close()

    return [
        {
            "id": r[0],
            "query_type": r[1],
            "duration_ms": r[2],
            "sql": r[3],
            "suggestion": r[4],
            "language": r[5],
            "dbms_type": r[6],
            "created_at": r[7],
            "project_code": r[8],
            "user_id": r[9]
        }
        for r in rows
    ]