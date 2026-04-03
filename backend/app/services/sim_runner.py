"""
sim_runner.py — Panther Cloud Air 14-Day Simulation Runner (Part 2)

Supports two modes:
  1. run_all(db)      — Run all 14 days at once
  2. run_day(db, day) — Run a single day

Each day:
  - Loads flights from the timetable for that date
  - Applies the spec's fixed daily challenge via apply_day_challenge()
  - Generates passenger demand via daily_demand()
  - Computes financials (fuel, lease, landing fees, revenue)
  - Populates simulation_flights, financials, airport_activity tables
"""
import random
import logging
import os
from datetime import timedelta, date as date_type, datetime as datetime_type

from .simulation import apply_day_challenge, daily_demand
from ..config import Config

log = logging.getLogger(__name__)

SIM_START_DATE = "2026-03-09"
SIM_DAYS = 14
HUBS = ["ATL", "ORD", "DFW", "LAX"]


# ── Public API ────────────────────────────────────────────────────────────────

def reset_simulation(db):
    """Wipe all simulation data so a fresh run can start."""
    cur = db.cursor()
    cur.execute("SET FOREIGN_KEY_CHECKS = 0")
    for tbl in ("passenger_flights", "airport_activity", "financials",
                "passengers", "simulation_flights"):
        cur.execute(f"DELETE FROM {tbl}")
    cur.execute("SET FOREIGN_KEY_CHECKS = 1")
    db.commit()
    cur.close()


def run_all(db):
    """Execute the full 14-day simulation with no extra disruptions."""
    reset_simulation(db)
    day_summaries = []
    for day_num in range(1, SIM_DAYS + 1):
        # Reload refs each day so maintenance detection sees accumulated hours
        refs = _load_refs(db)
        summary = _simulate_day(db, day_num, refs)
        day_summaries.append(summary)
        db.commit()
    return _build_report(day_summaries)


def run_day(db, day_num):
    """Run a single simulation day with the spec's fixed daily challenge."""
    if not (1 <= day_num <= SIM_DAYS):
        raise ValueError(f"Day must be 1-{SIM_DAYS}")

    # Clear any existing data for this day (allows re-running)
    cur = db.cursor()
    cur.execute("SET FOREIGN_KEY_CHECKS = 0")
    cur.execute("""DELETE pf FROM passenger_flights pf
                   JOIN simulation_flights sf ON pf.sim_flight_id = sf.sim_flight_id
                   WHERE sf.sim_day = %s""", (day_num,))
    cur.execute("DELETE FROM passengers WHERE sim_day = %s", (day_num,))
    cur.execute("""DELETE aa FROM airport_activity aa
                   JOIN simulation_flights sf ON aa.sim_flight_id = sf.sim_flight_id
                   WHERE sf.sim_day = %s""", (day_num,))
    cur.execute("DELETE FROM financials WHERE sim_day = %s", (day_num,))
    cur.execute("DELETE FROM simulation_flights WHERE sim_day = %s", (day_num,))
    cur.execute("SET FOREIGN_KEY_CHECKS = 1")
    db.commit()
    cur.close()

    refs = _load_refs(db)
    summary = _simulate_day(db, day_num, refs)
    db.commit()
    return summary


def get_progress(db):
    """Return which days have been simulated."""
    cur = db.cursor(dictionary=True)
    cur.execute("SELECT DISTINCT sim_day FROM simulation_flights ORDER BY sim_day")
    completed = [r["sim_day"] for r in cur.fetchall()]
    cur.close()
    return completed


# ── Internal helpers ──────────────────────────────────────────────────────────

def _load_refs(db):
    """Load airports, aircraft, compute totals — cached per call."""
    cur = db.cursor(dictionary=True)

    # Load all airports indexed by IATA code
    cur.execute("SELECT * FROM airports")
    airports = {r["iata_code"]: r for r in cur.fetchall()}

    # Load active aircraft with their type specs (fuel burn, capacity, lease)
    cur.execute("""
        SELECT a.aircraft_id, a.tail_number, a.current_airport, at.fuel_burn_L_per_hr,
               at.capacity_passengers, at.monthly_lease_USD, at.model
        FROM aircraft a
        JOIN aircraft_types at ON a.type_id = at.type_id
        WHERE a.status = 'active'
    """)
    aircraft_map = {r["aircraft_id"]: r for r in cur.fetchall()}

    # Sum of all metro populations — used as the denominator in demand formula
    total_metro = sum(float(a["metro_pop_M"]) for a in airports.values())

    # Day 11 challenge: pick one hub aircraft to fail (deterministic seed for reproducibility)
    # Use a seed so the same aircraft fails if the sim is re-run
    rng = random.Random(42)
    hub_aircraft = [ac for ac in aircraft_map.values()
                    if ac["current_airport"] in HUBS and ac["tail_number"] != "N350CA"]
    failed_aircraft_id = rng.choice(hub_aircraft)["aircraft_id"] if hub_aircraft else None

    # ── Maintenance tracking ──────────────────────────────────────────────
    # Load per-aircraft flight hours from simulation to track 200-hr maintenance.
    cur.execute("""
        SELECT f.aircraft_id, sf.sim_day,
               SUM(TIMESTAMPDIFF(MINUTE, sf.actual_departure, sf.actual_arrival)) / 60.0 AS day_hours
        FROM simulation_flights sf
        JOIN flights f ON sf.flight_id = f.flight_id
        WHERE sf.status IN ('arrived', 'delayed')
        GROUP BY f.aircraft_id, sf.sim_day
        ORDER BY f.aircraft_id, sf.sim_day
    """)
    # Accumulate per-aircraft hours day-by-day to detect 200-hr threshold
    daily_hours_rows = cur.fetchall()
    sim_hours = {}          # aircraft_id -> running flight hours (resets after maintenance)
    maint_entered = {}      # aircraft_id -> sim_day when aircraft entered maintenance
    maint_completed = {}    # aircraft_id -> set of sim_days where maintenance completed

    # First pass: accumulate hours day-by-day to find when 200 hrs was hit
    ac_day_hours = {}  # aircraft_id → [(sim_day, hours_that_day), ...]
    for row in daily_hours_rows:
        ac_id = row["aircraft_id"]
        ac_day_hours.setdefault(ac_id, []).append((row["sim_day"], float(row["day_hours"] or 0)))

    # Spec says 1.5 days maintenance; round to 2 full sim days
    maint_duration_days = int(Config.MAINTENANCE_DURATION_DAYS + 0.5)

    for ac_id, ac in aircraft_map.items():
        base_hrs = float(ac.get("flight_hours", 0) or 0)  # hours from DB (pre-sim)
        running_hrs = base_hrs
        day_list = ac_day_hours.get(ac_id, [])
        ac_maint_entered = None
        ac_maint_completed_days = set()

        for sim_day, day_hrs in sorted(day_list, key=lambda x: x[0]):
            # Check if aircraft was in maintenance on this day (shouldn't have flown, but
            # hours are only from operated flights so this is safe)
            if ac_maint_entered is not None:
                # Aircraft is in maintenance — check if it's done
                days_in_maint = sim_day - ac_maint_entered
                if days_in_maint >= maint_duration_days:
                    # Maintenance complete — reset hours, record completion
                    ac_maint_completed_days.add(sim_day)
                    running_hrs = 0
                    ac_maint_entered = None

            running_hrs += day_hrs

            if ac_maint_entered is None and running_hrs >= Config.MAINTENANCE_AFTER_HOURS:
                # Aircraft crossed 200 hrs after flying this day — maintenance starts NEXT day
                ac_maint_entered = sim_day + 1

        # Check if base hours alone trigger maintenance (no sim flights yet)
        if ac_maint_entered is None and running_hrs >= Config.MAINTENANCE_AFTER_HOURS:
            ac_maint_entered = 1  # needs maintenance from day 1

        sim_hours[ac_id] = running_hrs
        if ac_maint_entered is not None:
            maint_entered[ac_id] = ac_maint_entered
        if ac_maint_completed_days:
            maint_completed[ac_id] = ac_maint_completed_days

    # Enforce max 3 simultaneous maintenance slots per hub per spec.
    # Aircraft are assigned to their nearest hub for maintenance — they don't
    # need to physically be at a hub to enter maintenance.
    maintenance_set = set()
    hub_maint_count = {h: 0 for h in HUBS}

    # Load routes to find nearest hub for non-hub aircraft
    cur.execute("SELECT origin_iata, dest_iata, distance_miles FROM routes")
    route_dists = {(r["origin_iata"], r["dest_iata"]): float(r["distance_miles"]) for r in cur.fetchall()}

    def _nearest_hub(airport_iata):
        """Find the closest hub to the given airport."""
        best, best_d = None, float("inf")
        for h in HUBS:
            d = route_dists.get((airport_iata, h), float("inf"))
            if d < best_d:
                best_d = d
                best = h
        return best or HUBS[0]

    for ac_id, entered_day in maint_entered.items():
        ac = aircraft_map.get(ac_id)
        if not ac:
            continue
        base_airport = ac.get("current_airport", "")
        # Assign to nearest hub for maintenance capacity tracking
        hub = base_airport if base_airport in HUBS else _nearest_hub(base_airport)
        if hub_maint_count[hub] < Config.MAX_MAINTENANCE_SIMULTANEOUS:
            maintenance_set.add(ac_id)
            hub_maint_count[hub] += 1

    cur.close()
    return {
        "airports": airports,
        "aircraft_map": aircraft_map,
        "total_metro": total_metro,
        "failed_aircraft_id": failed_aircraft_id,
        "maintenance_set": maintenance_set,
        "maint_entered": maint_entered,
        "maint_completed": maint_completed,
        "sim_hours": sim_hours,
    }


def _compute_flight_passengers(flights, airports, total_metro):
    """
    Compute passenger demand per flight using the spec formula:

        demand(A→B) = src_pop * 1,000,000 * 0.5% * 2% * (dest_pop / reachable_pop)

    where reachable_pop = total metro pop of all airports EXCLUDING the source.

    Handles BOTH direct passengers AND connecting passengers who travel
    through a hub.  For city pairs without a direct flight, passengers are
    routed via a connecting hub (spoke→hub→dest or origin→hub→spoke).

    Returns:
        pax_per_flight: list[int] — total passengers (direct + connecting) per flight
        direct_pax_per_flight: list[int] — only direct passengers per flight (for revenue)
        connecting_pax: list of dicts describing each connecting-passenger group:
            {source, dest, hub, leg1_idx, leg2_idx, count, fare}
    """
    from collections import defaultdict

    # 1. Group flights by (origin, dest) pair
    route_flights = defaultdict(list)
    for i, f in enumerate(flights):
        route_flights[(f["origin_iata"], f["dest_iata"])].append(i)

    # Set of city pairs that have direct flights
    direct_pairs = set(route_flights.keys())

    pax_per_flight = [0] * len(flights)
    direct_pax_per_flight = [0] * len(flights)
    connecting_pax = []  # groups of connecting passengers

    all_codes = list(airports.keys())

    for origin_iata in all_codes:
        origin_ap = airports.get(origin_iata, {})
        src_pop = float(origin_ap.get("metro_pop_M", 1))
        reachable_pop = total_metro - src_pop
        if reachable_pop <= 0:
            continue

        for dest_iata in all_codes:
            if dest_iata == origin_iata:
                continue

            dest_ap = airports.get(dest_iata, {})
            dst_pop = float(dest_ap.get("metro_pop_M", 1))

            route_demand = round(
                src_pop * 1_000_000
                * Config.DAILY_AIR_TRAVEL_PCT
                * Config.INITIAL_MARKET_SHARE_PCT
                * (dst_pop / reachable_pop)
            )
            if route_demand <= 0:
                continue

            # --- Case 1: Direct flight exists ---
            if (origin_iata, dest_iata) in direct_pairs:
                flight_idxs = route_flights[(origin_iata, dest_iata)]
                num_flights = len(flight_idxs)
                base_pax = route_demand // num_flights
                extra = route_demand % num_flights
                for j, idx in enumerate(flight_idxs):
                    pax = base_pax + (1 if j < extra else 0)
                    cap = int(flights[idx]["capacity"])
                    added = min(pax, cap)
                    pax_per_flight[idx] += added
                    direct_pax_per_flight[idx] += added
                continue

            # --- Case 2: No direct flight — route via connecting hub(s) ---
            connections = _find_all_connections(
                origin_iata, dest_iata, route_flights, flights,
            )
            if not connections:
                continue  # no connection possible

            # Spread demand evenly across available connections
            remaining_demand = route_demand
            n_conn = len(connections)
            base_per = remaining_demand // n_conn
            extra_conn = remaining_demand % n_conn

            for ci, (hub_iata, leg1_idx, leg2_idx) in enumerate(connections):
                allotted = base_per + (1 if ci < extra_conn else 0)
                if allotted <= 0:
                    continue

                # Cap by remaining capacity on both legs
                leg1_remaining = int(flights[leg1_idx]["capacity"]) - pax_per_flight[leg1_idx]
                leg2_remaining = int(flights[leg2_idx]["capacity"]) - pax_per_flight[leg2_idx]
                actual_pax = min(allotted, leg1_remaining, leg2_remaining)
                if actual_pax <= 0:
                    continue

                pax_per_flight[leg1_idx] += actual_pax
                pax_per_flight[leg2_idx] += actual_pax

                fare_leg1 = float(flights[leg1_idx]["fare_USD"])
                fare_leg2 = float(flights[leg2_idx]["fare_USD"])

                connecting_pax.append({
                    "source": origin_iata,
                    "dest": dest_iata,
                    "hub": hub_iata,
                    "leg1_idx": leg1_idx,
                    "leg2_idx": leg2_idx,
                    "count": actual_pax,
                    "fare": fare_leg1 + fare_leg2,
                })

    return pax_per_flight, direct_pax_per_flight, connecting_pax


def _find_all_connections(origin, dest, route_flights, flights):
    """
    Find ALL valid one-stop connections from origin→hub→dest.
    Returns list of (hub_iata, leg1_flight_idx, leg2_flight_idx) sorted by arrival.
    """
    connections = []

    for hub in HUBS:
        if hub == origin or hub == dest:
            continue
        leg1_idxs = route_flights.get((origin, hub))
        leg2_idxs = route_flights.get((hub, dest))
        if not leg1_idxs or not leg2_idxs:
            continue

        for l1 in leg1_idxs:
            arr1 = flights[l1]["scheduled_arrival"]
            min_connect = arr1 + timedelta(minutes=Config.TRANSIT_MIN_MINUTES)
            for l2 in leg2_idxs:
                dep2 = flights[l2]["scheduled_departure"]
                if dep2 >= min_connect:
                    connections.append((hub, l1, l2))
                    break  # take earliest valid leg2 for this leg1

    # Sort by final arrival time
    connections.sort(key=lambda c: flights[c[2]]["scheduled_arrival"])
    return connections


def _simulate_day(db, day_num, refs):
    """Simulate a single day: apply challenges, compute demand, record financials."""
    airports = refs["airports"]
    aircraft_map = refs["aircraft_map"]
    total_metro = refs["total_metro"]
    failed_aircraft_id = refs["failed_aircraft_id"]
    maintenance_set = refs.get("maintenance_set", set())
    maint_entered = refs.get("maint_entered", {})
    maint_duration_days = int(Config.MAINTENANCE_DURATION_DAYS + 0.5)  # 1.5 → 2 days

    # Only ground aircraft still within their maintenance window this day
    active_maintenance = set()
    for ac_id in maintenance_set:
        entered_day = maint_entered.get(ac_id, 0)
        days_in_maint = day_num - entered_day
        if days_in_maint < maint_duration_days:
            active_maintenance.add(ac_id)

    start_date = date_type.fromisoformat(SIM_START_DATE)
    sim_date = start_date + timedelta(days=day_num - 1)

    # Load the master timetable (single template day) and offset times
    # to the current simulation day
    from .scheduler import TEMPLATE_DATE
    day_offset = timedelta(days=(sim_date - TEMPLATE_DATE).days)

    cur = db.cursor(dictionary=True)
    cur.execute("""
        SELECT f.flight_id, f.flight_number, f.aircraft_id,
               f.origin_iata, f.dest_iata,
               f.scheduled_departure, f.scheduled_arrival,
               f.capacity, f.fare_USD
        FROM flights f
        WHERE f.scheduled_departure >= %s AND f.scheduled_departure < %s
        ORDER BY f.scheduled_departure
    """, (Config.TEMPLATE_RANGE_START, Config.TEMPLATE_RANGE_END))
    template_flights = cur.fetchall()
    cur.close()

    # Offset template times to this sim day
    flights = []
    for f in template_flights:
        flight = dict(f)
        flight["scheduled_departure"] = f["scheduled_departure"] + day_offset
        flight["scheduled_arrival"] = f["scheduled_arrival"] + day_offset
        flights.append(flight)

    # ── Demand computation ────────────────────────────────────────────
    flight_pax, direct_pax, connecting_groups = _compute_flight_passengers(
        flights, airports, total_metro,
    )

    # ── Per-flight simulation loop ────────────────────────────────────
    insert_cur = db.cursor()

    day_passengers = 0
    day_revenue = 0.0
    day_fuel_cost = 0.0
    day_landing_cost = 0.0
    completed = 0
    delayed_count = 0
    cancelled_count = 0
    events = []

    # Track per-flight data for connecting passenger insertion later
    sim_flight_ids = [None] * len(flights)
    flight_status = ["scheduled"] * len(flights)
    flight_actual_dep = [None] * len(flights)
    flight_actual_arr = [None] * len(flights)

    # Track aircraft location through the day to enforce round-trip integrity.
    # Each aircraft starts at its base. After an outbound leg, it's "away".
    # Return legs (back to base) are NEVER cancelled — the aircraft must get home.
    # If an outbound is cancelled, the aircraft never left, so the return is
    # also cancelled (nothing to return from).
    aircraft_base = {}       # aircraft_id → home airport (from DB)
    aircraft_away = set()    # aircraft IDs currently away from base
    aircraft_grounded = set()  # aircraft IDs whose outbound was cancelled

    for ac_id, ac in aircraft_map.items():
        aircraft_base[ac_id] = ac["current_airport"]

    # ── Gate occupancy tracking ──────────────────────────────────────
    # Per spec: "If a flight lands at an airport and a gate is not available,
    # then the aircraft must wait on the tarmac."
    # Each gate tracks when it becomes free. Flights are assigned the earliest
    # available gate; if none is free at arrival time, the aircraft waits.
    # gate_free_at[airport_iata] = list of datetimes (one per gate) when each gate opens
    gate_free_at = {}
    for iata, ap in airports.items():
        n_gates = int(ap.get("num_gates", 2))
        # All gates start free at the beginning of the operating day
        gate_free_at[iata] = [datetime_type.combine(sim_date, datetime_type.min.time())] * n_gates
    gate_wait_count = 0  # count of flights that had to wait for a gate

    for i, flight in enumerate(flights):
        origin = flight["origin_iata"]
        dest = flight["dest_iata"]
        origin_ap = airports.get(origin, {})
        dest_ap = airports.get(dest, {})
        ac = aircraft_map.get(flight["aircraft_id"], {})

        origin_lat = float(origin_ap.get("latitude", 0))
        origin_lon = float(origin_ap.get("longitude", 0))
        dest_lat = float(dest_ap.get("latitude", 0))
        dest_lon = float(dest_ap.get("longitude", 0))

        sched_dep = flight["scheduled_departure"]
        sched_arr = flight["scheduled_arrival"]
        sched_minutes = (sched_arr - sched_dep).total_seconds() / 60

        flight_info = {
            "scheduled_flight_minutes": sched_minutes,
            "_sched_minutes": sched_minutes,
            "aircraft_failed": (day_num == 11 and
                                flight["aircraft_id"] == failed_aircraft_id),
        }

        ac_id = flight["aircraft_id"]
        base = aircraft_base.get(ac_id)
        is_return_leg = ac_id in aircraft_away and dest == base

        # Apply the spec's fixed daily challenge
        challenge = apply_day_challenge(
            day_num, flight_info, origin_lat, origin_lon, dest_lat, dest_lon,
        )

        is_cancelled = challenge.get("cancelled", False)
        if day_num == 11 and ac_id == failed_aircraft_id:
            is_cancelled = True
            challenge["reason"] = "Aircraft taken out of service — unscheduled maintenance"

        # Maintenance: aircraft currently in maintenance window are grounded
        maint_reason = None
        if ac_id in active_maintenance:
            is_cancelled = True
            entered = maint_entered.get(ac_id, day_num)
            remaining = maint_duration_days - (day_num - entered)
            maint_reason = f"Scheduled maintenance (200+ flight hours, {remaining} day(s) remaining)"

        # Round-trip integrity:
        # - If this is an outbound and it's cancelled, mark aircraft grounded
        #   so the return leg is also cancelled (aircraft never left base).
        # - If this is a return leg and the aircraft is away from base,
        #   it MUST fly home — override any cancellation.
        if is_cancelled and not is_return_leg:
            aircraft_grounded.add(ac_id)
        elif is_return_leg and ac_id in aircraft_grounded:
            # Outbound was cancelled, aircraft never left — cancel return too
            is_cancelled = True
            challenge["reason"] = "Outbound leg cancelled — aircraft at base"
        elif is_return_leg and not (ac_id in aircraft_grounded):
            # Aircraft is away from base — it MUST return regardless of challenge
            is_cancelled = False
            maint_reason = None

        delay_min = challenge.get("delay_minutes", 0)

        # Combine reasons
        all_reasons = []
        if challenge.get("reason") and is_cancelled:
            all_reasons.append(challenge["reason"])
        if maint_reason:
            all_reasons.append(maint_reason)
        combined_reason = "; ".join(all_reasons) if all_reasons else None

        if is_cancelled:
            status = "cancelled"
            actual_dep = None
            actual_arr = None
            pax = 0
            fuel_L = 0
            cancelled_count += 1
            if cancelled_count <= 5:
                events.append(
                    f"{flight['flight_number']} {origin}-{dest} CANCELLED: "
                    f"{combined_reason or 'Unknown'}"
                )
        else:
            delay_type = challenge.get("delay_type", "departure")
            if delay_type == "airtime":
                # Flight time changed (Day 3 weather, Day 7 jet stream):
                # departure on schedule, only arrival shifts
                actual_dep = sched_dep
                actual_arr = sched_arr + timedelta(minutes=delay_min)
            else:
                # Departure delay (Day 5 icing, Day 9 gate):
                # both departure and arrival shift together
                actual_dep = sched_dep + timedelta(minutes=max(0, delay_min))
                actual_arr = sched_arr + timedelta(minutes=delay_min)
            status = "delayed" if delay_min > 5 else "arrived"

            # Update aircraft location tracking
            if is_return_leg:
                aircraft_away.discard(ac_id)
                aircraft_grounded.discard(ac_id)
            else:
                aircraft_away.add(ac_id)

            if status == "delayed":
                delayed_count += 1
            completed += 1

            pax = flight_pax[i]  # total bodies on plane (direct + connecting)

            flight_hrs = sched_minutes / 60
            fuel_burn = float(ac.get("fuel_burn_L_per_hr", 2800))
            fuel_L = fuel_burn * flight_hrs

        # ── Gate contention at destination airport ────────────────────
        # Per spec: passengers can only board/deplane at a gate. If no gate
        # is free when the aircraft arrives, it waits on the tarmac.
        # Gate occupancy = arrival time until departure (after turnaround).
        dep_gate = "—"
        arr_gate = "—"

        if not is_cancelled and actual_arr is not None:
            dest_gates = gate_free_at.get(dest, [datetime_type.combine(sim_date, datetime_type.min.time())])

            # Find the gate that frees up earliest
            earliest_idx = min(range(len(dest_gates)), key=lambda g: dest_gates[g])
            earliest_free = dest_gates[earliest_idx]

            if earliest_free <= actual_arr:
                # Gate available on arrival — no wait
                arr_gate = f"G{earliest_idx + 1}"
            else:
                # All gates occupied — aircraft waits on tarmac until one opens
                tarmac_wait = (earliest_free - actual_arr).total_seconds() / 60
                actual_arr = earliest_free  # arrival at gate is delayed
                arr_gate = f"G{earliest_idx + 1}"
                gate_wait_count += 1

                # Append tarmac wait to the delay reason
                wait_note = f"Tarmac wait {int(tarmac_wait)} min (no gate at {dest})"
                if combined_reason:
                    combined_reason += "; " + wait_note
                else:
                    combined_reason = wait_note
                # A tarmac wait counts as a delay if significant
                if tarmac_wait > 5 and status == "arrived":
                    status = "delayed"
                    delayed_count += 1
                    completed -= 1  # undo the earlier completed++, will re-add below
                    completed += 1

            # Mark this gate as occupied until turnaround completes
            # Turnaround: 50 min if long-haul (>120 min flight), else 40 min
            ta = 50 if sched_minutes > 120 else 40
            dest_gates[earliest_idx] = actual_arr + timedelta(minutes=ta)

        if not is_cancelled and actual_dep is not None:
            # Assign departure gate at origin (aircraft was already at gate from prior arrival)
            origin_gates = gate_free_at.get(origin, [datetime_type.combine(sim_date, datetime_type.min.time())])
            # Find a gate that's free at departure time (should usually be available
            # since the aircraft arrived here on a previous flight and occupied a gate)
            dep_idx = min(range(len(origin_gates)), key=lambda g: origin_gates[g])
            dep_gate = f"G{dep_idx + 1}"

        insert_cur.execute("""
            INSERT INTO simulation_flights
                (flight_id, sim_day, sim_date, actual_departure, actual_arrival,
                 passengers_boarded, gate_used, delay_reason, fuel_used_L, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            flight["flight_id"], day_num, sim_date,
            actual_dep, actual_arr,
            pax, arr_gate, combined_reason, round(fuel_L, 2) if fuel_L else 0,
            status,
        ))
        sim_flight_id = insert_cur.lastrowid
        sim_flight_ids[i] = sim_flight_id
        flight_status[i] = status
        flight_actual_dep[i] = actual_dep if not is_cancelled else None
        flight_actual_arr[i] = actual_arr if not is_cancelled else None

        # Insert individual passenger records for DIRECT passengers only
        # (connecting passengers are inserted in a second pass below)
        direct_count = direct_pax[i] if not is_cancelled else 0
        if direct_count > 0:
            pax_rows = [(origin, dest, day_num)] * direct_count
            insert_cur.executemany(
                "INSERT INTO passengers (source_iata, dest_iata, sim_day) VALUES (%s, %s, %s)",
                pax_rows,
            )
            first_pax_id = insert_cur.lastrowid
            pf_rows = [
                (first_pax_id + k, sim_flight_id, origin, dest,
                 sched_dep, actual_dep, sched_arr, actual_arr)
                for k in range(direct_count)
            ]
            insert_cur.executemany("""
                INSERT INTO passenger_flights
                    (passenger_id, sim_flight_id, leg_origin, leg_dest,
                     sched_departure, actual_departure, sched_arrival, actual_arrival)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, pf_rows)

        if not is_cancelled:
            insert_cur.execute("""
                INSERT INTO airport_activity
                    (airport_iata, sim_day, sim_flight_id, event_type, event_time,
                     gate_used, passengers_count, aircraft_tail)
                VALUES (%s, %s, %s, 'departure', %s, %s, %s, %s)
            """, (origin, day_num, sim_flight_id, actual_dep, dep_gate,
                  pax, ac.get("tail_number")))

            insert_cur.execute("""
                INSERT INTO airport_activity
                    (airport_iata, sim_day, sim_flight_id, event_type, event_time,
                     gate_used, passengers_count, aircraft_tail)
                VALUES (%s, %s, %s, 'arrival', %s, %s, %s, %s)
            """, (dest, day_num, sim_flight_id, actual_arr, arr_gate,
                  pax, ac.get("tail_number")))

        # Financials
        if not is_cancelled:
            fuel_gal = fuel_L * 0.264172
            origin_is_foreign = origin_ap.get("country") != "USA"
            is_intl = origin_is_foreign or dest_ap.get("country") != "USA"
            eur_usd = float(os.getenv("EUR_USD_RATE", "1.08"))

            # Fuel pricing: based on origin airport (where the aircraft refuels)
            # JFK→CDG refuels at JFK (US rate); CDG→JFK refuels at CDG (EUR rate)
            if origin_is_foreign:
                fuel_cost = Config.FUEL_PRICE_PARIS_EUR_PER_L * fuel_L * eur_usd
            else:
                fuel_cost = fuel_gal * Config.FUEL_PRICE_USD_PER_GALLON
            day_fuel_cost += fuel_cost

            # Landing fees: international pays US + EUR; domestic pays US at both ends
            if is_intl:
                landing = Config.LANDING_FEE_US_USD + Config.LANDING_FEE_PARIS_EUR * eur_usd
            else:
                landing = 2 * Config.LANDING_FEE_US_USD
            day_landing_cost += landing

            day_revenue += direct_count * float(flight["fare_USD"])
            day_passengers += direct_count  # unique direct passengers only (connecting added below)

    # ── Connecting passengers (hub transfers) ─────────────────────────
    connecting_total = 0
    for cg in connecting_groups:
        l1 = cg["leg1_idx"]
        l2 = cg["leg2_idx"]
        # Only count if BOTH legs operated (not cancelled)
        if flight_status[l1] == "cancelled" or flight_status[l2] == "cancelled":
            continue
        count = cg["count"]
        if count <= 0:
            continue

        source = cg["source"]
        dest = cg["dest"]
        hub = cg["hub"]
        sf1 = sim_flight_ids[l1]
        sf2 = sim_flight_ids[l2]
        f1 = flights[l1]
        f2 = flights[l2]

        # Insert passenger records (source→dest is their true origin/dest)
        pax_rows = [(source, dest, day_num)] * count
        insert_cur.executemany(
            "INSERT INTO passengers (source_iata, dest_iata, sim_day) VALUES (%s, %s, %s)",
            pax_rows,
        )
        first_pax_id = insert_cur.lastrowid

        # Each connecting passenger has TWO flight legs
        pf_rows = []
        for k in range(count):
            pid = first_pax_id + k
            # Leg 1: origin → hub
            pf_rows.append((
                pid, sf1, source, hub,
                f1["scheduled_departure"], flight_actual_dep[l1],
                f1["scheduled_arrival"], flight_actual_arr[l1],
            ))
            # Leg 2: hub → dest
            pf_rows.append((
                pid, sf2, hub, dest,
                f2["scheduled_departure"], flight_actual_dep[l2],
                f2["scheduled_arrival"], flight_actual_arr[l2],
            ))
        insert_cur.executemany("""
            INSERT INTO passenger_flights
                (passenger_id, sim_flight_id, leg_origin, leg_dest,
                 sched_departure, actual_departure, sched_arrival, actual_arrival)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, pf_rows)

        # Revenue: connecting passengers pay the combined fare of both legs
        day_revenue += count * cg["fare"]
        day_passengers += count  # unique connecting passengers
        connecting_total += count

    if connecting_total > 0:
        events.append(f"{connecting_total} connecting passengers via hubs")

    # ── Rebooking: move stranded passengers to alternate flights ──────
    # Collect cancelled flights that had potential passengers
    rebooked_count = 0
    if cancelled_count > 0:
        # Find cancelled flights and their would-be demand
        cancel_cur = db.cursor(dictionary=True)
        cancel_cur.execute("""
            SELECT sf.sim_flight_id, f.origin_iata, f.dest_iata, f.capacity,
                   f.fare_USD, f.scheduled_departure, f.scheduled_arrival
            FROM simulation_flights sf
            JOIN flights f ON sf.flight_id = f.flight_id
            WHERE sf.sim_day = %s AND sf.status = 'cancelled'
        """, (day_num,))
        cancelled_flights = cancel_cur.fetchall()

        for cf in cancelled_flights:
            o, d = cf["origin_iata"], cf["dest_iata"]
            o_ap = airports.get(o, {})
            d_ap = airports.get(d, {})
            src_pop = float(o_ap.get("metro_pop_M", 1))
            dst_pop = float(d_ap.get("metro_pop_M", 1))
            would_be_pax = min(
                daily_demand(src_pop, dst_pop, total_metro),
                int(cf["capacity"]),
            )
            if would_be_pax == 0:
                continue

            # Find alternate flights on same route with remaining capacity
            cancel_cur.execute("""
                SELECT sf.sim_flight_id, f.capacity, sf.passengers_boarded,
                       sf.actual_departure, sf.actual_arrival,
                       f.scheduled_departure, f.scheduled_arrival, f.fare_USD
                FROM simulation_flights sf
                JOIN flights f ON sf.flight_id = f.flight_id
                WHERE sf.sim_day = %s AND sf.status IN ('arrived', 'delayed')
                  AND f.origin_iata = %s AND f.dest_iata = %s
                  AND sf.passengers_boarded < f.capacity
                ORDER BY sf.actual_departure
            """, (day_num, o, d))
            alts = cancel_cur.fetchall()

            remaining = would_be_pax
            for alt in alts:
                if remaining <= 0:
                    break
                space = int(alt["capacity"]) - int(alt["passengers_boarded"])
                to_rebook = min(remaining, space)
                if to_rebook <= 0:
                    continue

                # Update the alternate flight's passenger count
                insert_cur.execute("""
                    UPDATE simulation_flights
                    SET passengers_boarded = passengers_boarded + %s
                    WHERE sim_flight_id = %s
                """, (to_rebook, alt["sim_flight_id"]))

                # Insert rebooked passenger records
                pax_rows = [(o, d, day_num)] * to_rebook
                insert_cur.executemany(
                    "INSERT INTO passengers (source_iata, dest_iata, sim_day) VALUES (%s, %s, %s)",
                    pax_rows,
                )
                first_id = insert_cur.lastrowid
                pf_rows = [
                    (first_id + i, alt["sim_flight_id"], o, d,
                     alt["scheduled_departure"], alt["actual_departure"],
                     alt["scheduled_arrival"], alt["actual_arrival"])
                    for i in range(to_rebook)
                ]
                insert_cur.executemany("""
                    INSERT INTO passenger_flights
                        (passenger_id, sim_flight_id, leg_origin, leg_dest,
                         sched_departure, actual_departure, sched_arrival, actual_arrival)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, pf_rows)

                day_revenue += to_rebook * float(alt["fare_USD"])
                day_passengers += to_rebook
                rebooked_count += to_rebook
                remaining -= to_rebook

        cancel_cur.close()

    if rebooked_count > 0:
        events.append(f"{rebooked_count} passengers rebooked from cancelled flights")

    if gate_wait_count > 0:
        events.append(f"{gate_wait_count} flights waited on tarmac (no gate available)")

    # ── Financial summary for this day ────────────────────────────────
    # Lease is a fixed daily cost regardless of flights operated
    daily_lease = sum(float(ac["monthly_lease_USD"]) for ac in aircraft_map.values()) / 30
    total_day_costs = day_fuel_cost + daily_lease + day_landing_cost

    # Insert one row per financial category (fuel, lease, landing_fee, revenue)
    for cat, amt, note in [
        ("fuel", day_fuel_cost, f"Day {day_num} fuel costs"),
        ("lease", daily_lease, f"Day {day_num} fleet lease amortization"),
        ("landing_fee", day_landing_cost, f"Day {day_num} landing/terminal fees"),
        ("revenue", day_revenue, f"Day {day_num} passenger revenue"),
    ]:
        insert_cur.execute("""
            INSERT INTO financials (sim_day, sim_date, category, amount_USD, notes)
            VALUES (%s, %s, %s, %s, %s)
        """, (day_num, sim_date, cat, round(amt, 2), note))

    insert_cur.close()

    return {
        "day": day_num,
        "date": sim_date.isoformat(),
        "total_flights": len(flights),
        "completed": completed,
        "delayed": delayed_count,
        "cancelled": cancelled_count,
        "passengers": day_passengers,
        "revenue": round(day_revenue, 2),
        "costs": round(total_day_costs, 2),
        "events": events,
    }


def _build_report(day_summaries):
    """Aggregate all 14 day summaries into a final simulation report."""
    total_pax = sum(d["passengers"] for d in day_summaries)
    total_revenue = sum(d["revenue"] for d in day_summaries)
    total_costs = sum(d["costs"] for d in day_summaries)
    return {
        "days": day_summaries,
        "totals": {
            "total_passengers": total_pax,
            "total_revenue_USD": round(total_revenue, 2),
            "total_costs_USD": round(total_costs, 2),
            "profit_loss_USD": round(total_revenue - total_costs, 2),
        },
    }
