# Part 2 daily challenge logic.
# Each sim day (1-14) has a fixed challenge from the project spec. Provides:
#   - apply_day_challenge(): delay/cancellation info for a single flight
#   - daily_demand(): passenger demand between two airports

import random
import math
from .timetable import wind_time_factor, bearing_degrees

# Day Challenge Handlers

def apply_day_challenge(day, flight, origin_lat, origin_lon, dest_lat, dest_lon):
    """
    Apply the daily challenge to a flight.
    Returns a dict with delay_minutes (int) and reason (str).
    """
    delay_minutes = 0
    reason = None

    if day == 1:
        # Day 1: Baseline — follow timetable exactly, no disruptions
        pass

    elif day in (2, 4, 6, 8, 10, 12, 14):
        # Even days: No delays — aircraft start where they ended previous day
        pass

    elif day == 3:
        # 25% of flights: bad weather → extend flight time 1 min to 15%
        if random.random() < 0.25:
            max_ext = int(flight["scheduled_flight_minutes"] * 0.15)
            delay_minutes = random.randint(1, max(1, max_ext))
            reason = "Bad weather — extended flight time"

    elif day == 5:
        # Day 5: 20% of flights from airports above 40°N latitude get ground icing delay (10-45 min)
        if origin_lat > 40.0 and random.random() < 0.20:
            delay_minutes = random.randint(10, 45)
            reason = "Ground icing delay"

    elif day == 7:
        # Day 7: Strong jet stream — eastbound flights +12% time, westbound −12%, interpolated by heading
        heading = bearing_degrees(origin_lat, origin_lon, dest_lat, dest_lon)
        angle_from_east = math.radians(heading - 90)
        effect = 0.12 * math.cos(angle_from_east)
        # Positive cos → heading toward East → headwind → longer flight time
        delay_minutes = int(flight["scheduled_flight_minutes"] * effect)
        reason = f"Jet stream effect ({'+' if delay_minutes > 0 else ''}{delay_minutes} min)"

    elif day == 9:
        # 5% of flights: gate delay 5–90 min
        if random.random() < 0.05:
            delay_minutes = random.randint(5, 90)
            reason = "Gate delay"

    elif day == 11:
        # Day 11: Aircraft failure at a major hub — aircraft removed for full day
        # Handled at scheduler level; individual flights check aircraft_failed flag
        if flight.get("aircraft_failed", False):
            delay_minutes = 0
            reason = "Aircraft taken out of service — unscheduled maintenance"

    elif day == 13:
        # Day 13: 8% of flights originating west of 103°W longitude are cancelled; passengers must rebook
        if origin_lon < -103.0 and random.random() < 0.08:
            reason = "CANCELLED — weather west of 103°W"
            return {"delay_minutes": 0, "reason": reason, "cancelled": True}

    # delay_type: "departure" = plane departs late (Day 5 icing, Day 9 gate)
    #             "airtime"   = flight time changes, departure on schedule (Day 3 weather, Day 7 jet stream)
    delay_type = "departure"
    if day == 3 or day == 7:
        delay_type = "airtime"

    return {"delay_minutes": delay_minutes, "reason": reason, "cancelled": False, "delay_type": delay_type}

# Passenger Demand

def daily_demand(source_metro_M, dest_metro_M, all_airports_total_M,
                 market_share=0.02, travel_rate=0.005):
    """
    Number of passengers wanting to travel from source to dest on any given day.
    Spec: demand proportional to dest metro pop relative to all reachable airports
    (excluding source airport's metro population from the denominator).
    """
    reachable_total = all_airports_total_M - source_metro_M
    if reachable_total <= 0:
        return 0
    dest_share = dest_metro_M / reachable_total
    daily_travelers = source_metro_M * 1_000_000 * travel_rate * market_share
    return max(0, round(daily_travelers * dest_share))
