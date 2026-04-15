-- ------------------------------------------------------------
-- SIMULATION DATA (Part 2)
-- Actual vs scheduled times across 14-day simulation
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS simulation_flights (
    sim_flight_id       INT AUTO_INCREMENT PRIMARY KEY,
    flight_id           INT          NOT NULL,
    sim_day             INT          NOT NULL COMMENT '1-14',
    sim_date            DATE         NOT NULL,
    actual_departure    DATETIME,
    actual_arrival      DATETIME,
    passengers_boarded  INT          NOT NULL DEFAULT 0,
    gate_used           VARCHAR(5),
    delay_reason        VARCHAR(100),
    fuel_used_L         DECIMAL(10,2),
    status              ENUM('scheduled','departed','arrived','cancelled','delayed') NOT NULL DEFAULT 'scheduled',
    FOREIGN KEY (flight_id) REFERENCES flights(flight_id)
);

-- ------------------------------------------------------------
-- PASSENGERS
-- Part 2: Passenger records per simulation
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS passengers (
    passenger_id        INT AUTO_INCREMENT PRIMARY KEY,
    source_iata         VARCHAR(3)   NOT NULL,
    dest_iata           VARCHAR(3)   NOT NULL,
    sim_day             INT          NOT NULL,
    preferred_dept_time TIME,
    FOREIGN KEY (source_iata) REFERENCES airports(iata_code),
    FOREIGN KEY (dest_iata)   REFERENCES airports(iata_code)
);

CREATE TABLE IF NOT EXISTS passenger_flights (
    id                  INT AUTO_INCREMENT PRIMARY KEY,
    passenger_id        INT          NOT NULL,
    sim_flight_id       INT          NOT NULL,
    leg_origin          VARCHAR(3)   NOT NULL,
    leg_dest            VARCHAR(3)   NOT NULL,
    sched_departure     DATETIME,
    actual_departure    DATETIME,
    sched_arrival       DATETIME,
    actual_arrival      DATETIME,
    FOREIGN KEY (passenger_id)  REFERENCES passengers(passenger_id),
    FOREIGN KEY (sim_flight_id) REFERENCES simulation_flights(sim_flight_id)
);

-- ------------------------------------------------------------
-- AIRPORT ACTIVITY LOG (per simulation day)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS airport_activity (
    activity_id         INT AUTO_INCREMENT PRIMARY KEY,
    airport_iata        VARCHAR(3)   NOT NULL,
    sim_day             INT          NOT NULL,
    sim_flight_id       INT          NOT NULL,
    event_type          ENUM('arrival','departure') NOT NULL,
    event_time          DATETIME     NOT NULL,
    gate_used           VARCHAR(5),
    passengers_count    INT          NOT NULL DEFAULT 0,
    aircraft_tail       VARCHAR(6),
    FOREIGN KEY (airport_iata)  REFERENCES airports(iata_code),
    FOREIGN KEY (sim_flight_id) REFERENCES simulation_flights(sim_flight_id)
);

-- ------------------------------------------------------------
-- COSTS & REVENUE (per simulation day)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS financials (
    financial_id        INT AUTO_INCREMENT PRIMARY KEY,
    sim_day             INT          NOT NULL,
    sim_date            DATE         NOT NULL,
    category            ENUM('fuel','lease','landing_fee','terminal_fee','revenue') NOT NULL,
    amount_USD          DECIMAL(12,2) NOT NULL,
    notes               VARCHAR(100)
);
