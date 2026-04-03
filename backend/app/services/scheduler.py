"""
scheduler.py — Panther Cloud Air Flight Schedule Generator (Part 1)

Generates a daily flight schedule for 56 aircraft across 31 airports
using a hub-and-spoke model with 4 hubs (ATL, ORD, DFW, LAX).

Each aircraft performs round-trip flights from its base airport throughout
the operating day (5:00 AM – 1:00 AM local time).  The same flight numbers
repeat every calendar day.
"""

from datetime import datetime, timedelta, date as date_type
from zoneinfo import ZoneInfo
from .timetable import (
    compute_flight_time_minutes,
    taxi_time_minutes,
    compute_fare,
)
from ..config import Config

UTC = ZoneInfo("UTC")

# The 4 hub airports in PCA's hub-and-spoke network
HUBS = ["ATL", "ORD", "DFW", "LAX"]

# Ordered destination lists for each hub (inter-hub routes first, then spokes)
HUB_DESTINATIONS = {
    "ATL": ["ORD", "DFW", "LAX",
            "MCO", "MIA", "FLL", "CLT", "BNA",
            "JFK", "LGA", "BWI", "DCA", "MDW",
            "SEA", "SFO", "DEN"],
    "ORD": ["ATL", "DFW", "LAX",
            "DTW", "MSP", "STL", "MCI", "BOS", "PHL",
            "SEA", "SFO", "DEN", "JFK", "MIA"],
    "DFW": ["ATL", "ORD", "LAX",
            "IAH", "DEN", "SLC", "BNA", "MDW", "SAN",
            "SEA", "SFO", "JFK", "MIA", "BOS"],
    "LAX": ["HNL", "ATL", "ORD", "DFW",
            "SFO", "SEA", "PDX", "LAS", "PHX",
            "DEN", "JFK", "MIA"],
}

# Spoke aircraft tail numbers mapped to their assigned hub for shuttle service
SPOKE_HUB_MAP = {
    "N813CA": "ATL", "N225CA": "ORD", "N301CA": "DFW",
    "N814CA": "ATL", "N306CA": "ORD",
    "N815CA": "ATL", "N307CA": "DFW",
    "N226CA": "LAX", "N310CA": "LAX",
    "N227CA": "LAX", "N309CA": "ORD",
    "N228CA": "LAX", "N312CA": "DFW",
    "N229CA": "DFW", "N311CA": "ORD",
    "N230CA": "ORD", "N313CA": "DFW",
    "N231CA": "ORD",
    "N232CA": "ATL",
    "N308CA": "DFW",
}


# ── Public API ───────────────────────────────────────────────────────────────

TEMPLATE_DATE = date_type(2026, 3, 9)   # reference date — Day 1 per spec (DST active)


def generate_schedule(db):
    """
    Generate the master timetable — a single day of flights that repeats
    identically every day.  Stored with TEMPLATE_DATE as the reference.
    The simulation offsets these times for each sim day.
    Returns the number of template flights inserted.
    """
    airports   = _load_airports(db)
    aircraft   = _load_aircraft(db)
    routes     = _load_routes(db)
    ac_types   = _load_aircraft_types(db)

    # Wipe previous schedule
    cur = db.cursor()
    cur.execute("SET FOREIGN_KEY_CHECKS = 0")
    cur.execute("DELETE FROM flight_legs")
    cur.execute("DELETE FROM flights")
    cur.execute("SET FOREIGN_KEY_CHECKS = 1")
    db.commit()

    assignments = _build_assignments(aircraft, airports, routes, ac_types)

    day_flights = _generate_day(assignments, TEMPLATE_DATE, airports, routes)
    if day_flights:
        day_flights = _recompute_fares(day_flights, ac_types, airports, routes)
        _insert_flights(db, day_flights)
    db.commit()
    return len(day_flights) if day_flights else 0


# ── Data loaders ─────────────────────────────────────────────────────────────

def _load_airports(db):
    cur = db.cursor(dictionary=True)
    cur.execute("SELECT * FROM airports")
    return {r["iata_code"]: r for r in cur.fetchall()}


def _load_aircraft(db):
    cur = db.cursor(dictionary=True)
    cur.execute("SELECT * FROM aircraft WHERE status = 'active' ORDER BY aircraft_id")
    return cur.fetchall()


def _load_routes(db):
    cur = db.cursor(dictionary=True)
    cur.execute("SELECT * FROM routes")
    return {(r["origin_iata"], r["dest_iata"]): r for r in cur.fetchall()}


def _load_aircraft_types(db):
    cur = db.cursor(dictionary=True)
    cur.execute("SELECT * FROM aircraft_types")
    return {r["type_id"]: r for r in cur.fetchall()}


# ── Assignment builder ───────────────────────────────────────────────────────

def _build_assignments(aircraft_list, airports, routes, ac_types):
    """Decide what destinations each aircraft visits in a day."""
    assignments = []
    hub_groups = {h: [] for h in HUBS}  # collect hub-based aircraft for round-robin

    for ac in aircraft_list:
        base = ac["current_airport"]
        ac_type = ac_types[ac["type_id"]]
        tail = ac["tail_number"]

        # Special case: the A350 flies the sole international route JFK-CDG
        if tail == "N350CA":
            assignments.append(dict(
                aircraft=ac, type=ac_type, base="JFK",
                destinations=["CDG"], is_international=True,
            ))
            continue

        # Spoke aircraft: shuttle back and forth to their assigned hub
        if not airports[base]["is_hub"]:
            hub = SPOKE_HUB_MAP.get(tail)
            if not hub or (base, hub) not in routes:
                hub = _nearest_hub(base, routes)
            if hub:
                assignments.append(dict(
                    aircraft=ac, type=ac_type, base=base,
                    destinations=[hub], is_international=False,
                ))
            continue

        # Hub aircraft — collect for round-robin destination assignment
        hub_groups[base].append((ac, ac_type))

    # Round-robin: distribute each hub's destination list across its aircraft.
    # Aircraft 0 gets dests 0,N,2N,...; aircraft 1 gets 1,N+1,2N+1,... etc.
    for hub, ac_list in hub_groups.items():
        dests = [d for d in HUB_DESTINATIONS.get(hub, [])
                 if (hub, d) in routes]
        if not ac_list or not dests:
            continue
        n = len(ac_list)
        for idx, (ac, ac_type) in enumerate(ac_list):
            my_dests = [dests[j] for j in range(len(dests)) if j % n == idx]
            assignments.append(dict(
                aircraft=ac, type=ac_type, base=hub,
                destinations=my_dests, is_international=False,
            ))

    return assignments


def _nearest_hub(airport_iata, routes):
    """Find the closest hub that has a route from this airport."""
    best, best_d = None, float("inf")
    for h in HUBS:
        r = routes.get((airport_iata, h))
        if r and float(r["distance_miles"]) < best_d:
            best_d = float(r["distance_miles"])
            best = h
    return best


# ── Day generator ────────────────────────────────────────────────────────────

def _generate_day(assignments, current_date, airports, routes):
    """Produce every flight for a single calendar day."""
    all_flights = []
    flight_num = 1001

    for asn in assignments:
        flights, flight_num = _plan_aircraft_day(
            asn, current_date, airports, routes, flight_num,
        )
        all_flights.extend(flights)

    return all_flights


def _plan_aircraft_day(asn, current_date, airports, routes, flight_num):
    """
    Build round-trip legs for one aircraft for one day.
    Every aircraft MUST end the day back at its base airport.
    Return flights must land by 00:59 local time (before airport closes at 01:00).
    """
    ac       = asn["aircraft"]
    ac_type  = asn["type"]
    base     = asn["base"]
    dests    = asn["destinations"]
    is_intl  = asn.get("is_international", False)

    base_ap  = airports[base]
    base_tz  = ZoneInfo(base_ap["timezone"])

    # Operating window (local): depart from 05:00, must be back by 00:59 next day.
    # Exception: international flights (JFK→CDG) depart at 18:00 local to allow
    # same-day connections from US cities and minimize overnight NYC layovers.
    if is_intl:
        day_start = datetime(current_date.year, current_date.month, current_date.day,
                             18, 0, tzinfo=base_tz)
    else:
        day_start = datetime(current_date.year, current_date.month, current_date.day,
                             5, 0, tzinfo=base_tz)
    base_curfew = datetime(current_date.year, current_date.month, current_date.day,
                           0, 59, tzinfo=base_tz) + timedelta(days=1)

    current_utc = day_start.astimezone(UTC)
    base_curfew_utc = base_curfew.astimezone(UTC)
    flights = []
    cycle = 0
    max_cycles = 1 if is_intl else 30  # international = 1 round trip; domestic = safety cap

    while cycle < max_cycles and dests:
        dest_iata = dests[cycle % len(dests)]

        # ── outbound: base → dest ──
        out = _make_leg(base, dest_iata, current_utc, current_date,
                        ac, ac_type, airports, routes, flight_num, is_intl)
        if out is None:
            break

        # ── return:   dest → base ──
        needs_fuel_out = float(routes[(base, dest_iata)]["distance_miles"]) > 800
        turnaround_out = (Config.GATE_TURNOVER_WITH_FUEL_MIN
                          if needs_fuel_out else Config.GATE_TURNOVER_MIN)
        ret_depart = out["scheduled_arrival_utc"] + timedelta(minutes=turnaround_out)

        # For international flights, the return may land the next day — use that date
        ret_date = current_date if not is_intl else ret_depart.date()
        ret = _make_leg(dest_iata, base, ret_depart, ret_date,
                        ac, ac_type, airports, routes, flight_num + 1, is_intl)
        if ret is None:
            break  # can't complete round trip — stop

        # Enforce base curfew: return must land at base by 00:59 local
        if not is_intl and ret["scheduled_arrival_utc"] > base_curfew_utc:
            break

        flights.append(out)
        flights.append(ret)
        flight_num += 2

        # turnaround back at base
        needs_fuel_ret = float(routes[(dest_iata, base)]["distance_miles"]) > 800
        turnaround_ret = (Config.GATE_TURNOVER_WITH_FUEL_MIN
                          if needs_fuel_ret else Config.GATE_TURNOVER_MIN)
        current_utc = ret["scheduled_arrival_utc"] + timedelta(minutes=turnaround_ret)

        cycle += 1

    return flights, flight_num


def _make_leg(origin, dest, depart_utc, current_date,
              ac, ac_type, airports, routes, flight_num, is_international):
    """Compute one flight leg.  Returns a dict or None if it won't fit."""
    route = routes.get((origin, dest))
    if route is None:
        return None

    origin_ap = airports[origin]
    dest_ap   = airports[dest]

    t_out = taxi_time_minutes(float(origin_ap["metro_pop_M"]),
                              bool(origin_ap["is_hub"]))
    ft    = compute_flight_time_minutes(
                float(route["distance_km"]),
                float(ac_type["max_speed_kmh"]),
                float(route["heading_degrees"]),
                bool(route["is_international"]),
                float(route["distance_miles"]))
    t_in  = taxi_time_minutes(float(dest_ap["metro_pop_M"]),
                              bool(dest_ap["is_hub"]))

    total_min = t_out + ft + t_in
    arrival_utc = depart_utc + timedelta(minutes=total_min)

    # Must arrive before destination closes (00:59 local next day)
    dest_tz = ZoneInfo(dest_ap["timezone"])
    arrival_local = arrival_utc.astimezone(dest_tz)
    close_local = datetime(current_date.year, current_date.month, current_date.day,
                           0, 59, tzinfo=dest_tz) + timedelta(days=1)
    if arrival_local > close_local and not is_international:
        return None

    # Fuel pricing: based on origin airport (where the aircraft refuels)
    origin_is_foreign = origin_ap.get("country") != "USA"
    fare = compute_fare(
        float(route["distance_miles"]),
        int(ac_type["capacity_passengers"]),
        float(ac_type["fuel_burn_L_per_hr"]),
        ft,
        float(ac_type["monthly_lease_USD"]),
        bool(route["is_international"]),
        origin_is_foreign=origin_is_foreign,
    )

    return {
        "flight_number":        f"CA{flight_num}",
        "aircraft_id":          ac["aircraft_id"],
        "type_id":              ac["type_id"],
        "origin_iata":          origin,
        "dest_iata":            dest,
        "scheduled_departure":  depart_utc.replace(tzinfo=None),
        "scheduled_arrival":    arrival_utc.replace(tzinfo=None),
        "scheduled_arrival_utc": arrival_utc,          # kept for chaining
        "capacity":             int(ac_type["capacity_passengers"]),
        "fare_USD":             fare,
    }


# ── Fare recomputation ───────────────────────────────────────────────────────

def _recompute_fares(day_flights, ac_types, airports, routes):
    """
    After generating a full day of flights, count how many flights each
    aircraft actually makes and recompute fares so that at 30% load
    each flight covers its real share of fuel + landing + lease costs.
    """
    from collections import Counter

    # Count actual flights per aircraft to correctly amortize lease costs
    flights_per_ac = Counter(f["aircraft_id"] for f in day_flights)

    for f in day_flights:
        route = routes.get((f["origin_iata"], f["dest_iata"]))
        if route is None:
            continue

        ac_type = ac_types.get(f["type_id"])
        if ac_type is None:
            continue

        fpd = flights_per_ac[f["aircraft_id"]]
        flight_time = compute_flight_time_minutes(
            float(route["distance_km"]),
            float(ac_type["max_speed_kmh"]),
            float(route["heading_degrees"]),
            bool(route["is_international"]),
            float(route["distance_miles"]),
        )

        origin_is_foreign = airports.get(f["origin_iata"], {}).get("country") != "USA"
        f["fare_USD"] = compute_fare(
            float(route["distance_miles"]),
            int(ac_type["capacity_passengers"]),
            float(ac_type["fuel_burn_L_per_hr"]),
            flight_time,
            float(ac_type["monthly_lease_USD"]),
            bool(route["is_international"]),
            flights_per_day=fpd,
            origin_is_foreign=origin_is_foreign,
        )

    return day_flights


# ── DB insert ────────────────────────────────────────────────────────────────

def _insert_flights(db, flights):
    """Bulk-insert all generated flights into the flights table."""
    cur = db.cursor()
    sql = """INSERT INTO flights
             (flight_number, aircraft_id, origin_iata, dest_iata,
              scheduled_departure, scheduled_arrival, capacity, fare_USD, status)
             VALUES (%s,%s,%s,%s,%s,%s,%s,%s,'scheduled')"""
    rows = [
        (f["flight_number"], f["aircraft_id"], f["origin_iata"], f["dest_iata"],
         f["scheduled_departure"], f["scheduled_arrival"],
         f["capacity"], f["fare_USD"])
        for f in flights
    ]
    cur.executemany(sql, rows)
