import html
import time
import pandas as pd
from urllib.parse import quote, urlencode
from datetime import date
from st_aggrid import AgGrid, GridOptionsBuilder, JsCode
import streamlit as st
from auth.session import is_logged_in, save_session_state, get_current_user
from database.user import get_user, list_users, create_user, update_user
from database.project import get_project_by_project_code, list_projects, create_project, update_project
from database.user_project import assign_user_to_project, remove_user_from_project, list_user_projects
from database.login_log import list_login_logs_filtered
from utils.datetime import utc_to_local, local_to_utc

class AdminDashboard:
    """관리자 대시보드 클래스"""
    
    def __init__(self):
        self.current_user = get_current_user()
        self._init_session_state()
    
    def _init_session_state(self):
        """세션 상태 초기화"""

        defaults = {
            "user_tab_selected_mode": "list",
            "user_tab_selected_user_id": None,
            "user_tab_selected_user_id": None,
            "project_tab_selected_mode": "list",
            "project_tab_selected_project_code": None,
            "project_tab_selected_project_code": None
        }
        
        for key, value in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = value


    def _save_and_rerun(self):
        """세션 저장 및 페이지 새로고침"""
        save_session_state(self.current_user['user_id'])
        st.rerun()

    
    def _show_user_management(self):
        """사용자 관리 탭"""
        mode = st.session_state["user_tab_selected_mode"]
        
        mode_handlers = {
            "list": self._show_user_list,
            # "view": self._show_user_list,
            "edit": self._show_user_edit,
            "create": self._show_user_create
        }
        
        handler = mode_handlers.get(mode, self._show_user_list)
        handler()
    
    def _show_project_management(self):
        """프로젝트 관리 탭"""
        mode = st.session_state["project_tab_selected_mode"]
        
        mode_handlers = {
            "list": self._show_project_list,
            # "view": self._show_project_detail,
            "edit": self._show_project_edit,
            "create": self._show_project_create
        }
        
        handler = mode_handlers.get(mode, self._show_project_list)
        handler()
    
    def _show_user_project_mapping(self):
        """사용자-프로젝트 매핑 탭"""
        st.subheader("사용자 프로젝트 매핑")
        
        users = list_users()
        projects = list_projects()
        
        # 매핑 등록 섹션
        self._render_mapping_form(users, projects)
        
        st.divider()
        
        # 현재 매핑 현황
        self._render_current_mappings(users)
    
    def _render_mapping_form(self, users, projects):
        """매핑 등록 폼"""
        # st.write("#### 새 매핑 등록")
        
        user_options = {u['user_id']: u['user_id'] for u in users}
        project_options = {p['project_name']: p['project_code'] for p in projects}
        
        col1, col2, col3 = st.columns([3, 3, 2])
        
        with col1:
            selected_user = st.selectbox("사용자 선택", options=list(user_options.keys()))
        
        with col2:
            selected_project = st.selectbox("프로젝트 선택", options=list(project_options.keys()))
        
        with col3:
            st.write("")  # 공백
            if st.button("매핑 등록", use_container_width=True):
                self._handle_mapping_assignment(
                    user_options[selected_user],
                    project_options[selected_project],
                    selected_user,
                    selected_project
                )
    
    def _handle_mapping_assignment(self, user_id, project_code, user_name, project_name):
        """매핑 등록 처리"""
        success = assign_user_to_project(
            user_id=user_id,
            project_code=project_code,
            created_by=self.current_user['user_id']
        )
        
        if success:
            st.success(f"✅ {user_name}님이 {project_name} 프로젝트에 매핑되었습니다.")
            self._save_and_rerun()
        else:
            st.warning("⚠️ 이미 매핑된 사용자-프로젝트 조합입니다.")
    
    def _render_current_mappings(self, users):
        """현재 매핑 현황 표시"""
        st.write("#### 사용자 프로젝트 매핑 현황")
        
        for user in users:
            if not user['is_admin']:
                with st.expander(f"👤 {user['user_id']}님의 프로젝트", expanded=False):
                    mapped_projects = list_user_projects(user['user_id'])
                    
                    if mapped_projects:
                        for mp in mapped_projects:
                            col1, col2 = st.columns([4, 1])
                            with col1:
                                st.write(f"📁 {mp['project_code']} : {mp['project_name']}")
                            with col2:
                                if st.button("🗑️ 해제", key=f"btn_unmap_{user['user_id']}_{mp['project_code']}"):
                                    self._handle_mapping_removal(user['user_id'], mp['project_code'], mp['project_name'])
                    else:
                        st.info("등록된 프로젝트가 없습니다.")
    
    def _handle_mapping_removal(self, user_id, project_code, project_name):
        """매핑 해제 처리"""
        remove_user_from_project(user_id, project_code)
        st.success(f"✅ {user_id}님의 {project_name} 매핑이 해제되었습니다.")
        self._save_and_rerun()

    
    def _show_user_list(self):
        """사용자 목록 화면"""
        col1, col2 = st.columns([8, 2])
        
        with col1:
            st.subheader("사용자 목록")
        
        with col2:
            if st.button("➕ 사용자 등록", use_container_width=True):
                st.session_state["user_tab_selected_mode"] = "create"
                self._save_and_rerun()
        
        users = list_users()
        
        if not users:
            st.info("등록된 사용자가 없습니다.")
            return
        
        # 데이터프레임 생성
        df_users = self._create_user_dataframe(users)
        
        # AgGrid 설정
        grid_response_users = self._create_user_grid(df_users)
        
        # 선택된 사용자 정보 표시
        self._display_selected_user_info(grid_response_users)
    
    def _create_user_dataframe(self, users):
        """사용자 데이터프레임 생성"""
        df = pd.DataFrame(users)
        df["created_dt"] = utc_to_local(df["created_at"])
        df["role"] = df["is_admin"].apply(lambda x: "✅ 관리자" if x else "👤 사용자")
        df = df[["user_id", "role", "created_dt"]]
        df.columns = ["아이디", "권한", "등록일"]
        df.insert(0, "No", range(1, len(df) + 1))
        return df
    
    def _create_user_grid(self, df):
        """사용자 그리드 생성"""
        gb = GridOptionsBuilder.from_dataframe(df)
        gb.configure_column("No", header_name="No", width=60, sortable=False)
        gb.configure_pagination(paginationAutoPageSize=False, paginationPageSize=10)
        gb.configure_selection('single', use_checkbox=False)
        grid_options = gb.build()
        
        return AgGrid(
            df,
            gridOptions=grid_options,
            fit_columns_on_grid_load=True,
            update_mode="MODEL_CHANGED",
            allow_unsafe_jscode=True,
            height=400,
            theme="streamlit"
        )
    
    def _display_selected_user_info(self, grid_response):
        """선택된 사용자 정보 표시"""
        selected_rows = grid_response.get('selected_rows')
        
        if selected_rows is not None and not selected_rows.empty:
            selected_user = selected_rows.iloc[0]
            user_id = selected_user["아이디"]
            
            # 사용자 상세 정보 표시
            st.divider()
            st.subheader("사용자 상세 정보")
            
            # 실제 사용자 정보 조회
            user_detail = get_user(user_id)
            
            # 상세 정보 표시
            col1, col2 = st.columns([1, 3])
            
            with col1:
                st.write("**아이디:**")
                st.write("**권한:**")
                st.write("**등록일:**")
                if user_detail.get('updated_at'):
                    st.write("**수정일:**")
                if user_detail.get('created_by'):
                    st.write("**등록자:**")

            with col2:
                st.write(f"`{user_detail['user_id']}`")
                st.write("관리자" if user_detail['is_admin'] else "일반 사용자")
                st.write(f"`{utc_to_local(user_detail.get('created_at', 'N/A'))}`")
                if user_detail.get('updated_at'):
                    st.write(f"`{utc_to_local(user_detail.get('updated_at', 'N/A'))}`")
                if user_detail.get('created_by'):
                    st.write(f"`{user_detail.get('created_by', 'N/A')}`")
            
            # 사용자의 프로젝트 매핑 정보
            if not user_detail['is_admin']:
                st.write("#### 📁 할당된 프로젝트")
                mapped_projects = list_user_projects(user_id)
                
                if mapped_projects:
                    for i, mp in enumerate(mapped_projects, 1):
                        st.write(f"{i}. **{mp['project_code']}** - {mp['project_name']}")
                else:
                    st.info("할당된 프로젝트가 없습니다.")

            # 수정 버튼
            if st.button("수정", use_container_width=True):
                st.session_state["user_tab_selected_mode"] = "edit"
                st.session_state["user_tab_selected_user_id"] = user_id
                self._save_and_rerun()
    
    
    def _show_user_edit(self):
        """사용자 수정 화면"""
        user_id = st.session_state.get("user_tab_selected_user_id")
        user = get_user(user_id)
        
        st.subheader(f"✏️ 사용자 수정")
        
        # 폼
        st.markdown(f"**아이디:** `{user['user_id']}`")
        password = st.text_input("비밀번호 (변경 시 입력)", type="password")
        is_admin = st.checkbox("관리자 권한", value=user['is_admin'])
        
        # 버튼
        col1, col2 = st.columns([1, 1])
        
        with col1:
            if st.button("저장", use_container_width=True):
                self._handle_user_update(user, password, is_admin)
        
        with col2:
            if st.button("취소", use_container_width=True):
                st.session_state["user_tab_selected_mode"] = "list"
                st.session_state["user_tab_selected_user_id"] = None
                self._save_and_rerun()
    
    def _handle_user_update(self, user, password, is_admin):
        """사용자 수정 처리"""
        try:
            update_user(
                user_id=user['user_id'],
                password=password or None,
                is_admin=is_admin,
                updated_by=self.current_user["user_id"]
            )
            st.success("✅ 수정이 완료되었습니다.")
            st.session_state["user_tab_selected_mode"] = "list"
            st.session_state["user_tab_selected_user_id"] = None
            self._save_and_rerun()
        except Exception as e:
            st.error(f"❌ 수정 중 오류가 발생했습니다: {e}")
    
    def _show_user_create(self):
        """사용자 등록 화면"""
        st.subheader("사용자 등록")
        
        # 폼
        user_id = st.text_input("아이디")
        password = st.text_input("비밀번호", type="password")
        is_admin = st.checkbox("관리자 권한")
        
        # 버튼
        col1, col2 = st.columns([1, 1])
        
        with col1:
            if st.button("등록", use_container_width=True):
                self._handle_user_creation(user_id, password, is_admin)
        
        with col2:
            if st.button("취소", use_container_width=True):
                st.session_state["user_tab_selected_mode"] = "list"
                self._save_and_rerun()
    
    def _handle_user_creation(self, user_id, password, is_admin):
        """사용자 등록 처리"""
        if not user_id or not password:
            st.error("❌ 아이디와 비밀번호를 입력하세요.")
            return
        
        if get_user(user_id):
            st.warning("⚠️ 이미 등록된 아이디입니다.")
            return
        
        try:
            create_user(
                user_id=user_id,
                password=password,
                is_admin=is_admin,
                created_by=self.current_user["user_id"]
            )
            st.success("✅ 사용자 등록이 완료되었습니다.")
            st.session_state["user_tab_selected_mode"] = "list"
            self._save_and_rerun()
        except Exception as e:
            st.error(f"❌ 등록 중 오류가 발생했습니다: {e}")
    
    def _show_project_list(self):
        """프로젝트 목록 화면"""
        col1, col2 = st.columns([8, 2])
        
        with col1:
            st.subheader("프로젝트 목록")
        
        with col2:
            if st.button("➕ 프로젝트 등록", use_container_width=True):
                st.session_state["project_tab_selected_mode"] = "create"
                self._save_and_rerun()
        
        projects = list_projects()
        
        if not projects:
            st.info("등록된 프로젝트가 없습니다.")
            return
        
        # 데이터프레임 생성
        df_projects = self._create_project_dataframe(projects)
        
        # AgGrid 설정
        grid_response_projects = self._create_project_grid(df_projects)
        
        # 선택된 사용자 정보 표시
        self._display_selected_project_info(grid_response_projects)
        
    
    def _create_project_dataframe(self, projects):
        """프로젝트 데이터프레임 생성"""
        df = pd.DataFrame(projects)
        df["created_dt"] = utc_to_local(df["created_at"])
        df = df[["project_code", "project_name", "created_dt"]]
        df.columns = ["프로젝트 코드", "프로젝트명", "등록일"]
        df.insert(0, "No", range(1, len(df) + 1))
        return df
    
    def _create_project_grid(self, df):
        """프로젝트 그리드 생성"""

        gb = GridOptionsBuilder.from_dataframe(df)
        gb.configure_column("No", header_name="No", width=60, sortable=False)
        gb.configure_pagination(paginationAutoPageSize=False, paginationPageSize=10)
        gb.configure_selection('single', use_checkbox=False)
        grid_options = gb.build()
        
        return AgGrid(
            df,
            gridOptions=grid_options,
            fit_columns_on_grid_load=True,
            update_mode="MODEL_CHANGED",
            allow_unsafe_jscode=True,
            height=400,
            theme="streamlit"
        )
    
    def _display_selected_project_info(self, grid_response):
        """선택된 프로젝트 정보 표시"""
        selected_rows = grid_response.get('selected_rows')
        
        if selected_rows is not None and not selected_rows.empty:
            selected_project = selected_rows.iloc[0]
            project_code = selected_project["프로젝트 코드"]
            
            # 프로젝트 상세 정보 표시
            st.divider()
            st.subheader("프로젝트 상세 정보")
            
            # 실제 프로젝트 정보 조회
            project_detail = get_project_by_project_code(project_code)
            
            # 상세 정보 표시
            col1, col2 = st.columns([1, 3])
            
            with col1:
                st.write("**프로젝트 코드:**")
                st.write("**프로젝트명:**")
                st.write("**등록일:**")
                if project_detail.get('updated_at'):
                    st.write("**수정일:**")
                if project_detail.get('created_by'):
                    st.write("**등록자:**")
            
            with col2:
                st.write(f"`{project_detail['project_code']}`")
                st.write(f"`{project_detail['project_name']}`")
                st.write(f"`{utc_to_local(project_detail.get('created_at', 'N/A'))}`")
                if project_detail.get('updated_at'):
                    st.write(f"`{utc_to_local(project_detail.get('updated_at', 'N/A'))}`")
                if project_detail.get('created_by'):
                    st.write(f"`{project_detail.get('created_by', 'N/A')}`")
            
            # 수정 버튼
            if st.button("수정", use_container_width=True):
                st.session_state["project_tab_selected_mode"] = "edit"
                st.session_state["project_tab_selected_project_code"] = project_code
                self._save_and_rerun()


    def _show_project_edit(self):
        """프로젝트 수정 화면"""
        project_code = st.session_state.get("project_tab_selected_project_code")
        project = get_project_by_project_code(project_code)
        
        st.subheader(f"프로젝트 수정")
        
        # 폼
        st.markdown(f"**프로젝트 코드:** `{project['project_code']}`")
        project_name = st.text_input("프로젝트명", value=project['project_name'])
        
        # 버튼
        col1, col2 = st.columns([1, 1])
        
        with col1:
            if st.button("저장", use_container_width=True):
                self._handle_project_update(project, project_name)
        
        with col2:
            if st.button("취소", use_container_width=True):
                st.session_state["project_tab_selected_mode"] = "list"
                self._save_and_rerun()
    
    def _handle_project_update(self, project, project_name):
        """프로젝트 수정 처리"""
        try:
            update_project(
                project_code=project['project_code'],
                project_name=project_name,
                updated_by=self.current_user["user_id"]
            )
            st.success("✅ 수정이 완료되었습니다.")
            st.session_state["project_tab_selected_mode"] = "list"
            self._save_and_rerun()
        except Exception as e:
            st.error(f"❌ 수정 중 오류가 발생했습니다: {e}")
    
    def _show_project_create(self):
        """프로젝트 등록 화면"""
        st.subheader("프로젝트 등록")
        
        # 폼
        project_code = st.text_input("프로젝트 코드", max_chars=8)
        project_name = st.text_input("프로젝트명")
        
        # 버튼
        col1, col2 = st.columns([1, 1])
        
        with col1:
            if st.button("등록", use_container_width=True):
                self._handle_project_creation(project_code, project_name)
        
        with col2:
            if st.button("취소", use_container_width=True):
                st.session_state["project_tab_selected_mode"] = "list"
                self._save_and_rerun()
    
    def _handle_project_creation(self, project_code, project_name):
        """프로젝트 등록 처리"""
        if not project_code or not project_name:
            st.error("❌ 프로젝트 코드와 프로젝트명을 입력하세요.")
            return
        
        if get_project_by_project_code(project_code):
            st.warning("⚠️ 이미 등록된 프로젝트 코드입니다.")
            return
        
        try:
            create_project(
                project_code=project_code,
                project_name=project_name,
                created_by=self.current_user["user_id"]
            )
            st.success("✅ 프로젝트 등록이 완료되었습니다.")
            st.session_state["project_tab_selected_mode"] = "list"
            self._save_and_rerun()
        except Exception as e:
            st.error(f"❌ 등록 중 오류가 발생했습니다: {e}")


# def show():
#     """메인 엔트리 포인트"""
#     dashboard = AdminDashboard()
#     dashboard.show()