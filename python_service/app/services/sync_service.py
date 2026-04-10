import json
import os
import sys
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[3]
DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
SYNC_STATE_PATH = DATA_DIR / "sync_state.json"

if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from ingest import run_incremental_ingestion


def _load_json(path: Path, default):
    if not path.exists():
        return default
    try:
        with open(path, "r", encoding="utf-8") as file:
            return json.load(file)
    except Exception:
        return default


def _save_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4)


def _count_json_items(filename: str):
    data = _load_json(RAW_DIR / filename, [])
    return len(data) if isinstance(data, list) else 0


def _has_text_file(filename: str):
    path = RAW_DIR / filename
    if not path.exists():
        return False
    try:
        return bool(path.read_text(encoding="utf-8").strip())
    except Exception:
        return False


def get_sync_status():
    sync_state = _load_json(SYNC_STATE_PATH, {})
    slack_state = sync_state.get("slack", {})
    gmail_state = sync_state.get("gmail", {})
    manual_sync_epoch = int(sync_state.get("app", {}).get("last_manual_sync_epoch", 0) or 0)

    last_slack_ts = slack_state.get("last_ts")
    last_gmail_fetch = gmail_state.get("last_fetch_epoch")
    last_sync_epoch = manual_sync_epoch

    try:
        if last_slack_ts:
            last_sync_epoch = max(last_sync_epoch, int(float(last_slack_ts)))
    except Exception:
        pass

    try:
        if last_gmail_fetch:
            last_sync_epoch = max(last_sync_epoch, int(last_gmail_fetch))
    except Exception:
        pass

    return {
        "last_sync_epoch": last_sync_epoch,
        "last_sync_display": (
            time.strftime("%d %b %Y, %I:%M:%S %p", time.localtime(last_sync_epoch))
            if last_sync_epoch
            else "Not synced yet"
        ),
        "sources": [
            {
                "id": "slack",
                "label": "Slack",
                "status": "Connected" if _count_json_items("slack_messages.json") > 0 else "Idle",
                "count": _count_json_items("slack_messages.json"),
                "detail": f"Last cursor: {last_slack_ts or 'not available'}",
            },
            {
                "id": "gmail",
                "label": "Gmail",
                "status": "Connected" if _count_json_items("gmail_messages.json") > 0 else "Idle",
                "count": _count_json_items("gmail_messages.json"),
                "detail": (
                    f"Last fetch epoch: {last_gmail_fetch}"
                    if last_gmail_fetch
                    else "Fetch state not available"
                ),
            },
            {
                "id": "meeting",
                "label": "Meeting notes",
                "status": "Present" if _has_text_file("meeting_notes.txt") else "Missing",
                "count": 1 if _has_text_file("meeting_notes.txt") else 0,
                "detail": "Static decision context document",
            },
            {
                "id": "final_document",
                "label": "Final document",
                "status": "Present" if _has_text_file("final_document.txt") else "Missing",
                "count": 1 if _has_text_file("final_document.txt") else 0,
                "detail": "Final approved decision artifact",
            },
        ],
        "interval_options": [60, 90, 120],
        "recommended_interval": 90,
    }


def run_sync_now():
    sync_state = _load_json(SYNC_STATE_PATH, {"slack": {}, "gmail": {}, "app": {}})
    current_epoch = int(time.time())
    sync_state.setdefault("app", {})
    sync_state["app"]["last_manual_sync_epoch"] = current_epoch
    _save_json(SYNC_STATE_PATH, sync_state)

    previous_cwd = os.getcwd()
    try:
        os.chdir(BASE_DIR)
        result = run_incremental_ingestion(include_static_docs=False)
    finally:
        os.chdir(previous_cwd)

    status = get_sync_status()
    return {
        "status": "completed",
        "message": (
            f"Sync complete. Slack: {result.get('new_slack', 0)} new, "
            f"Gmail: {result.get('new_gmail', 0)} new."
        ),
        "result": result,
        "sync_status": status,
    }
