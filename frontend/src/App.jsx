// Root component for Panther Cloud Air frontend.
//
// Responsibilities:
//   1. Wrap the whole tree in AuthProvider so any page can read the current
//      user / JWT via useAuth().
//   2. Define the client-side route table and gate protected pages behind
//      <ProtectedRoute>. Admin-only pages also pass roles={["admin"]}.
//   3. Provide the shared chrome (Sidebar, footer, floating HelpButton)
//      through the <Layout> wrapper so pages don't each re-implement it.

import { useState } from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider } from "./context/AuthContext";
import ProtectedRoute from "./components/ProtectedRoute";
import Sidebar from "./components/Sidebar";
import HelpButton from "./components/HelpButton";
import Login from "./pages/Login";
import Home from "./pages/Home";
import BookFlight from "./pages/BookFlight";
import Timetable from "./pages/Timetable";
import Simulation from "./pages/Simulation";
import Finances from "./pages/Finances";
import MyBookings from "./pages/MyBookings";
import AdminDashboard from "./pages/AdminDashboard";
import Search from "./pages/Search";
import Unauthorized from "./pages/Unauthorized";
import "./App.css";

/**
 * Shared page chrome: collapsible sidebar, main content slot, footer, and the
 * floating help button. Sidebar open/closed state lives here (not in a
 * context) because no other component needs to read or toggle it.
 *
 * The layout-body class toggles between --open and --closed so CSS can shift
 * the content area to account for the sidebar width.
 */
function Layout({ children }) {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <div className="app">
      <Sidebar open={sidebarOpen} onToggle={() => setSidebarOpen(v => !v)} />
      <div className={`layout-body ${sidebarOpen ? "layout-body--open" : "layout-body--closed"}`}>
        <main className="main-content">{children}</main>
        <footer className="footer">
          <p>Panther Cloud Air &copy; 2026</p>
        </footer>
      </div>
      <HelpButton />
    </div>
  );
}

/**
 * Route table.
 *
 * Routes fall into three tiers:
 *   - Public        : /login (no auth required)
 *   - Authenticated : any logged-in user (admin OR user role)
 *   - Admin-only    : ProtectedRoute with roles={["admin"]}
 *
 * /unauthorized is rendered inside the Layout so a user who hits a page they
 * lack permission for still sees the sidebar and can navigate away, rather
 * than landing on a bare error screen.
 *
 * The catch-all "*" route redirects unknown URLs to "/" instead of showing a
 * 404. Since "/" is itself protected, unauthenticated users get bounced to
 * /login by ProtectedRoute — so a bad URL never leaks app structure.
 */
export default function App() {
  return (
    <AuthProvider>
      <Routes>
        {/* Public entry point */}
        <Route path="/login" element={<Login />} />

        {/* Shown when a logged-in user hits an admin-only page */}
        <Route path="/unauthorized" element={<Layout><Unauthorized /></Layout>} />

        {/* Authenticated routes (any role) */}
        <Route path="/" element={
          <ProtectedRoute>
            <Layout><Home /></Layout>
          </ProtectedRoute>
        } />
        <Route path="/book" element={
          <ProtectedRoute>
            <Layout><BookFlight /></Layout>
          </ProtectedRoute>
        } />
        <Route path="/bookings" element={
          <ProtectedRoute>
            <Layout><MyBookings /></Layout>
          </ProtectedRoute>
        } />
        <Route path="/timetable" element={
          <ProtectedRoute>
            <Layout><Timetable /></Layout>
          </ProtectedRoute>
        } />
        <Route path="/search" element={
          <ProtectedRoute>
            <Layout><Search /></Layout>
          </ProtectedRoute>
        } />

        {/* Admin-only routes */}
        {/* These still check auth first (via ProtectedRoute) before the
            role check — a non-admin lands on /unauthorized, a logged-out
            user lands on /login. */}
        <Route path="/simulation" element={
          <ProtectedRoute roles={["admin"]}>
            <Layout><Simulation /></Layout>
          </ProtectedRoute>
        } />
        <Route path="/finances" element={
          <ProtectedRoute roles={["admin"]}>
            <Layout><Finances /></Layout>
          </ProtectedRoute>
        } />
        <Route path="/admin" element={
          <ProtectedRoute roles={["admin"]}>
            <Layout><AdminDashboard /></Layout>
          </ProtectedRoute>
        } />

        {/* Unknown URL → bounce home. Home is protected, so logged-out
            users continue on to /login automatically. */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AuthProvider>
  );
}
