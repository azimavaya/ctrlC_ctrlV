/**
 * BookFlight.jsx — 3-step booking wizard.
 *   Step 1: Search flights by origin, destination, and date. Shows direct and connecting options.
 *   Step 2: Enter passenger details (name, email, phone, address).
 *   Step 3: Confirmation page with booking reference and summary.
 */
import { useState, useEffect } from "react";
import { useAuth } from "../context/AuthContext";
import "./BookFlight.css";

const API = "/api";

export default function BookFlight() {
  const { authFetch } = useAuth();
  const [step, setStep] = useState(1);        // current wizard step (1, 2, or 3)
  const [airports, setAirports] = useState([]); // list of airports for dropdown selects

  // Step 1 — flight search state
  const [form, setForm] = useState({ origin: "", destination: "", date: "" });
  const [results, setResults] = useState(null);       // search results from API
  const [searching, setSearching] = useState(false);
  const [searchError, setSearchError] = useState(null);
  const [selectedFlight, setSelectedFlight] = useState(null); // chosen flight (direct or connecting)

  // Step 2 — passenger information state
  const [passenger, setPassenger] = useState({ name: "", email: "", phone: "", address: "" });

  // Step 3 — booking confirmation state
  const [booking, setBooking] = useState(null);        // response from POST /api/bookings
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState(null);

  // Load airport list on mount for the origin/destination dropdowns
  useEffect(() => {
    fetch(`${API}/airports/`)
      .then(r => r.json())
      .then(d => setAirports(Array.isArray(d) ? d : []))
      .catch(() => {});
  }, []);

  // Get today's date in YYYY-MM-DD for min date on input
  const today = new Date().toISOString().split("T")[0];

  /** Search for available flights (direct + connecting) via GET /api/bookings/search */
  const handleSearch = async (e) => {
    e.preventDefault();
    setSearching(true);
    setSearchError(null);
    setResults(null);
    setSelectedFlight(null);
    try {
      const params = new URLSearchParams({
        origin: form.origin,
        destination: form.destination,
        date: form.date,
      });
      const res = await authFetch(`${API}/bookings/search?${params}`);
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Search failed");
      setResults(data);
    } catch (err) {
      setSearchError(err.message);
    } finally {
      setSearching(false);
    }
  };

  /** Select a direct flight and advance to step 2 */
  const selectDirect = (flight) => {
    setSelectedFlight({
      type: "direct",
      flight_id: flight.flight_id,
      flight_id_leg2: null,
      summary: {
        flight_number: flight.flight_number,
        origin: `${flight.origin_iata} (${flight.origin_city})`,
        destination: `${flight.dest_iata} (${flight.dest_city})`,
        departure: flight.scheduled_departure,
        arrival: flight.scheduled_arrival,
        duration_min: flight.duration_min,
        fare: flight.display_fare,
        aircraft: flight.aircraft_model,
        distance: flight.distance_miles,
      },
    });
    setStep(2);
  };

  /** Select a connecting flight (1- or 2-stop) and advance to step 2 */
  const selectConnecting = (conn) => {
    const is2stop = conn.stops === 2;
    const flightNums = is2stop
      ? `${conn.leg1_flight_number} + ${conn.leg2_flight_number} + ${conn.leg3_flight_number}`
      : `${conn.leg1_flight_number} + ${conn.leg2_flight_number}`;
    const dest = is2stop ? conn.leg3_dest : conn.leg2_dest;
    const arrival = is2stop ? conn.leg3_arrival : conn.leg2_arrival;
    const distance = parseFloat(conn.leg1_distance) + parseFloat(conn.leg2_distance)
      + (is2stop ? parseFloat(conn.leg3_distance) : 0);
    const stops = is2stop
      ? `${conn.hub1_iata} (${conn.hub1_city}), ${conn.hub2_iata} (${conn.hub2_city})`
      : `${conn.hub_iata} (${conn.hub_city})`;

    setSelectedFlight({
      type: "connecting",
      flight_id: conn.leg1_flight_id,
      flight_id_leg2: conn.leg2_flight_id,
      flight_id_leg3: is2stop ? conn.leg3_flight_id : null,
      summary: {
        flight_number: flightNums,
        origin: conn.leg1_origin,
        destination: dest,
        departure: conn.leg1_departure,
        arrival: arrival,
        duration_min: conn.total_duration_min,
        hub: stops,
        layover_min: is2stop ? `${conn.layover1_min} + ${conn.layover2_min}` : conn.layover_min,
        fare: conn.display_fare,
        distance,
        stops: conn.stops,
      },
    });
    setStep(2);
  };

  /** Submit the booking to POST /api/bookings with flight + passenger data */
  const handleBook = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    setSubmitError(null);
    try {
      const res = await authFetch(`${API}/bookings`, {
        method: "POST",
        body: JSON.stringify({
          flight_id: selectedFlight.flight_id,
          flight_id_leg2: selectedFlight.flight_id_leg2,
          flight_id_leg3: selectedFlight.flight_id_leg3 || null,
          passenger_name: passenger.name,
          passenger_email: passenger.email,
          passenger_phone: passenger.phone,
          passenger_address: passenger.address,
        }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Booking failed");
      setBooking(data);
      setStep(3);
    } catch (err) {
      setSubmitError(err.message);
    } finally {
      setSubmitting(false);
    }
  };

  /** Reset all wizard state back to step 1 for a new booking */
  const resetWizard = () => {
    setStep(1);
    setResults(null);
    setSelectedFlight(null);
    setPassenger({ name: "", email: "", phone: "", address: "" });
    setBooking(null);
    setSubmitError(null);
    setSearchError(null);
  };

  // Formatting helpers for times, dates, and durations
  const fmtTime = (iso) =>
    new Date(iso).toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit" });

  const fmtDate = (iso) =>
    new Date(iso).toLocaleDateString("en-US", { weekday: "short", month: "short", day: "numeric", year: "numeric" });

  const fmtDuration = (min) => {
    const h = Math.floor(min / 60);
    const m = min % 60;
    return `${h}h ${m}m`;
  };

  return (
    <div className="book-page">
      <h2>Book a Flight</h2>

      {/* Step indicator */}
      <div className="step-indicator">
        <div className={`step-dot ${step >= 1 ? "active" : ""}`}>
          <span className="step-num">1</span>
          <span className="step-label">Select Flight</span>
        </div>
        <div className="step-line" />
        <div className={`step-dot ${step >= 2 ? "active" : ""}`}>
          <span className="step-num">2</span>
          <span className="step-label">Passenger Info</span>
        </div>
        <div className="step-line" />
        <div className={`step-dot ${step >= 3 ? "active" : ""}`}>
          <span className="step-num">3</span>
          <span className="step-label">Confirmation</span>
        </div>
      </div>

      {/* ── STEP 1: Flight Selection ── */}
      {step === 1 && (
        <>
          <div className="card">
            <form className="search-form" onSubmit={handleSearch}>
              <div className="form-row">
                <div className="form-group">
                  <label>From</label>
                  <select value={form.origin} onChange={e => setForm({ ...form, origin: e.target.value })} required>
                    <option value="">Select origin...</option>
                    {airports.map(a => (
                      <option key={a.iata_code} value={a.iata_code}>
                        {a.iata_code} — {a.city}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="form-group">
                  <label>To</label>
                  <select value={form.destination} onChange={e => setForm({ ...form, destination: e.target.value })} required>
                    <option value="">Select destination...</option>
                    {airports.filter(a => a.iata_code !== form.origin).map(a => (
                      <option key={a.iata_code} value={a.iata_code}>
                        {a.iata_code} — {a.city}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="form-group">
                  <label>Date</label>
                  <input
                    type="date"
                    value={form.date}
                    min={today}
                    max="2027-02-28"
                    onChange={e => setForm({ ...form, date: e.target.value })}
                    required
                  />
                </div>
              </div>
              <button className="btn-primary" type="submit" disabled={searching}>
                {searching ? "Searching..." : "Search Flights"}
              </button>
            </form>
          </div>

          {searchError && <div className="error-msg">{searchError}</div>}

          {results && (
            <div className="flight-results">
              <h3>
                {results.origin} → {results.destination} &nbsp;·&nbsp; {results.date}
              </h3>

              {/* Direct flights */}
              {results.direct_flights.length > 0 && (
                <>
                  <h4>Direct Flights ({results.direct_flights.length})</h4>
                  <div className="flight-cards">
                    {results.direct_flights.map(f => (
                      <div className="flight-card" key={f.flight_id}>
                        <div className="flight-card-header">
                          <span className="flight-num">{f.flight_number}</span>
                          <span className="flight-aircraft">{f.aircraft_model}</span>
                        </div>
                        <div className="flight-card-route">
                          <div className="route-point">
                            <span className="route-time">{fmtTime(f.scheduled_departure)}</span>
                            <span className="route-code">{f.origin_iata}</span>
                            <span className="route-city">{f.origin_city}</span>
                          </div>
                          <div className="route-line">
                            <span className="route-duration">{fmtDuration(f.duration_min)}</span>
                            <div className="route-dash" />
                            <span className="route-type">Direct</span>
                          </div>
                          <div className="route-point">
                            <span className="route-time">{fmtTime(f.scheduled_arrival)}</span>
                            <span className="route-code">{f.dest_iata}</span>
                            <span className="route-city">{f.dest_city}</span>
                          </div>
                        </div>
                        <div className="flight-card-footer">
                          <span className="flight-distance">{parseFloat(f.distance_miles).toFixed(0)} mi</span>
                          <span className="flight-fare">${f.display_fare.toFixed(2)}</span>
                          <button className="btn-primary btn-select" onClick={() => selectDirect(f)}>
                            Select
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                </>
              )}

              {/* 1-stop connecting flights */}
              {results.connecting_flights?.filter(c => c.stops !== 2).length > 0 && (
                <>
                  <h4 style={{ marginTop: "1.5rem" }}>1 Layover ({results.connecting_flights.filter(c => c.stops !== 2).length})</h4>
                  <div className="flight-cards">
                    {results.connecting_flights.filter(c => c.stops !== 2).map((c, i) => (
                      <div className="flight-card flight-card--connecting" key={i}>
                        <div className="flight-card-header">
                          <span className="flight-num">{c.leg1_flight_number} → {c.leg2_flight_number}</span>
                          <span className="flight-layover">1 stop: {c.layover_min} min at {c.hub_iata}</span>
                        </div>
                        <div className="flight-card-route">
                          <div className="route-point">
                            <span className="route-time">{fmtTime(c.leg1_departure)}</span>
                            <span className="route-code">{c.leg1_origin}</span>
                          </div>
                          <div className="route-line">
                            <span className="route-duration">{fmtDuration(c.total_duration_min)}</span>
                            <div className="route-dash" />
                            <span className="route-type">via {c.hub_city}</span>
                          </div>
                          <div className="route-point">
                            <span className="route-time">{fmtTime(c.leg2_arrival)}</span>
                            <span className="route-code">{c.leg2_dest}</span>
                          </div>
                        </div>
                        <div className="flight-card-footer">
                          <span className="flight-distance">
                            {(parseFloat(c.leg1_distance) + parseFloat(c.leg2_distance)).toFixed(0)} mi
                          </span>
                          <span className="flight-fare">${c.display_fare.toFixed(2)}</span>
                          <button className="btn-primary btn-select" onClick={() => selectConnecting(c)}>Select</button>
                        </div>
                      </div>
                    ))}
                  </div>
                </>
              )}

              {/* 2-stop connecting flights */}
              {results.connecting_flights?.filter(c => c.stops === 2).length > 0 && (
                <>
                  <h4 style={{ marginTop: "1.5rem" }}>2 Layovers ({results.connecting_flights.filter(c => c.stops === 2).length})</h4>
                  <div className="flight-cards">
                    {results.connecting_flights.filter(c => c.stops === 2).map((c, i) => (
                      <div className="flight-card flight-card--connecting" key={i}>
                        <div className="flight-card-header">
                          <span className="flight-num">{c.leg1_flight_number} → {c.leg2_flight_number} → {c.leg3_flight_number}</span>
                          <span className="flight-layover">2 stops: {c.layover1_min} min at {c.hub1_iata} + {c.layover2_min} min at {c.hub2_iata}</span>
                        </div>
                        <div className="flight-card-route">
                          <div className="route-point">
                            <span className="route-time">{fmtTime(c.leg1_departure)}</span>
                            <span className="route-code">{c.leg1_origin}</span>
                          </div>
                          <div className="route-line">
                            <span className="route-duration">{fmtDuration(c.total_duration_min)}</span>
                            <div className="route-dash" />
                            <span className="route-type">via {c.hub1_city}, {c.hub2_city}</span>
                          </div>
                          <div className="route-point">
                            <span className="route-time">{fmtTime(c.leg3_arrival)}</span>
                            <span className="route-code">{c.leg3_dest}</span>
                          </div>
                        </div>
                        <div className="flight-card-footer">
                          <span className="flight-distance">
                            {(parseFloat(c.leg1_distance) + parseFloat(c.leg2_distance) + parseFloat(c.leg3_distance)).toFixed(0)} mi
                          </span>
                          <span className="flight-fare">${c.display_fare.toFixed(2)}</span>
                          <button className="btn-primary btn-select" onClick={() => selectConnecting(c)}>Select</button>
                        </div>
                      </div>
                    ))}
                  </div>
                </>
              )}

              {results.direct_flights.length === 0 &&
                (!results.connecting_flights || results.connecting_flights.length === 0) && (
                <p className="no-results">No flights found for this route and date.</p>
              )}
            </div>
          )}
        </>
      )}

      {/* ── STEP 2: Passenger Details ── */}
      {step === 2 && selectedFlight && (
        <>
          <div className="card booking-summary-mini">
            <h4>Selected Flight</h4>
            <p>
              <strong>{selectedFlight.summary.flight_number}</strong>
              {" — "}
              {selectedFlight.summary.origin} → {selectedFlight.summary.destination}
            </p>
            <p>
              {fmtDate(selectedFlight.summary.departure)} &nbsp;·&nbsp;
              {fmtTime(selectedFlight.summary.departure)} – {fmtTime(selectedFlight.summary.arrival)}
              &nbsp;·&nbsp; {fmtDuration(selectedFlight.summary.duration_min)}
            </p>
            {selectedFlight.summary.hub && (
              <p>Connecting via {selectedFlight.summary.hub} ({selectedFlight.summary.layover_min} min layover{selectedFlight.summary.stops === 2 ? "s" : ""})</p>
            )}
            <p className="summary-fare">
              Fare: <strong>${selectedFlight.summary.fare.toFixed(2)}</strong>
            </p>
          </div>

          <div className="card">
            <h4>Passenger Details</h4>
            <form className="passenger-form" onSubmit={handleBook}>
              <div className="form-row">
                <div className="form-group">
                  <label>Full Name</label>
                  <input
                    type="text"
                    value={passenger.name}
                    onChange={e => setPassenger({ ...passenger, name: e.target.value })}
                    placeholder="John Doe"
                    required
                  />
                </div>
                <div className="form-group">
                  <label>Email</label>
                  <input
                    type="email"
                    value={passenger.email}
                    onChange={e => setPassenger({ ...passenger, email: e.target.value })}
                    placeholder="john@example.com"
                    required
                  />
                </div>
              </div>
              <div className="form-row">
                <div className="form-group">
                  <label>Phone</label>
                  <input
                    type="tel"
                    value={passenger.phone}
                    onChange={e => setPassenger({ ...passenger, phone: e.target.value })}
                    placeholder="(555) 123-4567"
                    required
                  />
                </div>
                <div className="form-group">
                  <label>Address</label>
                  <input
                    type="text"
                    value={passenger.address}
                    onChange={e => setPassenger({ ...passenger, address: e.target.value })}
                    placeholder="123 Main St, Atlanta, GA 30301"
                    required
                  />
                </div>
              </div>

              {submitError && <div className="error-msg">{submitError}</div>}

              <div className="form-actions">
                <button type="button" className="btn-secondary" onClick={() => setStep(1)}>
                  Back
                </button>
                <button type="submit" className="btn-primary" disabled={submitting}>
                  {submitting ? "Booking..." : "Confirm Booking"}
                </button>
              </div>
            </form>
          </div>
        </>
      )}

      {/* ── STEP 3: Confirmation ── */}
      {step === 3 && booking && (
        <div className="card confirmation-card">
          <div className="confirm-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M22 11.08V12a10 10 0 11-5.93-9.14" />
              <polyline points="22 4 12 14.01 9 11.01" />
            </svg>
          </div>
          <h3>Booking Confirmed!</h3>
          <p className="confirm-ref">Booking Reference: <strong>{booking.booking_ref}</strong></p>
          <p className="confirm-email">
            A confirmation email has been sent to <strong>{booking.passenger_email}</strong>
          </p>

          <div className="confirm-details">
            <div className="confirm-row">
              <span>Passenger</span>
              <span>{booking.passenger_name}</span>
            </div>
            <div className="confirm-row">
              <span>Flight</span>
              <span>{selectedFlight.summary.flight_number}</span>
            </div>
            <div className="confirm-row">
              <span>Route</span>
              <span>{selectedFlight.summary.origin} → {selectedFlight.summary.destination}</span>
            </div>
            <div className="confirm-row">
              <span>Date</span>
              <span>{fmtDate(selectedFlight.summary.departure)}</span>
            </div>
            <div className="confirm-row">
              <span>Time</span>
              <span>{fmtTime(selectedFlight.summary.departure)} – {fmtTime(selectedFlight.summary.arrival)}</span>
            </div>
            <div className="confirm-row total-row">
              <span>Total Fare</span>
              <span>${booking.total_fare_usd.toFixed(2)}</span>
            </div>
          </div>

          <button className="btn-primary" onClick={resetWizard} style={{ marginTop: "1.5rem" }}>
            Book Another Flight
          </button>
        </div>
      )}
    </div>
  );
}
