-- ------------------------------------------------------------
-- INDEXES for simulation query performance
-- ------------------------------------------------------------
CREATE INDEX idx_sim_flights_day ON simulation_flights(sim_day);
CREATE INDEX idx_sim_flights_flight ON simulation_flights(flight_id);
CREATE INDEX idx_sim_flights_status ON simulation_flights(status);
CREATE INDEX idx_passengers_day ON passengers(sim_day);
CREATE INDEX idx_pax_flights_pax ON passenger_flights(passenger_id);
CREATE INDEX idx_pax_flights_sim ON passenger_flights(sim_flight_id);
CREATE INDEX idx_airport_activity_day ON airport_activity(sim_day);
CREATE INDEX idx_airport_activity_airport ON airport_activity(airport_iata);
CREATE INDEX idx_bookings_user ON bookings(user_id);
CREATE INDEX idx_financials_day ON financials(sim_day);
CREATE INDEX idx_flights_departure ON flights(scheduled_departure);
