import googlemaps
import requests
from datetime import datetime, timedelta
# import pytz  # For time zone handling  - Not used.
from typing import List, Tuple, Dict, Optional, Any
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.chains import LLMChain
from langchain.tools import Tool
from langchain.agents import initialize_agent, AgentType

# API Keys (Replace with your actual keys)
GOOGLE_MAPS_API_KEY = "YOUR_GOOGLE_MAPS_API_KEY"  #  Replace with your actual Google Maps API key
OPENWEATHERMAP_API_KEY = "YOUR_OPENWEATHERMAP_API_KEY"  # Replace with your actual OpenWeatherMap API key
OPENAI_API_KEY = "YOUR_OPENAI_API_KEY"  # Replace with your actual OpenAI API key

# Initialize Google Maps client
gmaps = googlemaps.Client(key=GOOGLE_MAPS_API_KEY)

# Initialize LLM for LangChain
llm = ChatOpenAI(model_name="gpt-3.5-turbo", openai_api_key=OPENAI_API_KEY)  # Or any other LLM you prefer

def get_driving_route(origin: str, destination: str, departure_time: datetime) -> Dict[str, Any]:
    """
    Gets driving directions and route information from Google Maps API.

    Args:
        origin: The origin address.
        destination: The destination address.
        departure_time: The departure time as a datetime object.

    Returns:
        A dictionary containing:
            - 'route': The detailed route information from Google Maps.
            - 'estimated_arrival_time': The estimated arrival time as a datetime object in UTC.
            - 'total_duration': The total travel time in seconds.
            - 'route_summary': A human-readable summary of the route.
    """
    try:
        directions_result = gmaps.directions(
            origin,
            destination,
            mode="driving",
            departure_time=departure_time,
            units="metric"  # Get distances in metric units
        )
    except Exception as e:
        print(f"Error fetching directions: {e}")
        return {}

    if not directions_result:
        print("No directions found.")
        return {}

    route = directions_result[0]  # Get the first route
    legs = route.get('legs', [])
    if not legs:
        print("No legs found in route.")
        return {}

    # Calculate total duration
    total_duration = sum(leg.get('duration', {}).get('value', 0) for leg in legs)

    # Get arrival time.  Google Maps returns arrival_time as a string.  Convert it to datetime in UTC.
    arrival_time_str = legs[0].get('arrival_time')  # Arrival time of the first leg
    arrival_time_utc = datetime.fromisoformat(arrival_time_str.replace('Z', '+00:00'))  # Handle Zulu time

    # Create a route summary
    route_summary = f"Drive from {origin} to {destination}. The total distance is {legs[0]['distance']['text']} and the estimated travel time is {legs[0]['duration']['text']}."

    return {
        'route': route,
        'estimated_arrival_time': arrival_time_utc,
        'total_duration': total_duration,
        'route_summary': route_summary
    }



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
    # Convert datetime to Unix timestamp (OpenWeatherMap uses Unix timestamps)
    timestamp = int(time.timestamp())
    url = f"https://api.openweathermap.org/data/2.5/forecast?lat={latitude}&lon={longitude}&appid={OPENWEATHERMAP_API_KEY}&units=metric"  # Use metric units
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
        weather_data = response.json()

        # Find the forecast closest to the specified time
        closest_forecast = None
        min_time_diff = float('inf')
        for forecast in weather_data['list']:
            forecast_time = datetime.utcfromtimestamp(forecast['dt'])  # Convert to UTC
            time_diff = abs((forecast_time - time).total_seconds())
            if time_diff < min_time_diff:
                min_time_diff = time_diff
                closest_forecast = forecast

        return closest_forecast if closest_forecast else {}

    except requests.exceptions.RequestException as e:
        print(f"Error fetching weather data: {e}")
        return None  # Explicitly return None in case of an error
    except KeyError as e:
        print(f"Error parsing weather data: {e}")
        return None



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
        time = datetime.utcfromtimestamp(data['dt']) #added line

        if "snow" in description or "sleet" in description:
            hazards.append(f"Snow/Sleet at {time.strftime('%Y-%m-%d %H:%M')}") #modified line
        elif "heavy rain" in description:
            hazards.append(f"Heavy Rain at {time.strftime('%Y-%m-%d %H:%M')}")#modified line
        elif "fog" in description:
            hazards.append(f"Fog at {time.strftime('%Y-%m-%d %H:%M')}")#modified line
        elif temperature < 0:
            hazards.append(f"Freezing Temperatures ({temperature}°C) at {time.strftime('%Y-%m-%d %H:%M')}")#modified line
        elif wind_speed > 15:  # Consider 15 m/s as a threshold for strong winds
            hazards.append(f"Strong Winds ({wind_speed} m/s) at {time.strftime('%Y-%m-%d %H:%M')}")#modified line

    return hazards



def suggest_departure_time(route: Dict[str, Any], weather_data: List[Dict[str, Any]],
                           departure_time: datetime) -> datetime:
    """
    Suggests an optimal departure time based on weather conditions along the route.

    Args:
        route: The route data from Google Maps.
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
    min_hazards = len(hazards) # Start with the number of hazards at the original departure time

    # Check a few departure times around the original time
    for i in range(-2, 3):  # Check 2 hours before and 2 hours after
        alternative_departure_time = departure_time + timedelta(hours=i)
        #Get new weather data for the alternative departure time
        alternative_weather_data = get_weather_along_route(route, alternative_departure_time)
        alternative_hazards = analyze_weather_conditions(alternative_weather_data)
        num_hazards = len(alternative_hazards)

        if num_hazards < min_hazards:
            min_hazards = num_hazards
            best_departure_time = alternative_departure_time
    return best_departure_time

def get_weather_along_route(route: Dict[str, Any], departure_time: datetime) -> List[Dict[str, Any]]:
    """
    Fetches weather forecast data along the driving route.  This function now
    correctly handles multi-leg routes and timezones.

    Args:
        route: The route data from Google Maps API (directions result).
        departure_time: The intended departure time.

    Returns:
        A list of weather data dictionaries, with each dictionary containing
        the weather at a point along the route at the estimated arrival time.
        Returns an empty list on error.
    """
    weather_data = []
    legs = route.get('legs', [])
    if not legs:
        print("No legs found in route to get weather.")
        return []

    current_time = departure_time
    for leg in legs:
        # Get the arrival time at the *end* of this leg.
        arrival_time_str = leg.get('arrival_time')
        if not arrival_time_str:
            print("Leg missing arrival_time.")
            return []
        arrival_time = datetime.fromisoformat(arrival_time_str.replace('Z', '+00:00'))

        # Get the latitude and longitude for weather query.  Use the *end* location.
        end_location = leg.get('end_location')
        if not end_location:
            print("Leg missing end_location.")
            return []
        end_lat = end_location.get('lat')
        end_lng = end_location.get('lng')

        # Fetch weather data for the arrival time
        weather = get_weather_forecast(end_lat, end_lng, arrival_time)
        if weather:
            # Store the location (lat/lng) with the weather data.
            weather['location'] = {'latitude': end_lat, 'longitude': end_lng}
            weather_data.append(weather)
        else:
            print(f"Failed to get weather for location: {end_lat}, {end_lng}")

        # Update current_time for the next leg.  Start the next leg at the
        # arrival time of the *previous* leg.
        current_time = arrival_time

    return weather_data


def generate_itinerary_with_llm(origin: str, destination: str, departure_time_str: str) -> str:
    """
    Generates a travel itinerary with weather considerations using a Large Language Model (LLM).

    Args:
        origin: The origin address.
        destination: The destination address.
        departure_time_str: The departure time as a string.

    Returns:
        A string containing the itinerary and weather recommendations generated by the LLM.
    """
    try:
        departure_time = datetime.fromisoformat(departure_time_str)
    except ValueError:
        return "Invalid departure time format. Please use %Y-%m-%dT%H:%M:%S format."

    route_info = get_driving_route(origin, destination, departure_time)
    if not route_info:
        return "Could not retrieve route information."

    weather_data = get_weather_along_route(route_info['route'], departure_time)
    optimal_departure_time = suggest_departure_time(route_info['route'], weather_data, departure_time)

    # Format the weather data into a string that the LLM can understand
    weather_summary = ""
    if weather_data:
        weather_summary = "Here is the weather forecast for your trip:\n"
        for data in weather_data:
            forecast_time = datetime.utcfromtimestamp(data['dt'])
            weather_summary += (
                f"- At {forecast_time.strftime('%Y-%m-%d %H:%M')}, near "
                f"({data['location']['latitude']:.2f}, {data['location']['longitude']:.2f}): "
                f"{data['weather'][0]['description']}, "
                f"Temperature: {data['main']['temp']}°C, "
                f"Wind: {data['wind']['speed']} m/s.\n"
            )
    else:
        weather_summary = "There is no weather data available for this route."

    # Use LLM to generate a more natural-language itinerary
    prompt_template = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful travel assistant that provides detailed and friendly travel itineraries, including weather information and recommendations for optimal departure times."),
        ("user", "I am planning a trip from {origin} to {destination}, departing at {departure_time}. Please provide a detailed itinerary, including information about the weather conditions along the route and the best time to depart to avoid bad weather."),
    ])
    llm_chain = LLMChain(llm=llm, prompt=prompt_template)

    # Create the input for the LLM.
    inputs = {
        "origin": origin,
        "destination": destination,
        "departure_time": departure_time.strftime('%Y-%m-%d %H:%M:%S'),
        "route_summary": route_info['route_summary'],
        "weather_conditions": weather_summary,
        "optimal_departure_time": optimal_departure_time.strftime('%Y-%m-%d %H:%M:%S'),
    }

    # Generate the itinerary using the LLM
    itinerary_response = llm_chain.run(inputs)

    return itinerary_response



# Define tools
tools = [
    Tool(
        name="get_driving_route",
        func=get_driving_route,
        description="Gets the driving route and estimated arrival time from Google Maps. Input should be the origin and destination addresses, and departure time in আইএসও8601 format.",
    ),
    Tool(
        name="get_weather_forecast",
        func=get_weather_forecast,
        description="Fetches the weather forecast for a specific location and time. Input should be latitude, longitude, and time in আইএসও8601 format.",
    ),
    Tool(
        name="get_weather_along_route",
        func=get_weather_along_route,
        description="Fetches the weather forecast data along the driving route.  Input is the route from get_driving_route, and the departure time.",
    ),
    Tool(
        name="suggest_departure_time",
        func=suggest_departure_time,
        description="Suggests the optimal departure time based on weather conditions along the route. Input should be the route information and weather data.",
    ),
    Tool(
        name="generate_itinerary",
        func=generate_itinerary_with_llm,
        description="Generates a user-friendly travel itinerary with weather considerations. Input should be the origin, destination, and departure time.",
    ),
]

# Initialize the agent
agent = initialize_agent(
    tools=tools,
    llm=llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,  # Or use a different agent type
    verbose=True,  # Set to True to see the agent's reasoning
)

if __name__ == "__main__":
    origin = "Toronto, Canada"
    destination = "Chicago, USA"
    departure_time_str = "2024-12-25T09:00:00"

    # Run the agent
    itinerary = agent.run(f"I want a detailed itinerary for a trip from {origin} to {destination}, departing at {departure_time_str}.  What is the best time to leave to avoid bad weather?")
    print(itinerary)
