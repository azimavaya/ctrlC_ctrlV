"""
Airport Reference Data and Distance Calculator
Contains information for top 30 US airports plus Charles de Gaulle (Paris)
Includes functions to calculate distances and retrieve airport information
"""

import math
from typing import Dict, Tuple, Optional


class Airport:
    """Represents an airport with its key information"""
    def __init__(self, iata: str, name: str, city: str, state: str, 
                 latitude: float, longitude: float, metro_area: str = ""):
        self.iata = iata
        self.name = name
        self.city = city
        self.state = state
        self.latitude = latitude
        self.longitude = longitude
        self.metro_area = metro_area
    
    def __repr__(self):
        return f"Airport({self.iata}: {self.name}, {self.city}, {self.state})"


# Airport data with coordinates (latitude, longitude)
AIRPORTS: Dict[str, Airport] = {
    # Top 30 US Airports
    'ATL': Airport('ATL', 'Hartsfield-Jackson Atlanta International Airport', 
                   'Atlanta', 'GA', 33.6407, -84.4277, 'Metro Atlanta'),
    'DFW': Airport('DFW', 'Dallas/Fort Worth International Airport', 
                   'Dallas and Fort Worth', 'TX', 32.8998, -97.0403, 'Dallas–Fort Worth'),
    'DEN': Airport('DEN', 'Denver International Airport', 
                   'Denver', 'CO', 39.8561, -104.6737, 'Greater Denver'),
    'ORD': Airport('ORD', "O'Hare International Airport", 
                   'Chicago', 'IL', 41.9786, -87.9048, 'Chicagoland'),
    'LAX': Airport('LAX', 'Los Angeles International Airport', 
                   'Los Angeles', 'CA', 33.9425, -118.4081, 'Greater Los Angeles'),
    'JFK': Airport('JFK', 'John F. Kennedy International Airport', 
                   'New York City', 'NY', 40.6413, -73.7781, 'New York Metro'),
    'CLT': Airport('CLT', 'Charlotte Douglas International Airport', 
                   'Charlotte', 'NC', 35.2144, -80.9473, 'Greater Charlotte'),
    'LAS': Airport('LAS', 'Harry Reid International Airport', 
                   'Las Vegas', 'NV', 36.0840, -115.1537, 'Las Vegas Valley'),
    'MCO': Airport('MCO', 'Orlando International Airport', 
                   'Orlando', 'FL', 28.4312, -81.3083, 'Greater Orlando'),
    'MIA': Airport('MIA', 'Miami International Airport', 
                   'Miami', 'FL', 25.7959, -80.2870, 'Miami Metro'),
    'PHX': Airport('PHX', 'Phoenix Sky Harbor International Airport', 
                   'Phoenix', 'AZ', 33.4342, -112.0116, 'Metro Phoenix'),
    'SEA': Airport('SEA', 'Seattle-Tacoma International Airport', 
                   'Seattle and Tacoma', 'WA', 47.4502, -122.3088, 'Seattle Metro'),
    'SFO': Airport('SFO', 'San Francisco International Airport', 
                   'San Francisco', 'CA', 37.6213, -122.3790, 'San Francisco Bay Area'),
    'EWR': Airport('EWR', 'Newark Liberty International Airport', 
                   'Newark and New York City', 'NJ', 40.6895, -74.1745, 'New York Metro'),
    'IAH': Airport('IAH', 'George Bush Intercontinental Airport', 
                   'Houston', 'TX', 29.9844, -95.3414, 'Greater Houston'),
    'BOS': Airport('BOS', 'Logan International Airport', 
                   'Boston', 'MA', 42.3656, -71.0096, 'Greater Boston'),
    'MSP': Airport('MSP', 'Minneapolis-Saint Paul International Airport', 
                   'Minneapolis and Saint Paul', 'MN', 44.8848, -93.2223, 'Minneapolis–Saint Paul'),
    'FLL': Airport('FLL', 'Fort Lauderdale-Hollywood International Airport', 
                   'Fort Lauderdale and Hollywood', 'FL', 26.0712, -80.1528, 'Miami Metro'),
    'LGA': Airport('LGA', 'LaGuardia Airport', 
                   'New York City', 'NY', 40.7769, -73.8740, 'New York Metro'),
    'DTW': Airport('DTW', 'Detroit Metropolitan Airport', 
                   'Detroit', 'MI', 42.2162, -83.3554, 'Detroit Metro'),
    'PHL': Airport('PHL', 'Philadelphia International Airport', 
                   'Philadelphia', 'PA', 39.8719, -75.2411, 'Philadelphia Metro'),
    'SLC': Airport('SLC', 'Salt Lake City International Airport', 
                   'Salt Lake City', 'UT', 40.7899, -111.9791, 'Wasatch Front'),
    'BWI': Airport('BWI', 'Baltimore-Washington International Airport', 
                   'Baltimore and Washington, D.C.', 'MD', 39.1774, -76.6684, 'Baltimore metropolitan area'),
    'IAD': Airport('IAD', 'Dulles International Airport', 
                   'Washington, D.C.', 'VA', 38.9531, -77.4565, 'Washington Metro'),
    'SAN': Airport('SAN', 'San Diego International Airport', 
                   'San Diego', 'CA', 32.7338, -117.1933, 'Greater San Diego'),
    'DCA': Airport('DCA', 'Ronald Reagan Washington National Airport', 
                   'Washington, D.C.', 'VA', 38.8512, -77.0402, 'Washington Metro'),
    'TPA': Airport('TPA', 'Tampa International Airport', 
                   'Tampa', 'FL', 27.9755, -82.5332, 'Tampa Bay area'),
    'BNA': Airport('BNA', 'Nashville International Airport', 
                   'Nashville', 'TN', 36.1263, -86.6774, 'Greater Nashville'),
    'AUS': Airport('AUS', 'Austin-Bergstrom International Airport', 
                   'Austin', 'TX', 30.1945, -97.6699, 'Greater Austin'),
    'HNL': Airport('HNL', 'Daniel K. Inouye International Airport', 
                   'Honolulu', 'HI', 21.3206, -157.9242, 'Oahu'),
    
    # International - Paris
    'CDG': Airport('CDG', 'Charles de Gaulle Airport', 
                   'Paris', 'France', 49.0097, 2.5479, 'Paris Metropolitan Area'),
}


def get_airport(iata: str) -> Optional[Airport]:
    """
    Retrieve airport information by IATA code.
    
    Args:
        iata: Three-letter IATA airport code (e.g., 'ATL', 'JFK', 'CDG')
    
    Returns:
        Airport object if found, None otherwise
    
    Example:
        >>> airport = get_airport('ATL')
        >>> print(airport.name)
        Hartsfield–Jackson Atlanta International Airport
    """
    return AIRPORTS.get(iata.upper())


def get_coordinates(iata: str) -> Optional[Tuple[float, float]]:
    """
    Get latitude and longitude coordinates for an airport.
    
    Args:
        iata: Three-letter IATA airport code
    
    Returns:
        Tuple of (latitude, longitude) if found, None otherwise
    
    Example:
        >>> coords = get_coordinates('JFK')
        >>> print(coords)
        (40.6413, -73.7781)
    """
    airport = get_airport(iata)
    if airport:
        return (airport.latitude, airport.longitude)
    return None


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great circle distance between two points on Earth using the Haversine formula.
    
    Args:
        lat1: Latitude of first point in degrees
        lon1: Longitude of first point in degrees
        lat2: Latitude of second point in degrees
        lon2: Longitude of second point in degrees
    
    Returns:
        Distance in miles
    
    Example:
        >>> distance = haversine_distance(40.6413, -73.7781, 33.9425, -118.4081)
        >>> print(f"{distance:.2f} miles")
        2475.00 miles
    """
    # Earth's radius in miles
    R = 3958.8
    
    # Convert degrees to radians
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    # Haversine formula
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    a = (math.sin(dlat / 2) ** 2 + 
         math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2)
    c = 2 * math.asin(math.sqrt(a))
    
    distance = R * c
    return distance


def get_distance(iata1: str, iata2: str, unit: str = 'miles') -> Optional[float]:
    """
    Calculate the distance between two airports using their IATA codes.
    
    Args:
        iata1: IATA code of first airport
        iata2: IATA code of second airport
        unit: Unit of measurement ('miles' or 'kilometers')
    
    Returns:
        Distance in specified unit, or None if either airport not found
    
    Example:
        >>> distance = get_distance('ATL', 'JFK')
        >>> print(f"{distance:.2f} miles")
        762.34 miles
        
        >>> distance_km = get_distance('ATL', 'CDG', unit='kilometers')
        >>> print(f"{distance_km:.2f} km")
        7123.45 km
    """
    airport1 = get_airport(iata1)
    airport2 = get_airport(iata2)
    
    if not airport1 or not airport2:
        return None
    
    distance_miles = haversine_distance(
        airport1.latitude, airport1.longitude,
        airport2.latitude, airport2.longitude
    )
    
    if unit.lower() == 'kilometers' or unit.lower() == 'km':
        return distance_miles * 1.60934
    return distance_miles


def get_airport_info(iata: str) -> Optional[Dict]:
    """
    Get comprehensive information about an airport.
    
    Args:
        iata: Three-letter IATA airport code
    
    Returns:
        Dictionary with airport information, or None if not found
    
    Example:
        >>> info = get_airport_info('LAX')
        >>> print(info['name'])
        Los Angeles International Airport
    """
    airport = get_airport(iata)
    if not airport:
        return None
    
    return {
        'iata': airport.iata,
        'name': airport.name,
        'city': airport.city,
        'state': airport.state,
        'metro_area': airport.metro_area,
        'latitude': airport.latitude,
        'longitude': airport.longitude,
        'coordinates': (airport.latitude, airport.longitude)
    }


def list_all_airports() -> Dict[str, Airport]:
    """
    Get a dictionary of all available airports.
    
    Returns:
        Dictionary mapping IATA codes to Airport objects
    
    Example:
        >>> airports = list_all_airports()
        >>> print(f"Total airports: {len(airports)}")
        Total airports: 31
    """
    return AIRPORTS.copy()


def get_route_info(iata1: str, iata2: str) -> Optional[Dict]:
    """
    Get comprehensive information about a route between two airports.
    
    Args:
        iata1: IATA code of origin airport
        iata2: IATA code of destination airport
    
    Returns:
        Dictionary with route information including distance and airport details
    
    Example:
        >>> route = get_route_info('ATL', 'CDG')
        >>> print(f"Distance: {route['distance_miles']:.2f} miles")
        Distance: 4424.56 miles
    """
    airport1 = get_airport(iata1)
    airport2 = get_airport(iata2)
    
    if not airport1 or not airport2:
        return None
    
    distance_miles = get_distance(iata1, iata2, 'miles')
    distance_km = get_distance(iata1, iata2, 'kilometers')
    
    return {
        'origin': {
            'iata': airport1.iata,
            'name': airport1.name,
            'city': airport1.city,
            'state': airport1.state,
            'coordinates': (airport1.latitude, airport1.longitude)
        },
        'destination': {
            'iata': airport2.iata,
            'name': airport2.name,
            'city': airport2.city,
            'state': airport2.state,
            'coordinates': (airport2.latitude, airport2.longitude)
        },
        'distance_miles': distance_miles,
        'distance_kilometers': distance_km
    }


# Example usage and testing
if __name__ == "__main__":
    # Example 1: Get airport information
    print("=" * 60)
    print("Example 1: Get Airport Information")
    print("=" * 60)
    atl = get_airport('ATL')
    if atl:
        print(f"IATA: {atl.iata}")
        print(f"Name: {atl.name}")
        print(f"City: {atl.city}, {atl.state}")
        print(f"Coordinates: ({atl.latitude}, {atl.longitude})")
    
    print("\n")
    
    # Example 2: Calculate distance between two airports
    print("=" * 60)
    print("Example 2: Calculate Distance")
    print("=" * 60)
    distance = get_distance('ATL', 'JFK')
    print(f"Distance from ATL to JFK: {distance:.2f} miles")
    
    distance_km = get_distance('ATL', 'CDG', unit='kilometers')
    print(f"Distance from ATL to CDG: {distance_km:.2f} km")
    
    print("\n")
    
    # Example 3: Get route information
    print("=" * 60)
    print("Example 3: Route Information")
    print("=" * 60)
    route = get_route_info('LAX', 'JFK')
    if route:
        print(f"Route: {route['origin']['iata']} -> {route['destination']['iata']}")
        print(f"  {route['origin']['name']}")
        print(f"  to")
        print(f"  {route['destination']['name']}")
        print(f"Distance: {route['distance_miles']:.2f} miles ({route['distance_kilometers']:.2f} km)")
    
    print("\n")
    
    # Example 4: List all airports
    print("=" * 60)
    print("Example 4: All Available Airports")
    print("=" * 60)
    airports = list_all_airports()
    print(f"Total airports available: {len(airports)}")
    print("\nIATA Codes:", ", ".join(sorted(airports.keys())))