import time
import streamlit as st
import os
from streamlit_option_menu import option_menu
from auth.session import get_current_user, load_session_state, load_user_from_token
from database.connection import init_db
from router import login_page
from router.admin_dashboard import AdminDashboard
from router.user_dashboard import UserDashboard

# if 'selected_menu_index' not in st.session_state:
#     st.session_state["selected_menu_index"] = 0

def logout():
    token = st.query_params.get("session_token", [None])[0]
    tokenpath = f"./session_tokens/{token}.json"
    if os.path.exists(tokenpath):
        os.remove(tokenpath)
    st.query_params.clear()

    user = st.session_state.get("user", {})
    filepath = f"./session_states/session_{user['user_id']}.json"
    if os.path.exists(filepath):
        os.remove(filepath)
    st.session_state.clear()
    st.rerun()

# 페이지 Routing
def route():

    dashboard = None

    if not st.session_state.get("logged_in", False):

        params = st.query_params
        token = params.get("session_token", [None])[0]

        if token:
            # st.write("token: ", token)
            user_id = load_user_from_token(token)
            # st.write("✅ 현재 사용자:", user_id)
            load_session_state(user_id)
            st.rerun()
        # else:
        #     st.warning("세션 정보 없음")
        st.set_page_config(
            page_title="로그인",
            layout="centered"
        )

        login_page.show()
    else:
        current_user = get_current_user()
        is_admin = current_user.get("is_admin", False)
        load_session_state(current_user["user_id"])

        if is_admin:

            dashboard = AdminDashboard()
            st.set_page_config(
                page_title="관리자 대시보드",
                layout="wide",       # 화면 넓게 사용
                initial_sidebar_state="auto"
            )

            with st.sidebar:
                st.markdown(f"**{current_user["user_id"]}님**")
                selected = option_menu(
                    menu_title="관리자 메뉴",
                    options=["사용자 관리", "프로젝트 관리", "사용자 프로젝트 매핑"],
                    icons=["people", "folder", "link"],
                    menu_icon="cast",
                    default_index=0,
                    orientation="vertical",
                )
                # 로그아웃
                st.markdown("---")
                if st.button("🔚 로그아웃", use_container_width=True):
                    logout()
            
            page = selected

            if page == "사용자 관리":
                dashboard._show_user_management()
            elif page == "프로젝트 관리":
                dashboard._show_project_management()
            elif page == "사용자 프로젝트 매핑":
                dashboard._show_user_project_mapping()

            # dashboard_admin.show()
        else:

            dashboard = UserDashboard()

            st.set_page_config(
                page_title="사용자 대시보드",
                layout="wide",       # 화면 넓게 사용
                initial_sidebar_state="auto"
            )

            with st.sidebar:
                st.markdown(f"**{current_user["user_id"]}님**")
                selected = option_menu(
                    menu_title="사용자 메뉴",
                    options=["쿼리 로그 분석", "이력 관리"],
                    icons=["bi-graph-up", "bi-clipboard-data"],
                    menu_icon="cast",
                    default_index=0,
                    orientation="vertical",
                )
                # 로그아웃
                st.markdown("---")
                if st.button("🔓 로그아웃", use_container_width=True):
                    logout()

            page = selected

            if page == "쿼리 로그 분석":
                dashboard._show_query_log_analysis()
            elif page == "이력 관리":
                dashboard._show_query_log_analysis_history()



if __name__ == "__main__":
    init_db()
    route()
