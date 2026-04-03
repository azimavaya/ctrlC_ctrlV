/**
 * Simulation.jsx — 14-day operations simulation page (admin-only).
 * Run the simulation day-by-day or all at once. Shows per-day stats
 * (flights, passengers, on-time %, delays, cancellations), aircraft lookup
 * with maintenance tracking (200-hour threshold), and reset capability.
 */
import { useState, useEffect, useCallback } from "react";
import { useAuth } from "../context/AuthContext";
import "./Simulation.css";

const SIM_DAYS = 14; // total days in the simulation period (March 9-22, 2026)

// Pre-defined challenges/disruptions for each simulation day
const DAY_CHALLENGES = {
  1:  "Follow timetable exactly",
  2:  "Follow timetable exactly",
  3:  "Bad weather: 25% of flights delayed",
  4:  "Follow timetable exactly",
  5:  "Icing: 20% of flights above 40\u00b0N delayed",
  6:  "Follow timetable exactly",
  7:  "Jet stream: E/W flights \u00b112% time",
  8:  "Follow timetable exactly",
  9:  "Gate delays: 5% of flights delayed",
  10: "Follow timetable exactly",
  11: "Aircraft failure at hub",
  12: "Follow timetable exactly",
  13: "8% of flights west of 103\u00b0W cancelled",
  14: "Follow timetable exactly",
};

// Formatting helpers
const fmt = (n) => (n ?? 0).toLocaleString();
/** Convert a simulation day number (1-14) to a readable date string */
const simDate = (day) => {
  const d = new Date(2026, 2, 8 + day); // March 9–22, 2026 (post-DST)
  return d.toLocaleDateString("en-US", { weekday: "short", month: "short", day: "numeric" });
};

/** Return CSS class for on-time percentage badge (green/yellow/red) */
function otBadgeClass(pct) {
  if (pct >= 90) return "sim-ot--good";
  if (pct >= 75) return "sim-ot--warn";
  return "sim-ot--bad";
}

// ── Main Component ───────────────────────────────────────────────────────────
export default function Simulation() {
  const { user, authFetch } = useAuth();
  const isAdmin = user?.role === "admin";

  // Simulation progress state
  const [simState, setSimState]     = useState("idle");   // "idle" | "running" | "complete"
  const [currentDay, setCurrentDay] = useState(0);        // last completed day (0-14)
  const [dayResults, setDayResults] = useState([]);        // array of per-day result objects
  const [isProgressing, setIsProgressing] = useState(false); // true while a day is being simulated
  const [error, setError]           = useState(null);

  // Day-detail panel state (shown when a day row is clicked)
  const [selectedDay, setSelectedDay] = useState(null);
  const [dayFlights, setDayFlights]   = useState(null);
  const [dayLoading, setDayLoading]   = useState(false);

  // Aircraft lookup state
  const [tailQuery, setTailQuery]     = useState("");      // selected tail number
  const [tailResult, setTailResult]   = useState(null);    // lookup response
  const [tailLoading, setTailLoading] = useState(false);
  const [aircraftList, setAircraftList] = useState([]);    // fleet list for dropdown


  // Load existing simulation data on mount
  const loadExisting = useCallback(async () => {
    try {
      const res = await authFetch("/api/simulation/status");
      const data = await res.json();
      if (data.has_data && data.days?.length > 0) {
        const maxDay = Math.max(...data.days.map(d => d.sim_day));
        setCurrentDay(maxDay);
        setDayResults(data.days.map(d => {
          const op = (d.completed ?? 0) + (d.delayed ?? 0);
          return {
            day: d.sim_day,
            date: simDate(d.sim_day),
            flights: d.total_flights,
            completed: d.completed ?? 0,
            delayed: d.delayed ?? 0,
            cancelled: d.cancelled ?? 0,
            passengers: d.total_passengers ?? 0,
            onTimePct: op > 0 ? Math.round((d.completed / op) * 100) : 100,
            challenge: DAY_CHALLENGES[d.sim_day] || "",
          };
        }));
        setSimState(maxDay >= SIM_DAYS ? "complete" : "running");
      }
    } catch { /* ignore */ }
  }, [authFetch]);

  useEffect(() => { loadExisting(); }, [loadExisting]);

  // Load aircraft list for dropdown
  useEffect(() => {
    fetch("/api/flights/fleet")
      .then(r => r.json())
      .then(d => setAircraftList(Array.isArray(d) ? d : []))
      .catch(() => {});
  }, []);

  /** Transform the API response for a single day into a display-ready object */
  const buildDayResult = (d, result) => {
    const operated = result.completed + result.delayed;
    const otPct = operated > 0 ? Math.round((result.completed / operated) * 100) : 100;
    return {
      day: d,
      date: simDate(d),
      flights: result.total_flights,
      completed: result.completed,
      delayed: result.delayed,
      cancelled: result.cancelled,
      passengers: result.passengers,
      onTimePct: otPct,
      revenue: result.revenue,
      costs: result.costs,
      challenge: DAY_CHALLENGES[d] || "",
      events: result.events || [],
    };
  };

  const refreshAircraftLookup = useCallback(async () => {
    if (!tailQuery) return;
    try {
      const r = await authFetch(`/api/simulation/aircraft/${tailQuery}`);
      const data = await r.json();
      setTailResult(r.ok ? data : { error: data.error });
    } catch { /* ignore */ }
  }, [tailQuery, authFetch]);

  /** Simulate a single day by POSTing to /api/simulation/progress */
  const handleProgressDay = useCallback(async () => {
    if (currentDay >= SIM_DAYS) return;
    setIsProgressing(true);
    setError(null);
    const nextDay = currentDay + 1;

    try {
      const res = await authFetch("/api/simulation/progress", {
        method: "POST",
        body: JSON.stringify({ day: nextDay }),
      });
      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.error || "Failed to progress day");
      }
      const result = await res.json();
      const dayResult = buildDayResult(nextDay, result);

      setDayResults(prev => [...prev, dayResult]);
      setCurrentDay(nextDay);

      if (nextDay >= SIM_DAYS) {
        setSimState("complete");
      } else {
        setSimState("running");
      }
      refreshAircraftLookup();
    } catch (e) {
      setError(e.message);
    } finally {
      setIsProgressing(false);
    }
  }, [currentDay, authFetch, refreshAircraftLookup]);

  /** Run all remaining simulation days sequentially */
  const handleRunAll = useCallback(async () => {
    setIsProgressing(true);
    setError(null);
    const newResults = [];

    try {
      for (let d = currentDay + 1; d <= SIM_DAYS; d++) {
        const res = await authFetch("/api/simulation/progress", {
          method: "POST",
          body: JSON.stringify({ day: d }),
        });
        if (!res.ok) {
          const data = await res.json();
          throw new Error(data.error || `Failed on day ${d}`);
        }
        const result = await res.json();
        newResults.push(buildDayResult(d, result));
      }

      setDayResults(prev => [...prev, ...newResults]);
      setCurrentDay(SIM_DAYS);
      setSimState("complete");
      refreshAircraftLookup();
    } catch (e) {
      setError(e.message);
    } finally {
      setIsProgressing(false);
    }
  }, [currentDay, authFetch, refreshAircraftLookup]);

  /** Reset the simulation — clears all sim data on the backend and resets UI state */
  const handleReset = async () => {
    setIsProgressing(true);
    try {
      await authFetch("/api/simulation/reset", { method: "POST" });
      setSimState("idle");
      setCurrentDay(0);
      setDayResults([]);
      setSelectedDay(null);
      setDayFlights(null);
      setTailResult(null);
      setError(null);
    } catch { /* ignore */ } finally {
      setIsProgressing(false);
    }
  };

  /** Fetch detailed flight data for a specific simulation day (toggle on/off) */
  const loadDay = async (day) => {
    if (selectedDay === day) {
      setSelectedDay(null);
      setDayFlights(null);
      return;
    }
    setSelectedDay(day);
    setDayLoading(true);
    try {
      const res = await authFetch(`/api/simulation/day/${day}`);
      const data = await res.json();
      setDayFlights(data.flights || []);
    } catch {
      setDayFlights([]);
    } finally {
      setDayLoading(false);
    }
  };

  /** Look up an aircraft by tail number to see its simulation history */
  const lookupTail = async () => {
    if (!tailQuery.trim()) return;
    setTailLoading(true);
    setTailResult(null);
    try {
      const res = await authFetch(`/api/simulation/aircraft/${tailQuery.trim()}`);
      const data = await res.json();
      setTailResult(res.ok ? data : { error: data.error });
    } catch {
      setTailResult({ error: "Request failed" });
    } finally {
      setTailLoading(false);
    }
  };

  // Aggregate totals across all simulated days for the stats row
  const totals = dayResults.reduce((acc, r) => ({
    flights:    acc.flights    + (r.flights ?? 0),
    completed:  acc.completed  + (r.completed ?? 0),
    delayed:    acc.delayed    + (r.delayed ?? 0),
    cancelled:  acc.cancelled  + (r.cancelled ?? 0),
    passengers: acc.passengers + (r.passengers ?? 0),
  }), { flights: 0, completed: 0, delayed: 0, cancelled: 0, passengers: 0 });

  const avgOnTime = dayResults.length
    ? Math.round(dayResults.reduce((s, r) => s + (r.onTimePct ?? 100), 0) / dayResults.length)
    : null;

  const progressPct = Math.round((currentDay / SIM_DAYS) * 100);

  // ── Render ──────────────────────────────────────────────────────────────────
  return (
    <div className="sim-page">
      {/* Header */}
      <div className="sim-header">
        <div>
          <h2>14-Day Simulation</h2>
          <p className="sim-header-sub">Panther Cloud Air — March 2026 Operations</p>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
          {/* Status chip */}
          <div className="sim-status-chip">
            <span className={`sim-dot ${
              simState === "idle" ? "sim-dot--gray" :
              simState === "running" ? "sim-dot--green" :
              "sim-dot--gold"
            }`} />
            {simState === "idle" ? "Idle" : simState === "running" ? "Running" : "Complete"}
          </div>
        </div>
      </div>

      {/* Error banner */}
      {error && (
        <div style={{ background: "#fee2e2", color: "#991b1b", padding: "0.75rem 1rem", borderRadius: "var(--radius)", fontSize: "0.88rem" }}>
          {error}
        </div>
      )}

      {/* Stats row */}
      <div className="sim-stats-row">
        <div className="sim-stat">
          <span>{fmt(totals.flights)}</span>
          <label>Total Flights</label>
        </div>
        <div className="sim-stat sim-stat--good">
          <span>{fmt(totals.completed)}</span>
          <label>Completed</label>
        </div>
        <div className="sim-stat sim-stat--warn">
          <span>{fmt(totals.delayed)}</span>
          <label>Delayed</label>
        </div>
        <div className="sim-stat sim-stat--danger">
          <span>{fmt(totals.cancelled)}</span>
          <label>Cancelled</label>
        </div>
        <div className="sim-stat">
          <span>{fmt(totals.passengers)}</span>
          <label>Passengers</label>
        </div>
        <div className={`sim-stat ${avgOnTime !== null ? (avgOnTime >= 90 ? "sim-stat--good" : avgOnTime >= 75 ? "sim-stat--warn" : "sim-stat--danger") : ""}`}>
          <span>{avgOnTime !== null ? avgOnTime + "%" : "--"}</span>
          <label>Avg On-Time %</label>
        </div>
      </div>

      {/* Main grid */}
      <div className="sim-main-grid">
        {/* Left column */}
        <div className="sim-left-col">
          {/* Control card */}
          <div className="card sim-control-card">
            <h3>Simulation Controls</h3>
            <div className="sim-progress-bar-wrap">
              <div className="sim-progress-bar" style={{ width: `${progressPct}%` }} />
            </div>
            <div className="sim-day-label">
              Day {currentDay} of {SIM_DAYS} {simState === "complete" && " — Complete"}
            </div>
            <div className="sim-btn-row">
              <button
                className="btn-primary sim-btn-progress"
                onClick={handleProgressDay}
                disabled={isProgressing || currentDay >= SIM_DAYS}
              >
                {isProgressing ? <span className="sim-spinner" /> : "Run Next Day"}
              </button>
              <button
                className="btn-secondary"
                onClick={handleRunAll}
                disabled={isProgressing || currentDay >= SIM_DAYS}
              >
                Run All
              </button>
              {isAdmin && (
                <button
                  className="btn-danger"
                  onClick={handleReset}
                  disabled={isProgressing}
                >
                  Reset
                </button>
              )}
            </div>
            {!isAdmin && (
              <p className="sim-readonly-note">Only admins can reset the simulation.</p>
            )}
          </div>


        </div>

        {/* Right column */}
        <div className="sim-right-col">
          {/* Results table */}
          <div className="card sim-results-card">
            <h3>Day-by-Day Results</h3>
            {dayResults.length === 0 ? (
              <p className="sim-empty">No simulation data yet. Run the first day to see results.</p>
            ) : (
              <div className="sim-results-scroll">
                <table className="sim-results-table">
                  <thead>
                    <tr>
                      <th>Day</th>
                      <th>Date</th>
                      <th>Flights</th>
                      <th>Completed</th>
                      <th>Delayed</th>
                      <th>Cancelled</th>
                      <th>Pax</th>
                      <th>On-Time</th>
                      <th>Challenge</th>
                    </tr>
                  </thead>
                  <tbody>
                    {dayResults.map((r) => (
                      <tr
                        key={r.day}
                        onClick={() => loadDay(r.day)}
                        className={selectedDay === r.day ? "sim-row-selected" : ""}
                        style={{ cursor: "pointer" }}
                      >
                        <td>{r.day}</td>
                        <td>{r.date}</td>
                        <td>{fmt(r.flights)}</td>
                        <td>{fmt(r.completed)}</td>
                        <td className={r.delayed > 0 ? "sim-cell--warn" : ""}>{fmt(r.delayed)}</td>
                        <td className={r.cancelled > 0 ? "sim-cell--danger" : ""}>{fmt(r.cancelled)}</td>
                        <td>{fmt(r.passengers)}</td>
                        <td>
                          <span className={`sim-ot-badge ${otBadgeClass(r.onTimePct)}`}>
                            {r.onTimePct}%
                          </span>
                        </td>
                        <td className="sim-disruptions-cell">
                          {r.challenge && r.challenge !== "Follow timetable exactly" ? (
                            <span className="sim-disrupt-tag">{r.challenge}</span>
                          ) : (
                            <span className="sim-nodisrupt">None</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {/* Day detail / flights */}
          {selectedDay !== null && (
            <div className="card sim-results-card">
              <h3>Day {selectedDay} Flights — {simDate(selectedDay)}</h3>
              {dayLoading ? (
                <p style={{ textAlign: "center", padding: "1rem" }}>
                  <span className="sim-spinner" style={{ borderColor: "rgba(0,100,200,0.3)", borderTopColor: "var(--pca-blue)" }} />
                </p>
              ) : dayFlights && dayFlights.length > 0 ? (
                <div className="sim-results-scroll">
                  <table className="sim-results-table">
                    <thead>
                      <tr>
                        <th>Flight</th>
                        <th>Origin</th>
                        <th>Destination</th>
                        <th>Aircraft</th>
                        <th>Status</th>
                        <th>Pax</th>
                      </tr>
                    </thead>
                    <tbody>
                      {dayFlights.map((f, i) => (
                        <tr key={i}>
                          <td>{f.flight_number || "--"}</td>
                          <td>{f.origin_city || f.origin_iata || "--"}</td>
                          <td>{f.dest_city || f.dest_iata || "--"}</td>
                          <td>{f.tail_number || "--"}</td>
                          <td className={
                            f.status === "cancelled" ? "sim-cell--danger" :
                            f.status === "delayed" ? "sim-cell--warn" : ""
                          }>
                            {f.status === "cancelled" && f.delay_reason && f.delay_reason.toLowerCase().includes("maintenance")
                              ? "maintenance"
                              : f.status || "--"}
                          </td>
                          <td>{fmt(f.passengers_boarded ?? 0)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <p className="sim-empty">No flight data available for this day.</p>
              )}
            </div>
          )}

          {/* Aircraft lookup */}
          <div className="card sim-results-card">
            <h3>Aircraft Lookup</h3>
            <div style={{ marginBottom: "0.75rem" }}>
              <select
                value={tailQuery}
                onChange={(e) => {
                  const val = e.target.value;
                  setTailQuery(val);
                  if (val) {
                    setTailLoading(true);
                    setTailResult(null);
                    authFetch(`/api/simulation/aircraft/${val}`)
                      .then(r => r.json().then(data => setTailResult(r.ok ? data : { error: data.error })))
                      .catch(() => setTailResult({ error: "Request failed" }))
                      .finally(() => setTailLoading(false));
                  } else {
                    setTailResult(null);
                  }
                }}
                style={{
                  width: "100%", padding: "0.5rem 0.75rem", border: "1px solid var(--pca-border)",
                  borderRadius: "var(--radius)", fontFamily: "var(--font)", fontSize: "0.88rem",
                  background: "var(--pca-white)", color: "var(--pca-text, inherit)",
                }}
              >
                <option value="">Select an aircraft...</option>
                {aircraftList.map(a => (
                  <option key={a.tail_number} value={a.tail_number}>
                    {a.tail_number} — {a.model} ({a.current_airport})
                  </option>
                ))}
              </select>
            </div>
            {tailLoading && (
              <p style={{ textAlign: "center", padding: "1rem" }}>
                <span className="sim-spinner" style={{ borderColor: "rgba(0,100,200,0.3)", borderTopColor: "var(--pca-blue)" }} />
              </p>
            )}
            {tailResult && (
              tailResult.error ? (
                <p style={{ color: "#991b1b", fontSize: "0.85rem" }}>{tailResult.error}</p>
              ) : (
                <div>
                  <div className="sim-stats-row" style={{ marginBottom: "0.75rem" }}>
                    <div className="sim-stat">
                      <span style={{ fontSize: "1.1rem" }}>{tailResult.tail_number}</span>
                      <label>Tail Number</label>
                    </div>
                    <div className="sim-stat">
                      <span>{tailResult.total_flights}</span>
                      <label>Total Flights</label>
                    </div>
                    <div className={`sim-stat ${otBadgeClass(tailResult.pct_on_time ?? 0) === "sim-ot--good" ? "sim-stat--good" : otBadgeClass(tailResult.pct_on_time ?? 0) === "sim-ot--warn" ? "sim-stat--warn" : "sim-stat--danger"}`}>
                      <span>{Math.round(tailResult.pct_on_time ?? 0)}%</span>
                      <label>On-Time</label>
                    </div>
                    <div className={`sim-stat ${
                      (tailResult.total_hours ?? 0) >= 200 ? "sim-stat--danger" :
                      (tailResult.total_hours ?? 0) >= 180 ? "sim-stat--warn" : ""
                    }`}>
                      <span>{(tailResult.total_hours ?? 0).toFixed(1)}</span>
                      <label>Flight Hours</label>
                    </div>
                  </div>
                  {tailResult.maintenance_status && (
                    <div style={{
                      padding: "0.4rem 0.75rem",
                      marginBottom: "0.75rem",
                      borderRadius: "var(--radius)",
                      fontSize: "0.82rem",
                      fontWeight: 600,
                      background: tailResult.maintenance_status === "In maintenance" ? "#fee2e2" : "#fef3c7",
                      color: tailResult.maintenance_status === "In maintenance" ? "#991b1b" : "#92400e",
                    }}>
                      {tailResult.maintenance_status === "In maintenance"
                        ? "Aircraft in maintenance (200+ flight hours)"
                        : `Approaching maintenance — ${(200 - (tailResult.total_hours ?? 0)).toFixed(1)} hours remaining`}
                    </div>
                  )}
                  {tailResult.flights?.length > 0 && (
                    <div className="sim-results-scroll" style={{ maxHeight: 400 }}>
                      <table className="sim-results-table">
                        <thead>
                          <tr>
                            <th>Day</th>
                            <th>Flight</th>
                            <th>From</th>
                            <th>To</th>
                            <th>Status</th>
                          </tr>
                        </thead>
                        <tbody>
                          {tailResult.flights.map((f, i) => (
                            <tr key={i}>
                              <td>{f.sim_day ?? "--"}</td>
                              <td>{f.flight_number || "--"}</td>
                              <td>{f.origin_city || f.origin_iata || "--"}</td>
                              <td>{f.dest_city || f.dest_iata || "--"}</td>
                              <td className={
                                f.status === "cancelled" ? "sim-cell--danger" :
                                f.status === "delayed" ? "sim-cell--warn" : ""
                              }>{f.status === "cancelled" && f.delay_reason && f.delay_reason.toLowerCase().includes("maintenance")
                                ? "maintenance"
                                : f.status || "--"}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </div>
              )
            )}
          </div>

        </div>
      </div>
    </div>
  );
}
