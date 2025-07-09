from database.setup_database import get_connection

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
        SELECT QL.id, QL.query_type, QL.duration_ms, QL.sql, QL.suggestion, QL.language, QL.dbms_type, QL.created_at, QL.project_code, P.project_name, QL.user_id 
        FROM query_logs QL INNER JOIN projects P ON QL.project_code = p.project_code
        WHERE user_id = ?
        ORDER BY QL.created_at DESC
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
            "project_name": r[9],
            "user_id": r[10]
        }
        for r in rows
    ]