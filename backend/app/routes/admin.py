"""
admin.py — Admin-only endpoints for schedule generation, dashboard overview,
and live flight statistics.  All routes require the 'admin' role.
"""
from datetime import datetime, timezone
from flask import Blueprint, jsonify, request
from ..db import get_db
from ..middleware import role_required
from ..config import Config

_T_START = Config.TEMPLATE_RANGE_START
_T_END   = Config.TEMPLATE_RANGE_END

admin_bp = Blueprint("admin", __name__)


@admin_bp.route("/generate-schedule", methods=["POST"])
@role_required("admin")
def generate_schedule():
    """Generate (or regenerate) the master timetable."""
    from ..services.scheduler import generate_schedule as gen
    db = get_db()
    total = gen(db)
    return jsonify({"message": f"Generated {total} template flights.",
                    "flights": total})


@admin_bp.route("/overview", methods=["GET"])
@role_required("admin")
def admin_overview():
    """Return high-level stats plus full lists of users, aircraft, and airports."""
    db = get_db()
    cur = db.cursor(dictionary=True)

    # ── Aggregate counts ────────────────────────────────────────────
    cur.execute("SELECT COUNT(*) as n FROM users")
    user_count = cur.fetchone()["n"]
    cur.execute("SELECT COUNT(*) as n FROM aircraft")
    aircraft_count = cur.fetchone()["n"]
    cur.execute("SELECT COUNT(*) as n FROM airports")
    airport_count = cur.fetchone()["n"]
    cur.execute("SELECT COUNT(*) as n FROM routes")
    route_count = cur.fetchone()["n"]
    cur.execute("SELECT COUNT(*) as n FROM flights WHERE scheduled_departure >= %s AND scheduled_departure < %s",
                (_T_START, _T_END))
    flights_per_day = cur.fetchone()["n"]

    # ── Full entity lists for the admin dashboard ─────────────────────
    cur.execute("""
        SELECT u.user_id, u.username, u.email, u.is_active,
               u.failed_login_attempts, u.locked_at,
               u.created_at, u.last_login, r.role_name
        FROM users u
        JOIN roles r ON u.role_id = r.role_id
        ORDER BY u.user_id
    """)
    users = cur.fetchall()

    # Aircraft joined with type details and daily flight hours from the template schedule
    cur.execute("""
        SELECT a.aircraft_id, a.tail_number, a.current_airport,
               a.status, a.flight_hours,
               t.model, t.manufacturer, t.capacity_passengers,
               t.fuel_capacity_L, t.fuel_burn_L_per_hr,
               t.max_speed_kmh, t.range_km, t.monthly_lease_USD,
               COALESCE(dh.daily_hours, 0) AS daily_flight_hours
        FROM aircraft a
        JOIN aircraft_types t ON a.type_id = t.type_id
        LEFT JOIN (
            SELECT f.aircraft_id,
                   ROUND(SUM(TIMESTAMPDIFF(MINUTE, f.scheduled_departure, f.scheduled_arrival)) / 60.0, 1) AS daily_hours
            FROM flights f
            WHERE f.scheduled_departure >= %s AND f.scheduled_departure < %s
            GROUP BY f.aircraft_id
        ) dh ON dh.aircraft_id = a.aircraft_id
        ORDER BY a.tail_number
    """, (_T_START, _T_END))
    aircraft = cur.fetchall()

    # Fleet breakdown: count of aircraft per type
    cur.execute("""
        SELECT t.model, t.manufacturer, COUNT(a.aircraft_id) as count
        FROM aircraft_types t
        LEFT JOIN aircraft a ON t.type_id = a.type_id
        GROUP BY t.type_id
        ORDER BY count DESC
    """)
    fleet_breakdown = cur.fetchall()

    cur.execute("""
        SELECT airport_id, iata_code, name, city, state, country,
               is_hub, num_gates, timezone, metro_pop_M
        FROM airports ORDER BY iata_code
    """)
    airports = cur.fetchall()

    cur.close()
    return jsonify({
        "stats": {
            "users": user_count,
            "aircraft": aircraft_count,
            "airports": airport_count,
            "routes": route_count,
            "flights_per_day": flights_per_day,
        },
        "users": users,
        "aircraft": aircraft,
        "fleet_breakdown": fleet_breakdown,
        "airports": airports,
    })


@admin_bp.route("/live-stats", methods=["GET"])
@role_required("admin")
def live_stats():
    """Return real-time flight stats mapped onto the template timetable."""
    # Map current wall-clock time onto the template date so the timetable
    # appears to repeat daily (same approach as flights/live-stats).
    now = datetime.now(timezone.utc)
    today = now.strftime("%Y-%m-%d")
    template_now = datetime(2026, 3, 9, now.hour, now.minute, now.second)
    template_now_str = template_now.strftime("%Y-%m-%d %H:%M:%S")

    db = get_db()
    cur = db.cursor(dictionary=True)

    cur.execute("SELECT COUNT(*) as n FROM flights WHERE scheduled_departure >= %s AND scheduled_departure < %s",
                (_T_START, _T_END))
    total_today = cur.fetchone()["n"]

    cur.execute(
        """SELECT COUNT(*) as n FROM flights
           WHERE scheduled_departure <= %s AND scheduled_arrival > %s
             AND scheduled_departure >= %s AND scheduled_departure < %s""",
        (template_now_str, template_now_str, _T_START, _T_END),
    )
    in_air = cur.fetchone()["n"]

    cur.execute(
        """SELECT COUNT(*) as n FROM flights
           WHERE scheduled_arrival <= %s
             AND scheduled_departure >= %s AND scheduled_departure < %s""",
        (template_now_str, _T_START, _T_END),
    )
    completed = cur.fetchone()["n"]

    cur.execute(
        """SELECT COUNT(*) as n FROM flights
           WHERE scheduled_departure > %s
             AND scheduled_departure < %s""",
        (template_now_str, _T_END),
    )
    remaining = cur.fetchone()["n"]

    cur.execute(
        """SELECT f.flight_number, f.origin_iata, f.dest_iata,
                  f.scheduled_departure, f.status,
                  ao.city AS origin_city, ad.city AS dest_city
           FROM flights f
           JOIN airports ao ON f.origin_iata = ao.iata_code
           JOIN airports ad ON f.dest_iata   = ad.iata_code
           WHERE f.scheduled_departure > %s
             AND f.scheduled_departure < %s
           ORDER BY f.scheduled_departure
           LIMIT 5""",
        (template_now_str, _T_END),
    )
    next_departures = cur.fetchall()

    cur.execute(
        """SELECT f.flight_number, f.origin_iata, f.dest_iata,
                  f.scheduled_departure, f.scheduled_arrival, f.status,
                  ao.city AS origin_city, ad.city AS dest_city,
                  a.tail_number
           FROM flights f
           JOIN airports ao ON f.origin_iata = ao.iata_code
           JOIN airports ad ON f.dest_iata   = ad.iata_code
           JOIN aircraft a  ON f.aircraft_id = a.aircraft_id
           WHERE f.scheduled_departure <= %s AND f.scheduled_arrival > %s
             AND f.scheduled_departure >= %s AND f.scheduled_departure < %s
           ORDER BY f.scheduled_arrival
           LIMIT 20""",
        (template_now_str, template_now_str, _T_START, _T_END),
    )
    in_air_flights = cur.fetchall()

    cur.close()
    return jsonify({
        "server_utc": now.isoformat(),
        "date": today,
        "total_today": total_today,
        "in_air": in_air,
        "completed": completed,
        "remaining": remaining,
        "next_departures": next_departures,
        "in_air_flights": in_air_flights,
    })
