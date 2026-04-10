import json
import os
from pathlib import Path
from typing import List

import chromadb
from chromadb.api.types import EmbeddingFunction, Documents, Embeddings
from dotenv import load_dotenv
from google import genai

from fetch_slack import fetch_channel_messages_incremental
from fetch_gmail import authenticate_gmail, fetch_group_emails_incremental

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
RAW_DIR = BASE_DIR / "data" / "raw"
CHROMA_DIR = BASE_DIR / "chroma_data"
COLLECTION_NAME = "org_memory"
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


class GeminiEmbeddingFunction(EmbeddingFunction):
    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("Missing GEMINI_API_KEY in .env")
        self.client = genai.Client(api_key=api_key)

    def __call__(self, input: Documents) -> Embeddings:
        embeddings: List[List[float]] = []
        for text in input:
            response = self.client.models.embed_content(
                model="gemini-embedding-001",
                contents=text,
            )
            embeddings.append(response.embeddings[0].values)
        return embeddings


def get_collection():
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    embedding_function = GeminiEmbeddingFunction(api_key=GEMINI_API_KEY)
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=embedding_function,
    )


def safe_read_text(path: Path):
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8").strip()


def chunk_text(text: str, chunk_size: int = 1200, overlap: int = 150):
    text = text.strip()
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


def ingest_new_slack(collection, new_messages: list):
    ids, documents, metadatas = [], [], []

    for msg in new_messages:
        text = (msg.get("text") or "").strip()
        if not text:
            continue

        ids.append(f"slack_{msg.get('ts', '')}")
        documents.append(text)
        metadatas.append({
            "source": "slack",
            "channel": str(msg.get("channel", "")),
            "user": str(msg.get("user", "unknown")),
            "user_name": str(msg.get("user_name", msg.get("user", "unknown"))),
            "thread_ts": str(msg.get("thread_ts", "")),
            "ts": str(msg.get("ts", "")),
        })

    if ids:
        collection.upsert(ids=ids, documents=documents, metadatas=metadatas)
    return len(ids)


def ingest_new_gmail(collection, new_emails: list):
    ids, documents, metadatas = [], [], []

    for msg in new_emails:
        subject = (msg.get("subject") or "").strip()
        body = (msg.get("body") or "").strip()
        content = f"Subject: {subject}\n\n{body}".strip()

        if not content:
            continue

        ids.append(f"gmail_{msg.get('message_id', '')}")
        documents.append(content)
        metadatas.append({
            "source": "gmail",
            "from": str(msg.get("from", "")),
            "to": str(msg.get("to", "")),
            "cc": str(msg.get("cc", "")),
            "thread_id": str(msg.get("thread_id", "")),
            "date": str(msg.get("date", "")),
            "subject": subject,
        })

    if ids:
        collection.upsert(ids=ids, documents=documents, metadatas=metadatas)
    return len(ids)


def ingest_text_file_once(collection, filename: str, source_name: str):
    path = RAW_DIR / filename
    content = safe_read_text(path)
    if not content:
        return 0

    chunks = chunk_text(content)
    ids, documents, metadatas = [], [], []

    for index, chunk in enumerate(chunks, start=1):
        ids.append(f"{source_name}_{index}")
        documents.append(chunk)
        metadatas.append({
            "source": source_name,
            "file_name": filename,
            "chunk_index": index,
        })

    if ids:
        collection.upsert(ids=ids, documents=documents, metadatas=metadatas)
    return len(ids)


def run_incremental_ingestion(include_static_docs: bool = False):
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    collection = get_collection()

    new_slack = []
    new_gmail = []

    try:
        new_slack = fetch_channel_messages_incremental()
    except Exception as e:
        print(f"Slack fetch failed: {e}")

    try:
        service = authenticate_gmail()
        new_gmail = fetch_group_emails_incremental(service)
    except Exception as e:
        print(f"Gmail fetch failed: {e}")

    slack_count = ingest_new_slack(collection, new_slack)
    gmail_count = ingest_new_gmail(collection, new_gmail)

    meeting_count = 0
    final_doc_count = 0

    if include_static_docs:
        meeting_count = ingest_text_file_once(collection, "meeting_notes.txt", "meeting")
        final_doc_count = ingest_text_file_once(collection, "final_document.txt", "final_document")

    return {
        "new_slack": slack_count,
        "new_gmail": gmail_count,
        "meeting_chunks": meeting_count,
        "final_document_chunks": final_doc_count,
    }


if __name__ == "__main__":
    result = run_incremental_ingestion(include_static_docs=True)
    print(result)