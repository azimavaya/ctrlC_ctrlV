// Displays the current user's flight bookings.
// Admins see all bookings (with "Booked By" column) and can delete any.
// Regular users see only their own bookings with no delete option.

import { useState, useEffect } from "react";
import { useAuth } from "../context/AuthContext";

const API = "/api";

export default function MyBookings() {
  const { authFetch, user } = useAuth();
  const [bookings, setBookings] = useState([]); // array of booking objects from API
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Fetch bookings on mount — admins get all bookings, users get their own
  useEffect(() => {
    authFetch(`${API}/bookings/`)
      .then(r => r.json())
      .then(d => { setBookings(Array.isArray(d) ? d : []); setLoading(false); })
      .catch(() => { setError("Failed to load bookings"); setLoading(false); });
  }, []);

  const fmtDate = (iso) =>
    new Date(iso).toLocaleDateString("en-US", { weekday: "short", month: "short", day: "numeric", year: "numeric" });

  const fmtTime = (iso) =>
    new Date(iso).toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit" });

  const isAdmin = user?.role === "admin";

  /** Delete a booking (admin only) — prompts for confirmation first */
  const handleDelete = async (bookingId) => {
    if (!window.confirm("Are you sure you want to delete this booking?")) return;
    try {
      const res = await authFetch(`${API}/bookings/${bookingId}`, { method: "DELETE" });
      if (!res.ok) { const d = await res.json(); throw new Error(d.error); }
      setBookings(prev => prev.filter(b => b.booking_id !== bookingId));
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <div className="bookings-page">
      <h2>My Bookings</h2>

      {loading && <p className="bookings-loading">Loading bookings...</p>}
      {error && <div className="error-msg">{error}</div>}

      {!loading && bookings.length === 0 && (
        <div className="card bookings-empty">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"
            style={{ width: 48, height: 48, margin: "0 auto 1rem", display: "block", color: "var(--pca-gray)", opacity: 0.5 }}>
            <rect x="2" y="3" width="20" height="18" rx="2" />
            <line x1="2" y1="8" x2="22" y2="8" />
          </svg>
          <p style={{ color: "var(--pca-gray)", textAlign: "center" }}>
            No bookings yet. Head over to <a href="/book">Book Flight</a> to make your first reservation.
          </p>
        </div>
      )}

      {!loading && bookings.length > 0 && (
        <div className="bookings-list">
          {bookings.map(b => (
            <div className="boarding-pass" key={b.booking_id}>
              <div className="bp-main">
                <div className="bp-airline">
                  <span className="bp-airline-icon">✈</span>
                  <span className="bp-airline-name">Panther Cloud Air</span>
                </div>
                <div className="bp-route">
                  <div className="bp-point">
                    <span className="bp-iata">{b.origin_iata}</span>
                    <span className="bp-city">{b.origin_city}</span>
                    <span className="bp-time">{fmtTime(b.scheduled_departure)}</span>
                  </div>
                  <div className="bp-flight-line">
                    <div className="bp-line-track" />
                    <svg className="bp-plane-icon" viewBox="0 0 24 24" fill="currentColor" width="20" height="20">
                      <path d="M21 16v-2l-8-5V3.5A1.5 1.5 0 0011.5 2 1.5 1.5 0 0010 3.5V9l-8 5v2l8-2.5V19l-2 1.5V22l3.5-1 3.5 1v-1.5L13 19v-5.5l8 2.5z"/>
                    </svg>
                    <span className="bp-flight-num">{b.flight_number}</span>
                  </div>
                  <div className="bp-point">
                    <span className="bp-iata">{b.dest_iata}</span>
                    <span className="bp-city">{b.dest_city}</span>
                    <span className="bp-time">{fmtTime(b.scheduled_arrival)}</span>
                  </div>
                </div>
                <div className="bp-details">
                  <div className="bp-detail">
                    <span className="bp-detail-label">Passenger</span>
                    <span className="bp-detail-value">{b.passenger_name}</span>
                  </div>
                  <div className="bp-detail">
                    <span className="bp-detail-label">Date</span>
                    <span className="bp-detail-value">{fmtDate(b.scheduled_departure)}</span>
                  </div>
                  <div className="bp-detail">
                    <span className="bp-detail-label">Class</span>
                    <span className="bp-detail-value">Economy</span>
                  </div>
                  <div className="bp-detail">
                    <span className="bp-detail-label">Fare</span>
                    <span className="bp-detail-value bp-fare">${parseFloat(b.total_fare_usd).toFixed(2)}</span>
                  </div>
                  {isAdmin && b.username && (
                    <div className="bp-detail">
                      <span className="bp-detail-label">Booked By</span>
                      <span className="bp-detail-value">{b.username}</span>
                    </div>
                  )}
                </div>
              </div>
              <div className="bp-tear" />
              <div className="bp-stub">
                <span className="bp-stub-ref-label">Booking Ref</span>
                <span className="bp-stub-ref">{b.booking_ref}</span>
                <div className="bp-barcode">
                  {Array.from({ length: 20 }, (_, i) => (
                    <div key={i} className="bp-bar" style={{ height: `${14 + Math.random() * 16}px`, width: Math.random() > 0.5 ? "3px" : "2px" }} />
                  ))}
                </div>
                <span className="bp-stub-route">{b.origin_iata} → {b.dest_iata}</span>
                {isAdmin && (
                  <button className="btn-delete-booking" onClick={() => handleDelete(b.booking_id)} style={{ marginTop: "0.5rem" }}>
                    Delete
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
