import json
import re
from pathlib import Path

import streamlit as st

from utils.sidebar import render_common_sidebar

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "data" / "raw"
DATA_DIR = BASE_DIR / "data"
ORG_CONFIG_PATH = DATA_DIR / "org_config.json"

st.set_page_config(page_title="Login | Memora", page_icon="🔐", layout="wide")


def initialize_session():
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


def safe_read_json(path: Path):
    if not path.exists():
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def load_org_config():
    default = {
        "org_name": "Memora Labs",
        "allowed_domains": ["gmail.com"],
        "allowed_emails": [],
    }

    if not ORG_CONFIG_PATH.exists():
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        with open(ORG_CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(default, f, indent=4, ensure_ascii=False)
        return default

    try:
        with open(ORG_CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def extract_email(value: str) -> str:
    if not value:
        return ""
    match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', value)
    return match.group(0).lower() if match else ""


def extract_name_from_sender(value: str) -> str:
    if not value:
        return ""
    email = extract_email(value)
    cleaned = value.replace(f"<{email}>", "").strip() if email else value.strip()
    if cleaned:
        return cleaned
    if email:
        return email.split("@")[0].replace(".", " ").title()
    return "Unknown"


def collect_known_org_emails():
    known_emails = set()
    gmail_messages = safe_read_json(RAW_DIR / "gmail_messages.json")

    for msg in gmail_messages:
        sender = extract_email(msg.get("from", ""))
        to_email = extract_email(msg.get("to", ""))
        cc_email = extract_email(msg.get("cc", ""))

        if sender:
            known_emails.add(sender)
        if to_email:
            known_emails.add(to_email)
        if cc_email:
            known_emails.add(cc_email)

    return known_emails


def collect_known_people():
    people = {}
    gmail_messages = safe_read_json(RAW_DIR / "gmail_messages.json")

    for msg in gmail_messages:
        sender_raw = msg.get("from", "")
        sender_email = extract_email(sender_raw)
        sender_name = extract_name_from_sender(sender_raw)
        if sender_email:
            people[sender_email] = sender_name

    return people


def is_allowed_user(email: str, org_config: dict, known_org_emails: set):
    email = email.lower().strip()
    if not email or "@" not in email:
        return False, "Enter a valid organization email."

    domain = email.split("@")[-1].lower()
    allowed_domains = [d.lower() for d in org_config.get("allowed_domains", [])]
    allowed_emails = [e.lower() for e in org_config.get("allowed_emails", [])]

    if allowed_domains and domain not in allowed_domains:
        return False, "Your email domain is not allowed for this organization."

    if allowed_emails and email not in allowed_emails:
        return False, "This email is not registered for organization access."

    if known_org_emails and email not in known_org_emails and email not in allowed_emails:
        return False, "This email was not found in the organization memory sources."

    return True, "Access granted."


initialize_session()
org_config = load_org_config()
known_org_emails = collect_known_org_emails()
known_people = collect_known_people()

# Only show sidebar if user is already logged in
if st.session_state.get("logged_in"):
    render_common_sidebar()

st.markdown("""
<style>
div[data-testid="stVerticalBlockBorderWrapper"] {
    background: rgba(255,255,255,0.03);
    border-radius: 18px;
}

.hero-box {
    padding: 1.6rem 1.8rem;
    border-radius: 22px;
    background: linear-gradient(135deg, rgba(99,102,241,0.16), rgba(16,185,129,0.10));
    border: 1px solid rgba(255,255,255,0.08);
    margin-bottom: 1rem;
}

.hero-title {
    font-size: 2.1rem;
    font-weight: 800;
    margin-bottom: 0.25rem;
}

.hero-subtitle {
    color: #b8bfd0;
    font-size: 0.98rem;
}
</style>
""", unsafe_allow_html=True)

st.markdown(
    f"""
    <div class="hero-box">
        <div class="hero-title">🔐 Secure Organization Access</div>
        <div class="hero-subtitle">
            Access is restricted to verified members of <b>{org_config.get("org_name", "Organization")}</b>.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

left, right = st.columns([1.15, 1], gap="large")

with left:
    with st.container(border=True):
        st.markdown("### Sign in with your organization email")

        email = st.text_input(
            "Organization Email",
            value=st.session_state.user_email,
            placeholder="name@company.com",
        )

        if st.button("Verify Access", use_container_width=True):
            clean_email = email.strip().lower()
            allowed, message = is_allowed_user(clean_email, org_config, known_org_emails)

            if not allowed:
                st.error(message)
            else:
                display_name = known_people.get(
                    clean_email,
                    clean_email.split("@")[0].replace(".", " ").title()
                )
                st.session_state.logged_in = True
                st.session_state.user_email = clean_email
                st.session_state.user_name = display_name
                st.session_state.org_name = org_config.get("org_name", "Organization")
                st.session_state.user_role = "Member"

                st.switch_page("pages/2_My_Organization.py")

with right:
    with st.container(border=True):
        st.markdown("### Access policy")
        st.write("A user can enter only if:")
        st.write("- the email matches the organization domain")
        st.write("- the email is allowed in the org configuration")
        st.write("- the identity exists in organization memory sources")

        st.markdown("---")
        st.markdown("### Organization")
        st.write(f"**Name:** {org_config.get('org_name', 'Organization')}")
        st.write(f"**Allowed domains:** {', '.join(org_config.get('allowed_domains', [])) or '—'}")
        st.write(f"**Known org identities detected:** {len(known_org_emails)}")

        if st.session_state.logged_in:
            st.markdown("---")
            st.success(f"Logged in as {st.session_state.user_name}")
            st.write(f"**Email:** {st.session_state.user_email}")
            st.write(f"**Org:** {st.session_state.org_name}")

            if st.button("Log out", use_container_width=True):
                st.session_state.logged_in = False
                st.session_state.user_email = ""
                st.session_state.user_name = ""
                st.session_state.org_name = ""
                st.session_state.user_role = "Member"
                st.rerun()
