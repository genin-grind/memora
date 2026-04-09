import os
import json
import base64
from html import unescape

from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

load_dotenv()

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
DEFAULT_GROUP_EMAIL = os.getenv("GMAIL_GROUP", "memora-labs@googlegroups.com")


def authenticate_gmail():
    creds = None

    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json",
                SCOPES,
            )
            creds = flow.run_local_server(port=0)

        with open("token.json", "w", encoding="utf-8") as token_file:
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


def fetch_group_emails(service, group_email: str | None = None, max_results: int = 50) -> list:
    group_email = group_email or DEFAULT_GROUP_EMAIL

    primary_query = f"list:{group_email}"
    fallback_query = f"(to:{group_email} OR from:{group_email})"

    messages = search_messages(service, primary_query, max_results)
    used_query = primary_query

    if not messages:
        messages = search_messages(service, fallback_query, max_results)
        used_query = fallback_query

    if not messages:
        raise ValueError(f"No emails found for group {group_email}")

    emails = []
    grouped_threads = {}

    for msg in messages:
        msg_data = service.users().messages().get(
            userId="me",
            id=msg["id"],
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

        emails.append(email_item)

        if thread_id not in grouped_threads:
            grouped_threads[thread_id] = {
                "thread_id": thread_id,
                "group_email": group_email,
                "subject": subject,
                "messages": [],
            }

        grouped_threads[thread_id]["messages"].append(email_item)

    output_dir = os.path.join("data", "raw")
    os.makedirs(output_dir, exist_ok=True)

    emails_path = os.path.join(output_dir, "gmail_messages.json")
    threads_path = os.path.join(output_dir, "gmail_threads.json")

    with open(emails_path, "w", encoding="utf-8") as f:
        json.dump(emails, f, indent=4, ensure_ascii=False)

    with open(threads_path, "w", encoding="utf-8") as f:
        json.dump(list(grouped_threads.values()), f, indent=4, ensure_ascii=False)

    print(f"Saved {len(emails)} Gmail messages to {emails_path}")
    print(f"Saved {len(grouped_threads)} Gmail threads to {threads_path}")

    return list(grouped_threads.values())


if __name__ == "__main__":
    service = authenticate_gmail()
    fetch_group_emails(service)