/**
 * Represents a stop along the route with associated weather information.
 * 
 * @interface WeatherStop
 * @property {string} location - Name or address of the location
 * @property {string} arrival_time - Expected arrival time at this location (ISO format)
 * @property {string} weather - Weather description with temperature (e.g. "Partly cloudy, 15°C")
 * @property {[number, number]} coordinates - Location coordinates as [latitude, longitude]
 */
export interface WeatherStop {
  location: string;
  arrival_time: string;
  weather: string;
  coordinates: [number, number];
}

/**
 * Represents a complete route option with timing, weather risk assessment, and waypoints.
 * 
 * @interface RouteOption
 * @property {number} id - Unique identifier for this route option
 * @property {string} departureTime - Suggested departure time in ISO format
 * @property {string} estimatedDuration - Human-readable duration (e.g. "5 hours")
 * @property {'Low' | 'Medium' | 'High'} weatherRisk - Risk assessment based on weather conditions
 * @property {WeatherStop[]} stops - List of waypoints along the route with weather info
 * @property {number} score - Route quality score from 0-100, considering weather and timing
 * @property {[number, number][]} coordinates - List of [latitude, longitude] pairs defining the route geometry
 */
export interface RouteOption {
  id: number;
  departureTime: string;
  estimatedDuration: string;
  weatherRisk: 'Low' | 'Medium' | 'High';
  stops: WeatherStop[];
  score: number;
  coordinates: [number, number][];
}

/**
 * Represents a trip planning request from the user.
 * 
 * @interface TripFormData
 * @property {string} start - Starting location address or city name
 * @property {string} end - Destination address or city name
 * @property {string} departure_time - ISO formatted departure time string (e.g. "2025-04-14T09:00:00")
 */
export interface TripFormData {
  start: string;
  end: string;
  departure_time: string;
}
