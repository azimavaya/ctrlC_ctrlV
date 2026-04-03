"""
bookings.py
Flight booking endpoints for all authenticated users.
"""
import re
import random
import string
from flask import Blueprint, jsonify, request
from ..db import get_db
from ..middleware import token_required
from ..config import Config

_IATA_RE = re.compile(r'^[A-Z]{3}$')

_T_START = Config.TEMPLATE_RANGE_START
_T_END   = Config.TEMPLATE_RANGE_END

bookings_bp = Blueprint("bookings", __name__)


def _gen_booking_ref(cursor):
    """Generate a unique 6-char alphanumeric booking reference."""
    for _ in range(20):
        ref = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
        cursor.execute("SELECT 1 FROM bookings WHERE booking_ref = %s", (ref,))
        if not cursor.fetchone():
            return ref
    raise RuntimeError("Could not generate unique booking reference")


@bookings_bp.route("/search", methods=["GET"])
@token_required
def search_for_booking():
    """
    Search flights available for booking from the template timetable.
    Query params: origin, destination, date (date is for display/booking only)
    """
    origin = request.args.get("origin", "").upper()
    destination = request.args.get("destination", "").upper()
    date = request.args.get("date", "")

    if not origin or not destination or not date:
        return jsonify({"error": "origin, destination, and date are required"}), 400
    if not _IATA_RE.match(origin):
        return jsonify({"error": "Invalid origin airport code"}), 400
    if not _IATA_RE.match(destination):
        return jsonify({"error": "Invalid destination airport code"}), 400
    if origin == destination:
        return jsonify({"error": "Origin and destination must differ"}), 400

    db = get_db()
    cursor = db.cursor(dictionary=True)

    # ── Direct flights: single-hop from origin to destination ─────────
    cursor.execute("""
        SELECT f.flight_id, f.flight_number, f.origin_iata, f.dest_iata,
               f.scheduled_departure, f.scheduled_arrival, f.fare_USD,
               a.tail_number, at2.model AS aircraft_model,
               o.city AS origin_city, d.city AS dest_city,
               r.distance_miles,
               TIMESTAMPDIFF(MINUTE, f.scheduled_departure, f.scheduled_arrival) AS duration_min
        FROM flights f
        JOIN aircraft a        ON f.aircraft_id = a.aircraft_id
        JOIN aircraft_types at2 ON a.type_id = at2.type_id
        JOIN airports o        ON f.origin_iata  = o.iata_code
        JOIN airports d        ON f.dest_iata    = d.iata_code
        JOIN routes r          ON r.origin_iata = f.origin_iata AND r.dest_iata = f.dest_iata
        WHERE f.origin_iata = %s
          AND f.dest_iata   = %s
          AND f.status != 'cancelled'
          AND f.scheduled_departure >= %s AND f.scheduled_departure < %s
        ORDER BY f.scheduled_departure
    """, (origin, destination, _T_START, _T_END))
    direct = cursor.fetchall()

    for f in direct:
        f["display_fare"] = round(float(f["fare_USD"]), 2)

    cursor.close()

    # ── 1-stop connecting flights: origin -> hub -> destination ────────
    # Self-join flights where leg1's dest matches leg2's origin (the hub).
    # Layover must be 30-360 min per spec (minimum connect time to max wait).
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
        JOIN flights f2      ON f1.dest_iata = f2.origin_iata
        JOIN airports hub    ON hub.iata_code = f1.dest_iata
        JOIN routes r1       ON r1.origin_iata = f1.origin_iata AND r1.dest_iata = f1.dest_iata
        JOIN routes r2       ON r2.origin_iata = f2.origin_iata AND r2.dest_iata = f2.dest_iata
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

    for c in connecting:
        c["display_fare"] = round(float(c["leg1_fare"]) + float(c["leg2_fare"]), 2)
        c["stops"] = 1

    cursor.close()

    # ── 2-stop connecting flights: origin -> hub1 -> hub2 -> destination
    # Triple self-join through two intermediate airports.
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
               f3.flight_id      AS leg3_flight_id,
               f3.flight_number  AS leg3_flight_number,
               f3.origin_iata    AS leg3_origin,
               f3.dest_iata      AS leg3_dest,
               f3.scheduled_departure AS leg3_departure,
               f3.scheduled_arrival   AS leg3_arrival,
               f3.fare_USD       AS leg3_fare,
               h1.city AS hub1_city, h1.iata_code AS hub1_iata,
               h2.city AS hub2_city, h2.iata_code AS hub2_iata,
               TIMESTAMPDIFF(MINUTE, f1.scheduled_arrival, f2.scheduled_departure) AS layover1_min,
               TIMESTAMPDIFF(MINUTE, f2.scheduled_arrival, f3.scheduled_departure) AS layover2_min,
               TIMESTAMPDIFF(MINUTE, f1.scheduled_departure, f3.scheduled_arrival) AS total_duration_min,
               r1.distance_miles AS leg1_distance,
               r2.distance_miles AS leg2_distance,
               r3.distance_miles AS leg3_distance
        FROM flights f1
        JOIN flights f2      ON f1.dest_iata = f2.origin_iata
        JOIN flights f3      ON f2.dest_iata = f3.origin_iata
        JOIN airports h1     ON h1.iata_code = f1.dest_iata
        JOIN airports h2     ON h2.iata_code = f2.dest_iata
        JOIN routes r1       ON r1.origin_iata = f1.origin_iata AND r1.dest_iata = f1.dest_iata
        JOIN routes r2       ON r2.origin_iata = f2.origin_iata AND r2.dest_iata = f2.dest_iata
        JOIN routes r3       ON r3.origin_iata = f3.origin_iata AND r3.dest_iata = f3.dest_iata
        WHERE f1.origin_iata = %s
          AND f3.dest_iata   = %s
          AND f1.status != 'cancelled'
          AND f2.status != 'cancelled'
          AND f3.status != 'cancelled'
          AND f1.scheduled_departure >= %s AND f1.scheduled_departure < %s
          AND f2.scheduled_departure >= %s AND f2.scheduled_departure < %s
          AND f3.scheduled_departure >= %s AND f3.scheduled_departure < %s
          AND TIMESTAMPDIFF(MINUTE, f1.scheduled_arrival, f2.scheduled_departure) >= 30
          AND TIMESTAMPDIFF(MINUTE, f1.scheduled_arrival, f2.scheduled_departure) <= 360
          AND TIMESTAMPDIFF(MINUTE, f2.scheduled_arrival, f3.scheduled_departure) >= 30
          AND TIMESTAMPDIFF(MINUTE, f2.scheduled_arrival, f3.scheduled_departure) <= 360
        ORDER BY f1.scheduled_departure, f2.scheduled_departure, f3.scheduled_departure
        LIMIT 20
    """, (origin, destination, _T_START, _T_END, _T_START, _T_END, _T_START, _T_END))
    connecting_2stop = cursor.fetchall()

    for c in connecting_2stop:
        c["display_fare"] = round(float(c["leg1_fare"]) + float(c["leg2_fare"]) + float(c["leg3_fare"]), 2)
        c["stops"] = 2

    cursor.close()

    return jsonify({
        "origin": origin,
        "destination": destination,
        "date": date,
        "direct_flights": direct,
        "connecting_flights": connecting + connecting_2stop,
    })


@bookings_bp.route("", methods=["POST"])
@token_required
def create_booking():
    """Create a new flight booking."""
    data = request.get_json() or {}

    required = ["flight_id", "passenger_name",
                "passenger_email", "passenger_phone", "passenger_address"]
    missing = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

    flight_id = data["flight_id"]
    flight_id_leg2 = data.get("flight_id_leg2")
    flight_id_leg3 = data.get("flight_id_leg3")
    user_id = request.current_user["user_id"]

    db = get_db()
    cursor = db.cursor(dictionary=True)

    # Validate and sum fares for all legs
    total_fare = 0.0
    for leg_name, leg_id in [("Flight", flight_id), ("Leg 2", flight_id_leg2), ("Leg 3", flight_id_leg3)]:
        if not leg_id:
            continue
        cursor.execute("""
            SELECT flight_id, fare_USD, scheduled_departure, status
            FROM flights WHERE flight_id = %s
        """, (leg_id,))
        leg = cursor.fetchone()
        if not leg:
            cursor.close()
            return jsonify({"error": f"{leg_name} not found"}), 404
        if leg["status"] == "cancelled":
            cursor.close()
            return jsonify({"error": f"{leg_name} is cancelled"}), 400
        total_fare += float(leg["fare_USD"])

    total_fare = round(total_fare, 2)

    ref = _gen_booking_ref(cursor)

    cursor.execute("""
        INSERT INTO bookings
            (user_id, flight_id, flight_id_leg2, flight_id_leg3, cabin_class, total_fare_usd,
             passenger_name, passenger_email, passenger_phone, passenger_address, booking_ref)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        user_id, flight_id, flight_id_leg2, flight_id_leg3, "economy", total_fare,
        data["passenger_name"], data["passenger_email"],
        data["passenger_phone"], data["passenger_address"], ref
    ))
    db.commit()
    cursor.close()

    return jsonify({
        "booking_ref": ref,
        "total_fare_usd": total_fare,
        "passenger_name": data["passenger_name"],
        "passenger_email": data["passenger_email"],
    }), 201


@bookings_bp.route("", methods=["GET"])
@bookings_bp.route("/", methods=["GET"])
@token_required
def list_bookings():
    """List bookings for the current user (or all if admin)."""
    user = request.current_user
    db = get_db()
    cursor = db.cursor(dictionary=True)

    if user.get("role") == "admin":
        cursor.execute("""
            SELECT b.*, f1.flight_number, f1.origin_iata, f1.dest_iata,
                   f1.scheduled_departure, f1.scheduled_arrival,
                   o1.city AS origin_city, d1.city AS dest_city,
                   u.username
            FROM bookings b
            JOIN flights f1  ON b.flight_id = f1.flight_id
            JOIN airports o1 ON f1.origin_iata = o1.iata_code
            JOIN airports d1 ON f1.dest_iata   = d1.iata_code
            JOIN users u     ON b.user_id = u.user_id
            ORDER BY b.created_at DESC
        """)
    else:
        cursor.execute("""
            SELECT b.*, f1.flight_number, f1.origin_iata, f1.dest_iata,
                   f1.scheduled_departure, f1.scheduled_arrival,
                   o1.city AS origin_city, d1.city AS dest_city
            FROM bookings b
            JOIN flights f1  ON b.flight_id = f1.flight_id
            JOIN airports o1 ON f1.origin_iata = o1.iata_code
            JOIN airports d1 ON f1.dest_iata   = d1.iata_code
            WHERE b.user_id = %s
            ORDER BY b.created_at DESC
        """, (user["user_id"],))

    bookings = cursor.fetchall()
    cursor.close()
    return jsonify(bookings)


@bookings_bp.route("/<int:booking_id>", methods=["DELETE"])
@token_required
def delete_booking(booking_id):
    """Delete a booking. Admin only."""
    if request.current_user.get("role") != "admin":
        return jsonify({"error": "Admin access required"}), 403

    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT booking_id FROM bookings WHERE booking_id = %s", (booking_id,))
    if not cursor.fetchone():
        cursor.close()
        return jsonify({"error": "Booking not found"}), 404

    cursor.execute("DELETE FROM bookings WHERE booking_id = %s", (booking_id,))
    db.commit()
    cursor.close()
    return jsonify({"message": "Booking deleted"}), 200
