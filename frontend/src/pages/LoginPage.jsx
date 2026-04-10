import { useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import HeroPanel from "../components/HeroPanel";
import { loginWithEmail } from "../services/api";
import { getStoredUser, storeUser } from "../services/authStore";

export default function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const [email, setEmail] = useState("");
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
      const result = await loginWithEmail(email);
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
        title="Quiet, secure access to your organization memory."
        description="A cleaner protected entry flow for the product demo. Sign in with a verified org email to unlock the workspace."
      >
        <div className="login-layout">
          <form className="minimal-card login-card" onSubmit={handleSubmit}>
            <div className="panel-heading">
              <p className="panel-kicker">Member Access</p>
              <h3>Sign in</h3>
            </div>
            <p className="panel-copy">
              Use an email already present in your organization sources.
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
                Access the internal dashboard, source explorer, and the decision
                reasoning workspace after verification.
              </p>
            </div>
            <div className="minimal-card">
              <div className="panel-heading">
                <p className="panel-kicker">Current State</p>
                <h3>Phase One</h3>
              </div>
              <p className="panel-copy">
                This is the first gated slice, not the full product yet. Next we
                wire the main Memora reasoning flow into the new UI.
              </p>
            </div>
          </div>
        </div>
      </HeroPanel>
    </div>
  );
}
