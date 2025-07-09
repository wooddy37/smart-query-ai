from abc import ABC, abstractmethod

class BaseLogParser(ABC):
    @abstractmethod
    def extract_slow_queries(self, log_text: str, threshold_ms: int):
        """슬로우 쿼리 추출"""
        pass

    @abstractmethod
    def extract_error_queries(self, log_text: str):
        """오류 쿼리 추출"""
        pass

    @abstractmethod
    def extract_sql_features(self, sql: str):
        """SQL에서 테이블명, 쿼리 패턴 등 추출"""
        pass

    @abstractmethod
    def get_dbms_name(self):
        """DBMS 이름 반환 (예: 'PostgreSQL', 'MySQL')"""
        pass