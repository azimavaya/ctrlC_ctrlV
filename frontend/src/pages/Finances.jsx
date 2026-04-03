/**
 * Finances.jsx — Financial reporting page (admin-only).
 * Shows simulation revenue, costs (fuel/lease/landing), and profit/loss.
 * Supports USD/EUR currency toggle (1.08 rate). Includes daily breakdown
 * table with per-day flights, passengers, and cost categories.
 */
import { useEffect, useState } from "react";
import { useAuth } from "../context/AuthContext";
import "./Finances.css";

const EUR_RATE = 1.08; // 1 EUR = 1.08 USD (xe.com Jan 31, 2026)

const CATEGORY_LABELS = {
  fuel:        "Fuel Costs",
  lease:       "Fleet Lease",
  landing_fee: "Landing & Terminal Fees",
  revenue:     "Passenger Revenue",
};

function fmtMoney(amount, currency) {
  if (amount == null) return "\u2014";
  const val = currency === "EUR" ? amount / EUR_RATE : amount;
  const sym = currency === "EUR" ? "\u20ac" : "$";
  return `${sym}${val.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

function fmtNum(n) {
  if (n == null) return "\u2014";
  return n.toLocaleString("en-US");
}

function SummaryCard({ label, value, accent, textColor }) {
  return (
    <div className="fin-summary-card" style={{ borderTopColor: accent }}>
      <span className="fin-summary-value" style={textColor ? { color: textColor } : undefined}>
        {value ?? "\u2014"}
      </span>
      <span className="fin-summary-label">{label}</span>
    </div>
  );
}

export default function Finances() {
  const { authFetch } = useAuth();
  const [report, setReport]   = useState(null);
  const [status, setStatus]   = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError]     = useState(null);
  const [currency, setCurrency] = useState("USD");

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);

    authFetch("/api/simulation/status")
      .then(r => r.ok ? r.json() : Promise.reject(r))
      .then(stat => {
        if (cancelled) return;
        setStatus(stat);
        if (!stat.has_data) return;
        return authFetch("/api/simulation/report")
          .then(r => r.ok ? r.json() : Promise.reject(r))
          .then(rep => { if (!cancelled) setReport(rep); });
      })
      .catch(() => {
        if (!cancelled) setError("Failed to load financial data");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => { cancelled = true; };
  }, []);

  if (loading) return <div className="fin-loading">Loading financial data&hellip;</div>;

  const hasData = status?.has_data && report;

  if (!hasData) {
    return (
      <div className="fin-page">
        <div className="fin-header">
          <div>
            <h2>Finances &amp; Revenue</h2>
            <span className="fin-header-sub">Panther Cloud Air</span>
          </div>
        </div>
        <div className="fin-empty">
          <p className="fin-empty-title">Begin simulation to view financial data</p>
        </div>
      </div>
    );
  }

  const { total_passengers, total_revenue_USD, total_costs_USD, profit_loss_USD, breakdown } = report;
  const days = status.days || [];

  const costCategories = (breakdown || []).filter(b => b.category !== "revenue");
  const totalCostsFromBreakdown = costCategories.reduce((s, b) => s + Math.abs(b.total), 0);
  const costPerPassenger = total_passengers > 0 ? total_costs_USD / total_passengers : 0;
  const isProfit = profit_loss_USD >= 0;

  const daily = report.daily || [];

  return (
    <div className="fin-page">
      {/* Header */}
      <div className="fin-header">
        <div>
          <h2>Finances &amp; Revenue</h2>
          <span className="fin-header-sub">Panther Cloud Air &mdash; Financial Overview</span>
        </div>
        <div className="fin-currency-pick">
          <label htmlFor="fin-currency">Currency</label>
          <select
            id="fin-currency"
            value={currency}
            onChange={e => setCurrency(e.target.value)}
          >
            <option value="USD">USD ($)</option>
            <option value="EUR">EUR (&euro;)</option>
          </select>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="fin-summary-row">
        <SummaryCard
          label="Total Revenue"
          value={fmtMoney(total_revenue_USD, currency)}
          accent="#10b981"
          textColor="#065f46"
        />
        <SummaryCard
          label="Total Costs"
          value={fmtMoney(total_costs_USD, currency)}
          accent="#ef4444"
          textColor="#991b1b"
        />
        <SummaryCard
          label="Profit / Loss"
          value={fmtMoney(profit_loss_USD, currency)}
          accent="#3b82f6"
          textColor={isProfit ? "#065f46" : "#991b1b"}
        />
        <SummaryCard
          label="Total Passengers"
          value={fmtNum(total_passengers)}
          accent="#8b5cf6"
        />
        <SummaryCard
          label="Cost Per Passenger"
          value={fmtMoney(costPerPassenger, currency)}
          accent="#f59e0b"
          textColor="#92400e"
        />
      </div>

      {/* Cost Breakdown */}
      <div className="fin-section">
        <h3>Cost Breakdown</h3>
        <div className="fin-table-wrap">
          <table className="fin-table">
            <thead>
              <tr>
                <th>Category</th>
                <th className="fin-align-right">Amount</th>
                <th className="fin-align-right">% of Total Costs</th>
              </tr>
            </thead>
            <tbody>
              {(breakdown || []).map(b => {
                const label = CATEGORY_LABELS[b.category] || b.category;
                const abs = Math.abs(b.total);
                const pct = totalCostsFromBreakdown > 0
                  ? ((abs / totalCostsFromBreakdown) * 100).toFixed(1)
                  : "0.0";
                const isRevRow = b.category === "revenue";
                return (
                  <tr key={b.category} className={isRevRow ? "fin-row-revenue" : ""}>
                    <td>{label}</td>
                    <td className="fin-align-right">{fmtMoney(Math.abs(b.total), currency)}</td>
                    <td className="fin-align-right">
                      {isRevRow ? <span className="fin-muted">&mdash;</span> : `${pct}%`}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Daily Financial Performance */}
      {daily.length > 0 && (
        <div className="fin-section">
          <h3>Daily Financial Performance</h3>
          <div className="fin-table-wrap fin-table-scroll">
            <table className="fin-table">
              <thead>
                <tr>
                  <th>Day</th>
                  <th>Date</th>
                  <th className="fin-align-right">Flights</th>
                  <th className="fin-align-right">Passengers</th>
                  <th className="fin-align-right">Revenue</th>
                  <th className="fin-align-right">Fuel</th>
                  <th className="fin-align-right">Lease</th>
                  <th className="fin-align-right">Landing</th>
                  <th className="fin-align-right">Daily P/L</th>
                </tr>
              </thead>
              <tbody>
                {daily.map(d => (
                  <tr key={d.sim_day}>
                    <td>{d.sim_day}</td>
                    <td>{d.sim_date}</td>
                    <td className="fin-align-right">{fmtNum(d.flights_operated)}</td>
                    <td className="fin-align-right">{fmtNum(d.passengers)}</td>
                    <td className="fin-align-right fin-text-green">{fmtMoney(d.revenue, currency)}</td>
                    <td className="fin-align-right fin-text-red">{fmtMoney(d.fuel_cost, currency)}</td>
                    <td className="fin-align-right fin-text-red">{fmtMoney(d.lease_cost, currency)}</td>
                    <td className="fin-align-right fin-text-red">{fmtMoney(d.landing_cost, currency)}</td>
                    <td className={`fin-align-right ${d.daily_profit >= 0 ? "fin-text-green" : "fin-text-red"}`}>
                      {fmtMoney(d.daily_profit, currency)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* DST / Timezone Info Panel */}
      <div className="fin-dst-panel">
        <h3>Daylight Saving Time &amp; Timezone Info</h3>
        <div className="fin-dst-grid">
          <div className="fin-dst-item">
            <span className="fin-dst-region">United States</span>
            <span className="fin-dst-detail">Second Sunday in March &ndash; First Sunday in November</span>
            <span className="fin-dst-dates">Mar 8, 2026 &ndash; Nov 1, 2026</span>
          </div>
          <div className="fin-dst-item">
            <span className="fin-dst-region">France (EU)</span>
            <span className="fin-dst-detail">Last Sunday in March &ndash; Last Sunday in October</span>
            <span className="fin-dst-dates">Mar 29, 2026 &ndash; Oct 25, 2026</span>
          </div>
        </div>
        <div className="fin-dst-notes">
          <p>Arizona and Hawaii do not observe DST.</p>
          <p>Simulation runs March 9&ndash;22, 2026 &mdash; US DST is active (began March 8).</p>
        </div>
      </div>
    </div>
  );
}
