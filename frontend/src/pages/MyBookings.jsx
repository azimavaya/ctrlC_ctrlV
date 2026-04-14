// Displays the current user's flight bookings.
// Admins see all bookings (with "Booked By" column) and can delete any.
// Regular users see only their own bookings with no delete option.

import { useState, useEffect } from "react";
import { useAuth } from "../context/AuthContext";
import "./MyBookings.css";

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
            <div className="card booking-card" key={b.booking_id}>
              <div className="booking-card-header">
                <div className="booking-ref-block">
                  <span className="booking-ref-label">Booking Ref</span>
                  <span className="booking-ref">{b.booking_ref}</span>
                </div>
                <span className="booking-cabin cabin-eco">Economy</span>
              </div>

              <div className="booking-card-route">
                <div className="booking-route-point">
                  <span className="booking-iata">{b.origin_iata}</span>
                  <span className="booking-city">{b.origin_city}</span>
                </div>
                <div className="booking-route-arrow">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ width: 24, height: 24 }}>
                    <line x1="5" y1="12" x2="19" y2="12" />
                    <polyline points="12 5 19 12 12 19" />
                  </svg>
                </div>
                <div className="booking-route-point">
                  <span className="booking-iata">{b.dest_iata}</span>
                  <span className="booking-city">{b.dest_city}</span>
                </div>
              </div>

              <div className="booking-card-details">
                <div className="booking-detail">
                  <span className="detail-label">Flight</span>
                  <span className="detail-value">{b.flight_number}</span>
                </div>
                <div className="booking-detail">
                  <span className="detail-label">Date</span>
                  <span className="detail-value">{fmtDate(b.scheduled_departure)}</span>
                </div>
                <div className="booking-detail">
                  <span className="detail-label">Departure</span>
                  <span className="detail-value">{fmtTime(b.scheduled_departure)}</span>
                </div>
                <div className="booking-detail">
                  <span className="detail-label">Arrival</span>
                  <span className="detail-value">{fmtTime(b.scheduled_arrival)}</span>
                </div>
                <div className="booking-detail">
                  <span className="detail-label">Passenger</span>
                  <span className="detail-value">{b.passenger_name}</span>
                </div>
                <div className="booking-detail">
                  <span className="detail-label">Total Fare</span>
                  <span className="detail-value detail-fare">${parseFloat(b.total_fare_usd).toFixed(2)}</span>
                </div>
                {isAdmin && b.username && (
                  <div className="booking-detail">
                    <span className="detail-label">Booked By</span>
                    <span className="detail-value">{b.username}</span>
                  </div>
                )}
              </div>

              <div className="booking-card-footer">
                <span className="booking-date">Booked {fmtDate(b.created_at)}</span>
                {isAdmin && (
                  <button className="btn-delete-booking" onClick={() => handleDelete(b.booking_id)}>
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
