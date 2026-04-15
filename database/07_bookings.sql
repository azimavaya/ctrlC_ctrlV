-- ------------------------------------------------------------
-- BOOKINGS (user-facing flight reservations)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS bookings (
    booking_id        INT AUTO_INCREMENT PRIMARY KEY,
    user_id           INT            NOT NULL,
    flight_id         INT            NOT NULL,
    flight_id_leg2    INT            NULL,
    flight_id_leg3    INT            NULL,
    cabin_class       VARCHAR(10)    NOT NULL DEFAULT 'economy',
    total_fare_usd    DECIMAL(10,2)  NOT NULL,
    passenger_name    VARCHAR(100)   NOT NULL,
    passenger_email   VARCHAR(254)   NOT NULL,
    passenger_phone   VARCHAR(20)    NOT NULL,
    passenger_address TEXT           NOT NULL,
    booking_ref       VARCHAR(6)     NOT NULL UNIQUE,
    created_at        DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id)        REFERENCES users(user_id),
    FOREIGN KEY (flight_id)      REFERENCES flights(flight_id),
    FOREIGN KEY (flight_id_leg2) REFERENCES flights(flight_id),
    FOREIGN KEY (flight_id_leg3) REFERENCES flights(flight_id)
);
