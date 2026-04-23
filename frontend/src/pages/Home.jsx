import { useEffect, useState, useRef } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

const API = "/api";

function useCountUp(target, duration = 1200) {
  const [value, setValue] = useState(0);
  const prev = useRef(null);
  useEffect(() => {
    if (target == null || target === prev.current) return;
    prev.current = target;
    const start = performance.now();
    const from = 0;
    const step = (now) => {
      const t = Math.min((now - start) / duration, 1);
      const eased = 1 - Math.pow(1 - t, 3);
      setValue(Math.round(from + (target - from) * eased));
      if (t < 1) requestAnimationFrame(step);
    };
    requestAnimationFrame(step);
  }, [target, duration]);
  return value;
}

function todayLabel() {
  return new Date().toLocaleDateString("en-US", {
    weekday: "long", month: "long", day: "numeric", year: "numeric",
  });
}

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

export default function Home() {
  const { user } = useAuth();
  const [live, setLive]             = useState(null);

  const animTotal     = useCountUp(live?.total_today);
  const animInAir     = useCountUp(live?.in_air);
  const animCompleted = useCountUp(live?.completed);
  const animRemaining = useCountUp(live?.remaining);

  const loadLive = () => {
    fetch(`${API}/flights/live-stats`)
      .then(r => r.json())
      .then(d => setLive(d))
      .catch(() => {});
  };

  useEffect(() => { loadLive(); }, []);

  useEffect(() => {
    const id = setInterval(loadLive, 60_000);
    return () => clearInterval(id);
  }, []);

  return (
    <div className="home">

      <div className="home-hero">
        <div className="home-hero-left">
          <div className="home-ops-badge">Operations Active</div>
          <h1 className="home-title">Panther Cloud Air</h1>
          <p className="home-subtitle">{todayLabel()}</p>
          <p className="home-tagline">
            31 airports &nbsp;·&nbsp; 56 aircraft &nbsp;·&nbsp; 4 hubs
          </p>
        </div>
        <div className="home-hero-right">
          {live ? (
            <div className="home-live-strip">
              <div className="home-live-item">
                <span className="home-live-val home-live-total">{animTotal}</span>
                <span className="home-live-lbl">Flights Today</span>
              </div>
              <div className="home-live-divider" />
              <div className="home-live-item">
                <span className="home-live-val home-live-air">{animInAir}</span>
                <span className="home-live-lbl">In the Air</span>
              </div>
              <div className="home-live-divider" />
              <div className="home-live-item">
                <span className="home-live-val home-live-done">{animCompleted}</span>
                <span className="home-live-lbl">Completed</span>
              </div>
              <div className="home-live-divider" />
              <div className="home-live-item">
                <span className="home-live-val home-live-left">{animRemaining}</span>
                <span className="home-live-lbl">Remaining</span>
              </div>
            </div>
          ) : (
            <div className="home-clock-block">
              <div className="home-clock-label">Flights Today</div>
              <div className="home-clock-time">—</div>
              <div className="home-clock-date">loading…</div>
            </div>
          )}
        </div>
      </div>

      {live && (live.in_air_flights?.length > 0 || live.next_departures?.length > 0 || live.completed_flights?.length > 0) && (
        <div className="home-live-tables">
          {live.completed_flights?.length > 0 && (
            <div className="card home-live-card">
              <div className="home-live-card-hdr home-live-card-hdr--done">
                Completed ({live.completed})
              </div>
              <div className="home-live-scroll">
                <table className="home-live-tbl">
                  <thead>
                    <tr><th>Flight</th><th>Route</th><th>Aircraft</th><th>Arrived (UTC)</th></tr>
                  </thead>
                  <tbody>
                    {live.completed_flights.map((f, i) => (
                      <tr key={i}>
                        <td className="home-fn">{f.flight_number}</td>
                        <td>{f.origin_iata} → {f.dest_iata}</td>
                        <td className="home-aircraft">{f.tail_number}</td>
                        <td className="home-time">{fmt(f.scheduled_arrival)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
          {live.in_air_flights?.length > 0 && (
            <div className="card home-live-card">
              <div className="home-live-card-hdr">
                <span className="home-live-dot" />
                In the Air ({live.in_air})
              </div>
              <div className="home-live-scroll">
                <table className="home-live-tbl">
                  <thead>
                    <tr><th>Flight</th><th>Route</th><th>Aircraft</th><th>ETA (UTC)</th></tr>
                  </thead>
                  <tbody>
                    {live.in_air_flights.map((f, i) => (
                      <tr key={i}>
                        <td className="home-fn">{f.flight_number}</td>
                        <td>{f.origin_iata} → {f.dest_iata}</td>
                        <td className="home-aircraft">{f.tail_number}</td>
                        <td className="home-time">{fmt(f.scheduled_arrival)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
          {live.next_departures?.length > 0 && (
            <div className="card home-live-card">
              <div className="home-live-card-hdr">Next Departures ({live.remaining})</div>
              <div className="home-live-scroll">
                <table className="home-live-tbl">
                  <thead>
                    <tr><th>Flight</th><th>Route</th><th>Aircraft</th><th>Departs (UTC)</th></tr>
                  </thead>
                  <tbody>
                    {live.next_departures.map((f, i) => (
                      <tr key={i}>
                        <td className="home-fn">{f.flight_number}</td>
                        <td>{f.origin_iata} → {f.dest_iata}</td>
                        <td className="home-aircraft">{f.tail_number}</td>
                        <td className="home-time">{fmt(f.scheduled_departure)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}

      <div className="home-cards">
        <Link to="/book" className="home-card">
          <div className="home-card-icon">✈</div>
          <h3>Book Flight</h3>
          <p>Search available routes, compare fares, and book your flight.</p>
        </Link>
        <Link to="/bookings" className="home-card">
          <div className="home-card-icon">🎫</div>
          <h3>My Bookings</h3>
          <p>View and manage your flight reservations.</p>
        </Link>
        <Link to="/timetable" className="home-card">
          <div className="home-card-icon">🗓</div>
          <h3>Timetable</h3>
          <p>View the complete schedule for all routes and airports.</p>
        </Link>
        {user?.role === "admin" && (
          <Link to="/admin" className="home-card">
            <div className="home-card-icon">⚙</div>
            <h3>Admin Dashboard</h3>
            <p>Manage users, fleet, and system settings.</p>
          </Link>
        )}
      </div>

    </div>
  );
}
