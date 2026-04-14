# Passenger detail endpoint for the simulation.
# Returns a passenger's full itinerary (all flight legs) from simulation data.

from flask import Blueprint, jsonify, request
from ..db import get_db
from ..middleware import token_required

passengers_bp = Blueprint("passengers", __name__)

@passengers_bp.route("/<int:passenger_id>", methods=["GET"])
@token_required
def get_passenger(passenger_id):
    """Get full itinerary for a passenger."""
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM passengers WHERE passenger_id = %s", (passenger_id,))
    passenger = cursor.fetchone()
    if not passenger:
        cursor.close()
        return jsonify({"error": "Passenger not found"}), 404

    cursor.execute("""
        SELECT pf.*, sf.sim_day, f.flight_number,
               o.city AS leg_origin_city, d.city AS leg_dest_city
        FROM passenger_flights pf
        JOIN simulation_flights sf ON pf.sim_flight_id = sf.sim_flight_id
        JOIN flights f             ON sf.flight_id      = f.flight_id
        JOIN airports o            ON pf.leg_origin     = o.iata_code
        JOIN airports d            ON pf.leg_dest       = d.iata_code
        WHERE pf.passenger_id = %s
        ORDER BY pf.sched_departure
    """, (passenger_id,))
    itinerary = cursor.fetchall()
    cursor.close()

    return jsonify({"passenger": passenger, "itinerary": itinerary})
