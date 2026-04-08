import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import "./Home.css";

const API = "/api";

const TZ_OPTIONS = {
  UTC: { label: "UTC", zone: "UTC" },
  ET:  { label: "ET",  zone: "America/New_York" },
};

function todayLabel() {
  return new Date().toLocaleDateString("en-US", {
    weekday: "long", month: "long", day: "numeric", year: "numeric",
  });
}

function fmt(dt, tz) {
  if (!dt) return "—";
  const d = new Date(dt + (dt.endsWith("Z") ? "" : "Z"));
  const now = new Date();
  const today = new Date(Date.UTC(
    now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate(),
    d.getUTCHours(), d.getUTCMinutes(), d.getUTCSeconds()
  ));
  return today.toLocaleTimeString("en-US", {
    hour: "2-digit", minute: "2-digit", hour12: true,
    timeZone: TZ_OPTIONS[tz]?.zone ?? "UTC",
  });
}

export default function Home() {
  const { user } = useAuth();
  const [live, setLive]             = useState(null);
  const [tz, setTz]                 = useState("UTC");
  const [showInfo, setShowInfo]     = useState(false);

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

      <div className="home-hero" style={{ position: "relative" }}>
        {user?.role === "admin" && (
          <button
            onClick={() => setShowInfo(true)}
            title="System Information"
            style={{
              position: "absolute", top: 12, right: 12,
              width: 28, height: 28, borderRadius: "50%", border: "2px solid rgba(255,255,255,0.6)",
              background: "transparent", color: "#fff", fontWeight: 700, fontSize: "0.85rem",
              cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center",
            }}
          >i</button>
        )}
        <div className="home-hero-left">
          <div className="home-ops-badge">Operations Active</div>
          <h1 className="home-title">Panther Cloud Air</h1>
          <p className="home-subtitle">{todayLabel()}</p>
          <p className="home-tagline">
            31 airports &nbsp;·&nbsp; 56 aircraft &nbsp;·&nbsp; 4 hubs
          </p>
          <div className="home-tz-toggle">
            {Object.keys(TZ_OPTIONS).map(k => (
              <button
                key={k}
                className={`home-tz-btn${tz === k ? " home-tz-btn--active" : ""}`}
                onClick={() => setTz(k)}
              >
                {TZ_OPTIONS[k].label}
              </button>
            ))}
          </div>
        </div>
        <div className="home-hero-right">
          {live ? (
            <div className="home-live-strip">
              <div className="home-live-item">
                <span className="home-live-val home-live-total">{live.total_today}</span>
                <span className="home-live-lbl">Flights Today</span>
              </div>
              <div className="home-live-divider" />
              <div className="home-live-item">
                <span className="home-live-val home-live-air">{live.in_air}</span>
                <span className="home-live-lbl">In the Air</span>
              </div>
              <div className="home-live-divider" />
              <div className="home-live-item">
                <span className="home-live-val home-live-done">{live.completed}</span>
                <span className="home-live-lbl">Completed</span>
              </div>
              <div className="home-live-divider" />
              <div className="home-live-item">
                <span className="home-live-val home-live-left">{live.remaining}</span>
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
                    <tr><th>Flight</th><th>Route</th><th>Aircraft</th><th>Arrived</th></tr>
                  </thead>
                  <tbody>
                    {live.completed_flights.map((f, i) => (
                      <tr key={i}>
                        <td className="home-fn">{f.flight_number}</td>
                        <td>{f.origin_iata} → {f.dest_iata}</td>
                        <td className="home-aircraft">{f.tail_number}</td>
                        <td className="home-time">{fmt(f.scheduled_arrival, tz)}</td>
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
                    <tr><th>Flight</th><th>Route</th><th>Aircraft</th><th>ETA</th></tr>
                  </thead>
                  <tbody>
                    {live.in_air_flights.map((f, i) => (
                      <tr key={i}>
                        <td className="home-fn">{f.flight_number}</td>
                        <td>{f.origin_iata} → {f.dest_iata}</td>
                        <td className="home-aircraft">{f.tail_number}</td>
                        <td className="home-time">{fmt(f.scheduled_arrival, tz)}</td>
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
                    <tr><th>Flight</th><th>Route</th><th>Aircraft</th><th>Departs</th></tr>
                  </thead>
                  <tbody>
                    {live.next_departures.map((f, i) => (
                      <tr key={i}>
                        <td className="home-fn">{f.flight_number}</td>
                        <td>{f.origin_iata} → {f.dest_iata}</td>
                        <td className="home-aircraft">{f.tail_number}</td>
                        <td className="home-time">{fmt(f.scheduled_departure, tz)}</td>
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

      {showInfo && (
        <div className="info-overlay" onClick={() => setShowInfo(false)}>
          <div className="info-panel" onClick={e => e.stopPropagation()}>
            <button className="info-close" onClick={() => setShowInfo(false)}>&times;</button>
            <h2 style={{ marginTop: 0 }}>Panther Cloud Air — System Reference</h2>

            <h3>Timetable (Part 1)</h3>
            <p>The scheduler generates a single template day of ~310 flights using a hub-and-spoke model with 4 hubs (ATL, ORD, DFW, LAX). Each of the 56 aircraft performs round-trip flights from its base airport between 05:00–01:00 local time. This template repeats identically every day — the same flight numbers, routes, and times.</p>
            <p>The A350-900 (N350CA) is dedicated to the JFK↔CDG international route. All other aircraft cycle through assigned destinations via round-robin.</p>

            <h3>14-Day Simulation (Part 2)</h3>
            <p>The simulation runs March 9–22, 2026, offsetting the template schedule to each day. Each day applies a fixed challenge from the spec:</p>
            <ul>
              <li><strong>Days 1,2,4,6,8,10,12,14:</strong> No disruptions</li>
              <li><strong>Day 3:</strong> 25% of flights get weather delays (+1 min to +15% flight time)</li>
              <li><strong>Day 5:</strong> 20% of flights from airports above 40°N get icing delays (10–45 min)</li>
              <li><strong>Day 7:</strong> Jet stream — eastbound flights +12% time, westbound −12%</li>
              <li><strong>Day 9:</strong> 5% of flights get gate delays (5–90 min)</li>
              <li><strong>Day 11:</strong> One aircraft fails at a hub — grounded for the full day</li>
              <li><strong>Day 13:</strong> 8% of flights from airports west of 103°W cancelled; passengers rebooked</li>
            </ul>

            <h3>Passenger Demand</h3>
            <p>Daily demand from airport A to B is calculated as:</p>
            <code style={{ display: "block", background: "var(--pca-light)", padding: "0.5rem", borderRadius: 6, fontSize: "0.82rem", margin: "0.5rem 0" }}>
              demand = pop_A × 0.005 × 0.02 × (pop_B / total_reachable_pop)
            </code>
            <p>0.5% of the population flies daily, PCA holds 2% market share, and demand is proportional to the destination's metro population relative to all reachable airports. Passengers without a direct flight are routed through hub connections.</p>

            <h3>Fare Pricing</h3>
            <p>Fares are set so the airline breaks even at 30% load factor. Each fare covers:</p>
            <code style={{ display: "block", background: "var(--pca-light)", padding: "0.5rem", borderRadius: 6, fontSize: "0.82rem", margin: "0.5rem 0" }}>
              fare = (fuel_cost + landing_fees + lease_share) / (capacity × 0.30)
            </code>
            <ul>
              <li><strong>Fuel (domestic):</strong> burn_rate_L/hr × flight_hours × 0.264172 gal/L × $6.19/gal</li>
              <li><strong>Fuel (Paris):</strong> burn_rate_L/hr × flight_hours × €1.97/L × EUR/USD rate</li>
              <li><strong>Landing fees:</strong> $2,000 per takeoff + $2,000 per landing (US); €2,100 each (CDG)</li>
              <li><strong>Lease share:</strong> monthly_lease / 30 days / flights_per_day for that aircraft</li>
            </ul>

            <h3>Flight Time Calculation</h3>
            <p>Aircraft operate at 80% of max airspeed. Flight time includes taxi, takeoff (1 min), climb (250→280 kt → cruise speed), cruise, descent (250→200 kt), and landing (2 min).</p>
            <p><strong>Wind effect:</strong> A ±4.5% adjustment based on heading. Due east (90°) flights are 4.5% faster, due west (270°) are 4.5% slower, using the formula:</p>
            <code style={{ display: "block", background: "var(--pca-light)", padding: "0.5rem", borderRadius: 6, fontSize: "0.82rem", margin: "0.5rem 0" }}>
              wind_factor = −0.045 × sin(heading_radians)
            </code>

            <h3>Gate Allocation</h3>
            <p>Gates per airport = <code>min(5, round(metro_pop_M))</code> where .5 rounds up. Hub airports get 11 gates. If no gate is available, the aircraft waits on the tarmac.</p>
            <table style={{ width: "100%", fontSize: "0.82rem", borderCollapse: "collapse", margin: "0.5rem 0" }}>
              <thead><tr style={{ borderBottom: "2px solid var(--pca-border)" }}><th style={{ textAlign: "left", padding: "4px 8px" }}>Airport Type</th><th style={{ textAlign: "left", padding: "4px 8px" }}>Gates</th><th style={{ textAlign: "left", padding: "4px 8px" }}>Taxi Time</th></tr></thead>
              <tbody>
                <tr><td style={{ padding: "4px 8px" }}>Hub (ATL, ORD, DFW, LAX)</td><td style={{ padding: "4px 8px" }}>11</td><td style={{ padding: "4px 8px" }}>min(20, 15 + floor((pop_M − 9) / 2))</td></tr>
                <tr><td style={{ padding: "4px 8px" }}>Non-hub</td><td style={{ padding: "4px 8px" }}>min(5, round(pop_M))</td><td style={{ padding: "4px 8px" }}>min(13, pop × 0.0000075)</td></tr>
              </tbody>
            </table>

            <h3>Cruising Altitudes</h3>
            <table style={{ width: "100%", fontSize: "0.82rem", borderCollapse: "collapse", margin: "0.5rem 0" }}>
              <thead><tr style={{ borderBottom: "2px solid var(--pca-border)" }}><th style={{ textAlign: "left", padding: "4px 8px" }}>Distance</th><th style={{ textAlign: "left", padding: "4px 8px" }}>Altitude</th></tr></thead>
              <tbody>
                <tr><td style={{ padding: "4px 8px" }}>International (CDG)</td><td style={{ padding: "4px 8px" }}>38,000 ft</td></tr>
                <tr><td style={{ padding: "4px 8px" }}>≥ 1,500 miles</td><td style={{ padding: "4px 8px" }}>35,000 ft</td></tr>
                <tr><td style={{ padding: "4px 8px" }}>350–1,499 miles</td><td style={{ padding: "4px 8px" }}>30,000 ft</td></tr>
                <tr><td style={{ padding: "4px 8px" }}>200–349 miles</td><td style={{ padding: "4px 8px" }}>25,000 ft</td></tr>
                <tr><td style={{ padding: "4px 8px" }}>&lt; 200 miles</td><td style={{ padding: "4px 8px" }}>20,000 ft</td></tr>
              </tbody>
            </table>

            <h3>Aircraft Maintenance</h3>
            <p>Every 200 flight hours, an aircraft enters maintenance for 2 days (1.5 rounded up). Maintenance occurs at hub airports only, max 3 aircraft per hub simultaneously. The aircraft's flight hours reset to 0 after completion. Cost is included in the monthly lease. In the 14-day simulation, only N350CA (JFK↔CDG) accumulates enough hours (~18 hrs/day) to trigger maintenance — it enters on day 12 and returns on day 14.</p>

            <h3>Daylight Saving Time</h3>
            <p>The simulation runs during US DST (began March 8, 2026). France switches to CEST on March 29. All times stored in UTC; local times are derived from each airport's timezone. Arizona (PHX) and Hawaii (HNL) do not observe DST.</p>

            <h3>Turnaround &amp; Connections</h3>
            <ul>
              <li><strong>Standard turnaround:</strong> 40 min (disembark 15 + clean/crew 10 + board 15)</li>
              <li><strong>With refueling:</strong> 50 min (+10 min fuel, for routes &gt; 800 mi)</li>
              <li><strong>Passenger connection:</strong> 30 min minimum between flights</li>
              <li><strong>Door close:</strong> 15 min before scheduled departure</li>
            </ul>

            <h3>Booking</h3>
            <p>The Book Flight page searches the template timetable for direct, 1-stop, and 2-stop connections. Layovers must be 30–360 minutes. Fares are summed across legs. Bookings are stored with a unique 6-character reference code. Note: bookings are decorative for Part 1 — the simulation generates its own passenger demand independently.</p>

            <h3>Security &amp; Authentication</h3>
            <ul>
              <li><strong>Passwords:</strong> Hashed with bcrypt (adaptive, salted). Never stored or returned in plaintext.</li>
              <li><strong>JWT tokens:</strong> HS256-signed, 8-hour expiry. Sent as Bearer token in Authorization header.</li>
              <li><strong>Rate limiting:</strong> Max 10 login attempts per minute per IP address.</li>
              <li><strong>Account lockout:</strong> After 5 failed attempts, account is locked until admin unlocks it.</li>
              <li><strong>Roles:</strong> <code>user</code> (view flights, book, see own bookings) and <code>admin</code> (simulation, finances, user management, all bookings).</li>
              <li><strong>SQL injection:</strong> All queries use parameterized statements. No string interpolation in SQL.</li>
              <li><strong>Database:</strong> Not exposed outside the Docker network. Backend connects as restricted <code>pca_user</code>.</li>
            </ul>

            <h3>Fleet Summary</h3>
            <table style={{ width: "100%", fontSize: "0.82rem", borderCollapse: "collapse", margin: "0.5rem 0" }}>
              <thead><tr style={{ borderBottom: "2px solid var(--pca-border)" }}><th style={{ textAlign: "left", padding: "4px 8px" }}>Type</th><th style={{ padding: "4px 8px" }}>Count</th><th style={{ padding: "4px 8px" }}>Capacity</th><th style={{ padding: "4px 8px" }}>Speed (op)</th><th style={{ padding: "4px 8px" }}>Range</th></tr></thead>
              <tbody>
                <tr><td style={{ padding: "4px 8px" }}>Boeing 737-600</td><td style={{ padding: "4px 8px", textAlign: "center" }}>15</td><td style={{ padding: "4px 8px", textAlign: "center" }}>119</td><td style={{ padding: "4px 8px", textAlign: "center" }}>701 km/h</td><td style={{ padding: "4px 8px", textAlign: "center" }}>5,648 km</td></tr>
                <tr><td style={{ padding: "4px 8px" }}>Boeing 737-800</td><td style={{ padding: "4px 8px", textAlign: "center" }}>15</td><td style={{ padding: "4px 8px", textAlign: "center" }}>162</td><td style={{ padding: "4px 8px", textAlign: "center" }}>701 km/h</td><td style={{ padding: "4px 8px", textAlign: "center" }}>5,765 km</td></tr>
                <tr><td style={{ padding: "4px 8px" }}>Airbus A200-100</td><td style={{ padding: "4px 8px", textAlign: "center" }}>12</td><td style={{ padding: "4px 8px", textAlign: "center" }}>120</td><td style={{ padding: "4px 8px", textAlign: "center" }}>697 km/h</td><td style={{ padding: "4px 8px", textAlign: "center" }}>5,627 km</td></tr>
                <tr><td style={{ padding: "4px 8px" }}>Airbus A220-300</td><td style={{ padding: "4px 8px", textAlign: "center" }}>13</td><td style={{ padding: "4px 8px", textAlign: "center" }}>149</td><td style={{ padding: "4px 8px", textAlign: "center" }}>697 km/h</td><td style={{ padding: "4px 8px", textAlign: "center" }}>6,300 km</td></tr>
                <tr><td style={{ padding: "4px 8px" }}>Airbus A350-900</td><td style={{ padding: "4px 8px", textAlign: "center" }}>1</td><td style={{ padding: "4px 8px", textAlign: "center" }}>300</td><td style={{ padding: "4px 8px", textAlign: "center" }}>728 km/h</td><td style={{ padding: "4px 8px", textAlign: "center" }}>15,000 km</td></tr>
              </tbody>
            </table>

            <h3>Excluded Routes</h3>
            <p>10 city pairs under 150 miles cannot have direct service: JFK↔LGA, ORD↔MDW, MIA↔FLL, BWI↔DCA, PHL↔BWI, JFK↔PHL, PHL↔LGA, LAX↔SAN, PHL↔DCA, SEA↔PDX.</p>

            <h3>Paris (CDG) Service</h3>
            <p>One daily round-trip: CA001 JFK→CDG (dep 18:00 EDT / 22:00 UTC, arr ~07:49 CET+1) and CA002 CDG→JFK (dep ~08:39 CET, arr ~13:08 EDT). Served by N350CA (A350-900). The evening departure allows same-day connections from US cities. Paris fees billed monthly in EUR at xe.com end-of-month exchange rate.</p>

          </div>
        </div>
      )}

    </div>
  );
}
