import time
import streamlit as st
from ingest import run_incremental_ingestion


def render_common_sidebar():
    """Render the common sidebar with profile, sync controls, and auto-sync logic."""
    if "last_sync_time" not in st.session_state:
        st.session_state.last_sync_time = 0

    if "auto_sync_interval" not in st.session_state:
        st.session_state.auto_sync_interval = 90

    with st.sidebar:
        st.markdown("---")
        st.markdown("### 👤 Profile")
        st.write(f"**{st.session_state.get('user_name', '')}**")
        st.caption(st.session_state.get("user_email", ""))
        st.caption(f"Role: {st.session_state.get('user_role', 'Member')}")

        if st.button("Logout"):
            st.session_state.logged_in = False
            st.session_state.user_email = ""
            st.session_state.user_name = ""
            st.session_state.org_name = ""
            st.session_state.user_role = "Member"
            st.switch_page("pages/1_Login.py")

        st.markdown("---")
        st.markdown("### Sync Control")

        if st.button("Sync Now", use_container_width=True):
            with st.spinner("Syncing Slack and Gmail..."):
                sync_result = run_incremental_ingestion(include_static_docs=False)
                st.session_state.last_sync_time = time.time()

            st.success(
                f"Sync complete | Slack: {sync_result['new_slack']} new | "
                f"Gmail: {sync_result['new_gmail']} new"
            )

        st.session_state.auto_sync_interval = st.selectbox(
            "Auto-sync interval",
            options=[60, 90, 120],
            index=[60, 90, 120].index(st.session_state.get("auto_sync_interval", 90)),
            format_func=lambda x: f"{x} sec",
        )

        st.caption(
            f"Last sync: {time.strftime('%H:%M:%S', time.localtime(st.session_state.last_sync_time)) if st.session_state.last_sync_time else 'Not synced yet'}"
        )
