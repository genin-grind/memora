import json
from collections import Counter
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[3]
DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
UPLOADS_DIR = RAW_DIR / "uploads"
ORG_CONFIG_PATH = DATA_DIR / "org_config.json"


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


def _collect_text_documents(kind: str, primary_filename: str):
    documents = []
    primary_path = RAW_DIR / primary_filename
    primary_text = _load_text_file(primary_path)
    if primary_text:
        documents.append({"file_name": primary_filename, "content": primary_text})

    upload_dir = UPLOADS_DIR / kind
    if upload_dir.exists():
        for path in sorted(upload_dir.iterdir()):
            if path.is_file():
                content = _load_text_file(path)
                if content:
                    documents.append(
                        {
                            "file_name": str(Path("uploads") / kind / path.name),
                            "content": content,
                        }
                    )
    return documents


def _load_org_name() -> str:
    default_name = "Memora Labs"
    if not ORG_CONFIG_PATH.exists():
        return default_name
    try:
        with open(ORG_CONFIG_PATH, "r", encoding="utf-8") as file:
            config = json.load(file)
        if isinstance(config, dict):
            return config.get("org_name", default_name)
    except Exception:
        return default_name
    return default_name


def _get_user_name(user_id: str, slack_users: dict) -> str:
    if not user_id:
        return "Unknown"
    return slack_users.get(user_id, user_id)


def _collect_slack_people(slack_messages, slack_users):
    names = []
    for message in slack_messages:
        explicit_name = str(message.get("user_name", "")).strip()
        if explicit_name:
            names.append(explicit_name)
            continue
        names.append(_get_user_name(str(message.get("user", "")).strip(), slack_users))
    return sorted({name for name in names if name and name != "Unknown"})


def _collect_gmail_senders(gmail_messages):
    senders = []
    for message in gmail_messages:
        sender = str(message.get("from", "")).strip()
        if sender:
            senders.append(sender)
    return sorted(set(senders))


def _top_counter_entry(counter, fallback_label):
    if not counter:
        return {"label": fallback_label, "count": 0}
    label, count = counter.most_common(1)[0]
    return {"label": label, "count": count}


def get_org_summary():
    slack_messages = _load_json_file(RAW_DIR / "slack_messages.json", [])
    gmail_messages = _load_json_file(RAW_DIR / "gmail_messages.json", [])
    gmail_threads = _load_json_file(RAW_DIR / "gmail_threads.json", [])
    slack_users = _load_json_file(RAW_DIR / "slack_users.json", {})
    meeting_notes = _collect_text_documents("meeting", "meeting_notes.txt")
    final_documents = _collect_text_documents("final_document", "final_document.txt")

    slack_people = _collect_slack_people(slack_messages, slack_users)
    gmail_senders = _collect_gmail_senders(gmail_messages)

    connected_sources = [
        {
            "id": "slack",
            "label": "Slack workspace",
            "available": len(slack_messages) > 0,
            "detail": f"{len(slack_messages)} messages indexed",
            "weight": "Early discussion",
        },
        {
            "id": "gmail",
            "label": "Gmail archive",
            "available": len(gmail_messages) > 0,
            "detail": f"{len(gmail_messages)} messages captured",
            "weight": "Formal context",
        },
        {
            "id": "meeting",
            "label": "Meeting notes",
            "available": bool(meeting_notes),
            "detail": f"{len(meeting_notes)} transcript file(s)" if meeting_notes else "Transcript missing",
            "weight": "Consensus layer",
        },
        {
            "id": "document",
            "label": "Final document",
            "available": bool(final_documents),
            "detail": f"{len(final_documents)} decision artifact(s)" if final_documents else "Decision artifact missing",
            "weight": "Highest authority",
        },
    ]

    indexed_artifacts = len(slack_messages) + len(gmail_messages) + len(gmail_threads)
    decision_record_count = 0
    indexed_artifacts += len(meeting_notes)
    indexed_artifacts += len(final_documents)
    decision_record_count += len(meeting_notes) + len(final_documents)

    top_channels = Counter(
        str(message.get("channel", "")).strip()
        for message in slack_messages
        if str(message.get("channel", "")).strip()
    )
    top_subjects = Counter(
        str(message.get("subject", "")).strip()
        for message in gmail_messages
        if str(message.get("subject", "")).strip()
    )

    available_source_count = sum(1 for source in connected_sources if source["available"])
    coverage_score = round((available_source_count / len(connected_sources)) * 100)

    return {
        "org_name": _load_org_name(),
        "slack_messages": len(slack_messages),
        "gmail_messages": len(gmail_messages),
        "gmail_threads": len(gmail_threads),
        "indexed_artifacts": indexed_artifacts,
        "has_meeting_notes": bool(meeting_notes),
        "has_final_document": bool(final_documents),
        "coverage_score": coverage_score,
        "available_source_count": available_source_count,
        "source_count": len(connected_sources),
        "decision_record_count": decision_record_count,
        "participant_count": len(set(slack_people + gmail_senders)),
        "slack_people": slack_people[:12],
        "gmail_senders": gmail_senders[:12],
        "connected_sources": connected_sources,
        "top_channel": _top_counter_entry(top_channels, "No Slack activity yet"),
        "top_subject": _top_counter_entry(top_subjects, "No Gmail activity yet"),
        "decision_assets": [
            asset
            for asset, available in (
                ("Meeting Notes", bool(meeting_notes)),
                ("Final Decision Document", bool(final_documents)),
            )
            if available
        ],
        "highlights": [
            {
                "label": "Coverage",
                "value": f"{available_source_count} of {len(connected_sources)} sources live",
                "tone": "success",
            },
            {
                "label": "Primary Slack channel",
                "value": _top_counter_entry(top_channels, "No Slack activity yet")["label"],
                "tone": "neutral",
            },
            {
                "label": "Top Gmail subject",
                "value": _top_counter_entry(top_subjects, "No Gmail activity yet")["label"],
                "tone": "neutral",
            },
            {
                "label": "Decision records",
                "value": ", ".join(
                    [
                        asset
                        for asset, available in (
                            ("Meeting Notes", bool(meeting_notes)),
                            ("Final Document", bool(final_documents)),
                        )
                        if available
                    ]
                )
                or "No decision artifacts available",
                "tone": "neutral",
            },
        ],
    }


def get_source_status():
    summary = get_org_summary()
    return {"sources": summary["connected_sources"]}
