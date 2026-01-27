"""
Panther Cloud Air API Routes
RESTful API endpoints for the application
"""

from flask import Blueprint, jsonify, request
from app import db
from app.models import Airport, Aircraft, Flight, MaintenanceSchedule

api_bp = Blueprint('api', __name__)

@api_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'message': 'API is running'}), 200

@api_bp.route('/airports', methods=['GET'])
def get_airports():
    """Get all airports"""
    try:
        airports = Airport.query.all()
        return jsonify([airport.to_dict() for airport in airports]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/aircraft', methods=['GET'])
def get_aircraft():
    """Get all aircraft"""
    try:
        aircraft_list = Aircraft.query.all()
        return jsonify([aircraft.to_dict() for aircraft in aircraft_list]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/flights', methods=['GET'])
def get_flights():
    """Get all flights"""
    try:
        flights = Flight.query.all()
        return jsonify([flight.to_dict() for flight in flights]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/stats/summary', methods=['GET'])
def get_statistics_summary():
    """Get summary statistics"""
    try:
        stats = {
            'total_airports': Airport.query.count(),
            'total_hubs': Airport.query.filter_by(is_hub=True).count(),
            'total_aircraft': Aircraft.query.count(),
            'available_aircraft': Aircraft.query.filter_by(status='available').count(),
            'total_flights': Flight.query.count(),
            'scheduled_flights': Flight.query.filter_by(status='scheduled').count(),
        }
        return jsonify(stats), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500