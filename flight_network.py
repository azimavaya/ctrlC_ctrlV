"""
Panther Cloud Air Flight Network Generator
Determines optimal hubs and generates all possible flights for the airline network.
Only includes flights >= 150 miles apart.
"""

from airport_reference import AIRPORTS, get_distance, get_airport
from typing import List, Dict, Tuple, Set
import json


# Top 30 US Airports (excluding CDG for hub selection)
US_AIRPORTS = [
    'ATL', 'DFW', 'DEN', 'ORD', 'LAX', 'JFK', 'CLT', 'LAS', 'MCO', 'MIA',
    'PHX', 'SEA', 'SFO', 'EWR', 'IAH', 'BOS', 'MSP', 'FLL', 'LGA', 'DTW',
    'PHL', 'SLC', 'BWI', 'IAD', 'SAN', 'DCA', 'TPA', 'BNA', 'AUS', 'HNL'
]

# Selected 4 Major Hubs based on:
# 1. Geographic distribution (covering all regions)
# 2. High passenger volume
# 3. Strategic location for connections
# 4. Maximizing profit and passenger convenience
MAJOR_HUBS = ['ATL', 'DFW', 'DEN', 'ORD']

# Rationale:
# ATL (Atlanta) - Southeast hub, highest passenger volume, central to East Coast
# DFW (Dallas) - Central US hub, high volume, excellent for cross-country connections
# DEN (Denver) - Mountain/West hub, high volume, central location for West Coast
# ORD (Chicago) - Midwest/Northeast hub, high volume, excellent for northern routes


class Flight:
    """Represents a flight route"""
    def __init__(self, origin: str, destination: str, distance: float, 
                 is_direct: bool = True, via_hub: str = None):
        self.origin = origin
        self.destination = destination
        self.distance = distance
        self.is_direct = is_direct
        self.via_hub = via_hub  # If not direct, which hub it goes through
    
    def __repr__(self):
        if self.is_direct:
            return f"Flight({self.origin} -> {self.destination}, {self.distance:.2f} miles)"
        else:
            return f"Flight({self.origin} -> {self.destination} via {self.via_hub}, {self.distance:.2f} miles)"
    
    def to_dict(self):
        return {
            'origin': self.origin,
            'destination': self.destination,
            'distance_miles': round(self.distance, 2),
            'is_direct': self.is_direct,
            'via_hub': self.via_hub
        }


def calculate_minimum_distance_through_hubs(origin: str, destination: str, 
                                          hubs: List[str]) -> Tuple[float, str]:
    """
    Calculate the minimum distance from origin to destination through any hub.
    
    Returns:
        Tuple of (minimum_distance, hub_used)
    """
    min_distance = float('inf')
    best_hub = None
    
    for hub in hubs:
        if hub == origin or hub == destination:
            continue
        
        dist1 = get_distance(origin, hub)
        dist2 = get_distance(hub, destination)
        
        if dist1 and dist2:
            total_distance = dist1 + dist2
            if total_distance < min_distance:
                min_distance = total_distance
                best_hub = hub
    
    return min_distance, best_hub


def should_create_direct_flight(origin: str, destination: str, 
                                 direct_distance: float, hubs: List[str]) -> bool:
    """
    Determine if a direct flight should be created based on:
    1. Distance must be >= 150 miles
    2. Direct flight should be more efficient than going through hubs
    """
    if direct_distance < 150:
        return False
    
    # Calculate minimum distance through hubs
    hub_distance, _ = calculate_minimum_distance_through_hubs(origin, destination, hubs)
    
    # Create direct flight if:
    # - It's within 20% of the hub route distance (efficiency threshold)
    # - Or if it's a short-medium distance route (< 1000 miles)
    if direct_distance < 1000:
        return True
    
    # For longer routes, only create direct if significantly shorter
    efficiency_ratio = direct_distance / hub_distance if hub_distance > 0 else 1.0
    return efficiency_ratio <= 0.85  # Direct must be at least 15% shorter


def generate_flight_network() -> List[Flight]:
    """
    Generate the complete flight network for Panther Cloud Air.
    
    Strategy:
    1. All airports connect to all 4 hubs (hub connections)
    2. Hubs connect to each other (hub-to-hub)
    3. Direct flights between airports where it makes sense (efficiency)
    4. No flights less than 150 miles
    """
    flights: List[Flight] = []
    processed_pairs: Set[Tuple[str, str]] = set()
    
    # 1. Create hub-to-hub connections (all hubs connect to each other)
    print("Creating hub-to-hub connections...")
    for i, hub1 in enumerate(MAJOR_HUBS):
        for hub2 in MAJOR_HUBS[i+1:]:
            distance = get_distance(hub1, hub2)
            if distance and distance >= 150:
                flights.append(Flight(hub1, hub2, distance, is_direct=True))
                processed_pairs.add((hub1, hub2))
                processed_pairs.add((hub2, hub1))
                print(f"  Hub connection: {hub1} <-> {hub2} ({distance:.2f} miles)")
    
    # 2. Connect all airports to all hubs
    print("\nCreating airport-to-hub connections...")
    for airport in US_AIRPORTS:
        if airport in MAJOR_HUBS:
            continue  # Skip if airport is itself a hub
        
        for hub in MAJOR_HUBS:
            distance = get_distance(airport, hub)
            if distance and distance >= 150:
                flights.append(Flight(airport, hub, distance, is_direct=True))
                flights.append(Flight(hub, airport, distance, is_direct=True))
                processed_pairs.add((airport, hub))
                processed_pairs.add((hub, airport))
    
    print(f"  Created {len([f for f in flights if f.origin not in MAJOR_HUBS or f.destination not in MAJOR_HUBS])} airport-hub connections")
    
    # 3. Create direct flights between non-hub airports where efficient
    print("\nAnalyzing direct flight opportunities...")
    direct_flights_created = 0
    
    for i, origin in enumerate(US_AIRPORTS):
        for destination in US_AIRPORTS[i+1:]:
            # Skip if already processed
            if (origin, destination) in processed_pairs:
                continue
            
            # Skip if both are hubs (already handled)
            if origin in MAJOR_HUBS and destination in MAJOR_HUBS:
                continue
            
            # Skip if one is a hub (already handled)
            if origin in MAJOR_HUBS or destination in MAJOR_HUBS:
                continue
            
            direct_distance = get_distance(origin, destination)
            
            if direct_distance and direct_distance >= 150:
                if should_create_direct_flight(origin, destination, direct_distance, MAJOR_HUBS):
                    flights.append(Flight(origin, destination, direct_distance, is_direct=True))
                    flights.append(Flight(destination, origin, direct_distance, is_direct=True))
                    processed_pairs.add((origin, destination))
                    processed_pairs.add((destination, origin))
                    direct_flights_created += 1
                    print(f"  Direct: {origin} <-> {destination} ({direct_distance:.2f} miles)")
    
    print(f"\nCreated {direct_flights_created} direct flight pairs")
    
    return flights


def get_route_options(origin: str, destination: str, flights: List[Flight]) -> List[Dict]:
    """
    Get all possible route options from origin to destination.
    Returns direct flights and hub-connection options.
    """
    options = []
    
    # Check for direct flight
    direct_flights = [f for f in flights 
                     if f.origin == origin and f.destination == destination and f.is_direct]
    if direct_flights:
        options.append({
            'type': 'direct',
            'route': [origin, destination],
            'distance': direct_flights[0].distance,
            'stops': 0
        })
    
    # Check for routes through hubs
    for hub in MAJOR_HUBS:
        if hub == origin or hub == destination:
            continue
        
        leg1 = [f for f in flights if f.origin == origin and f.destination == hub]
        leg2 = [f for f in flights if f.origin == hub and f.destination == destination]
        
        if leg1 and leg2:
            total_distance = leg1[0].distance + leg2[0].distance
            options.append({
                'type': 'hub_connection',
                'route': [origin, hub, destination],
                'distance': total_distance,
                'stops': 1,
                'hub': hub
            })
    
    # Sort by distance (shortest first)
    options.sort(key=lambda x: x['distance'])
    return options


def verify_network_constraints(flights: List[Flight]) -> Tuple[bool, List[str]]:
    """
    Verify that all flights meet the minimum distance requirement (>= 150 miles).
    Returns (all_valid, list_of_violations)
    """
    violations = []
    for flight in flights:
        if flight.distance < 150:
            violations.append(f"{flight.origin} -> {flight.destination}: {flight.distance:.2f} miles")
    
    return len(violations) == 0, violations


def analyze_network_statistics(flights: List[Flight]) -> Dict:
    """Analyze and return statistics about the flight network"""
    direct_flights = [f for f in flights if f.is_direct]
    hub_connections = len([f for f in flights if f.origin in MAJOR_HUBS or f.destination in MAJOR_HUBS])
    
    total_distance = sum(f.distance for f in flights)
    avg_distance = total_distance / len(flights) if flights else 0
    
    # Count unique airport pairs
    unique_pairs = set()
    for flight in flights:
        pair = tuple(sorted([flight.origin, flight.destination]))
        unique_pairs.add(pair)
    
    return {
        'total_flights': len(flights),
        'unique_routes': len(unique_pairs),
        'direct_flights': len(direct_flights),
        'hub_connections': hub_connections,
        'total_network_distance': round(total_distance, 2),
        'average_flight_distance': round(avg_distance, 2),
        'hubs': MAJOR_HUBS,
        'airports_served': len(US_AIRPORTS)
    }


def save_flight_network(flights: List[Flight], filename: str = 'flight_network.json'):
    """Save flight network to JSON file"""
    network_data = {
        'hubs': MAJOR_HUBS,
        'airports': US_AIRPORTS,
        'flights': [flight.to_dict() for flight in flights],
        'statistics': analyze_network_statistics(flights)
    }
    
    with open(filename, 'w') as f:
        json.dump(network_data, f, indent=2)
    
    print(f"\nFlight network saved to {filename}")


if __name__ == "__main__":
    print("=" * 70)
    print("Panther Cloud Air - Flight Network Generator")
    print("=" * 70)
    
    print(f"\nSelected Major Hubs: {', '.join(MAJOR_HUBS)}")
    print("\nHub Details:")
    for hub in MAJOR_HUBS:
        airport = get_airport(hub)
        if airport:
            print(f"  {hub}: {airport.name}, {airport.city}, {airport.state}")
    
    print("\n" + "=" * 70)
    print("Generating Flight Network...")
    print("=" * 70)
    
    # Generate flight network
    all_flights = generate_flight_network()
    
    # Verify network constraints
    print("\n" + "=" * 70)
    print("Verifying Network Constraints")
    print("=" * 70)
    is_valid, violations = verify_network_constraints(all_flights)
    if is_valid:
        print("[OK] All flights meet minimum distance requirement (>= 150 miles)")
    else:
        print(f"[ERROR] Found {len(violations)} violations:")
        for violation in violations:
            print(f"  - {violation}")
    
    # Analyze network
    print("\n" + "=" * 70)
    print("Network Statistics")
    print("=" * 70)
    stats = analyze_network_statistics(all_flights)
    for key, value in stats.items():
        if key != 'hubs':
            print(f"{key.replace('_', ' ').title()}: {value}")
    
    # Example route queries
    print("\n" + "=" * 70)
    print("Example Route Queries")
    print("=" * 70)
    
    test_routes = [
        ('LAX', 'JFK'),
        ('MIA', 'SEA'),
        ('BOS', 'SAN'),
        ('HNL', 'ATL'),
        ('CLT', 'PHX')
    ]
    
    for origin, destination in test_routes:
        print(f"\nRoutes from {origin} to {destination}:")
        options = get_route_options(origin, destination, all_flights)
        for i, option in enumerate(options[:3], 1):  # Show top 3 options
            route_str = " -> ".join(option['route'])
            print(f"  Option {i}: {route_str} ({option['distance']:.2f} miles, {option['stops']} stop(s))")
    
    # Save to file
    save_flight_network(all_flights)
    
    print("\n" + "=" * 70)
    print("Flight Network Generation Complete!")
    print("=" * 70)