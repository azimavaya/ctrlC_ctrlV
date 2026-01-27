"""
Panther Cloud Air Database Models
SQLAlchemy ORM models for the application
"""

from app import db
from datetime import datetime

class Airport(db.Model):
    """Airport model"""
    __tablename__ = 'airports'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(3), unique=True, nullable=False)
    name = db.Column(db.String(255), nullable=False)
    city = db.Column(db.String(100), nullable=False)
    state = db.Column(db.String(50))
    country = db.Column(db.String(50), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    metro_population = db.Column(db.Integer, nullable=False)
    is_hub = db.Column(db.Boolean, default=False)
    num_gates = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'city': self.city,
            'state': self.state,
            'country': self.country,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'metro_population': self.metro_population,
            'is_hub': self.is_hub,
            'num_gates': self.num_gates
        }


class Aircraft(db.Model):
    """Aircraft model"""
    __tablename__ = 'aircraft'
    
    id = db.Column(db.Integer, primary_key=True)
    tail_number = db.Column(db.String(10), unique=True, nullable=False)
    aircraft_type = db.Column(db.String(50), nullable=False)
    max_speed_kmh = db.Column(db.Integer, nullable=False)
    cruise_speed_kmh = db.Column(db.Integer, nullable=False)
    passenger_capacity = db.Column(db.Integer, nullable=False)
    fuel_capacity_gallons = db.Column(db.Float, nullable=False)
    monthly_lease_cost = db.Column(db.Float, nullable=False)
    flight_hours = db.Column(db.Float, default=0.0)
    maintenance_required = db.Column(db.Boolean, default=False)
    current_airport_id = db.Column(db.Integer, db.ForeignKey('airports.id'))
    status = db.Column(db.String(20), default='available')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    current_airport = db.relationship('Airport', backref='aircraft_at_airport')
    
    def to_dict(self):
        return {
            'id': self.id,
            'tail_number': self.tail_number,
            'aircraft_type': self.aircraft_type,
            'max_speed_kmh': self.max_speed_kmh,
            'cruise_speed_kmh': self.cruise_speed_kmh,
            'passenger_capacity': self.passenger_capacity,
            'fuel_capacity_gallons': self.fuel_capacity_gallons,
            'monthly_lease_cost': self.monthly_lease_cost,
            'flight_hours': self.flight_hours,
            'maintenance_required': self.maintenance_required,
            'current_airport_id': self.current_airport_id,
            'status': self.status
        }


class Flight(db.Model):
    """Flight schedule model"""
    __tablename__ = 'flights'
    
    id = db.Column(db.Integer, primary_key=True)
    flight_number = db.Column(db.String(10), nullable=False)
    aircraft_id = db.Column(db.Integer, db.ForeignKey('aircraft.id'), nullable=False)
    origin_airport_id = db.Column(db.Integer, db.ForeignKey('airports.id'), nullable=False)
    destination_airport_id = db.Column(db.Integer, db.ForeignKey('airports.id'), nullable=False)
    departure_time = db.Column(db.DateTime, nullable=False)
    arrival_time = db.Column(db.DateTime, nullable=False)
    distance_km = db.Column(db.Float, nullable=False)
    flight_duration_minutes = db.Column(db.Integer, nullable=False)
    passenger_capacity = db.Column(db.Integer, nullable=False)
    passengers_booked = db.Column(db.Integer, default=0)
    ticket_price = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='scheduled')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    aircraft = db.relationship('Aircraft', backref='flights')
    origin_airport = db.relationship('Airport', foreign_keys=[origin_airport_id], backref='departures')
    destination_airport = db.relationship('Airport', foreign_keys=[destination_airport_id], backref='arrivals')
    
    def to_dict(self):
        return {
            'id': self.id,
            'flight_number': self.flight_number,
            'aircraft_id': self.aircraft_id,
            'origin_airport_id': self.origin_airport_id,
            'destination_airport_id': self.destination_airport_id,
            'departure_time': self.departure_time.isoformat() if self.departure_time else None,
            'arrival_time': self.arrival_time.isoformat() if self.arrival_time else None,
            'distance_km': self.distance_km,
            'flight_duration_minutes': self.flight_duration_minutes,
            'passenger_capacity': self.passenger_capacity,
            'passengers_booked': self.passengers_booked,
            'ticket_price': self.ticket_price,
            'status': self.status
        }


class MaintenanceSchedule(db.Model):
    """Maintenance schedule model"""
    __tablename__ = 'maintenance_schedules'
    
    id = db.Column(db.Integer, primary_key=True)
    aircraft_id = db.Column(db.Integer, db.ForeignKey('aircraft.id'), nullable=False)
    hub_airport_id = db.Column(db.Integer, db.ForeignKey('airports.id'), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), default='scheduled')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    aircraft = db.relationship('Aircraft', backref='maintenance_history')
    hub_airport = db.relationship('Airport', backref='maintenance_schedules')
    
    def to_dict(self):
        return {
            'id': self.id,
            'aircraft_id': self.aircraft_id,
            'hub_airport_id': self.hub_airport_id,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'status': self.status
        }