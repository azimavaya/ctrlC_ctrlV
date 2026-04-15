-- ------------------------------------------------------------
-- FLIGHTS (Timetable)
-- Part 1: Schedule stored here
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS flights (
    flight_id           INT AUTO_INCREMENT PRIMARY KEY,
    flight_number       VARCHAR(6)   NOT NULL,
    aircraft_id         INT          NOT NULL,
    origin_iata         VARCHAR(3)   NOT NULL,
    dest_iata           VARCHAR(3)   NOT NULL,
    scheduled_departure DATETIME     NOT NULL,
    scheduled_arrival   DATETIME     NOT NULL,
    capacity            INT          NOT NULL,
    fare_USD            DECIMAL(8,2) NOT NULL DEFAULT 0.00,
    status              ENUM('scheduled','boarding','departed','arrived','cancelled','delayed') NOT NULL DEFAULT 'scheduled',
    FOREIGN KEY (aircraft_id)   REFERENCES aircraft(aircraft_id),
    FOREIGN KEY (origin_iata)   REFERENCES airports(iata_code),
    FOREIGN KEY (dest_iata)     REFERENCES airports(iata_code)
);

-- Flight legs (for multi-stop flights)
CREATE TABLE IF NOT EXISTS flight_legs (
    leg_id              INT AUTO_INCREMENT PRIMARY KEY,
    flight_id           INT          NOT NULL,
    leg_number          INT          NOT NULL,
    origin_iata         VARCHAR(3)   NOT NULL,
    dest_iata           VARCHAR(3)   NOT NULL,
    scheduled_departure DATETIME     NOT NULL,
    scheduled_arrival   DATETIME     NOT NULL,
    layover_minutes     INT          NOT NULL DEFAULT 0,
    FOREIGN KEY (flight_id)   REFERENCES flights(flight_id),
    FOREIGN KEY (origin_iata) REFERENCES airports(iata_code),
    FOREIGN KEY (dest_iata)   REFERENCES airports(iata_code)
);

-- ============================================================
-- Flights table is populated by the scheduler (backend auto-seed).
-- No seed flights here — the scheduler generates the proper
-- template timetable with correct fares, times, and assignments.
-- ============================================================
