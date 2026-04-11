import { useMemo, useState } from "react";
import HeroPanel from "../components/HeroPanel";
import { queryMemora } from "../services/api";

const examples = [
  "Why did we choose FastAPI over MERN/Node?",
  "What final tech stack was approved?",
  "Why is Neo4j optional?",
  "What was finalized in the meeting?",
];

const tabs = [
  { id: "answer", label: "Final Answer" },
  { id: "evidence", label: "Evidence" },
  { id: "timeline", label: "Reasoning Flow" },
  { id: "graph", label: "Decision Graph" },
  { id: "trace", label: "Raw Trace" },
];

const graphTypeLabel = {
  decision: "Final Decision",
  source: "Source",
  person: "People",
  reason: "Reason",
};

const graphColumnOrder = ["person", "source", "reason", "decision"];

function parseAnswerSections(answer) {
  const lines = String(answer || "").split("\n").map((line) => line.trim());
  const sections = [];
  let current = null;

  for (const line of lines) {
    if (!line) continue;
    if (!line.startsWith("-")) {
      current = { title: line, items: [] };
      sections.push(current);
      continue;
    }
    if (!current) {
      current = { title: "Summary", items: [] };
      sections.push(current);
    }
    current.items.push(line.replace(/^-\s*/, ""));
  }

  return sections;
}

function shortenLabel(label, maxLength = 36) {
  const compact = String(label || "").replace(/\n/g, " ").trim();
  return compact.length > maxLength ? `${compact.slice(0, maxLength - 3)}...` : compact;
}

function getConfidenceWidth(confidence) {
  const value = String(confidence || "").toLowerCase();
  if (value.includes("high")) return "84%";
  if (value.includes("medium")) return "62%";
  if (value.includes("low")) return "36%";
  return "50%";
}

function groupEvidenceBySource(evidence) {
  const groups = {
    document: [],
    gmail: [],
    slack: [],
    meeting: [],
  };

  evidence.forEach((item) => {
    const key = String(item.source || "").toLowerCase();
    if (key.includes("doc")) groups.document.push(item);
    else if (key.includes("gmail")) groups.gmail.push(item);
    else if (key.includes("slack")) groups.slack.push(item);
    else groups.meeting.push(item);
  });

  return groups;
}

function getNodeFill(type) {
  if (type === "decision") return "#13261d";
  if (type === "source") return "#17283c";
  if (type === "person") return "#2e1f52";
  return "#463115";
}

function getNodeStroke(type) {
  if (type === "decision") return "#62b48b";
  if (type === "source") return "#6ea8dc";
  if (type === "person") return "#a68bff";
  return "#e3b262";
}

function getNodeDimensions(type) {
  if (type === "decision") {
    return { width: 220, height: 96 };
  }
  return { width: 180, height: 72 };
}

function buildGraphLayout(graph) {
  const leftPadding = 160;
  const rightPadding = 180;
  const columnGap = 280;
  const rowGap = 118;
  const topPadding = 120;
  const bottomPadding = 180;
  const nodes = graph?.nodes || [];
  const edges = graph?.edges || [];

  const grouped = {
    person: nodes.filter((node) => node.type === "person"),
    source: nodes.filter((node) => node.type === "source"),
    reason: nodes.filter((node) => node.type === "reason"),
    decision: nodes.filter((node) => node.type === "decision"),
  };

  const tallestColumnCount = Math.max(
    grouped.person.length,
    grouped.source.length,
    grouped.reason.length,
    grouped.decision.length,
    1,
  );
  const width = leftPadding + rightPadding + Math.max(graphColumnOrder.length - 1, 0) * columnGap;
  const height =
    topPadding +
    bottomPadding +
    Math.max(tallestColumnCount - 1, 0) * rowGap +
    Math.max(tallestColumnCount - 4, 0) * 22;

  const positioned = new Map();

  graphColumnOrder.forEach((type, columnIndex) => {
    const columnNodes = grouped[type];
    const x = leftPadding + columnIndex * columnGap;
    const totalHeight = Math.max(columnNodes.length - 1, 0) * rowGap;
    const contentTop = topPadding;
    const contentHeight = height - topPadding - bottomPadding;
    const startY = contentTop + contentHeight / 2 - totalHeight / 2;

    columnNodes.forEach((node, index) => {
      const dimensions = getNodeDimensions(type);
      positioned.set(node.id, {
        ...node,
        x,
        y: startY + index * rowGap,
        ...dimensions,
      });
    });
  });

  return {
    width,
    height,
    nodes: Array.from(positioned.values()),
    edges,
  };
}

function GraphCanvas({ graph }) {
  const layout = useMemo(() => buildGraphLayout(graph), [graph]);
  const [activeNodeId, setActiveNodeId] = useState(
    layout.nodes.find((node) => node.type === "decision")?.id || null,
  );

  const activeNode =
    layout.nodes.find((node) => node.id === activeNodeId) || layout.nodes[0] || null;

  const highlightedEdges = layout.edges.filter(
    (edge) => edge.source === activeNodeId || edge.target === activeNodeId,
  );

  const highlightedNodeLabels = highlightedEdges
    .map((edge) => {
      const connectedId = edge.source === activeNodeId ? edge.target : edge.source;
      const connectedNode = layout.nodes.find((node) => node.id === connectedId);
      return connectedNode ? shortenLabel(connectedNode.label, 30) : connectedId;
    })
    .filter(Boolean);

  const storyTitle = activeNode
    ? activeNode.type === "decision"
      ? "The final outcome"
      : activeNode.type === "reason"
        ? "A key deciding factor"
        : activeNode.type === "source"
          ? "A supporting source"
          : "A contributing person"
    : "Decision story";

  const plainLanguageSummary = activeNode
    ? activeNode.type === "decision"
      ? "This is the team's final call. Everything else in the map explains how the team arrived here."
      : activeNode.type === "reason"
        ? "This is a deciding factor. It captures one of the ideas or tradeoffs that pushed the team toward the outcome."
        : activeNode.type === "source"
          ? "This is supporting proof. It points to where the decision story was actually recorded."
          : "This is a contributor. It shows who helped shape the conversation or evidence trail."
    : "This map shows how people, evidence, and reasoning come together into one final decision.";

  if (!layout.nodes.length) {
    return <p className="panel-copy">No graph data available for this result yet.</p>;
  }

  return (
    <div className="graph-stage">
      <div
        className="graph-canvas-shell"
        style={{
          minHeight: `${layout.height + 72}px`,
        }}
      >
        <svg
          className="graph-svg graph-svg-wide"
          viewBox={`0 0 ${layout.width} ${layout.height}`}
          preserveAspectRatio="xMidYMid meet"
          style={{
            minWidth: `${layout.width}px`,
            minHeight: `${layout.height}px`,
          }}
        >
          {graphColumnOrder.map((type, index) => (
            <g key={type}>
              <text
                x={160 + index * 280}
                y={42}
                textAnchor="middle"
                className="graph-column-title"
              >
                {graphTypeLabel[type]}
              </text>
            </g>
          ))}

          {layout.edges.map((edge, index) => {
            const source = layout.nodes.find((node) => node.id === edge.source);
            const target = layout.nodes.find((node) => node.id === edge.target);
            if (!source || !target) return null;

            const sourceX = source.x + source.width / 2;
            const sourceY = source.y;
            const targetX = target.x - target.width / 2;
            const targetY = target.y;
            const curveX = (sourceX + targetX) / 2;
            const isActive = edge.source === activeNodeId || edge.target === activeNodeId;

            return (
              <g key={`${edge.source}-${edge.target}-${index}`}>
                <path
                  d={`M ${sourceX} ${sourceY} C ${curveX} ${sourceY}, ${curveX} ${targetY}, ${targetX} ${targetY}`}
                  className={`graph-line${isActive ? " graph-line-active" : ""}`}
                />
                <text
                  x={curveX}
                  y={(sourceY + targetY) / 2 - 10}
                  textAnchor="middle"
                  className={`graph-edge-label${isActive ? " graph-edge-label-active" : ""}`}
                >
                  {edge.label}
                </text>
              </g>
            );
          })}

          {layout.nodes.map((node) => {
            const isActive = node.id === activeNodeId;
            const x = node.x - node.width / 2;
            const y = node.y - node.height / 2;
            const title = shortenLabel(node.label, node.type === "decision" ? 42 : 28);

            return (
              <g
                key={node.id}
                onClick={() => setActiveNodeId(node.id)}
                className="graph-node-group"
              >
                <rect
                  x={x}
                  y={y}
                  rx="22"
                  ry="22"
                  width={node.width}
                  height={node.height}
                  fill={getNodeFill(node.type)}
                  stroke={getNodeStroke(node.type)}
                  strokeWidth={isActive ? 3 : 2}
                  className={isActive ? "graph-rect-active" : ""}
                />
                <text x={node.x} y={node.y - 8} textAnchor="middle" className="graph-sub-label graph-sub-label-strong">
                  {graphTypeLabel[node.type]}
                </text>
                <text x={node.x} y={node.y + 16} textAnchor="middle" className="graph-label">
                  {title}
                </text>
              </g>
            );
          })}
        </svg>
      </div>

      <div className="graph-legend-row">
        <div className="graph-legend-pill graph-legend-person">People</div>
        <div className="graph-legend-pill graph-legend-source">Source</div>
        <div className="graph-legend-pill graph-legend-reason">Reason</div>
        <div className="graph-legend-pill graph-legend-decision">Final Decision</div>
      </div>

      <div className="graph-inspector minimal-card">
        <div className="panel-heading">
          <p className="panel-kicker">Decision Story</p>
          <h3>{storyTitle}</h3>
        </div>
        {activeNode ? (
          <>
            <p className="graph-inspector-type">
              {graphTypeLabel[activeNode.type] || activeNode.type}
            </p>
            <div className="graph-story-hero">
              <p className="graph-story-node">{shortenLabel(activeNode.label, 64)}</p>
              <p className="graph-inspector-summary">{plainLanguageSummary}</p>
            </div>
            <div className="graph-story-grid">
              <div className="graph-story-card">
                <p className="graph-story-title">How to read it</p>
                <p>Move left to right: people create signals, sources preserve them, reasons concentrate them, and the final decision closes the chain.</p>
              </div>
              <div className="graph-story-card">
                <p className="graph-story-title">Why it matters</p>
                <p>This makes the decision explainable. Instead of only seeing the outcome, you can see the path that led there.</p>
              </div>
            </div>
            <div className="graph-story-links">
              <p className="graph-story-title">Connected to</p>
              <div className="graph-story-chip-row">
                {highlightedNodeLabels.map((label) => (
                  <span key={label} className="graph-story-chip">
                    {label}
                  </span>
                ))}
              </div>
            </div>
            <p className="graph-footnote">
              Non-technical shortcut: left side is who and where, middle is why, right side is what the team finally chose.
            </p>
          </>
        ) : null}
      </div>
    </div>
  );
}

export default function MemoraPage() {
  const [question, setQuestion] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [activeTab, setActiveTab] = useState("answer");
  const [selectedEvidenceId, setSelectedEvidenceId] = useState(null);
  const [answerSourceOpen, setAnswerSourceOpen] = useState(false);

  const selectedEvidence = useMemo(() => {
    if (!result?.evidence?.length) return null;
    if (!selectedEvidenceId) return result.evidence[0];
    return result.evidence.find((item) => item.id === selectedEvidenceId) || result.evidence[0];
  }, [result, selectedEvidenceId]);

  const answerSections = useMemo(
    () => parseAnswerSections(result?.answer || ""),
    [result?.answer],
  );

  const groupedEvidence = useMemo(() => {
    if (!result?.evidence?.length) return {};
    return groupEvidenceBySource(result.evidence);
  }, [result]);

  async function handleSubmit(event) {
    event.preventDefault();
    if (!question.trim()) {
      setError("Enter a question to analyze.");
      return;
    }

    setLoading(true);
    setError("");

    try {
      const response = await queryMemora(question);
      setResult(response);
      setSelectedEvidenceId(response.evidence?.[0]?.id || null);
      setAnswerSourceOpen(false);
      setActiveTab("answer");
    } catch (err) {
      setError(err.message || "Unable to analyze the question right now.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="page">
      <HeroPanel
        eyebrow="Memora Core"
        title="Ask one question and reconstruct the full decision trail."
        description="See the decision, the evidence behind it, the reasoning that shaped it, and the final outcome in one calm workspace."
      >
        <form className="query-layout" onSubmit={handleSubmit}>
          <div className="query-card query-card-large">
            <div className="query-card-inner">
              <div className="panel-heading">
                <p className="panel-kicker">Decision Query</p>
                <h3>Analyze organizational reasoning</h3>
              </div>
              <p className="panel-copy">
                Ask how or why a decision was made. The answer is grounded in your
                ingested Slack, Gmail, meeting transcript, and final document data.
              </p>
              <textarea
                className="text-area"
                value={question}
                onChange={(event) => setQuestion(event.target.value)}
                placeholder="Why did we choose FastAPI over MERN/Node?"
                rows={4}
              />
              <div className="example-row">
                {examples.map((example) => (
                  <button
                    key={example}
                    type="button"
                    className="example-chip"
                    onClick={() => setQuestion(example)}
                  >
                    {example}
                  </button>
                ))}
              </div>
            </div>
            <button className="primary-button primary-button-wide" type="submit" disabled={loading}>
              {loading ? "Analyzing" : "Analyze Decision"}
            </button>
            {error ? <p className="error-text query-error">{error}</p> : null}
          </div>

          <div className="query-side-stack">
            <div className="minimal-card query-side-card">
              <div className="panel-heading">
                <p className="panel-kicker">Sources</p>
                <h3>Priority model</h3>
              </div>
              <div className="status-list">
                <div className="status-row"><span>Final document</span><strong>Highest weight</strong></div>
                <div className="status-row"><span>Meeting notes</span><strong>Consensus layer</strong></div>
                <div className="status-row"><span>Gmail</span><strong>Formal context</strong></div>
                <div className="status-row"><span>Slack</span><strong>Early discussion</strong></div>
              </div>
            </div>

            <div className="hero-mini-metrics">
              <div className="metric-mini-card"><span>4</span><p>Primary source families</p></div>
              <div className="metric-mini-card"><span>Live</span><p>Traceability across tabs</p></div>
            </div>
          </div>
        </form>

        {result ? (
          <>
            {answerSourceOpen && selectedEvidence ? (
              <div className="source-focus-overlay" onClick={() => setAnswerSourceOpen(false)}>
                <div
                  className="source-focus-modal"
                  onClick={(event) => event.stopPropagation()}
                >
                  <button
                    type="button"
                    className="source-focus-close"
                    onClick={() => setAnswerSourceOpen(false)}
                  >
                    Close
                  </button>
                  <div className="source-focus-header">
                    <p className="panel-kicker">Opened Source</p>
                    <h3>{selectedEvidence.label}</h3>
                    <p className="source-focus-meta">{selectedEvidence.meta_display}</p>
                  </div>
                  <div className="source-focus-chip-row">
                    <span className="source-focus-chip">{selectedEvidence.source}</span>
                    <span className="source-focus-chip">Rank #{selectedEvidence.rank}</span>
                  </div>
                  <div className="source-focus-summary">
                    <p className="evidence-snippet">{selectedEvidence.snippet}</p>
                    <p className="panel-copy">{selectedEvidence.relevance_note}</p>
                  </div>
                  <pre className="trace-block trace-block-text source-focus-reader">
                    {selectedEvidence.full_text}
                  </pre>
                </div>
              </div>
            ) : null}


            <div className="stats-grid stats-grid-tight">
              <p className="ai-label">🧠 AI Decision Engine Output</p>
              <div className="minimal-card stat-card"><p className="stat-label">Evidence</p><h3 className="stat-value">{result.metrics.evidence_retrieved}</h3></div>
              <div className="minimal-card stat-card"><p className="stat-label">Source types</p><h3 className="stat-value">{result.metrics.source_types}</h3></div>
              <div className="minimal-card stat-card stat-card-highlight"><p className="stat-label">Strongest source</p><h3 className="stat-value stat-value-small">{result.metrics.strongest_source}</h3></div>
              <div className="minimal-card stat-card stat-card-highlight">
                <p className="stat-label">Confidence</p>
                <div className="confidence-bar">
                  <div
                    className="confidence-fill"
                    style={{ width: getConfidenceWidth(result.metrics.confidence) }}
                  />
                </div>
                <p className="confidence-text">{result.metrics.confidence}</p>
              </div>
            </div>

            <div className="analysis-ready-banner">
              Analysis ready. Explore the tabs below to trace how the decision was formed.
            </div>

            <div className="tab-row">
              {tabs.map((tab) => (
                <button
                  key={tab.id}
                  type="button"
                  className={`tab-chip${activeTab === tab.id ? " tab-chip-active" : ""}`}
                  onClick={() => setActiveTab(tab.id)}
                >
                  {tab.label}
                </button>
              ))}
            </div>

            {activeTab === "answer" ? (
              <div className={`answer-dashboard${answerSourceOpen ? " answer-dashboard-blurred" : ""}`}>
                <div className="answer-sections-grid">
                  {answerSections.map((section, index) => (
                    <section key={section.title} className={`minimal-card answer-section-card ${index === 0 ? "hero-card" : ""} answer-section-card-${index + 1}`}>
                      <div className="answer-section-head">
                        <p className="panel-kicker">{section.title}</p>
                        <span className="answer-section-orbit" />
                      </div>
                      <div className="answer-section-items">
                        {section.items.length ? section.items.map((item) => (
                          <div key={item} className="bullet-row">
                            <span>✔</span>
                            <p>{item}</p>
                          </div>
                        )) : <p>{section.title}</p>}
                      </div>
                    </section>
                  ))}
                </div>

                <div className="answer-side-rail">
                  <div className="minimal-card source-open-card">
                    <div className="panel-heading">
                      <p className="panel-kicker">Open Sources</p>
                      <h3>Supporting artifacts</h3>
                    </div>
                    <div className="open-source-grid">
                      {Object.entries(groupedEvidence).map(([group, items]) => (
                        items.length ? (
                            <div key={group} className="evidence-group">
                              <p className="group-title">{group.toUpperCase()}</p>
                              {items.map((item) => (
                                <button
                                  key={item.id}
                                  type="button"
                                  className={`source-row${selectedEvidence?.id === item.id ? " source-row-active" : ""}`}
                                  onClick={() => {
                                    setSelectedEvidenceId(item.id);
                                    setAnswerSourceOpen(true);
                                  }}
                                >
                                  <div className="source-row-main">
                                    <p className="source-row-title">{shortenLabel(item.label, 34)}</p>
                                    <p className="source-row-meta">
                                      {item.source} · Rank #{item.rank}
                                    </p>
                                  </div>
                                  <span className="source-row-arrow">↗</span>
                                </button>
                              ))}
                            </div>
                          ) : null
                      ))}
                    </div>

                    {selectedEvidence ? (
                      <div className="opened-source-panel">
                        <div>
                          <p className="opened-source-kicker">{selectedEvidence.source}</p>
                          <h4>{selectedEvidence.label}</h4>
                        </div>
                        <p className="timeline-meta">{selectedEvidence.meta_display}</p>
                        <p className="evidence-snippet">{selectedEvidence.snippet}</p>
                        <div className="opened-source-footer">
                          <p className="panel-copy">{selectedEvidence.relevance_note}</p>
                          <button
                            type="button"
                            className="secondary-button"
                            onClick={() => setAnswerSourceOpen(true)}
                          >
                            Open in Focus View
                          </button>
                        </div>
                      </div>
                    ) : null}
                  </div>
                </div>
              </div>
            ) : null}

            {activeTab === "evidence" ? (
              <div className="evidence-layout">
                <div className="evidence-grid">
                  {result.evidence.map((item) => (
                    <article
                      key={item.id}
                      className={`minimal-card evidence-card${selectedEvidence?.id === item.id ? " evidence-card-active" : ""}`}
                      onClick={() => setSelectedEvidenceId(item.id)}
                    >
                      <div className="evidence-topline">
                        <span className="evidence-rank">#{item.rank}</span>
                        <span className="evidence-source">{item.source}</span>
                      </div>
                      <h4>{item.label}</h4>
                      <p className="timeline-meta">{item.meta_display}</p>
                      <p className="evidence-snippet">{item.snippet}</p>
                    </article>
                  ))}
                </div>

                <aside className="minimal-card evidence-detail-card">
                  {selectedEvidence ? (
                    <>
                      <div className="panel-heading">
                        <p className="panel-kicker">Source Detail</p>
                        <h3>{selectedEvidence.label}</h3>
                      </div>
                      <p className="timeline-meta">{selectedEvidence.meta_display}</p>
                      <p className="panel-copy">{selectedEvidence.relevance_note}</p>
                      <pre className="trace-block trace-block-text evidence-detail-text">{selectedEvidence.full_text}</pre>
                    </>
                  ) : (
                    <p className="panel-copy">Select a source card to inspect it in detail.</p>
                  )}
                </aside>
              </div>
            ) : null}

            {activeTab === "timeline" ? (
              <div className="minimal-card timeline-card timeline-card-wide">
                <div className="panel-heading">
                  <p className="panel-kicker">Timeline</p>
                  <h3>Reasoning flow</h3>
                </div>

                <div className="timeline-flow">
                  {result.timeline.map((item, index) => {
                    const isLast = index === result.timeline.length - 1;

                    return (
                      <div
                        key={`${item.source}-${item.title}-${index}`}
                        className={`timeline-flow-card${isLast ? " timeline-flow-card-final" : ""}`}
                      >
                        <div className="timeline-flow-top">
                          <div className="timeline-step-badge">Step {index + 1}</div>
                          <div className="timeline-source-badge">{item.source}</div>
                        </div>

                        <p className="timeline-title">{item.title}</p>
                        <p className="timeline-meta">{item.meta}</p>
                        <p className="timeline-body">{shortenLabel(item.text, 160)}</p>

                        {!isLast ? (
                          <div className="timeline-arrow">→</div>
                        ) : (
                          <div className="timeline-arrow timeline-arrow-final">✓</div>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            ) : null}

            {activeTab === "graph" ? (
              <div className="minimal-card graph-card graph-card-hero">
                <div className="panel-heading">
                  <p className="panel-kicker">Decision Graph</p>
                  <h3>People, sources, reasons, and the final decision</h3>
                </div>
                <GraphCanvas graph={result.graph} />
              </div>
            ) : null}

            {activeTab === "trace" ? (
              <div className="trace-list">
                {result.evidence.map((item) => (
                  <div key={item.id} className="minimal-card trace-card">
                    <div className="panel-heading">
                      <p className="panel-kicker">Source {item.rank}</p>
                      <h3>{item.label}</h3>
                    </div>
                    <p className="trace-line"><strong>ID:</strong> {item.id}</p>
                    <p className="trace-line"><strong>Source:</strong> {item.source}</p>
                    <p className="trace-line"><strong>Meta:</strong> {item.meta_display}</p>
                    <pre className="trace-block">{JSON.stringify(item.metadata, null, 2)}</pre>
                    <pre className="trace-block trace-block-text">{item.full_text}</pre>
                  </div>
                ))}
              </div>
            ) : null}
          </>
        ) : null}
      </HeroPanel>
    </div>
  );
}
