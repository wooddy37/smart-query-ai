import re
from .base import BaseLogParser

class PostgresqlLogParser(BaseLogParser):

    def extract_slow_queries(self, log_text, threshold_ms):
        pattern = r'duration: ([\d\.]+) ms\s+statement: (.+)'
        matches = re.findall(pattern, log_text)
        return [(float(dur), stmt.strip()) for dur, stmt in matches if float(dur) >= threshold_ms]

    def extract_error_queries(self, log_text):
        pattern = r'ERROR:.*\n.*STATEMENT:\s(.+)'
        matches = re.findall(pattern, log_text)
        return [stmt.strip() for stmt in matches]

    def extract_sql_features(self, sql):
        table_pattern = r'(?:FROM|JOIN|UPDATE|INSERT INTO|DELETE FROM)\s+([a-zA-Z_][a-zA-Z0-9_]*)'
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
        return "PostgreSQL"