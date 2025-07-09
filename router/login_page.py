# 로그인 UI
import streamlit as st
from auth.login import login
from auth.session import create_session_token, get_current_user, save_session_state, set_user_session

def show():

    st.markdown("""
    <style>
    /* 전체 페이지 배경 */
    .stApp {
        background-color: #0f0f0f;
    }
    
    /* 메인 컨테이너를 화면 중앙에 배치 */
    .main .block-container {
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        min-height: 100vh;
        padding: 1rem;
        max-width: 400px;
        margin: 0 auto;
    }
    
    /* 로그인 폼 전체 컨테이너 */
    .login-form-container {
        width: 100%;
        max-width: 400px;
    }
    
    .login-title {
        font-size: 1.5rem;
        font-weight: 700;
        color: #00B4D8;
        text-align: center;
        margin-bottom: 2rem;
        margin-top: 0;
    }
    
    .stTextInput > div > div > input {
        background-color: #2d2d2d;
        color: #e0e0e0;
        border: 1px solid #00B4D8;
        border-radius: 6px;
    }
    
    .stButton > button {
        background-color: #00B4D8;
        color: white;
        border: none;
        border-radius: 6px;
        width: 100%;
        padding: 0.5rem 1rem;
        font-weight: 600;
        margin-top: 1rem;
    }
    
    .stButton > button:hover {
        background-color: #0099cc;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # 로그인 폼을 감싸는 컨테이너
    with st.container():
        st.markdown('<div class="login-form-container">', unsafe_allow_html=True)
        
        # 제목
        st.markdown('<div class="login-title">🤖 AI 기반의 지능형 쿼리 분석 시스템</div>', unsafe_allow_html=True)
        
        
    # 로그인 폼
    user_id = st.text_input("아이디")
    password = st.text_input("비밀번호", type="password")

    if st.button("로그인"):
        if not user_id or not password:
            st.warning("아이디와 비밀번호를 모두 입력하세요.")
            return

        user = login(user_id, password)
        if user:
            set_user_session(user)
            token = create_session_token(f"{user['user_id']}")
            st.query_params = {"session_token": [token]}
            current_user = get_current_user()
            save_session_state(current_user['user_id'])
            
            st.rerun()
        else:
            st.error("로그인 실패: 아이디 또는 비밀번호가 올바르지 않습니다.")
            return
            
    st.markdown('</div>', unsafe_allow_html=True)