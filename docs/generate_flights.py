#!/usr/bin/env python3
# Generates SQL INSERTs for the Day 1 flight schedule (2026-03-09, Monday).
# US DST is active (sprang forward March 8, 2026).
#
# Rules applied:
#   - Operating speed = 80% of max airspeed
#   - Wind factor     = -0.045 * sin(heading_radians)  [eastbound faster, westbound slower]
#   - Flight time     = (dist_km / op_speed) * (1 + wind_factor)  [airborne only]
#   - Total block time= taxi_out + airborne + taxi_in
  - Turnaround      = 40 min at hub, 50 min at non-hub
  - Fare            = max($75, $0.12 * distance_miles)
  - N350CA          = JFK→CDG only (evening departure, return next morning)
  - N305CA          = LAX→HNL round-trip (return arrives early March 10 UTC)

All datetimes stored in UTC.
"""

import math
from datetime import datetime, timedelta

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
OP_PCT = 0.80
WIND_K = 0.045        # ±4.5% max wind adjustment
R_KM   = 6371.0
KM2MI  = 0.621371

MIN_FARE      = 75.00
FARE_PER_MILE = 0.12

HUBS = {'ATL', 'LAX', 'ORD', 'DFW'}

# UTC offsets on 2026-03-09 (US DST active; France still on CET until Mar 29)
UTC_OFFSET = {
    'ATL': -4, 'BNA': -5, 'BOS': -4, 'BWI': -4, 'CDG': +1,
    'CLT': -4, 'DCA': -4, 'DEN': -6, 'DFW': -5, 'DTW': -4,
    'FLL': -4, 'HNL':-10, 'IAH': -5, 'JFK': -4, 'LAS': -7,
    'LAX': -7, 'LGA': -4, 'MCI': -5, 'MCO': -4, 'MDW': -5,
    'MIA': -4, 'MSP': -5, 'ORD': -5, 'PDX': -7, 'PHL': -4,
    'PHX': -7, 'SAN': -7, 'SEA': -7, 'SFO': -7, 'SLC': -6,
    'STL': -5,
}

# Taxi times (minutes): hub formula or non-hub min(13, pop×0.0000075)
TAXI = {
    # Hubs: min(20, 15 + max(0, floor((pop_M - 9.0) / 2.0)))
    # Population <= 9M → base 15 min (extra clamped to 0)
    'ATL': 15,   # 6.14M ≤ 9M → 15 + max(0, floor(-1.43)) = 15 + 0 = 15
    'LAX': 17,   # 13.2M > 9M → 15 + max(0, floor(2.1))   = 15 + 2 = 17
    'ORD': 15,   # 9.46M ≤ 9M → 15 + max(0, floor(0.23))  = 15 + 0 = 15
    'DFW': 15,   # 7.76M ≤ 9M → 15 + max(0, floor(-0.62)) = 15 + 0 = 15
    # Non-hubs below 13-min cap
    'SLC':  9,   # 1.26M × 0.0000075 = 9.45
    'HNL':  7,   # 0.98M × 0.0000075 = 7.35
    # All other non-hubs cap at 13 min
}

# Airport coordinates (lat, lon)
COORDS = {
    'ATL': (33.6407,  -84.4277),
    'LAX': (33.9425, -118.4081),
    'ORD': (41.9742,  -87.9073),
    'DFW': (32.8998,  -97.0403),
    'DEN': (39.8561, -104.6737),
    'JFK': (40.6413,  -73.7781),
    'SFO': (37.6213, -122.3790),
    'SEA': (47.4502, -122.3088),
    'LAS': (36.0840, -115.1537),
    'MCO': (28.4294,  -81.3090),
    'MIA': (25.7959,  -80.2870),
    'CLT': (35.2140,  -80.9431),
    'PHX': (33.4373, -112.0078),
    'IAH': (29.9902,  -95.3368),
    'BOS': (42.3656,  -71.0096),
    'MSP': (44.8848,  -93.2223),
    'FLL': (26.0726,  -80.1527),
    'DTW': (42.2162,  -83.3554),
    'PHL': (39.8719,  -75.2411),
    'LGA': (40.7769,  -73.8740),
    'MDW': (41.7868,  -87.7522),
    'BWI': (39.1754,  -76.6683),
    'SLC': (40.7884, -111.9778),
    'DCA': (38.8512,  -77.0402),
    'SAN': (32.7338, -117.1933),
    'MCI': (39.2976,  -94.7139),
    'STL': (38.7487,  -90.3700),
    'HNL': (21.3187, -157.9224),
    'PDX': (45.5898, -122.5951),
    'BNA': (36.1263,  -86.6774),
    'CDG': (49.0097,    2.5479),
}

# Aircraft type specs: (capacity, max_speed_kmh)
TYPE_SPECS = {
    1: (119, 876),   # 737-600
    2: (162, 876),   # 737-800
    3: (120, 871),   # A200-100
    4: (149, 871),   # A220-300
}

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------
def haversine_km(a, b):
    lat1, lon1 = COORDS[a]
    lat2, lon2 = COORDS[b]
    la1, lo1, la2, lo2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = la2 - la1
    dlon = lo2 - lo1
    h = math.sin(dlat/2)**2 + math.cos(la1)*math.cos(la2)*math.sin(dlon/2)**2
    return 2 * R_KM * math.asin(math.sqrt(h))


def init_bearing(a, b):
    lat1, lon1 = COORDS[a]
    lat2, lon2 = COORDS[b]
    la1, lo1, la2, lo2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlon = lo2 - lo1
    x = math.sin(dlon) * math.cos(la2)
    y = math.cos(la1)*math.sin(la2) - math.sin(la1)*math.cos(la2)*math.cos(dlon)
    return (math.degrees(math.atan2(x, y)) + 360) % 360


def block_minutes(origin, dest, type_id):
    """Total block time in minutes: taxi_out + airborne + taxi_in."""
    _, max_spd = TYPE_SPECS[type_id]
    op_spd = max_spd * OP_PCT
    km  = haversine_km(origin, dest)
    hdg = init_bearing(origin, dest)
    wf  = -WIND_K * math.sin(math.radians(hdg))
    air_hr = (km / op_spd) * (1 + wf)
    t_out = TAXI.get(origin, 13)
    t_in  = TAXI.get(dest,   13)
    return round(air_hr * 60) + t_out + t_in


def fare_usd(origin, dest):
    mi = haversine_km(origin, dest) * KM2MI
    return round(max(MIN_FARE, mi * FARE_PER_MILE), 2)


def turnaround(iata):
    return 40 if iata in HUBS else 50


def local_to_utc(h, m, iata, day=9):
    """Return UTC datetime for a local departure time on 2026-03-<day>."""
    local_dt = datetime(2026, 3, day, h, m)
    return local_dt - timedelta(hours=UTC_OFFSET[iata])


def fmt(dt):
    return dt.strftime('%Y-%m-%d %H:%M:%S')


# ---------------------------------------------------------------------------
# Schedule definition
# (aircraft_id, tail, type_id, origin, dest, dep_local_h, dep_local_m, return_same_day)
# ---------------------------------------------------------------------------
SCHEDULE = [
    # --- 737-600 (type 1): Short/medium haul, hub-based ---
    # ATL group (aircraft_id 1-4)
    ( 1, 'N601CA', 1, 'ATL', 'MCO',  7,  0, True),
    ( 2, 'N602CA', 1, 'ATL', 'CLT',  7, 30, True),
    ( 3, 'N603CA', 1, 'ATL', 'BNA',  8,  0, True),
    ( 4, 'N604CA', 1, 'ATL', 'MDW',  8, 30, True),
    # ORD group (aircraft_id 5-8)
    ( 5, 'N605CA', 1, 'ORD', 'MSP',  7,  0, True),
    ( 6, 'N606CA', 1, 'ORD', 'STL',  7, 30, True),
    ( 7, 'N607CA', 1, 'ORD', 'DTW',  8,  0, True),
    ( 8, 'N608CA', 1, 'ORD', 'BWI',  8, 30, True),
    # DFW group (aircraft_id 9-12)
    ( 9, 'N609CA', 1, 'DFW', 'IAH',  7,  0, True),
    (10, 'N610CA', 1, 'DFW', 'SAN',  7, 30, True),
    (11, 'N611CA', 1, 'DFW', 'MCI',  8,  0, True),
    (12, 'N612CA', 1, 'DFW', 'BNA',  8, 30, True),
    # LAX group (aircraft_id 13-15)
    (13, 'N613CA', 1, 'LAX', 'LAS',  7,  0, True),
    (14, 'N614CA', 1, 'LAX', 'PHX',  7, 30, True),
    (15, 'N615CA', 1, 'LAX', 'SFO',  8,  0, True),

    # --- 737-800 (type 2): Medium/long haul, hub-based ---
    # ATL group (aircraft_id 16-18)
    (16, 'N801CA', 2, 'ATL', 'JFK',  7,  0, True),
    (17, 'N802CA', 2, 'ATL', 'FLL',  7, 30, True),
    (18, 'N803CA', 2, 'ATL', 'LAX',  8,  0, True),
    # ORD group (aircraft_id 19-21)
    (19, 'N804CA', 2, 'ORD', 'LAX',  7,  0, True),
    (20, 'N805CA', 2, 'ORD', 'JFK',  7, 30, True),
    (21, 'N806CA', 2, 'ORD', 'BOS',  8,  0, True),
    # DFW group (aircraft_id 22-24)
    (22, 'N807CA', 2, 'DFW', 'LAX',  7,  0, True),
    (23, 'N808CA', 2, 'DFW', 'DEN',  7, 30, True),
    (24, 'N809CA', 2, 'DFW', 'PHX',  8,  0, True),
    # LAX group (aircraft_id 25-27)
    (25, 'N810CA', 2, 'LAX', 'ATL',  7,  0, True),
    (26, 'N811CA', 2, 'LAX', 'ORD',  7, 30, True),
    (27, 'N812CA', 2, 'LAX', 'DFW',  8,  0, True),
    # Non-hub starters (aircraft_id 28-30)
    (28, 'N813CA', 2, 'JFK', 'ATL',  7,  0, True),
    (29, 'N814CA', 2, 'BOS', 'ATL',  7,  0, True),
    (30, 'N815CA', 2, 'MIA', 'ATL',  7,  0, True),

    # --- A200-100 (type 3): Regional thin routes ---
    (31, 'N221CA', 3, 'ATL', 'DCA',  9,  0, True),
    (32, 'N222CA', 3, 'ORD', 'PHL',  9,  0, True),
    (33, 'N223CA', 3, 'DFW', 'CLT',  9,  0, True),
    (34, 'N224CA', 3, 'LAX', 'SLC',  9,  0, True),
    (35, 'N225CA', 3, 'JFK', 'BOS',  7,  0, True),
    (36, 'N226CA', 3, 'SFO', 'PDX',  7,  0, True),
    (37, 'N227CA', 3, 'SEA', 'LAX',  7,  0, True),
    (38, 'N228CA', 3, 'PHX', 'LAS',  7,  0, True),
    (39, 'N229CA', 3, 'DEN', 'SLC',  7,  0, True),
    (40, 'N230CA', 3, 'MSP', 'DTW',  7,  0, True),
    (41, 'N231CA', 3, 'DTW', 'LGA',  7,  0, True),
    (42, 'N232CA', 3, 'CLT', 'MIA',  7,  0, True),

    # --- A220-300 (type 4): Long haul / international ---
    (43, 'N301CA', 4, 'JFK', 'CDG', 18,  0, False),  # Overnight; CA002 runs Day 2
    (44, 'N302CA', 4, 'ATL', 'DEN',  9,  0, True),
    (45, 'N303CA', 4, 'ORD', 'SEA',  9,  0, True),
    (46, 'N304CA', 4, 'DFW', 'SFO',  9,  0, True),
    (47, 'N305CA', 4, 'LAX', 'HNL',  9,  0, True),   # Return arrives ~05:40 UTC Mar 10
    (48, 'N306CA', 4, 'BOS', 'MIA',  7,  0, True),
    (49, 'N307CA', 4, 'MIA', 'ORD',  7,  0, True),
    (50, 'N308CA', 4, 'IAH', 'ATL',  7,  0, True),
    (51, 'N309CA', 4, 'SEA', 'ORD',  7,  0, True),
    (52, 'N310CA', 4, 'SFO', 'DFW',  7,  0, True),
    (53, 'N311CA', 4, 'DEN', 'ATL',  7,  0, True),
    (54, 'N312CA', 4, 'PHX', 'ATL',  7,  0, True),
    (55, 'N313CA', 4, 'MSP', 'LAX',  7,  0, True),
]

# ---------------------------------------------------------------------------
# Generate SQL
# ---------------------------------------------------------------------------
rows = []
flight_counter = 100  # generates CA101, CA102, …

# N301CA uses reserved numbers CA001 / CA002 for the international service
intl_outbound = 'CA001'
intl_return   = 'CA002'

for ac_id, tail, type_id, origin, dest, dep_h, dep_m, do_return in SCHEDULE:
    cap = TYPE_SPECS[type_id][0]

    # ---- Outbound leg ----
    if ac_id == 43:           # N301CA — reserved flight number
        fn_out = intl_outbound
    else:
        flight_counter += 1
        fn_out = f'CA{flight_counter:03d}'

    dep_utc = local_to_utc(dep_h, dep_m, origin)
    blk     = block_minutes(origin, dest, type_id)
    arr_utc = dep_utc + timedelta(minutes=blk)
    f_out   = fare_usd(origin, dest)

    rows.append(
        f"  ('{fn_out}',{ac_id},'{origin}','{dest}',"
        f"'{fmt(dep_utc)}','{fmt(arr_utc)}',{cap},{f_out:.2f},'scheduled')"
    )

    # ---- Return leg ----
    if do_return:
        if ac_id == 43:
            fn_ret = intl_return
        else:
            flight_counter += 1
            fn_ret = f'CA{flight_counter:03d}'

        ta          = turnaround(dest)
        ret_dep_utc = arr_utc + timedelta(minutes=ta)
        blk2        = block_minutes(dest, origin, type_id)
        ret_arr_utc = ret_dep_utc + timedelta(minutes=blk2)
        f_ret       = fare_usd(dest, origin)

        rows.append(
            f"  ('{fn_ret}',{ac_id},'{dest}','{origin}',"
            f"'{fmt(ret_dep_utc)}','{fmt(ret_arr_utc)}',{cap},{f_ret:.2f},'scheduled')"
        )

# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------
print("-- ============================================================")
print("-- PCA Day 1 Flight Schedule (auto-generated by generate_flights.py)")
print("-- Sim Day 1 = 2026-03-09  |  All datetimes in UTC")
print("-- 55 aircraft  |  109 flights (1 international one-way + 54 round-trips)")
print("-- ============================================================")
print()
print(f"-- Total flight rows: {len(rows)}")
print()
print("INSERT INTO flights")
print("  (flight_number, aircraft_id, origin_iata, dest_iata,")
print("   scheduled_departure, scheduled_arrival, capacity, fare_USD, status)")
print("VALUES")
print(",\n".join(rows) + ";")
print()
print("-- ============================================================")
print("-- Flight summary by aircraft")
print("-- ============================================================")
# Print a human-readable summary
print()
flight_counter2 = 100
for ac_id, tail, type_id, origin, dest, dep_h, dep_m, do_return in SCHEDULE:
    if ac_id == 43:
        fn_out = 'CA001'
    else:
        flight_counter2 += 1
        fn_out = f'CA{flight_counter2:03d}'

    dep_utc = local_to_utc(dep_h, dep_m, origin)
    blk     = block_minutes(origin, dest, type_id)
    arr_utc = dep_utc + timedelta(minutes=blk)
    mi      = haversine_km(origin, dest) * KM2MI

    print(f"-- {tail}  {fn_out}  {origin}→{dest}  "
          f"dep={fmt(dep_utc)} UTC  +{blk}min  {mi:.0f}mi  ${fare_usd(origin, dest):.2f}")

    if do_return:
        if ac_id == 43:
            fn_ret = 'CA002'
        else:
            flight_counter2 += 1
            fn_ret = f'CA{flight_counter2:03d}'
        ta          = turnaround(dest)
        ret_dep     = arr_utc + timedelta(minutes=ta)
        blk2        = block_minutes(dest, origin, type_id)
        ret_arr     = ret_dep + timedelta(minutes=blk2)
        print(f"-- {tail}  {fn_ret}  {dest}→{origin}  "
              f"dep={fmt(ret_dep)} UTC  +{blk2}min  ${fare_usd(dest, origin):.2f}")
