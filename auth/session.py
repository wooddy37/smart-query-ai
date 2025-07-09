# 세션 
import uuid
import streamlit as st
import json
import os

def set_user_session(user: dict):
    """
    사용자 정보를 세션에 저장하여 로그인 상태 유지.
    user dict 예: {'id': ..., 'username': ..., 'is_admin': ...}
    """
    st.session_state['logged_in'] = True
    st.session_state['user'] = user

def clear_session():
    """
    로그아웃 시 세션 초기화.
    """
    for key in list(st.session_state.keys()):
        del st.session_state[key]

def is_logged_in() -> bool:
    """
    로그인 상태 확인.
    """
    return st.session_state.get('logged_in', False)


def get_current_user() -> dict | None:
    """
    현재 로그인한 사용자 정보 반환.
    """
    return st.session_state.get('user')

# 사용자 정보 토큰 생성
def create_session_token(user_id: str) -> str:
    
    SESSIONS_DIR = "session_tokens"
    os.makedirs(SESSIONS_DIR, exist_ok=True)

    token = str(uuid.uuid4())
    session_path = os.path.join(SESSIONS_DIR, f"{token}.json")
    with open(session_path, "w") as f:
        json.dump({"user_id": user_id}, f)
    return token

# 사용자 정보 토큰 불러오기
def load_user_from_token(token: str) -> str | None:

    SESSIONS_DIR = "session_tokens"
    os.makedirs(SESSIONS_DIR, exist_ok=True)

    session_path = os.path.join(SESSIONS_DIR, f"{token}.json")
    if os.path.exists(session_path):
        with open(session_path, "r") as f:
            data = json.load(f)
        return data.get("user_id")
    return None

# 세션 상태 저장 함수
def save_session_state(user_id: str):
    if user_id is None:
        return
    data = dict(st.session_state)
    # 저장할 경로
    filepath = f"./session_states/session_{user_id}.json"
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w") as f:
        json.dump(data, f)

# 세션 상태 복원 함수
def load_session_state(user_id):
    if user_id is None:
        return
    filepath = f"./session_states/session_{user_id}.json"
    if os.path.exists(filepath):
        with open(filepath, "r") as f:
            data = json.load(f)
        exclude_prefixes = ("btn_", "select_")
        for k, v in data.items():
            if not any(k.startswith(prefix) for prefix in exclude_prefixes): 
                st.session_state[k] = v