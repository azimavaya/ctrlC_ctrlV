// Admin control panel (admin-only).
// Tabs: aircraft table with specs/maintenance info, airport table sortable by IATA/hub,
// user management (CRUD + unlock).

import { useEffect, useState } from "react";
import { useAuth } from "../context/AuthContext";

const API = "/api";

function StatCard({ label, value, accent }) {
  return (
    <div className="ad-stat-card" style={{ borderTopColor: accent }}>
      <span className="ad-stat-value">{value ?? "—"}</span>
      <span className="ad-stat-label">{label}</span>
    </div>
  );
}

function RoleBadge({ role }) {
  const colors = { admin: "#ef4444", user: "#0ea5e9" };
  return (
    <span className="ad-badge" style={{ background: colors[role] ?? "#6b7280" }}>
      {role}
    </span>
  );
}

function StatusBadge({ status }) {
  const colors = { active: "#10b981", maintenance: "#f59e0b", grounded: "#ef4444" };
  return (
    <span className="ad-badge" style={{ background: colors[status] ?? "#6b7280" }}>
      {status}
    </span>
  );
}

export default function AdminDashboard() {
  const { token } = useAuth();
  const [data, setData]       = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError]     = useState(null);
  const [tab, setTab]         = useState("aircraft");

  const [airportSort, setAirportSort] = useState("iata");
  const [showCreateUser, setShowCreateUser] = useState(false);
  const [newUser, setNewUser] = useState({ username: "", password: "", email: "", role: "user" });
  const [createError, setCreateError] = useState(null);
  const [creating, setCreating] = useState(false);

  const loadData = () => {
    fetch(`${API}/admin/overview`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then(r => r.json())
      .then(d => { setData(d); setLoading(false); })
      .catch(() => { setError("Failed to load admin data"); setLoading(false); });
  };

  useEffect(() => { loadData(); }, [token]);

  const deleteUser = (user_id, username) => {
    if (!window.confirm(`Delete user "${username}"? This cannot be undone.`)) return;
    fetch(`${API}/auth/users/${user_id}`, {
      method:  "DELETE",
      headers: { Authorization: `Bearer ${token}` },
    })
      .then(async (r) => {
        const body = await r.json();
        if (!r.ok) throw new Error(body.error || "Failed to delete user");
        loadData();
      })
      .catch((err) => alert(err.message));
  };

  const unlockUser = (user_id) => {
    fetch(`${API}/auth/users/${user_id}`, {
      method:  "PATCH",
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
      body:    JSON.stringify({ unlock: true }),
    }).then(() => loadData());
  };

  const createUser = (e) => {
    e.preventDefault();
    setCreateError(null);
    setCreating(true);
    fetch(`${API}/auth/users`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
      body: JSON.stringify(newUser),
    })
      .then(async (r) => {
        const body = await r.json();
        if (!r.ok) throw new Error(body.error || "Failed to create user");
        setNewUser({ username: "", password: "", email: "", role: "user" });
        setShowCreateUser(false);
        loadData();
      })
      .catch((err) => setCreateError(err.message))
      .finally(() => setCreating(false));
  };

  if (loading) return <div className="ad-loading">Loading admin data…</div>;
  if (error)   return <div className="ad-error">{error}</div>;

  const { stats, users, aircraft, fleet_breakdown, airports } = data;

  return (
    <div className="admin-dashboard">
      <div className="ad-header">
        <h2>Admin Dashboard</h2>
        <span className="ad-header-sub">Panther Cloud Air — Operations Overview</span>
      </div>

      {/* Stats row */}
      <div className="ad-stats-row">
        <StatCard label="Users"     value={stats.users}    accent="#0ea5e9" />
        <StatCard label="Aircraft"  value={stats.aircraft} accent="#8b5cf6" />
        <StatCard label="Airports"  value={stats.airports} accent="#10b981" />
        <StatCard label="Routes"    value={stats.routes}   accent="#f59e0b" />
        <StatCard label="Daily Flights" value={stats.flights_per_day} accent="#ef4444" />
      </div>

      {/* Tab navigation */}
      <div className="ad-tabs">
        {[
          { key: "aircraft", label: `Aircraft (${aircraft.length})` },
          { key: "airports", label: `Airports (${airports.length})` },
          { key: "users",    label: `Users (${users.length})` },
        ].map(t => (
          <button
            key={t.key}
            className={`ad-tab ${tab === t.key ? "ad-tab--active" : ""}`}
            onClick={() => setTab(t.key)}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* Users table */}
      {tab === "users" && (
        <div className="card">
          <div className="ad-create-user-bar">
            <button
              className="ad-create-btn"
              onClick={() => { setShowCreateUser(!showCreateUser); setCreateError(null); }}
            >
              {showCreateUser ? "Cancel" : "+ Create User"}
            </button>
          </div>

          {showCreateUser && (
            <form className="ad-create-form" onSubmit={createUser}>
              <div className="ad-create-fields">
                <input
                  type="text"
                  placeholder="Username"
                  required
                  value={newUser.username}
                  onChange={(e) => setNewUser({ ...newUser, username: e.target.value })}
                />
                <input
                  type="password"
                  placeholder="Password"
                  required
                  value={newUser.password}
                  onChange={(e) => setNewUser({ ...newUser, password: e.target.value })}
                />
                <input
                  type="email"
                  placeholder="Email (optional)"
                  value={newUser.email}
                  onChange={(e) => setNewUser({ ...newUser, email: e.target.value })}
                />
                <select
                  value={newUser.role}
                  onChange={(e) => setNewUser({ ...newUser, role: e.target.value })}
                >
                  <option value="user">User</option>
                  <option value="admin">Admin</option>
                </select>
                <button type="submit" className="ad-submit-btn" disabled={creating}>
                  {creating ? "Creating…" : "Create"}
                </button>
              </div>
              {createError && <p className="ad-create-error">{createError}</p>}
            </form>
          )}

          <table className="pca-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Username</th>
                <th>Email</th>
                <th>Role</th>
                <th>Status</th>
                <th>Created</th>
                <th>Last Login</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {users.map(u => (
                <tr key={u.user_id}>
                  <td>{u.user_id}</td>
                  <td><strong>{u.username}</strong></td>
                  <td>{u.email ?? <span className="ad-null">—</span>}</td>
                  <td><RoleBadge role={u.role_name} /></td>
                  <td>
                    {u.locked_at
                      ? <span className="ad-badge ad-badge--red">locked</span>
                      : <span className={`ad-badge ${u.is_active ? "ad-badge--green" : "ad-badge--red"}`}>
                          {u.is_active ? "active" : "disabled"}
                        </span>
                    }
                  </td>
                  <td>{u.created_at ? new Date(u.created_at).toLocaleDateString() : "—"}</td>
                  <td>{u.last_login ? new Date(u.last_login).toLocaleString() : <span className="ad-null">never</span>}</td>
                  <td>
                    {u.locked_at && (
                      <button className="ad-unlock-btn" onClick={() => unlockUser(u.user_id)}>
                        Unlock
                      </button>
                    )}
                    {u.username !== "admin" && (
                      <button className="ad-delete-btn" onClick={() => deleteUser(u.user_id, u.username)}>
                        Delete
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Aircraft table */}
      {tab === "aircraft" && (
        <div className="card">
          <div className="ad-table-scroll">
          <table className="pca-table">
            <thead>
              <tr>
                <th>Tail #</th>
                <th>Model</th>
                <th>Manufacturer</th>
                <th>Base</th>
                <th>Capacity</th>
                <th>Fuel Cap (L)</th>
                <th>Burn (L/hr)</th>
                <th>Max Speed (km/h)</th>
                <th>Range (km)</th>
                <th>Daily Hours</th>
                <th>Maint. Due (days)</th>
              </tr>
            </thead>
            <tbody>
              {aircraft.map(a => (
                <tr key={a.aircraft_id}>
                  <td><strong>{a.tail_number}</strong></td>
                  <td>{a.model}</td>
                  <td>{a.manufacturer}</td>
                  <td>{a.current_airport ?? "—"}</td>
                  <td>{a.capacity_passengers}</td>
                  <td>{a.fuel_capacity_L != null ? Number(a.fuel_capacity_L).toLocaleString() : "—"}</td>
                  <td>{a.fuel_burn_L_per_hr != null ? Number(a.fuel_burn_L_per_hr).toLocaleString() : "—"}</td>
                  <td>{a.max_speed_kmh != null ? Number(a.max_speed_kmh).toLocaleString() : "—"}</td>
                  <td>{a.range_km != null ? Number(a.range_km).toLocaleString() : "—"}</td>
                  <td>{a.daily_flight_hours != null ? parseFloat(a.daily_flight_hours).toFixed(1) : "—"}</td>
                  <td>{a.daily_flight_hours > 0 ? Math.ceil(200 / parseFloat(a.daily_flight_hours)) : "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
          </div>
        </div>
      )}

      {/* Airports table */}
      {tab === "airports" && (
        <div className="card">
          <div className="ad-sort-bar">
            <span className="ad-sort-label">Sort by:</span>
            <button className={`ad-sort-btn${airportSort === "iata" ? " ad-sort-btn--active" : ""}`} onClick={() => setAirportSort("iata")}>IATA Code</button>
            <button className={`ad-sort-btn${airportSort === "hub" ? " ad-sort-btn--active" : ""}`} onClick={() => setAirportSort("hub")}>Hub First</button>
          </div>
          <table className="pca-table">
            <thead>
              <tr>
                <th>IATA</th>
                <th>Name</th>
                <th>City</th>
                <th>State/Country</th>
                <th>Hub</th>
                <th>Gates</th>
                <th>Metro Pop (M)</th>
                <th>Timezone</th>
              </tr>
            </thead>
            <tbody>
              {[...airports].sort((a, b) =>
                airportSort === "hub"
                  ? (b.is_hub - a.is_hub) || a.iata_code.localeCompare(b.iata_code)
                  : a.iata_code.localeCompare(b.iata_code)
              ).map(a => (
                <tr key={a.airport_id}>
                  <td><strong>{a.iata_code}</strong></td>
                  <td>{a.name}</td>
                  <td>{a.city}</td>
                  <td>{a.state ? `${a.state}, ${a.country}` : a.country}</td>
                  <td>
                    {a.is_hub
                      ? <span className="ad-badge" style={{ background: "#c9a84c", color: "#1a3a5c" }}>HUB</span>
                      : <span className="ad-null">—</span>}
                  </td>
                  <td>{a.num_gates}</td>
                  <td>{a.metro_pop_M != null ? Number(a.metro_pop_M).toFixed(2) : "—"}</td>
                  <td>{a.timezone}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
