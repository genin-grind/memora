import os
import re
import json
from functools import lru_cache
from pathlib import Path
from typing import Any

import chromadb
from chromadb.api.types import Documents
from chromadb.api.types import EmbeddingFunction
from chromadb.api.types import Embeddings
from dotenv import load_dotenv
from google import genai

from app.services.decision_graph_service import build_influence_graph


load_dotenv()

BASE_DIR = Path(__file__).resolve().parents[3]
CHROMA_DIR = BASE_DIR / "chroma_data"
COLLECTION_NAME = "org_memory"
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
RAW_DIR = BASE_DIR / "data" / "raw"


class GeminiEmbeddingFunction(EmbeddingFunction):
    def __init__(self, api_key: str):
        self.client = genai.Client(api_key=api_key)

    def __call__(self, input: Documents) -> Embeddings:
        embeddings: list[list[float]] = []
        for text in input:
            response = self.client.models.embed_content(
                model="gemini-embedding-001",
                contents=text,
            )
            embeddings.append(response.embeddings[0].values)
        return embeddings


@lru_cache(maxsize=1)
def get_genai_client():
    if not GEMINI_API_KEY:
        raise ValueError("Missing GEMINI_API_KEY in .env")
    return genai.Client(api_key=GEMINI_API_KEY)


@lru_cache(maxsize=1)
def get_collection():
    if not GEMINI_API_KEY:
        raise ValueError("Missing GEMINI_API_KEY in .env")

    embedding_function = GeminiEmbeddingFunction(api_key=GEMINI_API_KEY)
    chroma_client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    return chroma_client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=embedding_function,
    )


def clean_snippet(text: str, limit: int = 280) -> str:
    normalized = re.sub(r"\s+", " ", text or "").strip()
    if len(normalized) <= limit:
        return normalized
    return normalized[:limit].rstrip() + "..."


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


def _chunk_text(text: str, chunk_size: int = 1200, overlap: int = 150) -> list[str]:
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


def _build_raw_memory_records() -> list[dict[str, Any]]:
    slack_messages = _load_json_file(RAW_DIR / "slack_messages.json", [])
    gmail_messages = _load_json_file(RAW_DIR / "gmail_messages.json", [])
    meeting_notes = _load_text_file(RAW_DIR / "meeting_notes.txt")
    final_document = _load_text_file(RAW_DIR / "final_document.txt")

    records: list[dict[str, Any]] = []

    for message in slack_messages:
        text = str(message.get("text", "")).strip()
        ts = str(message.get("ts", "")).strip()
        if not text or not ts:
            continue
        records.append(
            {
                "id": f"slack_{ts}",
                "document": text,
                "metadata": {
                    "source": "slack",
                    "channel": str(message.get("channel", "")),
                    "user": str(message.get("user", "unknown")),
                    "user_name": str(message.get("user_name", message.get("user", "unknown"))),
                    "thread_ts": str(message.get("thread_ts", "")),
                    "ts": ts,
                },
            }
        )

    for message in gmail_messages:
        subject = str(message.get("subject", "")).strip()
        body = str(message.get("body", "")).strip()
        message_id = str(message.get("message_id", "")).strip()
        content = f"Subject: {subject}\n\n{body}".strip()
        if not content or not message_id:
            continue
        records.append(
            {
                "id": f"gmail_{message_id}",
                "document": content,
                "metadata": {
                    "source": "gmail",
                    "from": str(message.get("from", "")),
                    "to": str(message.get("to", "")),
                    "cc": str(message.get("cc", "")),
                    "thread_id": str(message.get("thread_id", "")),
                    "date": str(message.get("date", "")),
                    "subject": subject,
                },
            }
        )

    for index, chunk in enumerate(_chunk_text(meeting_notes), start=1):
        records.append(
            {
                "id": f"meeting_{index}",
                "document": chunk,
                "metadata": {
                    "source": "meeting",
                    "file_name": "meeting_notes.txt",
                    "chunk_index": index,
                },
            }
        )

    for index, chunk in enumerate(_chunk_text(final_document), start=1):
        records.append(
            {
                "id": f"final_document_{index}",
                "document": chunk,
                "metadata": {
                    "source": "final_document",
                    "file_name": "final_document.txt",
                    "chunk_index": index,
                },
            }
        )

    return records


def _ensure_collection_seeded(collection) -> list[dict[str, Any]]:
    records = _build_raw_memory_records()
    if not records:
        return []

    existing = collection.get(include=[])
    existing_ids = set(existing.get("ids", []))
    missing_records = [record for record in records if record["id"] not in existing_ids]

    if missing_records:
        collection.upsert(
            ids=[record["id"] for record in missing_records],
            documents=[record["document"] for record in missing_records],
            metadatas=[record["metadata"] for record in missing_records],
        )

    return records


def _keyword_score(query: str, text: str) -> int:
    normalized_query = re.sub(r"[^a-z0-9\s]+", " ", query.lower())
    normalized_text = re.sub(r"[^a-z0-9\s]+", " ", text.lower())
    query_tokens = [token for token in normalized_query.split() if len(token) > 2]
    if not query_tokens:
        return 0

    score = 0
    for token in query_tokens:
        if token in normalized_text:
            score += 1
    if normalized_query.strip() and normalized_query.strip() in normalized_text:
        score += 3
    return score


def _fallback_retrieve(user_query: str, records: list[dict[str, Any]], limit: int = 6):
    scored = []
    for record in records:
        metadata_text = " ".join(str(value) for value in record["metadata"].values())
        haystack = f"{record['document']} {metadata_text}"
        score = _keyword_score(user_query, haystack)
        if score > 0:
            scored.append((score, record))

    scored.sort(
        key=lambda item: (
            -item[0],
            source_priority(item[1]["metadata"].get("source", "")),
        )
    )
    return [record for _, record in scored[:limit]]


def _merge_results(
    vector_ids: list[str],
    vector_metas: list[dict[str, Any]],
    vector_docs: list[str],
    fallback_records: list[dict[str, Any]],
    limit: int = 6,
):
    merged: list[tuple[str, dict[str, Any], str]] = []
    seen_ids = set()

    for doc_id, meta, doc in zip(vector_ids, vector_metas, vector_docs):
        if doc_id in seen_ids:
            continue
        merged.append((doc_id, meta, doc))
        seen_ids.add(doc_id)

    for record in fallback_records:
        if record["id"] in seen_ids:
            continue
        merged.append((record["id"], record["metadata"], record["document"]))
        seen_ids.add(record["id"])

    merged.sort(key=lambda item: source_priority(item[1].get("source", "")))
    merged = merged[:limit]
    ids = [item[0] for item in merged]
    metas = [item[1] for item in merged]
    docs = [item[2] for item in merged]
    return ids, metas, docs


def source_priority(source: str) -> int:
    order = {
        "final_document": 1,
        "meeting": 2,
        "gmail": 3,
        "slack": 4,
    }
    return order.get((source or "").lower(), 99)


def get_human_source_label(doc_id: str, meta: dict[str, Any]) -> str:
    source = meta.get("source", "unknown")

    if source == "slack":
        user_label = meta.get("user_name") or meta.get("user", "Unknown")
        return f"Slack - {user_label}"

    if source == "gmail":
        subject = meta.get("subject", "No subject")
        short_subject = subject[:30] + "..." if len(subject) > 30 else subject
        return f"Gmail - {short_subject}"

    if source == "meeting":
        return "Meeting Notes"

    if source == "final_document":
        return "Final Document"

    return doc_id


def get_display_meta(source: str, meta: dict[str, Any]) -> str:
    source = (source or "").lower()

    if source == "slack":
        user_label = meta.get("user_name") or meta.get("user", "N/A")
        return f"Channel: {meta.get('channel', 'N/A')} | User: {user_label} | Timestamp: {meta.get('ts', 'N/A')}"
    if source == "gmail":
        return f"From: {meta.get('from', 'N/A')} | Subject: {meta.get('subject', 'N/A')} | Date: {meta.get('date', 'N/A')}"
    if source == "meeting":
        return f"File: {meta.get('file_name', 'meeting_notes.txt')} | Chunk: {meta.get('chunk_index', 'N/A')}"
    if source == "final_document":
        return f"File: {meta.get('file_name', 'final_document.txt')} | Chunk: {meta.get('chunk_index', 'N/A')}"
    return str(meta)


def explain_source_relevance(source: str) -> str:
    source = (source or "").lower()
    if source == "final_document":
        return "Strongest evidence because it captures the final confirmed decision."
    if source == "meeting":
        return "Shows how the team discussed and finalized the decision during the meeting."
    if source == "gmail":
        return "Supports the reasoning process with formal discussion from the email thread."
    if source == "slack":
        return "Captures the earlier discussion and informal context around the decision."
    return "Contributes supporting context to the final answer."


def infer_confidence(metas: list[dict[str, Any]]) -> str:
    sources = {meta.get("source", "") for meta in metas}
    if "final_document" in sources and "meeting" in sources:
        return "High"
    if len(sources) >= 3:
        return "Medium-High"
    if len(sources) >= 2:
        return "Medium"
    return "Low"


def strongest_source_label(metas: list[dict[str, Any]]) -> str:
    if not metas:
        return "-"
    best = sorted(metas, key=lambda meta: source_priority(meta.get("source", "")))[0]
    mapping = {
        "final_document": "Final Document",
        "meeting": "Meeting Notes",
        "gmail": "Gmail",
        "slack": "Slack",
    }
    return mapping.get(best.get("source", "unknown"), "Unknown")


def build_timeline_items(metas: list[dict[str, Any]], docs: list[str]) -> list[dict[str, str]]:
    items = []
    for meta, doc in zip(metas, docs):
        source = meta.get("source", "unknown")
        if source == "slack":
            title = "Slack discussion initiated"
        elif source == "gmail":
            title = "Email thread expanded the reasoning"
        elif source == "meeting":
            title = "Meeting discussion moved toward finalization"
        elif source == "final_document":
            title = "Final decision was documented"
        else:
            title = "Supporting evidence found"

        items.append(
            {
                "source": source,
                "title": title,
                "text": clean_snippet(doc, 220),
                "meta": get_display_meta(source, meta),
            }
        )

    items.sort(key=lambda item: source_priority(item["source"]))
    return items


def build_reasoning_prompt(user_query: str, ids: list[str], metas: list[dict[str, Any]], docs: list[str]) -> str:
    context_parts = []

    for index, (doc_id, meta, doc) in enumerate(zip(ids, metas, docs), start=1):
        source = meta.get("source", "unknown")
        human_label = get_human_source_label(doc_id, meta)
        context_parts.append(
            f"""[Source {index}]
ID: {doc_id}
Human Label: {human_label}
Source Type: {source}
Metadata: {meta}

Content:
{doc}
"""
        )

    context = "\n\n".join(context_parts)

    return f"""
You are Memora, an organizational reasoning engine.

Your task is to answer using ONLY the supplied evidence.

Rules:
- Do not invent facts.
- Prefer final_document over meeting notes when both exist.
- Prefer meeting notes over Slack and Gmail if there is any conflict.
- Slack and Gmail should be used as supporting context.
- Write in a crisp, product-like style.
- Do not output raw internal IDs like slack_123 or final_document_1.
- Use human-readable source names such as Final Document, Meeting Notes, Gmail Thread, Slack Discussion.
- Use this exact structure:

Final Decision
- ...

Why This Decision Was Made
- ...
- ...
- ...

Supporting Evidence Trail
- ...

Confidence
- High / Medium / Low

Sources Used
- Final Document
- Meeting Notes
- Gmail Thread
- Slack Discussion

User question:
{user_query}

Evidence:
{context}
"""


def build_evidence_items(ids: list[str], metas: list[dict[str, Any]], docs: list[str]) -> list[dict[str, Any]]:
    items = []
    for index, (doc_id, meta, doc) in enumerate(zip(ids, metas, docs), start=1):
        source = meta.get("source", "unknown")
        items.append(
            {
                "id": doc_id,
                "rank": index,
                "source": source,
                "label": get_human_source_label(doc_id, meta),
                "meta_display": get_display_meta(source, meta),
                "snippet": clean_snippet(doc, 320),
                "full_text": doc,
                "relevance_note": explain_source_relevance(source),
                "metadata": meta,
            }
        )
    return items


def analyze_query(user_query: str) -> dict[str, Any]:
    if not user_query or not user_query.strip():
        raise ValueError("Question is required.")

    collection = get_collection()
    genai_client = get_genai_client()
    raw_records = _ensure_collection_seeded(collection)

    results = collection.query(
        query_texts=[user_query],
        n_results=8,
    )

    ids = results.get("ids", [[]])[0]
    metas = results.get("metadatas", [[]])[0]
    docs = results.get("documents", [[]])[0]
    fallback_records = _fallback_retrieve(user_query, raw_records, limit=6)
    ids, metas, docs = _merge_results(ids, metas, docs, fallback_records, limit=6)

    if not docs:
        return {
            "ok": True,
            "query": user_query,
            "answer": "I could not find relevant evidence in the ingested data.",
            "evidence": [],
            "timeline": [],
            "graph": {"nodes": [], "edges": []},
            "metrics": {
                "evidence_retrieved": 0,
                "source_types": 0,
                "strongest_source": "-",
                "confidence": "Low",
            },
        }

    prompt = build_reasoning_prompt(user_query, ids, metas, docs)
    response = genai_client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )
    answer_text = response.text if hasattr(response, "text") else str(response)

    return {
        "ok": True,
        "query": user_query,
        "answer": answer_text,
        "evidence": build_evidence_items(ids, metas, docs),
        "timeline": build_timeline_items(metas, docs),
        "graph": build_influence_graph(ids[:6], metas[:6], docs[:6], user_query, answer_text),
        "metrics": {
            "evidence_retrieved": len(docs),
            "source_types": len(set(meta.get("source", "unknown") for meta in metas)),
            "strongest_source": strongest_source_label(metas),
            "confidence": infer_confidence(metas),
        },
    }
