import html
import pandas as pd
from urllib.parse import quote
from datetime import date
import time
import uuid
import streamlit as st
import os
from auth.session import is_logged_in, save_session_state
from utils.datetime import datetime, utc_to_local
from utils.string import get_truncated_sql
from auth.session import get_current_user
from database.user_project import list_user_projects
from database.query_log import create_query_log, list_query_logs_by_user_id
from ai.blob import upload_to_blob
# from utils.ai import analyze_query_log_file
from parser.mariadb import MariaDBLogParser
from parser.postgresql import PostgresqlLogParser
from parser.mysql import MysqlLogParser

from ai.search_client import get_embedding, index_query_to_search, search_documents, semantic_search_queries
from ai.openai_client import get_tuning_suggestion


class UserEmbedding:
    """사용자 임베딩 클래스"""

    def __init__(self):
        self.current_user = get_current_user()
        # self._init_session_state()
    
    # def _init_session_state(self):
    #     """세션 상태 초기화"""

        # defaults = {
        #     "": 2000,
        # }
        
        # for key, value in defaults.items():
        #     if key not in st.session_state:
        #         st.session_state[key] = value

    def _save_and_rerun(self):
        """세션 저장 및 페이지 새로고침"""
        save_session_state(self.current_user['user_id'])
        st.rerun()

    def show_query_similarity_search(self):
        st.subheader("유사 쿼리 검색")

        projects = list_user_projects(self.current_user['user_id'])

        if not projects:

            st.warning("할당된 프로젝트가 없습니다.")
        else:

            project_options = {f"{p['project_code']} - {p['project_name']}": p for p in projects}
            selected_label = st.selectbox("프로젝트 선택", options=list(project_options.keys()))
            selected_project = project_options[selected_label]

            st.divider()

            dbms_options = {
                "PostgreSQL": "postgresql",
                "MariaDB": "mariadb",
                "MySQL": "mysql"
            }
            # select_dbms = st.sidebar.selectbox("📦 대상 DBMS", options=list(dbms_options.keys()))
            select_dbms = st.selectbox("📦 대상 DBMS", options=list(dbms_options.keys()))
            dbms_type = dbms_options[select_dbms]


            st.markdown("임베딩 기반으로 유사한 SQL 쿼리를 검색합니다.")
            sql_input = st.text_area("📥 SQL 쿼리 입력", height=200, placeholder="예) SELECT * FROM orders WHERE status = 'pending'")

            if st.button("🔎 유사 쿼리 검색"):
                if not sql_input.strip():
                    st.warning("SQL 쿼리를 입력해 주세요.")
                    return
                
                project_code = selected_project["project_code"]

                with st.spinner("임베딩 생성 및 검색 중..."):
                    try:
                        filters = f"project_code eq '{project_code}' and dbms_type eq '{dbms_type}'"
                        results = semantic_search_queries(
                            query_text=sql_input,
                            dbms_type=dbms_type,
                            filters=filters,
                            top_k=10
                        )

                        if results:
                            st.success(f"총 {len(results)}개의 유사 쿼리를 찾았습니다.")
                            for idx, item in enumerate(results, start=1):
                                with st.container():
                                    st.markdown(f"#### ✅ 유사 쿼리 {idx} (유사도 점수: {item.get('@search.score', 0):.3f})")
                                    st.code(item.get("sql_query", ""), language="sql")
                                    # st.caption(f"유사도 점수: {item.get('@search.score', 0):.3f}")
                                    if item.get("suggestion"):
                                        with st.expander("💡 튜닝 제안 보기"):
                                            st.write(item["suggestion"])
                        else:
                            st.info("유사한 쿼리를 찾지 못했습니다.")

                    except Exception as e:
                        st.error(f"오류 발생: {e}")

