// Read-only flight search page (no booking).
// Lets any logged-in user search for direct and connecting flights by
// origin, destination, and date. Results are displayed in tables.

import { useState, useEffect } from "react";
import "./Search.css";

const API = "/api";

export default function Search() {
  const [airports, setAirports] = useState([]);  // airport list for dropdowns
  const [form, setForm]         = useState({ origin: "", destination: "", date: "" });
  const [results, setResults]   = useState(null); // search results from API
  const [loading, setLoading]   = useState(false);
  const [error, setError]       = useState(null);

  // Load the airport list on mount for origin/destination dropdowns
  useEffect(() => {
    fetch(`${API}/airports`)
      .then(r => r.json())
      .then(d => setAirports(Array.isArray(d) ? d : []))
      .catch(() => {});
  }, []);

  /** Fetch flight search results from GET /api/flights/search */
  const handleSearch = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResults(null);
    try {
      const res = await fetch(
        `${API}/flights/search?origin=${form.origin}&destination=${form.destination}&date=${form.date}`
      );
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Search failed");
      setResults(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="search-page">
      <h2>Search Flights</h2>

      <div className="card">
        <form className="search-form" onSubmit={handleSearch}>
          <div className="form-row">
            <div className="form-group">
              <label>From</label>
              <select
                name="origin"
                value={form.origin}
                onChange={e => setForm({ ...form, origin: e.target.value })}
                required
              >
                <option value="">Select origin…</option>
                {airports.map(a => (
                  <option key={a.iata_code} value={a.iata_code}>
                    {a.iata_code} — {a.city}
                  </option>
                ))}
              </select>
            </div>
            <div className="form-group">
              <label>To</label>
              <select
                name="destination"
                value={form.destination}
                onChange={e => setForm({ ...form, destination: e.target.value })}
                required
              >
                <option value="">Select destination…</option>
                {airports
                  .filter(a => a.iata_code !== form.origin)
                  .map(a => (
                    <option key={a.iata_code} value={a.iata_code}>
                      {a.iata_code} — {a.city}
                    </option>
                  ))}
              </select>
            </div>
            <div className="form-group">
              <label>Date</label>
              <input
                name="date"
                type="date"
                value={form.date}
                min="2026-03-09"
                max="2027-02-28"
                onChange={e => setForm({ ...form, date: e.target.value })}
                required
              />
            </div>
          </div>
          <button className="btn-primary" type="submit" disabled={loading}>
            {loading ? "Searching…" : "Search Flights"}
          </button>
        </form>
      </div>

      {error && <div className="error-msg">{error}</div>}

      {results && (
        <div className="results">
          <h3>
            {results.origin} → {results.destination} &nbsp;·&nbsp; {results.date}
          </h3>

          {/* Direct flights */}
          {results.direct_flights.length > 0 && (
            <div className="card">
              <h4>Direct Flights ({results.direct_flights.length})</h4>
              <table className="pca-table">
                <thead>
                  <tr>
                    <th>Flight #</th>
                    <th>Departs</th>
                    <th>Arrives</th>
                    <th>Duration</th>
                    <th>Distance</th>
                    <th>Aircraft</th>
                    <th>Fare (USD)</th>
                  </tr>
                </thead>
                <tbody>
                  {results.direct_flights.map(f => {
                    const dur = f.duration_min;
                    const h = Math.floor(dur / 60);
                    const m = dur % 60;
                    return (
                      <tr key={f.flight_id}>
                        <td>{f.flight_number}</td>
                        <td>{new Date(f.scheduled_departure).toLocaleTimeString("en-US", {hour:"2-digit",minute:"2-digit"})}</td>
                        <td>{new Date(f.scheduled_arrival).toLocaleTimeString("en-US", {hour:"2-digit",minute:"2-digit"})}</td>
                        <td>{h}h {m}m</td>
                        <td>{parseFloat(f.distance_miles).toFixed(0)} mi</td>
                        <td>{f.tail_number}</td>
                        <td>${parseFloat(f.fare_USD).toFixed(2)}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}

          {/* Connecting flights */}
          {results.connecting_flights && results.connecting_flights.length > 0 && (
            <div className="card" style={{marginTop:"1rem"}}>
              <h4>Connecting Flights ({results.connecting_flights.length})</h4>
              <table className="pca-table">
                <thead>
                  <tr>
                    <th>Leg 1</th>
                    <th>Departs</th>
                    <th>Connection</th>
                    <th>Layover</th>
                    <th>Leg 2</th>
                    <th>Arrives</th>
                    <th>Total Time</th>
                    <th>Total Distance</th>
                    <th>Total Fare</th>
                  </tr>
                </thead>
                <tbody>
                  {results.connecting_flights.map((c, i) => {
                    const dur = c.total_duration_min;
                    const h = Math.floor(dur / 60);
                    const m = dur % 60;
                    const dist = parseFloat(c.leg1_distance) + parseFloat(c.leg2_distance);
                    return (
                      <tr key={i}>
                        <td>{c.leg1_flight_number}</td>
                        <td>{new Date(c.leg1_departure).toLocaleTimeString("en-US", {hour:"2-digit",minute:"2-digit"})}</td>
                        <td>{c.hub_iata} ({c.hub_city})</td>
                        <td>{c.layover_min} min</td>
                        <td>{c.leg2_flight_number}</td>
                        <td>{new Date(c.leg2_arrival).toLocaleTimeString("en-US", {hour:"2-digit",minute:"2-digit"})}</td>
                        <td>{h}h {m}m</td>
                        <td>{dist.toFixed(0)} mi</td>
                        <td>${(parseFloat(c.leg1_fare) + parseFloat(c.leg2_fare)).toFixed(2)}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}

          {results.direct_flights.length === 0 && (!results.connecting_flights || results.connecting_flights.length === 0) && (
            <p className="no-results">No flights found for this route and date.</p>
          )}
        </div>
      )}
    </div>
  );
}
