import os
import re
from pathlib import Path
from typing import List, Dict, Any

import chromadb
import streamlit as st
from chromadb.api.types import EmbeddingFunction, Documents, Embeddings
from dotenv import load_dotenv
from google import genai

load_dotenv()
from utils.auth import require_auth

require_auth()
BASE_DIR = Path(__file__).resolve().parent
CHROMA_DIR = BASE_DIR / "chroma_data"
COLLECTION_NAME = "org_memory"
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError("Missing GEMINI_API_KEY in .env")


class GeminiEmbeddingFunction(EmbeddingFunction):
    def __init__(self, api_key: str):
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


genai_client = genai.Client(api_key=GEMINI_API_KEY)

embedding_function = GeminiEmbeddingFunction(api_key=GEMINI_API_KEY)
chroma_client = chromadb.PersistentClient(path=str(CHROMA_DIR))
collection = chroma_client.get_or_create_collection(
    name=COLLECTION_NAME,
    embedding_function=embedding_function,
)

st.set_page_config(
    page_title="Memora | Organizational Reasoning Engine",
    page_icon="🧠",
    layout="wide",
)

st.markdown(
    """
    <style>
        .main {
            padding-top: 1.2rem;
        }
        .hero-box {
            padding: 1.2rem 1.4rem;
            border-radius: 18px;
            background: linear-gradient(135deg, rgba(99,102,241,0.14), rgba(16,185,129,0.10));
            border: 1px solid rgba(255,255,255,0.08);
            margin-bottom: 1rem;
        }
        .hero-title {
            font-size: 2rem;
            font-weight: 700;
            margin-bottom: 0.25rem;
        }
        .hero-subtitle {
            color: #b8bfd0;
            font-size: 0.98rem;
        }
        .metric-card {
            padding: 0.9rem 1rem;
            border-radius: 16px;
            background: rgba(255,255,255,0.03);
            border: 1px solid rgba(255,255,255,0.07);
            text-align: center;
        }
        .metric-label {
            font-size: 0.82rem;
            color: #a7b0c0;
            margin-bottom: 0.2rem;
        }
        .metric-value {
            font-size: 1.35rem;
            font-weight: 700;
        }
        .answer-box {
            padding: 1.1rem 1.2rem;
            border-radius: 18px;
            background: rgba(255,255,255,0.03);
            border: 1px solid rgba(255,255,255,0.08);
            margin-bottom: 1rem;
        }
        .source-card {
            padding: 1rem 1rem 0.8rem 1rem;
            border-radius: 16px;
            background: rgba(255,255,255,0.025);
            border: 1px solid rgba(255,255,255,0.08);
            margin-bottom: 0.9rem;
        }
        .source-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 0.5rem;
            margin-bottom: 0.6rem;
            flex-wrap: wrap;
        }
        .source-title {
            font-weight: 700;
            font-size: 1rem;
        }
        .badge {
            display: inline-block;
            padding: 0.18rem 0.55rem;
            border-radius: 999px;
            font-size: 0.74rem;
            font-weight: 700;
            margin-right: 0.35rem;
            margin-bottom: 0.25rem;
        }
        .badge-slack {
            background: rgba(168, 85, 247, 0.18);
            color: #d8b4fe;
            border: 1px solid rgba(168, 85, 247, 0.35);
        }
        .badge-gmail {
            background: rgba(239, 68, 68, 0.16);
            color: #fca5a5;
            border: 1px solid rgba(239, 68, 68, 0.35);
        }
        .badge-meeting {
            background: rgba(59, 130, 246, 0.16);
            color: #93c5fd;
            border: 1px solid rgba(59, 130, 246, 0.35);
        }
        .badge-final {
            background: rgba(16, 185, 129, 0.16);
            color: #86efac;
            border: 1px solid rgba(16, 185, 129, 0.35);
        }
        .badge-rank {
            background: rgba(255,255,255,0.06);
            color: #d1d5db;
            border: 1px solid rgba(255,255,255,0.08);
        }
        .source-meta {
            color: #a7b0c0;
            font-size: 0.84rem;
            margin-bottom: 0.55rem;
        }
        .snippet-box {
            padding: 0.8rem 0.9rem;
            border-radius: 12px;
            background: rgba(255,255,255,0.03);
            border-left: 4px solid rgba(99,102,241,0.7);
            font-size: 0.93rem;
            margin-bottom: 0.7rem;
        }
        .timeline-item {
            padding: 0.85rem 1rem;
            border-left: 3px solid rgba(99,102,241,0.65);
            margin-left: 0.35rem;
            margin-bottom: 0.75rem;
            background: rgba(255,255,255,0.02);
            border-radius: 0 12px 12px 0;
        }
        .timeline-title {
            font-weight: 700;
            margin-bottom: 0.25rem;
        }
        .small-muted {
            color: #9aa3b2;
            font-size: 0.82rem;
        }
        .status-good {
            color: #86efac;
            font-weight: 600;
        }
        .status-info {
            color: #93c5fd;
            font-weight: 600;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


def get_source_badge(source: str) -> str:
    source = (source or "").lower()
    if source == "slack":
        return '<span class="badge badge-slack">Slack</span>'
    if source == "gmail":
        return '<span class="badge badge-gmail">Gmail</span>'
    if source == "meeting":
        return '<span class="badge badge-meeting">Meeting</span>'
    if source == "final_document":
        return '<span class="badge badge-final">Final Document</span>'
    return f'<span class="badge badge-rank">{source}</span>'


def clean_snippet(text: str, limit: int = 280) -> str:
    text = re.sub(r"\s+", " ", text or "").strip()
    if len(text) <= limit:
        return text
    return text[:limit].rstrip() + "..."


def explain_source_relevance(source: str, meta: Dict[str, Any]) -> str:
    source = (source or "").lower()
    if source == "final_document":
        return "This is the strongest evidence because it captures the final confirmed decision."
    if source == "meeting":
        return "This shows how the team discussed and finalized the decision during the meeting."
    if source == "gmail":
        return "This supports the reasoning process with formal discussion from the email thread."
    if source == "slack":
        return "This captures the early discussion and informal context around the decision."
    return "This source contributes supporting context to the final answer."


def get_display_meta(source: str, meta: Dict[str, Any]) -> str:
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


def source_priority(source: str) -> int:
    order = {
        "final_document": 1,
        "meeting": 2,
        "gmail": 3,
        "slack": 4,
    }
    return order.get((source or "").lower(), 99)


def build_timeline_items(metas: List[Dict[str, Any]], docs: List[str]) -> List[Dict[str, str]]:
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

    items.sort(key=lambda x: source_priority(x["source"]))
    return items


def count_unique_sources(metas: List[Dict[str, Any]]) -> int:
    return len(set((m.get("source", "unknown") for m in metas)))


def strongest_source_label(metas: List[Dict[str, Any]]) -> str:
    if not metas:
        return "-"
    best = sorted(metas, key=lambda m: source_priority(m.get("source", "")))[0]
    source = best.get("source", "unknown")
    mapping = {
        "final_document": "Final Document",
        "meeting": "Meeting Notes",
        "gmail": "Gmail",
        "slack": "Slack",
    }
    return mapping.get(source, source.title())


def infer_confidence(metas: List[Dict[str, Any]]) -> str:
    sources = {m.get("source", "") for m in metas}
    if "final_document" in sources and "meeting" in sources:
        return "High"
    if len(sources) >= 3:
        return "Medium-High"
    if len(sources) >= 2:
        return "Medium"
    return "Low"


def get_human_source_label(doc_id: str, meta: Dict[str, Any]) -> str:
    source = meta.get("source", "unknown")

    if source == "slack":
        user_label = meta.get("user_name") or meta.get("user", "Unknown")
        return f"Slack · {user_label}"

    if source == "gmail":
        subject = meta.get("subject", "No subject")
        short_subject = subject[:30] + "..." if len(subject) > 30 else subject
        return f"Gmail · {short_subject}"

    if source == "meeting":
        return "Meeting Notes"

    if source == "final_document":
        return "Final Document"

    return doc_id


if "last_query" not in st.session_state:
    st.session_state.last_query = ""

if "last_answer" not in st.session_state:
    st.session_state.last_answer = ""

if "last_docs" not in st.session_state:
    st.session_state.last_docs = []

if "last_metas" not in st.session_state:
    st.session_state.last_metas = []

if "last_ids" not in st.session_state:
    st.session_state.last_ids = []

if "selected_source_id" not in st.session_state:
    st.session_state.selected_source_id = None


st.markdown(
    """
    <div class="hero-box">
        <div class="hero-title">🧠 Memora: Organizational Reasoning Engine</div>
        <div class="hero-subtitle">
            Reconstruct decisions across Slack, Gmail, meetings, and final documents with transparent evidence.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

left_top, right_top = st.columns([1.3, 2])

with left_top:
    st.markdown("### Ask a decision question")
    user_query = st.text_area(
        "Question",
        value=st.session_state.last_query,
        placeholder="Why did we choose FastAPI over MERN/Node?",
        height=100,
        label_visibility="collapsed",
    )

    examples = [
        "Why did we choose FastAPI over MERN/Node?",
        "What final tech stack was approved?",
        "Why is Neo4j optional?",
        "What was finalized in the meeting?",
        "What is the final project scope?",
    ]
    selected_example = st.selectbox("Quick examples", [""] + examples)

    if selected_example and not user_query:
        user_query = selected_example

    analyze = st.button("Analyze Decision", use_container_width=True)

with right_top:
    st.markdown("### Agentic flow")
    st.markdown(
        """
        <div class="answer-box">
            <div class="small-muted">System pipeline</div>
            <div style="margin-top: 0.5rem;">
                <span class="status-info">Ingestion Agent</span> → Collects Slack, Gmail, meeting notes, final document<br>
                <span class="status-info">Retrieval Agent</span> → Finds relevant evidence from ChromaDB<br>
                <span class="status-info">Reasoning Agent</span> → Synthesizes cross-source explanation using Gemini<br>
                <span class="status-good">Traceability Layer</span> → Shows supporting evidence and source trail
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

if analyze and user_query.strip():
    st.session_state.selected_source_id = None

    with st.spinner("Running retrieval and reasoning pipeline..."):
        status = st.status("Memora is analyzing your question...", expanded=True)

        status.write("Step 1: Retriever Agent searching organizational memory")
        results = collection.query(
            query_texts=[user_query],
            n_results=6,
        )

        docs = results.get("documents", [[]])[0]
        metas = results.get("metadatas", [[]])[0]
        ids = results.get("ids", [[]])[0]

        if not docs:
            status.update(label="No relevant evidence found", state="error")
            st.session_state.last_query = user_query
            st.session_state.last_answer = "I could not find relevant evidence in the ingested data."
            st.session_state.last_docs = []
            st.session_state.last_metas = []
            st.session_state.last_ids = []
        else:
            status.write("Step 2: Relationship layer ranking strongest evidence")
            context_parts = []

            for i, (doc_id, meta, doc) in enumerate(zip(ids, metas, docs), start=1):
                source = meta.get("source", "unknown")
                human_label = get_human_source_label(doc_id, meta)

                context_parts.append(
                    f"""[Source {i}]
ID: {doc_id}
Human Label: {human_label}
Source Type: {source}
Metadata: {meta}

Content:
{doc}
"""
                )

            context = "\n\n".join(context_parts)

            status.write("Step 3: Reasoning Agent synthesizing final answer")
            prompt = f"""
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

            response = genai_client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
            )

            answer_text = response.text if hasattr(response, "text") else str(response)
            status.update(label="Analysis complete", state="complete")

            st.session_state.last_query = user_query
            st.session_state.last_answer = answer_text
            st.session_state.last_docs = docs
            st.session_state.last_metas = metas
            st.session_state.last_ids = ids

if st.session_state.last_answer:
    docs = st.session_state.last_docs
    metas = st.session_state.last_metas
    ids = st.session_state.last_ids
    answer_text = st.session_state.last_answer

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">Evidence Retrieved</div>
                <div class="metric-value">{len(docs)}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">Source Types</div>
                <div class="metric-value">{count_unique_sources(metas)}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">Strongest Source</div>
                <div class="metric-value" style="font-size:1rem;">{strongest_source_label(metas)}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c4:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">Confidence</div>
                <div class="metric-value">{infer_confidence(metas)}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    tab1, tab2, tab3, tab4 = st.tabs(
        ["Decision Answer", "Evidence Cards", "Reasoning Timeline", "Raw Trace"]
    )

    with tab1:
        st.markdown("### Decision Analysis")
        st.markdown(
            f"""
            <div class="answer-box">
                {answer_text.replace("\n", "<br>")}
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("### Open Sources")
        st.caption("Click any source to open the full supporting artifact.")

        if ids:
            num_cols = min(3, len(ids))
            cols = st.columns(num_cols)

            for idx, (doc_id, meta) in enumerate(zip(ids, metas)):
                label = get_human_source_label(doc_id, meta)
                with cols[idx % num_cols]:
                    if st.button(label, key=f"source_btn_{doc_id}", use_container_width=True):
                        st.session_state.selected_source_id = doc_id

        if st.session_state.selected_source_id:
            selected_index = None
            for i, doc_id in enumerate(ids):
                if doc_id == st.session_state.selected_source_id:
                    selected_index = i
                    break

            if selected_index is not None:
                selected_meta = metas[selected_index]
                selected_doc = docs[selected_index]
                selected_source = selected_meta.get("source", "unknown")
                selected_label = get_human_source_label(
                    st.session_state.selected_source_id,
                    selected_meta,
                )

                st.markdown("### Opened Source")
                st.markdown(
                    f"""
                    <div class="source-card">
                        <div class="source-header">
                            <div class="source-title">{selected_label}</div>
                            <div>{get_source_badge(selected_source)}</div>
                        </div>
                        <div class="source-meta">{get_display_meta(selected_source, selected_meta)}</div>
                        <div class="snippet-box">{clean_snippet(selected_doc, 500)}</div>
                        <div><b>Why it matters:</b> {explain_source_relevance(selected_source, selected_meta)}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                with st.expander("View full source content", expanded=True):
                    st.write(selected_meta)
                    st.code(selected_doc)

    with tab2:
        st.markdown("### Evidence Trail")
        st.caption("Each source is shown as a reasoning artifact, not just raw retrieval output.")

        for i, (doc_id, meta, doc) in enumerate(zip(ids, metas, docs), start=1):
            source = meta.get("source", "unknown")
            badge_html = get_source_badge(source)
            relevance_note = explain_source_relevance(source, meta)
            display_meta = get_display_meta(source, meta)
            snippet = clean_snippet(doc, 320)

            st.markdown(
                f"""
                <div class="source-card">
                    <div class="source-header">
                        <div class="source-title">Source {i} · {get_human_source_label(doc_id, meta)}</div>
                        <div>
                            {badge_html}
                            <span class="badge badge-rank">Rank #{i}</span>
                        </div>
                    </div>
                    <div class="source-meta">{display_meta}</div>
                    <div class="snippet-box">{snippet}</div>
                    <div><b>Why it matters:</b> {relevance_note}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            with st.expander(f"Open full source text — Source {i}"):
                st.write(meta)
                st.code(doc)

    with tab3:
        st.markdown("### Decision Timeline")
        st.caption("This reconstructs how the decision progressed across communication channels.")

        timeline_items = build_timeline_items(metas, docs)

        for item in timeline_items:
            st.markdown(
                f"""
                <div class="timeline-item">
                    <div class="timeline-title">{get_source_badge(item["source"])} {item["title"]}</div>
                    <div class="small-muted" style="margin-bottom:0.45rem;">{item["meta"]}</div>
                    <div>{item["text"]}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    with tab4:
        st.markdown("### Raw Retrieval Trace")
        st.caption("Useful for debugging, demo explanations, and proof of provenance.")
        for i, (doc_id, meta, doc) in enumerate(zip(ids, metas, docs), start=1):
            st.markdown(f"**Source {i}**")
            st.write(f"ID: {doc_id}")
            st.write(f"Label: {get_human_source_label(doc_id, meta)}")
            st.json(meta)
            st.code(doc)

else:
    st.info("Ask a question and click **Analyze Decision** to see reasoning, evidence cards, and a source timeline.")