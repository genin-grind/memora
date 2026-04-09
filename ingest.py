import json
import os
import shutil
from pathlib import Path
from typing import List

import chromadb
from chromadb.api.types import EmbeddingFunction, Documents, Embeddings
from dotenv import load_dotenv
from google import genai

from fetch_slack import fetch_channel_messages
from fetch_gmail import authenticate_gmail, fetch_group_emails

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


def reset_chroma():
    if CHROMA_DIR.exists():
        shutil.rmtree(CHROMA_DIR)
        print("Deleted old chroma_data directory")


def get_collection():
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    embedding_function = GeminiEmbeddingFunction(api_key=GEMINI_API_KEY)
    collection = client.create_collection(
        name=COLLECTION_NAME,
        embedding_function=embedding_function,
    )
    return collection


def safe_read_json(path: Path):
    if not path.exists():
        print(f"Missing file: {path}")
        return []

    content = path.read_text(encoding="utf-8").strip()
    if not content:
        print(f"Empty file: {path}")
        return []

    try:
        return json.loads(content)
    except json.JSONDecodeError:
        print(f"Invalid JSON in file: {path}")
        return []


def safe_read_text(path: Path):
    if not path.exists():
        print(f"Missing file: {path}")
        return ""
    return path.read_text(encoding="utf-8").strip()


def chunk_text(text: str, chunk_size: int = 1200, overlap: int = 150):
    text = text.strip()
    if not text:
        return []

    chunks = []
    start = 0
    text_len = len(text)

    while start < text_len:
        end = min(start + chunk_size, text_len)
        chunks.append(text[start:end])
        if end == text_len:
            break
        start = end - overlap

    return chunks


def auto_fetch_sources():
    print("Auto-fetching Slack messages...")
    try:
        fetch_channel_messages()
    except Exception as e:
        print(f"Slack fetch failed: {e}")

    print("Auto-fetching Gmail messages...")
    try:
        service = authenticate_gmail()
        fetch_group_emails(service)
    except Exception as e:
        print(f"Gmail fetch failed: {e}")


def ingest_slack(collection):
    slack_path = RAW_DIR / "slack_messages.json"
    messages = safe_read_json(slack_path)

    ids = []
    documents = []
    metadatas = []

    for msg in messages:
        text = (msg.get("text") or "").strip()
        if not text:
            continue

        doc_id = f"slack_{msg.get('ts', '')}"
        metadata = {
            "source": "slack",
            "channel": str(msg.get("channel", "")),
            "user": str(msg.get("user", "unknown")),
            "user_name": str(msg.get("user_name", msg.get("user", "unknown"))),
            "thread_ts": str(msg.get("thread_ts", "")),
            "ts": str(msg.get("ts", "")),
        }

        ids.append(doc_id)
        documents.append(text)
        metadatas.append(metadata)

    if ids:
        collection.upsert(ids=ids, documents=documents, metadatas=metadatas)
        print(f"Ingested {len(ids)} Slack messages")
    else:
        print("No Slack messages to ingest")


def ingest_gmail(collection):
    gmail_path = RAW_DIR / "gmail_messages.json"
    emails = safe_read_json(gmail_path)

    ids = []
    documents = []
    metadatas = []

    for msg in emails:
        subject = (msg.get("subject") or "").strip()
        body = (msg.get("body") or "").strip()
        content = f"Subject: {subject}\n\n{body}".strip()

        if not content:
            continue

        doc_id = f"gmail_{msg.get('message_id', '')}"
        metadata = {
            "source": "gmail",
            "from": str(msg.get("from", "")),
            "to": str(msg.get("to", "")),
            "cc": str(msg.get("cc", "")),
            "thread_id": str(msg.get("thread_id", "")),
            "date": str(msg.get("date", "")),
            "subject": subject,
        }

        ids.append(doc_id)
        documents.append(content)
        metadatas.append(metadata)

    if ids:
        collection.upsert(ids=ids, documents=documents, metadatas=metadatas)
        print(f"Ingested {len(ids)} Gmail messages")
    else:
        print("No Gmail messages to ingest")


def ingest_text_file(collection, filename: str, source_name: str):
    path = RAW_DIR / filename
    content = safe_read_text(path)

    if not content:
        print(f"Skipped empty or missing file: {filename}")
        return

    chunks = chunk_text(content)

    ids = []
    documents = []
    metadatas = []

    for index, chunk in enumerate(chunks, start=1):
        ids.append(f"{source_name}_{index}")
        documents.append(chunk)
        metadatas.append(
            {
                "source": source_name,
                "file_name": filename,
                "chunk_index": index,
            }
        )

    collection.upsert(ids=ids, documents=documents, metadatas=metadatas)
    print(f"Ingested {len(ids)} chunks from {filename}")


def main():
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    auto_fetch_sources()
    reset_chroma()
    collection = get_collection()

    ingest_slack(collection)
    ingest_gmail(collection)
    ingest_text_file(collection, "meeting_notes.txt", "meeting")
    ingest_text_file(collection, "final_document.txt", "final_document")

    print("All data ingested successfully into ChromaDB.")


if __name__ == "__main__":
    main()