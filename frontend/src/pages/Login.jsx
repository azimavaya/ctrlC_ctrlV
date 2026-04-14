// Sign-in page for Panther Cloud Air.
// Features: username/password form, account lockout detection, password
// visibility toggle, forgot-password flow (UI only), and a high-contrast
// accessibility mode.

import { useState, useRef, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import "./Login.css";

export default function Login() {
  const { login } = useAuth();
  const navigate  = useNavigate();

  // Backend readiness state
  const [backendReady, setBackendReady] = useState(false);
  const [readyProgress, setReadyProgress] = useState(0);

  // Form input state
  const [username,  setUsername]  = useState("");
  const [password,  setPassword]  = useState("");
  const [showPass,  setShowPass]  = useState(false);   // toggle password visibility
  const [error,     setError]     = useState(null);     // validation error message
  const [locked,    setLocked]    = useState(false);    // true if account is locked out
  const [loading,   setLoading]   = useState(false);    // true while login request is in-flight
  // Forgot-password flow state
  const [showForgot, setShowForgot] = useState(false);
  const [forgotEmail, setForgotEmail] = useState("");
  const [forgotSent, setForgotSent] = useState(false);
  // High-contrast accessibility mode
  const [highContrast, setHighContrast] = useState(false);

  const usernameRef = useRef(null);

  // Poll backend health until it's ready
  useEffect(() => {
    let cancelled = false;
    let progress = 0;
    const poll = async () => {
      while (!cancelled) {
        try {
          const res = await fetch("/api/health");
          if (res.ok) {
            setReadyProgress(100);
            setTimeout(() => { if (!cancelled) setBackendReady(true); }, 400);
            return;
          }
        } catch { /* backend not up yet */ }
        progress = Math.min(progress + 8 + Math.random() * 7, 90);
        setReadyProgress(Math.round(progress));
        await new Promise(r => setTimeout(r, 1500));
      }
    };
    poll();
    return () => { cancelled = true; };
  }, []);

  // Auto-focus the username field once backend is ready
  useEffect(() => { if (backendReady) usernameRef.current?.focus(); }, [backendReady]);

  /** Submit credentials to the auth API; handle lockout and errors */
  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!username.trim() || !password) return;
    setError(null);
    setLoading(true);
    try {
      await login(username.trim(), password);
      navigate("/", { replace: true });
    } catch (err) {
      if (err.message === "account_locked") {
        setLocked(true);
        return;
      }
      setError("Invalid username or password");
    } finally {
      setLoading(false);
    }
  };

  /** Forgot-password submit handler (UI-only, no backend endpoint) */
  const handleForgot = (e) => {
    e.preventDefault();
    if (!forgotEmail.trim()) return;
    setForgotSent(true);
  };

  return (
    <div className={`login-bg ${highContrast ? "login-hc" : ""}`}>
      {/* Hidden dummy inputs block browser autofill */}
      <input type="text"     style={{ display: "none" }} aria-hidden="true" />
      <input type="password" style={{ display: "none" }} aria-hidden="true" />

      <span className="login-trademark">Panther Cloud Air &copy; 2026</span>

      {/* Accessibility toggle */}
      <button
        className="login-a11y-toggle"
        onClick={() => setHighContrast(v => !v)}
        aria-label="Toggle high contrast mode"
        title="Toggle high contrast mode"
      >
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ width: 20, height: 20 }}>
          <circle cx="12" cy="12" r="10"/>
          <path d="M12 2a10 10 0 010 20V2z" fill="currentColor"/>
        </svg>
      </button>

      <div className="login-card">
        <div className="login-logo">
          <span className="login-plane" aria-hidden="true">✈</span>
          <h1>Panther Cloud Air</h1>
        </div>

        {!backendReady ? (
          <div className="login-ready-overlay">
            <p className="login-ready-text">Preparing systems...</p>
            <div className="login-progress-track">
              <div className="login-progress-bar" style={{ width: `${readyProgress}%` }} />
            </div>
            <p className="login-ready-subtext">Please wait while the server initializes</p>
          </div>
        ) : !showForgot ? (
          <form onSubmit={handleSubmit} className="login-form" autoComplete="off">
            <div className="form-group">
              <label htmlFor="username">Username or Email</label>
              <input
                ref={usernameRef}
                id="username"
                type="text"
                autoComplete="off"
                autoCorrect="off"
                autoCapitalize="off"
                spellCheck="false"
                value={username}
                onChange={(e) => { setUsername(e.target.value); setError(null); setLocked(false); }}
                placeholder="Enter your username or email"
                required
              />
            </div>

            <div className="form-group">
              <label htmlFor="password">Password</label>
              <div className="password-input-wrap">
                <input
                  id="password"
                  type={showPass ? "text" : "password"}
                  autoComplete="new-password"
                  value={password}
                  onChange={(e) => { setPassword(e.target.value); setError(null); setLocked(false); }}
                  placeholder="Enter your password"
                  disabled={locked}
                  required
                />
                <button
                  type="button"
                  className="eye-btn"
                  onClick={() => setShowPass((v) => !v)}
                  tabIndex={-1}
                  aria-label={showPass ? "Hide password" : "Show password"}
                >
                  {showPass ? (
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M17.94 17.94A10.07 10.07 0 0112 20c-7 0-11-8-11-8a18.45 18.45 0 015.06-5.94"/>
                      <path d="M9.9 4.24A9.12 9.12 0 0112 4c7 0 11 8 11 8a18.5 18.5 0 01-2.16 3.19"/>
                      <line x1="1" y1="1" x2="23" y2="23"/>
                    </svg>
                  ) : (
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
                      <circle cx="12" cy="12" r="3"/>
                    </svg>
                  )}
                </button>
              </div>
            </div>

            {locked
              ? <div className="login-error login-locked" role="alert">Your account has been locked. Please contact your administrator.</div>
              : error && <div className="login-error" role="alert">{error}</div>
            }

            <button className="btn-primary login-btn" type="submit" disabled={loading || !username.trim() || !password || locked}>
              {loading ? "Signing in…" : "Sign In"}
            </button>

            <button type="button" className="forgot-link" onClick={() => { setShowForgot(true); setForgotSent(false); setForgotEmail(""); }}>
              Forgot password?
            </button>
          </form>
        ) : (
          <div className="login-form">
            {!forgotSent ? (
              <>
                <p className="forgot-instructions">Enter the email address associated with your account and we'll send you a password reset link.</p>
                <form onSubmit={handleForgot}>
                  <div className="form-group">
                    <label htmlFor="forgot-email">Email Address</label>
                    <input
                      id="forgot-email"
                      type="email"
                      value={forgotEmail}
                      onChange={(e) => setForgotEmail(e.target.value)}
                      placeholder="you@example.com"
                      autoFocus
                      required
                    />
                  </div>
                  <button className="btn-primary login-btn" type="submit">
                    Send Reset Link
                  </button>
                </form>
                <button type="button" className="forgot-link" onClick={() => setShowForgot(false)}>
                  Back to sign in
                </button>
              </>
            ) : (
              <>
                <div className="forgot-success" role="status">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ width: 40, height: 40, margin: "0 auto 0.75rem", display: "block", color: "#16a34a" }}>
                    <path d="M22 11.08V12a10 10 0 11-5.93-9.14" />
                    <polyline points="22 4 12 14.01 9 11.01" />
                  </svg>
                  <p>If an account exists with <strong>{forgotEmail}</strong>, a password reset link has been sent.</p>
                </div>
                <button type="button" className="forgot-link" onClick={() => setShowForgot(false)}>
                  Back to sign in
                </button>
              </>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
