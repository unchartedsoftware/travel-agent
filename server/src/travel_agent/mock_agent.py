from datetime import datetime, timedelta
from typing import List, Dict, Any

def get_driving_route(origin: str, destination: str, departure_time: datetime) -> Dict[str, Any]:
    """Mock implementation that returns OpenRoute Service-like response."""
    # Create waypoints with OpenRoute Service coordinate format (longitude, latitude)
    waypoints = [
        {
            'name': origin,
            'coords': [-79.3832, 43.6532],  # Toronto (longitude, latitude)
            'time': departure_time
        },
        {
            'name': 'Detroit, USA',
            'coords': [-83.0458, 42.3314],  # Detroit (longitude, latitude)
            'time': departure_time + timedelta(hours=2.5)
        },
        {
            'name': destination,
            'coords': [-87.6298, 41.8781],  # Chicago (longitude, latitude)
            'time': departure_time + timedelta(hours=5)
        }
    ]

    # Create segments in OpenRoute Service format
    segments = [{
        'distance': 500000,  # 500 km in meters
        'duration': 18000,   # 5 hours in seconds
    }]

    # Create mock route geometry
    geometry = {
        'coordinates': [wp['coords'] for wp in waypoints],
        'type': 'LineString'
    }

    route = {
        'type': 'Feature',
        'geometry': geometry,
        'segments': segments,
        'legs': []  # Keep legs for backward compatibility
    }

    # Add legs for backward compatibility with existing frontend code
    for i in range(len(waypoints) - 1):
        leg = {
            'distance': {'text': '250 km'},
            'duration': {'text': '2.5 hours'},
            'start_address': waypoints[i]['name'],
            'end_address': waypoints[i + 1]['name'],
            'arrival_time': waypoints[i + 1]['time'].isoformat(),
            'start_location': {'lat': waypoints[i]['coords'][1], 'lng': waypoints[i]['coords'][0]},
            'end_location': {'lat': waypoints[i + 1]['coords'][1], 'lng': waypoints[i + 1]['coords'][0]}
        }
        route['legs'].append(leg)

    return {
        'route': route,
        'estimated_arrival_time': departure_time + timedelta(hours=5),
        'total_duration': 18000,  # 5 hours in seconds
        'route_summary': f"Drive from {origin} to {destination}. The total distance is 500 km and the estimated travel time is 5 hours."
    }

def get_weather_forecast(latitude: float, longitude: float, time: datetime) -> Dict[str, Any]:
    """Mock implementation that returns weather based on location."""
    # Return different weather based on latitude to simulate different conditions
    if latitude > 42:  # More northern locations
        return {
            'dt': int(time.timestamp()),
            'weather': [{'description': 'light snow'}],
            'main': {'temp': -2},
            'wind': {'speed': 12},
            'location': {'latitude': latitude, 'longitude': longitude}
        }
    else:  # More southern locations
        return {
            'dt': int(time.timestamp()),
            'weather': [{'description': 'partly cloudy'}],
            'main': {'temp': 15},
            'wind': {'speed': 8},
            'location': {'latitude': latitude, 'longitude': longitude}
        }

def analyze_weather_conditions(weather_data: List[Dict[str, Any]]) -> List[str]:
    """Mock implementation that analyzes weather conditions with enhanced criteria."""
    hazards = []
    for data in weather_data:
        weather = data.get('weather', [{}])[0]
        temperature = data.get('main', {}).get('temp', 0)
        wind_speed = data.get('wind', {}).get('speed', 0)
        time = datetime.utcfromtimestamp(data['dt'])

        description = weather.get('description', '').lower()
        if "snow" in description or "sleet" in description:
            hazards.append(f"Snow/Sleet at {time.strftime('%Y-%m-%d %H:%M')}")
        elif "heavy rain" in description:
            hazards.append(f"Heavy Rain at {time.strftime('%Y-%m-%d %H:%M')}")
        elif "fog" in description:
            hazards.append(f"Fog at {time.strftime('%Y-%m-%d %H:%M')}")
        elif temperature < 0:
            hazards.append(f"Freezing Temperatures ({temperature}°C) at {time.strftime('%Y-%m-%d %H:%M')}")
        elif wind_speed > 15:  # Updated threshold to match agent.py
            hazards.append(f"Strong Winds ({wind_speed} m/s) at {time.strftime('%Y-%m-%d %H:%M')}")

    return hazards

def get_weather_along_route(route: Dict[str, Any], departure_time: datetime) -> List[Dict[str, Any]]:
    """Mock implementation that returns weather data along the route."""
    weather_data = []
    coordinates = route.get('geometry', {}).get('coordinates', [])
    total_duration = route.get('segments', [{}])[0].get('duration', 18000)  # Default 5 hours
    
    num_points = 5  # Sample 5 points along the route
    time_increment = total_duration / (num_points + 1)

    current_time = departure_time
    for i in range(1, num_points + 1):
        point_time = current_time + timedelta(seconds=time_increment * i)
        
        # Get coordinate for this point
        point_index = int(len(coordinates) * i / (num_points + 1))
        if point_index >= len(coordinates):
            point_index = len(coordinates) - 1
        
        # OpenRoute Service uses [longitude, latitude]
        lng, lat = coordinates[point_index]
        
        weather = get_weather_forecast(lat, lng, point_time)
        if weather:
            weather['location'] = {'latitude': lat, 'longitude': lng}
            weather_data.append(weather)

    return weather_data

def suggest_departure_time(route: Dict[str, Any], weather_data: List[Dict[str, Any]], 
                         departure_time: datetime) -> datetime:
    """Mock implementation that suggests an optimal departure time."""
    # For mock data, suggest 2 hours later if there are hazards
    hazards = analyze_weather_conditions(weather_data)
    if hazards:
        return departure_time + timedelta(hours=2)
    return departure_time

def generate_itinerary_with_llm(origin: str, destination: str, departure_time_str: str) -> str:
    """Mock implementation that generates a simple itinerary."""
    try:
        departure_time = datetime.fromisoformat(departure_time_str)
        arrival_time = departure_time + timedelta(hours=5)
        
        return f"""Here's your travel itinerary from {origin} to {destination}:

Departure: {departure_time.strftime('%Y-%m-%d %H:%M')}
Estimated Arrival: {arrival_time.strftime('%Y-%m-%d %H:%M')}
Duration: 5 hours

Weather Conditions:
- {origin}: Light snow, -2°C
- {destination}: Partly cloudy, 15°C

Route Summary:
Drive south from {origin} to {destination}. The route is mostly highway driving.
Take regular breaks and watch for changing weather conditions."""
    except ValueError:
        return "Invalid departure time format. Please use ISO format (YYYY-MM-DDTHH:MM:SS)."
