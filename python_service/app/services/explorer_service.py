import json
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[3]
RAW_DIR = BASE_DIR / "data" / "raw"


def _load_json_file(path: Path, default):
    if not path.exists():
        return default
    try:
        with open(path, "r", encoding="utf-8") as file:
            return json.load(file)
    except Exception:
        return default


def _load_text_file(path: Path) -> str:
    if not path.exists():
        return ""
    try:
        return path.read_text(encoding="utf-8").strip()
    except Exception:
        return ""


def _short_text(text: str, limit: int = 240) -> str:
    compact = " ".join(str(text or "").split())
    if len(compact) <= limit:
        return compact
    return compact[: limit - 3].rstrip() + "..."


def _slack_records(slack_messages, slack_users):
    records = []
    for index, message in enumerate(
        sorted(slack_messages, key=lambda item: float(item.get("ts", "0")), reverse=True)
    ):
        user_name = str(message.get("user_name", "")).strip() or slack_users.get(
            str(message.get("user", "")).strip(),
            str(message.get("user", "")).strip() or "Unknown",
        )
        text = str(message.get("text", "")).strip()
        records.append(
            {
                "id": f"slack-{index}",
                "source": "slack",
                "title": user_name or "Unknown participant",
                "meta": f"#{message.get('channel', 'unknown')} · {message.get('ts', 'N/A')}",
                "snippet": _short_text(text, 180),
                "content": text,
                "badges": [message.get("channel", "Slack"), "Slack"],
                "search_text": " ".join(
                    [
                        str(message.get("channel", "")),
                        str(user_name),
                        text,
                    ]
                ).lower(),
            }
        )
    return records


def _gmail_records(gmail_messages):
    records = []
    for index, message in enumerate(
        sorted(gmail_messages, key=lambda item: str(item.get("date", "")), reverse=True)
    ):
        body = str(message.get("body", "")).strip()
        sender = str(message.get("from", "")).strip() or "Unknown sender"
        subject = str(message.get("subject", "")).strip() or "No subject"
        records.append(
            {
                "id": f"gmail-{index}",
                "source": "gmail",
                "title": subject,
                "meta": f"{sender} · {message.get('date', 'N/A')}",
                "snippet": _short_text(body, 220),
                "content": body,
                "badges": ["Gmail", sender],
                "search_text": " ".join(
                    [
                        sender,
                        str(message.get("to", "")),
                        subject,
                        body,
                    ]
                ).lower(),
            }
        )
    return records


def _document_record(source_id: str, title: str, filename: str, content: str, badge: str):
    return {
        "id": source_id,
        "source": source_id,
        "title": title,
        "meta": filename,
        "snippet": _short_text(content, 800),
        "content": content,
        "badges": [badge, "Document"],
        "search_text": content.lower(),
    }


def get_explorer_workspace():
    slack_messages = _load_json_file(RAW_DIR / "slack_messages.json", [])
    gmail_messages = _load_json_file(RAW_DIR / "gmail_messages.json", [])
    gmail_threads = _load_json_file(RAW_DIR / "gmail_threads.json", [])
    slack_users = _load_json_file(RAW_DIR / "slack_users.json", {})
    meeting_notes = _load_text_file(RAW_DIR / "meeting_notes.txt")
    final_document = _load_text_file(RAW_DIR / "final_document.txt")

    slack_records = _slack_records(slack_messages, slack_users)
    gmail_records = _gmail_records(gmail_messages)
    meeting_records = (
        [
            _document_record(
                "meeting",
                "Meeting Notes",
                "meeting_notes.txt",
                meeting_notes,
                "Meeting",
            )
        ]
        if meeting_notes
        else []
    )
    final_document_records = (
        [
            _document_record(
                "final_document",
                "Final Decision Document",
                "final_document.txt",
                final_document,
                "Final",
            )
        ]
        if final_document
        else []
    )

    return {
        "metrics": {
            "slack_messages": len(slack_messages),
            "gmail_messages": len(gmail_messages),
            "gmail_threads": len(gmail_threads),
            "indexed_sources": len(slack_records)
            + len(gmail_records)
            + len(meeting_records)
            + len(final_document_records),
        },
        "collections": {
            "slack": slack_records,
            "gmail": gmail_records,
            "meeting": meeting_records,
            "final_document": final_document_records,
        },
    }
