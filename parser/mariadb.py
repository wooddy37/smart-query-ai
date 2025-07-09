import re
from .base import BaseLogParser

class MariaDBLogParser(BaseLogParser):

    def extract_slow_queries(self, log_text, threshold_ms):
        # MariaDB slow query log 예시 패턴:
        # # Time: 2023-07-03T12:34:56.789123Z
        # # User@Host: root[root] @ localhost []
        # # Query_time: 1.234  Lock_time: 0.000 Rows_sent: 1  Rows_examined: 0
        # SELECT * FROM users WHERE id = 1;
        pattern = r'# Query_time: ([\d\.]+).+?\n(?:.+\n)*?(.+);'
        matches = re.findall(pattern, log_text, re.IGNORECASE)
        return [(float(dur)*1000, stmt.strip()) for dur, stmt in matches if float(dur)*1000 >= threshold_ms]

    def extract_error_queries(self, log_text):
        # MariaDB 일반 에러 로그는 형태가 다양하지만 보통 'ERROR' 문구 포함, 'Query' 라벨 뒤 SQL문
        # 예시:
        # 2023-07-03T12:34:56.789123Z 123 [ERROR] Some error message
        # Query: SELECT * FROM invalid_table;
        pattern = r'ERROR.*\nQuery:\s(.+);'
        matches = re.findall(pattern, log_text, re.IGNORECASE)
        return [stmt.strip() for stmt in matches]

    def extract_sql_features(self, sql):
        table_pattern = r'(?:FROM|JOIN|UPDATE|INSERT INTO|DELETE FROM)\s+`?([a-zA-Z_][a-zA-Z0-9_]*)`?'
        tables = list(set(re.findall(table_pattern, sql, re.IGNORECASE)))
        patterns = []
        if re.search(r'SELECT.*FROM', sql, re.IGNORECASE): patterns.append('SELECT')
        if re.search(r'INSERT INTO', sql, re.IGNORECASE): patterns.append('INSERT')
        if re.search(r'UPDATE.*SET', sql, re.IGNORECASE): patterns.append('UPDATE')
        if re.search(r'DELETE FROM', sql, re.IGNORECASE): patterns.append('DELETE')
        if re.search(r'JOIN', sql, re.IGNORECASE): patterns.append('JOIN')
        if re.search(r'GROUP BY', sql, re.IGNORECASE): patterns.append('GROUP_BY')
        if re.search(r'ORDER BY', sql, re.IGNORECASE): patterns.append('ORDER_BY')
        if re.search(r'HAVING', sql, re.IGNORECASE): patterns.append('HAVING')
        if re.search(r'SUBQUERY|\(SELECT', sql, re.IGNORECASE): patterns.append('SUBQUERY')
        return tables, patterns

    def get_dbms_name(self):
        return "MariaDB"