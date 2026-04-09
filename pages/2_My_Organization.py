import json
from pathlib import Path
from collections import Counter

import streamlit as st
from utils.auth import require_auth

require_auth()
st.set_page_config(
    page_title="My Organization",
    page_icon="🏢",
    layout="wide",
)

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


def get_user_name(user_id: str) -> str:
    if not user_id:
        return "Unknown"
    return slack_users.get(user_id, user_id)


def unique_slack_people():
    names = []
    for msg in slack_messages:
        if msg.get("user_name"):
            names.append(msg["user_name"])
        else:
            names.append(get_user_name(msg.get("user", "")))
    return sorted(set([n for n in names if n]))


def unique_gmail_senders():
    senders = []
    for msg in gmail_messages:
        sender = str(msg.get("from", "")).strip()
        if sender:
            senders.append(sender)
    return sorted(set(senders))


slack_people = unique_slack_people()
gmail_senders = unique_gmail_senders()

verified_user_name = "Kalyani Ugale"
verified_user_email = "kalyaniugale24@gmail.com"

connected_sources = [
    ("Slack connected", len(slack_messages) > 0),
    ("Gmail connected", len(gmail_messages) > 0),
    ("Meeting notes available", bool(meeting_notes)),
    ("Final decision document available", bool(final_document)),
]

source_status_count = sum(1 for _, ok in connected_sources if ok)
indexed_artifacts = len(slack_messages) + len(gmail_messages) + len(gmail_threads)
if meeting_notes:
    indexed_artifacts += 1
if final_document:
    indexed_artifacts += 1

top_channels = Counter(msg.get("channel", "unknown") for msg in slack_messages if msg.get("channel"))
top_channel_name = top_channels.most_common(1)[0][0] if top_channels else "N/A"

top_subjects = Counter(msg.get("subject", "No subject") for msg in gmail_messages if msg.get("subject"))
top_subject_name = top_subjects.most_common(1)[0][0] if top_subjects else "N/A"

st.markdown(
    """
    <style>
        .block-container {
            padding-top: 1.1rem;
            padding-bottom: 2rem;
        }

        .hero-card {
            background: linear-gradient(135deg, #0f172a, #111827);
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 22px;
            padding: 28px;
            margin-bottom: 18px;
        }

        .hero-title {
            font-size: 2rem;
            font-weight: 700;
            color: white;
            margin-bottom: 6px;
        }

        .hero-subtitle {
            color: #cbd5e1;
            font-size: 0.98rem;
            margin-bottom: 14px;
        }

        .verified-pill {
            display: inline-block;
            background: rgba(34,197,94,0.14);
            color: #86efac;
            border: 1px solid rgba(34,197,94,0.28);
            border-radius: 999px;
            padding: 7px 12px;
            font-size: 0.88rem;
            font-weight: 600;
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
            font-size: 1.7rem;
            font-weight: 700;
        }

        .section-card {
            background: #111827;
            border: 1px solid rgba(255,255,255,0.06);
            border-radius: 20px;
            padding: 18px;
            height: 100%;
        }

        .section-title {
            color: white;
            font-size: 1.05rem;
            font-weight: 700;
            margin-bottom: 14px;
        }

        .status-row {
            display: flex;
            align-items: center;
            justify-content: space-between;
            background: #0b1220;
            border: 1px solid rgba(255,255,255,0.05);
            border-radius: 14px;
            padding: 12px 14px;
            margin-bottom: 10px;
        }

        .status-label {
            color: #e5e7eb;
        }

        .status-ok {
            color: #86efac;
            font-weight: 600;
        }

        .status-pending {
            color: #fca5a5;
            font-weight: 600;
        }

        .person-chip {
            display: inline-block;
            background: #0b1220;
            border: 1px solid rgba(255,255,255,0.06);
            color: #e5e7eb;
            border-radius: 999px;
            padding: 8px 12px;
            margin: 0 8px 8px 0;
            font-size: 0.9rem;
        }

        .insight-card {
            background: #0b1220;
            border: 1px solid rgba(255,255,255,0.05);
            border-radius: 16px;
            padding: 14px;
            margin-bottom: 12px;
        }

        .insight-title {
            color: white;
            font-weight: 700;
            margin-bottom: 6px;
        }

        .insight-text {
            color: #cbd5e1;
            font-size: 0.92rem;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    f"""
    <div class="hero-card">
        <div class="hero-title">🏢 My Organization</div>
        <div class="hero-subtitle">
            Unified visibility into connected communication channels, indexed records, and team participation.
        </div>
        <div class="verified-pill">Verified access for {verified_user_name} · {verified_user_email}</div>
    </div>
    """,
    unsafe_allow_html=True,
)

c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">Slack Messages</div>
            <div class="metric-value">{len(slack_messages)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with c2:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">Gmail Messages</div>
            <div class="metric-value">{len(gmail_messages)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with c3:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">Gmail Threads</div>
            <div class="metric-value">{len(gmail_threads)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with c4:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">Indexed Artifacts</div>
            <div class="metric-value">{indexed_artifacts}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.write("")

left, center, right = st.columns([1.1, 1.1, 1])

with left:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Connected Knowledge Sources</div>', unsafe_allow_html=True)

    for label, ok in connected_sources:
        st.markdown(
            f"""
            <div class="status-row">
                <div class="status-label">{label}</div>
                <div class="{'status-ok' if ok else 'status-pending'}">{'Available' if ok else 'Not available'}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)

with center:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Active Participants</div>', unsafe_allow_html=True)

    st.markdown("**Slack identities**")
    if slack_people:
        for name in slack_people[:12]:
            st.markdown(f'<span class="person-chip">{name}</span>', unsafe_allow_html=True)
    else:
        st.caption("No Slack identities found.")

    st.write("")
    st.markdown("**Gmail senders**")
    if gmail_senders:
        for name in gmail_senders[:12]:
            st.markdown(f'<span class="person-chip">{name}</span>', unsafe_allow_html=True)
    else:
        st.caption("No Gmail senders found.")

    st.markdown("</div>", unsafe_allow_html=True)

with right:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Operational Highlights</div>', unsafe_allow_html=True)

    st.markdown(
        f"""
        <div class="insight-card">
            <div class="insight-title">Coverage</div>
            <div class="insight-text">{source_status_count} of {len(connected_sources)} organizational sources are currently available.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div class="insight-card">
            <div class="insight-title">Primary Slack Channel</div>
            <div class="insight-text">{top_channel_name}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div class="insight-card">
            <div class="insight-title">Top Gmail Subject</div>
            <div class="insight-text">{top_subject_name}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    decision_assets = []
    if meeting_notes:
        decision_assets.append("Meeting Notes")
    if final_document:
        decision_assets.append("Final Decision Document")

    st.markdown(
        f"""
        <div class="insight-card">
            <div class="insight-title">Decision Records</div>
            <div class="insight-text">{", ".join(decision_assets) if decision_assets else "No decision artifacts available."}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("</div>", unsafe_allow_html=True)

st.write("")

bottom_left, bottom_right = st.columns([1.2, 1])

with bottom_left:
    st.markdown("### Executive Summary")
    st.info(
        "This workspace brings together Slack communication, Gmail conversations, meeting notes, "
        "and final decision artifacts into one indexed organizational view."
    )

with bottom_right:
    st.markdown("### Quick Navigation")
    nav1, nav2 = st.columns(2)
    with nav1:
        st.page_link("pages/source_explorer.py", label="Open Source Explorer", icon="🗂️")
    with nav2:
        st.page_link("app.py", label="Go to Main App", icon="🧠")