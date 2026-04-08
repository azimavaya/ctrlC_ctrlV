import { useState } from "react";
import { useAuth } from "../context/AuthContext";
import "./HelpButton.css";

export default function HelpButton() {
  const [open, setOpen] = useState(false);
  const { user } = useAuth();
  const isAdmin = user?.role === "admin";

  return (
    <>
      {open && <div className="help-backdrop" onClick={() => setOpen(false)} />}
      <div className="help-container">
        {open && (
          <div className="help-panel">
            <div className="help-panel-header">
              <h3>Help</h3>
              <button className="help-close" onClick={() => setOpen(false)} aria-label="Close help">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="18" height="18">
                  <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
                </svg>
              </button>
            </div>
            <div className="help-panel-body">
              <section className="help-section">
                <h4>Getting Started</h4>
                <ul>
                  <li><strong>Search Flights</strong> — Use the search page to find direct and connecting flights between airports.</li>
                  <li><strong>Book a Flight</strong> — Select a flight from search results and complete the booking form.</li>
                  <li><strong>My Bookings</strong> — View all your upcoming and past reservations.</li>
                  <li><strong>Timetable</strong> — Browse the full daily flight schedule.</li>
                </ul>
              </section>
              {isAdmin && (
                <section className="help-section">
                  <h4>Admin Tools</h4>
                  <ul>
                    <li><strong>Admin Dashboard</strong> — Manage users, view system stats, and regenerate the flight schedule.</li>
                    <li><strong>Simulation</strong> — Run the 14-day flight simulation with daily challenges (weather, delays, cancellations).</li>
                    <li><strong>Finances</strong> — View the financial report including revenue, operating costs, and profit/loss.</li>
                  </ul>
                </section>
              )}
              <section className="help-section">
                <h4>Tips</h4>
                <ul>
                  <li>Use the sidebar to navigate between pages.</li>
                  <li>Use the sidebar to collapse or expand the navigation.</li>
                  <li>Connecting flights are shown when no direct route exists.</li>
                </ul>
              </section>
            </div>
          </div>
        )}
        <button
          className={`help-fab ${open ? "help-fab--active" : ""}`}
          onClick={() => setOpen(v => !v)}
          aria-label="Toggle help"
        >
          ?
        </button>
      </div>
    </>
  );
}
