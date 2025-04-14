from datetime import datetime
from typing import List, Optional
import logging
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from travel_agent import mock_agent as agent  # Use mock implementation

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
    """
    location: str
    arrival_time: str
    weather: str
    
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

@app.post("/api/plan-trip", response_model=List[RouteOption])
async def plan_trip(request: TripRequest):
    try:
        logger.info(f"Processing trip request from {request.start} to {request.end}")
        
        # Convert string to datetime
        departure_time = datetime.fromisoformat(request.departure_time)
        logger.debug(f"Parsed departure time: {departure_time}")
        
        # Get route info from Google Maps
        logger.debug("Fetching route information")
        route_info = agent.get_driving_route(request.start, request.end, departure_time)
        if not route_info:
            logger.warning("No route found")
            raise HTTPException(status_code=404, detail="Route not found")
            
        # Get weather data along route
        logger.debug("Fetching weather data")
        weather_data = agent.get_weather_along_route(route_info['route'], departure_time)
        
        # Get optimal departure time
        logger.debug("Calculating optimal departure time")
        optimal_time = agent.suggest_departure_time(route_info['route'], weather_data, departure_time)
        
        # Generate full itinerary using LLM
        logger.debug("Generating itinerary")
        itinerary = agent.generate_itinerary_with_llm(
            request.start,
            request.end,
            optimal_time.isoformat()
        )
        
        # Extract route coordinates for visualization
        logger.debug("Extracting route coordinates")
        coordinates = []
        if route_info['route'].get('legs'):
            # Add start location of first leg
            first_leg = route_info['route']['legs'][0]
            coordinates.append([
                first_leg['start_location']['lat'],
                first_leg['start_location']['lng']
            ])
            
            # Add end location of each leg
            for leg in route_info['route']['legs']:
                coordinates.append([
                    leg['end_location']['lat'],
                    leg['end_location']['lng']
                ])
        
        # Create route option with original departure time
        logger.debug("Creating route options")
        original_route = RouteOption(
            id=1,
            departure_time=departure_time.isoformat(),
            estimated_duration=route_info['route']['legs'][0]['duration']['text'],
            weather_risk="High" if len(agent.analyze_weather_conditions(weather_data)) > 2 else "Low",
            stops=[
                WeatherStop(
                    location=leg.get('start_address', ''),
                    arrival_time=leg['arrival_time'] if isinstance(leg['arrival_time'], str) else leg['arrival_time'].get('text', ''),
                    weather=f"{weather['weather'][0]['description'].capitalize()}, {weather['main']['temp']}°C"
                )
                for leg, weather in zip(route_info['route']['legs'], weather_data)
            ],
            score=85 if len(agent.analyze_weather_conditions(weather_data)) < 2 else 65,
            coordinates=coordinates
        )
        
        # Create route option with optimal departure time
        optimal_route = None
        if optimal_time != departure_time:
            optimal_route_info = agent.get_driving_route(request.start, request.end, optimal_time)
            optimal_weather = agent.get_weather_along_route(optimal_route_info['route'], optimal_time)
            
            optimal_route = RouteOption(
                id=2,
                departure_time=optimal_time.isoformat(),
                estimated_duration=optimal_route_info['route']['legs'][0]['duration']['text'],
                weather_risk="Low",
                stops=[
                    WeatherStop(
                        location=leg.get('start_address', ''),
                        arrival_time=leg['arrival_time'] if isinstance(leg['arrival_time'], str) else leg['arrival_time'].get('text', ''),
                        weather=f"{weather['weather'][0]['description'].capitalize()}, {weather['main']['temp']}°C"
                    )
                    for leg, weather in zip(optimal_route_info['route']['legs'], optimal_weather)
                ],
                score=90,
                coordinates=coordinates
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
