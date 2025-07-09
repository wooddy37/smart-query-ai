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

from ai.search_client import get_embedding, index_query_to_search, search_documents
from ai.openai_client import get_tuning_suggestion

class UserDashboard:
    """사용자 메뉴 클래스"""

    def __init__(self):
        self.current_user = get_current_user()
        self._init_session_state()
    
    def _init_session_state(self):
        """세션 상태 초기화"""

        defaults = {
            "slow_query_threshold": 2000,
            "prev_file_name": None,
            "input_slow_value": 2000,
            "slow_query_page": 0 ,
            "error_query_page": 0
        }
        
        for key, value in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = value


    def _save_and_rerun(self):
        """세션 저장 및 페이지 새로고침"""
        save_session_state(self.current_user['user_id'])
        st.rerun()


    def _show_query_log_analysis(self):
        
        # st.subheader("쿼리 로그 분석")
        # st.markdown(f"**아이디:** `{self.current_user['user_id']}`")
        # st.markdown(f"**권한:** {'관리자' if self.current_user['is_admin'] else '일반 사용자'}")
        # st.divider()

        st.subheader("📁 내 프로젝트 목록")
        projects = list_user_projects(self.current_user['user_id'])
        if not projects:

            st.warning("할당된 프로젝트가 없습니다.")
        else:
            
            project_options = {f"{p['project_code']} - {p['project_name']}": p for p in projects}
            selected_label = st.selectbox("프로젝트 선택", options=list(project_options.keys()))
            selected_project = project_options[selected_label]

            st.divider()
            st.subheader("📤 쿼리 로그 업로드 및 분석")

            dbms_options = {
                "PostgreSQL": "postgresql",
                "MariaDB": "mariadb",
                "MySQL": "mysql"
            }
            # select_dbms = st.sidebar.selectbox("📦 대상 DBMS", options=list(dbms_options.keys()))
            select_dbms = st.selectbox("📦 대상 DBMS", options=list(dbms_options.keys()))
            dbms_type = dbms_options[select_dbms]

            if dbms_type == "postgresql":
                parser = PostgresqlLogParser()
            elif dbms_type == "mariadb":
                parser = MariaDBLogParser()
            elif dbms_type == "mysql":
                parser = MysqlLogParser()
            else:
                st.error("지원하지 않는 DBMS입니다.")
                st.stop()

            uploaded_file = st.file_uploader(
                # lable="로그 파일 업로드 (LOG, TXT)", 
                label="📂 파일을 마우스로 끌어 오거나 클릭하여 업로드 하세요.",
                type=["log", "txt"],
                help="PostgreSQL, MariaDB, MySQL 로그 파일만 업로드할 수 있습니다."
            )

            st.number_input(
                label="**⏱ 슬로우 쿼리 기준 시간 (ms)** (100 ~ 10000 사이의 값 입력)",
                min_value=100,
                max_value=10000,
                # value=st.session_state.get("slow_query_threshold", 2000),
                step=100,
                key="input_slow_value",
                on_change=self.on_input_change,
            )

            slow_query_threshold_ms = st.session_state["slow_query_threshold"]
            st.write(f"현재 슬로우 쿼리 기준 시간: {slow_query_threshold_ms} ms")


            language = st.selectbox("🌐 튜닝 제안 언어", ["한국어", "English", "Tiếng Việt"])

            if uploaded_file:
                content = None
                project_code = selected_project["project_code"]
                # st.markdown(f"##### 💡 uploaded_file.name: {uploaded_file.name}")
                if uploaded_file.name != st.session_state["prev_file_name"]:
                    st.session_state["prev_file_name"] = uploaded_file.name   
                    st.session_state["slow_query_page"] = 0 
                    st.session_state["error_query_page"] = 0

                    keys_to_delete = [
                        key for key in st.session_state.keys() 
                        if "clicked_btn_ai_" in key or "result_suggestion_btn_ai_" in key or "result_similar_btn_ai_" in key
                    ]
                    for key in keys_to_delete:
                        del st.session_state[key]

                    with st.spinner("파일 업로드 중..."):

                        content = uploaded_file.read().decode("utf-8")
                        st.session_state["upload_content"] = content
                        
                        # 1️⃣ Azure Blob Storage 업로드
                        blob_path = upload_to_blob(file=uploaded_file, project_code=project_code, dbms_type=dbms_type)
                        self._save_and_rerun()
                else:
                    content = st.session_state["upload_content"]

                st.success("✅ Azure Blob Storage 업로드 완료")

                slow_queries = parser.extract_slow_queries(content, slow_query_threshold_ms)
                error_queries = parser.extract_error_queries(content)

                if slow_queries:
                    filters = f"query_type eq 'slow' and project_code eq '{project_code}' and dbms_type eq '{dbms_type}'"                
                    st.subheader(f"🐢 Slow Query {len(slow_queries)}개 발견됨")

                    page_size = 10
                    page = st.session_state.get("slow_query_page", 0)
                    start_idx = 0
                    end_idx = (page + 1) * page_size
                    end_idx = min(end_idx, len(slow_queries))

                    for i, (duration, sql) in enumerate(slow_queries[start_idx:end_idx], start=1):  
                        with st.expander(f"[Slow {i}] {duration:.2f}ms"):
                            st.code(sql, language="sql")
                            btn_key = f"btn_ai_slow_{i}"
                            clicked_btn_key = f"clicked_btn_ai_slow_{i}"
                            result_suggestion = f"result_suggestion_btn_ai_slow_{i}"
                            result_similar = f"result_similar_btn_ai_slow_{i}"

                            if clicked_btn_key not in st.session_state:
                                st.session_state[clicked_btn_key] = False

                            if result_suggestion not in st.session_state:
                                st.session_state[result_suggestion] = None

                            if result_similar not in st.session_state:
                                st.session_state[result_similar] = None

                            try:
                                if not st.session_state[clicked_btn_key]: 
                                    if st.button("💡 AI 튜닝 제안", key=btn_key):
                                        with st.spinner("AI 분석 중..."):
                                            similar_queries = search_documents(dbms_type=dbms_type, query_text=sql, filters=filters , top_k=5)
                                            similar_data = [
                                                {'sql_query': r['sql_query'], 'suggestion': r['suggestion']}
                                                for r in similar_queries if r.get('@search.score', 0) > 0.7
                                            ]
                                            suggestion = get_tuning_suggestion(sql, duration, language, similar_data, dbms_type=dbms_type)
                                            # st.markdown("##### 💡 AI 튜닝 제안")
                                            # st.write(suggestion)

                                            # if similar_data:
                                                # st.markdown("##### 🔍 유사 쿼리 참고")
                                                # for idx, sim in enumerate(similar_data[:2], 1):
                                                    # st.write(f"**유사 쿼리 {idx}:** {sim['sql_query'][:100]}...")
                                                    # st.write(f"**유사 쿼리 {idx}:** {sim['sql_query']}")

                                            create_query_log("slow", duration, sql, suggestion, language, dbms_type, project_code=selected_project["project_code"], user_id=self.current_user["user_id"])
                                            
                                            embedding = get_embedding(sql)
                                            if embedding:
                                                doc = {
                                                    "id": str(uuid.uuid4()),
                                                    "user_id": self.current_user['user_id'],
                                                    "sql_query": sql,
                                                    "suggestion": suggestion,
                                                    "query_type": "slow",
                                                    "duration_ms": duration,
                                                    "language": language,
                                                    "dbms_type": dbms_type,
                                                    "project_code": selected_project["project_code"],
                                                    "created_at": datetime.now().astimezone().isoformat(),
                                                    "sql_embedding": embedding
                                                }
                                                index_query_to_search(doc, dbms_type)
                                            # ✅ 상태 저장
                                            st.session_state[clicked_btn_key] = True
                                            st.session_state[result_suggestion] = suggestion
                                            st.session_state[result_similar] = similar_data
                                            self._save_and_rerun()
                            except Exception as e:
                                st.error(f"{e}")
                                return 
                            finally:
                                # 결과 출력
                                if st.session_state[result_suggestion]:
                                    st.markdown("##### 💡 AI 튜닝 제안")
                                    st.write(st.session_state[result_suggestion])
                                    # st.info("🔒 이미 분석된 쿼리입니다.")
                                    if st.session_state[result_similar]:
                                        st.markdown("##### 🔍 유사 쿼리 참고")
                                        saved_similar_data = st.session_state[result_similar]
                                        
                                        for idx, sim in enumerate(saved_similar_data[:2], 1):
                                            # st.write(f"**유사 쿼리 {idx}:** {sim['sql_query'][:100]}...")
                                            # st.write(f"**유사 쿼리 {idx}:** {sim['sql_query']}")
                                            # st.info("🔒 이미 분석된 쿼리입니다.")
                                            with st.container():
                                                st.markdown(f"#### ✅ 유사 쿼리 {idx}")
                                                st.code(sim["sql_query"], language="sql")
                                                if sim.get("suggestion"):
                                                    with st.expander("💡 튜닝 제안 보기"):
                                                        st.write(sim["suggestion"])
                    
                    # 👉 다음 페이지가 있으면 "더 보기" 버튼 표시
                    if end_idx < len(slow_queries):
                        if st.button("➕ 더 보기"):
                            st.session_state["slow_query_page"] += 1
                            self._save_and_rerun()
                    else:
                        st.markdown("✅ 모든 슬로우 쿼리를 다 확인했습니다.")

                if error_queries:
                    filters = f"query_type eq 'error' and project_code eq '{project_code}' and dbms_type eq '{dbms_type}'"
                    st.subheader(f"❌ Error Query {len(error_queries)}개 발견됨")

                    page_size = 10
                    page = st.session_state.get("error_query_page", 0)
                    start_idx = 0
                    end_idx = (page + 1) * page_size
                    end_idx = min(end_idx, len(error_queries))

                    for i, sql in enumerate(error_queries[start_idx:end_idx], start=1):
                        btn_key = f"btn_ai_error_{i}"
                        clicked_btn_key = f"clicked_btn_ai_error_{i}"
                        result_suggestion = f"result_suggestion_btn_ai_error_{i}"
                        result_similar = f"result_similar_btn_ai_error_{i}"

                        if clicked_btn_key not in st.session_state:
                            st.session_state[clicked_btn_key] = False

                        if result_suggestion not in st.session_state:
                            st.session_state[result_suggestion] = None

                        if result_similar not in st.session_state:
                            st.session_state[result_similar] = None

                        with st.expander(f"[Error {i}]", expanded=st.session_state[clicked_btn_key]):
                            st.code(sql, language="sql")

                            try:
                                if not st.session_state[clicked_btn_key]: 
                                    if st.button("🛠 AI 오류 분석", key=btn_key):
                                        with st.spinner("AI 오류 분석 중..."):
                                            similar_queries = search_documents(dbms_type=dbms_type, query_text=sql, filters=filters, top_k=3)
                                            similar_data = [
                                                {'sql_query': r['sql_query'], 'suggestion': r['suggestion']}
                                                for r in similar_queries if r.get('@search.score', 0) > 0.6
                                            ]
                                            suggestion = get_tuning_suggestion(sql, 0, language, similar_data, dbms_type=dbms_type)
                                            # st.markdown("##### 🛠 AI 오류 수정 제안")
                                            # st.write(suggestion)
                                            # # 3️⃣ DB 저장
                                            # st.info("DB 저장 중...")
                                            create_query_log("error", 0, sql, suggestion, language, dbms_type, project_code=selected_project["project_code"], user_id=self.current_user["user_id"])
                                            # st.success("✅ 분석 및 저장 완료")
                                            
                                            embedding = get_embedding(sql)
                                            if embedding:
                                                doc = {
                                                    "id": str(uuid.uuid4()),
                                                    "user_id": self.current_user['user_id'],
                                                    "sql_query": sql,
                                                    "suggestion": suggestion,
                                                    "query_type": "error",
                                                    "duration_ms": duration,
                                                    "language": language,
                                                    "dbms_type": dbms_type,
                                                    "project_code": selected_project["project_code"],
                                                    "created_at": datetime.now().astimezone().isoformat(),
                                                    "sql_embedding": embedding
                                                }
                                                index_query_to_search(doc, dbms_type)
                                            # ✅ 상태 저장
                                            st.session_state[clicked_btn_key] = True
                                            st.session_state[result_similar] = similar_data
                                            st.session_state[result_suggestion] = suggestion
                                            self._save_and_rerun()
                            except Exception as e:
                                st.error(f"{e}")
                                return 
                            finally:
                                # 결과 출력
                                if st.session_state[result_suggestion]:
                                    st.markdown("##### 🛠 AI 오류 수정 제안")
                                    st.write(st.session_state[result_suggestion])
                                    # st.info("🔒 이미 분석된 쿼리입니다.")

                    if end_idx < len(error_queries):
                        if st.button("➕ 더 보기 (에러 쿼리)"):
                            st.session_state["error_query_page"] += 1
                            self._save_and_rerun()
                    else:
                        st.markdown("✅ 모든 에러 쿼리를 다 확인했습니다.")
    

    def on_input_change(self):
        st.session_state["slow_query_threshold"] = st.session_state["input_slow_value"]
        self._save_and_rerun()


    def _show_query_log_analysis_history(self):

        st.subheader("쿼리 로그 분석 현황")
        query_logs = list_query_logs_by_user_id(user_id=self.current_user["user_id"])
        if query_logs:
            # 데이터프레임 생성
           df_query_logs = self._create_query_logs_dataframe(query_logs)
           st.dataframe(df_query_logs, use_container_width=True)

        else:
            st.info("등록된 쿼리 로그 분석 이력이 없습니다.")

    def _create_query_logs_dataframe(self, query_logs):
        """분석 이력 데이터프레임 생성"""

        df = pd.DataFrame(query_logs)
        df.index = df.index + 1
        df["created_dt"] = utc_to_local(df["created_at"])
        df["sql_html"] = df["sql"].str.replace('\n', '<br>', regex=False).apply(html.unescape)
        df = df[["project_code", "project_name", "dbms_type", "query_type", "sql_html", "suggestion", "created_at"]]
        df.columns = ["프로젝트 코드", "프로제트명", "DBMS", "쿼리 유형",  "쿼리", "제안", "등록일"]
        # df.insert(0, "No", range(1, len(df) + 1))

        df_range = df.copy()
        df_range.index = range(1, len(df) + 1)
        df_range.index.name = "No"

        return df_range
    