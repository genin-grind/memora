import json
import os
import re
import sys
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[3]
DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
UPLOADS_DIR = RAW_DIR / "uploads"
SYNC_STATE_PATH = DATA_DIR / "sync_state.json"

if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from ingest import get_collection
from ingest import ingest_text_file_once
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


def _count_text_collection(kind: str, filename: str):
    count = 1 if _has_text_file(filename) else 0
    upload_dir = UPLOADS_DIR / kind
    if upload_dir.exists():
        count += len([path for path in upload_dir.iterdir() if path.is_file()])
    return count


def _chunk_text(text: str, chunk_size: int = 1200, overlap: int = 150):
    text = str(text or "").strip()
    if not text:
        return []

    chunks = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunks.append(text[start:end])
        if end == len(text):
            break
        start = end - overlap
    return chunks


def _safe_slug(value: str):
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", str(value or "").strip()).strip("_").lower()
    return slug or "upload"


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
                "status": "Present" if _count_text_collection("meeting", "meeting_notes.txt") > 0 else "Missing",
                "count": _count_text_collection("meeting", "meeting_notes.txt"),
                "detail": "Static decision context documents",
            },
            {
                "id": "final_document",
                "label": "Final document",
                "status": "Present" if _count_text_collection("final_document", "final_document.txt") > 0 else "Missing",
                "count": _count_text_collection("final_document", "final_document.txt"),
                "detail": "Final approved decision artifacts",
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


def upload_manual_document(kind: str, filename: str, content: str):
    normalized_kind = (kind or "").strip().lower()
    mapping = {
        "meeting": ("meeting_notes.txt", "meeting", "Meeting notes"),
        "final_document": ("final_document.txt", "final_document", "Final document"),
    }

    if normalized_kind not in mapping:
        raise ValueError("Unsupported upload kind.")

    clean_content = str(content or "").strip()
    if not clean_content:
        raise ValueError("Uploaded content is empty.")

    target_filename, source_name, label = mapping[normalized_kind]
    upload_dir = UPLOADS_DIR / normalized_kind
    upload_dir.mkdir(parents=True, exist_ok=True)
    safe_name = _safe_slug(Path(filename or source_name).stem)
    extension = Path(filename or ".txt").suffix or ".txt"
    stored_filename = f"{int(time.time())}_{safe_name}{extension}"
    target_path = upload_dir / stored_filename
    target_path.write_text(clean_content, encoding="utf-8")

    previous_cwd = os.getcwd()
    try:
        os.chdir(BASE_DIR)
        collection = get_collection()
        chunks = _chunk_text(clean_content)
        ids = [f"{source_name}_{_safe_slug(target_path.stem)}_{index}" for index, _ in enumerate(chunks, start=1)]
        metadatas = [
            {
                "source": source_name,
                "file_name": str(Path("uploads") / normalized_kind / stored_filename),
                "chunk_index": index,
            }
            for index, _ in enumerate(chunks, start=1)
        ]
        if chunks:
            collection.upsert(ids=ids, documents=chunks, metadatas=metadatas)
        chunk_count = len(chunks)
    finally:
        os.chdir(previous_cwd)

    status = get_sync_status()
    return {
        "status": "completed",
        "message": f"{label} uploaded and indexed.",
        "upload": {
            "kind": normalized_kind,
            "filename": filename or target_filename,
            "saved_as": str(Path("uploads") / normalized_kind / stored_filename),
            "chunk_count": chunk_count,
        },
        "sync_status": status,
    }
