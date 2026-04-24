# Public flight endpoints: timetable, search, live stats, fleet.
# All queries scope to the template date range (2026-03-09) so the timetable
# appears to repeat daily. Live stats map wall-clock time onto that date.

import re
from datetime import datetime, timedelta, timezone
from flask import Blueprint, jsonify, request
from ..db import get_db
from ..config import Config

_IATA_RE   = re.compile(r'^[A-Z]{3}$')
_DATE_RE   = re.compile(r'^\d{4}-\d{2}-\d{2}$')

# Template date range — all flight queries scope to this window
_T_START = Config.TEMPLATE_RANGE_START
_T_END   = Config.TEMPLATE_RANGE_END

def _valid_iata(code: str) -> bool:
    return bool(_IATA_RE.match(code))

def _valid_date(d: str) -> bool:
    return bool(_DATE_RE.match(d))

flights_bp = Blueprint("flights", __name__)

@flights_bp.route("/", methods=["GET"])
def get_flights():
    """Return all template-day flights with aircraft and city info."""
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT f.*, a.tail_number, a.type_id,
               o.city AS origin_city, d.city AS dest_city
        FROM flights f
        JOIN aircraft a  ON f.aircraft_id = a.aircraft_id
        JOIN airports o  ON f.origin_iata  = o.iata_code
        JOIN airports d  ON f.dest_iata    = d.iata_code
        WHERE f.scheduled_departure >= %s AND f.scheduled_departure < %s
        ORDER BY f.scheduled_departure
    """, (_T_START, _T_END))
    flights = cursor.fetchall()
    cursor.close()
    return jsonify(flights)

@flights_bp.route("/search", methods=["GET"])
def search_flights():
    """
    Search for flight options from origin to destination.
    Query params: origin, destination, date
    Returns direct and connecting flight options with fares.
    """
    origin = request.args.get("origin", "").upper()
    destination = request.args.get("destination", "").upper()
    date = request.args.get("date")

    if not origin or not destination or not date:
        return jsonify({"error": "origin, destination, and date are required"}), 400
    if not _valid_iata(origin):
        return jsonify({"error": "Invalid origin airport code"}), 400
    if not _valid_iata(destination):
        return jsonify({"error": "Invalid destination airport code"}), 400
    if not _valid_date(date):
        return jsonify({"error": "date must be in YYYY-MM-DD format"}), 400
    if origin == destination:
        return jsonify({"error": "origin and destination must differ"}), 400

    db = get_db()
    cursor = db.cursor(dictionary=True)

    # Direct flights (template timetable — same every day, date param ignored)
    cursor.execute("""
        SELECT f.flight_id, f.flight_number, f.origin_iata, f.dest_iata,
               f.scheduled_departure, f.scheduled_arrival, f.capacity, f.fare_USD,
               a.tail_number, o.city AS origin_city, d.city AS dest_city,
               r.distance_miles,
               TIMESTAMPDIFF(MINUTE, f.scheduled_departure, f.scheduled_arrival) AS duration_min
        FROM flights f
        JOIN aircraft a ON f.aircraft_id = a.aircraft_id
        JOIN airports o ON f.origin_iata  = o.iata_code
        JOIN airports d ON f.dest_iata    = d.iata_code
        JOIN routes r   ON r.origin_iata = f.origin_iata AND r.dest_iata = f.dest_iata
        WHERE f.origin_iata = %s
          AND f.dest_iata   = %s
          AND f.status != 'cancelled'
          AND f.scheduled_departure >= %s AND f.scheduled_departure < %s
        ORDER BY f.scheduled_departure
    """, (origin, destination, _T_START, _T_END))
    direct = cursor.fetchall()
    cursor.close()

    # Connecting flights through hubs
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT f1.flight_id      AS leg1_flight_id,
               f1.flight_number  AS leg1_flight_number,
               f1.origin_iata    AS leg1_origin,
               f1.dest_iata      AS leg1_dest,
               f1.scheduled_departure AS leg1_departure,
               f1.scheduled_arrival   AS leg1_arrival,
               f1.fare_USD       AS leg1_fare,
               f2.flight_id      AS leg2_flight_id,
               f2.flight_number  AS leg2_flight_number,
               f2.origin_iata    AS leg2_origin,
               f2.dest_iata      AS leg2_dest,
               f2.scheduled_departure AS leg2_departure,
               f2.scheduled_arrival   AS leg2_arrival,
               f2.fare_USD       AS leg2_fare,
               hub.city          AS hub_city,
               hub.iata_code     AS hub_iata,
               TIMESTAMPDIFF(MINUTE, f1.scheduled_arrival, f2.scheduled_departure) AS layover_min,
               TIMESTAMPDIFF(MINUTE, f1.scheduled_departure, f2.scheduled_arrival) AS total_duration_min,
               r1.distance_miles AS leg1_distance,
               r2.distance_miles AS leg2_distance
        FROM flights f1
        JOIN flights f2 ON f1.dest_iata = f2.origin_iata
        JOIN airports hub ON hub.iata_code = f1.dest_iata
        JOIN routes r1 ON r1.origin_iata = f1.origin_iata AND r1.dest_iata = f1.dest_iata
        JOIN routes r2 ON r2.origin_iata = f2.origin_iata AND r2.dest_iata = f2.dest_iata
        WHERE f1.origin_iata = %s
          AND f2.dest_iata   = %s
          AND f1.status != 'cancelled'
          AND f2.status != 'cancelled'
          AND f1.scheduled_departure >= %s AND f1.scheduled_departure < %s
          AND f2.scheduled_departure >= %s AND f2.scheduled_departure < %s
          AND TIMESTAMPDIFF(MINUTE, f1.scheduled_arrival, f2.scheduled_departure) >= 30
          AND TIMESTAMPDIFF(MINUTE, f1.scheduled_arrival, f2.scheduled_departure) <= 360
        ORDER BY f1.scheduled_departure, f2.scheduled_departure
        LIMIT 30
    """, (origin, destination, _T_START, _T_END, _T_START, _T_END))
    connecting = cursor.fetchall()
    cursor.close()

    return jsonify({
        "origin": origin,
        "destination": destination,
        "date": date,
        "direct_flights": direct,
        "connecting_flights": connecting,
    })

@flights_bp.route("/departures", methods=["GET"])
def get_departures():
    """Return the master timetable flights — the same schedule repeats daily."""
    try:
        limit = min(int(request.args.get("limit", 200)), 500)
    except (ValueError, TypeError):
        limit = 200
    db = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute("""
        SELECT f.flight_number, f.origin_iata, f.dest_iata,
               f.scheduled_departure, f.scheduled_arrival, f.fare_USD, f.status, f.capacity,
               ao.city AS origin_city, ad.city AS dest_city,
               ao.timezone AS origin_tz, ad.timezone AS dest_tz,
               ac.tail_number, at2.model AS aircraft_model
        FROM flights f
        JOIN airports ao      ON f.origin_iata  = ao.iata_code
        JOIN airports ad      ON f.dest_iata    = ad.iata_code
        JOIN aircraft ac      ON f.aircraft_id  = ac.aircraft_id
        JOIN aircraft_types at2 ON ac.type_id   = at2.type_id
        WHERE f.scheduled_departure >= %s AND f.scheduled_departure < %s
        ORDER BY f.scheduled_departure
        LIMIT %s
    """, (_T_START, _T_END, limit))
    flights = cur.fetchall()
    cur.close()
    return jsonify(flights)


@flights_bp.route("/status", methods=["GET"])
def flight_status():
    """Look up flights by flight number or tail number on a given date."""
    q = request.args.get("q", "").strip().upper()
    date = request.args.get("date", "")

    if not q:
        return jsonify({"error": "q (flight number or tail number) is required"}), 400
    if not _valid_date(date):
        return jsonify({"error": "date must be YYYY-MM-DD"}), 400

    db = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute("""
        SELECT f.flight_number, f.origin_iata, f.dest_iata,
               f.scheduled_departure, f.scheduled_arrival,
               f.capacity, f.fare_USD, f.status,
               a.tail_number, at2.model AS aircraft_model,
               ao.city AS origin_city, ad.city AS dest_city,
               r.distance_miles,
               TIMESTAMPDIFF(MINUTE, f.scheduled_departure, f.scheduled_arrival) AS duration_min
        FROM flights f
        JOIN aircraft a     ON f.aircraft_id = a.aircraft_id
        JOIN aircraft_types at2 ON a.type_id = at2.type_id
        JOIN airports ao    ON f.origin_iata = ao.iata_code
        JOIN airports ad    ON f.dest_iata   = ad.iata_code
        JOIN routes r       ON r.origin_iata = f.origin_iata AND r.dest_iata = f.dest_iata
        WHERE (f.flight_number = %s OR a.tail_number = %s)
          AND f.scheduled_departure >= %s AND f.scheduled_departure < %s
        ORDER BY f.scheduled_departure
        LIMIT 20
    """, (q, q, _T_START, _T_END))
    flights = cur.fetchall()
    cur.close()
    return jsonify({"query": q, "date": date, "flights": flights})


@flights_bp.route("/live-stats", methods=["GET"])
def live_stats():
    """
    Live flight stats for the home page dashboard.
    Maps current UTC time-of-day onto the template date (2026-03-09)
    so the timetable appears to repeat every day.
    """
    now = datetime.now(timezone.utc)
    today = now.strftime("%Y-%m-%d")

    # Map current time-of-day onto the template date so the schedule loops daily.
    # Flights operate ~09:00 UTC to ~07:00 UTC next day (US morning → night),
    # so the operating day starts at 09:00 UTC, not midnight.
    OP_START = 9
    if now.hour >= OP_START:
        elapsed = timedelta(hours=now.hour - OP_START, minutes=now.minute, seconds=now.second)
    else:
        elapsed = timedelta(hours=24 - OP_START + now.hour, minutes=now.minute, seconds=now.second)
    template_now = datetime(2026, 3, 9, OP_START, 0, 0) + elapsed
    template_now_str = template_now.strftime("%Y-%m-%d %H:%M:%S")

    db = get_db()
    cur = db.cursor(dictionary=True)

    # Total flights in the template timetable
    cur.execute(
        "SELECT COUNT(*) as n FROM flights WHERE scheduled_departure >= %s AND scheduled_departure < %s",
        (_T_START, _T_END),
    )
    total_today = cur.fetchone()["n"]

    # Flights currently "in the air" (departed but not yet arrived)
    cur.execute(
        """SELECT COUNT(*) as n FROM flights
           WHERE scheduled_departure <= %s
             AND scheduled_arrival > %s
             AND scheduled_departure >= %s AND scheduled_departure < %s""",
        (template_now_str, template_now_str, _T_START, _T_END),
    )
    in_air = cur.fetchone()["n"]

    # Flights that have already arrived
    cur.execute(
        """SELECT COUNT(*) as n FROM flights
           WHERE scheduled_arrival <= %s
             AND scheduled_departure >= %s AND scheduled_departure < %s""",
        (template_now_str, _T_START, _T_END),
    )
    completed = cur.fetchone()["n"]

    # Flights still waiting to depart
    cur.execute(
        """SELECT COUNT(*) as n FROM flights
           WHERE scheduled_departure > %s
             AND scheduled_departure >= %s AND scheduled_departure < %s""",
        (template_now_str, _T_START, _T_END),
    )
    remaining = cur.fetchone()["n"]

    cur.execute(
        """SELECT f.flight_number, f.origin_iata, f.dest_iata,
                  f.scheduled_departure, f.scheduled_arrival,
                  ao.city AS origin_city, ad.city AS dest_city,
                  a.tail_number
           FROM flights f
           JOIN airports ao ON f.origin_iata = ao.iata_code
           JOIN airports ad ON f.dest_iata   = ad.iata_code
           JOIN aircraft a  ON f.aircraft_id = a.aircraft_id
           WHERE f.scheduled_departure <= %s
             AND f.scheduled_arrival > %s
             AND f.scheduled_departure >= %s AND f.scheduled_departure < %s
           ORDER BY f.scheduled_arrival
           LIMIT 20""",
        (template_now_str, template_now_str, _T_START, _T_END),
    )
    in_air_flights = cur.fetchall()

    cur.execute(
        """SELECT f.flight_number, f.origin_iata, f.dest_iata,
                  f.scheduled_departure,
                  ao.city AS origin_city, ad.city AS dest_city,
                  a.tail_number
           FROM flights f
           JOIN airports ao ON f.origin_iata = ao.iata_code
           JOIN airports ad ON f.dest_iata   = ad.iata_code
           JOIN aircraft a  ON f.aircraft_id = a.aircraft_id
           WHERE f.scheduled_departure > %s
             AND f.scheduled_departure < %s
           ORDER BY f.scheduled_departure
           LIMIT 50""",
        (template_now_str, _T_END),
    )
    next_departures = cur.fetchall()

    # Completed flights today (most recent first)
    cur.execute(
        """SELECT f.flight_number, f.origin_iata, f.dest_iata,
                  f.scheduled_departure, f.scheduled_arrival,
                  ao.city AS origin_city, ad.city AS dest_city,
                  a.tail_number
           FROM flights f
           JOIN airports ao ON f.origin_iata = ao.iata_code
           JOIN airports ad ON f.dest_iata   = ad.iata_code
           JOIN aircraft a  ON f.aircraft_id = a.aircraft_id
           WHERE f.scheduled_arrival <= %s
             AND f.scheduled_departure >= %s AND f.scheduled_departure < %s
           ORDER BY f.scheduled_arrival DESC
           LIMIT 50""",
        (template_now_str, _T_START, _T_END),
    )
    completed_flights = cur.fetchall()

    cur.close()
    return jsonify({
        "server_utc": now.isoformat(),
        "date": today,
        "total_today": total_today,
        "in_air": in_air,
        "completed": completed,
        "remaining": remaining,
        "in_air_flights": in_air_flights,
        "next_departures": next_departures,
        "completed_flights": completed_flights,
    })


@flights_bp.route("/fleet", methods=["GET"])
def get_fleet():
    """Return all aircraft with type details and total miles traveled."""
    db = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute("""
        SELECT a.aircraft_id, a.tail_number, a.current_airport, a.status, a.flight_hours,
               t.model, t.manufacturer, t.max_speed_kmh,
               t.capacity_passengers, t.fuel_capacity_L, t.fuel_burn_L_per_hr,
               t.range_km, t.monthly_lease_USD,
               ap.city AS base_city,
               COALESCE(fm.total_miles, 0) AS total_miles_traveled,
               COALESCE(fm.total_flights, 0) AS total_flights
        FROM aircraft a
        JOIN aircraft_types t ON a.type_id = t.type_id
        JOIN airports ap ON a.current_airport = ap.iata_code
        LEFT JOIN (
            SELECT f.aircraft_id,
                   CAST(SUM(r.distance_miles) AS UNSIGNED) AS total_miles,
                   COUNT(*) AS total_flights
            FROM flights f
            JOIN routes r ON r.origin_iata = f.origin_iata AND r.dest_iata = f.dest_iata
            WHERE f.scheduled_departure >= %s AND f.scheduled_departure < %s
            GROUP BY f.aircraft_id
        ) fm ON fm.aircraft_id = a.aircraft_id
        ORDER BY a.tail_number
    """, (_T_START, _T_END))
    fleet = cur.fetchall()
    cur.close()
    return jsonify(fleet)


@flights_bp.route("/<int:flight_id>", methods=["GET"])
def get_flight(flight_id):
    """Return a single flight by its primary key."""
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT f.*, a.tail_number,
               o.city AS origin_city, d.city AS dest_city
        FROM flights f
        JOIN aircraft a ON f.aircraft_id = a.aircraft_id
        JOIN airports o ON f.origin_iata  = o.iata_code
        JOIN airports d ON f.dest_iata    = d.iata_code
        WHERE f.flight_id = %s
    """, (flight_id,))
    flight = cursor.fetchone()
    cursor.close()
    if not flight:
        return jsonify({"error": "Flight not found"}), 404
    return jsonify(flight)
