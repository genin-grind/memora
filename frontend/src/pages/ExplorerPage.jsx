import { useEffect, useMemo, useState } from "react";
import HeroPanel from "../components/HeroPanel";
import { fetchExplorerWorkspace } from "../services/api";
import { useAsyncData } from "../services/useAsyncData";

const sourceTabs = [
  { id: "slack", label: "Slack" },
  { id: "gmail", label: "Gmail" },
  { id: "meeting", label: "Meeting Notes" },
  { id: "final_document", label: "Final Document" },
];

const PAGE_SIZE = 10;

function formatCount(value) {
  return new Intl.NumberFormat("en-US").format(value || 0);
}

export default function ExplorerPage() {
  const { data, loading, error } = useAsyncData(fetchExplorerWorkspace, null);
  const [activeSource, setActiveSource] = useState("slack");
  const [search, setSearch] = useState("");
  const [showFullText, setShowFullText] = useState(false);
  const [selectedRecordId, setSelectedRecordId] = useState(null);
  const [pageBySource, setPageBySource] = useState({
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

  const activeItems = filteredCollections[activeSource] || [];
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
              This view is built for demo clarity: a fast record list on the left,
              a clean source reader on the right, and one filter model across all
              source families.
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

            <div className="explorer-toggle-row">
              <div>
                <p className="explorer-toggle-label">Reading mode</p>
                <p className="explorer-toggle-copy">
                  Switch between short previews and full source text in the detail pane.
                </p>
              </div>
              <button
                type="button"
                className={`explorer-toggle${showFullText ? " explorer-toggle-active" : ""}`}
                onClick={() => setShowFullText((value) => !value)}
              >
                {showFullText ? "Full text" : "Preview"}
              </button>
            </div>
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
          {sourceTabs.map((tab) => (
            <button
              key={tab.id}
              type="button"
              className={`tab-chip${activeSource === tab.id ? " tab-chip-active" : ""}`}
              onClick={() => setActiveSource(tab.id)}
            >
              {tab.label}
            </button>
          ))}
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
                  <p className="explorer-record-snippet">{item.snippet}</p>
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
                    {sourceTabs.find((tab) => tab.id === activeSource)?.label}
                  </span>
                  <span className="explorer-detail-pill">{selectedRecord.meta}</span>
                </div>
                <p className="panel-copy">
                  Use this pane to read the full artifact without losing your place in the result list.
                </p>
                <pre className="trace-block trace-block-text explorer-reader">
                  {showFullText ? selectedRecord.content : selectedRecord.snippet}
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
