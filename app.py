import os
from pathlib import Path
from typing import List

import chromadb
import streamlit as st
from chromadb.api.types import EmbeddingFunction, Documents, Embeddings
from dotenv import load_dotenv
from google import genai

load_dotenv()

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

st.set_page_config(page_title="Mem-ora", page_icon="🧠", layout="wide")
st.title("🧠 Mem-ora")
st.caption("Organizational memory and reasoning across Slack, Gmail, meetings, and final documents")

if "messages" not in st.session_state:
    st.session_state.messages = []

with st.sidebar:
    st.header("How to use")
    st.write("Run `python ingest.py`, then ask questions here.")
    st.divider()
    st.write("Suggested questions:")
    st.write("- Why did we choose FastAPI?")
    st.write("- Why is Neo4j optional?")
    st.write("- What was finalized in the meeting?")
    st.write("- What is the final project scope?")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

user_query = st.chat_input("Ask about past decisions...")

if user_query:
    st.session_state.messages.append({"role": "user", "content": user_query})
    with st.chat_message("user"):
        st.markdown(user_query)

    with st.chat_message("assistant"):
        with st.spinner("Searching organizational memory..."):
            results = collection.query(
                query_texts=[user_query],
                n_results=6,
            )

            docs = results.get("documents", [[]])[0]
            metas = results.get("metadatas", [[]])[0]
            ids = results.get("ids", [[]])[0]

            if not docs:
                answer_text = "I could not find relevant evidence in the ingested data."
                st.markdown(answer_text)
                st.session_state.messages.append(
                    {"role": "assistant", "content": answer_text}
                )
            else:
                context_parts = []
                evidence_lines = []

                for i, (doc_id, meta, doc) in enumerate(zip(ids, metas, docs), start=1):
                    source = meta.get("source", "unknown")
                    evidence_lines.append(
                        f"Source {i} | id={doc_id} | source={source} | metadata={meta}"
                    )
                    context_parts.append(
                        f"""[Source {i}]
ID: {doc_id}
Source Type: {source}
Metadata: {meta}

Content:
{doc}
"""
                    )

                context = "\n\n".join(context_parts)

                prompt = f"""
You are an organizational reasoning assistant.

Rules:
- Answer ONLY from the evidence provided.
- Do not make up facts.
- If evidence is weak or missing, say so clearly.
- Prefer final_document over meeting notes when both exist.
- Use meeting notes over informal chat if they conflict.
- Use Slack and Gmail as supporting evidence.
- At the end, include a section called "Sources used" listing source numbers.

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
                st.markdown(answer_text)

                with st.expander("Evidence retrieved"):
                    for line in evidence_lines:
                        st.write(line)

                    st.divider()

                    for i, (meta, doc) in enumerate(zip(metas, docs), start=1):
                        st.markdown(f"**Source {i}**")
                        st.write(meta)
                        st.code(doc)

                st.session_state.messages.append(
                    {"role": "assistant", "content": answer_text}
                )