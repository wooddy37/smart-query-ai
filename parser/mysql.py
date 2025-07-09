import re
from .base import BaseLogParser

class MysqlLogParser(BaseLogParser):

    def extract_slow_queries(self, log_text, threshold_ms):
        # MySQL slow query log 패턴 예시 처리
        pattern = r'# Query_time: ([\d\.]+).+?\n(?:.+\n)*?(.+);'
        matches = re.findall(pattern, log_text, re.MULTILINE)
        # 단위 sec → ms 변환 및 threshold 필터링
        return [(float(dur)*1000, stmt.strip()) for dur, stmt in matches if float(dur)*1000 >= threshold_ms]

    def extract_error_queries(self, log_text):
        # MySQL 에러 로그는 일반 slow query 로그와 별개이므로 별도 구현 필요 (임시 빈 리스트)
        return []

    def extract_sql_features(self, sql):
        # MySQL 문법에 맞게 테이블명 추출 (대략 PostgreSQL과 비슷)
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
        return "MySQL"