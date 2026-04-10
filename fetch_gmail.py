import os
import json
import base64
from pathlib import Path
from html import unescape
from datetime import datetime, timezone

from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
DEFAULT_GROUP_EMAIL = os.getenv("GMAIL_GROUP", "memora-labs@googlegroups.com")
RECENT_QUERY_WINDOW = "30d"

RAW_DIR = BASE_DIR / "data" / "raw"
SYNC_STATE_PATH = BASE_DIR / "data" / "sync_state.json"
TOKEN_PATH = BASE_DIR / "token.json"
CREDENTIALS_PATH = BASE_DIR / "credentials.json"


def load_sync_state():
    if not SYNC_STATE_PATH.exists():
        return {"slack": {"last_ts": "0"}, "gmail": {"last_fetch_epoch": 0}}
    with open(SYNC_STATE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_sync_state(state):
    SYNC_STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(SYNC_STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=4)


def load_existing_emails():
    path = RAW_DIR / "gmail_messages.json"
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_emails(emails):
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    with open(RAW_DIR / "gmail_messages.json", "w", encoding="utf-8") as f:
        json.dump(emails, f, indent=4, ensure_ascii=False)


def save_threads(grouped_threads):
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    with open(RAW_DIR / "gmail_threads.json", "w", encoding="utf-8") as f:
        json.dump(grouped_threads, f, indent=4, ensure_ascii=False)


def authenticate_gmail():
    creds = None

    if TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                str(CREDENTIALS_PATH),
                SCOPES,
            )
            creds = flow.run_local_server(port=0)

        with open(TOKEN_PATH, "w", encoding="utf-8") as token_file:
            token_file.write(creds.to_json())

    return build("gmail", "v1", credentials=creds)


def get_header(headers, name):
    for header in headers:
        if header.get("name", "").lower() == name.lower():
            return header.get("value", "")
    return ""


def decode_base64_data(data):
    if not data:
        return ""
    try:
        missing_padding = len(data) % 4
        if missing_padding:
            data += "=" * (4 - missing_padding)
        return base64.urlsafe_b64decode(data.encode("utf-8")).decode(
            "utf-8",
            errors="ignore",
        )
    except Exception:
        return ""


def strip_html_tags(text):
    import re

    text = re.sub(r"(?is)<(script|style).*?>.*?</\1>", "", text)
    text = re.sub(r"(?i)<br\s*/?>", "\n", text)
    text = re.sub(r"(?i)</p>", "\n", text)
    text = re.sub(r"<[^>]+>", "", text)
    return unescape(text).strip()


def extract_body_from_payload(payload):
    plain_text_parts = []
    html_parts = []

    def walk_parts(part):
        mime_type = part.get("mimeType", "")
        body = part.get("body", {})
        data = body.get("data", "")

        if mime_type == "text/plain" and data:
            decoded = decode_base64_data(data)
            if decoded.strip():
                plain_text_parts.append(decoded.strip())

        elif mime_type == "text/html" and data:
            decoded = decode_base64_data(data)
            if decoded.strip():
                html_parts.append(decoded.strip())

        for subpart in part.get("parts", []):
            walk_parts(subpart)

    if payload:
        walk_parts(payload)

    if plain_text_parts:
        return "\n\n".join(plain_text_parts).strip()

    if html_parts:
        return strip_html_tags("\n\n".join(html_parts))

    fallback_data = payload.get("body", {}).get("data", "") if payload else ""
    if fallback_data:
        decoded = decode_base64_data(fallback_data)
        if "<html" in decoded.lower() or "<div" in decoded.lower():
            return strip_html_tags(decoded)
        return decoded.strip()

    return ""


def search_messages(service, query, max_results):
    results = service.users().messages().list(
        userId="me",
        q=query,
        maxResults=max_results,
        includeSpamTrash=True,
    ).execute()
    return results.get("messages", [])


def fetch_group_emails_incremental(service, group_email=None, max_results=50):
    group_email = group_email or DEFAULT_GROUP_EMAIL
    state = load_sync_state()
    queries = [
        f"list:{group_email} newer_than:{RECENT_QUERY_WINDOW}",
        f"(to:{group_email} OR from:{group_email} OR cc:{group_email} OR deliveredto:{group_email}) newer_than:{RECENT_QUERY_WINDOW}",
        f"\"{group_email}\" newer_than:{RECENT_QUERY_WINDOW}",
    ]

    messages_by_id = {}
    used_query = queries[0]

    for query in queries:
        matches = search_messages(service, query, max_results)
        if matches and used_query == queries[0]:
            used_query = query
        for match in matches:
            messages_by_id[match["id"]] = match

    messages = list(messages_by_id.values())

    existing_emails = load_existing_emails()
    existing_ids = {email.get("message_id") for email in existing_emails}

    new_emails = []
    grouped_threads = {}

    for msg in messages:
        msg_id = msg["id"]
        if msg_id in existing_ids:
            continue

        msg_data = service.users().messages().get(
            userId="me",
            id=msg_id,
            format="full",
        ).execute()

        payload = msg_data.get("payload", {})
        headers = payload.get("headers", [])

        subject = get_header(headers, "Subject")
        sender = get_header(headers, "From")
        to_email = get_header(headers, "To")
        cc_email = get_header(headers, "Cc")
        list_id = get_header(headers, "List-Id")
        date = get_header(headers, "Date")
        snippet = msg_data.get("snippet", "")
        thread_id = msg_data.get("threadId", "")
        message_id = msg_data.get("id", "")

        body = extract_body_from_payload(payload)
        if not body.strip():
            body = snippet

        email_item = {
            "source": "gmail",
            "group_email": group_email,
            "query_used": used_query,
            "message_id": message_id,
            "thread_id": thread_id,
            "from": sender,
            "to": to_email,
            "cc": cc_email,
            "list_id": list_id,
            "subject": subject,
            "date": date,
            "snippet": snippet,
            "body": body,
        }

        new_emails.append(email_item)

        if thread_id not in grouped_threads:
            grouped_threads[thread_id] = {
                "thread_id": thread_id,
                "group_email": group_email,
                "subject": subject,
                "messages": [],
            }

        grouped_threads[thread_id]["messages"].append(email_item)

    merged_emails = existing_emails + new_emails
    save_emails(merged_emails)
    save_threads(list(grouped_threads.values()))

    state.setdefault("gmail", {})
    state["gmail"]["last_fetch_epoch"] = int(datetime.now(timezone.utc).timestamp())
    save_sync_state(state)

    print(f"Gmail incremental sync complete. New emails: {len(new_emails)}")
    return new_emails


if __name__ == "__main__":
    service = authenticate_gmail()
    fetch_group_emails_incremental(service)
