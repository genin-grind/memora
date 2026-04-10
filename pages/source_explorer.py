import json
from pathlib import Path

import streamlit as st

st.set_page_config(
    page_title="Source Explorer",
    page_icon="🗂️",
    layout="wide",
)

from utils.auth import require_auth

require_auth()

with st.sidebar:
    st.markdown("---")
    st.markdown("### 👤 Profile")
    st.write(f"**{st.session_state.user_name}**")
    st.caption(st.session_state.user_email)
    st.caption(f"Role: {st.session_state.user_role}")

    if st.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.user_email = ""
        st.session_state.user_name = ""
        st.session_state.org_name = ""
        st.session_state.user_role = "Member"
        st.switch_page("pages/1_Login.py")

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "data" / "raw"


def load_json_file(path: Path, default):
    if not path.exists():
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def load_text_file(path: Path) -> str:
    if not path.exists():
        return ""
    try:
        return path.read_text(encoding="utf-8").strip()
    except Exception:
        return ""


slack_messages = load_json_file(RAW_DIR / "slack_messages.json", [])
gmail_messages = load_json_file(RAW_DIR / "gmail_messages.json", [])
gmail_threads = load_json_file(RAW_DIR / "gmail_threads.json", [])
slack_users = load_json_file(RAW_DIR / "slack_users.json", {})
meeting_notes = load_text_file(RAW_DIR / "meeting_notes.txt")
final_document = load_text_file(RAW_DIR / "final_document.txt")


page_size = 5

if "page_slack" not in st.session_state:
    st.session_state.page_slack = 1
if "page_gmail" not in st.session_state:
    st.session_state.page_gmail = 1
if "page_meeting" not in st.session_state:
    st.session_state.page_meeting = 1
if "page_final" not in st.session_state:
    st.session_state.page_final = 1


def get_user_name(user_id: str) -> str:
    if not user_id:
        return "Unknown"
    return slack_users.get(user_id, user_id)


def short_text(text: str, limit: int = 180) -> str:
    text = " ".join((text or "").split())
    if len(text) <= limit:
        return text
    return text[:limit].rstrip() + "..."


st.markdown(
    """
    <style>
        .block-container {
            padding-top: 1.1rem;
            padding-bottom: 2rem;
        }

        .hero {
            background: linear-gradient(135deg, #0f172a, #111827);
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 22px;
            padding: 26px 28px;
            margin-bottom: 18px;
        }

        .hero-title {
            font-size: 2rem;
            font-weight: 700;
            color: white;
            margin-bottom: 4px;
        }

        .hero-sub {
            color: #cbd5e1;
            font-size: 0.98rem;
        }

        .metric-card {
            background: #0f172a;
            border: 1px solid rgba(255,255,255,0.06);
            border-radius: 18px;
            padding: 18px;
            text-align: center;
        }

        .metric-label {
            color: #94a3b8;
            font-size: 0.85rem;
            margin-bottom: 8px;
        }

        .metric-value {
            color: white;
            font-size: 1.75rem;
            font-weight: 700;
        }

        .panel {
            background: #111827;
            border: 1px solid rgba(255,255,255,0.06);
            border-radius: 20px;
            padding: 18px;
        }

        .panel-title {
            color: white;
            font-size: 1.05rem;
            font-weight: 700;
            margin-bottom: 12px;
        }

        .record-card {
            background: #0b1220;
            border: 1px solid rgba(255,255,255,0.05);
            border-radius: 16px;
            padding: 14px;
            margin-bottom: 12px;
        }

        .record-title {
            font-weight: 700;
            color: white;
            margin-bottom: 6px;
        }

        .record-meta {
            color: #94a3b8;
            font-size: 0.84rem;
            margin-bottom: 8px;
        }

        .record-text {
            color: #e5e7eb;
            font-size: 0.94rem;
            line-height: 1.5;
        }

        .badge {
            display: inline-block;
            padding: 5px 10px;
            border-radius: 999px;
            font-size: 0.78rem;
            font-weight: 600;
            margin-right: 6px;
            margin-bottom: 6px;
        }

        .badge-slack {
            background: rgba(168,85,247,0.16);
            color: #d8b4fe;
            border: 1px solid rgba(168,85,247,0.3);
        }

        .badge-gmail {
            background: rgba(239,68,68,0.14);
            color: #fca5a5;
            border: 1px solid rgba(239,68,68,0.28);
        }

        .badge-meeting {
            background: rgba(59,130,246,0.14);
            color: #93c5fd;
            border: 1px solid rgba(59,130,246,0.28);
        }

        .badge-final {
            background: rgba(16,185,129,0.14);
            color: #86efac;
            border: 1px solid rgba(16,185,129,0.28);
        }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="hero">
        <div class="hero-title">🗂️ Source Explorer</div>
        <div class="hero-sub">
            Explore Slack, Gmail, meeting notes, and final decision artifacts from one organized workspace.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

m1, m2, m3, m4 = st.columns(4)
with m1:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">Slack Messages</div>
            <div class="metric-value">{len(slack_messages)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with m2:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">Gmail Messages</div>
            <div class="metric-value">{len(gmail_messages)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with m3:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">Gmail Threads</div>
            <div class="metric-value">{len(gmail_threads)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with m4:
    indexed = len(slack_messages) + len(gmail_messages)
    if meeting_notes:
        indexed += 1
    if final_document:
        indexed += 1
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">Indexed Sources</div>
            <div class="metric-value">{indexed}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.write("")

left, right = st.columns([1, 2])

with left:
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown('<div class="panel-title">Filters</div>', unsafe_allow_html=True)

    source_type = st.selectbox(
        "Source Type",
        ["All", "Slack", "Gmail", "Meeting Notes", "Final Document"],
    )

    search_text = st.text_input("Search", placeholder="Search text, subject, sender, user...")

    show_full_text = st.toggle("Show full text in cards", value=False)

    st.markdown("---")
    st.markdown("**Pagination**")
    st.markdown("Each source displays 10 results per page.")

    st.markdown("</div>", unsafe_allow_html=True)

with right:
    tabs = st.tabs(["Slack", "Gmail", "Meeting Notes", "Final Document"])

    with tabs[0]:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown('<div class="panel-title">Slack Messages</div>', unsafe_allow_html=True)

        filtered_slack = []
        for msg in slack_messages:
            user_name = msg.get("user_name") or get_user_name(msg.get("user", ""))
            haystack = " ".join(
                [
                    str(msg.get("channel", "")),
                    str(user_name),
                    str(msg.get("text", "")),
                ]
            ).lower()

            if search_text and search_text.lower() not in haystack:
                continue
            filtered_slack.append(msg)

        if source_type not in ["All", "Slack"]:
            st.info("Select Slack in the filter panel to view Slack records here.")
        elif not filtered_slack:
            st.info("No Slack messages found.")
        else:
            total_pages = (len(filtered_slack) + page_size - 1) // page_size
            start = (st.session_state.page_slack - 1) * page_size
            end = start + page_size
            
            for msg in filtered_slack[start:end]:
                user_name = msg.get("user_name") or get_user_name(msg.get("user", ""))
                text = msg.get("text", "")
                preview = text if show_full_text else short_text(text)

                st.markdown(
                    f"""
                    <div class="record-card">
                        <div class="record-title">
                            <span class="badge badge-slack">Slack</span> {user_name}
                        </div>
                        <div class="record-meta">
                            Channel: {msg.get("channel", "N/A")} | Timestamp: {msg.get("ts", "N/A")}
                        </div>
                        <div class="record-text">{preview}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            
            st.markdown("---")
            col1, col2, col3 = st.columns([1, 2, 1])
            with col1:
                if st.button("← Previous", key="slack_prev", disabled=st.session_state.page_slack == 1):
                    st.session_state.page_slack -= 1
                    st.rerun()
            with col2:
                st.markdown(f"<div style='text-align:center; color: #9aa4b2;'>Page {st.session_state.page_slack} of {total_pages}</div>", unsafe_allow_html=True)
            with col3:
                if st.button("Next →", key="slack_next", disabled=st.session_state.page_slack == total_pages):
                    st.session_state.page_slack += 1
                    st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

    with tabs[1]:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown('<div class="panel-title">Gmail Messages</div>', unsafe_allow_html=True)

        filtered_gmail = []
        for msg in gmail_messages:
            haystack = " ".join(
                [
                    str(msg.get("from", "")),
                    str(msg.get("to", "")),
                    str(msg.get("subject", "")),
                    str(msg.get("body", "")),
                ]
            ).lower()

            if search_text and search_text.lower() not in haystack:
                continue
            filtered_gmail.append(msg)

        if source_type not in ["All", "Gmail"]:
            st.info("Select Gmail in the filter panel to view Gmail records here.")
        elif not filtered_gmail:
            st.info("No Gmail messages found.")
        else:
            total_pages = (len(filtered_gmail) + page_size - 1) // page_size
            start = (st.session_state.page_gmail - 1) * page_size
            end = start + page_size
            
            for msg in filtered_gmail[start:end]:
                body = msg.get("body", "")
                preview = body if show_full_text else short_text(body)

                st.markdown(
                    f"""
                    <div class="record-card">
                        <div class="record-title">
                            <span class="badge badge-gmail">Gmail</span> {msg.get("subject", "No subject")}
                        </div>
                        <div class="record-meta">
                            From: {msg.get("from", "N/A")} | Date: {msg.get("date", "N/A")}
                        </div>
                        <div class="record-text">{preview}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            
            st.markdown("---")
            col1, col2, col3 = st.columns([1, 2, 1])
            with col1:
                if st.button("← Previous", key="gmail_prev", disabled=st.session_state.page_gmail == 1):
                    st.session_state.page_gmail -= 1
                    st.rerun()
            with col2:
                st.markdown(f"<div style='text-align:center; color: #9aa4b2;'>Page {st.session_state.page_gmail} of {total_pages}</div>", unsafe_allow_html=True)
            with col3:
                if st.button("Next →", key="gmail_next", disabled=st.session_state.page_gmail == total_pages):
                    st.session_state.page_gmail += 1
                    st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

    with tabs[2]:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown('<div class="panel-title">Meeting Notes</div>', unsafe_allow_html=True)

        if source_type not in ["All", "Meeting Notes"]:
            st.info("Select Meeting Notes in the filter panel to view this section.")
        elif not meeting_notes:
            st.info("No meeting notes file found.")
        else:
            content = meeting_notes
            if search_text and search_text.lower() not in content.lower():
                st.info("No matching content found in meeting notes.")
            else:
                preview = content if show_full_text else short_text(content, 1200)
                st.markdown(
                    f"""
                    <div class="record-card">
                        <div class="record-title">
                            <span class="badge badge-meeting">Meeting Notes</span> meeting_notes.txt
                        </div>
                        <div class="record-meta">Text artifact</div>
                        <div class="record-text">{preview}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        st.markdown("</div>", unsafe_allow_html=True)

    with tabs[3]:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown('<div class="panel-title">Final Decision Document</div>', unsafe_allow_html=True)

        if source_type not in ["All", "Final Document"]:
            st.info("Select Final Document in the filter panel to view this section.")
        elif not final_document:
            st.info("No final document file found.")
        else:
            content = final_document
            if search_text and search_text.lower() not in content.lower():
                st.info("No matching content found in final document.")
            else:
                preview = content if show_full_text else short_text(content, 1200)
                st.markdown(
                    f"""
                    <div class="record-card">
                        <div class="record-title">
                            <span class="badge badge-final">Final Document</span> final_document.txt
                        </div>
                        <div class="record-meta">Text artifact</div>
                        <div class="record-text">{preview}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        st.markdown("</div>", unsafe_allow_html=True)