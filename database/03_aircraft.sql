-- ------------------------------------------------------------
-- AIRCRAFT
-- Fleet: 15x 737-600, 15x 737-800, 12x A200-100, 13x A220-300
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS aircraft_types (
    type_id             INT AUTO_INCREMENT PRIMARY KEY,
    model               VARCHAR(10)    NOT NULL UNIQUE,
    manufacturer        VARCHAR(20)    NOT NULL,
    max_speed_kmh       INT            NOT NULL,
    capacity_passengers INT            NOT NULL,
    fuel_capacity_L     INT            NOT NULL,
    fuel_burn_L_per_hr  INT            NOT NULL,
    cruising_altitude_ft INT           NOT NULL,
    range_km            INT            NOT NULL,
    monthly_lease_USD   DECIMAL(10,2)  NOT NULL
);

CREATE TABLE IF NOT EXISTS aircraft (
    aircraft_id     INT AUTO_INCREMENT PRIMARY KEY,
    tail_number     VARCHAR(6)   NOT NULL UNIQUE,
    type_id         INT          NOT NULL,
    current_airport VARCHAR(3)   REFERENCES airports(iata_code),
    status          ENUM('active','maintenance','grounded') NOT NULL DEFAULT 'active',
    flight_hours    DECIMAL(8,2) NOT NULL DEFAULT 0.00 COMMENT 'Hours since last maintenance',
    FOREIGN KEY (type_id) REFERENCES aircraft_types(type_id)
);

-- ------------------------------------------------------------
-- SEED: Aircraft Types
-- ------------------------------------------------------------
INSERT INTO aircraft_types (model, manufacturer, max_speed_kmh, capacity_passengers, fuel_capacity_L, fuel_burn_L_per_hr, cruising_altitude_ft, range_km, monthly_lease_USD) VALUES
('737-600', 'Boeing',  876, 119, 26020, 2800, 41000,  5648,  245000.00),
('737-800', 'Boeing',  876, 162, 26020, 2900, 41000,  5765,  270000.00),
('A200-100','Airbus',  871, 120, 21805, 2600, 41000,  5627,  192000.00),
('A220-300','Airbus',  871, 149, 21805, 2700, 41000,  6300,  228000.00),
('A350-900','Airbus',  910, 300,158000, 7200, 43000, 15000, 1200000.00);

-- ------------------------------------------------------------
-- SEED: Aircraft Fleet
-- 15x Boeing 737-600  (type_id=1)  tails N601CA–N615CA
-- 15x Boeing 737-800  (type_id=2)  tails N801CA–N815CA
-- 12x Airbus A200-100 (type_id=3)  tails N221CA–N232CA
-- 13x Airbus A220-300 (type_id=4)  tails N301CA–N313CA
-- Starting positions spread across hubs and key airports
-- N350CA (A350-900) is dedicated to JFK-CDG international service (evening departure)
-- ------------------------------------------------------------
INSERT INTO aircraft (tail_number, type_id, current_airport, status, flight_hours) VALUES
  ('N601CA',1,'ATL','active',0.00),
  ('N602CA',1,'ATL','active',0.00),
  ('N603CA',1,'ATL','active',0.00),
  ('N604CA',1,'ATL','active',0.00),
  ('N605CA',1,'ORD','active',0.00),
  ('N606CA',1,'ORD','active',0.00),
  ('N607CA',1,'ORD','active',0.00),
  ('N608CA',1,'ORD','active',0.00),
  ('N609CA',1,'DFW','active',0.00),
  ('N610CA',1,'DFW','active',0.00),
  ('N611CA',1,'DFW','active',0.00),
  ('N612CA',1,'DFW','active',0.00),
  ('N613CA',1,'LAX','active',0.00),
  ('N614CA',1,'LAX','active',0.00),
  ('N615CA',1,'LAX','active',0.00),
  ('N801CA',2,'ATL','active',0.00),
  ('N802CA',2,'ATL','active',0.00),
  ('N803CA',2,'ATL','active',0.00),
  ('N804CA',2,'ORD','active',0.00),
  ('N805CA',2,'ORD','active',0.00),
  ('N806CA',2,'ORD','active',0.00),
  ('N807CA',2,'DFW','active',0.00),
  ('N808CA',2,'DFW','active',0.00),
  ('N809CA',2,'DFW','active',0.00),
  ('N810CA',2,'LAX','active',0.00),
  ('N811CA',2,'LAX','active',0.00),
  ('N812CA',2,'LAX','active',0.00),
  ('N813CA',2,'JFK','active',0.00),
  ('N814CA',2,'BOS','active',0.00),
  ('N815CA',2,'MIA','active',0.00),
  ('N221CA',3,'ATL','active',0.00),
  ('N222CA',3,'ORD','active',0.00),
  ('N223CA',3,'DFW','active',0.00),
  ('N224CA',3,'LAX','active',0.00),
  ('N225CA',3,'JFK','active',0.00),
  ('N226CA',3,'SFO','active',0.00),
  ('N227CA',3,'SEA','active',0.00),
  ('N228CA',3,'PHX','active',0.00),
  ('N229CA',3,'DEN','active',0.00),
  ('N230CA',3,'MSP','active',0.00),
  ('N231CA',3,'DTW','active',0.00),
  ('N232CA',3,'CLT','active',0.00),
  ('N301CA',4,'JFK','active',0.00),
  ('N302CA',4,'ATL','active',0.00),
  ('N303CA',4,'ORD','active',0.00),
  ('N304CA',4,'DFW','active',0.00),
  ('N305CA',4,'LAX','active',0.00),
  ('N306CA',4,'BOS','active',0.00),
  ('N307CA',4,'MIA','active',0.00),
  ('N308CA',4,'IAH','active',0.00),
  ('N309CA',4,'SEA','active',0.00),
  ('N310CA',4,'SFO','active',0.00),
  ('N311CA',4,'DEN','active',0.00),
  ('N312CA',4,'PHX','active',0.00),
  ('N313CA',4,'MSP','active',0.00);

-- ------------------------------------------------------------
-- SEED: A350-900 Fleet (announced Mar 2, 2026)
-- 1x Airbus A350-900  (type_id=5)
-- N350CA — JFK (JFK↔CDG international service)
-- ------------------------------------------------------------
INSERT INTO aircraft (tail_number, type_id, current_airport, status, flight_hours) VALUES
  ('N350CA',5,'JFK','active',0.00);
