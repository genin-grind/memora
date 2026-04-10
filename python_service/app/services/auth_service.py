import json
import os
import re
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parents[3]
DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
ORG_CONFIG_PATH = DATA_DIR / "org_config.json"
load_dotenv(BASE_DIR / ".env")

MEMORA_ACCESS_KEY = os.getenv("MEMORA_ACCESS_KEY", "Memora-Access-2026")


def _safe_read_json(path: Path, default):
    if not path.exists():
        return default
    try:
        with open(path, "r", encoding="utf-8") as file:
            return json.load(file)
    except Exception:
        return default


def load_org_config():
    default = {
        "org_name": "Memora Labs",
        "allowed_domains": ["gmail.com"],
        "allowed_emails": [],
    }

    if not ORG_CONFIG_PATH.exists():
        return default

    config = _safe_read_json(ORG_CONFIG_PATH, default)
    return config if isinstance(config, dict) else default


def extract_email(value: str) -> str:
    if not value:
        return ""
    match = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", value)
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
    gmail_messages = _safe_read_json(RAW_DIR / "gmail_messages.json", [])

    for message in gmail_messages:
        for field_name in ["from", "to", "cc"]:
            field_value = extract_email(message.get(field_name, ""))
            if field_value:
                known_emails.add(field_value)

    return known_emails


def collect_known_people():
    people = {}
    gmail_messages = _safe_read_json(RAW_DIR / "gmail_messages.json", [])

    for message in gmail_messages:
        sender_raw = message.get("from", "")
        sender_email = extract_email(sender_raw)
        sender_name = extract_name_from_sender(sender_raw)
        if sender_email:
            people[sender_email] = sender_name

    return people


def validate_org_user(email: str, access_key: str):
    org_config = load_org_config()
    known_org_emails = collect_known_org_emails()
    known_people = collect_known_people()

    clean_email = email.lower().strip()
    if not clean_email or "@" not in clean_email:
        return False, "Enter a valid organization email.", None

    if not str(access_key or "").strip():
        return False, "Enter your Memora access key.", None

    if str(access_key).strip() != MEMORA_ACCESS_KEY:
        return False, "Invalid Memora access key.", None

    domain = clean_email.split("@")[-1].lower()
    allowed_domains = [item.lower() for item in org_config.get("allowed_domains", [])]
    allowed_emails = [item.lower() for item in org_config.get("allowed_emails", [])]

    if allowed_domains and domain not in allowed_domains:
        return False, "Your email domain is not allowed for this organization.", None

    if allowed_emails and clean_email not in allowed_emails:
        return False, "This email is not registered for organization access.", None

    if known_org_emails and clean_email not in known_org_emails and clean_email not in allowed_emails:
        return False, "This email was not found in the organization memory sources.", None

    display_name = known_people.get(
        clean_email,
        clean_email.split("@")[0].replace(".", " ").title(),
    )
    user = {
      "email": clean_email,
      "name": display_name,
      "org_name": org_config.get("org_name", "Organization"),
      "role": "Member",
    }
    return True, "Access granted.", user
