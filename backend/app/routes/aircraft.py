"""
aircraft.py — REST endpoints for querying the PCA fleet.

Provides list/detail views for individual aircraft and aircraft types.
"""
from flask import Blueprint, jsonify
from ..db import get_db

aircraft_bp = Blueprint("aircraft", __name__)


@aircraft_bp.route("/", methods=["GET"])
def get_all_aircraft():
    """Return every aircraft joined with its type details."""
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT a.*, t.model, t.manufacturer, t.capacity_passengers,
               t.max_speed_kmh, t.monthly_lease_USD
        FROM aircraft a
        JOIN aircraft_types t ON a.type_id = t.type_id
        ORDER BY a.tail_number
    """)
    fleet = cursor.fetchall()
    cursor.close()
    return jsonify(fleet)

@aircraft_bp.route("/<string:tail>", methods=["GET"])
def get_aircraft(tail):
    """Return a single aircraft by tail number (e.g. N350CA)."""
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT a.*, t.model, t.manufacturer, t.capacity_passengers,
               t.max_speed_kmh, t.monthly_lease_USD
        FROM aircraft a
        JOIN aircraft_types t ON a.type_id = t.type_id
        WHERE a.tail_number = %s
    """, (tail.upper(),))
    ac = cursor.fetchone()
    cursor.close()
    if not ac:
        return jsonify({"error": "Aircraft not found"}), 404
    return jsonify(ac)

@aircraft_bp.route("/types", methods=["GET"])
def get_types():
    """Return all aircraft type definitions (capacity, speed, range, etc.)."""
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM aircraft_types")
    types = cursor.fetchall()
    cursor.close()
    return jsonify(types)
