"""
airports.py — REST endpoints for querying PCA airports.

Provides list/detail views for all 31 airports and a hub-only filter.
"""
from flask import Blueprint, jsonify
from ..db import get_db

airports_bp = Blueprint("airports", __name__)


@airports_bp.route("/", methods=["GET"])
def get_airports():
    """Return all airports sorted by city name."""
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM airports ORDER BY city")
    airports = cursor.fetchall()
    cursor.close()
    return jsonify(airports)

@airports_bp.route("/<string:iata>", methods=["GET"])
def get_airport(iata):
    """Return a single airport by IATA code (e.g. ATL)."""
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM airports WHERE iata_code = %s", (iata.upper(),))
    airport = cursor.fetchone()
    cursor.close()
    if not airport:
        return jsonify({"error": "Airport not found"}), 404
    return jsonify(airport)

@airports_bp.route("/hubs", methods=["GET"])
def get_hubs():
    """Return only the 4 hub airports (ATL, ORD, DFW, LAX)."""
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM airports WHERE is_hub = TRUE")
    hubs = cursor.fetchall()
    cursor.close()
    return jsonify(hubs)
