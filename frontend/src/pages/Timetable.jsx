// Full daily flight schedule with filtering.
// Features: origin/destination airport filters, print-friendly view, and color-coded status badges.

import { useState, useEffect } from "react";

const API = "/api";

// Hardcoded airport list for the filter dropdowns (matches the 31 PCA airports)
const AIRPORTS = [
  { iata: "ATL", city: "Atlanta" },
  { iata: "BNA", city: "Nashville" },
  { iata: "BOS", city: "Boston" },
  { iata: "BWI", city: "Baltimore" },
  { iata: "CDG", city: "Paris" },
  { iata: "CLT", city: "Charlotte" },
  { iata: "DCA", city: "Washington" },
  { iata: "DEN", city: "Denver" },
  { iata: "DFW", city: "Dallas" },
  { iata: "DTW", city: "Detroit" },
  { iata: "FLL", city: "Fort Lauderdale" },
  { iata: "HNL", city: "Honolulu" },
  { iata: "IAH", city: "Houston" },
  { iata: "JFK", city: "New York" },
  { iata: "LAS", city: "Las Vegas" },
  { iata: "LAX", city: "Los Angeles" },
  { iata: "LGA", city: "New York" },
  { iata: "MCI", city: "Kansas City" },
  { iata: "MCO", city: "Orlando" },
  { iata: "MDW", city: "Chicago" },
  { iata: "MIA", city: "Miami" },
  { iata: "MSP", city: "Minneapolis" },
  { iata: "ORD", city: "Chicago" },
  { iata: "PDX", city: "Portland" },
  { iata: "PHL", city: "Philadelphia" },
  { iata: "PHX", city: "Phoenix" },
  { iata: "SAN", city: "San Diego" },
  { iata: "SEA", city: "Seattle" },
  { iata: "SFO", city: "San Francisco" },
  { iata: "SLC", city: "Salt Lake City" },
  { iata: "STL", city: "St. Louis" },
];


/** Format a departure/arrival time in UTC */
function fmt(dt) {
  if (!dt) return "—";
  const d = new Date(dt + (dt.endsWith("Z") ? "" : "Z"));
  const now = new Date();
  const today = new Date(Date.UTC(
    now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate(),
    d.getUTCHours(), d.getUTCMinutes(), d.getUTCSeconds()
  ));
  return today.toLocaleTimeString("en-US", {
    hour: "2-digit", minute: "2-digit", hour12: true,
    timeZone: "UTC",
  });
}

/** Calculate flight duration from departure/arrival */
function fmtDuration(dep, arr) {
  if (!dep || !arr) return "—";
  const d = new Date(dep + (dep.endsWith("Z") ? "" : "Z"));
  const a = new Date(arr + (arr.endsWith("Z") ? "" : "Z"));
  const realMin = Math.round((a - d) / 60000);
  const h = Math.floor(realMin / 60);
  const m = realMin % 60;
  return `${h}h ${m}m`;
}

/** Renders a color-coded pill for flight status (scheduled, boarding, departed, etc.) */
function StatusBadge({ status }) {
  return <span className={`tt-badge tt-badge--${status}`}>{status}</span>;
}

export default function Timetable() {
  const [flights, setFlights] = useState([]);
  const [loading, setLoading] = useState(true);
  const [originFilter, setOriginFilter] = useState("");
  const [destFilter, setDestFilter]     = useState("");

  // Fetch the full daily flight schedule on mount
  useEffect(() => {
    fetch(`${API}/flights/departures?limit=500`)
      .then(r => r.json())
      .then(d => { setFlights(Array.isArray(d) ? d : []); setLoading(false); })
      .catch(() => setLoading(false));
  }, []);

  // Apply origin and destination filters to the flight list
  const filtered = flights.filter(f =>
    (!originFilter || f.origin_iata === originFilter) &&
    (!destFilter   || f.dest_iata   === destFilter)
  );

  return (
    <div className="timetable-page">
      <div className="tt-header">
        <h2>Flight Timetable</h2>
        <span className="tt-header-sub">Panther Cloud Air — Daily Schedule</span>
      </div>

      {/* Controls */}
      <div className="card tt-controls">
        <div className="form-group">
          <label>Origin</label>
          <select value={originFilter} onChange={e => setOriginFilter(e.target.value)}>
            <option value="">All airports</option>
            {AIRPORTS.map(a => (
              <option key={a.iata} value={a.iata}>{a.iata} — {a.city}</option>
            ))}
          </select>
        </div>
        <div className="form-group">
          <label>Destination</label>
          <select value={destFilter} onChange={e => setDestFilter(e.target.value)}>
            <option value="">All airports</option>
            {AIRPORTS.map(a => (
              <option key={a.iata} value={a.iata}>{a.iata} — {a.city}</option>
            ))}
          </select>
        </div>
        <div className="tt-count-badge">
          {loading ? "Loading…" : `${filtered.length} flight${filtered.length !== 1 ? "s" : ""}`}
        </div>
        <button className="btn-print" onClick={() => window.print()} title="Print timetable">
          Print
        </button>
      </div>

      {/* Table */}
      <div className="card tt-table-card">
        <div className="tt-scroll">
          <table className="pca-table tt-table">
            <thead>
              <tr>
                <th>Flight</th>
                <th>From</th>
                <th>To</th>
                <th>Departs (UTC)</th>
                <th>Arrives (UTC)</th>
                <th>Duration</th>
                <th>Aircraft</th>
                <th>Capacity</th>
                <th>Fare</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr><td colSpan={10} className="tt-center">Loading…</td></tr>
              ) : filtered.length === 0 ? (
                <tr><td colSpan={10} className="tt-center">No flights found</td></tr>
              ) : filtered.map((f, i) => (
                <tr key={i}>
                  <td className="tt-fn">{f.flight_number}</td>
                  <td>
                    <span className="tt-iata">{f.origin_iata}</span>
                    <span className="tt-city">{f.origin_city}</span>
                  </td>
                  <td>
                    <span className="tt-iata">{f.dest_iata}</span>
                    <span className="tt-city">{f.dest_city}</span>
                  </td>
                  <td className="tt-time">{fmt(f.scheduled_departure)}</td>
                  <td className="tt-time">{fmt(f.scheduled_arrival)}</td>
                  <td className="tt-duration">{fmtDuration(f.scheduled_departure, f.scheduled_arrival)}</td>
                  <td className="tt-model">{f.aircraft_model}</td>
                  <td>{f.capacity ?? "—"}</td>
                  <td>${parseFloat(f.fare_USD).toFixed(2)}</td>
                  <td><StatusBadge status={f.status} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
