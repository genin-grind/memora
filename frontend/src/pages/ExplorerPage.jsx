import { useEffect, useMemo, useState } from "react";
import HeroPanel from "../components/HeroPanel";
import { fetchExplorerWorkspace } from "../services/api";
import { useAsyncData } from "../services/useAsyncData";

const sourceTabs = [
  { id: "all", label: "All" },
  { id: "slack", label: "Slack" },
  { id: "gmail", label: "Gmail" },
  { id: "meeting", label: "Meeting Notes" },
  { id: "final_document", label: "Final Document" },
];

const PAGE_SIZE = 5;

function formatCount(value) {
  return new Intl.NumberFormat("en-US").format(value || 0);
}

function shortenLabel(label, maxLength = 140) {
  const compact = String(label || "").replace(/\n/g, " ").trim();
  return compact.length > maxLength ? `${compact.slice(0, maxLength - 3)}...` : compact;
}

export default function ExplorerPage() {
  const { data, loading, error } = useAsyncData(fetchExplorerWorkspace, null);
  const [activeSource, setActiveSource] = useState("all");
  const [search, setSearch] = useState("");
  const [selectedRecordId, setSelectedRecordId] = useState(null);
  const [pageBySource, setPageBySource] = useState({
    all: 1,
    slack: 1,
    gmail: 1,
    meeting: 1,
    final_document: 1,
  });

  const collections = data?.collections || {};

  const filteredCollections = useMemo(() => {
    const searchValue = search.trim().toLowerCase();
    return Object.fromEntries(
      Object.entries(collections).map(([key, items]) => [
        key,
        (items || []).filter((item) => {
          if (!searchValue) return true;
          return item.search_text?.includes(searchValue);
        }),
      ]),
    );
  }, [collections, search]);

  const allItems = useMemo(() => {
    return [
      ...(filteredCollections.slack || []),
      ...(filteredCollections.gmail || []),
      ...(filteredCollections.meeting || []),
      ...(filteredCollections.final_document || []),
    ];
  }, [filteredCollections]);

  const activeItems = activeSource === "all"
    ? allItems
    : (filteredCollections[activeSource] || []);
  const activePage = pageBySource[activeSource] || 1;
  const totalPages = Math.max(1, Math.ceil(activeItems.length / PAGE_SIZE));
  const safePage = Math.min(activePage, totalPages);
  const paginatedItems = activeItems.slice(
    (safePage - 1) * PAGE_SIZE,
    safePage * PAGE_SIZE,
  );

  useEffect(() => {
    if (activePage !== safePage) {
      setPageBySource((current) => ({
        ...current,
        [activeSource]: safePage,
      }));
    }
  }, [activePage, activeSource, safePage]);

  useEffect(() => {
    setPageBySource((current) => ({
      ...current,
      [activeSource]: 1,
    }));
  }, [activeSource, search]);

  useEffect(() => {
    if (!paginatedItems.length) {
      setSelectedRecordId(null);
      return;
    }
    const stillExists = paginatedItems.some((item) => item.id === selectedRecordId);
    if (!stillExists) {
      setSelectedRecordId(paginatedItems[0].id);
    }
  }, [paginatedItems, selectedRecordId]);

  const selectedRecord =
    paginatedItems.find((item) => item.id === selectedRecordId) || paginatedItems[0] || null;

  return (
    <div className="page">
      <HeroPanel
        eyebrow="Explorer"
        title="Evidence explorer for the full memory trail."
        description="Search across Slack, Gmail, meeting notes, and final records in a cleaner research workspace with a focused reading pane."
      >
        <div className="explorer-hero-band">
          <div className="explorer-callout">
            <p className="explorer-callout-kicker">Research workspace</p>
            <h3>Scan quickly, open deeply, and stay oriented.</h3>
            <p>
              Browse records on the left and read the full source on the right.
            </p>
          </div>

          <div className="explorer-filter-card minimal-card">
            <div className="panel-heading">
              <p className="panel-kicker">Filter desk</p>
              <h3>Refine the evidence set</h3>
            </div>

            <label className="field-label" htmlFor="explorer-search">
              Search
            </label>
            <input
              id="explorer-search"
              className="input"
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              placeholder="Search text, sender, subject, channel..."
            />
          </div>
        </div>

        <div className="stats-grid stats-grid-tight">
          <div className="minimal-card stat-card">
            <p className="stat-label">Slack messages</p>
            <h3 className="stat-value">{loading ? "..." : formatCount(data?.metrics?.slack_messages)}</h3>
          </div>
          <div className="minimal-card stat-card">
            <p className="stat-label">Gmail messages</p>
            <h3 className="stat-value">{loading ? "..." : formatCount(data?.metrics?.gmail_messages)}</h3>
          </div>
          <div className="minimal-card stat-card">
            <p className="stat-label">Gmail threads</p>
            <h3 className="stat-value">{loading ? "..." : formatCount(data?.metrics?.gmail_threads)}</h3>
          </div>
          <div className="minimal-card stat-card stat-card-highlight">
            <p className="stat-label">Indexed sources</p>
            <h3 className="stat-value">{loading ? "..." : formatCount(data?.metrics?.indexed_sources)}</h3>
          </div>
        </div>

        <div className="tab-row">
          {sourceTabs.map((tab) => {
            const count =
              tab.id === "all"
                ? allItems.length
                : (filteredCollections[tab.id]?.length || 0);

            return (
              <button
                key={tab.id}
                type="button"
                className={`tab-chip${activeSource === tab.id ? " tab-chip-active" : ""}`}
                onClick={() => setActiveSource(tab.id)}
              >
                {tab.label}
                <span className="tab-chip-count">{count}</span>
              </button>
            );
          })}
        </div>

        {error ? <p className="error-text">{error}</p> : null}

        <div className="explorer-workspace">
          <section className="minimal-card explorer-list-panel">
            <div className="panel-heading">
              <p className="panel-kicker">Records</p>
              <h3>{sourceTabs.find((tab) => tab.id === activeSource)?.label || "Source records"}</h3>
            </div>
              <p className="panel-copy">
              {loading
                ? "Loading source records..."
                : `${activeItems.length} matching records in this source family.`}
            </p>

            <div className="explorer-record-list">
              {!loading && !activeItems.length ? (
                <div className="explorer-empty-state">
                  <h4>No matching records</h4>
                  <p>Try changing the source tab or clearing the current search.</p>
                </div>
              ) : null}

              {paginatedItems.map((item) => (
                <button
                  key={item.id}
                  type="button"
                  className={`explorer-record-card${selectedRecord?.id === item.id ? " explorer-record-card-active" : ""}`}
                  onClick={() => setSelectedRecordId(item.id)}
                >
                  <div className="explorer-record-badges">
                    {item.badges.map((badge) => (
                      <span key={`${item.id}-${badge}`} className="explorer-badge">
                        {badge}
                      </span>
                    ))}
                  </div>
                  <h4>{item.title}</h4>
                  <p className="timeline-meta">{item.meta}</p>
                  <p className="explorer-record-snippet">{shortenLabel(item.snippet, 140)}</p>
                </button>
              ))}
            </div>

            {!loading && activeItems.length > PAGE_SIZE ? (
              <div className="explorer-pagination">
                <button
                  type="button"
                  className="secondary-button"
                  disabled={safePage === 1}
                  onClick={() =>
                    setPageBySource((current) => ({
                      ...current,
                      [activeSource]: Math.max(1, safePage - 1),
                    }))
                  }
                >
                  Previous
                </button>
                <p className="explorer-pagination-copy">
                  Page {safePage} of {totalPages}
                </p>
                <button
                  type="button"
                  className="secondary-button"
                  disabled={safePage === totalPages}
                  onClick={() =>
                    setPageBySource((current) => ({
                      ...current,
                      [activeSource]: Math.min(totalPages, safePage + 1),
                    }))
                  }
                >
                  Next
                </button>
              </div>
            ) : null}
          </section>

          <aside className="minimal-card explorer-detail-panel">
            <div className="panel-heading">
              <p className="panel-kicker">Source reader</p>
              <h3>{selectedRecord ? selectedRecord.title : "Select a record"}</h3>
            </div>

            {selectedRecord ? (
              <>
                <div className="explorer-detail-meta">
                  <span className="explorer-detail-pill">
                    {selectedRecord?.badges?.[0] || sourceTabs.find((tab) => tab.id === activeSource)?.label}
                  </span>
                  <span className="explorer-detail-pill">
                    {shortenLabel(selectedRecord.meta, 80)}
                  </span>
                </div>
                <pre className="trace-block trace-block-text explorer-reader">
                  {selectedRecord.content}
                </pre>
              </>
            ) : (
              <div className="explorer-empty-state explorer-empty-state-detail">
                <h4>Choose a record to read</h4>
                <p>The full source text and metadata will appear here.</p>
              </div>
            )}
          </aside>
        </div>
      </HeroPanel>
    </div>
  );
}
