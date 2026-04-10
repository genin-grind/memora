import { useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import HeroPanel from "../components/HeroPanel";
import { loginWithEmail } from "../services/api";
import { getStoredUser, storeUser } from "../services/authStore";

export default function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const [email, setEmail] = useState("");
  const [accessKey, setAccessKey] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (getStoredUser()) {
      navigate("/organization", { replace: true });
    }
  }, [navigate]);

  async function handleSubmit(event) {
    event.preventDefault();
    setLoading(true);
    setError("");
    setMessage("");

    try {
      const result = await loginWithEmail(email, accessKey);
      storeUser(result.user);
      setMessage(`Access granted for ${result.user.name}`);
      const destination = location.state?.from || "/organization";
      window.setTimeout(() => {
        navigate(destination, { replace: true });
      }, 400);
    } catch (err) {
      setError(err.message || "Unable to verify access");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="page page-login">
      <HeroPanel
        eyebrow="Secure Entry"
        title="Secure entry to the Memora organization workspace."
        description="Use your verified organization email and your organization access key to unlock the workspace."
      >
        <div className="login-layout">
          <form className="minimal-card login-card" onSubmit={handleSubmit}>
            <div className="panel-heading">
              <p className="panel-kicker">Member Access</p>
              <h3>Sign in</h3>
            </div>
            <p className="panel-copy">
              Enter your organization email and your organization access key.
            </p>
            <label className="field-label" htmlFor="email">
              Organization Email
            </label>
            <input
              id="email"
              className="input"
              type="email"
              placeholder="name@company.com"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
            />
            <label className="field-label" htmlFor="accessKey">
              Organization Access Key
            </label>
            <input
              id="accessKey"
              className="input"
              type="password"
              placeholder="Organization-issued access key"
              value={accessKey}
              onChange={(event) => setAccessKey(event.target.value)}
            />
            <button className="primary-button" type="submit" disabled={loading}>
              {loading ? "Verifying" : "Continue"}
            </button>
            {message ? <p className="success-text">{message}</p> : null}
            {error ? <p className="error-text">{error}</p> : null}
          </form>

          <div className="login-notes">
            <div className="minimal-card">
              <div className="panel-heading">
                <p className="panel-kicker">What You Unlock</p>
                <h3>Organization Workspace</h3>
              </div>
              <p className="panel-copy">
                Access the internal dashboard, source explorer, control room, and
                the decision reasoning workspace after verification.
              </p>
            </div>
            <div className="minimal-card">
              <div className="panel-heading">
                <p className="panel-kicker">Access Model</p>
                <h3>Organization-issued entry</h3>
              </div>
              <p className="panel-copy">
                Only verified members with the organization access key can enter the
                workspace.
              </p>
            </div>
          </div>
        </div>
      </HeroPanel>
    </div>
  );
}
