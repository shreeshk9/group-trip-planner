"""
Route optimization: Find the best order to visit cities.
"""

import math
from itertools import permutations

def calculate_distance(lat1, lon1, lat2, lon2):
    """
    Calculate distance between two coordinates using Haversine formula.
    
    Returns distance in kilometers.
    
    Why Haversine?
    - Earth is a sphere, not flat
    - Gives actual travel distance (not straight line through earth)
    - Standard formula for geo-distance
    
    Math: 
    - Convert lat/lon to radians
    - Apply spherical trigonometry
    - Multiply by Earth's radius
    """
    # Earth's radius in kilometers
    R = 6371
    
    # Convert degrees to radians
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    
    # Haversine formula
    a = (math.sin(delta_lat / 2) ** 2 +
         math.cos(lat1_rad) * math.cos(lat2_rad) *
         math.sin(delta_lon / 2) ** 2)
    
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    distance = R * c
    
    return distance

def calculate_route_distance(cities_order, cities_database):
    """
    Calculate total distance for a specific route.
    
    Example: ["Jaipur", "Udaipur", "Jodhpur"]
    - Distance = Jaipur→Udaipur + Udaipur→Jodhpur
    
    Returns: Total distance in km
    """
    total_distance = 0
    
    for i in range(len(cities_order) - 1):
        city1 = cities_order[i]
        city2 = cities_order[i + 1]
        
        # Get coordinates
        loc1 = cities_database[city1]['location']
        loc2 = cities_database[city2]['location']
        
        # Calculate distance between consecutive cities
        dist = calculate_distance(loc1['lat'], loc1['lon'],
                                  loc2['lat'], loc2['lon'])
        
        total_distance += dist
    
    return total_distance

def optimize_route(cities_list, cities_database):
    """
    Find the best order to visit cities (minimize total travel distance).
    
    Approach: Brute force for small N (≤7 cities)
    - Try all possible orderings
    - Calculate distance for each
    - Pick shortest
    
    Why brute force?
    - N! permutations (3 cities = 6, 4 cities = 24, 5 cities = 120)
    - For small N, brute force is fast and guarantees optimal solution
    - Alternative: TSP algorithms (overkill for our use case)
    
    For larger N (>7), we'd use heuristics like nearest neighbor or genetic algorithm.
    But our trips are 2-4 cities, so brute force is perfect.
    
    Returns: (optimized_order, total_distance, distance_matrix)
    """
    if len(cities_list) <= 1:
        return cities_list, 0, {}
    
    # For 2 cities, no optimization needed (only one route)
    if len(cities_list) == 2:
        distance = calculate_route_distance(cities_list, cities_database)
        distance_matrix = {
            f"{cities_list[0]}-{cities_list[1]}": round(distance, 1)
        }
        return cities_list, round(distance, 1), distance_matrix
    
    # For 3+ cities, try all permutations
    best_route = None
    best_distance = float('inf')
    
    # Try all possible orderings
    for route in permutations(cities_list):
        route = list(route)
        distance = calculate_route_distance(route, cities_database)
        
        if distance < best_distance:
            best_distance = distance
            best_route = route
    
    # Build distance matrix (shows distance between each pair of cities)
    distance_matrix = {}
    for i in range(len(best_route) - 1):
        city1 = best_route[i]
        city2 = best_route[i + 1]
        
        loc1 = cities_database[city1]['location']
        loc2 = cities_database[city2]['location']
        
        dist = calculate_distance(loc1['lat'], loc1['lon'],
                                  loc2['lat'], loc2['lon'])
        
        distance_matrix[f"{city1}-{city2}"] = round(dist, 1)
    
    return best_route, round(best_distance, 1), distance_matrix

def estimate_travel_time(distance_km, transport_mode="car"):
    """
    Estimate travel time based on distance and transport mode.
    
    Average speeds:
    - Car: 60 km/h (accounting for traffic, stops)
    - Train: 80 km/h (faster but includes station time)
    - Flight: Only for >500km, assume 2 hours door-to-door
    
    Returns: Travel time in hours (rounded to 1 decimal)
    
    Why these speeds?
    - Not highway speeds (accounting for realistic conditions)
    - Includes buffer for breaks, delays
    - India-specific (traffic, road conditions)
    """
    if distance_km > 500:
        # Long distance = flight recommended
        return 2.0  # Assume fixed 2 hours door-to-door for flights
    elif distance_km > 200:
        # Medium distance = train preferred
        avg_speed = 80  # km/h
        return round(distance_km / avg_speed, 1)
    else:
        # Short distance = car/taxi
        avg_speed = 60  # km/h
        return round(distance_km / avg_speed, 1)

def get_recommended_transport(distance_km):
    """
    Recommend transport mode based on distance.
    
    Logic:
    - <100 km: Car/Taxi (convenient, flexible)
    - 100-300 km: Car or Train (both viable)
    - 300-500 km: Train (comfortable, reliable)
    - >500 km: Flight (time-efficient)
    
    Returns: Transport mode as string
    """
    if distance_km < 100:
        return "Car/Taxi"
    elif distance_km < 300:
        return "Car or Train"
    elif distance_km < 500:
        return "Train"
    else:
        return "Flight"

def create_travel_plan(cities_order, cities_database):
    """
    Create detailed travel plan with timings and transport recommendations.
    
    Returns: List of travel segments with details
    
    Example output:
    [
        {
            "from": "Jaipur",
            "to": "Udaipur", 
            "distance_km": 395,
            "travel_time_hours": 6.5,
            "transport": "Train",
            "cost_estimate": 2000
        },
        ...
    ]
    """
    travel_plan = []
    
    for i in range(len(cities_order) - 1):
        city1 = cities_order[i]
        city2 = cities_order[i + 1]
        
        # Calculate distance
        loc1 = cities_database[city1]['location']
        loc2 = cities_database[city2]['location']
        distance = calculate_distance(loc1['lat'], loc1['lon'],
                                     loc2['lat'], loc2['lon'])
        
        # Estimate time and transport
        travel_time = estimate_travel_time(distance)
        transport = get_recommended_transport(distance)
        
        # Estimate cost (rough estimates in ₹)
        if "Flight" in transport:
            cost = 4000
        elif "Train" in transport:
            cost = 1500
        else:
            cost = int(distance * 10)  # ₹10 per km for car
        
        travel_plan.append({
            "from": city1,
            "to": city2,
            "distance_km": round(distance, 1),
            "travel_time_hours": travel_time,
            "transport": transport,
            "cost_estimate": cost
        })
    
    return travel_plan