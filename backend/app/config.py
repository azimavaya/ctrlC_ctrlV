# Configuration for the PCA Flask app. All values come from env vars


import os

class Config:
    # JWT / Authentication
    JWT_SECRET       = os.getenv("JWT_SECRET",      "pca-jwt-secret-change-in-prod")
    JWT_EXPIRY_HOURS = int(os.getenv("JWT_EXPIRY_HOURS", 8))

    # Database connection
    DB_HOST     = os.getenv("DB_HOST",     "localhost")
    DB_PORT     = int(os.getenv("DB_PORT", 3306))
    DB_NAME     = os.getenv("DB_NAME",     "pca_db")
    DB_USER     = os.getenv("DB_USER",     "pca_user")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "pca_password")
    FLASK_ENV   = os.getenv("FLASK_ENV",   "development")
    DEBUG       = FLASK_ENV == "development"

    # Admin seed credentials, override via env var in production
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "pca")

    # CORS: restrict to frontend origin in production
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000")

    # PCA Business Constants (from project spec)

    # Fuel pricing
    FUEL_PRICE_USD_PER_GALLON    = 6.19
    FUEL_PRICE_PARIS_EUR_PER_L   = 1.97
    LANDING_FEE_PARIS_EUR        = 2100
    LANDING_FEE_US_USD           = 2000

    # Aircraft operating parameters
    AIRCRAFT_OPERATE_SPEED_PCT   = 0.80
    MIN_FLIGHT_DISTANCE_MILES    = 150
    GATE_TURNOVER_MIN            = 40
    GATE_TURNOVER_WITH_FUEL_MIN  = 50
    TRANSIT_MIN_MINUTES          = 30
    # Demand and market parameters
    WIND_EFFECT_PCT              = 0.045   # 4.5% E/W wind adjustment
    DAILY_AIR_TRAVEL_PCT         = 0.005   # 0.5% of population travels by air/day
    INITIAL_MARKET_SHARE_PCT     = 0.02    # 2% market share initially
    FARE_LOAD_FACTOR             = 0.30    # 30% load assumed for fare calculation
    # Maintenance and fleet parameters
    MAINTENANCE_AFTER_HOURS      = 200
    MAINTENANCE_DURATION_DAYS    = 1.5
    MAX_MAINTENANCE_SIMULTANEOUS = 3

    # Template date range — the scheduler generates flights for this window.
    # All flight queries should scope to this range to handle stale DB volumes.
    TEMPLATE_DATE_STR     = "2026-03-09"
    TEMPLATE_RANGE_START  = "2026-03-09 00:00:00"
    TEMPLATE_RANGE_END    = "2026-03-11 00:00:00"  # 2-day window covers all UTC offsets
