import re
from typing import List, Dict, Any


def extract_reason_labels(doc: str) -> List[str]:
    text = (doc or "").lower()

    reason_map = {
        "AI Fit": [
            "reasoning", "ai", "llm", "embedding", "model", "agentic"
        ],
        "Stability": [
            "stability", "stable", "reliable", "robust", "break", "risk"
        ],
        "Time Constraint": [
            "deadline", "hackathon", "limited time", "quick", "timeline", "faster to build"
        ],
        "Simplicity": [
            "simple", "simpler", "less complex", "complexity", "easy to maintain", "lightweight"
        ],
        "Performance": [
            "performance", "fast", "faster", "latency", "efficient", "speed"
        ],
        "Scalability": [
            "scale", "scalable", "scalability", "future growth"
        ],
        "Cost": [
            "cost", "cheap", "budget", "expensive", "resource usage"
        ],
    }

    found = []
    for label, keywords in reason_map.items():
        if any(keyword in text for keyword in keywords):
            found.append(label)

    if not found:
        found = ["General Fit"]

    return found[:2]


def _safe_id(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_]", "_", str(value).strip().lower())


def _clean_line(text: str) -> str:
    text = re.sub(r"\s+", " ", str(text or "")).strip()
    text = re.sub(r"^[\-\*\u2022\:\s]+", "", text)
    return text.strip()


def _wrap_text(text: str, line_len: int = 22, max_lines: int = 2) -> str:
    text = _clean_line(text)
    if not text:
        return ""

    words = text.split()
    lines = []
    current = ""

    for word in words:
        candidate = word if not current else current + " " + word
        if len(candidate) <= line_len:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word

            if len(lines) == max_lines - 1:
                break

    if current and len(lines) < max_lines:
        lines.append(current)

    used_words = sum(len(line.split()) for line in lines)
    if used_words < len(words) and lines:
        lines[-1] = lines[-1].rstrip(" .") + "..."

    return "\n".join(lines)


def extract_decision_label(answer_text: str, question: str = "") -> str:
    """
    Generic extraction:
    1. Prefer the first bullet under 'Final Decision'
    2. Else first useful non-heading line
    3. Else first sentence from answer
    4. Else fall back to user question
    """
    answer = str(answer_text or "").strip()
    question = str(question or "").strip()

    if not answer:
        return _wrap_text(question, 22, 2) if question else "Final\nDecision"

    lines = [line.strip() for line in answer.splitlines() if line.strip()]

    section_stoppers = {
        "why this decision was made",
        "supporting evidence trail",
        "confidence",
        "sources used",
    }

    headings = {
        "final decision",
        "why this decision was made",
        "supporting evidence trail",
        "confidence",
        "sources used",
    }

    # 1) Look under "Final Decision"
    for i, line in enumerate(lines):
        if line.lower().startswith("final decision"):
            for j in range(i + 1, len(lines)):
                nxt = lines[j].strip()
                low = nxt.lower()
                if any(low.startswith(stop) for stop in section_stoppers):
                    break

                cleaned = _clean_line(nxt)
                if cleaned:
                    return _wrap_text(cleaned, 22, 2)

    # 2) First useful non-heading line
    for line in lines:
        cleaned = _clean_line(line)
        low = cleaned.lower()
        if low in headings:
            continue
        if cleaned:
            return _wrap_text(cleaned, 22, 2)

    # 3) First sentence fallback
    first_sentence = re.split(r"[.!?]", answer)[0].strip()
    if first_sentence:
        return _wrap_text(first_sentence, 22, 2)

    # 4) Question fallback
    if question:
        return _wrap_text(question, 22, 2)

    return "Final\nDecision"


def build_influence_graph(
    ids: List[str],
    metas: List[Dict[str, Any]],
    docs: List[str],
    question: str,
    answer_text: str = "",
) -> Dict[str, Any]:
    nodes = []
    edges = []

    added_nodes = set()
    added_edges = set()

    decision_id = "decision_main"
    decision_label = extract_decision_label(answer_text, question)

    def add_node(node_id: str, label: str, node_type: str, meta: Dict[str, Any] | None = None):
        if node_id in added_nodes:
            return

        nodes.append(
            {
                "id": node_id,
                "label": label,
                "type": node_type,
                "meta": meta or {},
            }
        )
        added_nodes.add(node_id)

    def add_edge(source: str, target: str, label: str):
        key = (source, target, label)
        if key in added_edges:
            return

        edges.append(
            {
                "source": source,
                "target": target,
                "label": label,
            }
        )
        added_edges.add(key)

    add_node(
        decision_id,
        decision_label,
        "decision",
        {
            "question": question,
            "answer": answer_text,
        },
    )

    for idx, (doc_id, meta, doc) in enumerate(zip(ids, metas, docs), start=1):
        source_type = meta.get("source", "unknown")

        if source_type == "slack":
            person_label = meta.get("user_name") or meta.get("user", "Unknown")
            source_label = "Slack Discussion"

        elif source_type == "gmail":
            person_label = meta.get("from", "Unknown")
            source_label = "Email Thread"

        elif source_type == "meeting":
            person_label = None
            source_label = "Meeting Notes"

        elif source_type == "final_document":
            person_label = None
            source_label = "Final Document"

        else:
            person_label = None
            source_label = f"Source {idx}"

        source_node_id = f"source_{_safe_id(doc_id)}"
        add_node(
            source_node_id,
            source_label,
            "source",
            {
                "source_type": source_type,
                "raw_id": doc_id,
                "meta": meta,
                "preview": (doc or "")[:280],
            },
        )

        if source_type == "final_document":
            add_edge(source_node_id, decision_id, "confirms")
        elif source_type == "meeting":
            add_edge(source_node_id, decision_id, "finalizes")
        elif source_type == "gmail":
            add_edge(source_node_id, decision_id, "supports")
        else:
            add_edge(source_node_id, decision_id, "influences")

        if person_label:
            person_id = f"person_{_safe_id(person_label)}"
            add_node(
                person_id,
                person_label,
                "person",
                {
                    "name": person_label,
                },
            )

            if source_type == "slack":
                add_edge(person_id, source_node_id, "said")
            elif source_type == "gmail":
                add_edge(person_id, source_node_id, "sent")

        reasons = extract_reason_labels(doc)
        for reason in reasons:
            reason_id = f"reason_{_safe_id(reason)}"
            add_node(
                reason_id,
                reason,
                "reason",
                {
                    "reason": reason,
                },
            )
            add_edge(source_node_id, reason_id, "mentions")
            add_edge(reason_id, decision_id, "shapes")

    return {"nodes": nodes, "edges": edges}