import { Link } from "react-router-dom";
import HeroPanel from "../components/HeroPanel";
import { fetchOrgSummary } from "../services/api";
import { useAsyncData } from "../services/useAsyncData";
import { getStoredUser } from "../services/authStore";

function formatCount(value) {
  return new Intl.NumberFormat("en-US").format(value || 0);
}

export default function OrganizationPage() {
  const { data, loading, error } = useAsyncData(fetchOrgSummary, null);
  const user = getStoredUser();

  const coverageLabel = loading
    ? "..."
    : `${data?.available_source_count ?? 0}/${data?.source_count ?? 4}`;

  const participantPreview = [
    ...(data?.slack_people || []).map((name) => ({ name, type: "Slack" })),
    ...(data?.gmail_senders || []).map((name) => ({ name, type: "Gmail" })),
  ].slice(0, 12);

  return (
    <div className="page">
      <HeroPanel
        eyebrow="Organization"
        title={loading ? "Organization intelligence" : `${data?.org_name || "Memora Labs"} command center`}
        description={`A calm overview of source coverage, contributor signals, and decision records across the organization. Signed in as ${user?.name || "Member"}.`}
      >
        <div className="org-hero-band">
          <div className="org-hero-intro">
            <p className="org-hero-badge">Verified workspace access</p>
            <h3>Everything important is visible in one place.</h3>
            <p>
              Track what is connected, who is active, and whether the decision trail is
              ready for analysis before you move into Memora Core.
            </p>
          </div>

          <div className="org-hero-profile minimal-card">
            <p className="panel-kicker">Current member</p>
            <h3>{user?.name || "Member"}</h3>
            <p className="org-profile-email">{user?.email || "No email available"}</p>
            <div className="org-profile-chip-row">
              <span className="org-profile-chip">Protected access</span>
              <span className="org-profile-chip">Live backend data</span>
            </div>
          </div>
        </div>

        <div className="stats-grid org-stats-grid">
          <div className="minimal-card stat-card org-stat-card org-stat-card-featured">
            <p className="stat-label">Coverage score</p>
            <h3 className="stat-value">{loading ? "..." : `${data?.coverage_score ?? 0}%`}</h3>
            <p className="org-stat-footnote">{coverageLabel} source families active</p>
          </div>
          <div className="minimal-card stat-card org-stat-card">
            <p className="stat-label">Indexed artifacts</p>
            <h3 className="stat-value">{loading ? "..." : formatCount(data?.indexed_artifacts)}</h3>
            <p className="org-stat-footnote">Messages, records, and decision files</p>
          </div>
          <div className="minimal-card stat-card org-stat-card">
            <p className="stat-label">Participants</p>
            <h3 className="stat-value">{loading ? "..." : formatCount(data?.participant_count)}</h3>
            <p className="org-stat-footnote">Contributors visible across sources</p>
          </div>
          <div className="minimal-card stat-card org-stat-card">
            <p className="stat-label">Decision records</p>
            <h3 className="stat-value">{loading ? "..." : formatCount(data?.decision_record_count)}</h3>
            <p className="org-stat-footnote">Meeting notes and final documents</p>
          </div>
        </div>

        {error ? <p className="error-text">{error}</p> : null}

        <div className="org-grid">
          <section className="minimal-card org-panel org-panel-wide">
            <div className="panel-heading">
              <p className="panel-kicker">Knowledge coverage</p>
              <h3>Connected source health</h3>
            </div>
            <p className="panel-copy">
              Memora is strongest when discussion, formal communication, meeting context,
              and final decisions all stay connected.
            </p>
            <div className="org-source-list">
              {(data?.connected_sources || []).map((source) => (
                <div key={source.id} className="org-source-row">
                  <div>
                    <p className="org-source-title">{source.label}</p>
                    <p className="org-source-detail">{source.detail}</p>
                  </div>
                  <div className="org-source-meta">
                    <span className={`org-source-status${source.available ? " org-source-status-live" : ""}`}>
                      {source.available ? "Live" : "Missing"}
                    </span>
                    <span className="org-source-weight">{source.weight}</span>
                  </div>
                </div>
              ))}
            </div>
          </section>

          <section className="minimal-card org-panel">
            <div className="panel-heading">
              <p className="panel-kicker">Operational highlights</p>
              <h3>Signals worth knowing</h3>
            </div>
            <div className="org-highlight-stack">
              {(data?.highlights || []).map((item) => (
                <div key={item.label} className="org-highlight-card">
                  <p className="org-highlight-label">{item.label}</p>
                  <h4>{item.value}</h4>
                </div>
              ))}
            </div>
          </section>

          <section className="minimal-card org-panel">
            <div className="panel-heading">
              <p className="panel-kicker">Activity map</p>
              <h3>Core communication volume</h3>
            </div>
            <div className="org-volume-stack">
              <div className="org-volume-item">
                <div className="org-volume-head">
                  <span>Slack messages</span>
                  <strong>{loading ? "..." : formatCount(data?.slack_messages)}</strong>
                </div>
                <div className="org-volume-bar">
                  <span style={{ width: `${Math.min(((data?.slack_messages || 0) / 60) * 100, 100)}%` }} />
                </div>
              </div>
              <div className="org-volume-item">
                <div className="org-volume-head">
                  <span>Gmail messages</span>
                  <strong>{loading ? "..." : formatCount(data?.gmail_messages)}</strong>
                </div>
                <div className="org-volume-bar">
                  <span style={{ width: `${Math.min(((data?.gmail_messages || 0) / 60) * 100, 100)}%` }} />
                </div>
              </div>
              <div className="org-volume-item">
                <div className="org-volume-head">
                  <span>Gmail threads</span>
                  <strong>{loading ? "..." : formatCount(data?.gmail_threads)}</strong>
                </div>
                <div className="org-volume-bar">
                  <span style={{ width: `${Math.min(((data?.gmail_threads || 0) / 20) * 100, 100)}%` }} />
                </div>
              </div>
            </div>
          </section>

          <section className="minimal-card org-panel org-panel-wide">
            <div className="panel-heading">
              <p className="panel-kicker">Participants</p>
              <h3>Who is shaping the memory trail</h3>
            </div>
            <div className="org-people-cloud">
              {participantPreview.length ? (
                participantPreview.map((person) => (
                  <span key={`${person.type}-${person.name}`} className="org-person-pill">
                    {person.name}
                    <small>{person.type}</small>
                  </span>
                ))
              ) : (
                <p className="panel-copy">Contributor identities will appear here once source data is present.</p>
              )}
            </div>
          </section>

          <section className="minimal-card org-panel">
            <div className="panel-heading">
              <p className="panel-kicker">Decision readiness</p>
              <h3>Evidence stack</h3>
            </div>
            <div className="org-decision-stack">
              <div className="org-decision-card">
                <p className="org-highlight-label">Primary Slack channel</p>
                <h4>{loading ? "..." : data?.top_channel?.label || "No Slack activity yet"}</h4>
                <p>{loading ? "" : `${data?.top_channel?.count ?? 0} messages`}</p>
              </div>
              <div className="org-decision-card">
                <p className="org-highlight-label">Top Gmail subject</p>
                <h4>{loading ? "..." : data?.top_subject?.label || "No Gmail activity yet"}</h4>
                <p>{loading ? "" : `${data?.top_subject?.count ?? 0} mentions`}</p>
              </div>
              <div className="org-decision-assets">
                {(data?.decision_assets || []).length ? (
                  data.decision_assets.map((asset) => (
                    <span key={asset} className="org-asset-pill">
                      {asset}
                    </span>
                  ))
                ) : (
                  <p className="panel-copy">No decision artifacts captured yet.</p>
                )}
              </div>
            </div>
          </section>

          <section className="minimal-card org-panel">
            <div className="panel-heading">
              <p className="panel-kicker">Next moves</p>
              <h3>Continue through the workspace</h3>
            </div>
            <div className="org-action-stack">
              <Link className="org-action-card" to="/memora">
                <span className="org-action-kicker">Analyze</span>
                <strong>Open Memora Core</strong>
                <p>Move from coverage into real decision reasoning.</p>
              </Link>
              <Link className="org-action-card" to="/explorer">
                <span className="org-action-kicker">Inspect</span>
                <strong>Browse Source Explorer</strong>
                <p>Review the evidence library source by source.</p>
              </Link>
            </div>
          </section>
        </div>
      </HeroPanel>
    </div>
  );
}
