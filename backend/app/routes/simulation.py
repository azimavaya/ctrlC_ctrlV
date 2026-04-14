# 14-day simulation endpoints (admin-only).
# Provides run/reset/progress, per-day flight data, the final financial
# report, aircraft history by tail number, and EUR/USD exchange rate info.

import re
from flask import Blueprint, jsonify, request
from ..db import get_db
from ..middleware import token_required, role_required

simulation_bp = Blueprint("simulation", __name__)

_TAIL_RE = re.compile(r'^[A-Z0-9]{4,10}$')


@simulation_bp.route("/run", methods=["POST"])
@role_required("admin")
def run_all():
    """Execute the full 14-day simulation at once. Admin only."""
    from ..services.sim_runner import run_all as do_run_all
    db = get_db()
    result = do_run_all(db)
    return jsonify(result)


@simulation_bp.route("/reset", methods=["POST"])
@role_required("admin")
def reset():
    """Clear all simulation data so a fresh run can start."""
    from ..services.sim_runner import reset_simulation
    db = get_db()
    reset_simulation(db)
    return jsonify({"ok": True})


@simulation_bp.route("/progress", methods=["POST"])
@role_required("admin")
def progress_day():
    """
    Run a single simulation day.
    Body: { "day": 1 }
    The spec's fixed daily challenge is applied automatically.
    """
    from ..services.sim_runner import run_day
    body = request.get_json(silent=True) or {}
    day = body.get("day")
    if not day or not isinstance(day, int) or not (1 <= day <= 14):
        return jsonify({"error": "day must be an integer 1-14"}), 400

    db = get_db()
    try:
        result = run_day(db, day)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    return jsonify(result)


@simulation_bp.route("/progress-status", methods=["GET"])
@token_required
def progress_status():
    """Which days have been simulated so far."""
    from ..services.sim_runner import get_progress
    db = get_db()
    completed = get_progress(db)
    return jsonify({"completed_days": completed, "total_days": 14})


@simulation_bp.route("/status", methods=["GET"])
@token_required
def get_status():
    """Overall simulation status and day summary."""
    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("SELECT COUNT(*) AS n FROM simulation_flights")
    count = cursor.fetchone()["n"]
    if count == 0:
        cursor.close()
        return jsonify({"has_data": False, "days": []})

    cursor.execute("""
        SELECT sf.sim_day, sf.sim_date,
               COUNT(*) AS total_flights,
               SUM(CASE WHEN sf.status='arrived'   THEN 1 ELSE 0 END) AS completed,
               SUM(CASE WHEN sf.status='cancelled' THEN 1 ELSE 0 END) AS cancelled,
               SUM(CASE WHEN sf.status='delayed'   THEN 1 ELSE 0 END) AS `delayed`,
               (SELECT COUNT(*) FROM passengers p WHERE p.sim_day = sf.sim_day) AS total_passengers
        FROM simulation_flights sf
        GROUP BY sf.sim_day, sf.sim_date
        ORDER BY sf.sim_day
    """)
    days = cursor.fetchall()
    cursor.close()
    return jsonify({"has_data": True, "days": days})


@simulation_bp.route("/day/<int:day>", methods=["GET"])
@role_required("admin")
def get_day(day):
    """All flight activity for a given simulation day (1-14)."""
    if not (1 <= day <= 14):
        return jsonify({"error": "Day must be between 1 and 14"}), 400

    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT sf.*, f.flight_number, f.origin_iata, f.dest_iata,
               a.tail_number, o.city AS origin_city, d.city AS dest_city
        FROM simulation_flights sf
        JOIN flights  f ON sf.flight_id   = f.flight_id
        JOIN aircraft a ON f.aircraft_id  = a.aircraft_id
        JOIN airports o ON f.origin_iata  = o.iata_code
        JOIN airports d ON f.dest_iata    = d.iata_code
        WHERE sf.sim_day = %s
        ORDER BY sf.actual_departure
    """, (day,))
    flights = cursor.fetchall()
    cursor.close()
    return jsonify({"day": day, "flights": flights})


@simulation_bp.route("/report", methods=["GET"])
@role_required("admin")
def get_report():
    """Final simulation report: passengers, costs, revenue, profit/loss."""
    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("SELECT COUNT(*) AS n FROM simulation_flights")
    if cursor.fetchone()["n"] == 0:
        cursor.close()
        return jsonify({"error": "Simulation has not been run yet"}), 404

    cursor.execute("SELECT COUNT(*) AS total_passengers FROM passengers")
    pax = cursor.fetchone()

    cursor.execute("""
        SELECT category, SUM(amount_USD) AS total
        FROM financials
        GROUP BY category
    """)
    financials = cursor.fetchall()

    revenue = sum(float(f["total"]) for f in financials if f["category"] == "revenue")
    costs   = sum(float(f["total"]) for f in financials if f["category"] != "revenue")

    # --- daily breakdown ---
    cursor.execute("""
        SELECT
            f.sim_day,
            f.sim_date,
            COALESCE(SUM(CASE WHEN f.category = 'revenue'  THEN f.amount_USD ELSE 0 END), 0) AS revenue,
            COALESCE(SUM(CASE WHEN f.category = 'fuel'     THEN f.amount_USD ELSE 0 END), 0) AS fuel_cost,
            COALESCE(SUM(CASE WHEN f.category = 'lease'    THEN f.amount_USD ELSE 0 END), 0) AS lease_cost,
            COALESCE(SUM(CASE WHEN f.category = 'landing_fee'  THEN f.amount_USD ELSE 0 END), 0) AS landing_cost
        FROM financials f
        GROUP BY f.sim_day, f.sim_date
        ORDER BY f.sim_day
    """)
    daily_financials = cursor.fetchall()

    cursor.execute("""
        SELECT
            sf.sim_day,
            COUNT(*)                  AS flights_operated,
            (SELECT COUNT(*) FROM passengers p WHERE p.sim_day = sf.sim_day) AS passengers
        FROM simulation_flights sf
        GROUP BY sf.sim_day
        ORDER BY sf.sim_day
    """)
    daily_flights = {row["sim_day"]: row for row in cursor.fetchall()}
    cursor.close()

    daily = []
    for df in daily_financials:
        day_num = df["sim_day"]
        fl = daily_flights.get(day_num, {})
        rev  = float(df["revenue"])
        fuel = float(df["fuel_cost"])
        lease = float(df["lease_cost"])
        landing = float(df["landing_cost"])
        daily.append({
            "sim_day":         day_num,
            "sim_date":        df["sim_date"],
            "flights_operated": int(fl.get("flights_operated", 0)),
            "passengers":      int(fl.get("passengers", 0) or 0),
            "revenue":         round(rev, 2),
            "fuel_cost":       round(fuel, 2),
            "lease_cost":      round(lease, 2),
            "landing_cost":    round(landing, 2),
            "daily_profit":    round(rev - fuel - lease - landing, 2),
        })

    return jsonify({
        "total_passengers": int(pax["total_passengers"] or 0),
        "total_revenue_USD": round(revenue, 2),
        "total_costs_USD":   round(costs, 2),
        "profit_loss_USD":   round(revenue - costs, 2),
        "breakdown": financials,
        "daily": daily
    })


@simulation_bp.route("/aircraft/<string:tail>", methods=["GET"])
@role_required("admin")
def get_aircraft_history(tail):
    """Query simulation history by aircraft tail number."""
    tail = tail.upper().strip()
    if not _TAIL_RE.match(tail):
        return jsonify({"error": "Invalid tail number format"}), 400

    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT sf.sim_day, sf.sim_date, f.flight_number,
               f.origin_iata, f.dest_iata,
               sf.actual_departure, sf.actual_arrival,
               sf.passengers_boarded, sf.status, sf.delay_reason,
               o.city AS origin_city, d.city AS dest_city
        FROM simulation_flights sf
        JOIN flights  f ON sf.flight_id  = f.flight_id
        JOIN aircraft a ON f.aircraft_id = a.aircraft_id
        JOIN airports o ON f.origin_iata = o.iata_code
        JOIN airports d ON f.dest_iata   = d.iata_code
        WHERE a.tail_number = %s
        ORDER BY sf.sim_day, sf.actual_departure
    """, (tail,))
    history = cursor.fetchall()
    cursor.close()

    if not history:
        return jsonify({"error": "No simulation data for that tail number"}), 404

    # Calculate on-time performance for this aircraft
    on_time = sum(1 for h in history if h["status"] == "arrived")
    operated = [h for h in history if h["status"] in ("arrived", "delayed")]
    pct_on_time = (on_time / len(operated) * 100) if operated else 0

    # Load maintenance-aware flight hour totals from the sim_runner
    from ..services.sim_runner import _load_refs
    refs = _load_refs(db)

    # Resolve tail number to aircraft_id for the maintenance lookup
    ac_id = None
    for aid, ac in refs["aircraft_map"].items():
        if ac["tail_number"] == tail:
            ac_id = aid
            break

    total_hours = 0.0
    base_hours = 0.0
    maint_status = None
    if ac_id is not None:
        ac = refs["aircraft_map"][ac_id]
        base_hours = float(ac.get("flight_hours", 0) or 0)
        # sim_hours includes base_hours and accounts for maintenance resets
        total_hours = refs["sim_hours"].get(ac_id, base_hours)

        # Determine maintenance status: in maintenance, approaching, or clear
        if ac_id in refs.get("maint_entered", {}):
            maint_status = "In maintenance"
        elif total_hours >= 180:
            maint_status = "Approaching maintenance"

    return jsonify({
        "tail_number": tail,
        "flights": history,
        "total_flights": len(history),
        "pct_on_time": round(pct_on_time, 1),
        "total_hours": round(total_hours, 1),
        "maintenance_threshold": 200,
        "maintenance_status": maint_status,
    })


@simulation_bp.route("/exchange-info", methods=["GET"])
@token_required
def exchange_info():
    """EUR/USD exchange rate and DST information for the simulation period."""
    return jsonify({
        "eur_usd_rate": 1.08,
        "rate_date": "2026-01-31",
        "source": "xe.com",
        "dst_info": {
            "us": {
                "start": "2026-03-08",
                "end": "2026-11-01",
                "note": "Second Sunday in March to First Sunday in November. Arizona and Hawaii do not observe DST."
            },
            "france": {
                "start": "2026-03-29",
                "end": "2026-10-25",
                "note": "Last Sunday in March to Last Sunday in October"
            },
            "simulation_note": "Simulation runs March 9-22, 2026. US DST is active (began March 8)."
        }
    })
