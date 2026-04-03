/**
 * AuthContext.jsx — Provides authentication state to the entire app.
 * Manages JWT token storage in localStorage, login/logout actions,
 * and an authFetch helper that auto-attaches the Bearer token to API requests.
 */
import { createContext, useContext, useState, useEffect } from "react";

const AuthContext = createContext(null);

// localStorage keys for persisting session across page reloads
const TOKEN_KEY = "pca_token";
const USER_KEY  = "pca_user";

export function AuthProvider({ children }) {
  // Restore user/token from localStorage on initial load (survives refresh)
  const [user,  setUser]  = useState(() => {
    try { return JSON.parse(localStorage.getItem(USER_KEY)); } catch { return null; }
  });
  const [token, setToken] = useState(() => localStorage.getItem(TOKEN_KEY) || null);
  const [loading, setLoading] = useState(true); // true while validating stored token

  // Validate stored token on mount
  useEffect(() => {
    if (!token) { setLoading(false); return; }
    fetch("/api/auth/me", {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((r) => r.ok ? r.json() : Promise.reject())
      .then((data) => {
        setUser({ username: data.username, role: data.role_name });
      })
      .catch(() => {
        // Token invalid/expired — clear it
        localStorage.removeItem(TOKEN_KEY);
        localStorage.removeItem(USER_KEY);
        setToken(null);
        setUser(null);
      })
      .finally(() => setLoading(false));
  }, []);

  /** POST credentials to /api/auth/login, store token + user on success */
  const login = async (username, password) => {
    const res  = await fetch("/api/auth/login", {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify({ username, password }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Login failed");

    localStorage.setItem(TOKEN_KEY, data.token);
    localStorage.setItem(USER_KEY,  JSON.stringify({ username: data.username, role: data.role }));
    setToken(data.token);
    setUser({ username: data.username, role: data.role });
    return data;
  };

  /** Clear all auth state and remove tokens from localStorage */
  const logout = () => {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
    setToken(null);
    setUser(null);
  };

  /** Attach Bearer token to any fetch call */
  const authFetch = (url, options = {}) => {
    return fetch(url, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...(options.headers || {}),
        Authorization: `Bearer ${token}`,
      },
    });
  };

  return (
    <AuthContext.Provider value={{ user, token, loading, login, logout, authFetch }}>
      {children}
    </AuthContext.Provider>
  );
}

/** Custom hook — shorthand for consuming AuthContext from any component */
export const useAuth = () => useContext(AuthContext);
