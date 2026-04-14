// Route guard component. Wraps a route so only authenticated users can
// access it. Optionally restrict to specific roles:
//   <ProtectedRoute roles={["admin"]} />
//
// Redirect logic:
//   - If auth is still loading, show a loading screen.
//   - If no user is logged in, redirect to /login.
//   - If user lacks the required role, redirect to /unauthorized.
//   - Otherwise, render the child page.

import { Navigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function ProtectedRoute({ children, roles }) {
  const { user, loading } = useAuth();

  // Show spinner while AuthContext validates the stored JWT on first load
  if (loading) return <div className="loading-screen">Loading…</div>;

  // No authenticated user, send to login
  if (!user) return <Navigate to="/login" replace />;

  // User exists but lacks the required role, show access-denied page
  if (roles && !roles.includes(user.role)) {
    return <Navigate to="/unauthorized" replace />;
  }

  // Authorized, render the protected page
  return children;
}
