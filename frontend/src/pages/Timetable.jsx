/**
 * Timetable.jsx — Full daily flight schedule with filtering and timezone support.
 * Features: origin/destination airport filters, UTC/ET/Local timezone toggle,
 * print-friendly view, and color-coded status badges.
 */
import { useState, useEffect } from "react";
import "./Timetable.css";

const API = "/api";

// Timezone options — "LOCAL" uses each airport's native timezone
const TZ_OPTIONS = {
  UTC:   { label: "UTC",   zone: "UTC" },
  ET:    { label: "ET",    zone: "America/New_York" },
  LOCAL: { label: "Local", zone: null },
};

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


/** Format a departure/arrival time into the selected timezone; LOCAL mode shows UTC offset */
function fmt(dt, tz, airportTz) {
  if (!dt) return "—";
  const d = new Date(dt + (dt.endsWith("Z") ? "" : "Z"));
  const now = new Date();
  const today = new Date(Date.UTC(
    now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate(),
    d.getUTCHours(), d.getUTCMinutes(), d.getUTCSeconds()
  ));
  const zone = tz === "LOCAL" && airportTz ? airportTz : (TZ_OPTIONS[tz]?.zone ?? "UTC");
  const time = today.toLocaleTimeString("en-US", {
    hour: "2-digit", minute: "2-digit", hour12: true,
    timeZone: zone,
  });
  if (tz === "LOCAL" && airportTz) {
    // Compute UTC offset for this timezone
    const utcStr = today.toLocaleString("en-US", { timeZone: "UTC" });
    const localStr = today.toLocaleString("en-US", { timeZone: airportTz });
    const offMin = (new Date(localStr) - new Date(utcStr)) / 60000;
    const sign = offMin >= 0 ? "+" : "";
    const offH = offMin / 60;
    return `${time} (UTC${sign}${offH % 1 === 0 ? offH.toFixed(0) : offH})`;
  }
  return time;
}

/** Calculate flight duration from departure/arrival; shows timezone offset difference if applicable */
function fmtDuration(dep, arr, originTz, destTz) {
  if (!dep || !arr) return "—";
  const d = new Date(dep + (dep.endsWith("Z") ? "" : "Z"));
  const a = new Date(arr + (arr.endsWith("Z") ? "" : "Z"));
  const realMin = Math.round((a - d) / 60000);
  const h = Math.floor(realMin / 60);
  const m = realMin % 60;
  let label = `${h}h ${m}m`;

  // Compute timezone offset difference (dest - origin) in hours
  if (originTz && destTz) {
    // Use a reference date to get UTC offsets for each timezone
    const ref = new Date();
    const originOff = -new Date(ref.toLocaleString("en-US", { timeZone: originTz })).getTimezoneOffset() - (-ref.getTimezoneOffset());
    const destOff = -new Date(ref.toLocaleString("en-US", { timeZone: destTz })).getTimezoneOffset() - (-ref.getTimezoneOffset());
    // Actually simpler: get offset in minutes for each tz
    const getOffset = (tz) => {
      const utcStr = ref.toLocaleString("en-US", { timeZone: "UTC" });
      const tzStr = ref.toLocaleString("en-US", { timeZone: tz });
      return (new Date(tzStr) - new Date(utcStr)) / 60000;
    };
    const diff = getOffset(destTz) - getOffset(originTz);
    if (diff !== 0) {
      const sign = diff > 0 ? "+" : "";
      const diffH = diff / 60;
      label += ` (${sign}${diffH}h)`;
    }
  }
  return label;
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
  const [tz, setTz]                     = useState("UTC");

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
        <div className="tt-tz-toggle">
          {Object.keys(TZ_OPTIONS).map(k => (
            <button
              key={k}
              className={`tt-tz-btn${tz === k ? " tt-tz-btn--active" : ""}`}
              onClick={() => setTz(k)}
            >
              {TZ_OPTIONS[k].label}
            </button>
          ))}
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
                <th>Departs{tz !== "LOCAL" ? ` (${tz})` : ""}</th>
                <th>Arrives{tz !== "LOCAL" ? ` (${tz})` : ""}</th>
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
                  <td className="tt-time">{fmt(f.scheduled_departure, tz, f.origin_tz)}</td>
                  <td className="tt-time">{fmt(f.scheduled_arrival, tz, f.dest_tz)}</td>
                  <td className="tt-duration">{fmtDuration(f.scheduled_departure, f.scheduled_arrival, f.origin_tz, f.dest_tz)}</td>
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
