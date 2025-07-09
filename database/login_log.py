import sqlite3
from database.connection import get_connection

def create_login_log(user_id, ip_address=None):
    """
    로그인 이력 기록, ip_address는 선택적
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute('''
        INSERT INTO login_logs (user_id, login_time, ip_address)
        VALUES (?, CURRENT_TIMESTAMP, ?)
    ''', (user_id, ip_address))
    conn.commit()
    conn.close()

    
def list_login_logs_filtered(user_id=None, start_date=None, end_date=None, limit=100):
    conn = get_connection()
    cur = conn.cursor()

    sql = '''
        SELECT ll.user_id, ll.login_time
        FROM login_logs ll
        LEFT JOIN users u ON ll.user_id = u.user_id
        WHERE 1=1
    '''
    params = []

    if user_id is not None:
        sql += " AND ll.user_id = ?"
        params.append(user_id)

    if start_date is not None:
        sql += " AND ll.login_time >= ?"
        params.append(start_date.isoformat())

    if end_date is not None:
        sql += " AND ll.login_time <= ?"
        params.append(end_date.isoformat())

    sql += " ORDER BY ll.login_time DESC LIMIT ?"
    params.append(limit)

    cur.execute(sql, params)
    rows = cur.fetchall()
    conn.close()
    return [{"user_id": r[0], "login_time": r[1]} for r in rows]