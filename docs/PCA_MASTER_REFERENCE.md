# Panther Cloud Air (PCA) — Master Reference
**CSC 4710 Software Engineering | Spring 2026**

---

## 1. Network Overview

| Item | Value |
|---|---|
| **Airline** | Panther Cloud Air (PCA), prefix CA |
| **Airports** | 31 (30 US + Paris CDG) |
| **Aircraft** | 56 (55 original + 1 A350-900) |
| **Hubs** | 4 — ATL, ORD, DFW, LAX |
| **Valid Routes** | 455 unique pairs / 910 directional (min 150 mi) |
| **Fuel (US)** | $6.19/gal (1-year contract) |
| **Fuel (Paris)** | €1.97/liter |
| **Airport Fee (US)** | $2,000 per take-off + $2,000 per landing |
| **Paris Fees** | €2,100 per take-off + €2,100 per landing |
| **Operating Hours** | 05:00–01:00 local (domestic) |

---

## 2. Airport Directory

| # | IATA | City | Metro Pop (M) | Gates | Hub | Taxi (min) | Timezone |
|---|---|---|---|---|---|---|---|
| 1 | **ATL** | Atlanta | 6.14 | **11** | Yes | 15 | America/New_York |
| 2 | **LAX** | Los Angeles | 13.20 | **11** | Yes | 17 | America/Los_Angeles |
| 3 | **ORD** | Chicago O'Hare | 9.46 | **11** | Yes | 15 | America/Chicago |
| 4 | **DFW** | Dallas/Fort Worth | 7.76 | **11** | Yes | 15 | America/Chicago |
| 5 | DEN | Denver | 2.93 | 3 | — | 13 | America/Denver |
| 6 | JFK | New York JFK | 20.14 | 5 | — | 13 | America/New_York |
| 7 | SFO | San Francisco | 4.75 | 5 | — | 13 | America/Los_Angeles |
| 8 | SEA | Seattle | 4.02 | 4 | — | 13 | America/Los_Angeles |
| 9 | LAS | Las Vegas | 2.23 | 2 | — | 13 | America/Los_Angeles |
| 10 | MCO | Orlando | 2.67 | 3 | — | 13 | America/New_York |
| 11 | MIA | Miami | 6.17 | 5 | — | 13 | America/New_York |
| 12 | CLT | Charlotte | 2.67 | 3 | — | 13 | America/New_York |
| 13 | PHX | Phoenix | 4.95 | 5 | — | 13 | America/Phoenix |
| 14 | IAH | Houston | 7.34 | 5 | — | 13 | America/Chicago |
| 15 | BOS | Boston | 4.87 | 5 | — | 13 | America/New_York |
| 16 | MSP | Minneapolis | 3.65 | 4 | — | 13 | America/Chicago |
| 17 | FLL | Fort Lauderdale | 1.95 | 2 | — | 13 | America/New_York |
| 18 | DTW | Detroit | 4.37 | 4 | — | 13 | America/New_York |
| 19 | PHL | Philadelphia | 6.23 | 5 | — | 13 | America/New_York |
| 20 | LGA | New York LaGuardia | 20.14 | 5 | — | 13 | America/New_York |
| 21 | MDW | Chicago Midway | 9.46 | 5 | — | 13 | America/Chicago |
| 22 | BWI | Baltimore | 9.97 | 5 | — | 13 | America/New_York |
| 23 | SLC | Salt Lake City | 1.26 | 1 | — | 9 | America/Denver |
| 24 | DCA | Washington Reagan | 9.97 | 5 | — | 13 | America/New_York |
| 25 | SAN | San Diego | 3.34 | 3 | — | 13 | America/Los_Angeles |
| 26 | MCI | Kansas City | 2.22 | 2 | — | 13 | America/Chicago |
| 27 | STL | St. Louis | 2.81 | 3 | — | 13 | America/Chicago |
| 28 | HNL | Honolulu | 0.98 | 1 | — | 7 | Pacific/Honolulu |
| 29 | PDX | Portland | 2.51 | 3 | — | 13 | America/Los_Angeles |
| 30 | BNA | Nashville | 2.01 | 2 | — | 13 | America/Chicago |
| 31 | CDG | Paris | 12.20 | 5 | — | — | Europe/Paris |

**Gate formula:** `min(5, round(metro_pop_M))` for non-hubs; hubs get 11. Rounding uses
standard rounding (0.5 rounds up, so 0.98M = 1 gate, 1.95M = 2 gates).
**Taxi (non-hub):** `min(13, metro_pop * 0.0000075)` minutes.
**Taxi (hub):** `min(20, 15 + floor((metro_pop_M - 9) / 2))` minutes.

---

## 3. Fleet

| Type | Mfg | Speed (max/op) | Capacity | Range (km) | Fuel Burn (L/hr) | Lease/mo |
|---|---|---|---|---|---|---|
| 737-600 | Boeing | 876/701 km/h | 119 | 5,648 | 2,800 | $245,000 |
| 737-800 | Boeing | 876/701 km/h | 162 | 5,765 | 2,900 | $270,000 |
| A200-100 | Airbus | 871/697 km/h | 120 | 5,627 | 2,600 | $192,000 |
| A220-300 | Airbus | 871/697 km/h | 149 | 6,300 | 2,700 | $228,000 |
| **A350-900** | Airbus | 910/728 km/h | 300 | 15,000 | 7,200 | $1,200,000 |

**Fleet count:** 15x 737-600, 15x 737-800, 12x A200-100, 13x A220-300, 1x A350-900 = **56 total**
**Monthly lease total:** $14,193,000
**Maintenance:** Every 200 flight hours, 1.5 days, hub airports only, max 3 per hub.


---

## 4. Key Formulas

```
# Flight time
op_speed = max_speed * 0.80
wind_factor = -0.045 * sin(heading_radians)
flight_time = (distance_km / op_speed) * (1 + wind_factor)

# Passenger demand (A → B)
demand = pop_A * 0.005 * 0.02 * (pop_B / sum_reachable_pop)

# Fare (30% load break-even)
fare = (fuel_cost + landing_fees + lease_share) / (capacity * 0.30)
```

**Cruising altitudes:** International=38k ft, ≥1500mi=35k, <1500=30k, <350=25k, <200=20k ft.
**Turnaround:** 40 min standard, 50 min with refueling.
**Transit connection:** 30 min minimum.

---

## 5. Excluded Routes (< 150 mi)

JFK↔LGA (10.6), ORD↔MDW (15.2), MIA↔FLL (20.9), BWI↔DCA (30.0), PHL↔BWI (90.0), JFK↔PHL (93.7), PHL↔LGA (95.4), LAX↔SAN (109.0), PHL↔DCA (119.2), SEA↔PDX (129.3)

---

## 6. Paris (CDG) Service

- **Aircraft:** N350CA (A350-900), dedicated JFK↔CDG
- **CA001:** JFK→CDG, departs 18:00 EDT (22:00 UTC), arrives ~07:49 CET+1
- **CA002:** CDG→JFK, departs ~08:39 CET (after 50 min turnaround), arrives ~13:08 EDT
- **Paris fees:** €2,100 per T/O + €2,100 per landing, fuel at €1.97/L
- **Exchange rate:** Hardcoded at 1.08 USD/EUR (xe.com Jan 31, 2026 rate per spec)
- **DST:** France last-Sun-Mar to last-Sun-Oct; US 2nd-Sun-Mar to 1st-Sun-Nov

---

## 7. Simulation Challenges (14 Days)

| Day | Challenge |
|---|---|
| 1 | Baseline timetable |
| 2,4,6,8,10,12,14 | No delays — aircraft start where they ended |
| 3 | 25% flights: weather delay +1 min to +15% flight time |
| 5 | 20% of flights from airports >40°N: icing delay 10–45 min |
| 7 | Jet stream: eastbound +12%, westbound −12%, interpolated |
| 9 | 5% of flights: gate delay 5–90 min |
| 11 | Aircraft failure at a hub — out of service all day |
| 13 | 8% flights from airports west of 103°W cancelled, rebook passengers |

**>40°N airports:** BOS, JFK, LGA, ORD, MDW, MSP, DTW, SLC, SEA, PDX, CDG
**West of 103°W:** LAX, SFO, SEA, LAS, PDX, SLC, PHX, DEN, SAN, HNL

---

## 8. Web Application

| Page | Path | Access | Purpose |
|---|---|---|---|
| Login | `/login` | Public | Authentication |
| Home | `/` | All | Live flight stats, dashboard |
| Timetable | `/timetable` | All | Full daily schedule with timezone toggle |
| Book Flight | `/book` | All | Search + book direct/connecting flights |
| My Bookings | `/bookings` | All | View/manage personal bookings |
| Simulation | `/simulation` | Admin | Run 14-day simulation |
| Finances | `/finances` | Admin | Revenue/cost/profit breakdown |
| Admin | `/admin` | Admin | Users, aircraft, airports management |

---