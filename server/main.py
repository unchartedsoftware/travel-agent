from datetime import datetime
from typing import List, Optional, Any
import logging
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
# from src.travel_agent import mock_agent as agent  # Use mock implementation
from src.travel_agent import agent  # Use mock implementation
import openrouteservice

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="AI Trip Planner API")

# Configure CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite's default dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.exception("An error occurred while processing the request")
    return JSONResponse(
        status_code=500,
        content={"detail": f"Server error: {str(exc)}", "type": type(exc).__name__}
    )

class TripRequest(BaseModel):
    """
    Represents a trip planning request from the client.

    Attributes:
        start: Starting location address or city name.
        end: Destination address or city name.
        departure_time: ISO formatted departure time string (e.g. "2025-04-14T09:00:00").
    """
    start: str
    end: str
    departure_time: str

class WeatherStop(BaseModel):
    """
    Represents a stop along the route with associated weather information.

    Attributes:
        location: Name or address of the location.
        arrival_time: Expected arrival time at this location (ISO format).
        weather: Weather description with temperature (e.g. "Partly cloudy, 15°C").
        coordinates: Location coordinates as [latitude, longitude].
    """
    location: str
    arrival_time: str
    weather: str
    coordinates: List[float]

class RouteOption(BaseModel):
    """
    Represents a complete route option with timing, weather risk assessment, and waypoints.

    Attributes:
        id: Unique identifier for this route option.
        departure_time: Suggested departure time in ISO format.
        estimated_duration: Human-readable duration (e.g. "5 hours").
        weather_risk: Risk assessment based on weather conditions ("Low", "Medium", or "High").
        stops: List of WeatherStop objects representing waypoints along the route.
        score: Route quality score from 0-100, considering weather and timing.
        coordinates: List of [latitude, longitude] pairs defining the route geometry.
    """
    id: int
    departure_time: str
    estimated_duration: str
    weather_risk: str
    stops: List[WeatherStop]
    score: int
    coordinates: List[List[float]]

class PlanTripResponse(BaseModel):
    response: Any  # Adjust fields based on the actual response structure
    ai_messages_content: Any

@app.post("/api/trial", response_model=List[str])
async def plan_trip(request: TripRequest):
    try:
        logger.info(f"Processing trip request from {request.start} to {request.end}")

        # Convert string to datetime
        departure_time = datetime.fromisoformat(request.departure_time)
        logger.debug(f"Parsed departure time: {departure_time}")

        # Generate full itinerary using LLM
        logger.debug("Generating itinerary")
        itinerary = agent.passthrough_llm_function(
            request.start,
            request.end,
            departure_time
        )

        return itinerary.split('\n')

    except Exception as e:
        logger.exception("Error processing trip request")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/plan-trip-agent", response_model=PlanTripResponse)
async def ask_travel_agent(request: TripRequest):
    prompt = f"I want a detailed itinerary for a trip from {request.start} to {request.end}, departing at {request.departure_time}. Please provide major stops along the way and weather conditions at each stop at the time of arrival. Include estimated travel time and any potential weather risks. Please make sure to avoid bad weather along the way"
    # Use the agent
    # config = {"configurable": {"thread_id": "abc123"}}
    all_messages = []
    ai_messages_content = []
    agent_stream = agent.agent_executor.stream(
        {"messages": [HumanMessage(content=prompt)]},
        # config,
        stream_mode="values",
    ) 
    for step in agent_stream:
        step["messages"][-1].pretty_print()
        msg = step["messages"][-1]
        all_messages.append(msg)
        if msg.type == "ai":
            ai_messages_content.append(msg.content)

    return {"response": all_messages, "ai_messages_content": ai_messages_content}

@app.post("/api/plan-trip", response_model=List[RouteOption])
async def plan_trip(request: TripRequest):
    try:
        logger.info(f"Processing trip request from {request.start} to {request.end}")

        # Convert string to datetime
        departure_time = datetime.fromisoformat(request.departure_time)
        logger.debug(f"Parsed departure time: {departure_time}")

        # Get route info from OpenRoute Service
        logger.debug("Fetching route information")
        route_info = agent.get_driving_route.func([request.start, request.end], departure_time)
        agent.add_legs_to_route(route_info['route'], departure_time)
        route_info["route"]["geometry_decoded"] = openrouteservice.convert.decode_polyline(route_info["route"].get('geometry', ''))
        
        if not route_info:
            logger.warning("No route found")
            raise HTTPException(status_code=404, detail="Route not found")

        # Get weather data along route
        logger.debug("Fetching weather data")
        weather_data = agent.get_weather_along_route.func(route_info['route'], departure_time)

        # Get optimal departure time
        logger.debug("Calculating optimal departure time")
        optimal_time = agent.suggest_departure_time.func(route_info['route'], weather_data, departure_time)

        # Generate full itinerary using LLM
        logger.debug("Generating itinerary")
        itinerary = agent.generate_itinerary_with_llm.func(
            request.start,
            request.end,
            optimal_time.isoformat()
        )

        # Extract route coordinates for visualization
        logger.debug("Extracting route coordinates")
        geometry = route_info['route'].get('geometry', {})
        coordinates = []
        if geometry:
            decoded = agent.openrouteservice.convert.decode_polyline(geometry)
            coordinates = [[coord[1], coord[0]] for coord in decoded.get('coordinates', [])]

        # Analyze weather hazards
        hazards = agent.analyze_weather_conditions.func(weather_data)
        
        # Calculate weather risk based on hazard types and count
        def calculate_weather_risk(hazards):
            if not hazards:
                return "Low"
            severe_conditions = ["Snow/Sleet", "Heavy Rain", "Strong Winds"]
            severe_count = sum(1 for h in hazards if any(c in h for c in severe_conditions))
            if severe_count > 1:
                return "High"
            elif severe_count == 1 or len(hazards) > 2:
                return "Medium"
            return "Low"

        # Create weather stops from the sampled weather points
        def create_weather_stops(weather_data):
            stops = []
            for data in weather_data:
                if not data or 'location' not in data:
                    continue
                lat = data['location']['latitude']
                lon = data['location']['longitude']
                stops.append(WeatherStop(
                    location=f"Route point at {lat:.2f}, {lon:.2f}",
                    arrival_time=data['time'],
                    weather=f"{data['weather'][0]['description'].capitalize()}, {data['main']['temp']}°C",
                    coordinates=[lat, lon]  # WeatherStop expects [latitude, longitude]
                ))
            return stops

        # Create route option with original departure time
        logger.debug("Creating route options")
        weather_risk = calculate_weather_risk(hazards)
        original_route = RouteOption(
            id=1,
            departure_time=departure_time.isoformat(),
            estimated_duration=str(route_info.get('total_duration', 0)),
            weather_risk=weather_risk,
            stops=create_weather_stops(weather_data),
            score=85 if weather_risk == "Low" else (75 if weather_risk == "Medium" else 65),
            coordinates=coordinates
        )

        # Create route option with optimal departure time if different
        optimal_route = None
        if optimal_time != departure_time:
            optimal_route_info = agent.get_driving_route.func([request.start, request.end], optimal_time)
            agent.add_legs_to_route(optimal_route_info['route'], optimal_time)
            optimal_route_info["route"]["geometry_decoded"] = openrouteservice.convert.decode_polyline(optimal_route_info["route"].get('geometry', ''))
            optimal_weather = agent.get_weather_along_route.func(optimal_route_info['route'], optimal_time)
            optimal_hazards = agent.analyze_weather_conditions.func(optimal_weather)
            optimal_risk = calculate_weather_risk(optimal_hazards)

            # Extract coordinates from optimal route
            optimal_geometry = optimal_route_info['route'].get('geometry', {})
            optimal_coordinates = []
            if optimal_geometry:
                decoded = agent.openrouteservice.convert.decode_polyline(optimal_geometry)
                optimal_coordinates = [[coord[1], coord[0]] for coord in decoded.get('coordinates', [])]

            optimal_route = RouteOption(
                id=2,
                departure_time=optimal_time.isoformat(),
                estimated_duration=str(optimal_route_info.get('total_duration', 0)),
                weather_risk=optimal_risk,
                stops=create_weather_stops(optimal_weather),
                score=90 if optimal_risk == "Low" else (80 if optimal_risk == "Medium" else 70),
                coordinates=optimal_coordinates
            )

        logger.info("Successfully processed trip request")
        return [original_route, optimal_route] if optimal_route else [original_route]

    except Exception as e:
        logger.exception("Error processing trip request")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn_config = uvicorn.Config(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="debug",
        access_log=True
    )
    server = uvicorn.Server(uvicorn_config)
    server.run()
