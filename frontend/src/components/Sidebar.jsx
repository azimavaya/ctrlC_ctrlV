import { NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

const IconHome = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z"/>
    <polyline points="9 22 9 12 15 12 15 22"/>
  </svg>
);
const IconSearch = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <circle cx="11" cy="11" r="8"/>
    <line x1="21" y1="21" x2="16.65" y2="16.65"/>
  </svg>
);
const IconCalendar = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <rect x="3" y="4" width="18" height="18" rx="2"/>
    <line x1="16" y1="2" x2="16" y2="6"/>
    <line x1="8" y1="2" x2="8" y2="6"/>
    <line x1="3" y1="10" x2="21" y2="10"/>
  </svg>
);
const IconChart = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <line x1="18" y1="20" x2="18" y2="10"/>
    <line x1="12" y1="20" x2="12" y2="4"/>
    <line x1="6"  y1="20" x2="6"  y2="14"/>
  </svg>
);
const IconDollar = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <line x1="12" y1="1" x2="12" y2="23"/>
    <path d="M17 5H9.5a3.5 3.5 0 000 7h5a3.5 3.5 0 010 7H6"/>
  </svg>
);
const IconShield = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
  </svg>
);
const IconTicket = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="M2 9a3 3 0 013-3h14a3 3 0 013 3v0a3 3 0 00-3 3v0a3 3 0 003 3v0a3 3 0 01-3 3H5a3 3 0 01-3-3v0a3 3 0 003-3v0a3 3 0 00-3-3z"/>
    <line x1="9" y1="6" x2="9" y2="18"/>
  </svg>
);
const IconLogout = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4"/>
    <polyline points="16 17 21 12 16 7"/>
    <line x1="21" y1="12" x2="9" y2="12"/>
  </svg>
);
const IconMenu = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <line x1="3" y1="6"  x2="21" y2="6"/>
    <line x1="3" y1="12" x2="21" y2="12"/>
    <line x1="3" y1="18" x2="21" y2="18"/>
  </svg>
);
const IconClose = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <line x1="18" y1="6" x2="6" y2="18"/>
    <line x1="6" y1="6" x2="18" y2="18"/>
  </svg>
);

const ROLE_COLORS = {
  admin:   "#ef4444",
  user: "#0ea5e9",
};

export default function Sidebar({ open, onToggle }) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/login", { replace: true });
  };

  const initials = user?.username?.slice(0, 2).toUpperCase() ?? "??";
  const roleColor = ROLE_COLORS[user?.role] ?? "#6b7280";

  const navItems = [
    { to: "/",            label: "Home",           Icon: IconHome,     roles: null },
    { to: "/book",         label: "Book Flight",     Icon: IconSearch,   roles: null },
    { to: "/bookings",     label: "My Bookings",    Icon: IconTicket,   roles: null },
    { to: "/timetable",   label: "Timetable",       Icon: IconCalendar, roles: null },
    { to: "/simulation",  label: "Simulation",      Icon: IconChart,    roles: ["admin"] },
    { to: "/finances",    label: "Finances",        Icon: IconDollar,   roles: ["admin"] },
    { to: "/admin",       label: "Admin Dashboard", Icon: IconShield,   roles: ["admin"] },
  ].filter(item => !item.roles || item.roles.includes(user?.role));

  return (
    <aside className={`sidebar ${open ? "sidebar--open" : "sidebar--closed"}`}>

        <button className="sidebar-toggle" onClick={onToggle} aria-label="Toggle sidebar">
          {open ? <IconClose /> : <IconMenu />}
        </button>

        <nav className="sidebar-nav">
          {navItems.map(({ to, label, Icon }) => (
            <NavLink
              key={to}
              to={to}
              end={to === "/"}
              className={({ isActive }) =>
                `sidebar-item ${isActive ? "sidebar-item--active" : ""}`
              }
            >
              <span className="sidebar-icon"><Icon /></span>
              {open && <span className="sidebar-label">{label}</span>}
            </NavLink>
          ))}
        </nav>

        {/* User block */}
        <div className="sidebar-user">
          <div className="sidebar-avatar" style={{ background: roleColor }}>
            {initials}
          </div>
          {open && (
            <div className="sidebar-user-info">
              <span className="sidebar-username">{user?.username}</span>
              <span className="sidebar-role" style={{ color: roleColor }}>
                {user?.role?.charAt(0).toUpperCase() + user?.role?.slice(1)}
              </span>
            </div>
          )}
          <button
            className="sidebar-logout"
            onClick={handleLogout}
            aria-label="Sign out"
            title="Sign out"
          >
            <IconLogout />
          </button>
        </div>
    </aside>
  );
}
