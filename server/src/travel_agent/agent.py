import requests
from datetime import datetime, timedelta, timezone
from typing import List, Tuple, Dict, Optional, Any
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent
from langgraph.prebuilt.chat_agent_executor import AgentState
from dotenv import load_dotenv  # Added import
import json
import os  # Added import
import openrouteservice

from typing import Literal


# Load environment variables from .env file
load_dotenv()  # Added line

# API Keys (Loaded from .env file)
OPENWEATHERMAP_API_KEY = os.getenv("OPENWEATHERMAP_API_KEY")  # Updated line
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")  # Updated line
OPENROUTE_SERVICE_API_KEY = os.getenv("OPENROUTE_SERVICE_API_KEY")  # Updated line

# Initialize LLM for LangChain
model = ChatOpenAI(model_name="gpt-3.5-turbo", openai_api_key=OPENAI_API_KEY)  # Or any other LLM you prefer

# @tool
def get_driving_route(stops: List[str], departure_time: datetime) -> Dict[str, Any]:
    """
    Gets driving directions and route information from OpenRoute Service API for multiple stops.

    Args:
        stops: A list of addresses representing the stops in the route.  The first address is the origin,
               and the last address is the destination, with any intermediate stops in between.
        departure_time: The departure time as a datetime object.

    Returns:
        A dictionary containing:
            - 'route': The detailed route information from OpenRoute Service.
            - 'estimated_arrival_time': The estimated arrival time as a datetime object in UTC.
            - 'total_duration': The total travel time in seconds.
            - 'route_summary': A human-readable summary of the route.
            - 'waypoints': A list of dictionaries, where each dictionary contains the geocoded
                          coordinates (longitude and latitude) for each stop.
    """
    if not stops:
        return {}

    # Geocode all stops
    geocode_url = "https://api.openrouteservice.org/geocode/search"
    headers = {"Accept": "application/json, application/geo+json; charset=utf-8"}
    waypoints = []
    coordinates = []

    for stop in stops:
        geocode_params = {
            "api_key": OPENROUTE_SERVICE_API_KEY,
            "text": stop,
        }
        try:
            response = requests.get(geocode_url, headers=headers, params=geocode_params)
            response.raise_for_status()
            data = response.json()
            if data and data['features']:
                coordinates.append(data['features'][0]['geometry']['coordinates'])
                waypoints.append({
                    'address': stop,
                    'coordinates': data['features'][0]['geometry']['coordinates']  # [longitude, latitude]
                })
            else:
                print(f"Geocoding failed for stop: {stop}")
                return {} # Return empty dict if any geocoding fails.  Consider alternative error handling.

        except requests.exceptions.RequestException as e:
            print(f"Error during geocoding for stop {stop}: {e}")
            return {}
        except KeyError as e:
            print(f"Error parsing geocoding response for stop {stop}: {e}")
            return {}
    # Construct routing request
    url = "https://api.openrouteservice.org/v2/directions/driving-car"
    headers = {
        "Accept": "application/json, application/geo+json, application/gpx+xml; charset=utf-8",
        "Authorization": OPENROUTE_SERVICE_API_KEY,
        "Content-Type": "application/json; charset=utf-8",
    }
    body = {
        "coordinates": coordinates,
        "geometry_simplify": "true"
        # "alternative_routes":{"target_count":2,"weight_factor":1.4,"share_factor":0.6},
    }
    try:
        response = requests.post(url, headers=headers, json=body)
        response.raise_for_status()
        route_data = response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching route: {e}")
        return {}
    except KeyError as e:
        print(f"Error parsing route data: {e}")
        return {}

    if not route_data or not route_data.get('routes'):
        print("No route found.")
        return {}

    route = route_data['routes'][0]
    segments = route.get('segments', [])
    if not segments:
        print("No segments found in route.")
        return {}
    duration = route['summary'].get('duration', 0) # seconds
    distance = route['summary'].get('distance', 0) # meters
    arrival_time = departure_time + timedelta(seconds=duration)

    route_summary = f"Drive from {stops[0]} to {stops[-1]} with stops at "
    route_summary += ", ".join(stops[1:-1]) if len(stops) > 2 else "no intermediate stops"
    route_summary += f". The total distance is {(distance / 1000):.2f} km and the estimated travel time is {timedelta(seconds=duration)} (hh:mm:ss)."
    return {
        'route': route,
        'estimated_arrival_time': arrival_time,
        'total_duration': duration,
        'route_summary': route_summary,
        'waypoints': waypoints,
    }


# @tool
def get_weather_forecast(latitude: float, longitude: float, time: datetime) -> Dict[str, Any]:
    """
    Fetches weather forecast data for a specific location and time from OpenWeatherMap API.

    Args:
        latitude: The latitude of the location.
        longitude: The longitude of the location.
        time: The time for which the forecast is needed (datetime object).

    Returns:
        The weather forecast data as a dictionary, or None on error.
    """
    # Make sure 'time' is timezone-aware (in UTC)
    if time.tzinfo is None:
        time = time.replace(tzinfo=timezone.utc)

    url = f"https://api.openweathermap.org/data/2.5/forecast?lat={latitude}&lon={longitude}&appid={OPENWEATHERMAP_API_KEY}&units=metric"  # Use metric units
    try:
        response = requests.get(url)
        response.raise_for_status()
        weather_data = response.json()

        # Find the forecast closest to the specified time
        closest_forecast = None
        min_time_diff = float('inf')

        for forecast in weather_data['list']:
            forecast_time = datetime.fromtimestamp(forecast['dt'], tz=timezone.utc)
            time_diff = abs((forecast_time - time).total_seconds())

            if time_diff < min_time_diff:
                min_time_diff = time_diff
                closest_forecast = forecast

        return closest_forecast if closest_forecast else {}

    except requests.exceptions.RequestException as e:
        print(f"Error fetching weather data: {e}")
        return None
    except KeyError as e:
        print(f"Error parsing weather data: {e}")
        return None


# @tool
def analyze_weather_conditions(weather_data: List[Dict[str, Any]]) -> List[str]:
    """
    Analyzes weather data for potential driving hazards.

    Args:
        weather_data: A list of weather forecasts.

    Returns:
        A list of strings describing any hazardous conditions.
    """
    hazards = []
    for data in weather_data:
        weather = data.get('weather', [])
        if not weather:
            continue
        description = weather[0].get('description', '').lower()
        temperature = data.get('main', {}).get('temp', 0)
        wind_speed = data.get('wind', {}).get('speed', 0)
        time = datetime.fromtimestamp(data['dt'], tz=timezone.utc)  # added line

        if "snow" in description or "sleet" in description:
            hazards.append(f"Snow/Sleet at {time.strftime('%Y-%m-%d %H:%M')}")  # modified line
        elif "heavy rain" in description:
            hazards.append(f"Heavy Rain at {time.strftime('%Y-%m-%d %H:%M')}")  # modified line
        elif "fog" in description:
            hazards.append(f"Fog at {time.strftime('%Y-%m-%d %H:%M')}")  # modified line
        # elif temperature < 0:
        #     hazards.append(f"Freezing Temperatures ({temperature}°C) at {time.strftime('%Y-%m-%d %H:%M')}")  # modified line
        elif temperature < 13: # For testing, consider 20°C as a threshold for freezing
            hazards.append(f"Freezing Temperatures ({temperature}°C) at {time.strftime('%Y-%m-%d %H:%M')}")  # modified line
        elif wind_speed > 15:  # Consider 15 m/s as a threshold for strong winds
            hazards.append(f"Strong Winds ({wind_speed} m/s) at {time.strftime('%Y-%m-%d %H:%M')}")  # modified line

    return hazards


# @tool
def suggest_departure_time(route: Dict[str, Any], weather_data: List[Dict[str, Any]],
                          departure_time: datetime) -> datetime:
    """
    Suggests an optimal departure time based on weather conditions along the route.

    Args:
        route: The route data from OpenRoute Service.
        weather_data: The weather forecast data for the route.
        departure_time: the departure time the user wants to depart

    Returns:
        The suggested departure time as a datetime object.
    """

    # If no weather data, return the original departure time
    if not weather_data:
        return departure_time

    # Analyze weather conditions
    hazards = analyze_weather_conditions(weather_data)

    if not hazards:
        return departure_time

    print("Potential hazards detected:")
    for hazard in hazards:
        print(hazard)

    # Calculate the time with the least hazards.
    best_departure_time = departure_time
    min_hazards = len(hazards)  # Start with the number of hazards at the original departure time

    # Check a few departure times around the original time
    for i in range(-2, 3):  # Check 2 hours before and 2 hours after
        alternative_departure_time = departure_time + timedelta(hours=i)
        # Get new weather data for the alternative departure time
        alternative_weather_data = get_weather_along_route(route, alternative_departure_time)
        alternative_hazards = analyze_weather_conditions(alternative_weather_data)
        num_hazards = len(alternative_hazards)

        if num_hazards < min_hazards:
            min_hazards = num_hazards
            best_departure_time = alternative_departure_time
    return best_departure_time

# @tool
def get_weather_along_route(route: Dict[str, Any], departure_time: datetime) -> List[Dict[str, Any]]:
    """
    Fetches weather forecast data along a driving route, handling multi-segment routes.
    Args:
        route: The route data from OpenRoute Service.
        departure_time: The intended departure time.
    Returns:
        A list of weather data dictionaries, with each dictionary containing
        the weather at a point along the route at the estimated arrival time.
        Returns an empty list on error.
    """
    weather_data = []

    try:
        geometry = openrouteservice.convert.decode_polyline(route.get('geometry', ''))
        segments = route.get('segments', [])

        coordinates = geometry.get('coordinates', [])
        if not coordinates:
            print("No coordinates found in geometry.")
            return []

        total_duration = sum(segment.get('duration', 0) for segment in segments)
        if total_duration == 0:
            print("No route duration found.")
            return []

        num_points = 10  # Number of points to sample along the route
        time_increment = total_duration / (num_points + 1)
        current_time = departure_time

        for i in range(1, num_points + 1):
            point_time = current_time + timedelta(seconds=time_increment * i)

            # Estimate point index
            point_index = int(len(coordinates) * i / (num_points + 1))
            point_index = min(point_index, len(coordinates) - 1)

            lng, lat = coordinates[point_index]
            weather = get_weather_forecast(lat, lng, point_time)
            if weather:
                weather['location'] = {'latitude': lat, 'longitude': lng}
                weather['time'] = point_time.isoformat()
                weather_data.append(weather)
            else:
                print(f"Failed to get weather for location: {lat}, {lng} at {point_time}")
    except Exception as e:
        print(f"Error while processing route: {e}")

    return weather_data

# @tool
# def generate_itinerary_with_llm(origin: str, destination: str, departure_time_str: str) -> str:
#     """
#     Generates a travel itinerary with weather considerations using a Large Language Model (LLM).

#     Args:
#         origin: The origin address.
#         destination: The destination address.
#         departure_time_str: The departure time as a string.

#     Returns:
#         A string containing the itinerary and weather recommendations generated by the LLM.
#     """
#     try:
#         departure_time = datetime.fromisoformat(departure_time_str)
#     except ValueError:
#         return "Invalid departure time format. Please use %Y-%m-%dT%H:%M:%S format."

#     route_info = get_driving_route(origin, destination, departure_time)
#     if not route_info:
#         return "Could not retrieve route information."

#     weather_data = get_weather_along_route(route_info['route'], departure_time)
#     optimal_departure_time = suggest_departure_time(route_info['route'], weather_data, departure_time)

#     # Format the weather data into a string that the LLM can understand
#     weather_summary = ""
#     if weather_data:
#         weather_summary = "Here is the weather forecast for your trip:\n"
#         for data in weather_data:
#             forecast_time = datetime.utcfromtimestamp(data['dt'])
#             weather_summary += (
#                 f"- At {forecast_time.strftime('%Y-%m-%d %H:%M')}, near "
#                 f"({data['location']['latitude']:.2f}, {data['location']['longitude']:.2f}): "
#                 f"{data['weather'][0]['description']}, "
#                 f"Temperature: {data['main']['temp']}°C, "
#                 f"Wind: {data['wind']['speed']} m/s.\n"
#             )
#     else:
#         weather_summary = "There is no weather data available for this route."

#     # Use LLM to generate a more natural-language itinerary
#     prompt_template = ChatPromptTemplate.from_messages([
#         ("system", "You are a helpful travel assistant that provides detailed and friendly travel itineraries, including weather information and recommendations for optimal departure times."),
#         ("user", "I am planning a trip from {origin} to {destination}, departing at {departure_time}. Please provide a detailed itinerary, including information about the weather conditions along the route and the best time to depart to avoid bad weather."),
#     ])
#     llm_chain = LLMChain(llm=model, prompt=prompt_template)

#     # Create the input for the LLM.
#     inputs = {
#         "origin": origin,
#         "destination": destination,
#         "departure_time": departure_time.strftime('%Y-%m-%d %H:%M:%S'),
#         "route_summary": route_info['route_summary'],
#         "weather_conditions": weather_summary,
#         "optimal_departure_time": optimal_departure_time.strftime('%Y-%m-%d %H:%M:%S'),
#     }

#     # Generate the itinerary using the LLM
#     itinerary_response = llm_chain.run(inputs)

#     return itinerary_response

tools = [
    get_driving_route,
    get_weather_forecast,
    get_weather_along_route,
    analyze_weather_conditions,
    suggest_departure_time,
    # generate_itinerary_with_llm,
]

agent_executor = create_react_agent(model, tools)

if __name__ == "__main__":
    origin = "Toronto, Canada"
    destination = "Chicago, Illinois, USA"
    # destination = "Hamilton, Ontario"
    departure_time_str = "2025-04-14T09:00:00"

    prompt = f"I want a detailed itinerary for a trip from {origin} to {destination}, departing at {departure_time_str}.  What is the best time to leave to avoid bad weather?"
    messages = agent_executor.invoke({"messages": [("human", prompt)]})
    print(
        {
            "input": prompt,
            "output": messages["messages"][-1].content,
        }
    )

    # route_info = get_driving_route([origin, 'Fort Wayne, Indiana, USA', destination], datetime.fromisoformat(departure_time_str))
    # # # # [[-79.38171, 43.64877], [-85.12887, 41.113154], [-87.66063, 41.87897]]
    # weather_data = get_weather_along_route(route_info['route'], datetime.fromisoformat(departure_time_str))
    # print(weather_data)
    # # Example weather data for testing
    # weather_conditions = analyze_weather_conditions(weather_data)
    # print(weather_conditions)
    # departure_time = suggest_departure_time(route_info['route'], weather_data, datetime.fromisoformat(departure_time_str))
    # print(departure_time)

