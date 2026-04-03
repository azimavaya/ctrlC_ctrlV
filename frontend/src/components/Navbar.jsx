/**
 * Navbar.jsx — Top navigation bar (currently replaced by Sidebar in the layout,
 * but kept as an alternate nav component). Shows brand, nav links, user info,
 * and a role badge. Links and user section are conditionally rendered only
 * when a user is logged in.
 */
import { NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import "./Navbar.css";

// Maps role names to badge colors for the user section
const ROLE_BADGE = {
  admin:   { label: "Admin",   color: "#dc2626" },
  user: { label: "User", color: "#0369a1" },
};

export default function Navbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  // Sign out and redirect to login page
  const handleLogout = () => {
    logout();
    navigate("/login", { replace: true });
  };

  // Determine the badge color/label for the current user's role
  const badge = user ? (ROLE_BADGE[user.role] ?? { label: user.role, color: "#6b7280" }) : null;

  return (
    <nav className="navbar">
      <div className="navbar-brand">
        <span className="brand-icon">✈</span>
        <span className="brand-name">Panther Cloud Air</span>
      </div>

      {user && (
        <ul className="navbar-links">
          <li><NavLink to="/"          end>Home</NavLink></li>
          <li><NavLink to="/search"       >Search Flights</NavLink></li>
          <li><NavLink to="/timetable"    >Timetable</NavLink></li>
          {user.role === "admin" && (
            <li><NavLink to="/simulation">Simulation</NavLink></li>
          )}
        </ul>
      )}

      {user && (
        <div className="navbar-user">
          <span className="user-name">{user.username}</span>
          <span
            className="role-badge"
            style={{ background: badge.color }}
          >
            {badge.label}
          </span>
          <button className="logout-btn" onClick={handleLogout}>Sign Out</button>
        </div>
      )}
    </nav>
  );
}
