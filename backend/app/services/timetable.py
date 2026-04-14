# Part 1 core flight logic.
# Physics/math functions needed to build the daily timetable and compute fares:
#   - Great-circle distance (haversine)
#   - Initial compass bearing
#   - Wind time factor (+/- 4.5% east/west per project spec)
#   - Cruising altitude selection by distance
#   - Full flight time (taxi, takeoff, climb, cruise, descent, landing)
#   - Taxi time formulas (hub vs non-hub)
#   - Fare calculation at 30% load factor break-even

import math
from ..config import Config

# Great Circle Distance

def great_circle_distance_miles(lat1, lon1, lat2, lon2):
    """Return distance in miles between two GPS coordinates using the haversine formula."""
    R_miles = 3958.8
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin(dlon/2)**2
    return R_miles * 2 * math.asin(math.sqrt(a))

def great_circle_distance_km(lat1, lon1, lat2, lon2):
    return great_circle_distance_miles(lat1, lon1, lat2, lon2) * 1.60934

# Bearing / Heading

def bearing_degrees(lat1, lon1, lat2, lon2):
    """
    Calculate initial compass bearing (degrees) from point 1 to point 2.
    0 = North, 90 = East, 180 = South, 270 = West.
    Formula: https://www.igismap.com/formula-to-find-bearing-or-heading-angle-between-two-points-latitude-longitude/
    """
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    x = math.sin(lon2 - lon1) * math.cos(lat2)
    y = math.cos(lat1)*math.sin(lat2) - math.sin(lat1)*math.cos(lat2)*math.cos(lon2-lon1)
    bearing = math.degrees(math.atan2(x, y))
    return (bearing + 360) % 360

# Wind Effect

def wind_time_factor(heading_deg):
    """
    Returns a multiplier for flight time based on heading.
    Due East (90°)  → factor = 1 - WIND_EFFECT_PCT  (faster)
    Due West (270°) → factor = 1 + WIND_EFFECT_PCT  (slower)
    North/South     → factor = 1.0
    Uses cosine interpolation for intermediate headings.
    """
    # Convert heading to radians measured from East axis (math convention)
    # Due East = 90 deg heading → angle_from_east = 0
    angle_from_east = math.radians(heading_deg - 90)
    effect = Config.WIND_EFFECT_PCT * math.cos(angle_from_east)
    # Positive cos → heading toward East → reduce time
    return 1.0 - effect

# Cruising Altitude

def cruising_altitude_ft(distance_miles, is_international=False):
    """Select cruising altitude based on route distance (longer routes fly higher)."""
    if is_international:
        return 38000
    if distance_miles >= 1500:
        return 35000
    if distance_miles >= 350:
        return 30000
    if distance_miles >= 200:
        return 25000
    return 20000

# Flight Time Calculation

KNOTS_TO_KMH = 1.852

def compute_flight_time_minutes(distance_km, max_speed_kmh, heading_deg, is_international=False, distance_miles=None):
    """
    Full flight time including:
      - Takeoff roll (1 min)
      - Climb phase (250 kt → 280 kt → cruise speed)
      - Cruise
      - Descent phase (250 kt → 200 kt)
      - Landing roll (2 min)
    Wind correction applied to entire cruise segment.
    Returns total minutes (float).
    """
    if distance_miles is None:
        distance_miles = distance_km / 1.60934

    # Aircraft operate at 80% of their max speed per spec
    cruise_speed_kmh = max_speed_kmh * Config.AIRCRAFT_OPERATE_SPEED_PCT
    alt_ft = cruising_altitude_ft(distance_miles, is_international)

    # --- Climb (4 phases) ---
    # Phase 1: Takeoff roll — 0 → 150 kt on runway (1 min, ~2.78 km)
    takeoff_dist_km = (150 * KNOTS_TO_KMH) * (1/60)

    # Phase 2: Climb at 250 kt to 10,000 ft
    # Angle 6 degrees → horizontal dist per ft gained = 1/tan(6°)
    climb_angle_rad = math.radians(6)
    ft_per_km_horizontal = math.tan(climb_angle_rad) * 3280.84  # ft gained per km horizontal
    dist_to_10k_km = 10000 / ft_per_km_horizontal
    speed_250_kmh  = 250 * KNOTS_TO_KMH
    time_to_10k_min = (dist_to_10k_km / speed_250_kmh) * 60

    # Phase 3: 280 kt from 10,000 ft to cruising altitude
    dist_10k_to_cruise_km = (alt_ft - 10000) / ft_per_km_horizontal
    speed_280_kmh         = 280 * KNOTS_TO_KMH
    time_10k_to_cruise_min = (dist_10k_to_cruise_km / speed_280_kmh) * 60

    # Phase 4: Accelerate from 280 kt to cruise speed at 25 kt/min
    accel_time_min = (cruise_speed_kmh/KNOTS_TO_KMH - 280) / 25
    accel_dist_km  = ((speed_280_kmh + cruise_speed_kmh) / 2) * (accel_time_min / 60)

    climb_dist_km = takeoff_dist_km + dist_to_10k_km + dist_10k_to_cruise_km + accel_dist_km
    climb_time_min = 1 + time_to_10k_min + time_10k_to_cruise_min + accel_time_min

    # --- Descent (4 phases) ---
    # Per spec: aircraft decelerate at 35 knots/minute during descent
    # Descent rate: 1,000 ft per 3 nautical miles = 1,000 ft per 5.556 km
    NM_TO_KM = 1.852
    descent_rate_km_per_ft = (3 * NM_TO_KM) / 1000

    # Phase 1: Decelerate from cruise speed to 250 kt at 35 kt/min
    cruise_speed_kt = cruise_speed_kmh / KNOTS_TO_KMH
    decel_to_250_min = max(0, (cruise_speed_kt - 250) / 35)
    avg_decel_speed_kmh = ((cruise_speed_kmh + 250 * KNOTS_TO_KMH) / 2)
    decel_to_250_dist_km = avg_decel_speed_kmh * (decel_to_250_min / 60)

    # Phase 2: Descend at 250 kt from cruising altitude to 10,000 ft
    dist_cruise_to_10k_km = (alt_ft - 10000) * descent_rate_km_per_ft
    time_cruise_to_10k_min = (dist_cruise_to_10k_km / (250 * KNOTS_TO_KMH)) * 60

    # Phase 3: Decelerate from 250 kt to 200 kt at 35 kt/min
    decel_250_to_200_min = (250 - 200) / 35
    avg_speed_250_200_kmh = ((250 + 200) / 2) * KNOTS_TO_KMH
    decel_250_to_200_dist_km = avg_speed_250_200_kmh * (decel_250_to_200_min / 60)

    # Phase 4: Descend at 200 kt from 10,000 ft to ground
    speed_200_kmh = 200 * KNOTS_TO_KMH
    dist_10k_to_ground_km = 10000 * descent_rate_km_per_ft
    time_10k_to_ground_min = (dist_10k_to_ground_km / speed_200_kmh) * 60

    descent_dist_km = (decel_to_250_dist_km + dist_cruise_to_10k_km
                       + decel_250_to_200_dist_km + dist_10k_to_ground_km)
    descent_time_min = (decel_to_250_min + time_cruise_to_10k_min
                        + decel_250_to_200_min + time_10k_to_ground_min + 2)  # +2 min landing roll

    # --- Cruise (remaining distance at 80% max speed) ---
    cruise_dist_km = max(0, distance_km - climb_dist_km - descent_dist_km)
    cruise_time_min = (cruise_dist_km / cruise_speed_kmh) * 60

    # Wind correction: ±4.5% applied to total airborne time per project spec
    wf = wind_time_factor(heading_deg)
    total_flight_min = (climb_time_min + cruise_time_min + descent_time_min) * wf

    return total_flight_min

# Taxi Time

def taxi_time_minutes(metro_pop_M, is_hub):
    """Estimate taxi time based on airport size (hub vs spoke, metro population)."""
    if is_hub:
        base = 15
        extra = max(0, math.floor((metro_pop_M - 9) / 2))
        return min(20, base + extra)
    else:
        return min(13, math.floor(metro_pop_M * 7.5))

# Fare Calculation

def compute_fare(distance_miles, aircraft_capacity, fuel_burn_L_per_hr, flight_time_min,
                 monthly_lease_USD, is_international=False, flights_per_day=None,
                 origin_is_foreign=False):
    """
    Fare assumes 30% load factor covering:
      - Fuel cost
      - Monthly lease (amortized per flight based on actual daily flights)
      - Landing/terminal fees
    At exactly 30% load, the airline breaks even.

    origin_is_foreign: True if the aircraft refuels at a non-US airport (e.g., CDG).
    JFK→CDG uses US fuel pricing (refuels at JFK); CDG→JFK uses EUR pricing (refuels at CDG).
    """
    # Compute total fuel consumed during the flight
    flight_hrs = flight_time_min / 60
    fuel_L = fuel_burn_L_per_hr * flight_hrs

    import os
    eur_to_usd = float(os.getenv("EUR_USD_RATE", "1.08"))

    # Fuel pricing depends on WHERE the aircraft refuels (origin airport)
    if origin_is_foreign:
        # Departing from a non-US airport (CDG) — fuel at Paris EUR rate
        fuel_cost_usd = Config.FUEL_PRICE_PARIS_EUR_PER_L * fuel_L * eur_to_usd
    else:
        # Departing from a US airport — fuel at US gallon rate
        fuel_cost_usd = fuel_L * 0.264172 * Config.FUEL_PRICE_USD_PER_GALLON  # L→gal

    # Landing fees: international routes pay US fee at one end + EUR fee at the other
    if is_international:
        landing_usd = Config.LANDING_FEE_US_USD + Config.LANDING_FEE_PARIS_EUR * eur_to_usd
    else:
        landing_usd = 2 * Config.LANDING_FEE_US_USD

    # Amortize the monthly lease evenly across the aircraft's daily flights
    daily_lease = monthly_lease_USD / 30
    fpd = flights_per_day if flights_per_day and flights_per_day > 0 else 2
    lease_per_flight = daily_lease / fpd

    # Total cost per flight, then divide by expected paying passengers (30% load)
    total_cost = fuel_cost_usd + landing_usd + lease_per_flight
    paying_passengers = aircraft_capacity * Config.FARE_LOAD_FACTOR
    fare = total_cost / max(1, paying_passengers)
    return round(fare, 2)
