import streamlit as st


def init_auth_state():
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "user_email" not in st.session_state:
        st.session_state.user_email = ""
    if "user_name" not in st.session_state:
        st.session_state.user_name = ""
    if "org_name" not in st.session_state:
        st.session_state.org_name = ""
    if "user_role" not in st.session_state:
        st.session_state.user_role = "Member"


def require_auth():
    init_auth_state()

    if not st.session_state.logged_in:
        st.warning("Please sign in to continue.")
        st.page_link("pages/1_Login.py", label="Go to Login", icon="🔐")
        st.stop()