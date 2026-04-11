import os
import re
import time
from pathlib import Path
from typing import List, Dict, Any
from utils.graph_builder import build_influence_graph
import chromadb
import streamlit as st
from chromadb.api.types import EmbeddingFunction, Documents, Embeddings
from dotenv import load_dotenv
from google import genai
import json
import html
import streamlit.components.v1 as components
from graphviz import Digraph

from ingest import run_incremental_ingestion
from utils.sidebar import render_common_sidebar

st.set_page_config(
    page_title="Memora | Organizational Reasoning Engine",
    page_icon="🧠",
    layout="wide",
)

load_dotenv()
from utils.auth import require_auth

require_auth()

# Render the common sidebar
render_common_sidebar()

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

# Auto-sync every N seconds
current_time = time.time()
if current_time - st.session_state.last_sync_time > st.session_state.auto_sync_interval:
    try:
        sync_result = run_incremental_ingestion(include_static_docs=False)
        st.session_state.last_sync_time = current_time
    except Exception as e:
        pass  # Silent fail for auto-sync

st.markdown("""
<style>
:root {
    --bg: #0b1020;
    --panel: #121a2b;
    --panel-2: #182235;
    --border: rgba(255,255,255,0.08);
    --text: #f3f4f6;
    --muted: #9aa4b2;
    --accent: #7c3aed;
    --accent-2: #06b6d4;
    --success: #22c55e;
    --warning: #f59e0b;
}

.stApp {
    background:
        radial-gradient(circle at top left, rgba(124,58,237,0.16), transparent 28%),
        radial-gradient(circle at top right, rgba(6,182,212,0.12), transparent 24%),
        linear-gradient(180deg, #0a0f1d 0%, #0b1020 100%);
    color: var(--text);
}

.block-container {
    padding-top: 1.2rem;
    padding-bottom: 2rem;
    max-width: 1400px;
}

[data-testid="stHeader"] {
    background: rgba(0,0,0,0);
}

[data-testid="stToolbar"] {
    right: 1rem;
}

.main-hero {
    padding: 1.05rem 1.3rem;
    border-radius: 22px;
    background: linear-gradient(135deg, rgba(124,58,237,0.18), rgba(6,182,212,0.10));
    border: 1px solid var(--border);
    box-shadow: 0 10px 30px rgba(0,0,0,0.18);
    margin-bottom: 1rem;
}

.hero-title {
    font-size: 1.85rem;
    font-weight: 800;
    color: white;
    margin-bottom: 0.25rem;
}

.hero-subtitle {
    color: #c7d2fe;
    font-size: 0.93rem;
    line-height: 1.45;
}

.glass-card {
    background: rgba(18, 26, 43, 0.82);
    border: 1px solid var(--border);
    border-radius: 22px;
    padding: 1.1rem;
    box-shadow: 0 8px 24px rgba(0,0,0,0.16);
    backdrop-filter: blur(10px);
    margin-top: 0 !important;
}

div[data-testid="column"] > div:has(.glass-card) {
    margin-top: 0 !important;
}

.metric-shell {
    background: linear-gradient(180deg, rgba(255,255,255,0.02), rgba(255,255,255,0.01));
    border: 1px solid var(--border);
    border-radius: 18px;
    padding: 1rem;
    text-align: left;
    min-height: 92px;
}

.metric-label {
    font-size: 0.8rem;
    color: var(--muted);
    margin-bottom: 0.35rem;
}

.metric-value {
    font-size: 1.35rem;
    font-weight: 800;
    color: white;
}

.section-title {
    font-size: 1.05rem;
    font-weight: 700;
    color: white;
    margin-bottom: 0.7rem;
}

.muted-text {
    color: var(--muted);
    font-size: 0.9rem;
}

.answer-panel {
    background: rgba(18,26,43,0.88);
    border: 1px solid var(--border);
    border-radius: 22px;
    padding: 1.2rem;
    line-height: 1.7;
    color: #e5e7eb;
}

.source-card {
    background: rgba(255,255,255,0.025);
    border: 1px solid var(--border);
    border-radius: 18px;
    padding: 1rem;
    margin-bottom: 0.9rem;
}

.source-title {
    font-size: 1rem;
    font-weight: 700;
    color: white;
    margin-bottom: 0.35rem;
}

.source-meta {
    color: var(--muted);
    font-size: 0.83rem;
    margin-bottom: 0.7rem;
}

.snippet {
    background: rgba(255,255,255,0.03);
    border-left: 4px solid rgba(124,58,237,0.85);
    border-radius: 12px;
    padding: 0.85rem;
    color: #dde5f0;
    margin-bottom: 0.8rem;
}

.badge {
    display: inline-block;
    padding: 0.24rem 0.62rem;
    border-radius: 999px;
    font-size: 0.72rem;
    font-weight: 700;
    margin-right: 0.35rem;
    margin-bottom: 0.25rem;
}

.badge-slack { background: rgba(168,85,247,0.16); color: #e9d5ff; border: 1px solid rgba(168,85,247,0.30); }
.badge-gmail { background: rgba(239,68,68,0.14); color: #fecaca; border: 1px solid rgba(239,68,68,0.28); }
.badge-meeting { background: rgba(59,130,246,0.16); color: #bfdbfe; border: 1px solid rgba(59,130,246,0.28); }
.badge-final { background: rgba(34,197,94,0.14); color: #bbf7d0; border: 1px solid rgba(34,197,94,0.28); }
.badge-rank { background: rgba(255,255,255,0.05); color: #d1d5db; border: 1px solid rgba(255,255,255,0.09); }

.timeline-item {
    background: rgba(255,255,255,0.02);
    border: 1px solid var(--border);
    border-left: 4px solid rgba(6,182,212,0.8);
    border-radius: 16px;
    padding: 1rem;
    margin-bottom: 0.8rem;
}

.pipeline-step {
    padding: 0.8rem 0.9rem;
    border-radius: 14px;
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.06);
    margin-bottom: 0.65rem;
    color: #dbeafe;
    line-height: 1.45;
}

div[data-testid="stTextArea"] textarea {
    background: rgba(10,15,29,0.92) !important;
    color: white !important;
    border-radius: 16px !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    padding: 1rem !important;
    font-size: 1rem !important;
}

div[data-testid="stTextArea"] label {
    color: #cbd5e1 !important;
}

div[data-testid="stSelectbox"] > div {
    border-radius: 14px !important;
}

div[data-testid="stSelectbox"] > div > div {
    background: rgba(10,15,29,0.92) !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    border-radius: 14px !important;
}

div[data-testid="stSelectbox"] label {
    color: #cbd5e1 !important;
}

div.stButton > button {
    border-radius: 14px !important;
    font-weight: 700 !important;
    border: 1px solid rgba(124,58,237,0.35) !important;
    background: linear-gradient(135deg, rgba(124,58,237,0.95), rgba(6,182,212,0.85)) !important;
    color: white !important;
    min-height: 46px;
}

div[data-testid="stTabs"] button {
    border-radius: 12px 12px 0 0 !important;
}

.stExpander {
    border: 1px solid var(--border) !important;
    border-radius: 16px !important;
    background: rgba(255,255,255,0.02) !important;
}

[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #151826 0%, #1a1f2e 100%);
    border-right: 1px solid rgba(255,255,255,0.06);
}

[data-testid="stSidebar"] * {
    color: #e5e7eb;
}

[data-testid="stSidebarNav"] {
    padding-top: 1rem;
}

[data-testid="stSidebarNav"]::before {
    content: "MEMORA";
    display: block;
    font-size: 1.25rem;
    font-weight: 800;
    color: white;
    padding: 0.5rem 1rem 1rem 1rem;
    letter-spacing: 0.04em;
}

[data-testid="stSidebarNav"] a {
    border-radius: 12px;
    margin: 0.15rem 0.6rem;
    padding: 0.2rem 0.4rem;
}

[data-testid="stSidebarNav"] a:hover {
    background: rgba(124,58,237,0.14);
}

[data-testid="stSidebarNav"] a[aria-current="page"] {
    background: rgba(255,255,255,0.08);
}

h3 {
    margin-bottom: 0.45rem !important;
}

p, label {
    color: #cbd5e1;
}

hr {
    border-color: rgba(255,255,255,0.08);
}

div[data-testid="stMarkdownContainer"] p {
    line-height: 1.5;
}
</style>
""", unsafe_allow_html=True)


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


def render_graphviz_graph(graph_data: Dict[str, Any]):
    dot = Digraph(comment="Memora Decision Graph")
    dot.attr(rankdir="LR", bgcolor="#0b1020", pad="0.4", nodesep="0.55", ranksep="1.0")
    dot.attr("graph", fontname="Inter", splines="spline")
    dot.attr("node", fontname="Inter", shape="box", style="rounded,filled", color="#334155", penwidth="1.4")
    dot.attr("edge", fontname="Inter", color="#94a3b8", arrowsize="0.8", penwidth="1.3")

    type_styles = {
        "person": {
            "fillcolor": "#2b1748",
            "fontcolor": "#f5f3ff",
            "color": "#8b5cf6",
        },
        "source": {
            "fillcolor": "#0f2a44",
            "fontcolor": "#e0f2fe",
            "color": "#38bdf8",
        },
        "reason": {
            "fillcolor": "#3b2506",
            "fontcolor": "#fef3c7",
            "color": "#f59e0b",
        },
        "decision": {
            "fillcolor": "#0d2f1f",
            "fontcolor": "#dcfce7",
            "color": "#22c55e",
        },
    }

    edge_colors = {
        "said": "#a78bfa",
        "sent": "#fb7185",
        "mentions": "#fbbf24",
        "supports": "#38bdf8",
        "influences": "#7dd3fc",
        "finalizes": "#60a5fa",
        "confirms": "#4ade80",
        "shapes": "#f59e0b",
    }

    def shorten(text: str, max_len: int = 28) -> str:
        text = str(text or "").strip()
        return text if len(text) <= max_len else text[:max_len - 3] + "..."

    def format_node_label(node: Dict[str, Any]) -> str:
        label = shorten(node.get("label", ""), 30)
        node_type = node.get("type", "").title()
        return f"{label}\\n{node_type}"

    # Add nodes
    for node in graph_data["nodes"]:
        node_type = node.get("type", "source")
        style = type_styles.get(node_type, type_styles["source"])

        width = "2.2"
        if node_type == "decision":
            width = "2.6"

        dot.node(
            node["id"],
            format_node_label(node),
            fillcolor=style["fillcolor"],
            fontcolor=style["fontcolor"],
            color=style["color"],
            width=width,
            height="0.8",
            margin="0.18,0.12",
        )

    # Add edges
    for edge in graph_data["edges"]:
        label = edge.get("label", "")
        dot.edge(
            edge["source"],
            edge["target"],
            label=label,
            color=edge_colors.get(label, "#94a3b8"),
            fontcolor="#cbd5e1",
        )

    st.markdown("### Decision Graph")
    st.caption("Interactive-free professional graph built directly in Streamlit.")
    st.graphviz_chart(dot,width="stretch")


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


st.markdown("""
<div class="main-hero">
    <div class="hero-title">Memora</div>
    <div class="hero-subtitle">
        Organizational decision intelligence across Slack, Gmail, meeting notes, and final documents.
        Ask one question and trace how the final decision was formed.
    </div>
</div>
""", unsafe_allow_html=True)

left_top, right_top = st.columns([1.2, 0.8], gap="medium")

with left_top:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Ask a decision question</div>', unsafe_allow_html=True)
    st.markdown('<div class="muted-text">Query your organizational memory and reconstruct why a decision was made.</div>', unsafe_allow_html=True)

    user_query = st.text_area(
        "Question",
        value=st.session_state.last_query,
        placeholder="Why did we choose FastAPI over MERN/Node?",
        height=120,
        label_visibility="collapsed",
    )

    examples = [
        "Why did we choose FastAPI over MERN/Node?",
        "What final tech stack was approved?",
        "Why is Neo4j optional?",
        "What was finalized in the meeting?",
        "What is the final project scope?",
    ]
    selected_example = st.selectbox("Try an example", [""] + examples)

    if selected_example and not user_query:
        user_query = selected_example

    analyze = st.button("Analyze Decision", width="stretch")
    st.markdown("</div>", unsafe_allow_html=True)

with right_top:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">How Memora works</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="pipeline-step"><b>1. Retrieval</b> — Finds relevant evidence from ChromaDB.</div>
    <div class="pipeline-step"><b>2. Ranking</b> — Prioritizes stronger organizational sources.</div>
    <div class="pipeline-step"><b>3. Reasoning</b> — Synthesizes a grounded answer with Gemini.</div>
    <div class="pipeline-step"><b>4. Traceability</b> — Shows evidence, timeline, and provenance.</div>
    """, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

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

# Supporting Evidence Trail
# - ...

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
                model="gemini-2.5-flash-lite",
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

    c1, c2, c3, c4 = st.columns(4, gap="medium")

    with c1:
        st.markdown(f"""
        <div class="metric-shell">
            <div class="metric-label">Evidence Retrieved</div>
            <div class="metric-value">{len(docs)}</div>
        </div>
        """, unsafe_allow_html=True)

    with c2:
        st.markdown(f"""
        <div class="metric-shell">
            <div class="metric-label">Source Types</div>
            <div class="metric-value">{count_unique_sources(metas)}</div>
        </div>
        """, unsafe_allow_html=True)

    with c3:
        st.markdown(f"""
        <div class="metric-shell">
            <div class="metric-label">Strongest Source</div>
            <div class="metric-value" style="font-size:1rem;">{strongest_source_label(metas)}</div>
        </div>
        """, unsafe_allow_html=True)

    with c4:
        st.markdown(f"""
        <div class="metric-shell">
            <div class="metric-label">Confidence</div>
            <div class="metric-value">{infer_confidence(metas)}</div>
        </div>
        """, unsafe_allow_html=True)
    

    st.markdown(
       """
      <div style="
        margin-top:1rem;
        margin-bottom:1rem;
        padding:1rem 1.2rem;
        border-radius:16px;
        background:rgba(34,197,94,0.12);
        border:1px solid rgba(34,197,94,0.28);
        color:white;
        font-weight:600;
      ">
        ✅ Analysis ready. Explore the <b>Decision Graph</b> tab to see who said what and how this decision was formed.
        </div>
        """,
       unsafe_allow_html=True,
    )


    tab1, tab2, tab3, tab4,tab5= st.tabs(
        ["🧠 Final Answer", "📁 Evidence", "🕒 Reasoning Flow", "🕸️ Decision Graph", "🧾 Raw Trace"]
    )

    with tab1:
        st.markdown("### Decision Analysis")
        st.markdown(
            f"""
            <div class="answer-panel">
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
                    if st.button(label, key=f"source_btn_{doc_id}", width="stretch"):
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
                        <div class="source-title">{selected_label}</div>
                        <div style="margin-bottom:0.5rem;">{get_source_badge(selected_source)}</div>
                        <div class="source-meta">{get_display_meta(selected_source, selected_meta)}</div>
                        <div class="snippet">{clean_snippet(selected_doc, 500)}</div>
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
                    <div class="source-title">Source {i} · {get_human_source_label(doc_id, meta)}</div>
                    <div style="margin-bottom:0.5rem;">
                        {badge_html}
                        <span class="badge badge-rank">Rank #{i}</span>
                    </div>
                    <div class="source-meta">{display_meta}</div>
                    <div class="snippet">{snippet}</div>
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
                    <div class="source-title">{get_source_badge(item["source"])} {item["title"]}</div>
                    <div class="source-meta">{item["meta"]}</div>
                    <div>{item["text"]}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    with tab4:
       graph_data = build_influence_graph(
        ids[:6],
        metas[:6],
        docs[:6],
        st.session_state.last_query,
        answer_text,
      )
       render_graphviz_graph(graph_data)

    with tab5:
        st.markdown("### Raw Retrieval Trace")
        st.caption("Useful for debugging, demo explanations, and proof of provenance.")
        for i, (doc_id, meta, doc) in enumerate(zip(ids, metas, docs), start=1):
            st.markdown(f"**Source {i}**")
            st.write(f"ID: {doc_id}")
            st.write(f"Label: {get_human_source_label(doc_id, meta)}")
            st.json(meta)
            st.code(doc)

else:
    st.markdown("""
    <div class="glass-card" style="padding:0.9rem 1rem; margin-top:0.8rem;">
        <div class="muted-text">
            Ask a question to generate a grounded decision answer with evidence cards and a timeline.
        </div>
    </div>
    """, unsafe_allow_html=True)