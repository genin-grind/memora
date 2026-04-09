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
        st.markdown(
            """
            <style>
                .guard-box {
                    max-width: 760px;
                    margin: 5rem auto;
                    padding: 1.7rem 1.9rem;
                    border-radius: 22px;
                    background: rgba(255,255,255,0.03);
                    border: 1px solid rgba(255,255,255,0.08);
                    text-align: center;
                }
                .guard-title {
                    font-size: 2rem;
                    font-weight: 800;
                    margin-bottom: 0.5rem;
                }
                .guard-subtitle {
                    color: #b8bfd0;
                    font-size: 1rem;
                    margin-bottom: 1rem;
                }
            </style>
            <div class="guard-box">
                <div class="guard-title">🔒 Restricted Organizational Access</div>
                <div class="guard-subtitle">
                    This workspace contains protected organizational memory and is available only to verified members.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.warning("You must sign in with a verified organization identity to continue.")
        st.page_link("pages/1_Login.py", label="Go to Login", icon="🔐")
        st.stop()