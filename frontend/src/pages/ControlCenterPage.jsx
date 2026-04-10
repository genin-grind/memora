import { useState } from "react";
import HeroPanel from "../components/HeroPanel";
import { fetchSyncStatus, runSyncNow } from "../services/api";
import { useAsyncData } from "../services/useAsyncData";

export default function ControlCenterPage() {
  const { data, loading, error } = useAsyncData(fetchSyncStatus, null);
  const [running, setRunning] = useState(false);
  const [runMessage, setRunMessage] = useState("");
  const [intervalChoice, setIntervalChoice] = useState(90);
  const [overrideStatus, setOverrideStatus] = useState(null);

  const currentStatus = overrideStatus || data;

  async function handleRunSync() {
    try {
      setRunning(true);
      setRunMessage("");
      const result = await runSyncNow();
      setRunMessage(result.message || "Sync completed.");
      setOverrideStatus(result.sync_status || null);
    } catch (runError) {
      setRunMessage(runError.message || "Unable to run sync right now.");
    } finally {
      setRunning(false);
    }
  }

  const sources = currentStatus?.sources || [];
  const connectedCount = sources.filter((item) =>
    ["Connected", "Present"].includes(item.status),
  ).length;

  return (
    <div className="page">
      <HeroPanel
        eyebrow="Control"
        title="Operations control room for ingestion and system readiness."
        description="Run manual syncs, inspect source state, and keep the memory pipeline healthy before you present the experience."
      >
        <div className="control-hero-band">
          <div className="control-callout">
            <p className="control-callout-kicker">Operations center</p>
            <h3>Control ingestion, readiness, and source health.</h3>
            <p>
              A compact operations surface for sync visibility and source readiness.
            </p>
          </div>

          <div className="minimal-card control-command-card">
            <div className="panel-heading">
              <p className="panel-kicker">Manual sync</p>
              <h3>Refresh live data now</h3>
            </div>
            <p className="panel-copy">
              Pull the newest Slack and Gmail records into the workspace without
              leaving the app shell.
            </p>
            <button
              type="button"
              className="primary-button"
              disabled={running}
              onClick={handleRunSync}
            >
              {running ? "Syncing now" : "Sync Now"}
            </button>
            <p className="control-status-line">
              Last sync: {loading && !currentStatus ? "..." : currentStatus?.last_sync_display || "Not synced yet"}
            </p>
            {runMessage ? <p className="success-text">{runMessage}</p> : null}
            {error ? <p className="error-text">{error}</p> : null}
          </div>
        </div>

        <div className="stats-grid stats-grid-tight">
          <div className="minimal-card stat-card control-stat-card control-stat-card-featured">
            <p className="stat-label">Connected sources</p>
            <h3 className="stat-value">{loading ? "..." : `${connectedCount}/${sources.length || 4}`}</h3>
            <p className="control-stat-copy">Live ingestion surface coverage</p>
          </div>
          <div className="minimal-card stat-card control-stat-card">
            <p className="stat-label">Recommended interval</p>
            <h3 className="stat-value">{loading && !currentStatus ? "..." : `${currentStatus?.recommended_interval || 90}s`}</h3>
            <p className="control-stat-copy">Balanced cadence for demos</p>
          </div>
          <div className="minimal-card stat-card control-stat-card">
            <p className="stat-label">Static decision docs</p>
            <h3 className="stat-value">
              {loading ? "..." : sources.filter((item) => ["meeting", "final_document"].includes(item.id) && item.count > 0).length}
            </h3>
            <p className="control-stat-copy">Meeting notes and final records present</p>
          </div>
          <div className="minimal-card stat-card control-stat-card">
            <p className="stat-label">Live feeds</p>
            <h3 className="stat-value">
              {loading ? "..." : sources.filter((item) => ["slack", "gmail"].includes(item.id) && item.count > 0).length}
            </h3>
            <p className="control-stat-copy">Slack and Gmail currently populated</p>
          </div>
        </div>

        <div className="control-grid">
          <section className="minimal-card control-panel control-panel-wide">
            <div className="panel-heading">
              <p className="panel-kicker">Source state</p>
              <h3>What the pipeline sees right now</h3>
            </div>
            <div className="control-source-list">
              {sources.map((source) => (
                <div key={source.id} className="control-source-row">
                  <div>
                    <p className="control-source-title">{source.label}</p>
                    <p className="control-source-detail">{source.detail}</p>
                  </div>
                  <div className="control-source-meta">
                    <span className={`control-source-status control-source-status-${source.status.toLowerCase().replace(/\s+/g, "-")}`}>
                      {source.status}
                    </span>
                    <strong>{source.count}</strong>
                  </div>
                </div>
              ))}
            </div>
          </section>

          <section className="minimal-card control-panel">
            <div className="panel-heading">
              <p className="panel-kicker">Interval presets</p>
              <h3>Sync cadence</h3>
            </div>
            <div className="control-interval-row">
              {(currentStatus?.interval_options || [60, 90, 120]).map((interval) => (
                <button
                  key={interval}
                  type="button"
                  className={`control-interval-chip${intervalChoice === interval ? " control-interval-chip-active" : ""}`}
                  onClick={() => setIntervalChoice(interval)}
                >
                  {interval}s
                </button>
              ))}
            </div>
            <div className="control-note-card">
              <p className="control-note-title">Selected profile</p>
              <p>
                {intervalChoice === 60
                  ? "High refresh"
                  : intervalChoice === 90
                    ? "Balanced"
                    : "Low noise"}
              </p>
            </div>
          </section>

          <section className="minimal-card control-panel">
            <div className="panel-heading">
              <p className="panel-kicker">System summary</p>
              <h3>Readiness snapshot</h3>
            </div>
            <div className="control-note-stack">
              <div className="control-note-card">
                <p className="control-note-title">Live feeds</p>
                <p>Slack and Gmail</p>
              </div>
              <div className="control-note-card">
                <p className="control-note-title">Decision records</p>
                <p>Meeting notes and final document</p>
              </div>
            </div>
          </section>
        </div>
      </HeroPanel>
    </div>
  );
}
